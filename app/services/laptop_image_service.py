# -*- coding: utf-8 -*-
import os
import requests
import logging
from PIL import Image
from datetime import datetime
from werkzeug.utils import secure_filename
from app import db
from app.models.laptop import LaptopImage
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

class LaptopImageService:
    """
    Servicio para procesamiento y almacenamiento de imágenes de laptops.
    CORREGIDO: Ahora con descarga paralela de imágenes desde Icecat.
    """
    
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'avif'}
    UPLOAD_FOLDER = 'app/static/uploads/laptops'
    MAX_WORKERS = 10  # Número máximo de descargas paralelas
    
    # Lock para operaciones thread-safe en la BD
    _db_lock = threading.Lock()
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in LaptopImageService.ALLOWED_EXTENSIONS

    @staticmethod
    def process_and_save_image(laptop_id, sku, source, position, is_cover=False, alt_text=None, db_session=None, app=None):
        """
        Procesa una imagen (desde archivo o URL), la guarda tal cual y extrae metadatos.
        
        Args:
            laptop_id: ID de la laptop
            sku: SKU para el nombre del archivo
            source: Objeto de archivo (FileStorage) o URL (str)
            position: Posición en la galería
            is_cover: Si es la imagen de portada
            alt_text: Texto alternativo para SEO
            db_session: Sesión de BD a usar (para operaciones paralelas)
            
        Returns:
            LaptopImage: El objeto creado, o None si falló
            o dict: Metadatos si se solicita no guardar inmediatamente
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Directorios (Ruta absoluta para Windows)
            base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            upload_root = os.path.join(base_dir, LaptopImageService.UPLOAD_FOLDER.replace('/', os.sep))
            upload_folder = os.path.join(upload_root, str(laptop_id))
            
            logger.info(f"Ruta base detectada: {base_dir}")
            logger.info(f"Ruta upload_root: {upload_root}")
            logger.info(f"Ruta destino final: {upload_folder}")
            
            os.makedirs(upload_folder, exist_ok=True)
            
            # 1. Obtener la extensión y el contenido
            extension = ".jpg" # Default
            mime_type = "image/jpeg"
            temp_path = os.path.join(upload_folder, f"temp_{timestamp}_{position}")
            
            if isinstance(source, str) and source.startswith('http'):
                # Descargar desde URL
                logger.info(f"Descargando imagen desde URL: {source} para Laptop ID: {laptop_id}")
                logger.info(f"Ruta temporal: {temp_path}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                try:
                    response = requests.get(source, stream=True, timeout=15, headers=headers)
                except requests.exceptions.SSLError:
                    logger.warning(f"Error SSL al descargar {source}. Reintentando sin verificacion.")
                    try:
                        import urllib3
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                        response = requests.get(source, stream=True, timeout=15, verify=False, headers=headers)
                    except Exception as e:
                        logger.error(f"Error fatal en reintento SSL: {e}")
                        return None
                except Exception as e:
                    logger.error(f"Error en descarga desde URL: {e}")
                    return None

                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    
                    # Mapa de extensiones por MIME
                    mime_map = {
                        'image/jpeg': '.jpg',
                        'image/jpg': '.jpg',
                        'image/png': '.png',
                        'image/webp': '.webp',
                        'image/gif': '.gif',
                        'image/avif': '.avif'
                    }
                    
                    found_mime = False
                    for m_type, ext in mime_map.items():
                        if m_type in content_type:
                            extension = ext
                            mime_type = m_type
                            found_mime = True
                            break
                    
                    if not found_mime:
                        # Fallback a extensión de la URL
                        url_ext = os.path.splitext(source.split('?')[0])[1].lower()
                        if url_ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif']:
                            extension = url_ext if url_ext != '.jpeg' else '.jpg'
                    
                    # Guardar raw content
                    with open(temp_path, 'wb') as f:
                        for chunk in response.iter_content(8192):
                            f.write(chunk)
                else:
                    logger.error(f"Error HTTP {response.status_code} al descargar: {source}")
                    return None
            else:
                # Es un archivo subido (FileStorage)
                orig_filename = secure_filename(source.filename)
                if '.' in orig_filename:
                    extension = '.' + orig_filename.rsplit('.', 1)[1].lower()
                    if extension == '.jpeg': extension = '.jpg'
                
                source.save(temp_path)
                mime_type = getattr(source, 'content_type', 'image/jpeg')
            
            # 2. Definir nombre final y ruta
            final_filename = f"{sku}_{position}_{timestamp}{extension}"
            final_path = os.path.join(upload_folder, final_filename)
            
            # Renombrar temporal a final (ahorro de espacio y CPU)
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_path, final_path)
            
            # 3. Extraer metadatos con PIL (sin guardar/convertir)
            if not os.path.exists(final_path):
                logger.error(f"¡CRÍTICO! El archivo final no existe en: {final_path}")
            else:
                logger.info(f"Archivo guardado exitosamente en: {final_path} (Size: {os.path.getsize(final_path)})")

            width, height, file_size = None, None, None
            try:
                file_size = os.path.getsize(final_path)
                with Image.open(final_path) as img:
                    width, height = img.size
            except Exception as e:
                logger.warning(f"No se pudieron extraer dimensiones de {final_filename}: {e}")
            
            # 4. Crear registro en BD (thread-safe)
            relative_path = f"uploads/laptops/{laptop_id}/{final_filename}"
            
            # Si solo queremos los metadatos (para guardar luego fuera de hilos paralelos)
            metadata = {
                'laptop_id': laptop_id,
                'image_path': relative_path,
                'alt_text': alt_text or f"Imagen {position}",
                'is_cover': is_cover,
                'position': position,
                'ordering': position,
                'file_size': file_size,
                'width': width,
                'height': height,
                'mime_type': mime_type
            }

            if db_session is False: # Centinela para retornar solo metadata
                return metadata

            # Comportamiento legacy/directo
            new_image = LaptopImage(**metadata)
            
            # Usar lock para operaciones de BD thread-safe
            def _db_ops():
                with LaptopImageService._db_lock:
                    if db_session:
                        db_session.add(new_image)
                    else:
                        db.session.add(new_image)

            # Si se proporcionó el objeto app, usar su contexto
            if app:
                with app.app_context():
                    _db_ops()
            else:
                _db_ops()
            
            return new_image
            
        except Exception as e:
            logger.error(f"Error crítico en process_and_save_image: {str(e)}")
            # Limpiar por si acaso
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return None

    @staticmethod
    def cleanup_laptop_images(laptop_id, keep_ids=None):
        """Elimina las imágenes de un laptop que no estén en la lista de IDs a mantener."""
        from flask import current_app
        images = LaptopImage.query.filter_by(laptop_id=laptop_id).all()
        for img in images:
            if keep_ids is None or img.id not in keep_ids:
                # Eliminar archivo físico
                full_path = os.path.join(current_app.root_path, 'static', img.image_path)
                if os.path.exists(full_path):
                    try: 
                        os.remove(full_path)
                    except Exception as e:
                        logger.error(f"No se pudo eliminar archivo físico {full_path}: {e}")
                # Eliminar de BD
                db.session.delete(img)
        db.session.flush()
    
    @staticmethod
    def _download_single_image(url):
        """
        Helper para descargar una sola imagen en un thread separado.
        Retorna (url, file_content_or_none, error_msg_or_none)
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            logger.info(f"Iniciando descarga individual: {url}")
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            if response.status_code == 200:
                logger.info(f"Descarga exitosa (HTTP 200): {url}")
                return url, response.content, None
            else:
                logger.error(f"Falla HTTP {response.status_code}: {url}")
                return url, None, f"Error HTTP {response.status_code}"
        except Exception as e:
            logger.error(f"EXCEPCIÓN EN DESCARGA {url}: {str(e)}")
            return url, None, str(e)
    
    @staticmethod
    def save_icecat_images_parallel(laptop_id, sku, image_urls, max_workers=None):
        """
        Descarga y guarda las imágenes de Icecat para un laptop EN PARALELO.
        NUEVO: Esta función optimiza el tiempo de creación descargando múltiples imágenes simultáneamente.
        
        Args:
            laptop_id: ID de la laptop
            sku: SKU de la laptop
            image_urls: Lista de URLs de imágenes desde Icecat
            max_workers: Número máximo de threads paralelos (default: MAX_WORKERS de la clase)
            
        Returns:
            tuple: (cantidad_exitosa, lista_de_errores, lista_de_objetos_imagen)
        """
        if not image_urls:
            logger.warning(f"No se proporcionaron URLs de imágenes para laptop {laptop_id}")
            return 0, [], []
        
        if max_workers is None:
            max_workers = LaptopImageService.MAX_WORKERS
        
        success_count = 0
        errors = []
        successful_images = []
        
        from flask import current_app
        app = current_app._get_current_object()
        
        # Función interna para procesar una sola imagen en paralelo
        def _target_process(idx, url):
            try:
                # Usamos el método existente que ya maneja descarga y guardado
                img = LaptopImageService.process_and_save_image(
                    laptop_id=laptop_id,
                    sku=sku,
                    source=url,
                    position=idx,
                    is_cover=(idx == 1),
                    alt_text=f"Imagen {idx}",
                    app=app
                )
                if img:
                    img.source = 'icecat'
                    return idx, img, None
                return idx, None, f"Falla en process_and_save_image para {url}"
            except Exception as e:
                return idx, None, str(e)

        # Usar ThreadPoolExecutor para procesamiento paralelo (Descarga + Guardado)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_target_process, idx, url) for idx, url in enumerate(image_urls, start=1)]
            
            for future in as_completed(futures):
                idx, img_obj, error = future.result()
                if img_obj:
                    successful_images.append(img_obj)
                    success_count += 1
                elif error:
                    errors.append(f"Error en imagen {idx}: {error}")
                        
        
        return success_count, errors, successful_images

    @staticmethod
    def background_save_icecat_images(laptop_id, sku, image_urls, app):
        """
        Versión para segundo plano de la descarga de Icecat.
        Maneja su propia sesión y commit.
        """
        with app.app_context():
            logger.info(f"🧵 Hilo de background iniciado para laptop {laptop_id}")
            # Usamos la versión paralela que ya optimizamos
            # Pero necesitamos que use el app_context para cada operación individual
            success, errors, images = LaptopImageService.save_icecat_images_parallel(
                laptop_id=laptop_id, 
                sku=sku, 
                image_urls=image_urls
            )
            
            if success > 0:
                try:
                    db.session.commit()
                    logger.info(f"✅ Hilo de background completado: {success} imágenes guardadas.")
                except Exception as e:
                    logger.error(f"❌ Error al hacer commit en background: {str(e)}")
            else:
                logger.warning(f"⚠️ Hilo de background terminado sin imágenes guardadas. Errores: {errors}")
    
    @staticmethod
    def save_icecat_images(laptop_id, sku, image_urls):
        """
        MÉTODO LEGACY: Descarga y guarda las imágenes de Icecat de forma SECUENCIAL.
        Se mantiene por compatibilidad, pero se recomienda usar save_icecat_images_parallel().
        
        Args:
            laptop_id: ID de la laptop
            sku: SKU de la laptop
            image_urls: Lista de URLs de imágenes desde Icecat
            
        Returns:
            tuple: (cantidad_exitosa, lista_de_errores)
        """
        logger.warning("⚠️ Usando método secuencial de descarga. Se recomienda save_icecat_images_parallel()")
        
        if not image_urls:
            logger.warning(f"No se proporcionaron URLs de imágenes para laptop {laptop_id}")
            return 0, []
        
        success_count = 0
        errors = []
        
        for idx, image_url in enumerate(image_urls, start=1):
            if not image_url or not image_url.startswith('http'):
                logger.warning(f"URL inválida en posición {idx}: {image_url}")
                continue
            
            try:
                # Usar el servicio existente para descargar y guardar
                img_obj = LaptopImageService.process_and_save_image(
                    laptop_id=laptop_id,
                    sku=sku,
                    source=image_url,
                    position=idx,
                    is_cover=(idx == 1),  # La primera es la portada
                    alt_text=f"Imagen {idx}"
                )
                
                if img_obj:
                    # Marcar como imagen externa
                    img_obj.source = 'icecat'
                    success_count += 1
                    logger.info(f"Imagen {idx} descargada exitosamente desde Icecat: {image_url}")
                else:
                    error_msg = f"No se pudo procesar imagen {idx} desde URL: {image_url}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error al descargar imagen {idx}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if success_count > 0:
            try:
                db.session.flush()
                logger.info(f"Se guardaron {success_count} imágenes de Icecat para laptop {laptop_id}")
            except Exception as e:
                logger.error(f"Error al hacer flush de imágenes: {str(e)}")
                return 0, [f"Error al guardar en BD: {str(e)}"]
        
        return success_count, errors
