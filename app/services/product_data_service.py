# -*- coding: utf-8 -*-
# ============================================
# SERVICIO DE GESTIÓN DE DATOS DE PRODUCTO
# ============================================
# Implementa el patrón PIM (Product Information Management)
# para la gestión centralizada de datos de productos.
#
# Características:
# - Importación desde Icecat
# - Entrada manual de datos
# - Merge inteligente de datos
# - Tracking de origen de campos
# - Descarga de imágenes de Icecat
# - Validación y normalización de datos

import os
import re
import logging
import hashlib
import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlparse

from app import db
from app.models.laptop import (
    Laptop, LaptopImage, LaptopTechnicalSpecs, IcecatProductData,
    Brand, LaptopModel, Processor, OperatingSystem, Screen,
    GraphicsCard, Storage, Ram, Store, Location, Supplier,
    DataSource, ProductCondition, ProductCategory
)
from app.services.icecat_service import get_icecat_service, IcecatProduct
from app.services.sku_service import SKUService

logger = logging.getLogger(__name__)


class ProductDataService:
    """
    Servicio central para la gestión de datos de productos.
    
    Implementa las mejores prácticas de PIM:
    - Centralización de datos
    - Validación y normalización
    - Tracking de origen
    - Enriquecimiento de datos
    """
    
    # Directorio para almacenar imágenes descargadas de Icecat
    ICECAT_IMAGES_DIR = 'static/uploads/icecat'
    
    def __init__(self):
        self.icecat_service = get_icecat_service()
        self.sku_service = SKUService()
    
    # =========================================
    # BÚSQUEDA EN ICECAT
    # =========================================
    
    def search_icecat_by_gtin(self, gtin: str, language: str = 'ES') -> Tuple[bool, Any]:
        """
        Busca un producto en Icecat por GTIN (EAN/UPC).
        
        Args:
            gtin: Código GTIN/EAN/UPC
            language: Código de idioma
            
        Returns:
            Tuple (success, IcecatProduct o mensaje de error)
        """
        return self.icecat_service.search_by_gtin(gtin, language)
    
    def search_icecat_by_brand_code(self, brand: str, product_code: str, 
                                     language: str = 'ES') -> Tuple[bool, Any]:
        """
        Busca un producto en Icecat por marca y código de producto.
        
        Args:
            brand: Nombre de la marca
            product_code: Part Number del fabricante
            language: Código de idioma
            
        Returns:
            Tuple (success, IcecatProduct o mensaje de error)
        """
        return self.icecat_service.search_by_brand_code(brand, product_code, language)
    
    # =========================================
    # IMPORTACIÓN DESDE ICECAT
    # =========================================
    
    def import_from_icecat(self, icecat_product: IcecatProduct, 
                           auto_download_images: bool = True) -> Tuple[bool, Any]:
        """
        Importa un producto desde Icecat y crea los registros necesarios.
        
        Este método:
        1. Verifica si ya existe en la base de datos
        2. Crea el registro IcecatProductData
        3. Prepara los datos para el formulario de edición
        
        Args:
            icecat_product: Producto parseado de Icecat
            auto_download_images: Si descargar las imágenes automáticamente
            
        Returns:
            Tuple (success, datos preparados para formulario o error)
        """
        try:
            # Verificar si ya existe un registro de Icecat con este ID
            existing = IcecatProductData.query.filter_by(
                icecat_id=icecat_product.icecat_id
            ).first()
            
            if existing:
                logger.info(f"Producto Icecat {icecat_product.icecat_id} ya existe, actualizando...")
                icecat_data = self._update_icecat_data(existing, icecat_product)
            else:
                logger.info(f"Creando nuevo registro Icecat para ID {icecat_product.icecat_id}")
                icecat_data = IcecatProductData.create_from_icecat_product(icecat_product)
                db.session.add(icecat_data)
            
            db.session.flush()  # Obtener el ID sin commit
            
            # Preparar datos para el formulario
            form_data = self._prepare_form_data_from_icecat(icecat_data, icecat_product)
            
            db.session.commit()
            
            return True, {
                'icecat_data_id': icecat_data.id,
                'form_data': form_data,
                'images': icecat_data.images_json,
                'specifications': icecat_data.feature_groups_json,
                'raw_extracted': {
                    'processor': icecat_data.extracted_processor,
                    'ram': icecat_data.extracted_ram,
                    'storage': icecat_data.extracted_storage,
                    'screen': icecat_data.extracted_screen,
                    'graphics': icecat_data.extracted_graphics,
                    'os': icecat_data.extracted_os,
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importando producto de Icecat: {e}", exc_info=True)
            return False, str(e)
    
    def _update_icecat_data(self, existing: IcecatProductData, 
                           icecat_product: IcecatProduct) -> IcecatProductData:
        """Actualiza un registro existente de Icecat"""
        # Actualizar campos principales
        existing.product_name = icecat_product.product_name
        existing.title = icecat_product.title
        existing.short_description = icecat_product.short_description or icecat_product.summary_short
        existing.long_description_html = icecat_product.long_description
        existing.summary_short = icecat_product.summary_short
        existing.summary_long = icecat_product.summary_long
        
        # Actualizar especificaciones
        specs = {}
        for feature in icecat_product.features:
            specs[feature.name] = {
                'value': feature.value,
                'group': feature.group,
                'measure': feature.measure
            }
        existing.specifications_json = specs
        existing.feature_groups_json = icecat_product.feature_groups
        
        # Actualizar imágenes
        images = []
        if icecat_product.main_image:
            images.append({
                'url': icecat_product.main_image.url,
                'thumb_url': icecat_product.main_image.thumb_url,
                'is_main': True,
                'position': 0
            })
        for img in icecat_product.gallery:
            images.append({
                'url': img.url,
                'thumb_url': img.thumb_url,
                'is_main': img.is_main,
                'position': img.position
            })
        existing.images_json = images
        existing.main_image_url = icecat_product.main_image.url if icecat_product.main_image else None
        
        # Actualizar timestamp
        existing.last_icecat_update = datetime.utcnow()
        existing.raw_response_json = icecat_product.raw_data
        
        # Re-extraer especificaciones
        existing._extract_specs_from_features(icecat_product.features)
        
        return existing
    
    def _prepare_form_data_from_icecat(self, icecat_data: IcecatProductData, 
                                        icecat_product: IcecatProduct) -> Dict[str, Any]:
        """
        Prepara los datos de Icecat para pre-poblar el formulario.
        El usuario puede ajustar estos valores antes de guardar.
        """
        # Obtener o crear marca
        brand = Brand.get_or_create_from_icecat(
            brand_name=icecat_data.brand_name,
            icecat_brand_id=icecat_data.brand_id_icecat
        )
        
        # Extraer nombre del modelo del título
        model_name = self._extract_model_name(
            icecat_data.title, 
            icecat_data.brand_name
        )
        
        # Obtener o crear modelo
        model = LaptopModel.get_or_create(model_name)
        model.brand_id = brand.id
        
        # Obtener o crear componentes
        processor = self._get_or_create_processor(icecat_data.extracted_processor)
        ram = self._get_or_create_ram(icecat_data.extracted_ram)
        storage = self._get_or_create_storage(icecat_data.extracted_storage)
        screen = self._get_or_create_screen(icecat_data.extracted_screen)
        graphics = self._get_or_create_graphics(icecat_data.extracted_graphics)
        os = self._get_or_create_os(icecat_data.extracted_os)
        
        db.session.flush()
        
        return {
            # Identificadores
            'icecat_data_id': icecat_data.id,
            'gtin': icecat_data.icecat_gtin,
            'mpn': icecat_data.product_code,
            
            # Marketing
            'display_name': icecat_data.title or icecat_data.product_name,
            'short_description': self._clean_html(icecat_data.short_description)[:500] if icecat_data.short_description else '',
            'long_description_html': icecat_data.long_description_html,
            
            # Relaciones
            'brand_id': brand.id,
            'brand_name': brand.name,
            'model_id': model.id,
            'model_name': model.name,
            'processor_id': processor.id if processor else None,
            'processor_name': processor.name if processor else icecat_data.extracted_processor,
            'ram_id': ram.id if ram else None,
            'ram_name': ram.name if ram else icecat_data.extracted_ram,
            'storage_id': storage.id if storage else None,
            'storage_name': storage.name if storage else icecat_data.extracted_storage,
            'screen_id': screen.id if screen else None,
            'screen_name': screen.name if screen else icecat_data.extracted_screen,
            'graphics_card_id': graphics.id if graphics else None,
            'graphics_card_name': graphics.name if graphics else icecat_data.extracted_graphics,
            'os_id': os.id if os else None,
            'os_name': os.name if os else icecat_data.extracted_os,
            
            # Dimensiones (extraídas)
            'weight_kg': float(icecat_data.extracted_weight_kg) if icecat_data.extracted_weight_kg else None,
            'battery_wh': float(icecat_data.extracted_battery_wh) if icecat_data.extracted_battery_wh else None,
            
            # Categoría sugerida
            'category': self._suggest_category(icecat_data),
            
            # Imágenes disponibles
            'available_images': icecat_data.images_json,
            'main_image_url': icecat_data.main_image_url,
            
            # Especificaciones completas
            'all_specifications': icecat_data.feature_groups_json,
            
            # Warranty
            'warranty_info': icecat_data.warranty_info,
        }
    
    # =========================================
    # CREACIÓN/ACTUALIZACIÓN DE LAPTOP
    # =========================================
    
    def create_laptop(self, form_data: Dict[str, Any], 
                      icecat_data_id: Optional[int] = None,
                      selected_images: Optional[List[Dict]] = None,
                      user_id: Optional[int] = None) -> Tuple[bool, Any]:
        """
        Crea un nuevo laptop en el inventario.
        
        Puede ser:
        - Desde Icecat (con icecat_data_id)
        - Manual (sin icecat_data_id)
        
        Args:
            form_data: Datos del formulario
            icecat_data_id: ID del registro de Icecat (si aplica)
            selected_images: Imágenes seleccionadas (URLs o archivos)
            user_id: ID del usuario que crea
            
        Returns:
            Tuple (success, Laptop creado o mensaje de error)
        """
        try:
            # Determinar origen de datos
            data_source = DataSource.ICECAT.value if icecat_data_id else DataSource.MANUAL.value
            
            # Generar SKU
            brand = Brand.query.get(form_data.get('brand_id'))
            sku = self.sku_service.generate_sku(
                brand=brand.name if brand else 'GEN',
                category=form_data.get('category', 'laptop')
            )
            
            # Generar slug
            slug = self._generate_slug(form_data.get('display_name', ''), sku)
            
            # Crear laptop
            laptop = Laptop(
                sku=sku,
                slug=slug,
                icecat_data_id=icecat_data_id,
                gtin=form_data.get('gtin'),
                mpn=form_data.get('mpn'),
                data_source=data_source,
                
                # Marketing
                display_name=form_data.get('display_name'),
                short_description=form_data.get('short_description'),
                long_description_html=form_data.get('long_description_html'),
                is_published=form_data.get('is_published', False),
                is_featured=form_data.get('is_featured', False),
                seo_title=form_data.get('seo_title'),
                seo_description=form_data.get('seo_description'),
                
                # Relaciones
                brand_id=form_data.get('brand_id'),
                model_id=form_data.get('model_id'),
                processor_id=form_data.get('processor_id'),
                os_id=form_data.get('os_id'),
                screen_id=form_data.get('screen_id'),
                graphics_card_id=form_data.get('graphics_card_id'),
                storage_id=form_data.get('storage_id'),
                ram_id=form_data.get('ram_id'),
                store_id=form_data.get('store_id'),
                location_id=form_data.get('location_id'),
                supplier_id=form_data.get('supplier_id'),
                created_by_id=user_id,
                
                # Técnicos
                npu=form_data.get('npu', False),
                storage_upgradeable=form_data.get('storage_upgradeable', False),
                ram_upgradeable=form_data.get('ram_upgradeable', False),
                keyboard_layout=form_data.get('keyboard_layout', 'US'),
                keyboard_backlit=form_data.get('keyboard_backlit', True),
                fingerprint_reader=form_data.get('fingerprint_reader', False),
                ir_camera=form_data.get('ir_camera', False),
                connectivity_ports=form_data.get('connectivity_ports', {}),
                wireless_connectivity=form_data.get('wireless_connectivity', {}),
                
                # Dimensiones
                weight_kg=form_data.get('weight_kg'),
                width_mm=form_data.get('width_mm'),
                depth_mm=form_data.get('depth_mm'),
                height_mm=form_data.get('height_mm'),
                battery_wh=form_data.get('battery_wh'),
                battery_cells=form_data.get('battery_cells'),
                color=form_data.get('color'),
                chassis_material=form_data.get('chassis_material'),
                
                # Estado
                category=form_data.get('category', ProductCategory.LAPTOP.value),
                condition=form_data.get('condition', ProductCondition.USED.value),
                warranty_months=form_data.get('warranty_months'),
                warranty_type=form_data.get('warranty_type'),
                
                # Financieros
                purchase_cost=Decimal(str(form_data.get('purchase_cost', 0))),
                sale_price=Decimal(str(form_data.get('sale_price', 0))),
                discount_price=Decimal(str(form_data.get('discount_price', 0))) if form_data.get('discount_price') else None,
                tax_percent=Decimal(str(form_data.get('tax_percent', 0))),
                msrp=Decimal(str(form_data.get('msrp', 0))) if form_data.get('msrp') else None,
                currency=form_data.get('currency', 'DOP'),
                
                # Inventario
                quantity=form_data.get('quantity', 1),
                reserved_quantity=form_data.get('reserved_quantity', 0),
                min_alert=form_data.get('min_alert', 1),
                
                # Notas
                internal_notes=form_data.get('internal_notes'),
            )
            
            db.session.add(laptop)
            db.session.flush()
            
            # Procesar imágenes seleccionadas
            if selected_images:
                self._process_images(laptop.id, selected_images, icecat_data_id)
            
            # Guardar especificaciones técnicas adicionales
            if form_data.get('technical_specs'):
                self._save_technical_specs(laptop.id, form_data['technical_specs'])
            
            # Registrar campos modificados si viene de Icecat
            if icecat_data_id:
                self._track_modified_fields(laptop, form_data, icecat_data_id)
            
            db.session.commit()
            logger.info(f"Laptop creado exitosamente: {laptop.sku}")
            
            return True, laptop
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creando laptop: {e}", exc_info=True)
            return False, str(e)
    
    def update_laptop(self, laptop_id: int, form_data: Dict[str, Any],
                      selected_images: Optional[List[Dict]] = None) -> Tuple[bool, Any]:
        """
        Actualiza un laptop existente.
        
        Si el laptop viene de Icecat, rastrea qué campos fueron modificados.
        """
        try:
            laptop = Laptop.query.get(laptop_id)
            if not laptop:
                return False, "Laptop no encontrado"
            
            # Campos a actualizar
            update_fields = [
                'display_name', 'short_description', 'long_description_html',
                'is_published', 'is_featured', 'seo_title', 'seo_description',
                'brand_id', 'model_id', 'processor_id', 'os_id', 'screen_id',
                'graphics_card_id', 'storage_id', 'ram_id', 'store_id',
                'location_id', 'supplier_id', 'npu', 'storage_upgradeable',
                'ram_upgradeable', 'keyboard_layout', 'keyboard_backlit',
                'fingerprint_reader', 'ir_camera', 'connectivity_ports',
                'wireless_connectivity', 'weight_kg', 'width_mm', 'depth_mm',
                'height_mm', 'battery_wh', 'battery_cells', 'color',
                'chassis_material', 'category', 'condition', 'warranty_months',
                'warranty_type', 'purchase_cost', 'sale_price', 'discount_price',
                'tax_percent', 'msrp', 'currency', 'quantity', 'reserved_quantity',
                'min_alert', 'internal_notes', 'gtin', 'mpn'
            ]
            
            for field in update_fields:
                if field in form_data:
                    old_value = getattr(laptop, field)
                    new_value = form_data[field]
                    
                    # Convertir a Decimal si es necesario
                    if field in ['purchase_cost', 'sale_price', 'discount_price', 'tax_percent', 'msrp']:
                        if new_value is not None and new_value != '':
                            new_value = Decimal(str(new_value))
                        elif field in ['discount_price', 'msrp']:
                            new_value = None
                        else:
                            new_value = Decimal('0')
                    
                    if old_value != new_value:
                        setattr(laptop, field, new_value)
                        
                        # Rastrear modificación si viene de Icecat
                        if laptop.is_from_icecat:
                            laptop.mark_field_modified(field, old_value)
            
            # Actualizar slug si cambió el nombre
            if 'display_name' in form_data:
                laptop.slug = self._generate_slug(form_data['display_name'], laptop.sku)
            
            # Actualizar imágenes si se proporcionaron
            if selected_images is not None:
                # Eliminar imágenes existentes
                LaptopImage.query.filter_by(laptop_id=laptop_id).delete()
                self._process_images(laptop_id, selected_images, laptop.icecat_data_id)
            
            # Actualizar especificaciones técnicas
            if form_data.get('technical_specs'):
                LaptopTechnicalSpecs.query.filter_by(laptop_id=laptop_id).delete()
                self._save_technical_specs(laptop_id, form_data['technical_specs'])
            
            db.session.commit()
            logger.info(f"Laptop actualizado: {laptop.sku}")
            
            return True, laptop
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error actualizando laptop: {e}", exc_info=True)
            return False, str(e)
    
    def sync_with_icecat(self, laptop_id: int, 
                         update_modified: bool = False) -> Tuple[bool, str]:
        """
        Sincroniza un laptop con la última información de Icecat.
        
        Args:
            laptop_id: ID del laptop
            update_modified: Si True, sobrescribe campos modificados por el usuario
            
        Returns:
            Tuple (success, mensaje)
        """
        try:
            laptop = Laptop.query.get(laptop_id)
            if not laptop or not laptop.icecat_data:
                return False, "Laptop no tiene datos de Icecat asociados"
            
            # Buscar en Icecat
            success, result = self.icecat_service.search_by_icecat_id(
                laptop.icecat_data.icecat_id
            )
            
            if not success:
                return False, f"Error consultando Icecat: {result}"
            
            # Actualizar registro de Icecat
            icecat_data = self._update_icecat_data(laptop.icecat_data, result)
            
            # Actualizar campos del laptop (solo los no modificados)
            updated_fields = []
            form_data = self._prepare_form_data_from_icecat(icecat_data, result)
            
            fields_to_sync = [
                ('display_name', 'display_name'),
                ('short_description', 'short_description'),
                ('long_description_html', 'long_description_html'),
            ]
            
            for laptop_field, form_field in fields_to_sync:
                # Solo actualizar si no fue modificado o si update_modified es True
                if update_modified or laptop_field not in (laptop.modified_fields_json or {}):
                    if form_data.get(form_field):
                        setattr(laptop, laptop_field, form_data[form_field])
                        updated_fields.append(laptop_field)
            
            laptop.last_icecat_sync = datetime.utcnow()
            
            db.session.commit()
            
            return True, f"Sincronizado. Campos actualizados: {', '.join(updated_fields) or 'ninguno'}"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error sincronizando con Icecat: {e}", exc_info=True)
            return False, str(e)
    
    # =========================================
    # PROCESAMIENTO DE IMÁGENES
    # =========================================
    
    def _process_images(self, laptop_id: int, images: List[Dict], 
                        icecat_data_id: Optional[int] = None):
        """
        Procesa y guarda las imágenes del laptop.
        
        Soporta:
        - Imágenes remotas (URLs de Icecat)
        - Imágenes locales (subidas)
        """
        for idx, img_data in enumerate(images):
            image = LaptopImage(
                laptop_id=laptop_id,
                position=idx,
                is_cover=(idx == 0 or img_data.get('is_cover', False)),
                ordering=idx,
            )
            
            if img_data.get('is_remote', False) or img_data.get('url'):
                # Imagen remota (de Icecat)
                image.is_remote = True
                image.image_url = img_data.get('url')
                image.thumb_url = img_data.get('thumb_url')
                image.medium_url = img_data.get('medium_url')
                image.source = 'icecat'
                image.source_url = img_data.get('url')
            elif img_data.get('path'):
                # Imagen local
                image.is_remote = False
                image.image_path = img_data.get('path')
                image.source = 'manual'
            
            # Metadatos
            image.alt_text = img_data.get('alt_text') or f"Imagen {idx + 1}"
            image.width = img_data.get('width')
            image.height = img_data.get('height')
            
            db.session.add(image)
    
    def download_icecat_image(self, image_url: str, laptop_id: int) -> Optional[str]:
        """
        Descarga una imagen de Icecat y la guarda localmente.
        
        Args:
            image_url: URL de la imagen en Icecat
            laptop_id: ID del laptop
            
        Returns:
            Ruta local de la imagen o None si falla
        """
        try:
            # Crear directorio si no existe
            upload_dir = os.path.join('app', self.ICECAT_IMAGES_DIR, str(laptop_id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar nombre de archivo
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            parsed = urlparse(image_url)
            ext = os.path.splitext(parsed.path)[1] or '.jpg'
            filename = f"icecat_{url_hash}{ext}"
            filepath = os.path.join(upload_dir, filename)
            
            # Descargar imagen
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Guardar
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Retornar ruta relativa
            return os.path.join(self.ICECAT_IMAGES_DIR, str(laptop_id), filename)
            
        except Exception as e:
            logger.error(f"Error descargando imagen de Icecat: {e}")
            return None
    
    # =========================================
    # HELPERS DE CATÁLOGOS
    # =========================================
    
    def _get_or_create_processor(self, processor_name: Optional[str]) -> Optional[Processor]:
        """Obtiene o crea un procesador desde el nombre"""
        if not processor_name:
            return None
        
        processor_name = processor_name.strip()
        processor = Processor.query.filter(
            db.func.lower(Processor.name) == db.func.lower(processor_name)
        ).first()
        
        if not processor:
            # Intentar extraer información del nombre
            specs = self._parse_processor_name(processor_name)
            processor = Processor(name=processor_name, is_active=True, **specs)
            db.session.add(processor)
        
        return processor
    
    def _get_or_create_ram(self, ram_name: Optional[str]) -> Optional[Ram]:
        """Obtiene o crea una RAM desde el nombre"""
        if not ram_name:
            return None
        
        ram_name = ram_name.strip()
        ram = Ram.query.filter(
            db.func.lower(Ram.name) == db.func.lower(ram_name)
        ).first()
        
        if not ram:
            specs = self._parse_ram_name(ram_name)
            ram = Ram(name=ram_name, is_active=True, **specs)
            db.session.add(ram)
        
        return ram
    
    def _get_or_create_storage(self, storage_name: Optional[str]) -> Optional[Storage]:
        """Obtiene o crea un almacenamiento desde el nombre"""
        if not storage_name:
            return None
        
        storage_name = storage_name.strip()
        storage = Storage.query.filter(
            db.func.lower(Storage.name) == db.func.lower(storage_name)
        ).first()
        
        if not storage:
            specs = self._parse_storage_name(storage_name)
            storage = Storage(name=storage_name, is_active=True, **specs)
            db.session.add(storage)
        
        return storage
    
    def _get_or_create_screen(self, screen_name: Optional[str]) -> Optional[Screen]:
        """Obtiene o crea una pantalla desde el nombre"""
        if not screen_name:
            return None
        
        screen_name = screen_name.strip()
        screen = Screen.query.filter(
            db.func.lower(Screen.name) == db.func.lower(screen_name)
        ).first()
        
        if not screen:
            specs = self._parse_screen_name(screen_name)
            screen = Screen(name=screen_name, is_active=True, **specs)
            db.session.add(screen)
        
        return screen
    
    def _get_or_create_graphics(self, graphics_name: Optional[str]) -> Optional[GraphicsCard]:
        """Obtiene o crea una tarjeta gráfica desde el nombre"""
        if not graphics_name:
            return None
        
        graphics_name = graphics_name.strip()
        graphics = GraphicsCard.query.filter(
            db.func.lower(GraphicsCard.name) == db.func.lower(graphics_name)
        ).first()
        
        if not graphics:
            specs = self._parse_graphics_name(graphics_name)
            graphics = GraphicsCard(name=graphics_name, is_active=True, **specs)
            db.session.add(graphics)
        
        return graphics
    
    def _get_or_create_os(self, os_name: Optional[str]) -> Optional[OperatingSystem]:
        """Obtiene o crea un sistema operativo desde el nombre"""
        if not os_name:
            return None
        
        os_name = os_name.strip()
        os = OperatingSystem.query.filter(
            db.func.lower(OperatingSystem.name) == db.func.lower(os_name)
        ).first()
        
        if not os:
            os = OperatingSystem(name=os_name, is_active=True)
            db.session.add(os)
        
        return os
    
    # =========================================
    # PARSERS DE ESPECIFICACIONES
    # =========================================
    
    def _parse_processor_name(self, name: str) -> Dict[str, Any]:
        """Extrae especificaciones del nombre del procesador"""
        specs = {}
        name_lower = name.lower()
        
        # Detectar fabricante
        if 'intel' in name_lower:
            specs['manufacturer'] = 'Intel'
            if 'core' in name_lower:
                specs['family'] = 'Core'
        elif 'amd' in name_lower:
            specs['manufacturer'] = 'AMD'
            if 'ryzen' in name_lower:
                specs['family'] = 'Ryzen'
        elif 'apple' in name_lower or 'm1' in name_lower or 'm2' in name_lower or 'm3' in name_lower:
            specs['manufacturer'] = 'Apple'
        
        # Extraer número de núcleos
        cores_match = re.search(r'(\d+)[- ]?core', name_lower)
        if cores_match:
            specs['cores'] = int(cores_match.group(1))
        
        return specs
    
    def _parse_ram_name(self, name: str) -> Dict[str, Any]:
        """Extrae especificaciones del nombre de la RAM"""
        specs = {}
        name_lower = name.lower()
        
        # Extraer capacidad
        capacity_match = re.search(r'(\d+)\s*gb', name_lower)
        if capacity_match:
            specs['capacity_gb'] = int(capacity_match.group(1))
        
        # Detectar tipo
        if 'ddr5' in name_lower:
            specs['ram_type'] = 'DDR5'
        elif 'ddr4' in name_lower:
            specs['ram_type'] = 'DDR4'
        elif 'lpddr5' in name_lower:
            specs['ram_type'] = 'LPDDR5'
        elif 'lpddr4' in name_lower:
            specs['ram_type'] = 'LPDDR4'
        
        # Extraer velocidad
        speed_match = re.search(r'(\d{4})\s*mhz', name_lower)
        if speed_match:
            specs['speed_mhz'] = int(speed_match.group(1))
        
        return specs
    
    def _parse_storage_name(self, name: str) -> Dict[str, Any]:
        """Extrae especificaciones del nombre del almacenamiento"""
        specs = {}
        name_lower = name.lower()
        
        # Extraer capacidad
        gb_match = re.search(r'(\d+)\s*gb', name_lower)
        tb_match = re.search(r'(\d+)\s*tb', name_lower)
        
        if tb_match:
            specs['capacity_gb'] = int(tb_match.group(1)) * 1024
        elif gb_match:
            specs['capacity_gb'] = int(gb_match.group(1))
        
        # Detectar tipo
        if 'ssd' in name_lower:
            specs['storage_type'] = 'SSD'
            if 'nvme' in name_lower or 'pcie' in name_lower:
                specs['interface'] = 'NVMe'
            elif 'sata' in name_lower:
                specs['interface'] = 'SATA'
        elif 'hdd' in name_lower:
            specs['storage_type'] = 'HDD'
        elif 'emmc' in name_lower:
            specs['storage_type'] = 'eMMC'
        
        return specs
    
    def _parse_screen_name(self, name: str) -> Dict[str, Any]:
        """Extrae especificaciones del nombre de la pantalla"""
        specs = {}
        name_lower = name.lower()
        
        # Extraer tamaño
        size_match = re.search(r'(\d+\.?\d*)\s*["\']?(?:inch|pulgadas)?', name_lower)
        if size_match:
            specs['size_inches'] = Decimal(size_match.group(1))
        
        # Detectar resolución
        if '4k' in name_lower or '3840' in name_lower or '2160' in name_lower:
            specs['resolution_name'] = '4K'
            specs['resolution_width'] = 3840
            specs['resolution_height'] = 2160
        elif 'qhd' in name_lower or '2k' in name_lower or '2560' in name_lower:
            specs['resolution_name'] = 'QHD'
            specs['resolution_width'] = 2560
            specs['resolution_height'] = 1440
        elif 'fhd' in name_lower or '1920' in name_lower or '1080' in name_lower:
            specs['resolution_name'] = 'FHD'
            specs['resolution_width'] = 1920
            specs['resolution_height'] = 1080
        
        # Detectar tipo de panel
        if 'oled' in name_lower:
            specs['panel_type'] = 'OLED'
        elif 'ips' in name_lower:
            specs['panel_type'] = 'IPS'
        elif 'va' in name_lower:
            specs['panel_type'] = 'VA'
        elif 'tn' in name_lower:
            specs['panel_type'] = 'TN'
        
        # Detectar táctil
        if 'touch' in name_lower or 'táctil' in name_lower:
            specs['touch_enabled'] = True
        
        return specs
    
    def _parse_graphics_name(self, name: str) -> Dict[str, Any]:
        """Extrae especificaciones del nombre de la tarjeta gráfica"""
        specs = {}
        name_lower = name.lower()
        
        # Detectar fabricante
        if 'nvidia' in name_lower or 'geforce' in name_lower or 'rtx' in name_lower or 'gtx' in name_lower:
            specs['manufacturer'] = 'NVIDIA'
            specs['is_integrated'] = False
        elif 'amd' in name_lower or 'radeon' in name_lower:
            specs['manufacturer'] = 'AMD'
            specs['is_integrated'] = False
        elif 'intel' in name_lower:
            specs['manufacturer'] = 'Intel'
            if 'iris' in name_lower or 'uhd' in name_lower or 'hd graphics' in name_lower:
                specs['is_integrated'] = True
        
        # Extraer VRAM
        vram_match = re.search(r'(\d+)\s*gb', name_lower)
        if vram_match and not specs.get('is_integrated', False):
            specs['vram_gb'] = int(vram_match.group(1))
        
        # Detectar Ray Tracing
        if 'rtx' in name_lower:
            specs['ray_tracing'] = True
        
        return specs
    
    # =========================================
    # UTILIDADES
    # =========================================
    
    def _extract_model_name(self, title: str, brand: str) -> str:
        """Extrae el nombre del modelo del título"""
        if not title:
            return "Modelo Genérico"
        
        # Remover la marca del título
        model = title.replace(brand, '').strip()
        
        # Limpiar caracteres especiales
        model = re.sub(r'^\s*[-–]\s*', '', model)
        
        # Tomar solo la primera parte (antes de la primera coma o guión largo)
        parts = re.split(r'[,–-]', model)
        if parts:
            model = parts[0].strip()
        
        return model[:100] if model else "Modelo Genérico"
    
    def _generate_slug(self, name: str, sku: str) -> str:
        """Genera un slug amigable para URLs"""
        import unicodedata
        
        # Normalizar y convertir a minúsculas
        slug = unicodedata.normalize('NFKD', name.lower())
        slug = slug.encode('ascii', 'ignore').decode('ascii')
        
        # Reemplazar espacios y caracteres especiales con guiones
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        
        # Agregar SKU para unicidad
        return f"{slug}-{sku.lower()}"[:255]
    
    def _clean_html(self, text: str) -> str:
        """Limpia tags HTML de un texto"""
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', ' ', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def _suggest_category(self, icecat_data: IcecatProductData) -> str:
        """Sugiere una categoría basada en los datos de Icecat"""
        category_lower = (icecat_data.category_name or '').lower()
        title_lower = (icecat_data.title or '').lower()
        
        if 'gaming' in category_lower or 'gaming' in title_lower:
            return ProductCategory.GAMING.value
        elif 'workstation' in category_lower or 'workstation' in title_lower:
            return ProductCategory.WORKSTATION.value
        elif 'ultrabook' in category_lower:
            return ProductCategory.ULTRABOOK.value
        elif 'chromebook' in category_lower:
            return ProductCategory.CHROMEBOOK.value
        elif '2-in-1' in category_lower or '2 in 1' in category_lower or 'convertible' in category_lower:
            return ProductCategory.TWO_IN_ONE.value
        
        return ProductCategory.LAPTOP.value
    
    def _save_technical_specs(self, laptop_id: int, specs: Dict[str, Dict[str, str]]):
        """
        Guarda especificaciones técnicas adicionales.
        
        Args:
            laptop_id: ID del laptop
            specs: Dict con formato {grupo: {nombre: valor, ...}, ...}
        """
        order = 0
        for group_name, group_specs in specs.items():
            for spec_name, spec_value in group_specs.items():
                if spec_value:  # Solo guardar si hay valor
                    spec = LaptopTechnicalSpecs(
                        laptop_id=laptop_id,
                        spec_group=group_name,
                        spec_name=spec_name,
                        spec_value=str(spec_value),
                        display_order=order,
                        source='icecat' if self else 'manual'
                    )
                    db.session.add(spec)
                    order += 1
    
    def _track_modified_fields(self, laptop: Laptop, form_data: Dict[str, Any], 
                               icecat_data_id: int):
        """
        Compara los datos del formulario con los originales de Icecat
        y registra qué campos fueron modificados.
        """
        icecat_data = IcecatProductData.query.get(icecat_data_id)
        if not icecat_data:
            return
        
        # Campos a comparar
        comparisons = {
            'display_name': icecat_data.title,
            'short_description': icecat_data.short_description,
            'long_description_html': icecat_data.long_description_html,
        }
        
        for field, original_value in comparisons.items():
            form_value = form_data.get(field)
            if form_value and form_value != original_value:
                laptop.mark_field_modified(field, original_value)


# Singleton del servicio
_product_data_service = None


def get_product_data_service() -> ProductDataService:
    """Obtiene la instancia singleton del servicio"""
    global _product_data_service
    if _product_data_service is None:
        _product_data_service = ProductDataService()
    return _product_data_service
