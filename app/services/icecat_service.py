# -*- coding: utf-8 -*-
# ============================================
# SERVICIO DE INTEGRACIÓN CON ICECAT API
# ============================================
# Permite consultar productos desde el catálogo Icecat
# y mapear los datos al modelo de inventario
# 
# ACTUALIZADO: Lee configuración desde base de datos

import os
import logging
import requests
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from urllib.parse import quote

logger = logging.getLogger(__name__)


@dataclass
class IcecatConfig:
    """Configuración para el servicio de Icecat"""
    username: str
    api_token: Optional[str] = None
    content_token: Optional[str] = None
    base_url: str = "https://live.icecat.biz/api"
    default_language: str = "ES"
    timeout: int = 30
    enabled: bool = True


@dataclass
class IcecatImage:
    """Representa una imagen del producto de Icecat"""
    url: str
    thumb_url: Optional[str] = None
    low_url: Optional[str] = None
    medium_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
    is_main: bool = False
    position: int = 0
    image_type: Optional[str] = None


@dataclass
class IcecatFeature:
    """Representa una característica/especificación del producto"""
    name: str
    value: str
    group: str
    measure: Optional[str] = None
    feature_id: Optional[str] = None


@dataclass 
class IcecatProduct:
    """Representa un producto consultado desde Icecat"""
    icecat_id: int
    brand: str
    brand_id: Optional[str] = None
    product_code: str = ""
    product_name: str = ""
    title: str = ""
    category: str = ""
    category_id: Optional[str] = None
    gtin: Optional[str] = None
    gtins: List[str] = None
    short_description: str = ""
    long_description: str = ""
    summary_short: str = ""
    summary_long: str = ""
    main_image: Optional[IcecatImage] = None
    gallery: List[IcecatImage] = None
    features: List[IcecatFeature] = None
    feature_groups: Dict[str, List[IcecatFeature]] = None
    release_date: Optional[str] = None
    warranty_info: Optional[str] = None
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.gtins is None:
            self.gtins = []
        if self.gallery is None:
            self.gallery = []
        if self.features is None:
            self.features = []
        if self.feature_groups is None:
            self.feature_groups = {}


def get_icecat_config_from_db() -> IcecatConfig:
    """
    Obtiene la configuración de Icecat desde la base de datos.
    Si no existe, usa valores por defecto.
    """
    try:
        from app.models.system_setting import SystemSetting
        
        username = SystemSetting.get('icecat_username', 'openIcecat-live')
        api_token = SystemSetting.get('icecat_api_token', '')
        content_token = SystemSetting.get('icecat_content_token', '')
        language = SystemSetting.get('icecat_language', 'ES')
        enabled = SystemSetting.get('icecat_enabled', 'true').lower() == 'true'
        
        return IcecatConfig(
            username=username,
            api_token=api_token if api_token else None,
            content_token=content_token if content_token else None,
            default_language=language,
            enabled=enabled
        )
    except Exception as e:
        logger.warning(f"No se pudo leer configuración de Icecat desde DB: {e}")
        # Fallback a variables de entorno
        return IcecatConfig(
            username=os.environ.get('ICECAT_USERNAME', 'openIcecat-live'),
            api_token=os.environ.get('ICECAT_API_TOKEN'),
            content_token=os.environ.get('ICECAT_CONTENT_TOKEN'),
            default_language=os.environ.get('ICECAT_LANGUAGE', 'ES')
        )


class IcecatService:
    """
    Servicio para consultar productos desde el API de Icecat
    
    Documentación: https://iceclog.com/manual-for-icecat-json-product-requests/
    """
    
    def __init__(self, config: Optional[IcecatConfig] = None):
        """
        Inicializa el servicio con la configuración proporcionada,
        desde la base de datos, o desde variables de entorno.
        """
        if config:
            self.config = config
        else:
            self.config = get_icecat_config_from_db()
        
        self._session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configura la sesión HTTP con headers necesarios"""
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Luxera-Inventory/1.0'
        }
        
        if self.config.api_token:
            headers['api-token'] = self.config.api_token
        if self.config.content_token:
            headers['content-token'] = self.config.content_token
            
        self._session.headers.update(headers)
    
    def is_enabled(self) -> bool:
        """Verifica si el servicio de Icecat está habilitado"""
        return self.config.enabled
    
    def reload_config(self):
        """Recarga la configuración desde la base de datos"""
        self.config = get_icecat_config_from_db()
        self._setup_session()
    
    def search_by_gtin(self, gtin: str, language: Optional[str] = None) -> Tuple[bool, Any]:
        """
        Busca un producto por su código GTIN (EAN/UPC)
        
        Args:
            gtin: Código GTIN/EAN/UPC del producto
            language: Código de idioma (ES, EN, etc.)
            
        Returns:
            Tuple de (success, IcecatProduct o mensaje de error)
        """
        if not self.is_enabled():
            return False, "La integración con Icecat está deshabilitada"
        
        lang = language or self.config.default_language
        
        params = {
            'lang': lang,
            'shopname': self.config.username,
            'GTIN': gtin,
            'content': ''  # Contenido completo
        }
        
        return self._fetch_product(params)
    
    def search_by_brand_code(self, brand: str, product_code: str, 
                             language: Optional[str] = None) -> Tuple[bool, Any]:
        """
        Busca un producto por marca y código de producto
        
        Args:
            brand: Nombre de la marca (ej: "Dell", "HP", "Lenovo")
            product_code: Código/Part Number del producto
            language: Código de idioma
            
        Returns:
            Tuple de (success, IcecatProduct o mensaje de error)
        """
        if not self.is_enabled():
            return False, "La integración con Icecat está deshabilitada"
        
        lang = language or self.config.default_language
        
        params = {
            'lang': lang,
            'shopname': self.config.username,
            'Brand': brand,
            'ProductCode': quote(product_code, safe=''),
            'content': ''
        }
        
        return self._fetch_product(params)
    
    def search_by_icecat_id(self, icecat_id: int, 
                            language: Optional[str] = None) -> Tuple[bool, Any]:
        """
        Busca un producto por su ID interno de Icecat
        
        Args:
            icecat_id: ID único del producto en Icecat
            language: Código de idioma
            
        Returns:
            Tuple de (success, IcecatProduct o mensaje de error)
        """
        if not self.is_enabled():
            return False, "La integración con Icecat está deshabilitada"
        
        lang = language or self.config.default_language
        
        params = {
            'lang': lang,
            'shopname': self.config.username,
            'icecat_id': icecat_id,
            'content': ''
        }
        
        return self._fetch_product(params)
    
    def _fetch_product(self, params: Dict) -> Tuple[bool, Any]:
        """
        Realiza la consulta al API de Icecat
        
        Args:
            params: Parámetros de la consulta
            
        Returns:
            Tuple de (success, IcecatProduct o mensaje de error)
        """
        try:
            response = self._session.get(
                self.config.base_url,
                params=params,
                timeout=self.config.timeout
            )
            
            logger.info(f"Icecat API Response Status: {response.status_code}")
            logger.debug(f"Icecat API URL: {response.url}")
            
            if response.status_code != 200:
                return False, f"Error HTTP {response.status_code}: {response.text}"
            
            data = response.json()
            
            # Verificar si hay error en la respuesta
            if data.get('msg') != 'OK':
                error_msg = data.get('message', data.get('msg', 'Error desconocido'))
                status_code = data.get('statusCode', data.get('StatusCode', 0))
                return False, self._translate_error(status_code, error_msg)
            
            # Verificar si hay errores de contenido
            if data.get('data', {}).get('ContentErrors'):
                return False, data['data']['ContentErrors']
            
            # Parsear la respuesta
            product = self._parse_product(data.get('data', {}))
            return True, product
            
        except requests.Timeout:
            logger.error("Timeout al consultar Icecat API")
            return False, "Timeout: El servidor de Icecat no respondió a tiempo"
        except requests.RequestException as e:
            logger.error(f"Error de conexión con Icecat: {e}")
            return False, f"Error de conexión: {str(e)}"
        except Exception as e:
            logger.error(f"Error procesando respuesta de Icecat: {e}", exc_info=True)
            return False, f"Error procesando respuesta: {str(e)}"
    
    def _translate_error(self, status_code: int, message: str) -> str:
        """Traduce códigos de error de Icecat a mensajes amigables"""
        error_messages = {
            1: "Parámetros obligatorios faltantes (username, lang)",
            2: "Autenticación fallida - Verifica tu usuario y contraseña",
            3: "El idioma solicitado no está disponible para este producto",
            4: "Identificador de producto incorrecto (GTIN/Part Number no válido)",
            5: "IP no autorizada - Configura tu IP en el panel de Icecat",
            6: "Producto no encontrado en el catálogo Open Icecat",
            9: "Este producto requiere suscripción Full Icecat",
        }
        return error_messages.get(status_code, message)
    
    def _parse_product(self, data: Dict) -> IcecatProduct:
        """
        Parsea la respuesta JSON de Icecat a un objeto IcecatProduct
        """
        general_info = data.get('GeneralInfo', {})
        description = general_info.get('Description', {})
        summary = general_info.get('SummaryDescription', {})
        
        # Parsear imagen principal
        main_image = self._parse_main_image(data.get('Image', {}))
        
        # Parsear galería
        gallery = self._parse_gallery(data.get('Gallery', []))
        
        # Parsear características
        features, feature_groups = self._parse_features(data.get('FeaturesGroups', []))
        
        # Obtener GTINs
        gtins = general_info.get('GTIN', [])
        if isinstance(gtins, str):
            gtins = [gtins]
        
        # Obtener categoría
        category_info = general_info.get('Category', {})
        category_name = category_info.get('Name', {})
        if isinstance(category_name, dict):
            category_name = category_name.get('Value', '')
        
        return IcecatProduct(
            icecat_id=general_info.get('IcecatId', 0),
            brand=general_info.get('Brand', ''),
            brand_id=general_info.get('BrandID'),
            product_code=general_info.get('BrandPartCode', ''),
            product_name=general_info.get('ProductName', ''),
            title=general_info.get('Title', ''),
            category=category_name,
            category_id=category_info.get('CategoryID'),
            gtin=gtins[0] if gtins else None,
            gtins=gtins,
            short_description=description.get('MiddleDesc', ''),
            long_description=description.get('LongDesc', ''),
            summary_short=summary.get('ShortSummaryDescription', ''),
            summary_long=summary.get('LongSummaryDescription', ''),
            main_image=main_image,
            gallery=gallery,
            features=features,
            feature_groups=feature_groups,
            release_date=general_info.get('ReleaseDate'),
            warranty_info=description.get('WarrantyInfo'),
            raw_data=data
        )
    
    def _parse_main_image(self, image_data: Dict) -> Optional[IcecatImage]:
        """Parsea la imagen principal del producto"""
        if not image_data or not image_data.get('HighPic'):
            return None
        
        return IcecatImage(
            url=image_data.get('HighPic', ''),
            thumb_url=image_data.get('ThumbPic'),
            low_url=image_data.get('LowPic'),
            medium_url=image_data.get('Pic500x500'),
            width=int(image_data.get('HighPicWidth', 0)) if image_data.get('HighPicWidth') else None,
            height=int(image_data.get('HighPicHeight', 0)) if image_data.get('HighPicHeight') else None,
            size=int(image_data.get('HighPicSize', 0)) if image_data.get('HighPicSize') else None,
            is_main=True,
            position=0
        )
    
    def _parse_gallery(self, gallery_data: List[Dict]) -> List[IcecatImage]:
        """Parsea la galería de imágenes"""
        images = []
        
        for idx, img in enumerate(gallery_data):
            images.append(IcecatImage(
                url=img.get('Pic', ''),
                thumb_url=img.get('ThumbPic'),
                low_url=img.get('LowPic'),
                medium_url=img.get('Pic500x500'),
                width=int(img.get('PicWidth', 0)) if img.get('PicWidth') else None,
                height=int(img.get('PicHeight', 0)) if img.get('PicHeight') else None,
                size=int(img.get('Size', 0)) if img.get('Size') else None,
                is_main=img.get('IsMain') == 'Y',
                position=int(img.get('No', idx)) if img.get('No') else idx,
                image_type=img.get('Type')
            ))
        
        # Ordenar por posición
        images.sort(key=lambda x: x.position)
        return images
    
    def _parse_features(self, feature_groups_data: List[Dict]) -> Tuple[List[IcecatFeature], Dict]:
        """
        Parsea las características/especificaciones del producto
        
        Returns:
            Tuple de (lista plana de features, diccionario agrupado por grupo)
        """
        all_features = []
        grouped_features = {}
        
        for group_data in feature_groups_data:
            group_info = group_data.get('FeatureGroup', {})
            group_name_info = group_info.get('Name', {})
            
            if isinstance(group_name_info, dict):
                group_name = group_name_info.get('Value', 'Otros')
            else:
                group_name = str(group_name_info) if group_name_info else 'Otros'
            
            if group_name not in grouped_features:
                grouped_features[group_name] = []
            
            for feature_data in group_data.get('Features', []):
                feature_info = feature_data.get('Feature', {})
                feature_name_info = feature_info.get('Name', {})
                
                if isinstance(feature_name_info, dict):
                    feature_name = feature_name_info.get('Value', '')
                else:
                    feature_name = str(feature_name_info) if feature_name_info else ''
                
                # Obtener medida
                measure = ''
                measure_info = feature_info.get('Measure', {})
                if measure_info:
                    signs_info = measure_info.get('Signs', {})
                    if isinstance(signs_info, dict):
                        measure = signs_info.get('_', '')
                
                # Obtener valor (preferir PresentationValue)
                value = feature_data.get('PresentationValue', '') or feature_data.get('LocalValue', '') or feature_data.get('Value', '')
                
                if feature_name and value:
                    feature = IcecatFeature(
                        name=feature_name,
                        value=value,
                        group=group_name,
                        measure=measure,
                        feature_id=str(feature_info.get('ID', ''))
                    )
                    all_features.append(feature)
                    grouped_features[group_name].append(feature)
        
        return all_features, grouped_features
    
    def map_to_laptop_data(self, product: IcecatProduct) -> Dict[str, Any]:
        """
        Mapea un producto de Icecat a los campos del modelo Laptop
        
        Args:
            product: Producto de Icecat parseado
            
        Returns:
            Diccionario con datos mapeados al modelo Laptop
        """
        # Buscar especificaciones relevantes
        specs = {}
        for feature in product.features:
            specs[feature.name.lower()] = feature.value
        
        # Intentar extraer información de procesador, RAM, almacenamiento, etc.
        processor_info = self._extract_spec(specs, ['procesador', 'processor', 'cpu', 'tipo de procesador'])
        ram_info = self._extract_spec(specs, ['memoria interna', 'ram', 'memoria ram', 'internal memory'])
        storage_info = self._extract_spec(specs, ['capacidad total de almacenaje', 'almacenamiento', 'storage', 'ssd', 'hdd', 'disco duro'])
        screen_info = self._extract_spec(specs, ['diagonal de la pantalla', 'pantalla', 'screen size', 'display'])
        graphics_info = self._extract_spec(specs, ['tarjeta gráfica', 'gpu', 'graphics', 'modelo de adaptador gráfico discreto'])
        os_info = self._extract_spec(specs, ['sistema operativo', 'operating system', 'os instalado'])
        
        # Preparar imágenes para importar
        images_to_import = []
        if product.main_image:
            images_to_import.append({
                'url': product.main_image.url,
                'thumb_url': product.main_image.thumb_url,
                'is_cover': True,
                'position': 0
            })
        
        for img in product.gallery:
            if not img.is_main:  # Evitar duplicar la imagen principal
                images_to_import.append({
                    'url': img.url,
                    'thumb_url': img.thumb_url,
                    'is_cover': False,
                    'position': img.position
                })
        
        return {
            # Identificadores
            'icecat_id': product.icecat_id,
            'icecat_gtin': product.gtin,
            'icecat_product_code': product.product_code,
            
            # Información básica
            'display_name': product.title or product.product_name,
            'short_description': self._clean_html(product.summary_short or product.short_description)[:300],
            'long_description_html': product.long_description,
            
            # Marca
            'brand_name': product.brand,
            'brand_id_icecat': product.brand_id,
            
            # Especificaciones detectadas (para sugerir en formulario)
            'suggested_processor': processor_info,
            'suggested_ram': ram_info,
            'suggested_storage': storage_info,
            'suggested_screen': screen_info,
            'suggested_graphics': graphics_info,
            'suggested_os': os_info,
            
            # Categoría
            'icecat_category': product.category,
            
            # Imágenes para importar
            'images': images_to_import,
            
            # Especificaciones completas (para referencia)
            'all_specs': product.feature_groups,
            
            # Información adicional
            'warranty_info': product.warranty_info,
            'release_date': product.release_date,
            
            # Datos crudos para debugging
            'raw_data': product.raw_data
        }
    
    def _extract_spec(self, specs: Dict[str, str], keys: List[str]) -> Optional[str]:
        """Extrae una especificación buscando por múltiples claves posibles"""
        for key in keys:
            for spec_key, spec_value in specs.items():
                if key in spec_key:
                    return spec_value
        return None
    
    def _clean_html(self, text: str) -> str:
        """Limpia tags HTML básicos de un texto"""
        import re
        if not text:
            return ""
        # Remover tags HTML
        clean = re.sub(r'<[^>]+>', ' ', text)
        # Normalizar espacios
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()


# Singleton del servicio para uso global
_icecat_service_instance = None


def get_icecat_service(force_reload: bool = False) -> IcecatService:
    """
    Obtiene la instancia singleton del servicio de Icecat.
    
    Args:
        force_reload: Si True, recarga la configuración desde la DB
    """
    global _icecat_service_instance
    if _icecat_service_instance is None or force_reload:
        _icecat_service_instance = IcecatService()
    return _icecat_service_instance


def reload_icecat_config():
    """Fuerza la recarga de la configuración de Icecat"""
    global _icecat_service_instance
    _icecat_service_instance = None
    return get_icecat_service()
