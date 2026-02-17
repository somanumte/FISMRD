# ============================================
# SERIAL SERVICE - Gestión de Números de Serie
# ============================================
# Responsabilidad: toda la lógica de negocio de seriales
# 
# Funcionalidades:
# - CRUD de seriales
# - Validación de seriales
# - Asignación de seriales a ventas
# - Búsqueda por serial/código de barras
# - Generación de reportes de trazabilidad

from app import db
from app.models.serial import LaptopSerial, InvoiceItemSerial, SerialMovement, SERIAL_STATUS_CHOICES
from app.models.laptop import Laptop
from datetime import datetime, date
import logging
import re

logger = logging.getLogger(__name__)


class SerialService:
    """Servicio para gestión de números de serie de fabricante"""

    # ============================================
    # VALIDACIÓN DE SERIALES
    # ============================================

    @staticmethod
    def validate_serial_format(serial, serial_type='manufacturer'):
        """
        Valida el formato de un número de serie.

        Args:
            serial: Número de serie a validar
            serial_type: Tipo de serial para validación específica

        Returns:
            tuple: (is_valid, error_message)
        """
        if not serial:
            return False, "El número de serie no puede estar vacío"

        serial = serial.strip()

        # Longitud mínima y máxima
        if len(serial) < 3:
            return False, "El número de serie debe tener al menos 3 caracteres"

        if len(serial) > 100:
            return False, "El número de serie no puede exceder 100 caracteres"

        # Validaciones específicas por tipo
        if serial_type == 'service_tag':
            # Dell Service Tag: típicamente 7 caracteres alfanuméricos
            if not re.match(r'^[A-Z0-9]{5,7}$', serial.upper()):
                return False, "El Service Tag de Dell debe tener 5-7 caracteres alfanuméricos"

        elif serial_type == 'imei':
            # IMEI: 15 dígitos
            if not re.match(r'^\d{15}$', serial):
                return False, "El IMEI debe tener exactamente 15 dígitos"

        elif serial_type == 'mac_address':
            # MAC Address: XX:XX:XX:XX:XX:XX o XX-XX-XX-XX-XX-XX
            mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
            if not re.match(mac_pattern, serial):
                return False, "Formato de MAC Address inválido (use XX:XX:XX:XX:XX:XX)"

        # Caracteres permitidos (alfanuméricos, guiones, puntos)
        if not re.match(r'^[A-Za-z0-9\-_.]+$', serial):
            return False, "El serial solo puede contener letras, números, guiones, puntos y guiones bajos"

        return True, None

    @staticmethod
    def is_serial_unique(serial, exclude_id=None):
        """
        Verifica si un número de serie es único en el sistema.

        Args:
            serial: Número de serie a verificar
            exclude_id: ID de serial a excluir (para edición)

        Returns:
            tuple: (is_unique, existing_serial or None)
        """
        normalized = LaptopSerial.normalize_serial(serial)

        query = LaptopSerial.query.filter_by(serial_normalized=normalized)

        if exclude_id:
            query = query.filter(LaptopSerial.id != exclude_id)

        existing = query.first()

        if existing:
            return False, existing

        return True, None

    # ============================================
    # CRUD DE SERIALES
    # ============================================

    @staticmethod
    def create_serial(laptop_id, serial_number, **kwargs):
        """
        Crea un nuevo serial para una laptop.

        Args:
            laptop_id: ID de la laptop
            serial_number: Número de serie del fabricante
            **kwargs: Campos adicionales opcionales
                - serial_type: Tipo de serial
                - barcode: Código de barras
                - notes: Notas
                - unit_cost: Costo unitario
                - warranty_start: Inicio de garantía
                - warranty_end: Fin de garantía
                - warranty_provider: Proveedor de garantía
                - created_by_id: Usuario que crea

        Returns:
            tuple: (success, serial_or_error_message)
        """
        try:
            # Validar que la laptop existe
            laptop = Laptop.query.get(laptop_id)
            if not laptop:
                return False, f"Laptop con ID {laptop_id} no encontrada"

            # Validar formato del serial
            serial_type = kwargs.get('serial_type', 'manufacturer')
            is_valid, error = SerialService.validate_serial_format(serial_number, serial_type)
            if not is_valid:
                return False, error

            # Verificar unicidad
            is_unique, existing = SerialService.is_serial_unique(serial_number)
            if not is_unique:
                return False, f"El serial '{serial_number}' ya existe en el sistema (Laptop: {existing.laptop.sku if existing.laptop else 'N/A'})"

            # Crear el serial
            serial = LaptopSerial(
                laptop_id=laptop_id,
                serial_number=serial_number.strip(),
                serial_normalized=LaptopSerial.normalize_serial(serial_number),
                serial_type=serial_type,
                barcode=kwargs.get('barcode'),
                notes=kwargs.get('notes'),
                unit_cost=kwargs.get('unit_cost'),
                received_date=kwargs.get('received_date', date.today()),
                warranty_start=kwargs.get('warranty_start'),
                warranty_end=kwargs.get('warranty_end'),
                warranty_provider=kwargs.get('warranty_provider'),
                created_by_id=kwargs.get('created_by_id'),
                status='available'
            )

            db.session.add(serial)

            # Flush para obtener el ID del serial antes de registrar el movimiento
            db.session.flush()

            # Registrar movimiento de creación
            SerialService._log_movement(
                serial=serial,
                movement_type='created',
                new_status='available',
                description=f"Serial ingresado al inventario",
                user_id=kwargs.get('created_by_id')
            )

            db.session.commit()

            logger.info(f"✅ Serial creado: {serial_number} para laptop {laptop.sku}")
            return True, serial

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creando serial: {str(e)}", exc_info=True)
            return False, f"Error al crear serial: {str(e)}"

    @staticmethod
    def create_serials_batch(laptop_id, serial_numbers, **kwargs):
        """
        Crea múltiples seriales para una laptop.

        Args:
            laptop_id: ID de la laptop
            serial_numbers: Lista de números de serie
            **kwargs: Campos adicionales opcionales

        Returns:
            dict: {
                'success': bool,
                'created': list of serials,
                'errors': list of errors,
                'total': int,
                'created_count': int,
                'error_count': int
            }
        """
        created = []
        errors = []

        try:
            laptop = Laptop.query.get(laptop_id)
            if not laptop:
                return {
                    'success': False,
                    'created': [],
                    'errors': [f"Laptop con ID {laptop_id} no encontrada"],
                    'total': len(serial_numbers),
                    'created_count': 0,
                    'error_count': len(serial_numbers)
                }

            for serial_number in serial_numbers:
                if not serial_number or not serial_number.strip():
                    continue

                success, result = SerialService.create_serial(
                    laptop_id=laptop_id,
                    serial_number=serial_number,
                    **kwargs
                )

                if success:
                    created.append(result)
                else:
                    errors.append({
                        'serial': serial_number,
                        'error': result
                    })

            return {
                'success': len(errors) == 0,
                'created': created,
                'errors': errors,
                'total': len(serial_numbers),
                'created_count': len(created),
                'error_count': len(errors)
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error en batch de seriales: {str(e)}", exc_info=True)
            return {
                'success': False,
                'created': created,
                'errors': errors + [str(e)],
                'total': len(serial_numbers),
                'created_count': len(created),
                'error_count': len(serial_numbers) - len(created)
            }

    @staticmethod
    def update_serial(serial_id, **kwargs):
        """
        Actualiza un serial existente.

        Args:
            serial_id: ID del serial
            **kwargs: Campos a actualizar

        Returns:
            tuple: (success, serial_or_error_message)
        """
        try:
            serial = LaptopSerial.query.get(serial_id)
            if not serial:
                return False, f"Serial con ID {serial_id} no encontrado"

            # Si se actualiza el número de serie, validar
            if 'serial_number' in kwargs:
                new_serial = kwargs['serial_number']
                serial_type = kwargs.get('serial_type', serial.serial_type)

                is_valid, error = SerialService.validate_serial_format(new_serial, serial_type)
                if not is_valid:
                    return False, error

                is_unique, existing = SerialService.is_serial_unique(new_serial, exclude_id=serial_id)
                if not is_unique:
                    return False, f"El serial '{new_serial}' ya existe en el sistema"

                serial.serial_number = new_serial.strip()
                serial.serial_normalized = LaptopSerial.normalize_serial(new_serial)

            # Actualizar otros campos
            updateable_fields = [
                'serial_type', 'barcode', 'notes', 'unit_cost',
                'warranty_start', 'warranty_end', 'warranty_provider'
            ]

            for field in updateable_fields:
                if field in kwargs:
                    setattr(serial, field, kwargs[field])

            serial.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"✅ Serial actualizado: {serial.serial_number}")
            return True, serial

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error actualizando serial: {str(e)}", exc_info=True)
            return False, f"Error al actualizar serial: {str(e)}"

    @staticmethod
    def delete_serial(serial_id, user_id=None):
        """
        Elimina un serial (solo si está disponible y no tiene historial de ventas).

        Args:
            serial_id: ID del serial
            user_id: Usuario que elimina

        Returns:
            tuple: (success, error_message)
        """
        try:
            serial = LaptopSerial.query.get(serial_id)
            if not serial:
                return False, f"Serial con ID {serial_id} no encontrado"

            # No permitir eliminar si está vendido
            if serial.status == 'sold':
                return False, "No se puede eliminar un serial que ha sido vendido"

            # No permitir eliminar si tiene historial de ventas
            if serial.sales_history.count() > 0:
                return False, "No se puede eliminar un serial con historial de ventas"

            serial_number = serial.serial_number
            laptop_sku = serial.laptop.sku if serial.laptop else 'N/A'

            db.session.delete(serial)
            db.session.commit()

            logger.info(f"🗑️ Serial eliminado: {serial_number} de laptop {laptop_sku}")
            return True, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error eliminando serial: {str(e)}", exc_info=True)
            return False, f"Error al eliminar serial: {str(e)}"

    # ============================================
    # BÚSQUEDA DE SERIALES
    # ============================================

    @staticmethod
    def find_by_serial(serial_number):
        """
        Busca un serial por su número (o código de barras).

        Args:
            serial_number: Número de serie o código de barras

        Returns:
            LaptopSerial or None
        """
        if not serial_number:
            return None

        normalized = LaptopSerial.normalize_serial(serial_number)

        # Buscar por serial normalizado
        serial = LaptopSerial.query.filter_by(serial_normalized=normalized).first()

        # Si no encuentra, buscar por código de barras
        if not serial:
            serial = LaptopSerial.query.filter_by(barcode=serial_number.strip()).first()

        return serial

    @staticmethod
    def search_serials(query, laptop_id=None, status=None, limit=50):
        """
        Búsqueda avanzada de seriales.

        Args:
            query: Texto de búsqueda
            laptop_id: Filtrar por laptop específica
            status: Filtrar por estado
            limit: Límite de resultados

        Returns:
            list: Lista de seriales encontrados
        """
        base_query = LaptopSerial.query

        if query:
            search_pattern = f"%{query}%"
            base_query = base_query.filter(
                db.or_(
                    LaptopSerial.serial_number.ilike(search_pattern),
                    LaptopSerial.serial_normalized.ilike(search_pattern),
                    LaptopSerial.barcode.ilike(search_pattern),
                )
            )

        if laptop_id:
            base_query = base_query.filter_by(laptop_id=laptop_id)

        if status:
            if isinstance(status, list):
                base_query = base_query.filter(LaptopSerial.status.in_(status))
            else:
                base_query = base_query.filter_by(status=status)

        return base_query.order_by(LaptopSerial.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_available_serials_for_laptop(laptop_id):
        """
        Obtiene todos los seriales disponibles para una laptop.

        Args:
            laptop_id: ID de la laptop

        Returns:
            list: Lista de seriales disponibles
        """
        return LaptopSerial.query.filter_by(
            laptop_id=laptop_id,
            status='available'
        ).order_by(LaptopSerial.received_date.desc()).all()

    @staticmethod
    def count_serials_by_status(laptop_id=None):
        """
        Cuenta seriales agrupados por estado.

        Args:
            laptop_id: Filtrar por laptop (opcional)

        Returns:
            dict: {status: count}
        """
        query = db.session.query(
            LaptopSerial.status,
            db.func.count(LaptopSerial.id)
        )

        if laptop_id:
            query = query.filter_by(laptop_id=laptop_id)

        query = query.group_by(LaptopSerial.status)

        return dict(query.all())

    # ============================================
    # GESTIÓN DE VENTAS
    # ============================================

    @staticmethod
    def assign_serials_to_invoice_item(invoice_item, serial_ids, user_id=None):
        """
        Asigna seriales específicos a un item de factura.

        Args:
            invoice_item: Objeto InvoiceItem
            serial_ids: Lista de IDs de seriales a asignar
            user_id: Usuario que realiza la operación

        Returns:
            tuple: (success, result_or_error)
        """
        try:
            assigned = []
            errors = []

            for serial_id in serial_ids:
                serial = LaptopSerial.query.get(serial_id)

                if not serial:
                    errors.append(f"Serial ID {serial_id} no encontrado")
                    continue

                if not serial.is_available:
                    errors.append(f"Serial {serial.serial_number} no está disponible (estado: {serial.status_display})")
                    continue

                # Verificar que el serial pertenece al laptop del item
                if invoice_item.laptop_id and serial.laptop_id != invoice_item.laptop_id:
                    errors.append(f"Serial {serial.serial_number} no pertenece al producto del item")
                    continue

                # Crear relación
                item_serial = InvoiceItemSerial(
                    invoice_item_id=invoice_item.id,
                    serial_id=serial_id,
                    unit_sale_price=invoice_item.unit_price
                )
                db.session.add(item_serial)

                # Marcar serial como vendido
                old_status = serial.status
                serial.status = 'sold'
                serial.sale_price = invoice_item.unit_price
                serial.sold_date = datetime.utcnow()

                # Registrar movimiento
                SerialService._log_movement(
                    serial=serial,
                    movement_type='sold',
                    previous_status=old_status,
                    new_status='sold',
                    invoice_id=invoice_item.invoice_id,
                    description=f"Vendido en factura #{invoice_item.invoice.invoice_number if invoice_item.invoice else 'N/A'}",
                    user_id=user_id
                )

                assigned.append(serial)

            if errors:
                # Si hay errores pero también asignaciones, dejamos que el llamador decida si hacer commit parcial o rollback
                return True, {
                    'assigned': assigned,
                    'errors': errors,
                    'partial': len(assigned) > 0
                }

            logger.info(f"✅ {len(assigned)} seriales preparados para asignación a item de factura {invoice_item.id}")
            return True, {
                'assigned': assigned,
                'errors': [],
                'partial': False
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error asignando seriales: {str(e)}", exc_info=True)
            return False, str(e)

    @staticmethod
    def release_serials_from_invoice_item(invoice_item, user_id=None):
        """
        Libera los seriales de un item de factura (para cancelaciones/devoluciones).

        Args:
            invoice_item: Objeto InvoiceItem
            user_id: Usuario que realiza la operación

        Returns:
            tuple: (success, released_count_or_error)
        """
        try:
            released_count = 0

            for item_serial in invoice_item.sold_serials.all():
                serial = item_serial.serial

                if serial:
                    old_status = serial.status
                    serial.status = 'available'
                    serial.sale_price = None
                    serial.sold_date = None

                    # Registrar movimiento
                    SerialService._log_movement(
                        serial=serial,
                        movement_type='returned',
                        previous_status=old_status,
                        new_status='available',
                        invoice_id=invoice_item.invoice_id,
                        description=f"Devuelto/Cancelado de factura #{invoice_item.invoice.invoice_number if invoice_item.invoice else 'N/A'}",
                        user_id=user_id
                    )

                    released_count += 1

                # Eliminar la relación
                db.session.delete(item_serial)

            logger.info(f"✅ {released_count} seriales preparados para liberación de item de factura {invoice_item.id}")
            return True, released_count

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error liberando seriales: {str(e)}", exc_info=True)
            return False, str(e)

    @staticmethod
    def change_serial_status(serial_id, new_status, reason=None, user_id=None):
        """
        Cambia el estado de un serial.

        Args:
            serial_id: ID del serial
            new_status: Nuevo estado
            reason: Razón del cambio
            user_id: Usuario que realiza el cambio

        Returns:
            tuple: (success, serial_or_error)
        """
        try:
            serial = LaptopSerial.query.get(serial_id)
            if not serial:
                return False, f"Serial con ID {serial_id} no encontrado"

            # Validar estado
            valid_statuses = [s[0] for s in SERIAL_STATUS_CHOICES]
            if new_status not in valid_statuses:
                return False, f"Estado '{new_status}' no válido"

            old_status = serial.status

            if old_status == new_status:
                return True, serial  # No hay cambio

            serial.status = new_status
            serial.updated_at = datetime.utcnow()

            # Registrar movimiento
            SerialService._log_movement(
                serial=serial,
                movement_type='status_change',
                previous_status=old_status,
                new_status=new_status,
                description=reason or f"Cambio de estado: {old_status} → {new_status}",
                user_id=user_id
            )

            db.session.commit()

            logger.info(f"✅ Estado de serial {serial.serial_number} cambiado: {old_status} → {new_status}")
            return True, serial

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error cambiando estado de serial: {str(e)}", exc_info=True)
            return False, str(e)

    # ============================================
    # SINCRONIZACIÓN CON INVENTARIO
    # ============================================

    @staticmethod
    def sync_laptop_quantity(laptop_id):
        """
        Sincroniza la cantidad de una laptop con sus seriales disponibles.

        Args:
            laptop_id: ID de la laptop

        Returns:
            tuple: (success, info_dict)
        """
        try:
            laptop = Laptop.query.get(laptop_id)
            if not laptop:
                return False, f"Laptop con ID {laptop_id} no encontrada"

            # Contar seriales disponibles
            available_count = LaptopSerial.query.filter_by(
                laptop_id=laptop_id,
                status='available'
            ).count()

            # Total de seriales
            total_serials = LaptopSerial.query.filter_by(laptop_id=laptop_id).count()

            old_quantity = laptop.quantity

            # Actualizar cantidad de la laptop
            laptop.quantity = available_count
            laptop.updated_at = datetime.utcnow()

            db.session.commit()

            return True, {
                'laptop_id': laptop_id,
                'sku': laptop.sku,
                'old_quantity': old_quantity,
                'new_quantity': available_count,
                'total_serials': total_serials,
                'synced': old_quantity != available_count
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error sincronizando cantidad: {str(e)}", exc_info=True)
            return False, str(e)

    @staticmethod
    def validate_laptop_serial_count(laptop_id):
        """
        Valida que la cantidad de seriales coincida con la cantidad del inventario.

        Args:
            laptop_id: ID de la laptop

        Returns:
            dict: Información de validación
        """
        laptop = Laptop.query.get(laptop_id)
        if not laptop:
            return {
                'valid': False,
                'error': f"Laptop con ID {laptop_id} no encontrada"
            }

        available_serials = LaptopSerial.query.filter_by(
            laptop_id=laptop_id,
            status='available'
        ).count()

        return {
            'valid': laptop.quantity == available_serials,
            'laptop_quantity': laptop.quantity,
            'available_serials': available_serials,
            'difference': laptop.quantity - available_serials,
            'message': (
                "✅ Cantidad sincronizada" if laptop.quantity == available_serials
                else f"⚠️ Diferencia: {abs(laptop.quantity - available_serials)} unidades"
            )
        }

    # ============================================
    # TRAZABILIDAD
    # ============================================

    @staticmethod
    def get_serial_history(serial_id):
        """
        Obtiene el historial completo de un serial.

        Args:
            serial_id: ID del serial

        Returns:
            list: Lista de movimientos ordenados por fecha
        """
        return SerialMovement.query.filter_by(
            serial_id=serial_id
        ).order_by(SerialMovement.created_at.desc()).all()

    @staticmethod
    def get_serial_sale_info(serial_id):
        """
        Obtiene información de venta de un serial.

        Args:
            serial_id: ID del serial

        Returns:
            dict or None: Información de la venta si existe
        """
        item_serial = InvoiceItemSerial.query.filter_by(serial_id=serial_id).first()

        if not item_serial:
            return None

        invoice_item = item_serial.invoice_item
        invoice = invoice_item.invoice if invoice_item else None

        return {
            'invoice_number': invoice.invoice_number if invoice else None,
            'invoice_date': invoice.invoice_date if invoice else None,
            'customer': invoice.customer.full_name if invoice and invoice.customer else None,
            'customer_id': invoice.customer.id_number if invoice and invoice.customer else None,
            'sale_price': float(item_serial.unit_sale_price) if item_serial.unit_sale_price else None,
            'invoice_status': invoice.status if invoice else None,
        }

    # ============================================
    # MÉTODOS INTERNOS
    # ============================================

    @staticmethod
    def _log_movement(serial, movement_type, new_status=None, previous_status=None,
                      invoice_id=None, description=None, user_id=None, extra_data=None):
        """
        Registra un movimiento de serial (interno).
        """
        movement = SerialMovement(
            serial_id=serial.id,
            movement_type=movement_type,
            previous_status=previous_status or serial.status,
            new_status=new_status,
            invoice_id=invoice_id,
            description=description,
            extra_data=extra_data,
            user_id=user_id
        )
        db.session.add(movement)
        # No commit aquí - se hace en el método llamador

    # ============================================
    # ESTADÍSTICAS Y REPORTES
    # ============================================

    @staticmethod
    def get_serial_stats():
        """
        Obtiene estadísticas generales de seriales.

        Returns:
            dict: Estadísticas
        """
        total = LaptopSerial.query.count()

        stats_by_status = SerialService.count_serials_by_status()

        # Seriales con garantía activa
        with_warranty = LaptopSerial.query.filter(
            LaptopSerial.warranty_end >= date.today()
        ).count()

        # Seriales vendidos este mes
        from datetime import timedelta
        first_of_month = date.today().replace(day=1)
        sold_this_month = LaptopSerial.query.filter(
            LaptopSerial.status == 'sold',
            LaptopSerial.sold_date >= first_of_month
        ).count()

        return {
            'total': total,
            'by_status': stats_by_status,
            'available': stats_by_status.get('available', 0),
            'sold': stats_by_status.get('sold', 0),
            'with_active_warranty': with_warranty,
            'sold_this_month': sold_this_month,
        }