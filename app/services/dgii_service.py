# ============================================
# SERVICIO DE CONSULTA A LA DGII OFICIAL - VERSIÓN CORREGIDA
# ============================================

import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)


class DGIIService:
    """
    Servicio para consultar información de RNC/Cédula en la DGII oficial
    """

    # URLs actualizadas
    DGII_RNC_URL = "https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/rnc.aspx"
    DGII_CEDULA_URL = "https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/cedula.aspx"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://dgii.gov.do',
        'Referer': 'https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/cedula.aspx',
    }

    @classmethod
    def validate_and_get_info(cls, id_number: str, id_type: str = 'cedula') -> Dict:
        """Valida y obtiene información desde DGII oficial"""
        try:
            clean_id = id_number.replace('-', '').replace(' ', '').strip()

            logger.info(f"Consultando DGII: {id_type} {clean_id}")

            # Validar formato
            if id_type == 'cedula':
                if not re.match(r'^\d{11}$', clean_id):
                    return {'success': False, 'error': 'Cédula debe tener 11 dígitos'}
                # Consultar DGII para cédula
                result = cls._consultar_dgii_cedula(clean_id)
            else:  # rnc
                if not re.match(r'^(\d{9}|\d{11})$', clean_id):
                    return {'success': False, 'error': 'RNC debe tener 9 u 11 dígitos'}
                # Consultar DGII para RNC
                result = cls._consultar_dgii_rnc(clean_id)

            return result

        except Exception as e:
            logger.error(f"Error consultando DGII: {str(e)}", exc_info=True)
            # Fallback a validación local si hay error
            return cls._local_validation(id_number, id_type)

    @classmethod
    def _consultar_dgii_cedula(cls, id_number: str) -> Dict:
        """Consulta datos de cédula en la DGII - VERSIÓN CORREGIDA"""
        try:
            session = requests.Session()
            session.headers.update(cls.HEADERS)

            # Formatear cédula: 001-1234567-8
            formatted_id = f"{id_number[:3]}-{id_number[3:10]}-{id_number[10]}"
            logger.info(f"Consultando cédula DGII: {formatted_id}")

            # Paso 1: Obtener página inicial
            response = session.get(cls.DGII_CEDULA_URL, timeout=10)

            if response.status_code != 200:
                logger.error(f"Error al cargar página DGII: {response.status_code}")
                return cls._local_validation(id_number, 'cedula')

            soup = BeautifulSoup(response.text, 'html.parser')

            # Paso 2: Obtener campos del formulario ASP.NET
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstategen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            eventval = soup.find('input', {'name': '__EVENTVALIDATION'})

            if not all([viewstate, viewstategen, eventval]):
                logger.warning("No se encontraron campos ASP.NET necesarios")
                return cls._local_validation(id_number, 'cedula')

            # Paso 3: Preparar datos del formulario
            form_data = {
                '__VIEWSTATE': viewstate.get('value', ''),
                '__VIEWSTATEGENERATOR': viewstategen.get('value', ''),
                '__EVENTVALIDATION': eventval.get('value', ''),
                'ctl00$cphMain$txtCedula': formatted_id,
                'ctl00$cphMain$btnBuscar': 'Buscar',
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': ''
            }

            logger.info(f"Enviando consulta para cédula: {formatted_id}")

            # Paso 4: Enviar consulta
            response = session.post(cls.DGII_CEDULA_URL, data=form_data, timeout=15)

            if response.status_code != 200:
                logger.error(f"Error en consulta DGII: {response.status_code}")
                return cls._local_validation(id_number, 'cedula')

            # Paso 5: Parsear resultados - BASADO EN LA IMAGEN PROPORCIONADA
            soup = BeautifulSoup(response.text, 'html.parser')

            # Guardar para depuración (opcional)
            # with open('dgii_response.html', 'w', encoding='utf-8') as f:
            #     f.write(response.text)

            # Buscar la tabla de resultados
            # En la imagen, los datos están en una tabla
            nombre_completo = None
            estado = None

            # Método 1: Buscar por texto en celdas
            all_cells = soup.find_all(['td', 'th'])

            for i, cell in enumerate(all_cells):
                cell_text = cell.get_text(strip=True)

                # Buscar "Nombre/Razón Social"
                if 'nombre' in cell_text.lower() and 'razón' in cell_text.lower():
                    # El valor está en la siguiente celda
                    if i + 1 < len(all_cells):
                        next_cell = all_cells[i + 1]
                        nombre_completo = next_cell.get_text(strip=True)
                        logger.info(f"Nombre encontrado: {nombre_completo}")

                # Buscar "Estado"
                elif 'estado' in cell_text.lower():
                    if i + 1 < len(all_cells):
                        next_cell = all_cells[i + 1]
                        estado = next_cell.get_text(strip=True)
                        logger.info(f"Estado encontrado: {estado}")

            # Método 2: Si no encontramos, buscar en tablas
            if not nombre_completo:
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for j, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            if 'nombre' in cell_text.lower() and 'razón' in cell_text.lower():
                                if j + 1 < len(cells):
                                    nombre_completo = cells[j + 1].get_text(strip=True)
                                    break
                            elif 'estado' in cell_text.lower():
                                if j + 1 < len(cells):
                                    estado = cells[j + 1].get_text(strip=True)
                                    break

                    if nombre_completo:
                        break

            # Si encontramos el nombre, procesarlo
            if nombre_completo:
                # Dividir nombre completo en partes
                nombre_parts = nombre_completo.split()

                # Estrategia: asumir que el último elemento es el apellido
                if len(nombre_parts) >= 2:
                    # Tomar el último elemento como apellido
                    last_name = nombre_parts[-1]
                    # Todos los demás como nombre
                    first_name = ' '.join(nombre_parts[:-1])
                else:
                    first_name = nombre_completo
                    last_name = ''

                return {
                    'success': True,
                    'id_number': id_number,
                    'id_type': 'cedula',
                    'first_name': first_name,
                    'last_name': last_name,
                    'full_name': nombre_completo,
                    'status': estado or 'ACTIVO',
                    'validation_mode': 'dgii'
                }

            # Si no encontramos datos, verificar si hay mensaje de error
            error_msg = soup.find(text=re.compile(r'no se encontraron resultados|cedula no existe', re.IGNORECASE))
            if error_msg:
                return {
                    'success': False,
                    'error': 'No se encontraron datos para esta cédula en la DGII'
                }

            return cls._local_validation(id_number, 'cedula')

        except requests.Timeout:
            logger.error("Timeout al consultar DGII")
            return cls._local_validation(id_number, 'cedula')
        except Exception as e:
            logger.error(f"Error consultando DGII: {str(e)}", exc_info=True)
            return cls._local_validation(id_number, 'cedula')

    @classmethod
    def _consultar_dgii_rnc(cls, id_number: str) -> Dict:
        """Consulta datos de RNC en la DGII - VERSIÓN CORREGIDA"""
        try:
            session = requests.Session()
            session.headers.update(cls.HEADERS)

            # Formatear RNC según su longitud
            if len(id_number) == 9:
                formatted_id = f"{id_number[:1]}-{id_number[1:3]}-{id_number[3:8]}-{id_number[8]}"
            else:  # 11 dígitos
                formatted_id = f"{id_number[:3]}-{id_number[3:10]}-{id_number[10]}"

            logger.info(f"Consultando RNC DGII: {formatted_id}")

            # Paso 1: Obtener página inicial
            response = session.get(cls.DGII_RNC_URL, timeout=10)

            if response.status_code != 200:
                logger.error(f"Error al cargar página DGII: {response.status_code}")
                return cls._local_validation(id_number, 'rnc')

            soup = BeautifulSoup(response.text, 'html.parser')

            # Paso 2: Obtener campos del formulario
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstategen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            eventval = soup.find('input', {'name': '__EVENTVALIDATION'})

            if not all([viewstate, viewstategen, eventval]):
                logger.warning("No se encontraron campos ASP.NET necesarios")
                return cls._local_validation(id_number, 'rnc')

            # Paso 3: Preparar datos del formulario
            form_data = {
                '__VIEWSTATE': viewstate.get('value', ''),
                '__VIEWSTATEGENERATOR': viewstategen.get('value', ''),
                '__EVENTVALIDATION': eventval.get('value', ''),
                'ctl00$cphMain$txtRNC': formatted_id,
                'ctl00$cphMain$btnBuscar': 'Buscar',
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': ''
            }

            logger.info(f"Enviando consulta para RNC: {formatted_id}")

            # Paso 4: Enviar consulta
            response = session.post(cls.DGII_RNC_URL, data=form_data, timeout=15)

            if response.status_code != 200:
                logger.error(f"Error en consulta DGII: {response.status_code}")
                return cls._local_validation(id_number, 'rnc')

            # Paso 5: Parsear resultados - SIMILAR A CÉDULA
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar la tabla de resultados
            nombre_empresa = None
            estado = None

            # Buscar por texto en celdas
            all_cells = soup.find_all(['td', 'th'])

            for i, cell in enumerate(all_cells):
                cell_text = cell.get_text(strip=True).lower()

                # Buscar "Nombre/Razón Social" o "Nombre Comercial"
                if any(term in cell_text for term in ['nombre/razón social', 'razón social', 'nombre comercial']):
                    if i + 1 < len(all_cells):
                        next_cell = all_cells[i + 1]
                        nombre_empresa = next_cell.get_text(strip=True)
                        logger.info(f"Empresa encontrada: {nombre_empresa}")

                # Buscar "Estado"
                elif 'estado' in cell_text:
                    if i + 1 < len(all_cells):
                        next_cell = all_cells[i + 1]
                        estado = next_cell.get_text(strip=True)
                        logger.info(f"Estado encontrado: {estado}")

            # Si encontramos el nombre de la empresa
            if nombre_empresa:
                return {
                    'success': True,
                    'id_number': id_number,
                    'id_type': 'rnc',
                    'company_name': nombre_empresa,
                    'status': estado or 'ACTIVO',
                    'validation_mode': 'dgii'
                }

            # Si no encontramos datos
            error_msg = soup.find(text=re.compile(r'no se encontraron resultados|rnc no existe', re.IGNORECASE))
            if error_msg:
                return {
                    'success': False,
                    'error': 'No se encontraron datos para este RNC en la DGII'
                }

            return cls._local_validation(id_number, 'rnc')

        except requests.Timeout:
            logger.error("Timeout al consultar DGII")
            return cls._local_validation(id_number, 'rnc')
        except Exception as e:
            logger.error(f"Error consultando DGII: {str(e)}", exc_info=True)
            return cls._local_validation(id_number, 'rnc')

    @classmethod
    def _local_validation(cls, id_number: str, id_type: str) -> Dict:
        """Validación local como fallback"""
        return {
            'success': True,
            'id_number': id_number,
            'id_type': id_type,
            'first_name': '' if id_type == 'cedula' else None,
            'last_name': '' if id_type == 'cedula' else None,
            'company_name': '' if id_type == 'rnc' else None,
            'validation_mode': 'local',
            'message': 'Formato válido - Complete datos manualmente'
        }