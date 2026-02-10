# -*- coding: utf-8 -*-
"""
Servicio para manejar la creación dinámica de catálogos
Actualizado al nuevo modelo de datos
"""
import re

from app import db
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
)


class CatalogService:
    """Servicio para gestión dinámica de catálogos"""

    @staticmethod
    def _get_or_create_generic(model, value, **extra_fields):
        """
        Método genérico para obtener o crear items de catálogo

        Args:
            model: Modelo de SQLAlchemy
            value: ID (int) o nombre (str)
            **extra_fields: Campos adicionales para el modelo

        Returns:
            int: ID del item, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        # Si es un ID existente
        if isinstance(value, int) and value > 0:
            return value

        # Si es un string (nuevo valor)
        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            # Buscar si ya existe (case-insensitive)
            existing = model.query.filter(
                db.func.lower(model.name) == name.lower()
            ).first()

            if existing:
                # Actualizar campos adicionales si no existen
                base_changed = False
                for key, val in extra_fields.items():
                    if hasattr(existing, key) and val and getattr(existing, key) != val:
                        setattr(existing, key, val)
                        base_changed = True
                if base_changed:
                    db.session.flush()
                return existing.id

            # Crear nuevo item
            extra_fields.pop('name', None)
            new_item = model(name=name, is_active=True, **extra_fields)
            db.session.add(new_item)
            db.session.flush()  # Para obtener el ID sin commit
            return new_item.id

        return None

    @staticmethod
    def get_or_create_brand(value):
        """
        Obtiene o crea una marca

        Args:
            value: ID (int) o nombre (str) de la marca

        Returns:
            int: ID de la marca, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Brand, value)

    @staticmethod
    def get_or_create_model(value, brand_id=None):
        """
        Obtiene o crea un modelo

        Args:
            value: ID (int) o nombre (str) del modelo
            brand_id: ID de la marca asociada

        Returns:
            int: ID del modelo, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        # Si es un ID existente
        if isinstance(value, int) and value > 0:
            return value

        # Si es un string (nuevo valor)
        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            # Buscar si ya existe con la misma marca
            query = LaptopModel.query.filter(
                db.func.lower(LaptopModel.name) == name.lower()
            )

            if brand_id:
                query = query.filter(LaptopModel.brand_id == brand_id)

            existing = query.first()

            if existing:
                return existing.id

            # Crear nuevo modelo
            new_model = LaptopModel(name=name, brand_id=brand_id, is_active=True)
            db.session.add(new_model)
            db.session.flush()
            return new_model.id

        return None

    @staticmethod
    def get_or_create_processor(family, generation=None, model=None, manufacturer=None, has_npu=False, **extra_fields):
        """
        Obtiene o crea un registro de generación de procesador con soporte técnico para NPU.

        Args:
            family: Familia del procesador (str)
            generation: Nombre de la generación (str)
            model: Modelo/Número (str)
            manufacturer: Fabricante (str, opcional)
            has_npu: Si tiene NPU para AI

        Returns:
            int: ID de la generación del procesador, o None
        """
        # La prioridad ahora es el campo generation para el catálogo
        if not generation and not family:
            return None

        # Si no hay generación, usamos la familia como nombre de catálogo
        cat_name = (generation or family).strip()
        if not cat_name:
            return None

        full_name = extra_fields.get('full_name')

        # Normalizar datos para los campos técnicos
        family = family.strip() if family else ""
        generation = generation.strip() if generation else ""
        model = model.strip() if model else ""
        manufacturer = manufacturer.strip() if manufacturer else ""

        # Inferir fabricante si falta
        if not manufacturer and family:
            fam_lower = family.lower()
            if 'intel' in fam_lower:
                manufacturer = 'Intel'
            elif 'amd' in fam_lower:
                manufacturer = 'AMD'
            elif 'apple' in fam_lower or fam_lower.startswith('m1') or fam_lower.startswith('m2') or fam_lower.startswith('m3'):
                manufacturer = 'Apple'
            elif 'snapdragon' in fam_lower or 'qualcomm' in fam_lower:
                manufacturer = 'Qualcomm'

        # Buscar si ya existe por NOMBRE (que ahora representa la generación)
        existing = Processor.query.filter(
            db.func.lower(Processor.name) == cat_name.lower()
        ).first()

        if existing:
            # Si existe, actualizamos has_npu si es True o full_name si falta
            changed = False
            if has_npu and not existing.has_npu:
                existing.has_npu = True
                changed = True
            if full_name and existing.full_name != full_name:
                existing.full_name = full_name
                changed = True
            
            if changed:
                db.session.flush()
            return existing.id

        # Crear nuevo registro de generación
        new_processor = Processor(
            name=cat_name,
            family=family,
            generation=generation,
            model_number=model,
            manufacturer=manufacturer,
            has_npu=has_npu,
            full_name=full_name,
            is_active=True
        )
        db.session.add(new_processor)
        db.session.flush()
        return new_processor.id

    @staticmethod
    def get_or_create_os(value):
        """
        Obtiene o crea un sistema operativo

        Args:
            value: ID (int) o nombre (str) del sistema operativo

        Returns:
            int: ID del sistema operativo, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(OperatingSystem, value)

    @staticmethod
    def get_or_create_screen(value=None, **fields):
        """
        Obtiene o crea una pantalla con campos técnicos
        """
        if not value and not fields:
            return None

        # Si es un ID, retornar tal cual
        if isinstance(value, int) and value > 0:
            return value

        # Asegurar que resolution se capture de value si viene ahí (ej: del scanner o seeder)
        resolution = fields.get('resolution')
        if not resolution and value:
            # Buscar patrones tipo 1920x1080 o 1920 x 1080
            match = re.search(r'(\d{3,4}\s*[xX]\s*\d{3,4})', str(value))
            if match:
                resolution = match.group(1).replace(' ', '').lower()
                fields['resolution'] = resolution

        # Intentar construir un nombre descriptivo si tenemos datos
        # Si value es la resolución, buscamos algo más visual (diag + hd + res)
        name = value
        if not name or (resolution and name == resolution):
            parts = []
            diag = fields.get('diagonal_inches')
            if diag: parts.append(f"{diag}\"")
            
            hd = fields.get('hd_type')
            if hd: parts.append(hd)
            elif resolution: parts.append(resolution)
            
            panel = fields.get('panel_type')
            if panel: parts.append(panel.replace('-Level', ''))
            
            refresh = fields.get('refresh_rate')
            if refresh and refresh > 60: parts.append(f"{refresh}Hz")
            
            if fields.get('touchscreen'): parts.append('Touch')
            
            name = ' '.join(parts) if parts else (resolution or value or 'Generic Screen')

        return CatalogService._get_or_create_generic(Screen, name, **fields)

    @staticmethod
    def get_or_create_graphics_card(value=None, **fields):
        """
        Obtiene o crea una tarjeta gráfica con campos técnicos
        """
        if not value and not fields:
            return None

        if isinstance(value, int) and value > 0:
            return value

        name = value
        if not name:
            parts = []
            if fields.get('brand'): parts.append(fields.get('brand'))
            if fields.get('name'): parts.append(fields.get('name')) # Nombre del modelo GPU
            elif fields.get('onboard_model'): parts.append(fields.get('onboard_model'))
            elif fields.get('discrete_model'): parts.append(fields.get('discrete_model'))
                
            if fields.get('memory_gb'): parts.append(f"{fields.get('memory_gb')}GB")
            name = ' '.join(parts) if parts else 'Generic GPU'

        return CatalogService._get_or_create_generic(GraphicsCard, name, **fields)

    @staticmethod
    def get_or_create_storage(value=None, **fields):
        """
        Obtiene o crea almacenamiento con campos técnicos
        """
        if not value and not fields:
            return None

        if isinstance(value, int) and value > 0:
            return value

        name = value
        if not name:
            parts = []
            if fields.get('capacity_gb'): parts.append(f"{fields.get('capacity_gb')}GB")
            if fields.get('media_type'): parts.append(fields.get('media_type'))
            if fields.get('nvme'): parts.append('NVMe')
            if fields.get('form_factor'): parts.append(fields.get('form_factor'))
            name = ' '.join(parts) if parts else 'Generic Storage'

        return CatalogService._get_or_create_generic(Storage, name, **fields)

    @staticmethod
    def get_or_create_ram(value=None, **fields):
        """
        Obtiene o crea RAM con campos técnicos
        """
        if not value and not fields:
            return None

        if isinstance(value, int) and value > 0:
            return value

        name = value
        if not name:
            parts = []
            if fields.get('capacity_gb'): parts.append(f"{fields.get('capacity_gb')}GB")
            if fields.get('ram_type'): parts.append(fields.get('ram_type'))
            if fields.get('speed_mhz'): parts.append(f"{fields.get('speed_mhz')}MHz")
            name = ' '.join(parts) if parts else 'Generic RAM'

        return CatalogService._get_or_create_generic(Ram, name, **fields)

    @staticmethod
    def get_or_create_store(value):
        """
        Obtiene o crea una tienda

        Args:
            value: ID (int) o nombre (str) de la tienda

        Returns:
            int: ID de la tienda, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Store, value)

    @staticmethod
    def get_or_create_location(value, store_id=None):
        """
        Obtiene o crea una ubicación

        Args:
            value: ID (int) o nombre (str) de la ubicación
            store_id: ID de la tienda asociada

        Returns:
            int: ID de la ubicación, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        # Si es un ID existente
        if isinstance(value, int) and value > 0:
            return value

        # Si es un string (nuevo valor)
        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            # Buscar si ya existe en la misma tienda
            query = Location.query.filter(
                db.func.lower(Location.name) == name.lower()
            )

            if store_id:
                query = query.filter(Location.store_id == store_id)

            existing = query.first()

            if existing:
                return existing.id

            # Crear nueva ubicación
            new_location = Location(name=name, store_id=store_id, is_active=True)
            db.session.add(new_location)
            db.session.flush()
            return new_location.id

        return None

    @staticmethod
    def get_or_create_supplier(value):
        """
        Obtiene o crea un proveedor

        Args:
            value: ID (int) o nombre (str) del proveedor

        Returns:
            int: ID del proveedor, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Supplier, value)

    @staticmethod
    def process_laptop_form_data(form_data):
        """
        Procesa todos los campos de catálogo del formulario
        Convierte strings a IDs (creando registros si es necesario)

        Args:
            form_data: Diccionario con los datos del formulario

        Returns:
            dict: Diccionario con los IDs procesados
        """
        processed_data = {}

        # Procesar marca primero (se necesita para el modelo)
        brand_id = CatalogService.get_or_create_brand(form_data.get('brand_id'))
        processed_data['brand_id'] = brand_id

        # Procesar modelo (puede necesitar brand_id)
        model_id = CatalogService.get_or_create_model(
            form_data.get('model_id'),
            brand_id
        )
        processed_data['model_id'] = model_id

        # Procesar procesador
        processed_data['processor_id'] = CatalogService.get_or_create_processor(
            family=form_data.get('processor_family'),
            generation=form_data.get('processor_generation'),
            model=form_data.get('processor_model'),
            manufacturer=form_data.get('processor_manufacturer'),
            full_name=form_data.get('processor_full_name')
        )

        processed_data['os_id'] = CatalogService.get_or_create_os(
            form_data.get('os_id')
        )

        # Procesar pantalla (con campos granulares)
        processed_data['screen_id'] = CatalogService.get_or_create_screen(
            value=form_data.get('screen_id'),
            diagonal_inches=form_data.get('screen_diagonal_inches'),
            resolution=form_data.get('screen_resolution'),
            hd_type=form_data.get('screen_hd_type'),
            panel_type=form_data.get('screen_panel_type'),
            refresh_rate=form_data.get('screen_refresh_rate'),
            touchscreen=form_data.get('screen_touchscreen_override'),
            full_name=form_data.get('screen_full_name')
        )

        # Procesar gráfica (con campos granulares)
        processed_data['graphics_card_id'] = CatalogService.get_or_create_graphics_card(
            value=form_data.get('graphics_card_id'),
            has_discrete_gpu=form_data.get('has_discrete_gpu'),
            discrete_brand=form_data.get('discrete_gpu_brand'),
            discrete_model=form_data.get('discrete_gpu_model'),
            discrete_memory_gb=form_data.get('discrete_gpu_memory_gb'),
            discrete_memory_type=form_data.get('discrete_gpu_memory_type'),
            onboard_brand=form_data.get('onboard_gpu_brand'),
            onboard_model=form_data.get('onboard_gpu_model'),
            onboard_family=form_data.get('onboard_gpu_family'),
            discrete_full_name=form_data.get('discrete_gpu_full_name'),
            onboard_full_name=form_data.get('onboard_gpu_full_name')
        )

        # Procesar almacenamiento (con campos granulares)
        processed_data['storage_id'] = CatalogService.get_or_create_storage(
            value=form_data.get('storage_id'),
            capacity_gb=form_data.get('storage_capacity'),
            media_type=form_data.get('storage_media'),
            nvme=form_data.get('storage_nvme'),
            form_factor=form_data.get('storage_form_factor'),
            full_name=form_data.get('storage_full_name')
        )

        # Procesar RAM (con campos granulares)
        processed_data['ram_id'] = CatalogService.get_or_create_ram(
            value=form_data.get('ram_id'),
            capacity_gb=form_data.get('ram_capacity'),
            ram_type=form_data.get('ram_type_detailed'), # Nota: mapped to detailed type
            speed_mhz=form_data.get('ram_speed_mhz'),
            transfer_rate=form_data.get('ram_transfer_rate'),
            full_name=form_data.get('ram_full_name')
        )

        # Procesar tienda primero (se necesita para ubicación)
        store_id = CatalogService.get_or_create_store(form_data.get('store_id'))
        processed_data['store_id'] = store_id

        # Procesar ubicación (puede necesitar store_id)
        location_id = CatalogService.get_or_create_location(
            form_data.get('location_id'),
            store_id
        )
        processed_data['location_id'] = location_id

        # Procesar proveedor
        processed_data['supplier_id'] = CatalogService.get_or_create_supplier(
            form_data.get('supplier_id')
        )

        return processed_data

    @staticmethod
    def get_catalog_stats():
        """
        Obtiene estadísticas de todos los catálogos

        Returns:
            dict: Diccionario con conteos de cada catálogo
        """
        return {
            'brands': Brand.query.filter_by(is_active=True).count(),
            'models': LaptopModel.query.filter_by(is_active=True).count(),
            'processors': Processor.query.filter_by(is_active=True).count(),
            'operating_systems': OperatingSystem.query.filter_by(is_active=True).count(),
            'screens': Screen.query.filter_by(is_active=True).count(),
            'graphics_cards': GraphicsCard.query.filter_by(is_active=True).count(),
            'storage': Storage.query.filter_by(is_active=True).count(),
            'ram': Ram.query.filter_by(is_active=True).count(),
            'stores': Store.query.filter_by(is_active=True).count(),
            'locations': Location.query.filter_by(is_active=True).count(),
            'suppliers': Supplier.query.filter_by(is_active=True).count()
        }

    @staticmethod
    def deactivate_item(model, item_id):
        """
        Desactiva un item de catálogo (soft delete)

        Args:
            model: Modelo de SQLAlchemy
            item_id: ID del item a desactivar

        Returns:
            bool: True si se desactivó exitosamente
        """
        item = model.query.get(item_id)
        if item:
            item.is_active = False
            db.session.commit()
            return True
        return False

    @staticmethod
    def reactivate_item(model, item_id):
        """
        Reactiva un item de catálogo

        Args:
            model: Modelo de SQLAlchemy
            item_id: ID del item a reactivar

        Returns:
            bool: True si se reactivó exitosamente
        """
        item = model.query.get(item_id)
        if item:
            item.is_active = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def merge_items(model, source_id, target_id, update_laptops=True):
        """
        Fusiona dos items de catálogo, moviendo todas las referencias
        del source al target y desactivando el source

        Args:
            model: Modelo de SQLAlchemy
            source_id: ID del item a fusionar (será desactivado)
            target_id: ID del item destino
            update_laptops: Si actualizar las laptops que referencian al source

        Returns:
            int: Número de laptops actualizadas
        """
        from app.models.laptop import Laptop

        source = model.query.get(source_id)
        target = model.query.get(target_id)

        if not source or not target:
            return 0

        updated_count = 0

        if update_laptops:
            # Determinar el campo de FK basado en el modelo
            field_mapping = {
                Brand: 'brand_id',
                LaptopModel: 'model_id',
                Processor: 'processor_id',
                OperatingSystem: 'os_id',
                Screen: 'screen_id',
                GraphicsCard: 'graphics_card_id',
                Storage: 'storage_id',
                Ram: 'ram_id',
                Store: 'store_id',
                Location: 'location_id',
                Supplier: 'supplier_id'
            }

            field_name = field_mapping.get(model)
            if field_name:
                # Actualizar todas las laptops que usan el source
                updated_count = Laptop.query.filter(
                    getattr(Laptop, field_name) == source_id
                ).update({field_name: target_id}, synchronize_session=False)

        # Desactivar el source
        source.is_active = False
        db.session.commit()

        return updated_count