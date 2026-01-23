# ============================================
# INVOICE INVENTORY SERVICE - CON SERIALES
# ============================================
# Versión actualizada que integra gestión de seriales
# 
# Responsabilidad: 
# - Control de stock al vender/restaurar laptops
# - Asignación de seriales específicos a ventas
# - Trazabilidad completa de qué serial se vendió en cada factura

from app import db
from app.models.laptop import Laptop
from app.models.invoice import InvoiceItem
from app.models.serial import LaptopSerial, InvoiceItemSerial, SerialMovement
from app.services.serial_service import SerialService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InvoiceInventoryServiceWithSerials:
    """
    Servicio para manejar inventario en operaciones de facturación
    con soporte completo para seriales de fabricante.
    """

    # ============================================
    # VALIDACIÓN DE STOCK CON SERIALES
    # ============================================

    @staticmethod
    def validate_stock_for_invoice_items(items_data, require_serials=True):
        """
        Valida que haya suficiente stock para todos los items de laptop.

        Args:
            items_data: Lista de diccionarios con datos de items (JSON parseado)
            require_serials: Si True, requiere que se especifiquen seriales para cada unidad

        Returns:
            tuple: (is_valid, error_message, warnings)
        """
        try:
            warnings = []

            for item in items_data:
                if item.get('type') == 'laptop' and item.get('laptop_id'):
                    laptop_id = int(item['laptop_id'])
                    quantity = int(item.get('quantity', 1))
                    serial_ids = item.get('serial_ids', [])

                    laptop = Laptop.query.get(laptop_id)
                    if not laptop:
                        return False, f'Laptop ID {laptop_id} no encontrada', []

                    # Verificar cantidad general
                    if laptop.quantity < quantity:
                        return False, (
                            f'Stock insuficiente para {laptop.display_name}. '
                            f'Disponible: {laptop.quantity}, Solicitado: {quantity}'
                        ), []

                    # Verificar seriales si se requieren
                    if require_serials:
                        # Contar seriales disponibles
                        available_serials = LaptopSerial.query.filter_by(
                            laptop_id=laptop_id,
                            status='available'
                        ).count()

                        if available_serials < quantity:
                            return False, (
                                f'Seriales insuficientes para {laptop.display_name}. '
                                f'Seriales disponibles: {available_serials}, Solicitado: {quantity}'
                            ), []

                        # Si se especificaron seriales, validarlos
                        if serial_ids:
                            if len(serial_ids) != quantity:
                                return False, (
                                    f'Debe especificar exactamente {quantity} serial(es) para {laptop.display_name}. '
                                    f'Especificados: {len(serial_ids)}'
                                ), []

                            # Validar cada serial
                            for serial_id in serial_ids:
                                serial = LaptopSerial.query.get(serial_id)
                                if not serial:
                                    return False, f'Serial ID {serial_id} no encontrado', []
                                if serial.laptop_id != laptop_id:
                                    return False, f'Serial {serial.serial_number} no pertenece a {laptop.display_name}', []
                                if serial.status != 'available':
                                    return False, f'Serial {serial.serial_number} no está disponible (estado: {serial.status_display})', []
                        else:
                            # Warning: no se especificaron seriales
                            warnings.append(
                                f'No se especificaron seriales para {laptop.display_name}. '
                                f'Se asignarán automáticamente.'
                            )
                    else:
                        # Verificar si hay seriales registrados pero no se requieren
                        total_serials = LaptopSerial.query.filter_by(laptop_id=laptop_id).count()
                        if total_serials > 0:
                            warnings.append(
                                f'{laptop.display_name} tiene seriales registrados. '
                                f'Considere especificar qué seriales se venden.'
                            )

            return True, None, warnings

        except Exception as e:
            logger.error(f'Error validando stock con seriales: {str(e)}', exc_info=True)
            return False, f'Error validando stock: {str(e)}', []

    # ============================================
    # PROCESAMIENTO DE VENTA CON SERIALES
    # ============================================

    @staticmethod
    def process_sale_with_serials(invoice, items_data, user_id=None):
        """
        Procesa una venta actualizando inventario y asignando seriales.

        Args:
            invoice: Objeto Invoice
            items_data: Lista de datos de items con serial_ids opcional
            user_id: ID del usuario que realiza la operación

        Returns:
            tuple: (success, result_or_error)
        """
        try:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"🛒 PROCESANDO VENTA CON SERIALES - Factura {invoice.invoice_number}")
            logger.info(f"{'=' * 60}")

            results = {
                'items_processed': 0,
                'serials_assigned': 0,
                'auto_assigned': 0,
                'details': []
            }

            for item in invoice.items.all():
                if item.item_type == 'laptop' and item.laptop_id:
                    laptop = Laptop.query.get(item.laptop_id)
                    if not laptop:
                        return False, f'Laptop ID {item.laptop_id} no encontrada'

                    # Buscar datos del item (para obtener serial_ids)
                    item_data = next(
                        (d for d in items_data if d.get('laptop_id') == item.laptop_id),
                        {}
                    )
                    serial_ids = item_data.get('serial_ids', [])

                    # Si no se especificaron seriales, auto-asignar
                    if not serial_ids:
                        available = SerialService.get_available_serials_for_laptop(laptop.id)
                        if len(available) >= item.quantity:
                            serial_ids = [s.id for s in available[:item.quantity]]
                            results['auto_assigned'] += len(serial_ids)
                            logger.info(f"   🔄 Auto-asignando {len(serial_ids)} seriales para {laptop.sku}")
                        else:
                            # No hay suficientes seriales, proceder sin ellos
                            logger.warning(f"   ⚠️ No hay suficientes seriales para {laptop.sku}")

                    # Asignar seriales al item
                    if serial_ids:
                        success, assign_result = SerialService.assign_serials_to_invoice_item(
                            invoice_item=item,
                            serial_ids=serial_ids,
                            user_id=user_id
                        )

                        if not success:
                            return False, f'Error asignando seriales: {assign_result}'

                        results['serials_assigned'] += len(assign_result.get('assigned', []))

                        # Log de seriales asignados
                        for serial in assign_result.get('assigned', []):
                            logger.info(f"   ✅ Serial {serial.serial_number} asignado")
                            results['details'].append({
                                'laptop_sku': laptop.sku,
                                'serial': serial.serial_number,
                                'action': 'assigned'
                            })

                    # Actualizar cantidad del laptop
                    old_quantity = laptop.quantity
                    laptop.quantity -= item.quantity

                    if laptop.quantity == 0:
                        laptop.sale_date = datetime.now().date()

                    logger.info(f"   📦 {laptop.sku}: {old_quantity} → {laptop.quantity} (-{item.quantity})")

                    results['items_processed'] += 1

            db.session.commit()

            logger.info(f"\n✅ Venta procesada exitosamente")
            logger.info(f"   Items: {results['items_processed']}")
            logger.info(f"   Seriales asignados: {results['serials_assigned']}")
            logger.info(f"   Auto-asignados: {results['auto_assigned']}")
            logger.info(f"{'=' * 60}\n")

            return True, results

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error procesando venta: {str(e)}", exc_info=True)
            return False, str(e)

    # ============================================
    # CANCELACIÓN/DEVOLUCIÓN CON SERIALES
    # ============================================

    @staticmethod
    def reverse_sale_with_serials(invoice, user_id=None):
        """
        Revierte una venta, restaurando inventario y liberando seriales.

        Args:
            invoice: Objeto Invoice
            user_id: ID del usuario que realiza la operación

        Returns:
            tuple: (success, result_or_error)
        """
        try:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"🔄 REVIRTIENDO VENTA - Factura {invoice.invoice_number}")
            logger.info(f"{'=' * 60}")

            results = {
                'items_restored': 0,
                'serials_released': 0,
                'details': []
            }

            for item in invoice.items.all():
                if item.item_type == 'laptop' and item.laptop_id:
                    laptop = Laptop.query.get(item.laptop_id)
                    if not laptop:
                        logger.warning(f"   ⚠️ Laptop ID {item.laptop_id} no encontrada")
                        continue

                    # Liberar seriales asignados a este item
                    success, released_count = SerialService.release_serials_from_invoice_item(
                        invoice_item=item,
                        user_id=user_id
                    )

                    if success:
                        results['serials_released'] += released_count
                        logger.info(f"   🔓 {released_count} seriales liberados para {laptop.sku}")

                    # Restaurar cantidad
                    old_quantity = laptop.quantity
                    laptop.quantity += item.quantity

                    if old_quantity == 0:
                        laptop.sale_date = None

                    logger.info(f"   📦 {laptop.sku}: {old_quantity} → {laptop.quantity} (+{item.quantity})")

                    results['items_restored'] += 1
                    results['details'].append({
                        'laptop_sku': laptop.sku,
                        'quantity_restored': item.quantity,
                        'serials_released': released_count
                    })

            db.session.commit()

            logger.info(f"\n✅ Venta revertida exitosamente")
            logger.info(f"   Items restaurados: {results['items_restored']}")
            logger.info(f"   Seriales liberados: {results['serials_released']}")
            logger.info(f"{'=' * 60}\n")

            return True, results

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error revirtiendo venta: {str(e)}", exc_info=True)
            return False, str(e)

    # ============================================
    # CONSULTAS DE TRAZABILIDAD
    # ============================================

    @staticmethod
    def get_invoice_serials(invoice_id):
        """
        Obtiene todos los seriales vendidos en una factura.

        Args:
            invoice_id: ID de la factura

        Returns:
            list: Lista de seriales con información de la venta
        """
        from app.models.invoice import Invoice

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return []

        serials = []

        for item in invoice.items.all():
            for item_serial in item.sold_serials.all():
                serial = item_serial.serial
                serials.append({
                    'serial_number': serial.serial_number,
                    'serial_id': serial.id,
                    'laptop_sku': serial.laptop.sku if serial.laptop else None,
                    'laptop_name': serial.laptop.display_name if serial.laptop else None,
                    'sale_price': float(item_serial.unit_sale_price) if item_serial.unit_sale_price else None,
                    'item_description': item.description,
                    'warranty_end': serial.warranty_end.isoformat() if serial.warranty_end else None,
                })

        return serials

    @staticmethod
    def find_serial_sale(serial_number):
        """
        Busca en qué factura se vendió un serial.

        Args:
            serial_number: Número de serie a buscar

        Returns:
            dict or None: Información de la venta
        """
        serial = SerialService.find_by_serial(serial_number)

        if not serial:
            return None

        sale_info = SerialService.get_serial_sale_info(serial.id)

        if sale_info:
            return {
                'serial': serial.to_dict(),
                'sale': sale_info
            }

        return {
            'serial': serial.to_dict(),
            'sale': None,
            'message': 'Serial encontrado pero no ha sido vendido'
        }

    # ============================================
    # REPORTES
    # ============================================

    @staticmethod
    def get_sales_with_serials_report(start_date=None, end_date=None):
        """
        Genera un reporte de ventas con seriales.

        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)

        Returns:
            dict: Reporte con estadísticas y detalle
        """
        from app.models.invoice import Invoice

        query = Invoice.query.filter(Invoice.status.in_(['confirmed', 'paid']))

        if start_date:
            query = query.filter(Invoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(Invoice.invoice_date <= end_date)

        invoices = query.order_by(Invoice.invoice_date.desc()).all()

        report = {
            'total_invoices': len(invoices),
            'total_serials_sold': 0,
            'invoices': []
        }

        for invoice in invoices:
            serials = InvoiceInventoryServiceWithSerials.get_invoice_serials(invoice.id)

            invoice_data = {
                'invoice_number': invoice.invoice_number,
                'date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                'customer': invoice.customer.full_name if invoice.customer else None,
                'total': float(invoice.total) if invoice.total else 0,
                'serials_count': len(serials),
                'serials': serials
            }

            report['invoices'].append(invoice_data)
            report['total_serials_sold'] += len(serials)

        return report

    # ============================================
    # MÉTODOS DE COMPATIBILIDAD PARA invoices.py
    # ============================================

    @staticmethod
    def get_inventory_summary_for_invoice(invoice):
        """
        Obtiene un resumen de inventario para una factura.
        Método de compatibilidad para invoices.py.

        Args:
            invoice: Objeto Invoice

        Returns:
            dict: Resumen de inventario
        """
        has_laptops = any(item.item_type == 'laptop' for item in invoice.items.all())
        total_units = sum(item.quantity for item in invoice.items.all() if item.item_type == 'laptop')

        return {
            'has_laptops': has_laptops,
            'total_units': total_units
        }

    @staticmethod
    def check_invoice_items_availability(invoice):
        """
        Verifica la disponibilidad de los items de una factura.
        Método de compatibilidad para invoices.py.

        Args:
            invoice: Objeto Invoice

        Returns:
            dict: Resultado de la verificación
        """
        # Por defecto, asumimos que está disponible
        # La validación real se hace en validate_stock_for_invoice_items
        return {
            'can_process': True,
            'unavailable_items': [],
            'warnings': []
        }


# ============================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================

# Mantener compatibilidad con código existente
class InvoiceInventoryService(InvoiceInventoryServiceWithSerials):
    """Alias para compatibilidad con código existente"""

    @staticmethod
    def validate_stock_for_invoice_items(items_data):
        """Versión compatible sin requerir seriales"""
        valid, error, warnings = InvoiceInventoryServiceWithSerials.validate_stock_for_invoice_items(
            items_data,
            require_serials=False
        )
        return valid, error

    @staticmethod
    def update_inventory_for_invoice(invoice, action='subtract'):
        """Versión compatible para actualizar inventario"""
        if action == 'subtract':
            success, result = InvoiceInventoryServiceWithSerials.process_sale_with_serials(
                invoice,
                [],  # Sin datos de seriales específicos
                user_id=None
            )
        else:
            success, result = InvoiceInventoryServiceWithSerials.reverse_sale_with_serials(
                invoice,
                user_id=None
            )

        if success:
            return True, None
        return False, result