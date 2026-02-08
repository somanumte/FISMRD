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
        this.scannerContainer.classList.remove('hidden');
        this.scannerPlaceholder.classList.add('hidden');
        this.btnToggleScanner.textContent = 'Detener Scanner';
        this.btnToggleScanner.classList.replace('bg-indigo-500', 'bg-red-500');
        this.btnToggleScanner.classList.replace('hover:bg-indigo-400', 'hover:bg-red-400');

        this.html5QrCode = new Html5Qrcode("reader");
        const config = { fps: 10, qrbox: { width: 250, height: 150 } };

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
            alert("No se pudo iniciar la cámara. Asegúrate de dar permisos.");
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
        setVal('category', product.categoria);
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
            setVal('screen_id', product.pantalla.resolucion);
            const size = product.pantalla.diagonal_pulgadas;
            setVal('screen_size', size ? `${size}"` : '');
        }

        // Gráficos
        if (product.tarjeta_grafica) {
            const gpuModel = product.tarjeta_grafica.modelo_dedicado || product.tarjeta_grafica.modelo_integrado;
            setVal('graphics_card_id', gpuModel);
            setCheck('has_discrete_gpu', product.tarjeta_grafica.tiene_dedicada);
        }

        // Almacenamiento
        if (product.almacenamiento) {
            setVal('storage_id', product.almacenamiento.tipo_media);
            setVal('storage_capacity', product.almacenamiento.capacidad_total_gb);
            setCheck('storage_upgradeable', product.almacenamiento.ampliable);
        }

        // RAM
        if (product.memoria_ram) {
            setVal('ram_id', product.memoria_ram.tipo);
            setVal('ram_capacity', product.memoria_ram.capacidad_gb);
            setCheck('ram_upgradeable', product.memoria_ram.ampliable);
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
            setVal('cellular', product.conectividad.celular);
        }

        if (product.entrada) {
            setCheck('keyboard_backlight', product.entrada.retroiluminacion);
            if (product.entrada.disposicion_teclado) {
                setVal('keyboard_layout', product.entrada.disposicion_teclado);
            }
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
        if (window.updateDisplayName) {
            console.log("IcecatScanner: Triggering updateDisplayName");
            setTimeout(() => window.updateDisplayName(), 100);
        }
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
