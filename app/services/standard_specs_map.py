# -*- coding: utf-8 -*-
"""
================================================================================
MAPEO DE ESPECIFICACIONES ESTÁNDAR DE ICECAT PARA LAPTOPS
================================================================================
Versión: 2.0 - Mejorada y Completa
Fecha: 2025-02-07
Descripción: Mapeo exhaustivo de IDs y nombres de características de Icecat
             para laptops de las 10 principales marcas.

Estructura:
    - Cada categoría contiene campos con múltiples IDs y nombres alternativos
    - Soporta búsqueda por ID numérico o nombre de característica
    - Incluye campos obligatorios y opcionales según estándares de la industria

Marcas soportadas:
    Lenovo, HP, Dell, Apple, ASUS, Acer, MSI, Microsoft, LG, Samsung
================================================================================
"""

# =============================================================================
# MAPEO PRINCIPAL DE ESPECIFICACIONES
# =============================================================================

STANDARD_SPECS_MAP = {
    # =========================================================================
    # PROCESADOR (Processor)
    # =========================================================================
    "processor": {
        # Campos obligatorios
        "family": {
            "ids": [2196, 11379, 6088],
            "names": [
                "Familia de procesador",
                "Processor family",
                "Familia del procesador",
                "Processor Family"
            ],
            "required": True,
            "description": "Familia del procesador (ej: Intel Core i7, AMD Ryzen 7)"
        },
        "manufacturer": {
            "ids": [1013, 6087],
            "names": [
                "Fabricante de procesador",
                "Processor manufacturer",
                "Processor brand"
            ],
            "required": False,
            "description": "Fabricante del procesador (Intel, AMD, Apple)"
        },
        "model": {
            "ids": [47, 2853, 6086],
            "names": [
                "Modelo del procesador",
                "Processor model",
                "Processor Model"
            ],
            "required": True,
            "description": "Modelo específico del procesador (ej: i7-12700H)"
        },
        "generation": {
            "ids": [29830],
            "names": [
                "Generación de procesador",
                "Processor generation",
                "Processor Generation"
            ],
            "required": False,
            "description": "Generación del procesador (ej: 12th Gen, Ryzen 8000)"
        },
        "frequency_base": {
            "ids": [11379, 5, 6085],
            "names": [
                "Frecuencia del procesador",
                "Processor frequency",
                "Processor base frequency",
                "Frecuencia base"
            ],
            "required": True,
            "description": "Frecuencia base del procesador en GHz"
        },
        "frequency_turbo": {
            "ids": [6084, 11380],
            "names": [
                "Frecuencia del procesador turbo",
                "Processor boost frequency",
                "Max turbo frequency",
                "Turbo Boost"
            ],
            "required": False,
            "description": "Frecuencia turbo máxima en GHz"
        },
        "cores": {
            "ids": [6089, 11382],
            "names": [
                "Número de núcleos de procesador",
                "Processor cores",
                "Total cores",
                "Núcleos"
            ],
            "required": True,
            "description": "Cantidad de núcleos físicos"
        },
        "threads": {
            "ids": [7337, 11383],
            "names": [
                "Hilos de ejecución",
                "Processor threads",
                "Total threads",
                "Número de hilos"
            ],
            "required": False,
            "description": "Cantidad de hilos de ejecución"
        },
        "cache": {
            "ids": [10041, 6090],
            "names": [
                "Caché del procesador",
                "Processor cache",
                "Cache memory"
            ],
            "required": False,
            "description": "Caché del procesador (L1, L2, L3)"
        },
        "socket": {
            "ids": [6091],
            "names": [
                "Socket de procesador",
                "Processor socket"
            ],
            "required": False,
            "description": "Tipo de socket del procesador"
        },
        "tdp": {
            "ids": [6092],
            "names": [
                "TDP",
                "Thermal Design Power"
            ],
            "required": False,
            "description": "Potencia térmica de diseño en vatios"
        },
        "lithography": {
            "ids": [6093],
            "names": [
                "Litografía del procesador",
                "Processor lithography"
            ],
            "required": False,
            "description": "Tamaño de los transistores en nm"
        },
        "npu": {
            "ids": [29830, 29831],
            "names": [
                "NPU",
                "Neural Processing Unit",
                "AI Engine",
                "Ryzen AI",
                "Intel AI Boost"
            ],
            "required": False,
            "description": "Unidad de procesamiento neuronal para IA"
        }
    },

    # =========================================================================
    # MEMORIA RAM (Memory)
    # =========================================================================
    "memory": {
        # Campos obligatorios
        "internal": {
            "ids": [11381, 4, 672],
            "names": [
                "Memoria interna",
                "Internal memory",
                "RAM",
                "System memory"
            ],
            "required": True,
            "description": "Cantidad de memoria RAM instalada"
        },
        "type": {
            "ids": [427, 12942],
            "names": [
                "Tipo de memoria interna",
                "Internal memory type",
                "Memory type",
                "RAM type"
            ],
            "required": True,
            "description": "Tipo de memoria (DDR4, DDR5, LPDDR5)"
        },
        "speed": {
            "ids": [2931, 11384],
            "names": [
                "Velocidad de memoria del reloj",
                "Memory clock speed",
                "RAM speed",
                "Memory frequency"
            ],
            "required": True,
            "description": "Velocidad de la memoria en MHz"
        },
        # Campos opcionales
        "max": {
            "ids": [1452, 11385],
            "names": [
                "Memoria interna máxima",
                "Maximum internal memory",
                "Max RAM supported"
            ],
            "required": False,
            "description": "Máxima memoria RAM soportada"
        },
        "slots": {
            "ids": [672, 11386],
            "names": [
                "Ranuras de memoria",
                "Memory slots",
                "RAM slots"
            ],
            "required": False,
            "description": "Número de ranuras de memoria disponibles"
        },
        "form_factor": {
            "ids": [7696, 11387],
            "names": [
                "Forma de factor de memoria",
                "Memory form factor",
                "RAM form factor"
            ],
            "required": False,
            "description": "Factor de forma (SO-DIMM, DIMM)"
        },
        "upgradeable": {
            "ids": [29832],
            "names": [
                "Memoria ampliable",
                "Memory upgradeable",
                "RAM upgradeable"
            ],
            "required": False,
            "description": "Si la memoria es ampliable"
        },
        "channels": {
            "ids": [11388],
            "names": [
                "Canales de memoria",
                "Memory channels"
            ],
            "required": False,
            "description": "Canales de memoria (Single, Dual, Quad)"
        }
    },

    # =========================================================================
    # ALMACENAMIENTO (Storage)
    # =========================================================================
    "storage": {
        # Campos obligatorios
        "total_capacity": {
            "ids": [11375, 3318, 7],
            "names": [
                "Capacidad total de almacenaje",
                "Total storage capacity",
                "Storage capacity"
            ],
            "required": True,
            "description": "Capacidad total de almacenamiento"
        },
        "media": {
            "ids": [11441, 3317],
            "names": [
                "Unidad de almacenamiento",
                "Storage media",
                "Storage type"
            ],
            "required": True,
            "description": "Tipo de almacenamiento (SSD, HDD, eMMC)"
        },
        # Campos opcionales
        "ssd_capacity": {
            "ids": [57369, 11376],
            "names": [
                "Capacidad total de SSD",
                "Total SSDs capacity",
                "SSD capacity"
            ],
            "required": False,
            "description": "Capacidad del SSD si está presente"
        },
        "ssd_interface": {
            "ids": [5579, 11377],
            "names": [
                "Interfaz SSD",
                "SSD interface",
                "SSD form factor"
            ],
            "required": False,
            "description": "Interfaz del SSD (SATA, NVMe, PCIe)"
        },
        "ssd_form_factor": {
            "ids": [5579, 11378],
            "names": [
                "Factor de forma de disco SSD",
                "SSD form factor",
                "SSD size"
            ],
            "required": False,
            "description": "Factor de forma (M.2, 2.5\", etc.)"
        },
        "nvme": {
            "ids": [29833],
            "names": [
                "NVMe",
                "NVMe support"
            ],
            "required": False,
            "description": "Soporte para NVMe"
        },
        "hdd_capacity": {
            "ids": [7, 11389],
            "names": [
                "Capacidad de disco duro",
                "HDD capacity"
            ],
            "required": False,
            "description": "Capacidad del HDD si está presente"
        },
        "hdd_speed": {
            "ids": [11390],
            "names": [
                "Velocidad de disco duro",
                "HDD speed"
            ],
            "required": False,
            "description": "Velocidad de rotación del HDD"
        },
        "upgradeable": {
            "ids": [29834],
            "names": [
                "Almacenamiento ampliable",
                "Storage upgradeable"
            ],
            "required": False,
            "description": "Si el almacenamiento es ampliable"
        }
    },

    # =========================================================================
    # PANTALLA (Display)
    # =========================================================================
    "display": {
        # Campos obligatorios
        "diagonal": {
            "ids": [944, 1584],
            "names": [
                "Diagonal de la pantalla",
                "Display diagonal",
                "Screen size"
            ],
            "required": True,
            "description": "Tamaño de la pantalla en pulgadas"
        },
        "resolution": {
            "ids": [1585, 11391],
            "names": [
                "Resolución de la pantalla",
                "Display resolution",
                "Screen resolution"
            ],
            "required": True,
            "description": "Resolución de pantalla (1920x1080, etc.)"
        },
        # Campos opcionales
        "type": {
            "ids": [15285, 11392],
            "names": [
                "Tipo de pantalla",
                "Display type",
                "Panel type",
                "Panel technology"
            ],
            "required": False,
            "description": "Tipo de panel (IPS, OLED, TN, etc.)"
        },
        "hd_type": {
            "ids": [11393, 15286],
            "names": [
                "Tipo HD",
                "HD type",
                "Display HD type"
            ],
            "required": False,
            "description": "Tipo HD (Full HD, 4K UHD, etc.)"
        },
        "touchscreen": {
            "ids": [4963, 11394],
            "names": [
                "Pantalla táctil",
                "Touchscreen",
                "Touch display"
            ],
            "required": False,
            "description": "Si la pantalla es táctil"
        },
        "refresh_rate": {
            "ids": [29829, 11395],
            "names": [
                "Máxima velocidad de actualización",
                "Maximum refresh rate",
                "Refresh rate"
            ],
            "required": False,
            "description": "Tasa de refresco en Hz"
        },
        "brightness": {
            "ids": [13887, 11396],
            "names": [
                "Brillo de pantalla",
                "Display brightness"
            ],
            "required": False,
            "description": "Brillo máximo en nits"
        },
        "color_gamut": {
            "ids": [29835],
            "names": [
                "Gama de colores",
                "Color gamut",
                "sRGB coverage"
            ],
            "required": False,
            "description": "Cobertura de gama de colores"
        },
        "aspect_ratio": {
            "ids": [11397],
            "names": [
                "Relación de aspecto",
                "Aspect ratio"
            ],
            "required": False,
            "description": "Relación de aspecto (16:9, 16:10, 3:2)"
        },
        "surface": {
            "ids": [11398],
            "names": [
                "Superficie de pantalla",
                "Display surface"
            ],
            "required": False,
            "description": "Tipo de superficie (Mate, Brillante)"
        },
        "hdr": {
            "ids": [29836],
            "names": [
                "HDR",
                "High Dynamic Range"
            ],
            "required": False,
            "description": "Soporte HDR"
        }
    },

    # =========================================================================
    # GRÁFICOS (Graphics)
    # =========================================================================
    "graphics": {
        # Campos obligatorios
        "discrete_model": {
            "ids": [9018, 11400],
            "names": [
                "Modelo de adaptador de gráficos discretos",
                "Discrete graphics card model",
                "Discrete GPU"
            ],
            "required": False,  # Puede no tener GPU dedicada
            "description": "Modelo de GPU dedicada si existe"
        },
        "discrete_memory": {
            "ids": [18403, 11401],
            "names": [
                "Capacidad memoria de adaptador gráfico",
                "Discrete graphics card memory",
                "GPU memory"
            ],
            "required": False,
            "description": "Memoria VRAM de la GPU dedicada"
        },
        "onboard_model": {
            "ids": [9016, 11399],
            "names": [
                "Modelo de adaptador gráfico incorporado",
                "On-board graphics card model",
                "Integrated graphics"
            ],
            "required": True,
            "description": "GPU integrada en el procesador"
        },
        # Campos opcionales
        "discrete_brand": {
            "ids": [11402],
            "names": [
                "Marca de adaptador de gráficos discretos",
                "Discrete graphics card brand"
            ],
            "required": False,
            "description": "Marca de la GPU dedicada (NVIDIA, AMD)"
        },
        "onboard_brand": {
            "ids": [11403],
            "names": [
                "Marca de adaptador gráfico incorporado",
                "On-board graphics card brand"
            ],
            "required": False,
            "description": "Marca de la GPU integrada"
        },
        "ray_tracing": {
            "ids": [29837],
            "names": [
                "Ray Tracing",
                "RTX"
            ],
            "required": False,
            "description": "Soporte para Ray Tracing"
        },
        "dlss": {
            "ids": [29838],
            "names": [
                "DLSS",
                "FSR"
            ],
            "required": False,
            "description": "Soporte para tecnologías de upscaling"
        }
    },

    # =========================================================================
    # BATERÍA (Battery)
    # =========================================================================
    "battery": {
        "technology": {
            "ids": [434, 11404],
            "names": [
                "Tecnología de batería",
                "Battery technology"
            ],
            "required": False,
            "description": "Tecnología de la batería (Li-Ion, Li-Po)"
        },
        "capacity_wh": {
            "ids": [909, 11405],
            "names": [
                "Capacidad de batería (vatio-hora)",
                "Battery capacity (Watt-hours)",
                "Battery Wh"
            ],
            "required": False,
            "description": "Capacidad en vatios-hora"
        },
        "capacity_mah": {
            "ids": [11406],
            "names": [
                "Capacidad de batería (mAh)",
                "Battery capacity (mAh)"
            ],
            "required": False,
            "description": "Capacidad en miliamperios-hora"
        },
        "cells": {
            "ids": [1227, 11407],
            "names": [
                "Número de celdas de batería",
                "Number of battery cells"
            ],
            "required": False,
            "description": "Número de celdas de la batería"
        },
        "life": {
            "ids": [11408],
            "names": [
                "Duración de batería",
                "Battery life"
            ],
            "required": False,
            "description": "Duración estimada de la batería"
        }
    },

    # =========================================================================
    # DIMENSIONES Y PESO (Physical)
    # =========================================================================
    "physical": {
        # Campos obligatorios
        "weight": {
            "ids": [94, 11409],
            "names": [
                "Peso",
                "Weight"
            ],
            "required": True,
            "description": "Peso del laptop"
        },
        # Campos opcionales
        "width": {
            "ids": [1649, 11410],
            "names": [
                "Ancho",
                "Width"
            ],
            "required": False,
            "description": "Ancho del laptop"
        },
        "depth": {
            "ids": [1650, 11411],
            "names": [
                "Profundidad",
                "Depth"
            ],
            "required": False,
            "description": "Profundidad del laptop"
        },
        "height": {
            "ids": [1651, 11412],
            "names": [
                "Altura",
                "Height"
            ],
            "required": False,
            "description": "Altura/ grosor del laptop"
        },
        "thickness": {
            "ids": [29839],
            "names": [
                "Grosor",
                "Thickness"
            ],
            "required": False,
            "description": "Grosor del laptop"
        }
    },

    # =========================================================================
    # SOFTWARE (Software)
    # =========================================================================
    "software": {
        # Campos obligatorios
        "os": {
            "ids": [3233, 11413],
            "names": [
                "Sistema operativo instalado",
                "Operating system installed",
                "OS"
            ],
            "required": True,
            "description": "Sistema operativo preinstalado"
        },
        # Campos opcionales
        "os_arch": {
            "ids": [4372, 11414],
            "names": [
                "Arquitectura del sistema operativo",
                "Operating system architecture"
            ],
            "required": False,
            "description": "Arquitectura (64-bit, 32-bit)"
        },
        "os_version": {
            "ids": [11415],
            "names": [
                "Versión del sistema operativo",
                "OS version"
            ],
            "required": False,
            "description": "Versión específica del SO"
        }
    },

    # =========================================================================
    # CONECTIVIDAD (Connectivity)
    # =========================================================================
    "connectivity": {
        # Puertos USB
        "usb_2_0": {
            "ids": [2308],
            "names": [
                "Cantidad de puertos USB 2.0",
                "USB 2.0 ports quantity",
                "Puertos USB 2.0"
            ],
            "required": False,
            "description": "Número de puertos USB 2.0"
        },
        "usb_3_2_gen1": {
            "ids": [6768, 13311],
            "names": [
                "Cantidad de puertos tipo A USB 3.2 Gen 1 (3.1 Gen 1)",
                "USB 3.2 Gen 1 ports quantity",
                "USB 3.1 Gen 1"
            ],
            "required": False,
            "description": "Número de puertos USB 3.2 Gen 1"
        },
        "usb_3_2_gen2": {
            "ids": [22703, 13312],
            "names": [
                "Cantidad de puertos tipo A USB 3.2 Gen 2 (3.1 Gen 2)",
                "USB 3.2 Gen 2 ports quantity",
                "USB 3.1 Gen 2"
            ],
            "required": False,
            "description": "Número de puertos USB 3.2 Gen 2"
        },
        "usb_c": {
            "ids": [13311, 13312, 20805],
            "names": [
                "Cantidad de puertos tipo C USB 3.2 Gen 1 (3.1 Gen 1)",
                "Cantidad de puertos tipo C USB 3.2 Gen 2 (3.1 Gen 2)",
                "USB Type-C ports quantity"
            ],
            "required": False,
            "description": "Número de puertos USB-C"
        },
        "usb4": {
            "ids": [42559],
            "names": [
                "Número de puertos USB4 Gen 3×2",
                "USB4 ports quantity",
                "USB4"
            ],
            "required": False,
            "description": "Número de puertos USB4"
        },
        "thunderbolt": {
            "ids": [22325, 21614, 32700],
            "names": [
                "Cantidad de puertos Thunderbolt",
                "Thunderbolt ports quantity",
                "Thunderbolt 3",
                "Thunderbolt 4"
            ],
            "required": False,
            "description": "Puertos Thunderbolt"
        },
        # Video
        "hdmi": {
            "ids": [3566],
            "names": [
                "Cantidad de puertos HDMI",
                "HDMI ports quantity",
                "Número de puertos HDMI"
            ],
            "required": False,
            "description": "Número de puertos HDMI"
        },
        "hdmi_version": {
            "ids": [5452, 29840],
            "names": [
                "Versión HDMI",
                "HDMI version"
            ],
            "required": False,
            "description": "Versión de HDMI (2.0, 2.1)"
        },
        "displayport": {
            "ids": [3078, 11422],
            "names": [
                "DisplayPort",
                "DisplayPort quantity",
                "Cantidad de DisplayPorts"
            ],
            "required": False,
            "description": "Puertos DisplayPort"
        },
        "vga": {
            "ids": [2310, 11423],
            "names": [
                "VGA",
                "VGA (D-Sub)",
                "Cantidad de puertos VGA"
            ],
            "required": False,
            "description": "Puerto VGA"
        },
        # Red
        "ethernet": {
            "ids": [2312, 11424],
            "names": [
                "Ethernet LAN (RJ-45)",
                "Ethernet ports quantity",
                "Ethernet LAN (RJ-45) cantidad de puertos"
            ],
            "required": False,
            "description": "Puerto Ethernet RJ-45"
        },
        "ethernet_speed": {
            "ids": [29841],
            "names": [
                "Velocidad Ethernet",
                "Ethernet speed"
            ],
            "required": False,
            "description": "Velocidad de Ethernet"
        },
        # Audio
        "audio_jack": {
            "ids": [9858, 11425],
            "names": [
                "Combo de salida de auriculares / micrófono",
                "Combo headphone/mic port",
                "Audio jack",
                "Combo de salida de auriculares / micrófono del puerto"
            ],
            "required": False,
            "description": "Jack de audio 3.5mm"
        },
        # Lectores
        "sd_card": {
            "ids": [11426],
            "names": [
                "Lector de tarjeta de memoria",
                "Card reader"
            ],
            "required": False,
            "description": "Lector de tarjetas SD"
        },
        "smartcard": {
            "ids": [11427],
            "names": [
                "Lector de tarjeta inteligente",
                "SmartCard slot"
            ],
            "required": False,
            "description": "Lector de tarjetas inteligentes"
        },
        # Wireless
        "wifi": {
            "ids": [11428],
            "names": [
                "Wi-Fi",
                "Wireless LAN"
            ],
            "required": False,
            "description": "Estándar Wi-Fi"
        },
        "bluetooth": {
            "ids": [11429],
            "names": [
                "Bluetooth",
                "Bluetooth version"
            ],
            "required": False,
            "description": "Versión de Bluetooth"
        },
        "cellular": {
            "ids": [29842],
            "names": [
                "4G LTE",
                "5G",
                "Cellular"
            ],
            "required": False,
            "description": "Conectividad celular"
        },
        "nfc": {
            "ids": [29843],
            "names": [
                "NFC"
            ],
            "required": False,
            "description": "Soporte NFC"
        }
    },

    # =========================================================================
    # TECLADO Y ENTRADA (Input)
    # =========================================================================
    "input": {
        "keyboard_layout": {
            "ids": [11430],
            "names": [
                "Disposición del teclado",
                "Keyboard layout"
            ],
            "required": False,
            "description": "Distribución del teclado"
        },
        "numeric_keypad": {
            "ids": [11431],
            "names": [
                "Teclado numérico",
                "Numeric keypad"
            ],
            "required": False,
            "description": "Teclado numérico integrado"
        },
        "backlight": {
            "ids": [11432],
            "names": [
                "Retroiluminación de teclado",
                "Keyboard backlight"
            ],
            "required": False,
            "description": "Retroiluminación del teclado"
        },
        "backlight_color": {
            "ids": [29844],
            "names": [
                "Color de la retroiluminación del teclado",
                "Keyboard backlight color"
            ],
            "required": False,
            "description": "Color de la retroiluminación"
        },
        "keyboard_language": {
            "ids": [11433],
            "names": [
                "Idioma del teclado",
                "Keyboard language"
            ],
            "required": False,
            "description": "Idioma del teclado"
        },
        "pointing_device": {
            "ids": [11434],
            "names": [
                "Dispositivo señalador",
                "Pointing device"
            ],
            "required": False,
            "description": "Dispositivo apuntador (touchpad, trackpoint)"
        },
        "fingerprint": {
            "ids": [29845],
            "names": [
                "Lector de huellas dactilares",
                "Fingerprint reader"
            ],
            "required": False,
            "description": "Lector de huellas dactilares"
        },
        "face_recognition": {
            "ids": [29846],
            "names": [
                "Reconocimiento facial",
                "Face recognition"
            ],
            "required": False,
            "description": "Reconocimiento facial (Windows Hello)"
        },
        "stylus": {
            "ids": [29847],
            "names": [
                "Lápiz óptico",
                "Stylus support"
            ],
            "required": False,
            "description": "Soporte para lápiz óptico"
        }
    },

    # =========================================================================
    # CÁMARA (Camera)
    # =========================================================================
    "camera": {
        "front_camera": {
            "ids": [11435],
            "names": [
                "Cámara frontal",
                "Front camera"
            ],
            "required": False,
            "description": "Cámara web integrada"
        },
        "front_camera_resolution": {
            "ids": [29848],
            "names": [
                "Resolución de cámara frontal",
                "Front camera resolution"
            ],
            "required": False,
            "description": "Resolución de la cámara frontal"
        },
        "ir_camera": {
            "ids": [29849],
            "names": [
                "Cámara IR",
                "IR camera"
            ],
            "required": False,
            "description": "Cámara infrarroja para Windows Hello"
        },
        "privacy_shutter": {
            "ids": [29850],
            "names": [
                "Cubierta de privacidad",
                "Privacy shutter"
            ],
            "required": False,
            "description": "Cubierta de privacidad para cámara"
        }
    },

    # =========================================================================
    # AUDIO (Audio)
    # =========================================================================
    "audio": {
        "speakers": {
            "ids": [11436],
            "names": [
                "Altavoces",
                "Speakers"
            ],
            "required": False,
            "description": "Altavoces integrados"
        },
        "speaker_power": {
            "ids": [29851],
            "names": [
                "Potencia de altavoz",
                "Speaker power"
            ],
            "required": False,
            "description": "Potencia de los altavoces"
        },
        "microphone": {
            "ids": [11437],
            "names": [
                "Micrófono",
                "Built-in microphone"
            ],
            "required": False,
            "description": "Micrófono integrado"
        },
        "audio_chip": {
            "ids": [29852],
            "names": [
                "Chip de audio",
                "Audio chip"
            ],
            "required": False,
            "description": "Chip de audio"
        }
    },

    # =========================================================================
    # SEGURIDAD (Security)
    # =========================================================================
    "security": {
        "tpm": {
            "ids": [29853],
            "names": [
                "Módulo de plataforma segura (TPM)",
                "Trusted Platform Module (TPM)"
            ],
            "required": False,
            "description": "Chip TPM para seguridad"
        },
        "kensington_lock": {
            "ids": [29854],
            "names": [
                "Ranura para cable de seguridad",
                "Kensington lock"
            ],
            "required": False,
            "description": "Ranura para candado Kensington"
        }
    },

    # =========================================================================
    # CERTIFICACIONES (Certifications)
    # =========================================================================
    "certifications": {
        "energy_star": {
            "ids": [29855],
            "names": [
                "Energy Star",
                "ENERGY STAR certified"
            ],
            "required": False,
            "description": "Certificación Energy Star"
        },
        "eceee": {
            "ids": [29856],
            "names": [
                "EPEAT",
                "EPEAT compliance"
            ],
            "required": False,
            "description": "Certificación EPEAT"
        },
        "rohs": {
            "ids": [29857],
            "names": [
                "RoHS",
                "RoHS compliance"
            ],
            "required": False,
            "description": "Cumplimiento RoHS"
        }
    }
}


# =============================================================================
# MAPEO ESPECÍFICO POR MARCA
# =============================================================================

BRAND_SPECIFIC_MAP = {
    "lenovo": {
        "series_names": ["ThinkPad", "IdeaPad", "Legion", "Yoga", "V-Series", "ThinkBook"],
        "specific_fields": {
            "thinkpad_features": ["TrackPoint", "ThinkShutter", "MIL-STD"],
            "legion_features": ["Legion Coldfront", "TrueStrike"]
        }
    },
    "hp": {
        "series_names": ["Pavilion", "Envy", "Spectre", "Omen", "EliteBook", "ProBook", "ZBook"],
        "specific_fields": {
            "hp_features": ["HP Sure View", "HP Fast Charge", "Bang & Olufsen"]
        }
    },
    "dell": {
        "series_names": ["XPS", "Inspiron", "Latitude", "Precision", "Alienware", "Vostro"],
        "specific_fields": {
            "dell_features": ["Dell Cinema", "Dell Optimizer", "ExpressCharge"]
        }
    },
    "apple": {
        "series_names": ["MacBook Air", "MacBook Pro", "MacBook"],
        "specific_fields": {
            "apple_silicon": ["M1", "M2", "M3", "M4"],
            "apple_features": ["Touch ID", "Retina", "Liquid Retina"]
        }
    },
    "asus": {
        "series_names": ["ROG", "TUF", "ZenBook", "VivoBook", "ProArt", "ExpertBook"],
        "specific_fields": {
            "rog_features": ["Aura Sync", "ROG Intelligent Cooling"],
            "tuf_features": ["MIL-STD-810H"]
        }
    },
    "acer": {
        "series_names": ["Aspire", "Nitro", "Predator", "Swift", "Spin", "TravelMate"],
        "specific_fields": {
            "predator_features": ["PredatorSense", "AeroBlade"],
            "nitro_features": ["NitroSense"]
        }
    },
    "msi": {
        "series_names": ["Raider", "Stealth", "Vector", "Katana", "GF", "GS", "GE", "GT"],
        "specific_fields": {
            "msi_features": ["MSI Center", "Cooler Boost", "SteelSeries"]
        }
    },
    "microsoft": {
        "series_names": ["Surface Laptop", "Surface Book", "Surface Pro"],
        "specific_fields": {
            "surface_features": ["PixelSense", "Surface Pen", "Windows Hello"]
        }
    },
    "lg": {
        "series_names": ["Gram", "Ultra", "UltraGear"],
        "specific_fields": {
            "lg_features": ["DTS:X Ultra", "Mirametrix"]
        }
    },
    "samsung": {
        "series_names": ["Galaxy Book", "Notebook", "Odyssey"],
        "specific_fields": {
            "samsung_features": ["QLED", "S Pen", "Samsung DeX"]
        }
    }
}


# =============================================================================
# CAMPOS OBLIGATORIOS PARA VALIDACIÓN
# =============================================================================

REQUIRED_FIELDS = {
    "processor": ["family", "model", "frequency_base", "cores"],
    "memory": ["internal", "type", "speed"],
    "storage": ["total_capacity", "media"],
    "display": ["diagonal", "resolution"],
    "graphics": ["onboard_model"],
    "physical": ["weight"],
    "software": ["os"]
}


# =============================================================================
# UNIDADES DE MEDIDA ESTÁNDAR
# =============================================================================

STANDARD_UNITS = {
    "frequency": "GHz",
    "memory": "GB",
    "storage": "GB",
    "screen_size": '"',
    "weight": "kg",
    "dimensions": "mm",
    "battery": "Wh",
    "refresh_rate": "Hz",
    "brightness": "nits"
}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def get_field_ids(field_path):
    """
    Obtiene los IDs de un campo específico del mapa.
    
    Args:
        field_path: Ruta al campo (ej: "processor.family")
    
    Returns:
        Lista de IDs o lista vacía si no existe
    """
    parts = field_path.split('.')
    current = STANDARD_SPECS_MAP
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return []
    
    return current.get('ids', [])


def get_field_names(field_path):
    """
    Obtiene los nombres alternativos de un campo específico.
    
    Args:
        field_path: Ruta al campo (ej: "processor.family")
    
    Returns:
        Lista de nombres o lista vacía si no existe
    """
    parts = field_path.split('.')
    current = STANDARD_SPECS_MAP
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return []
    
    return current.get('names', [])


def is_required_field(category, field):
    """
    Verifica si un campo es obligatorio.
    
    Args:
        category: Categoría del campo
        field: Nombre del campo
    
    Returns:
        True si es obligatorio, False en caso contrario
    """
    if category in STANDARD_SPECS_MAP:
        if field in STANDARD_SPECS_MAP[category]:
            return STANDARD_SPECS_MAP[category][field].get('required', False)
    return False


def get_all_required_fields():
    """
    Obtiene todos los campos obligatorios organizados por categoría.
    
    Returns:
        Diccionario con campos obligatorios por categoría
    """
    required = {}
    for category, fields in STANDARD_SPECS_MAP.items():
        required[category] = [
            field_name for field_name, field_def in fields.items()
            if field_def.get('required', False)
        ]
    return required


def get_field_description(field_path):
    """
    Obtiene la descripción de un campo.
    
    Args:
        field_path: Ruta al campo
    
    Returns:
        Descripción del campo o cadena vacía
    """
    parts = field_path.split('.')
    current = STANDARD_SPECS_MAP
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return ""
    
    return current.get('description', '')


# =============================================================================
# MAPEO DE PUERTOS PARA CONECTIVIDAD
# =============================================================================

PORT_FEATURE_IDS = {
    "usb_2_0": [2308, 11416, 29858],
    "usb_3_2_gen1": [6768, 11417, 29859],
    "usb_3_2_gen2": [22703, 11418, 29860],
    "usb_c": [13311, 13312, 20805, 11419, 29861],
    "usb4": [42559],
    "thunderbolt_3": [21614, 29862],
    "thunderbolt_4": [32700, 29863],
    "hdmi": [3566, 11421, 29864],
    "hdmi_2_1": [29865],
    "displayport": [3078, 11422, 29866],
    "mini_displayport": [11319, 29867],
    "vga": [2310, 11423, 29868],
    "ethernet": [2312, 11424, 29869],
    "audio_jack": [9858, 11425, 29870],
    "sd_card": [1231, 11426, 29871],
    "microsd": [29872],
    "smartcard": [11427, 29873]
}

PORT_NAMES = {
    "usb_2_0": ["USB 2.0", "USB-A 2.0"],
    "usb_3_2_gen1": ["USB 3.2 Gen 1", "USB-A 3.2 Gen 1", "USB 3.0", "USB 3.1 Gen 1"],
    "usb_3_2_gen2": ["USB 3.2 Gen 2", "USB-A 3.2 Gen 2", "USB 3.1 Gen 2"],
    "usb_c_3_2_gen1": ["USB-C 3.2 Gen 1"],
    "usb_c_3_2_gen2": ["USB-C 3.2 Gen 2"],
    "usb4": ["USB4", "USB4 Gen 3x2"],
    "thunderbolt_3": ["Thunderbolt 3"],
    "thunderbolt_4": ["Thunderbolt 4"],
    "hdmi": ["HDMI"],
    "hdmi_2_0": ["HDMI 2.0"],
    "hdmi_2_1": ["HDMI 2.1"],
    "displayport": ["DisplayPort"],
    "mini_displayport": ["Mini DisplayPort"],
    "vga": ["VGA", "D-Sub"],
    "ethernet": ["Ethernet", "RJ-45"],
    "audio_jack": ["Audio Jack", "3.5mm Jack", "Combo de salida de auriculares"],
    "sd_card": ["SD Card", "SD Reader"],
    "microsd": ["MicroSD"],
    "smartcard": ["SmartCard"]
}


# Exportar todo
__all__ = [
    'STANDARD_SPECS_MAP',
    'BRAND_SPECIFIC_MAP',
    'REQUIRED_FIELDS',
    'STANDARD_UNITS',
    'PORT_FEATURE_IDS',
    'PORT_NAMES',
    'get_field_ids',
    'get_field_names',
    'is_required_field',
    'get_all_required_fields',
    'get_field_description'
]
