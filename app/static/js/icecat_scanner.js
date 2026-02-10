/**
 * Icecat Scanner & Data Fetcher
 * Handles barcode scanning via html5-qrcode and fetches product data from Icecat API.
 */

class IcecatScanner {
    constructor() {
        this.html5QrCode = null;
        this.isScannerRunning = false;
        this.scannerContainer = document.getElementById('scanner-container');
        this.scannerPlaceholder = document.getElementById('scanner-placeholder');
        this.btnToggleScanner = document.getElementById('btn-toggle-scanner');
        this.btnFetchIcecat = document.getElementById('btn-fetch-icecat');
        this.gtinInput = document.getElementById('gtin-input');

        this.init();
    }

    init() {
        if (this.btnToggleScanner) {
            this.btnToggleScanner.addEventListener('click', () => this.toggleScanner());
        }
        if (this.btnFetchIcecat) {
            this.btnFetchIcecat.addEventListener('click', () => this.fetchData());
        }

        // Listen for enter key in GTIN input
        if (this.gtinInput) {
            this.gtinInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.fetchData();
                }
            });
        }
    }

    async toggleScanner() {
        if (this.isScannerRunning) {
            await this.stopScanner();
        } else {
            this.startScanner();
        }
    }

    async startScanner() {
        if (!window.isSecureContext) {
            alert("Error: El scanner de cámara requiere una conexión segura (HTTPS) para funcionar en este navegador. Si estás en una red local, usa 'localhost' o configura un certificado SSL.");
            return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Error: Tu navegador no soporta el acceso a la cámara o está bloqueado por políticas de seguridad.");
            return;
        }

        this.scannerContainer.classList.remove('hidden');
        this.scannerPlaceholder.classList.add('hidden');
        this.btnToggleScanner.textContent = 'Detener Scanner';
        this.btnToggleScanner.classList.replace('bg-indigo-500', 'bg-red-500');
        this.btnToggleScanner.classList.replace('hover:bg-indigo-400', 'hover:bg-red-400');

        this.html5QrCode = new Html5Qrcode("reader");
        const config = { fps: 15, qrbox: { width: 250, height: 150 }, aspectRatio: 1.0 };

        try {
            await this.html5QrCode.start(
                { facingMode: "environment" },
                config,
                (decodedText) => {
                    this.gtinInput.value = decodedText;
                    this.stopScanner();
                    this.fetchData();
                }
            );
            this.isScannerRunning = true;
        } catch (err) {
            console.error("Error starting scanner:", err);
            let message = "No se pudo iniciar la cámara.";

            if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                message += " El acceso fue denegado. Por favor, concede permisos de cámara en los ajustes de tu navegador/iPhone.";
            } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                message += " No se encontró ninguna cámara disponible en este dispositivo.";
            } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
                message += " La cámara ya está siendo usada por otra aplicación o hay un error de hardware.";
            } else {
                message += " Asegúrate de dar permisos y de que ninguna otra app use la cámara. Detalle: " + err.message;
            }

            alert(message);
            this.stopScanner();
        }
    }

    async stopScanner() {
        if (this.html5QrCode) {
            try {
                await this.html5QrCode.stop();
            } catch (err) {
                console.error("Error stopping scanner:", err);
            }
            this.html5QrCode = null;
        }
        this.isScannerRunning = false;
        this.scannerContainer.classList.add('hidden');
        this.scannerPlaceholder.classList.remove('hidden');
        this.btnToggleScanner.textContent = 'Iniciar Cámara Scanner';
        this.btnToggleScanner.classList.replace('bg-red-500', 'bg-indigo-500');
        this.btnToggleScanner.classList.replace('hover:bg-red-400', 'hover:bg-indigo-400');
    }

    async fetchData() {
        const gtin = this.gtinInput.value.trim();
        if (!gtin) {
            alert("Por favor ingresa un código GTIN (UPC/EAN)");
            return;
        }

        this.setLoading(true);

        try {
            const response = await fetch(`/api/icecat/fetch/${gtin}`);
            const data = await response.json();

            if (data.success) {
                this.populateForm(data.product);
                if (window.showNotification) {
                    window.showNotification('Datos cargados desde Icecat exitosamente', 'success');
                } else {
                    alert('Datos cargados exitosamente');
                }
            } else {
                alert(`Error: ${data.message || 'No se encontró el producto en Icecat'}`);
            }
        } catch (err) {
            console.error("Error fetching data:", err);
            alert("Error de conexión al servidor");
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(isLoading) {
        const text = document.getElementById('fetch-text');
        const spinner = document.getElementById('fetch-spinner');

        if (isLoading) {
            text.classList.add('hidden');
            spinner.classList.remove('hidden');
            this.btnFetchIcecat.disabled = true;
            this.btnFetchIcecat.classList.add('opacity-70');
        } else {
            text.classList.remove('hidden');
            spinner.classList.add('hidden');
            this.btnFetchIcecat.disabled = false;
            this.btnFetchIcecat.classList.remove('opacity-70');
        }
    }

    populateForm(product) {
        console.log("IcecatScanner: Populating form with product", product);

        // Helper para asignar valores con seguridad
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) {
                el.value = val !== undefined && val !== null ? val : '';
                // Disparar evento change para que otros scripts reaccionen
                const event = new Event('change', { bubbles: true });
                el.dispatchEvent(event);
                // Si jQuery está presente, disparar también vía jQuery
                if (window.jQuery) {
                    window.jQuery(el).trigger('change');
                }
                return true;
            }
            return false;
        };

        // Helper para asignar checkboxes con seguridad
        const setCheck = (id, val) => {
            const el = document.getElementById(id);
            if (el) {
                el.checked = !!val;
                // Disparar evento change
                const event = new Event('change', { bubbles: true });
                el.dispatchEvent(event);
                if (window.jQuery) window.jQuery(el).trigger('change');
                return true;
            }
            return false;
        };

        // IDs y metadatos
        setVal('icecat_id', product.icecat_id);
        const fullSpecs = product.raw_specs || {};
        setVal('full_specs_json', JSON.stringify(fullSpecs));
        setVal('normalized_specs', JSON.stringify(product));

        // Información básica
        setVal('display_name', product.nombre_visualizacion || product.nombre_comercial);
        setVal('short_description', product.short_description);
        // Default Values as per requirements
        setVal('category', 'laptop');
        setVal('condition', 'new');
        setVal('gtin', product.gtin);

        // Especificaciones técnicas (Mapeo V2.0)
        setVal('brand_id', product.marca);
        setVal('model_id', product.modelo);

        // Procesador
        if (product.procesador) {
            setVal('processor_family', product.procesador.familia);
            setVal('processor_generation', product.procesador.generacion);
            setVal('processor_model', product.procesador.modelo);
            setVal('processor_full_name', product.procesador.nombre_completo);
            setCheck('npu', product.procesador.tiene_npu);
        }

        // Pantalla
        if (product.pantalla) {
            setVal('screen_id', product.pantalla.resolucion); // Backward compat
            setVal('screen_resolution', product.pantalla.resolucion);
            setVal('screen_hd_type', product.pantalla.tipo_hd);
            setVal('screen_diagonal_inches', product.pantalla.diagonal_pulgadas);
            setVal('screen_panel_type', product.pantalla.tipo);
            setVal('screen_refresh_rate', product.pantalla.tasa_refresco_hz);
            setCheck('screen_touchscreen_override', product.pantalla.tactil);

            // Resolution label mapping (FHD, 2K, 2.5K, 3K, 4K, 8K)
            const mapResolution = (res) => {
                if (!res) return null;
                const match = res.match(/(\d{3,4})/);
                if (!match) return null;
                const hRes = parseInt(match[1]);
                if (hRes >= 1800 && hRes <= 2000) return "FHD";
                if (hRes > 2000 && hRes <= 2600) return "2K";
                if (hRes > 2600 && hRes <= 2900) return "2.5K";
                if (hRes > 2900 && hRes <= 3400) return "3K";
                if (hRes > 3400 && hRes <= 4500) return "4K";
                if (hRes > 7000 && hRes <= 8500) return "8K";
                return null;
            };

            const resLabel = mapResolution(product.pantalla.resolucion);

            // Full Name: (Diagonal) + (Res Label) + (Tipo HD) + (Panel type) + (Refresh rate)
            const screenFullNameParts = [
                product.pantalla.diagonal_pulgadas ? `${product.pantalla.diagonal_pulgadas}"` : ''
            ];

            if (resLabel) screenFullNameParts.push(resLabel);

            if (product.pantalla.tipo_hd) {
                // Evitar duplicados (ej: FHD FHD)
                if (!resLabel || product.pantalla.tipo_hd.toLowerCase() !== resLabel.toLowerCase()) {
                    screenFullNameParts.push(product.pantalla.tipo_hd);
                }
            }

            if (product.pantalla.tipo) {
                screenFullNameParts.push(product.pantalla.tipo.replace(/-Level/g, ''));
            }

            if (product.pantalla.tasa_refresco_hz) {
                screenFullNameParts.push(`${product.pantalla.tasa_refresco_hz}Hz`);
            }

            const screenFullName = screenFullNameParts.filter(Boolean).join(' ');
            setVal('screen_full_name', screenFullName);
        }

        // Gráficos
        if (product.tarjeta_grafica) {
            const gpuModel = product.tarjeta_grafica.modelo_dedicado || product.tarjeta_grafica.modelo_integrado;
            setVal('graphics_card_id', gpuModel); // Backward compat

            setCheck('has_discrete_gpu', product.tarjeta_grafica.tiene_dedicada);

            // Discrete GPU
            setVal('discrete_gpu_brand', product.tarjeta_grafica.marca_dedicada);
            setVal('discrete_gpu_model', product.tarjeta_grafica.modelo_dedicado);
            setVal('discrete_gpu_memory_gb', product.tarjeta_grafica.memoria_dedicada_gb);
            setVal('discrete_gpu_memory_type', product.tarjeta_grafica.tipo_memoria_dedicada);

            // Discrete Full Name: Deduplicate brand and model
            if (product.tarjeta_grafica.tiene_dedicada) {
                const brand = product.tarjeta_grafica.marca_dedicada || "";
                const model = product.tarjeta_grafica.modelo_dedicado || "";

                const parts = [];
                if (brand && !model.toLowerCase().includes(brand.toLowerCase())) {
                    parts.push(brand);
                }
                parts.push(model);
                parts.push(product.tarjeta_grafica.memoria_dedicada_gb ? `${product.tarjeta_grafica.memoria_dedicada_gb}GB` : '');
                parts.push(product.tarjeta_grafica.tipo_memoria_dedicada);

                // Dedup consecutive words
                const cleanParts = [];
                const allParts = parts.filter(Boolean);
                allParts.forEach(p => {
                    if (cleanParts.length === 0 || p.toLowerCase() !== cleanParts[cleanParts.length - 1].toLowerCase()) {
                        cleanParts.push(p);
                    }
                });

                setVal('discrete_gpu_full_name', cleanParts.join(' '));
            }

            // Integrated GPU
            setVal('onboard_gpu_brand', product.tarjeta_grafica.marca_integrada);
            setVal('onboard_gpu_model', product.tarjeta_grafica.modelo_integrado);
            setVal('onboard_gpu_family', product.tarjeta_grafica.familia_integrada);
            setVal('onboard_gpu_memory_gb', product.tarjeta_grafica.memoria_integrada_gb);

            // Integrated Full Name: Deduplicate brand and model
            const iBrand = product.tarjeta_grafica.marca_integrada || "";
            const iModel = product.tarjeta_grafica.modelo_integrado || "";
            const iFamily = product.tarjeta_grafica.familia_integrada || "";

            const iParts = [];
            if (iBrand && !iModel.toLowerCase().includes(iBrand.toLowerCase())) {
                iParts.push(iBrand);
            }
            iParts.push(iModel);
            if (iFamily && !iModel.toLowerCase().includes(iFamily.toLowerCase())) {
                iParts.push(iFamily);
            }
            iParts.push(product.tarjeta_grafica.memoria_integrada_gb ? `${product.tarjeta_grafica.memoria_integrada_gb}GB` : '');

            const cleanIParts = [];
            iParts.filter(Boolean).forEach(p => {
                if (cleanIParts.length === 0 || p.toLowerCase() !== cleanIParts[cleanIParts.length - 1].toLowerCase()) {
                    cleanIParts.push(p);
                }
            });
            setVal('onboard_gpu_full_name', cleanIParts.join(' '));
        }

        // Almacenamiento
        if (product.almacenamiento) {
            setVal('storage_id', product.almacenamiento.tipo_media); // Backward compat
            setVal('storage_capacity', product.almacenamiento.capacidad_total_gb);
            setVal('storage_media', product.almacenamiento.tipo_media);
            setCheck('storage_nvme', product.almacenamiento.nvme);
            setVal('storage_form_factor', product.almacenamiento.factor_forma_ssd);
            setCheck('storage_upgradeable', product.almacenamiento.ampliable);

            // Storage Full Name: (Total storage capacity in GB or TB) + (Storage media) + (NVMe) + (SSD form factor)
            let capacityStr = '';
            if (product.almacenamiento.capacidad_total_gb) {
                if (product.almacenamiento.capacidad_total_gb >= 1024) {
                    capacityStr = `${(product.almacenamiento.capacidad_total_gb / 1024).toFixed(1)}TB`.replace('.0', '');
                } else {
                    capacityStr = `${product.almacenamiento.capacidad_total_gb}GB`;
                }
            }

            const storageFullName = [
                capacityStr,
                product.almacenamiento.tipo_media,
                product.almacenamiento.nvme ? 'NVMe' : '',
                product.almacenamiento.factor_forma_ssd
            ].filter(Boolean).join(' ');
            setVal('storage_full_name', storageFullName);
        }

        // RAM
        if (product.memoria_ram) {
            setVal('ram_id', product.memoria_ram.tipo); // Backward compat
            setVal('ram_capacity', product.memoria_ram.capacidad_gb);
            setVal('ram_type_detailed', product.memoria_ram.tipo);
            setVal('ram_speed_mhz', product.memoria_ram.velocidad_mhz);
            setVal('ram_transfer_rate', product.memoria_ram.tasa_transferencia);
            setCheck('ram_upgradeable', product.memoria_ram.ampliable);

            // RAM Full Name: (1nternal memory) + (Internal memory type "Remover -SDRAM") + (Memory clock speed) + (Memory data transfer rate)
            // Note: "Remover -SDRAM" is handled in backend logic for 'tipo', but consistent check here if needed.
            // Backend normalize_data already removes -SDRAM from 'tipo'.
            const ramFullName = [
                product.memoria_ram.capacidad_gb ? `${product.memoria_ram.capacidad_gb}GB` : '',
                product.memoria_ram.tipo,
                product.memoria_ram.velocidad_mhz ? `${product.memoria_ram.velocidad_mhz}MHz` : '',
                product.memoria_ram.tasa_transferencia ? `${product.memoria_ram.tasa_transferencia}MT/s` : ''
            ].filter(Boolean).join(' ');
            setVal('ram_full_name', ramFullName);
        }

        // Físico
        if (product.fisico) {
            setVal('weight_lbs', product.fisico.peso_lbs);
        }

        // Sistema Operativo
        if (product.sistema_operativo) {
            setVal('os_id', product.sistema_operativo);
        }

        // Otros detalles técnicos
        if (product.conectividad) {
            // Puertos (formato lista a string)
            if (product.conectividad.puertos && product.conectividad.puertos.length > 0) {
                const portsStr = product.conectividad.puertos
                    .map(p => `${p.cantidad}x ${p.tipo}${p.version ? ' ' + p.version : ''}`)
                    .join(', ');
                setVal('connectivity_ports', portsStr);
            }
            setVal('wifi_standard', product.conectividad.wifi);
            setVal('wifi_standards', product.conectividad.wifi_standards);
            setVal('cellular', product.conectividad.celular);
        }

        if (product.entrada) {
            setCheck('keyboard_backlight', product.entrada.retroiluminacion);
            setCheck('numeric_keypad', product.entrada.teclado_numerico);

            if (product.entrada.disposicion_teclado) {
                setVal('keyboard_layout', product.entrada.disposicion_teclado);
            }

            // Nuevos campos de teclado
            setVal('pointing_device', product.entrada.dispositivo_apuntador);
            setVal('keyboard_backlight_color', product.entrada.color_retroiluminacion);
            setVal('keyboard_backlight_zone', product.entrada.zona_retroiluminacion);
            setVal('keyboard_language', product.entrada.idioma_teclado);
        }

        if (product.palabras_clave) {
            setVal('keywords', product.palabras_clave);
        }

        // Manejar imágenes - IMPORTANTE: La API retorna "imagenes", no "images"
        console.log('🖼️ Verificando imágenes en product:', product);
        console.log('product.imagenes:', product.imagenes);
        console.log('product.images:', product.images);

        if (product.imagenes && product.imagenes.length > 0) {
            console.log(`📸 Cargando ${product.imagenes.length} imágenes desde Icecat...`);
            this.loadImages(product.imagenes);
        } else {
            console.warn('⚠️ No se encontraron imágenes en product.imagenes');
        }

        // Forzar generación de nombre comercial si la función global existe
        // ELIMINADO: Se debe usar el nombre original de Icecat
    }

    loadImages(imageUrls) {
        // Clear existing images that are not "saved" or "locked"
        // This integration depends on how laptop_gallery.js is implemented.
        // We will push URLs to hidden fields and let the background service handle them.

        const container = document.getElementById('images-container-premium');
        if (!container) return;

        // We'll use a custom event or direct call to laptop_gallery if available
        if (window.LaptopGalleryHybrid && window.LaptopGalleryHybrid.addImagesFromUrls) {
            window.LaptopGalleryHybrid.addImagesFromUrls(imageUrls);
        } else {
            console.warn("GalleryManager.addImagesFromUrls not found. Falls back to manual population.");
            // Manual fallback: populate hidden URL fields for all slots
            imageUrls.forEach((url, index) => {
                const slotIndex = index + 1;
                let urlInput = document.getElementById(`image_${slotIndex}_url`);
                if (!urlInput) {
                    // Create it if it doesn't exist
                    urlInput = document.createElement('input');
                    urlInput.type = 'hidden';
                    urlInput.id = `image_${slotIndex}_url`;
                    urlInput.name = `image_${slotIndex}_url`;
                    document.getElementById('laptop-form').appendChild(urlInput);
                }
                urlInput.value = url;

                // Visual feedback in the gallery if possible
                this.addGalleryPreview(url, slotIndex);
            });
        }
    }

    addGalleryPreview(url, index) {
        // This is a simplified version of what laptop_gallery.js does
        const container = document.getElementById('images-container-premium');
        if (!container) return;

        // Check if there's already an image in this slot
        const existingCard = container.querySelector(`[data-index="${index}"]`);
        if (existingCard) return;

        const card = document.createElement('div');
        card.className = 'image-card-premium new';
        card.dataset.index = index;
        card.innerHTML = `
            <div class="image-preview-premium">
                <img src="${url}" class="w-full h-full object-cover">
                <div class="type-badge new">
                    <i class="fas fa-cloud-download-alt"></i>
                </div>
            </div>
            <div class="image-info-premium">
                <div class="image-name-premium">Imagen ${index}</div>
                <input type="text" name="image_${index}_alt" class="alt-text-input-premium" placeholder="Texto alternativo">
            </div>
        `;
        container.appendChild(card);
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    window.icecatScanner = new IcecatScanner();
});
