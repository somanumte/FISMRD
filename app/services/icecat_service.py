# -*- coding: utf-8 -*-
"""
================================================================================
SERVICIO DE ICECAT MEJORADO - V2.0
================================================================================
Servicio para interactuar con la API v2 de Icecat con normalización robusta
y parsers específicos por marca.

Características:
    - Normalización unificada para todas las marcas
    - Parsers específicos por marca (Lenovo, HP, Dell, Apple, ASUS, Acer, MSI, Microsoft, LG, Samsung)
    - Validación exhaustiva de datos
    - Manejo de casos edge y datos faltantes
    - Extracción completa de puertos y conectividad

Marcas soportadas:
    Lenovo, HP, Dell, Apple, ASUS, Acer, MSI, Microsoft, LG, Samsung
================================================================================
"""

import requests
import logging
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from app.models.system_setting import SystemSetting
from app.services.standard_specs_map import (
    STANDARD_SPECS_MAP, BRAND_SPECIFIC_MAP, REQUIRED_FIELDS,
    STANDARD_UNITS, PORT_FEATURE_IDS, PORT_NAMES,
    get_field_ids, get_field_names, is_required_field
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES PARA ESTRUCTURA UNIFICADA
# =============================================================================

@dataclass
class UnifiedProcessor:
    """Datos unificados del procesador"""
    family: str = ""
    manufacturer: str = ""
    generation: str = ""
    model: str = ""
    full_name: str = ""
    frequency_base_ghz: float = 0.0
    frequency_turbo_ghz: float = 0.0
    cores: int = 0
    threads: int = 0
    cache: str = ""
    socket: str = ""
    tdp: str = ""
    lithography: str = ""
    has_npu: bool = False
    npu_details: str = ""


@dataclass
class UnifiedMemory:
    """Datos unificados de memoria RAM"""
    capacity_gb: int = 0
    type: str = ""  # DDR4, DDR5, LPDDR5
    speed_mhz: int = 0
    max_capacity_gb: int = 0
    slots: str = ""
    form_factor: str = ""  # SO-DIMM, DIMM
    channels: str = ""
    upgradeable: bool = False


@dataclass
class UnifiedStorage:
    """Datos unificados de almacenamiento"""
    total_capacity_gb: int = 0
    media_type: str = ""  # SSD, HDD, eMMC
    ssd_capacity_gb: int = 0
    ssd_interface: str = ""  # SATA, NVMe, PCIe
    ssd_form_factor: str = ""  # M.2, 2.5"
    nvme: bool = False
    hdd_capacity_gb: int = 0
    hdd_speed: str = ""
    upgradeable: bool = False


@dataclass
class UnifiedDisplay:
    """Datos unificados de pantalla"""
    diagonal_inches: float = 0.0
    resolution: str = ""
    type: str = ""  # IPS, OLED, TN
    hd_type: str = ""  # Full HD, 4K UHD
    touchscreen: bool = False
    refresh_rate_hz: int = 0
    brightness_nits: int = 0
    color_gamut: str = ""
    aspect_ratio: str = ""
    surface: str = ""  # Mate, Brillante
    hdr: bool = False


@dataclass
class UnifiedGraphics:
    """Datos unificados de gráficos"""
    discrete_model: str = ""
    discrete_memory_gb: float = 0.0
    discrete_brand: str = ""
    onboard_model: str = ""
    onboard_brand: str = ""
    has_discrete: bool = False
    ray_tracing: bool = False
    dlss: bool = False


@dataclass
class UnifiedPort:
    """Datos unificados de un puerto"""
    type: str = ""
    quantity: int = 0
    version: str = ""
    description: str = ""


@dataclass
class UnifiedConnectivity:
    """Datos unificados de conectividad"""
    ports: List[UnifiedPort] = field(default_factory=list)
    wifi_standard: str = ""
    bluetooth_version: str = ""
    ethernet: bool = False
    ethernet_speed: str = ""
    cellular: str = ""  # 4G, 5G
    nfc: bool = False


@dataclass
class UnifiedInput:
    """Datos unificados de entrada/teclado"""
    keyboard_layout: str = ""
    numeric_keypad: bool = False
    backlight: bool = False
    backlight_color: str = ""
    keyboard_language: str = ""
    pointing_device: str = ""
    fingerprint: bool = False
    face_recognition: bool = False
    stylus: bool = False


@dataclass
class UnifiedPhysical:
    """Datos unificados físicos"""
    weight_kg: float = 0.0
    width_mm: float = 0.0
    depth_mm: float = 0.0
    height_mm: float = 0.0
    thickness_mm: float = 0.0


@dataclass
class UnifiedBattery:
    """Datos unificados de batería"""
    technology: str = ""
    capacity_wh: float = 0.0
    capacity_mah: int = 0
    cells: int = 0
    life_hours: str = ""


@dataclass
class UnifiedCamera:
    """Datos unificados de cámara"""
    front_camera: str = ""
    front_resolution: str = ""
    ir_camera: bool = False
    privacy_shutter: bool = False


@dataclass
class UnifiedAudio:
    """Datos unificados de audio"""
    speakers: str = ""
    speaker_power: str = ""
    microphone: bool = False
    audio_chip: str = ""


@dataclass
class UnifiedSpecs:
    """Especificaciones unificadas completas"""
    brand: str = ""
    model: str = ""
    full_model: str = ""
    commercial_name: str = ""
    display_name: str = ""
    product_family: str = ""
    product_series: str = ""
    product_code: str = ""
    category: str = ""
    icecat_id: str = ""
    gtin: str = ""
    
    processor: UnifiedProcessor = field(default_factory=UnifiedProcessor)
    memory: UnifiedMemory = field(default_factory=UnifiedMemory)
    storage: UnifiedStorage = field(default_factory=UnifiedStorage)
    display: UnifiedDisplay = field(default_factory=UnifiedDisplay)
    graphics: UnifiedGraphics = field(default_factory=UnifiedGraphics)
    connectivity: UnifiedConnectivity = field(default_factory=UnifiedConnectivity)
    input: UnifiedInput = field(default_factory=UnifiedInput)
    physical: UnifiedPhysical = field(default_factory=UnifiedPhysical)
    battery: UnifiedBattery = field(default_factory=UnifiedBattery)
    camera: UnifiedCamera = field(default_factory=UnifiedCamera)
    audio: UnifiedAudio = field(default_factory=UnifiedAudio)
    
    os: str = ""
    os_arch: str = ""
    
    images: List[str] = field(default_factory=list)
    short_description: str = ""
    
    # Campos adicionales
    ram_upgradeable: bool = False
    storage_upgradeable: bool = False
    has_npu: bool = False
    
    # Raw data para debugging
    raw_specs: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convierte las especificaciones unificadas a diccionario"""
        return {
            "marca": self.brand,
            "modelo": self.model,
            "nombre_comercial": self.commercial_name,
            "nombre_visualizacion": self.display_name,
            "familia_producto": self.product_family,
            "serie_producto": self.product_series,
            "codigo_producto": self.product_code,
            "categoria": self.category,
            "icecat_id": self.icecat_id,
            "gtin": self.gtin,
            
            "procesador": {
                "familia": self.processor.family,
                "fabricante": self.processor.manufacturer,
                "generacion": self.processor.generation,
                "modelo": self.processor.model,
                "nombre_completo": self.processor.full_name,
                "frecuencia_base_ghz": self.processor.frequency_base_ghz,
                "frecuencia_turbo_ghz": self.processor.frequency_turbo_ghz,
                "nucleos": self.processor.cores,
                "hilos": self.processor.threads,
                "cache": self.processor.cache,
                "socket": self.processor.socket,
                "tdp": self.processor.tdp,
                "litografia": self.processor.lithography,
                "tiene_npu": self.processor.has_npu,
                "detalles_npu": self.processor.npu_details
            },
            
            "memoria_ram": {
                "capacidad_gb": self.memory.capacity_gb,
                "tipo": self.memory.type,
                "velocidad_mhz": self.memory.speed_mhz,
                "capacidad_maxima_gb": self.memory.max_capacity_gb,
                "ranuras": self.memory.slots,
                "factor_forma": self.memory.form_factor,
                "canales": self.memory.channels,
                "ampliable": self.memory.upgradeable
            },
            
            "almacenamiento": {
                "capacidad_total_gb": self.storage.total_capacity_gb,
                "tipo_media": self.storage.media_type,
                "capacidad_ssd_gb": self.storage.ssd_capacity_gb,
                "interfaz_ssd": self.storage.ssd_interface,
                "factor_forma_ssd": self.storage.ssd_form_factor,
                "nvme": self.storage.nvme,
                "capacidad_hdd_gb": self.storage.hdd_capacity_gb,
                "velocidad_hdd": self.storage.hdd_speed,
                "ampliable": self.storage.upgradeable
            },
            
            "pantalla": {
                "diagonal_pulgadas": self.display.diagonal_inches,
                "resolucion": self.display.resolution,
                "tipo": self.display.type,
                "tipo_hd": self.display.hd_type,
                "tactil": self.display.touchscreen,
                "tasa_refresco_hz": self.display.refresh_rate_hz,
                "brillo_nits": self.display.brightness_nits,
                "gama_colores": self.display.color_gamut,
                "relacion_aspecto": self.display.aspect_ratio,
                "superficie": self.display.surface,
                "hdr": self.display.hdr
            },
            
            "tarjeta_grafica": {
                "modelo_dedicado": self.graphics.discrete_model,
                "memoria_dedicada_gb": self.graphics.discrete_memory_gb,
                "marca_dedicada": self.graphics.discrete_brand,
                "modelo_integrado": self.graphics.onboard_model,
                "marca_integrada": self.graphics.onboard_brand,
                "tiene_dedicada": self.graphics.has_discrete,
                "ray_tracing": self.graphics.ray_tracing,
                "dlss": self.graphics.dlss
            },
            
            "conectividad": {
                "puertos": [
                    {
                        "tipo": p.type,
                        "cantidad": p.quantity,
                        "version": p.version,
                        "descripcion": p.description
                    } for p in self.connectivity.ports
                ],
                "wifi": self.connectivity.wifi_standard,
                "bluetooth": self.connectivity.bluetooth_version,
                "ethernet": self.connectivity.ethernet,
                "velocidad_ethernet": self.connectivity.ethernet_speed,
                "celular": self.connectivity.cellular,
                "nfc": self.connectivity.nfc
            },
            
            "entrada": {
                "disposicion_teclado": self.input.keyboard_layout,
                "teclado_numerico": self.input.numeric_keypad,
                "retroiluminacion": self.input.backlight,
                "color_retroiluminacion": self.input.backlight_color,
                "idioma_teclado": self.input.keyboard_language,
                "dispositivo_apuntador": self.input.pointing_device,
                "lector_huellas": self.input.fingerprint,
                "reconocimiento_facial": self.input.face_recognition,
                "lapiz_optico": self.input.stylus
            },
            
            "fisico": {
                "peso_kg": self.physical.weight_kg,
                "ancho_mm": self.physical.width_mm,
                "profundidad_mm": self.physical.depth_mm,
                "altura_mm": self.physical.height_mm,
                "grosor_mm": self.physical.thickness_mm
            },
            
            "bateria": {
                "tecnologia": self.battery.technology,
                "capacidad_wh": self.battery.capacity_wh,
                "capacidad_mah": self.battery.capacity_mah,
                "celdas": self.battery.cells,
                "duracion": self.battery.life_hours
            },
            
            "camara": {
                "frontal": self.camera.front_camera,
                "resolucion_frontal": self.camera.front_resolution,
                "camara_ir": self.camera.ir_camera,
                "cubierta_privacidad": self.camera.privacy_shutter
            },
            
            "audio": {
                "altavoces": self.audio.speakers,
                "potencia_altavoces": self.audio.speaker_power,
                "microfono": self.audio.microphone,
                "chip_audio": self.audio.audio_chip
            },
            
            "sistema_operativo": self.os,
            "arquitectura_os": self.os_arch,
            
            "imagenes": self.images,
            "palabras_clave": self.short_description, # Usar descripción corta como palabras clave base si no hay específicas
            "descripcion_corta": self.short_description,
            
            "caracteristicas_adicionales": {
                "ram_ampliable": self.ram_upgradeable,
                "almacenamiento_ampliable": self.storage_upgradeable,
                "tiene_npu": self.has_npu
            }
        }


# =============================================================================
# CLASE PRINCIPAL DEL SERVICIO
# =============================================================================

class IcecatService:
    """
    Servicio para interactuar con la API v2 de Icecat.
    Implementa normalización unificada para todas las marcas.
    """
    
    BASE_URL = "https://live.icecat.biz/api/"
    
    # Palabras clave para detección de NPU
    NPU_KEYWORDS = [
        'Ryzen AI', 'Core Ultra', 'NPU', 'AI Boost', 'Neural',
        'X Elite', 'X Plus', 'AI Powered', 'Intel AI', 'AMD AI'
    ]
    
    # Marcas de GPU dedicada
    DISCRETE_GPU_BRANDS = ['NVIDIA', 'GeForce', 'RTX', 'GTX', 'Quadro',
                           'AMD', 'Radeon', 'RX', 'FirePro']
    
    @staticmethod
    def get_credentials() -> Dict[str, str]:
        """Obtiene las credenciales de Icecat desde SystemSettings."""
        return {
            'api_token': SystemSetting.get_value('icecat_api_token', ''),
            'content_token': SystemSetting.get_value('icecat_content_token', ''),
            'api_username': SystemSetting.get_value('icecat_api_username', ''),
            'app_key': SystemSetting.get_value('icecat_app_key', ''),
            'content_username': SystemSetting.get_value('icecat_content_username', ''),
            'language': SystemSetting.get_value('icecat_language', 'es')
        }
    
    @staticmethod
    def _make_request(url: str, params: Dict, headers: Dict = None, 
                      timeout: int = 15) -> Tuple[Optional[requests.Response], Optional[str]]:
        """
        Realiza una petición HTTP manejando errores de SSL y reintentos.
        
        Returns:
            Tuple de (response, error_message)
        """
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            return response, None
        except requests.exceptions.SSLError:
            logger.warning(f"IcecatService: Error SSL conectando a {url}. Reintentando sin verificación.")
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = requests.get(url, params=params, headers=headers, 
                                       timeout=timeout, verify=False)
                return response, None
            except Exception as e:
                return None, str(e)
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def fetch_by_gtin(gtin: str) -> Dict:
        """
        Busca un producto en Icecat por su GTIN (UPC/EAN).
        
        Args:
            gtin: Código GTIN/EAN/UPC del producto
            
        Returns:
            Diccionario con los datos normalizados del producto
        """
        creds = IcecatService.get_credentials()
        
        params = {
            'GTIN': gtin,
            'Language': creds['language'],
            'Content': 'All'
        }
        headers = {}
        
        if creds['api_token']:
            headers['Api-Token'] = creds['api_token']
            if creds['content_token']:
                headers['Content-Token'] = creds['content_token']
        else:
            username = creds['content_username'] or creds['api_username'] or 'openicecat-live'
            params['UserName'] = username
            if creds['app_key']:
                params['AppKey'] = creds['app_key']
        
        response, error = IcecatService._make_request(IcecatService.BASE_URL, params, headers=headers)
        
        if error:
            logger.error(f"IcecatService: Error de conexión: {error}")
            return {'success': False, 'message': f'Error de conexión: {error}'}
        
        try:
            if response.status_code == 200:
                json_data = response.json()
                if 'data' in json_data and json_data['data']:
                    normalized = IcecatService.normalize_data(json_data['data'])
                    return {'success': True, 'product': normalized}
                else:
                    logger.warning(f"IcecatService: Producto no encontrado para GTIN {gtin}")
                    return {'success': False, 'message': 'Producto no encontrado en Icecat.'}
            elif response.status_code == 401:
                return {'success': False, 'message': 'Error de autenticación con Icecat.'}
            elif response.status_code == 404:
                error_data = response.json() if response.text else {}
                message = error_data.get('Message', 'Producto no encontrado')
                return {'success': False, 'message': f'Error de API Icecat: 404 - {message}'}
            else:
                logger.error(f"IcecatService: Error de API {response.status_code}")
                return {'success': False, 'message': f'Error de API Icecat: {response.status_code}'}
        except Exception as e:
            logger.error(f"IcecatService: Excepción al consultar API: {str(e)}")
            return {'success': False, 'message': f'Error de conexión: {str(e)}'}
    
    @staticmethod
    def normalize_data(raw_data: Dict) -> Dict:
        """
        Transforma la respuesta cruda de Icecat a un formato unificado.
        
        Args:
            raw_data: Datos crudos de la API de Icecat
            
        Returns:
            Diccionario con datos normalizados según el esquema unificado
        """
        # Extraer información básica
        general_info = raw_data.get('GeneralInfo', {})
        
        # Crear objeto de especificaciones unificadas
        specs = UnifiedSpecs()
        
        # Información básica
        specs.icecat_id = str(general_info.get('ProductId', ''))
        specs.brand = general_info.get('Brand', '')
        specs.commercial_name = general_info.get('Title', '')
        specs.category = IcecatService._get_category_name(raw_data)
        
        # Extraer campos para lógica de modelo
        def extract_val(obj):
            if isinstance(obj, dict):
                return obj.get('Value', '') or obj.get('Name', {}).get('Value', '')
            return str(obj) if obj else ""

        specs.product_family = extract_val(general_info.get('ProductFamily'))
        specs.product_series = extract_val(general_info.get('ProductSeries'))
        specs.product_code = general_info.get('ProductCode', '')
        
        # Construir modelo usando la nueva lógica estandarizada
        specs.model = IcecatService._build_model_name(
            specs.brand,
            specs.product_family,
            specs.product_series,
            general_info.get('ProductName', ''),
            specs.product_code
        )
        
        # Extraer GTINs
        gtins = raw_data.get('GTINs', [])
        if gtins:
            specs.gtin = gtins[0].get('GTIN', '')
        
        # Construir nombre de visualización
        specs.display_name = IcecatService._build_display_name(specs.brand, specs.model, 
                                                                specs.commercial_name)
        
        # Extraer descripción
        specs.short_description = IcecatService._extract_description(general_info)
        
        # Extraer imágenes
        specs.images = IcecatService._extract_images(raw_data)
        
        # Indexar especificaciones
        indexed_specs = IcecatService._index_specifications(raw_data)
        specs.raw_specs = indexed_specs
        
        # Parsear cada componente
        specs.processor = IcecatService._parse_processor(indexed_specs, specs.brand)
        specs.memory = IcecatService._parse_memory(indexed_specs)
        specs.storage = IcecatService._parse_storage(indexed_specs)
        specs.display = IcecatService._parse_display(indexed_specs)
        specs.graphics = IcecatService._parse_graphics(indexed_specs)
        specs.connectivity = IcecatService._parse_connectivity(indexed_specs)
        specs.input = IcecatService._parse_input(indexed_specs)
        specs.physical = IcecatService._parse_physical(indexed_specs)
        specs.battery = IcecatService._parse_battery(indexed_specs)
        specs.camera = IcecatService._parse_camera(indexed_specs)
        specs.audio = IcecatService._parse_audio(indexed_specs)
        
        # Sistema operativo
        specs.os = IcecatService._get_spec_value(indexed_specs, 'software.os')
        specs.os_arch = IcecatService._get_spec_value(indexed_specs, 'software.os_arch')
        
        # Características adicionales
        specs.ram_upgradeable = specs.memory.upgradeable
        specs.storage_upgradeable = specs.storage.upgradeable
        specs.has_npu = specs.processor.has_npu
        
        # Aplicar parser específico por marca
        specs = IcecatService._apply_brand_specific_parser(specs)
        
        return specs.to_dict()
    
    @staticmethod
    def _index_specifications(raw_data: Dict) -> Dict[str, Any]:
        """
        Indexa todas las especificaciones por ID y nombre para búsqueda rápida.
        
        Args:
            raw_data: Datos crudos de Icecat
            
        Returns:
            Diccionario indexado con todas las especificaciones
        """
        indexed = {'by_id': {}, 'by_name': {}, 'by_category': {}}
        
        # Extraer features de todos los grupos
        features_list = []
        feature_groups = raw_data.get('FeaturesGroups', [])
        
        for group in feature_groups:
            group_name = ''
            if group.get('FeatureGroup', {}).get('Name'):
                group_name = group['FeatureGroup']['Name'].get('Value', '')
            
            features = group.get('Features', [])
            for feat in features:
                features_list.append(feat)
                
                # Indexar por categoría
                if group_name:
                    if group_name not in indexed['by_category']:
                        indexed['by_category'][group_name] = []
                    indexed['by_category'][group_name].append(feat)
        
        # Indexar por ID y nombre
        for feat in features_list:
            feature_info = feat.get('Feature', {})
            feat_id = str(feature_info.get('ID', ''))
            feat_name = feature_info.get('Name', {}).get('Value', '').lower()
            presentation_value = feat.get('PresentationValue', '')
            raw_value = feat.get('RawValue', '')
            
            value = presentation_value or raw_value
            
            if feat_id:
                indexed['by_id'][feat_id] = value
            
            if feat_name:
                indexed['by_name'][feat_name] = value
        
        return indexed
    
    @staticmethod
    def _get_spec_value(indexed_specs: Dict, field_path: str) -> str:
        """
        Obtiene el valor de una especificación usando el mapeo estándar.
        
        Args:
            indexed_specs: Especificaciones indexadas
            field_path: Ruta al campo (ej: "processor.family")
            
        Returns:
            Valor de la especificación o cadena vacía
        """
        ids = get_field_ids(field_path)
        names = get_field_names(field_path)
        
        # Buscar por IDs
        for feat_id in ids:
            if str(feat_id) in indexed_specs['by_id']:
                return indexed_specs['by_id'][str(feat_id)]
        
        # Buscar por nombres
        for name in names:
            if name.lower() in indexed_specs['by_name']:
                return indexed_specs['by_name'][name.lower()]
        
        return ''

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Remueve símbolos comerciales y limpia espacios extra."""
        if not text:
            return ""
        # Remover symbols
        text = text.replace('®', '').replace('™', '').replace('(R)', '').replace('(TM)', '')
        # Limpiar espacios múltiples y extremos
        return " ".join(text.split()).strip()

    @staticmethod
    def _build_processor_full_name(manufacturer: str, family: str, model: str) -> str:
        """
        Construye el nombre completo siguiendo: [Manufacturer] [Family] [Model]
        Evita duplicación si el modelo ya contiene la familia.
        """
        manufacturer = IcecatService._normalize_text(manufacturer)
        family = IcecatService._normalize_text(family)
        model = IcecatService._normalize_text(model)

        if not family and not model:
            return manufacturer

        # Casos especiales de deduplicación
        # Si el modelo ya contiene la familia (ej: "Core i7-12700H" contiene "i7")
        # O si el modelo empieza con la familia
        
        # Primero, normalizar comparaciones (quitar espacios y guiones)
        family_clean = family.lower().replace(" ", "").replace("-", "")
        model_clean = model.lower().replace(" ", "").replace("-", "")

        # Si el modelo empieza con un prefijo que es parte de la familia (ej: i7-11800H y familia Core i7)
        # O si el modelo contiene la familia completa
        is_duplicate = False
        if family_clean in model_clean:
            is_duplicate = True
        elif '-' in model:
            model_prefix = model.split('-')[0].lower()
            if model_prefix in family_clean:
                is_duplicate = True

        if is_duplicate:
            # Si es duplicado, preferimos el modelo pero intentamos mantener la "marca" de la familia (ej: Core)
            primary_family_part = family.split(' ')[0]
            if primary_family_part.lower() == "intel": # Si la familia empieza con Intel, buscar la siguiente parte
                parts = family.split(' ')
                primary_family_part = parts[1] if len(parts) > 1 else primary_family_part
            
            if primary_family_part.lower() not in model.lower():
                full_name = f"{primary_family_part} {model}"
            else:
                full_name = model
        else:
            full_name = f"{family} {model}".strip()

        # Caso especial para Intel: Si es Core iX, asegurar que diga "Intel Core iX"
        if "intel" in manufacturer.lower() and "i" in model.lower() and "-" in model:
            if "core" not in full_name.lower():
                full_name = f"Core {full_name}"

        # Agregar fabricante si no está
        if manufacturer and manufacturer.lower() not in full_name.lower():
            full_name = f"{manufacturer} {full_name}"

        return " ".join(full_name.split()).strip()

    @staticmethod
    def _build_processor_extended_name(base_name: str, cores: int, frequency: float, cache: str) -> str:
        """
        Construye el nombre extendido: "Intel Core i7-11800H (8-Core, up to 4.8 GHz, 24MB Cache)"
        """
        details = []
        if cores:
            details.append(f"{cores}-Core")
        if frequency:
            details.append(f"up to {frequency} GHz")
        if cache:
            details.append(f"{cache} Cache")
        
        if not details:
            return base_name
            
        return f"{base_name} ({', '.join(details)})"
    
    @staticmethod
    def _parse_processor(indexed_specs: Dict, brand: str) -> UnifiedProcessor:
        """Parsea los datos del procesador."""
        proc = UnifiedProcessor()
        
        # Campos base normalizados
        family_raw = IcecatService._get_spec_value(indexed_specs, 'processor.family')
        manufacturer_raw = IcecatService._get_spec_value(indexed_specs, 'processor.manufacturer')
        generation_raw = IcecatService._get_spec_value(indexed_specs, 'processor.generation')
        model_raw = IcecatService._get_spec_value(indexed_specs, 'processor.model')
        
        proc.family = IcecatService._normalize_text(family_raw)
        proc.manufacturer = IcecatService._normalize_text(manufacturer_raw)
        proc.generation = IcecatService._normalize_text(generation_raw)
        proc.model = IcecatService._normalize_text(model_raw)

        # Inferencia si la generación viene vacía de Icecat
        if not proc.generation:
            proc.generation = IcecatService._infer_processor_generation(
                proc.manufacturer, proc.family, proc.model
            )
        
        # Construir nombre completo estandarizado (para el catálogo)
        standard_name = IcecatService._build_processor_full_name(
            proc.manufacturer, proc.family, proc.model
        )
        
        # Frecuencias
        freq_base = IcecatService._get_spec_value(indexed_specs, 'processor.frequency_base')
        proc.frequency_base_ghz = IcecatService._parse_frequency(freq_base)
        
        freq_turbo = IcecatService._get_spec_value(indexed_specs, 'processor.frequency_turbo')
        proc.frequency_turbo_ghz = IcecatService._parse_frequency(freq_turbo)
        
        # Núcleos e hilos
        cores = IcecatService._get_spec_value(indexed_specs, 'processor.cores')
        proc.cores = IcecatService._parse_int(cores)
        
        threads = IcecatService._get_spec_value(indexed_specs, 'processor.threads')
        proc.threads = IcecatService._parse_int(threads)
        
        # Cache
        proc.cache = IcecatService._get_spec_value(indexed_specs, 'processor.cache')

        # Construir nombre extendido (para mostrar a clientes)
        proc.full_name = IcecatService._build_processor_extended_name(
            standard_name, proc.cores, proc.frequency_turbo_ghz or proc.frequency_base_ghz, proc.cache
        )
        proc.socket = IcecatService._get_spec_value(indexed_specs, 'processor.socket')
        proc.tdp = IcecatService._get_spec_value(indexed_specs, 'processor.tdp')
        proc.lithography = IcecatService._get_spec_value(indexed_specs, 'processor.lithography')
        
        # Detección de NPU
        npu_info = IcecatService._get_spec_value(indexed_specs, 'processor.npu')
        proc.has_npu = IcecatService._detect_npu(proc.full_name, npu_info)
        proc.npu_details = npu_info
        
        return proc
    
    @staticmethod
    def _infer_processor_generation(manufacturer: str, family: str, model: str) -> str:
        """Infiere la generación del procesador basándose en fabricante y modelo."""
        if not model:
            return ""
            
        man_lower = manufacturer.lower() if manufacturer else ""
        fam_lower = family.lower() if family else ""
        mod_upper = model.upper()
        
        # Intel
        if 'intel' in man_lower or 'intel' in fam_lower:
            if 'ultra' in fam_lower:
                return "Core Ultra Series 1"
            
            # 10th Gen y superiores (5 o más dígitos o prefijo de 2 dígitos)
            gen_match_new = re.search(r'(\d{2})\d{3}', mod_upper) 
            if gen_match_new:
                return f"{gen_match_new.group(1)}th Gen"
            
            # 2nd a 9th Gen (4 dígitos empezando con 2-9)
            gen_match_old = re.search(r'([2-9])\d{3}', mod_upper)
            if gen_match_old:
                return f"{gen_match_old.group(1)}th Gen"
            
            # 1st Gen o modelos sin guión pero con número
            if re.search(r'^[1-9]\d{2}$', mod_upper):
                return "1st Gen"

        # AMD
        if 'amd' in man_lower or 'ryzen' in fam_lower:
            # Ryzen 5000, 7000, 8000
            gen_match = re.search(r'(\d)\d{3}', mod_upper)
            if gen_match:
                return f"Ryzen {gen_match.group(1)}000 Series"
                
        # Apple
        if 'apple' in man_lower or 'apple' in fam_lower:
            if 'M1' in mod_upper: return "Apple M1 Chip"
            if 'M2' in mod_upper: return "Apple M2 Chip"
            if 'M3' in mod_upper: return "Apple M3 Chip"
            
        return ""

    @staticmethod
    def _parse_memory(indexed_specs: Dict) -> UnifiedMemory:
        """Parsea los datos de memoria RAM."""
        mem = UnifiedMemory()
        
        # Capacidad
        capacity = IcecatService._get_spec_value(indexed_specs, 'memory.internal')
        mem.capacity_gb = IcecatService._parse_memory_capacity(capacity)
        
        # Tipo
        mem.type = IcecatService._get_spec_value(indexed_specs, 'memory.type')
        
        # Velocidad
        speed = IcecatService._get_spec_value(indexed_specs, 'memory.speed')
        mem.speed_mhz = IcecatService._parse_int(speed)
        
        # Capacidad máxima
        max_cap = IcecatService._get_spec_value(indexed_specs, 'memory.max')
        mem.max_capacity_gb = IcecatService._parse_memory_capacity(max_cap)
        
        # Ranuras
        mem.slots = IcecatService._get_spec_value(indexed_specs, 'memory.slots')
        
        # Factor de forma
        mem.form_factor = IcecatService._get_spec_value(indexed_specs, 'memory.form_factor')
        
        # Canales
        mem.channels = IcecatService._get_spec_value(indexed_specs, 'memory.channels')
        
        # Ampliable
        upgradeable = IcecatService._get_spec_value(indexed_specs, 'memory.upgradeable')
        mem.upgradeable = IcecatService._parse_boolean(upgradeable)
        
        # Si no está explícito, inferir de ranuras y capacidad máxima
        if not mem.upgradeable:
            if mem.slots and ('2' in mem.slots or 'ranura' in mem.slots.lower()):
                mem.upgradeable = True
            if mem.max_capacity_gb > mem.capacity_gb:
                mem.upgradeable = True
        
        return mem
    
    @staticmethod
    def _parse_storage(indexed_specs: Dict) -> UnifiedStorage:
        """Parsea los datos de almacenamiento."""
        storage = UnifiedStorage()
        
        # Capacidad total
        total = IcecatService._get_spec_value(indexed_specs, 'storage.total_capacity')
        storage.total_capacity_gb = IcecatService._parse_storage_capacity(total)
        
        # Tipo de media
        storage.media_type = IcecatService._get_spec_value(indexed_specs, 'storage.media')
        
        # SSD
        ssd_cap = IcecatService._get_spec_value(indexed_specs, 'storage.ssd_capacity')
        storage.ssd_capacity_gb = IcecatService._parse_storage_capacity(ssd_cap)
        
        storage.ssd_interface = IcecatService._get_spec_value(indexed_specs, 'storage.ssd_interface')
        storage.ssd_form_factor = IcecatService._get_spec_value(indexed_specs, 'storage.ssd_form_factor')
        
        # NVMe
        nvme = IcecatService._get_spec_value(indexed_specs, 'storage.nvme')
        storage.nvme = IcecatService._parse_boolean(nvme)
        
        # Si no está explícito, inferir de la interfaz
        if not storage.nvme and storage.ssd_interface:
            if 'nvme' in storage.ssd_interface.lower():
                storage.nvme = True
        
        # HDD
        hdd_cap = IcecatService._get_spec_value(indexed_specs, 'storage.hdd_capacity')
        storage.hdd_capacity_gb = IcecatService._parse_storage_capacity(hdd_cap)
        storage.hdd_speed = IcecatService._get_spec_value(indexed_specs, 'storage.hdd_speed')
        
        # Ampliable
        upgradeable = IcecatService._get_spec_value(indexed_specs, 'storage.upgradeable')
        storage.upgradeable = IcecatService._parse_boolean(upgradeable)
        
        # Si no está explícito, inferir del tipo
        if not storage.upgradeable:
            if storage.media_type and 'ssd' in storage.media_type.lower():
                storage.upgradeable = True
        
        return storage
    
    @staticmethod
    def _parse_display(indexed_specs: Dict) -> UnifiedDisplay:
        """Parsea los datos de pantalla."""
        disp = UnifiedDisplay()
        
        # Diagonal
        diagonal = IcecatService._get_spec_value(indexed_specs, 'display.diagonal')
        disp.diagonal_inches = IcecatService._parse_screen_size(diagonal)
        
        # Resolución
        disp.resolution = IcecatService._get_spec_value(indexed_specs, 'display.resolution')
        
        # Tipo de panel
        disp.type = IcecatService._get_spec_value(indexed_specs, 'display.type')
        
        # Tipo HD
        disp.hd_type = IcecatService._get_spec_value(indexed_specs, 'display.hd_type')
        
        # Táctil
        touchscreen = IcecatService._get_spec_value(indexed_specs, 'display.touchscreen')
        disp.touchscreen = IcecatService._parse_boolean(touchscreen)
        
        # Tasa de refresco
        refresh = IcecatService._get_spec_value(indexed_specs, 'display.refresh_rate')
        disp.refresh_rate_hz = IcecatService._parse_int(refresh)
        
        # Brillo
        brightness = IcecatService._get_spec_value(indexed_specs, 'display.brightness')
        disp.brightness_nits = IcecatService._parse_int(brightness)
        
        # Gama de colores
        disp.color_gamut = IcecatService._get_spec_value(indexed_specs, 'display.color_gamut')
        
        # Relación de aspecto
        disp.aspect_ratio = IcecatService._get_spec_value(indexed_specs, 'display.aspect_ratio')
        
        # Superficie
        disp.surface = IcecatService._get_spec_value(indexed_specs, 'display.surface')
        
        # HDR
        hdr = IcecatService._get_spec_value(indexed_specs, 'display.hdr')
        disp.hdr = IcecatService._parse_boolean(hdr)
        
        return disp
    
    @staticmethod
    def _parse_graphics(indexed_specs: Dict) -> UnifiedGraphics:
        """Parsea los datos de gráficos."""
        gpu = UnifiedGraphics()
        
        # GPU dedicada
        gpu.discrete_model = IcecatService._get_spec_value(indexed_specs, 'graphics.discrete_model')
        
        # Memoria dedicada
        discrete_mem = IcecatService._get_spec_value(indexed_specs, 'graphics.discrete_memory')
        gpu.discrete_memory_gb = IcecatService._parse_memory_capacity(discrete_mem)
        
        # Marca dedicada
        gpu.discrete_brand = IcecatService._get_spec_value(indexed_specs, 'graphics.discrete_brand')
        
        # Si no hay marca pero hay modelo, inferir
        if not gpu.discrete_brand and gpu.discrete_model:
            gpu.discrete_brand = IcecatService._infer_gpu_brand(gpu.discrete_model)
        
        # GPU integrada
        gpu.onboard_model = IcecatService._get_spec_value(indexed_specs, 'graphics.onboard_model')
        gpu.onboard_brand = IcecatService._get_spec_value(indexed_specs, 'graphics.onboard_brand')
        
        # Tiene GPU dedicada
        gpu.has_discrete = bool(gpu.discrete_model and 
                                gpu.discrete_model.lower() not in ['no', 'none', 'not available', 'no disponible'])
        
        # Ray Tracing y DLSS
        rt = IcecatService._get_spec_value(indexed_specs, 'graphics.ray_tracing')
        gpu.ray_tracing = IcecatService._parse_boolean(rt)
        
        dlss = IcecatService._get_spec_value(indexed_specs, 'graphics.dlss')
        gpu.dlss = IcecatService._parse_boolean(dlss)
        
        return gpu
    
    @staticmethod
    def _parse_connectivity(indexed_specs: Dict) -> UnifiedConnectivity:
        """Parsea los datos de conectividad."""
        conn = UnifiedConnectivity()
        
        # Parsear puertos
        ports = []
        
        # USB 2.0
        usb2 = IcecatService._get_spec_value(indexed_specs, 'connectivity.usb_2_0')
        if usb2:
            ports.append(UnifiedPort(
                type="USB 2.0",
                quantity=IcecatService._parse_int(usb2),
                description="USB-A 2.0"
            ))
        
        # USB 3.2 Gen 1
        usb3_gen1 = IcecatService._get_spec_value(indexed_specs, 'connectivity.usb_3_2_gen1')
        if usb3_gen1:
            ports.append(UnifiedPort(
                type="USB 3.2 Gen 1",
                quantity=IcecatService._parse_int(usb3_gen1),
                description="USB-A 3.2 Gen 1 (5Gbps)"
            ))
        
        # USB 3.2 Gen 2
        usb3_gen2 = IcecatService._get_spec_value(indexed_specs, 'connectivity.usb_3_2_gen2')
        if usb3_gen2:
            ports.append(UnifiedPort(
                type="USB 3.2 Gen 2",
                quantity=IcecatService._parse_int(usb3_gen2),
                description="USB-A 3.2 Gen 2 (10Gbps)"
            ))
        
        # USB-C
        usbc = IcecatService._get_spec_value(indexed_specs, 'connectivity.usb_c')
        if usbc:
            ports.append(UnifiedPort(
                type="USB-C",
                quantity=IcecatService._parse_int(usbc),
                description="USB Tipo C"
            ))
        
        # USB4
        usb4 = IcecatService._get_spec_value(indexed_specs, 'connectivity.usb4')
        if usb4:
            ports.append(UnifiedPort(
                type="USB4",
                quantity=IcecatService._parse_int(usb4),
                description="USB4 Gen 3x2 (40Gbps)"
            ))

        # Thunderbolt
        thunderbolt = IcecatService._get_spec_value(indexed_specs, 'connectivity.thunderbolt')
        if thunderbolt:
            ports.append(UnifiedPort(
                type="Thunderbolt",
                quantity=IcecatService._parse_int(thunderbolt),
                description="Thunderbolt"
            ))
        
        # HDMI
        hdmi = IcecatService._get_spec_value(indexed_specs, 'connectivity.hdmi')
        if hdmi:
            hdmi_version = IcecatService._get_spec_value(indexed_specs, 'connectivity.hdmi_version')
            # Si no hay versión en el campo específico, intentar extraerla del nombre si es HDMI 2.1
            if not hdmi_version and "2.1" in str(hdmi).lower():
                hdmi_version = "2.1"
            ports.append(UnifiedPort(
                type="HDMI",
                quantity=IcecatService._parse_int(hdmi),
                version=hdmi_version,
                description=f"HDMI {hdmi_version}" if hdmi_version else "HDMI"
            ))
        
        # DisplayPort
        dp = IcecatService._get_spec_value(indexed_specs, 'connectivity.displayport')
        if dp:
            ports.append(UnifiedPort(
                type="DisplayPort",
                quantity=IcecatService._parse_int(dp),
                description="DisplayPort"
            ))
        
        # VGA
        vga = IcecatService._get_spec_value(indexed_specs, 'connectivity.vga')
        if vga:
            ports.append(UnifiedPort(
                type="VGA",
                quantity=IcecatService._parse_int(vga),
                description="VGA (D-Sub)"
            ))
        
        # Ethernet
        ethernet = IcecatService._get_spec_value(indexed_specs, 'connectivity.ethernet')
        conn.ethernet = bool(ethernet)
        conn.ethernet_speed = IcecatService._get_spec_value(indexed_specs, 'connectivity.ethernet_speed')
        
        if ethernet:
            ports.append(UnifiedPort(
                type="Ethernet",
                quantity=IcecatService._parse_int(ethernet),
                description=f"RJ-45 {conn.ethernet_speed}" if conn.ethernet_speed else "RJ-45"
            ))
        
        # Audio Jack
        audio = IcecatService._get_spec_value(indexed_specs, 'connectivity.audio_jack')
        if audio:
            ports.append(UnifiedPort(
                type="Audio Jack",
                quantity=IcecatService._parse_int(audio),
                description="3.5mm Combo"
            ))
        
        # SD Card
        sd = IcecatService._get_spec_value(indexed_specs, 'connectivity.sd_card')
        if sd:
            ports.append(UnifiedPort(
                type="SD Card",
                quantity=IcecatService._parse_int(sd),
                description="Lector SD"
            ))
        
        # SmartCard
        smartcard = IcecatService._get_spec_value(indexed_specs, 'connectivity.smartcard')
        if smartcard:
            ports.append(UnifiedPort(
                type="SmartCard",
                quantity=IcecatService._parse_int(smartcard),
                description="Lector tarjeta inteligente"
            ))
        
        conn.ports = ports
        
        # Wireless
        conn.wifi_standard = IcecatService._get_spec_value(indexed_specs, 'connectivity.wifi')
        conn.bluetooth_version = IcecatService._get_spec_value(indexed_specs, 'connectivity.bluetooth')
        
        # Celular
        conn.cellular = IcecatService._get_spec_value(indexed_specs, 'connectivity.cellular')
        
        # NFC
        nfc = IcecatService._get_spec_value(indexed_specs, 'connectivity.nfc')
        conn.nfc = IcecatService._parse_boolean(nfc)
        
        # USB-C Features anidadas
        alt_mode = IcecatService._get_spec_value(indexed_specs, 'connectivity.raw_specs.by_name.usb type-c displayport alternate mode')
        if alt_mode and IcecatService._parse_boolean(alt_mode):
            for p in ports:
                if "USB-C" in p.type or "USB4" in p.type or "Thunderbolt" in p.type:
                    p.description += " (Alt Mode DP)"
        
        return conn
    
    @staticmethod
    def _parse_input(indexed_specs: Dict) -> UnifiedInput:
        """Parsea los datos de entrada/teclado."""
        inp = UnifiedInput()
        
        inp.keyboard_layout = IcecatService._get_spec_value(indexed_specs, 'input.keyboard_layout')
        
        # Teclado numérico
        numpad = IcecatService._get_spec_value(indexed_specs, 'input.numeric_keypad')
        inp.numeric_keypad = IcecatService._parse_boolean(numpad)
        
        # Retroiluminación
        backlight = IcecatService._get_spec_value(indexed_specs, 'input.backlight')
        inp.backlight = IcecatService._parse_boolean(backlight)
        inp.backlight_color = IcecatService._get_spec_value(indexed_specs, 'input.backlight_color')
        
        inp.keyboard_language = IcecatService._get_spec_value(indexed_specs, 'input.keyboard_language')
        inp.pointing_device = IcecatService._get_spec_value(indexed_specs, 'input.pointing_device')
        
        # Huella
        fingerprint = IcecatService._get_spec_value(indexed_specs, 'input.fingerprint')
        inp.fingerprint = IcecatService._parse_boolean(fingerprint)
        
        # Reconocimiento facial
        face = IcecatService._get_spec_value(indexed_specs, 'input.face_recognition')
        inp.face_recognition = IcecatService._parse_boolean(face)
        
        # Lápiz
        stylus = IcecatService._get_spec_value(indexed_specs, 'input.stylus')
        inp.stylus = IcecatService._parse_boolean(stylus)
        
        return inp
    
    @staticmethod
    def _parse_physical(indexed_specs: Dict) -> UnifiedPhysical:
        """Parsea los datos físicos."""
        phys = UnifiedPhysical()
        
        weight = IcecatService._get_spec_value(indexed_specs, 'physical.weight')
        phys.weight_kg = IcecatService._parse_weight(weight)
        
        width = IcecatService._get_spec_value(indexed_specs, 'physical.width')
        phys.width_mm = IcecatService._parse_dimension(width)
        
        depth = IcecatService._get_spec_value(indexed_specs, 'physical.depth')
        phys.depth_mm = IcecatService._parse_dimension(depth)
        
        height = IcecatService._get_spec_value(indexed_specs, 'physical.height')
        phys.height_mm = IcecatService._parse_dimension(height)
        
        thickness = IcecatService._get_spec_value(indexed_specs, 'physical.thickness')
        phys.thickness_mm = IcecatService._parse_dimension(thickness)
        
        return phys
    
    @staticmethod
    def _parse_battery(indexed_specs: Dict) -> UnifiedBattery:
        """Parsea los datos de batería."""
        batt = UnifiedBattery()
        
        batt.technology = IcecatService._get_spec_value(indexed_specs, 'battery.technology')
        
        capacity_wh = IcecatService._get_spec_value(indexed_specs, 'battery.capacity_wh')
        batt.capacity_wh = IcecatService._parse_float(capacity_wh)
        
        capacity_mah = IcecatService._get_spec_value(indexed_specs, 'battery.capacity_mah')
        batt.capacity_mah = IcecatService._parse_int(capacity_mah)
        
        cells = IcecatService._get_spec_value(indexed_specs, 'battery.cells')
        batt.cells = IcecatService._parse_int(cells)
        
        batt.life_hours = IcecatService._get_spec_value(indexed_specs, 'battery.life')
        
        return batt
    
    @staticmethod
    def _parse_camera(indexed_specs: Dict) -> UnifiedCamera:
        """Parsea los datos de cámara."""
        cam = UnifiedCamera()
        
        cam.front_camera = IcecatService._get_spec_value(indexed_specs, 'camera.front_camera')
        cam.front_resolution = IcecatService._get_spec_value(indexed_specs, 'camera.front_camera_resolution')
        
        ir = IcecatService._get_spec_value(indexed_specs, 'camera.ir_camera')
        cam.ir_camera = IcecatService._parse_boolean(ir)
        
        privacy = IcecatService._get_spec_value(indexed_specs, 'camera.privacy_shutter')
        cam.privacy_shutter = IcecatService._parse_boolean(privacy)
        
        return cam
    
    @staticmethod
    def _parse_audio(indexed_specs: Dict) -> UnifiedAudio:
        """Parsea los datos de audio."""
        audio = UnifiedAudio()
        
        audio.speakers = IcecatService._get_spec_value(indexed_specs, 'audio.speakers')
        audio.speaker_power = IcecatService._get_spec_value(indexed_specs, 'audio.speaker_power')
        
        mic = IcecatService._get_spec_value(indexed_specs, 'audio.microphone')
        audio.microphone = IcecatService._parse_boolean(mic)
        
        audio.audio_chip = IcecatService._get_spec_value(indexed_specs, 'audio.audio_chip')
        
        return audio
    
    # =========================================================================
    # PARSERS ESPECÍFICOS POR MARCA
    # =========================================================================
    
    @staticmethod
    def _apply_brand_specific_parser(specs: UnifiedSpecs) -> UnifiedSpecs:
        """
        Aplica parsers específicos según la marca del laptop.
        
        Args:
            specs: Especificaciones unificadas
            
        Returns:
            Especificaciones con ajustes específicos de marca
        """
        brand = specs.brand.lower() if specs.brand else ''
        
        if 'lenovo' in brand:
            return IcecatService._parse_lenovo_specific(specs)
        elif 'hp' in brand or 'hewlett' in brand:
            return IcecatService._parse_hp_specific(specs)
        elif 'dell' in brand:
            return IcecatService._parse_dell_specific(specs)
        elif 'apple' in brand or 'mac' in brand:
            return IcecatService._parse_apple_specific(specs)
        elif 'asus' in brand:
            return IcecatService._parse_asus_specific(specs)
        elif 'acer' in brand:
            return IcecatService._parse_acer_specific(specs)
        elif 'msi' in brand:
            return IcecatService._parse_msi_specific(specs)
        elif 'microsoft' in brand or 'surface' in brand:
            return IcecatService._parse_microsoft_specific(specs)
        elif 'lg' in brand:
            return IcecatService._parse_lg_specific(specs)
        elif 'samsung' in brand:
            return IcecatService._parse_samsung_specific(specs)
        
        return specs
    
    @staticmethod
    def _parse_lenovo_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para Lenovo."""
        # Detectar series específicas
        model = specs.model.lower()
        
        # ThinkPad - características empresariales
        if 'thinkpad' in model:
            if not specs.input.pointing_device:
                specs.input.pointing_device = "TrackPoint + ClickPad"
        
        # Legion - características gaming
        if 'legion' in model:
            if not specs.graphics.has_discrete:
                # Legion siempre tiene GPU dedicada
                pass
        
        # Yoga - características 2-en-1
        if 'yoga' in model:
            if not specs.display.touchscreen:
                specs.display.touchscreen = True
        
        return specs
    
    @staticmethod
    def _parse_hp_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para HP."""
        model = specs.model.lower()
        
        # Spectre/Envy - características premium
        if 'spectre' in model or 'envy' in model:
            if not specs.input.fingerprint:
                specs.input.fingerprint = True
        
        # Omen - gaming
        if 'omen' in model:
            if not specs.graphics.has_discrete:
                pass  # Omen siempre tiene GPU dedicada
        
        # EliteBook - empresarial
        if 'elitebook' in model:
            if not specs.security.get('tpm', False):
                pass
        
        return specs
    
    @staticmethod
    def _parse_dell_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para Dell."""
        model = specs.model.lower()
        
        # XPS - premium
        if 'xps' in model:
            if not specs.display.type:
                specs.display.type = "InfinityEdge"
        
        # Alienware - gaming
        if 'alienware' in model:
            if not specs.input.backlight:
                specs.input.backlight = True
                specs.input.backlight_color = "RGB"
        
        # Latitude - empresarial
        if 'latitude' in model:
            if not specs.input.pointing_device:
                specs.input.pointing_device = "Dual Pointing"
        
        return specs
    
    @staticmethod
    def _parse_apple_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para Apple."""
        # Apple Silicon
        if specs.processor.family:
            if 'm1' in specs.processor.family.lower() or 'm2' in specs.processor.family.lower() or \
               'm3' in specs.processor.family.lower() or 'm4' in specs.processor.family.lower():
                specs.processor.manufacturer = "Apple"
                specs.storage.upgradeable = False
                specs.memory.upgradeable = False
        
        # MacBook siempre tiene GPU integrada en el chip
        if not specs.graphics.onboard_model and specs.processor.full_name:
            if 'apple' in specs.processor.full_name.lower():
                specs.graphics.onboard_model = f"Apple GPU ({specs.processor.full_name})"
        
        return specs
    
    @staticmethod
    def _parse_asus_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para ASUS."""
        model = specs.model.lower()
        
        # ROG - gaming
        if 'rog' in model:
            if not specs.input.backlight:
                specs.input.backlight = True
                specs.input.backlight_color = "Aura Sync RGB"
        
        # TUF - gaming durable
        if 'tuf' in model:
            if not specs.physical.weight_kg:
                pass  # TUF suele ser más pesado
        
        # ZenBook - premium
        if 'zenbook' in model:
            if not specs.display.type:
                specs.display.type = "NanoEdge"
        
        return specs
    
    @staticmethod
    def _parse_acer_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para Acer."""
        model = specs.model.lower()
        
        # Predator - gaming high-end
        if 'predator' in model:
            if not specs.input.backlight:
                specs.input.backlight = True
                specs.input.backlight_color = "RGB"
        
        # Nitro - gaming entry
        if 'nitro' in model:
            if not specs.input.backlight:
                specs.input.backlight = True
                specs.input.backlight_color = "Rojo"
        
        # Swift - ultradelgado
        if 'swift' in model:
            if not specs.physical.weight_kg:
                pass  # Swift es ligero
        
        return specs
    
    @staticmethod
    def _parse_msi_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para MSI."""
        model = specs.model.lower()
        
        # MSI es principalmente gaming
        if not specs.input.backlight:
            specs.input.backlight = True
            specs.input.backlight_color = "RGB SteelSeries"
        
        # Series específicas
        if 'raider' in model or 'ge' in model:
            if not specs.display.refresh_rate_hz:
                specs.display.refresh_rate_hz = 240
        
        return specs
    
    @staticmethod
    def _parse_microsoft_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para Microsoft Surface."""
        model = specs.model.lower()
        
        # Surface siempre tiene pantalla táctil
        if 'surface' in model:
            if not specs.display.touchscreen:
                specs.display.touchscreen = True
            
            if not specs.input.stylus:
                specs.input.stylus = True
            
            if not specs.input.face_recognition:
                specs.input.face_recognition = True
        
        # Surface Laptop
        if 'laptop' in model:
            if not specs.display.type:
                specs.display.type = "PixelSense"
        
        return specs
    
    @staticmethod
    def _parse_lg_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para LG."""
        model = specs.model.lower()
        
        # Gram - ultraligero
        if 'gram' in model:
            if not specs.physical.weight_kg or specs.physical.weight_kg > 1.5:
                # Gram es conocido por ser ultraligero
                pass
        
        return specs
    
    @staticmethod
    def _parse_samsung_specific(specs: UnifiedSpecs) -> UnifiedSpecs:
        """Parser específico para Samsung."""
        model = specs.model.lower()
        
        # Galaxy Book
        if 'galaxy book' in model:
            if not specs.input.stylus:
                specs.input.stylus = True
        
        # QLED display
        if not specs.display.type:
            specs.display.type = "QLED"
        
        return specs
    
    # =========================================================================
    # FUNCIONES AUXILIARES DE PARSEO
    # =========================================================================
    
    @staticmethod
    def _extract_description(general_info: Dict) -> str:
        """Extrae la descripción del producto."""
        description_obj = general_info.get('Description', {})
        description = description_obj.get('ShortDesc', '')
        
        if not description:
            summary_info = general_info.get('SummaryDescription', {})
            description = summary_info.get('ShortSummaryDescription', '')
        
        if not description:
            description = general_info.get('Title', '')[:300]
        
        return description
    
    @staticmethod
    def _extract_images(raw_data: Dict) -> List[str]:
        """Extrae las URLs de las imágenes del producto de múltiples fuentes."""
        images = []
        
        # 1. Intentar desde la Galería (Galería completa)
        gallery = raw_data.get('Gallery', [])
        for img in gallery:
            img_url = img.get('Pic', '')
            if img_url and img_url not in images:
                images.append(img_url)
        
        # 2. Intentar desde GeneralInfo (Imagen principal / Alta resolución)
        general_info = raw_data.get('GeneralInfo', {})
        main_pics = [
            general_info.get('MainPic', ''),
            general_info.get('MainPicHighRes', '')
        ]
        
        for pic in main_pics:
            if pic and pic not in images:
                # Insertar al inicio si es la principal
                images.insert(0, pic)
        
        # 3. Intentar desde Multimedia (si existe)
        multimedia = raw_data.get('Multimedia', [])
        for item in multimedia:
            if item.get('Type') == 'ProductImage':
                url = item.get('URL', '')
                if url and url not in images:
                    images.append(url)
                    
        return images
    
    @staticmethod
    def _get_category_name(raw_data: Dict) -> str:
        """Obtiene el nombre de la categoría."""
        category = raw_data.get('Category', {})
        name_obj = category.get('Name', {})
        return name_obj.get('Value', '') if isinstance(name_obj, dict) else str(name_obj)
    
    @staticmethod
    def _build_model_name(brand: str, family: str, series: str, name: str, code: str = None) -> str:
        """
        Construye el nombre del modelo siguiendo la lógica estandarizada y reglas por marca.
        """
        if not (family or series or name or code):
            return name or ""

        brand_upper = brand.upper() if brand else ""
        modelo = ""
        
        # 1. Aplicar reglas por marca
        if 'LENOVO' in brand_upper:
            # Lenovo: Siempre usar name (ya incluye family)
            modelo = name
        
        elif 'APPLE' in brand_upper:
            # Apple: name + series (solo si series agrega info tipo "(M4, 2025)")
            if series and '(' in series:
                modelo = f"{name} {series}"
            else:
                modelo = name
                
        elif 'DELL' in brand_upper:
            # DELL: family + name (si name empieza con número, ej: Latitude 3550)
            if name and name[0].isdigit() and family:
                modelo = f"{family} {name}"
            else:
                modelo = name
                
        elif 'HP' in brand_upper or 'HEWLETT' in brand_upper:
            # HP: family + name (ej: ENVY x360 15...)
            if family and family.lower() not in name.lower():
                modelo = f"{family} {name}"
            else:
                modelo = name
                
        elif 'ASUS' in brand_upper or 'MSI' in brand_upper:
            # Gaming: Evitar duplicados como "Cyborg Cyborg"
            partes = []
            if family: partes.append(family)
            if series and series.lower() not in name.lower() and series.lower() not in (family.lower() if family else ""):
                partes.append(series)
            if name: partes.append(name)
            modelo = " ".join(partes)
            
        elif 'MICROSOFT' in brand_upper or 'SURFACE' in brand_upper:
            # Surface: family + series
            if family and series:
                modelo = f"{family} {series}"
            else:
                modelo = name or family or series or ""
        
        elif 'SAMSUNG' in brand_upper:
            # Samsung: Incluir familia si no está en el nombre (ej: Galaxy Book5 360)
            if family and family.lower() not in name.lower():
                modelo = f"{family} {name}"
            else:
                modelo = name
                
        elif 'GIGABYTE' in brand_upper:
            # Gigabyte: Incluir familia (ej: Gaming)
            if family and family.lower() not in name.lower():
                modelo = f"{family} {name}"
            else:
                modelo = name
            
        # 2. Lógica por defecto (Jerarquía)
        if not modelo:
            if name:
                modelo = name
                # Agregar series si aporta info y no está en el name
                if series and len(series) > 2 and not re.match(r'^\(.*\)$', series):
                    if series.lower() not in name.lower():
                        modelo = f"{series} {name}"
            elif code and len(code) > 5:
                modelo = code
            else:
                partes = [p for p in [family, series] if p]
                modelo = " ".join(partes)

        if not modelo:
            modelo = name or code or family or series or ""

        # 3. Limpieza de duplicados consecutivos (ej: "Cyborg Cyborg 15")
        palabras = modelo.split()
        modelo_limpio = []
        for palabra in palabras:
            if not modelo_limpio or palabra.lower() != modelo_limpio[-1].lower():
                modelo_limpio.append(palabra)
        
        return ' '.join(modelo_limpio).strip()

    @staticmethod
    def _build_display_name(brand: str, model: str, commercial_name: str) -> str:
        """Construye el nombre de visualización del producto."""
        if commercial_name:
            if brand and brand.lower() not in commercial_name.lower():
                return f"{brand} {commercial_name}"
            return commercial_name
        
        if model:
            if brand and brand.lower() not in model.lower():
                return f"{brand} {model}"
            return model
        
        return brand or "Unknown Laptop"
    
    @staticmethod
    def _detect_npu(processor_name: str, npu_info: str) -> bool:
        """Detecta si el procesador tiene NPU."""
        text_to_check = f"{processor_name} {npu_info}".lower()
        
        for keyword in IcecatService.NPU_KEYWORDS:
            if keyword.lower() in text_to_check:
                return True
        
        return False
    
    @staticmethod
    def _infer_gpu_brand(gpu_model: str) -> str:
        """Infiere la marca de la GPU a partir del modelo."""
        gpu_upper = gpu_model.upper()
        
        for brand in IcecatService.DISCRETE_GPU_BRANDS:
            if brand.upper() in gpu_upper:
                return brand
        
        return ""
    
    # =========================================================================
    # FUNCIONES DE PARSEO DE VALORES
    # =========================================================================
    
    @staticmethod
    def _parse_int(value: Any) -> int:
        """Parsea un valor a entero con seguridad extra para puertos."""
        if not value:
            return 0
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            val_lower = value.lower().strip()
            # Si es un indicador booleano de presencia, tratar como cantidad 1
            if val_lower in ['si', 'yes', 'y', 's', 'true', 'v']:
                return 1
            if val_lower in ['no', 'n', 'false', 'f']:
                return 0
                
            # Seguridad: si contiene ":" probablemente es una relación de aspecto (16:10)
            if ":" in value:
                return 0
                
            # Extraer números de la cadena
            numbers = re.findall(r'\d+', value.replace(',', ''))
            if numbers:
                # Si el número es absurdamente alto para un puerto (>32), ignorar
                val = int(numbers[0])
                return val if val <= 32 else 0
        
        try:
            return int(float(value))
        except:
            return 0
    
    @staticmethod
    def _parse_float(value: Any) -> float:
        """Parsea un valor a flotante."""
        if not value:
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Reemplazar coma por punto para decimales
            value = value.replace(',', '.')
            # Extraer números decimales
            numbers = re.findall(r'\d+\.?\d*', value)
            if numbers:
                return float(numbers[0])
        
        try:
            return float(value)
        except:
            return 0.0

    @staticmethod
    def _parse_screen_size(value: str) -> float:
        """Parsea el tamaño de pantalla priorizando pulgadas y detectando conversiones."""
        if not value:
            return 0.0
            
        # Limpiar y normalizar
        value_norm = str(value).replace(',', '.')
        
        # 1. Buscar valor con símbolo de pulgadas (") o "inch" o "pulgada"
        # Ejemplo: 15.6", 15.6 inch, 15.6 pulgada
        inch_match = re.search(r'(\d+\.?\d*)\s*(?:"|inch|pulgada|pulg)', value_norm.lower())
        if inch_match:
            try:
                return float(inch_match.group(1))
            except:
                pass
                
        # 2. Si hay varios números (típico: 39.6 cm (15.6")), buscar el que esté en rango de laptop (10-25)
        numbers = re.findall(r'\d+\.?\d*', value_norm)
        if len(numbers) >= 2:
            for num_str in reversed(numbers): # El último suele ser el de pulgadas en el formato (Inches)
                try:
                    num = float(num_str)
                    if 10 <= num <= 27: # Rango razonable para laptops y monitores pequeños
                        return num
                except:
                    continue
        
        # 3. Si solo hay un número y dice "cm", o el número es muy grande (>27), convertir
        num = IcecatService._parse_float(value)
        if num > 27 or 'cm' in value_norm.lower():
            # Si parece ser cm (basado en la unidad o el valor > 27)
            return round(num / 2.54, 1)
            
        return num
    
    @staticmethod
    def _parse_frequency(value: str) -> float:
        """Parsea una frecuencia a GHz."""
        if not value:
            return 0.0
        
        value_lower = value.lower()
        
        # Detectar unidad
        if 'mhz' in value_lower:
            # Convertir MHz a GHz
            num = IcecatService._parse_float(value)
            return round(num / 1000, 2)
        elif 'ghz' in value_lower or 'hz' in value_lower:
            return IcecatService._parse_float(value)
        
        # Intentar parsear directamente
        return IcecatService._parse_float(value)
    
    @staticmethod
    def _parse_memory_capacity(value: str) -> int:
        """Parsea capacidad de memoria a GB."""
        if not value:
            return 0
        
        value_lower = value.lower()
        
        # Detectar TB
        if 'tb' in value_lower:
            num = IcecatService._parse_float(value)
            return int(num * 1024)
        
        # Detectar MB
        if 'mb' in value_lower:
            num = IcecatService._parse_float(value)
            return max(1, int(num / 1024))
        
        # GB (default)
        return IcecatService._parse_int(value)
    
    @staticmethod
    def _parse_storage_capacity(value: str) -> int:
        """Parsea capacidad de almacenamiento a GB."""
        return IcecatService._parse_memory_capacity(value)
    
    @staticmethod
    def _parse_weight(value: str) -> float:
        """Parsea peso a kg."""
        if not value:
            return 0.0
        
        value_lower = value.lower()
        
        # Detectar gramos
        if 'g' in value_lower and 'kg' not in value_lower:
            num = IcecatService._parse_float(value)
            return round(num / 1000, 3)
        
        # Libras a kg
        if 'lb' in value_lower:
            num = IcecatService._parse_float(value)
            return round(num * 0.453592, 3)
        
        # kg (default)
        return IcecatService._parse_float(value)
    
    @staticmethod
    def _parse_dimension(value: str) -> float:
        """Parsea dimensiones a mm."""
        if not value:
            return 0.0
        
        value_lower = value.lower()
        
        # Detectar cm
        if 'cm' in value_lower:
            num = IcecatService._parse_float(value)
            return num * 10
        
        # Pulgadas a mm
        if '"' in value or 'inch' in value_lower:
            num = IcecatService._parse_float(value)
            return num * 25.4
        
        # mm (default)
        return IcecatService._parse_float(value)
    
    @staticmethod
    def _parse_boolean(value: str) -> bool:
        """Parsea un valor a booleano."""
        if not value:
            return False
        
        value_lower = value.lower().strip()
        
        positive_values = ['yes', 'si', 'sí', 'true', '1', 'y', 'ja', 'oui']
        
        return value_lower in positive_values


# =============================================================================
# CLASE DE VALIDACIÓN DE DATOS
# =============================================================================

class DataValidator:
    """
    Validador de calidad de datos para especificaciones unificadas.
    """
    
    @staticmethod
    def validate_unified_specs(specs: Dict) -> Tuple[bool, List[str]]:
        """
        Valida que las especificaciones unificadas cumplan con los criterios de calidad.
        
        Args:
            specs: Diccionario con especificaciones unificadas
            
        Returns:
            Tuple de (es_válido, lista_de_errores)
        """
        errors = []
        
        # Validar campos obligatorios
        required_checks = [
            ('marca', 'Marca'),
            ('modelo', 'Modelo'),
            ('procesador.nombre_completo', 'Procesador'),
            ('memoria_ram.capacidad_gb', 'Memoria RAM'),
            ('almacenamiento.capacidad_total_gb', 'Almacenamiento'),
            ('pantalla.diagonal_pulgadas', 'Pantalla'),
            ('sistema_operativo', 'Sistema Operativo'),
        ]
        
        for field_path, field_name in required_checks:
            if not DataValidator._get_nested_value(specs, field_path):
                errors.append(f"Campo obligatorio vacío: {field_name}")
        
        # Validar GPU (debe tener al menos una)
        gpu_discrete = DataValidator._get_nested_value(specs, 'tarjeta_grafica.modelo_dedicado')
        gpu_integrated = DataValidator._get_nested_value(specs, 'tarjeta_grafica.modelo_integrado')
        
        if not gpu_discrete and not gpu_integrated:
            errors.append("Debe tener al menos una GPU (dedicada o integrada)")
        
        # Validar consistencia de valores numéricos
        ram_gb = DataValidator._get_nested_value(specs, 'memoria_ram.capacidad_gb')
        if ram_gb and (ram_gb < 1 or ram_gb > 256):
            errors.append(f"Valor de RAM fuera de rango: {ram_gb} GB")
        
        storage_gb = DataValidator._get_nested_value(specs, 'almacenamiento.capacidad_total_gb')
        if storage_gb and (storage_gb < 16 or storage_gb > 8192):
            errors.append(f"Valor de almacenamiento fuera de rango: {storage_gb} GB")
        
        screen_size = DataValidator._get_nested_value(specs, 'pantalla.diagonal_pulgadas')
        if screen_size and (screen_size < 10 or screen_size > 20):
            errors.append(f"Tamaño de pantalla fuera de rango: {screen_size}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _get_nested_value(data: Dict, path: str) -> Any:
        """Obtiene un valor anidado de un diccionario."""
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current


# Exportar clases
__all__ = [
    'IcecatService',
    'DataValidator',
    'UnifiedSpecs',
    'UnifiedProcessor',
    'UnifiedMemory',
    'UnifiedStorage',
    'UnifiedDisplay',
    'UnifiedGraphics',
    'UnifiedConnectivity',
    'UnifiedInput',
    'UnifiedPhysical',
    'UnifiedBattery',
    'UnifiedCamera',
    'UnifiedAudio',
    'UnifiedPort'
]
