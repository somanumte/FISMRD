// ============================================
// SISTEMA DE ESCANEO INTELIGENTE PARA LAPTOPS v2.0
// MODIFICADO: Llenado automático sin modal
// ============================================
// Integra:
// - Escaneo de códigos de barras (EAN/UPC)
// - Búsqueda automática en Icecat
// - Detección de códigos conocidos en la base de datos
// - Compleción automática de campos
// - Navegación por pestañas

class LaptopScanner {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.scanHistory = [];
        this.currentGtin = null;
        this.currentIcecatData = null;

        // Elementos del formulario
        this.gtinField = document.getElementById('gtin');
        this.skuField = document.getElementById('sku');
        this.displayNameField = document.getElementById('display_name');
        this.quickScanField = document.getElementById('quick-scan-input');

        // Inicializar
        this.init();
    }

    init() {
        // Configurar campo GTIN para escaneo
        if (this.gtinField) {
            this.gtinField.addEventListener('change', () => this.handleGtinChange());
            this.gtinField.addEventListener('blur', () => this.handleGtinBlur());

            // Detectar entrada rápida (escaneo)
            let lastValue = '';
            let lastTime = 0;
            this.gtinField.addEventListener('input', (e) => {
                const now = Date.now();
                const value = e.target.value;

                // Si la entrada es muy rápida (escaneo)
                if (now - lastTime < 200 && value.length > 7) {
                    this.handleScan(value);
                }

                lastValue = value;
                lastTime = now;
            });
        }

        // Configurar campo de escaneo rápido (solo para nuevo producto)
        if (this.quickScanField) {
            this.quickScanField.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const gtin = this.quickScanField.value.trim();
                    if (gtin.length >= 8) {
                        this.handleScan(gtin);
                    }
                }
            });
        }

        // Botón de escaneo manual
        const scanBtn = document.getElementById('btn-start-scan');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => this.openScanner());
        }

        // Botón de búsqueda en Icecat
        const icecatBtn = document.getElementById('btn-search-icecat');
        if (icecatBtn) {
            icecatBtn.addEventListener('click', () => this.searchInIcecat());
        }

        // Botón para buscar por GTIN específico
        const searchByGtinBtn = document.getElementById('btn-search-by-gtin');
        if (searchByGtinBtn) {
            searchByGtinBtn.addEventListener('click', () => {
                const gtin = this.gtinField?.value.trim() || this.quickScanField?.value.trim();
                if (gtin && gtin.length >= 8) {
                    this.searchInIcecat(gtin);
                }
            });
        }
    }

    handleGtinChange() {
        const gtin = this.gtinField.value.trim();
        if (gtin.length >= 8) {
            this.checkExistingProduct(gtin);
        }
    }

    handleGtinBlur() {
        const gtin = this.gtinField.value.trim();
        if (gtin.length >= 8 && gtin !== this.currentGtin) {
            this.currentGtin = gtin;
            this.autoSearch(gtin);
        }
    }

    handleScan(gtin) {
        console.log('Escaneo detectado:', gtin);
        this.currentGtin = gtin;

        // Actualizar ambos campos GTIN si existen
        if (this.gtinField) this.gtinField.value = gtin;
        if (this.quickScanField) this.quickScanField.value = gtin;

        this.autoSearch(gtin);
    }

    async autoSearch(gtin) {
        // Paso 1: Verificar si ya existe en la base de datos
        const existing = await this.checkDatabase(gtin);

        if (existing) {
            this.showProductFound(existing);
            return;
        }

        // Paso 2: Buscar en Icecat
        this.searchInIcecat(gtin);
    }

    async checkDatabase(gtin) {
        try {
            const response = await fetch(`/api/laptops/by-gtin/${gtin}`);
            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (error) {
            console.error('Error checking database:', error);
            return null;
        }
    }

    async checkExistingProduct(gtin) {
        const existing = await this.checkDatabase(gtin);
        if (existing) {
            this.showDuplicateWarning(existing);
        }
    }

    async searchInIcecat(gtin = null) {
        const searchGtin = gtin || (this.gtinField ? this.gtinField.value.trim() : this.quickScanField.value.trim());

        if (!searchGtin || searchGtin.length < 8) {
            this.showError('Por favor ingresa un código GTIN válido (mínimo 8 dígitos)');
            return;
        }

        this.showLoading('Buscando en Icecat...');

        try {
            const response = await fetch('/icecat/api/search/gtin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    gtin: searchGtin,
                    language: 'ES'
                })
            });

            const data = await response.json();

            if (data.success) {
                // Llenar automáticamente sin mostrar modal
                this.autoFillFromIcecat(data);
            } else {
                this.showError(data.error || 'Producto no encontrado en Icecat');
                this.offerManualEntry(searchGtin);
            }
        } catch (error) {
            console.error('Error searching in Icecat:', error);
            this.showError('Error de conexión con Icecat');
            this.offerManualEntry(searchGtin);
        }
    }

    autoFillFromIcecat(data) {
        this.hideLoading();
        this.currentIcecatData = data;

        // Importar datos directamente sin modal
        this.importIcecatData(data);

        // Mostrar notificación de éxito
        this.showSuccess('Datos de Icecat cargados automáticamente. Puedes editar cualquier campo.');
    }

    importIcecatData(data) {
        // Configurar datos ocultos de Icecat
        const icecatIdField = document.getElementById('icecat_data_id');
        const dataSourceField = document.getElementById('data_source');

        if (icecatIdField) icecatIdField.value = data.icecat_data_id || data.product?.icecat_id || '';
        if (dataSourceField) dataSourceField.value = 'icecat';

        // Llamar a función global para manejar datos
        if (typeof window.handleIcecatData === 'function') {
            window.handleIcecatData(data);
        } else {
            // Fallback: prellenar el formulario directamente
            this.prefillForm(data, true);
        }

        // Mostrar notificación
        this.showSuccess('Datos de Icecat importados exitosamente');

        // Cambiar a pestaña de especificaciones
        setTimeout(() => {
            const specsTab = document.querySelector('[data-tab="specs"]');
            if (specsTab) {
                specsTab.click();
            }
        }, 500);
    }

    prefillForm(data, autoNavigate = true) {
        const mapped = data.mapped_data || {};
        const product = data.product || {};

        // === CAMPOS BÁSICOS ===
        // Nombre comercial
        if (mapped.display_name || product.title) {
            this.setFieldValue('display_name', mapped.display_name || product.title);
        }

        // Descripciones
        if (mapped.short_description || product.short_description || product.summary_short) {
            this.setFieldValue('short_description', mapped.short_description || product.short_description || product.summary_short);
        }

        if (mapped.long_description_html || product.long_description_html) {
            this.setFieldValue('long_description_html', mapped.long_description_html || product.long_description_html);
        }

        // Identificadores
        if (product.gtin) {
            this.setFieldValue('gtin', product.gtin);
        }

        if (product.product_code) {
            this.setFieldValue('mpn', product.product_code);
        }

        // === CAMPOS DE CATÁLOGO ===
        // Configurar selects (marcas, modelos, etc.)
        if (mapped.brand_name || product.brand) {
            this.prefillCatalogSelect('brand_id', mapped.brand_id, mapped.brand_name || product.brand);
        }

        if (mapped.model_name) {
            this.prefillCatalogSelect('model_id', mapped.model_id, mapped.model_name);
        }

        if (mapped.processor_name) {
            this.prefillCatalogSelect('processor_id', mapped.processor_id, mapped.processor_name);
        }

        if (mapped.ram_name) {
            this.prefillCatalogSelect('ram_id', mapped.ram_id, mapped.ram_name);
        }

        if (mapped.storage_name) {
            this.prefillCatalogSelect('storage_id', mapped.storage_id, mapped.storage_name);
        }

        if (mapped.screen_name) {
            this.prefillCatalogSelect('screen_id', mapped.screen_id, mapped.screen_name);
        }

        if (mapped.graphics_card_name) {
            this.prefillCatalogSelect('graphics_card_id', mapped.graphics_card_id, mapped.graphics_card_name);
        }

        if (mapped.os_name) {
            this.prefillCatalogSelect('os_id', mapped.os_id, mapped.os_name);
        }

        // === CAMPOS NUMÉRICOS ===
        if (mapped.weight_kg) {
            this.setFieldValue('weight_kg', mapped.weight_kg);
        }

        if (mapped.battery_wh) {
            this.setFieldValue('battery_wh', mapped.battery_wh);
        }

        // Categoría
        if (mapped.category || product.category) {
            this.setSelectValue('category', mapped.category || product.category);
        }

        // === CAMPOS DE SEO ===
        // Título SEO
        if (!document.getElementById('seo_title')?.value && (mapped.display_name || product.title)) {
            this.setFieldValue('seo_title', mapped.display_name || product.title);
        }

        // Meta descripción SEO
        if (!document.getElementById('seo_description')?.value && (mapped.short_description || product.short_description || product.summary_short)) {
            this.setFieldValue('seo_description', mapped.short_description || product.short_description || product.summary_short);
        }

        // Palabras clave SEO
        if (!document.getElementById('seo_keywords')?.value) {
            let keywords = [];
            if (mapped.brand_name || product.brand) {
                keywords.push(mapped.brand_name || product.brand);
            }
            if (mapped.category || product.category) {
                keywords.push(mapped.category || product.category);
            }
            if (mapped.processor_name) {
                keywords.push(mapped.processor_name);
            }
            if (keywords.length > 0) {
                this.setFieldValue('seo_keywords', keywords.join(', '));
            }
        }

        // === GENERAR SKU AUTOMÁTICO ===
        if (this.skuField && !this.skuField.value) {
            this.generateAutoSku();
        }

        // === MOSTRAR IMÁGENES DE ICECAT ===
        this.showIcecatImages(data);

        // === ACTUALIZAR ORIGEN DE DATOS ===
        this.updateDataSourceDisplay('icecat');

        // === NAVEGACIÓN AUTOMÁTICA ===
        if (autoNavigate) {
            setTimeout(() => {
                const specsTab = document.querySelector('[data-tab="specs"]');
                if (specsTab) specsTab.click();
            }, 300);
        }

        // === RESALTAR CAMPOS LLENADOS ===
        this.highlightFilledFields();
    }

    setFieldValue(fieldId, value, onlyIfEmpty = true) {
        const field = document.getElementById(fieldId);
        if (field && value !== undefined && value !== null) {
            // Solo llenar si el campo está vacío o onlyIfEmpty es false
            if (onlyIfEmpty && field.value.trim() !== '') {
                return;
            }

            field.value = value;

            // Disparar evento change para triggers
            const event = new Event('change', { bubbles: true });
            field.dispatchEvent(event);

            // Disparar evento input para contadores de caracteres
            const inputEvent = new Event('input', { bubbles: true });
            field.dispatchEvent(inputEvent);

            // Marcar como modificado por Icecat
            field.classList.add('filled-from-icecat');
        }
    }

    setSelectValue(selectId, value) {
        const select = document.getElementById(selectId);
        if (select && value) {
            select.value = value;

            // Disparar evento change
            const event = new Event('change', { bubbles: true });
            select.dispatchEvent(event);

            // Marcar como modificado por Icecat
            select.classList.add('filled-from-icecat');
        }
    }

    async prefillCatalogSelect(selectId, catalogId, catalogName) {
        const select = document.getElementById(selectId);
        if (!select || !catalogName) return;

        // Si ya hay un ID, seleccionarlo
        if (catalogId) {
            select.value = catalogId;
            this.updateSelect2(select);
            select.classList.add('filled-from-icecat');
            return;
        }

        // Si no hay ID pero hay nombre, buscar o crear
        try {
            const response = await fetch('/api/catalog/find-or-create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: selectId.replace('_id', ''),
                    name: catalogName
                })
            });

            const data = await response.json();
            if (data.id) {
                select.value = data.id;
                this.updateSelect2(select);
                select.classList.add('filled-from-icecat');
            }
        } catch (error) {
            console.error(`Error prellenando select ${selectId}:`, error);
        }
    }

    updateSelect2(selectElement) {
        // Actualizar Select2 si está en uso
        if (typeof $ !== 'undefined' && $.fn.select2) {
            setTimeout(() => {
                $(selectElement).trigger('change');
            }, 100);
        }
    }

    generateAutoSku() {
        const brandSelect = document.getElementById('brand_id');
        const categorySelect = document.getElementById('category');
        const skuField = this.skuField;

        if (!skuField) return;

        let brandText = 'GEN';
        if (brandSelect && brandSelect.selectedOptions && brandSelect.selectedOptions[0]) {
            brandText = brandSelect.selectedOptions[0].text || 'GEN';
        }

        let categoryText = 'LAP';
        if (categorySelect && categorySelect.value) {
            categoryText = categorySelect.value || 'LAP';
        }

        const timestamp = Date.now().toString().slice(-6);
        const sku = `${brandText.substring(0, 3).toUpperCase()}-${categoryText.substring(0, 3).toUpperCase()}-${timestamp}`;

        skuField.value = sku;
        skuField.classList.add('filled-from-icecat');

        // También actualizar slug si está vacío
        const slugField = document.getElementById('slug');
        if (slugField && !slugField.value) {
            slugField.value = sku.toLowerCase();
            slugField.classList.add('filled-from-icecat');
        }
    }

    updateDataSourceDisplay(source) {
        const display = document.getElementById('data-source-display');
        const sourceSpan = document.getElementById('current-data-source');

        if (display && sourceSpan) {
            display.classList.remove('hidden');
            sourceSpan.textContent = source === 'icecat' ? 'Importado de Icecat' : 'Manual';
            sourceSpan.className = source === 'icecat' ?
                'px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm' :
                'px-2 py-1 bg-green-100 text-green-800 rounded text-sm';
        }
    }

    showIcecatImages(data) {
        const imagesContainer = document.getElementById('icecat-images-container');
        const imagesGrid = document.getElementById('icecat-images-grid');
        const previewContainer = document.getElementById('image-preview-container');

        if (!imagesContainer || !imagesGrid || !previewContainer) return;

        const product = data.product;
        if (!product) return;

        imagesGrid.innerHTML = '';
        previewContainer.innerHTML = ''; // Limpiar previews existentes

        // Agregar todas las imágenes automáticamente
        const imagesToAdd = [];

        // Imagen principal
        if (product.main_image) {
            imagesToAdd.push({
                ...product.main_image,
                isMain: true
            });
        }

        // Imágenes de galería
        if (product.gallery && Array.isArray(product.gallery)) {
            product.gallery.forEach(img => {
                imagesToAdd.push({
                    ...img,
                    isMain: false
                });
            });
        }

        // Agregar todas las imágenes al preview
        imagesToAdd.forEach((img, index) => {
            this.addIcecatImageToPreview(img, index === 0); // Primera imagen como principal
        });

        // Mostrar contenedor si hay imágenes
        if (previewContainer.children.length > 0) {
            imagesContainer.classList.remove('hidden');
        }
    }

    addIcecatImageToPreview(imgData, isCover = false) {
        const previewContainer = document.getElementById('image-preview-container');
        if (!previewContainer) return;

        const imgElement = document.createElement('div');
        imgElement.className = 'relative group';
        imgElement.innerHTML = `
            <img src="${imgData.url}" class="w-full h-32 object-cover rounded-lg">
            <div class="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                <button type="button" class="delete-image bg-red-600 text-white p-2 rounded-full">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <input type="hidden" name="icecat_images[]" value="${imgData.url}">
            ${isCover ? '<input type="hidden" name="cover_image" value="' + imgData.url + '">' : ''}
        `;

        previewContainer.appendChild(imgElement);

        // Agregar evento para eliminar imagen
        imgElement.querySelector('.delete-image').addEventListener('click', function() {
            imgElement.remove();
        });
    }

    highlightFilledFields() {
        // Resaltar brevemente los campos llenados
        document.querySelectorAll('.filled-from-icecat').forEach(field => {
            field.classList.add('highlight-field');
            setTimeout(() => {
                field.classList.remove('highlight-field');
            }, 2000);
        });
    }

    showLoading(message) {
        let loader = document.getElementById('scan-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'scan-loader';
            loader.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            loader.innerHTML = `
                <div class="bg-white p-6 rounded-lg shadow-lg">
                    <div class="flex items-center">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
                        <span class="text-lg font-medium">${message}</span>
                    </div>
                </div>
            `;
            document.body.appendChild(loader);
        } else {
            loader.classList.remove('hidden');
        }
    }

    hideLoading() {
        const loader = document.getElementById('scan-loader');
        if (loader) {
            loader.remove();
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        document.querySelectorAll('.scan-notification').forEach(n => n.remove());

        const colors = {
            error: 'bg-red-100 border-red-400 text-red-700',
            success: 'bg-green-100 border-green-400 text-green-700',
            info: 'bg-blue-100 border-blue-400 text-blue-700',
            warning: 'bg-yellow-100 border-yellow-400 text-yellow-700'
        };

        const icons = {
            error: 'exclamation-circle',
            success: 'check-circle',
            info: 'info-circle',
            warning: 'exclamation-triangle'
        };

        const notification = document.createElement('div');
        notification.className = `scan-notification fixed top-4 right-4 px-4 py-3 rounded-lg border ${colors[type]} z-50 shadow-lg max-w-md`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${icons[type]} mr-3"></i>
                <div class="flex-1">${message}</div>
                <button class="ml-4 text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        notification.querySelector('button').addEventListener('click', () => {
            notification.remove();
        });

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    showProductFound(product) {
        this.showNotification(`Producto ya existe en inventario: ${product.sku} - ${product.display_name}`, 'info');

        if (product.id) {
            const editBtn = document.createElement('a');
            editBtn.href = `/inventory/laptops/${product.id}/edit`;
            editBtn.className = 'ml-2 text-blue-600 hover:underline';
            editBtn.textContent = 'Editar producto existente';

            setTimeout(() => {
                const notification = document.querySelector('.scan-notification .flex-1');
                if (notification) {
                    notification.appendChild(document.createElement('br'));
                    notification.appendChild(editBtn);
                }
            }, 100);
        }
    }

    showDuplicateWarning(product) {
        document.querySelectorAll('.duplicate-warning').forEach(w => w.remove());

        const warning = document.createElement('div');
        warning.className = 'duplicate-warning mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded';
        warning.innerHTML = `
            <div class="flex items-start">
                <i class="fas fa-exclamation-triangle text-yellow-600 mt-1 mr-2"></i>
                <div>
                    <p class="text-yellow-800 font-medium">¡Producto ya registrado!</p>
                    <p class="text-yellow-700 text-sm">SKU: ${product.sku} - ${product.display_name}</p>
                    <div class="flex space-x-2 mt-2">
                        <a href="/inventory/laptops/${product.id}/edit" 
                           class="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
                            <i class="fas fa-edit mr-1"></i> Editar existente
                        </a>
                        <button class="text-sm px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">
                            <i class="fas fa-times mr-1"></i> Continuar igual
                        </button>
                    </div>
                </div>
            </div>
        `;

        const gtinField = this.gtinField || this.quickScanField;
        if (gtinField && gtinField.parentNode) {
            gtinField.parentNode.appendChild(warning);
        }

        warning.querySelector('button').addEventListener('click', () => {
            warning.remove();
        });

        setTimeout(() => {
            if (warning.parentNode) {
                warning.remove();
            }
        }, 15000);
    }

    offerManualEntry(gtin) {
        document.querySelectorAll('.manual-entry-offer').forEach(o => o.remove());

        const container = document.createElement('div');
        container.className = 'manual-entry-offer mt-4 p-4 bg-gray-50 rounded border';
        container.innerHTML = `
            <p class="text-gray-700 mb-2">
                <i class="fas fa-search mr-1"></i>
                No encontrado en Icecat. ¿Deseas agregarlo manualmente?
            </p>
            <div class="flex space-x-2">
                <button class="btn-cancel-manual px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">
                    <i class="fas fa-times mr-1"></i> Cancelar
                </button>
                <button class="btn-continue-manual px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
                    <i class="fas fa-keyboard mr-1"></i> Continuar Manualmente
                </button>
            </div>
        `;

        const gtinField = this.gtinField || this.quickScanField;
        if (gtinField && gtinField.parentNode) {
            gtinField.parentNode.appendChild(container);
        }

        container.querySelector('.btn-cancel-manual').addEventListener('click', () => {
            container.remove();
        });

        container.querySelector('.btn-continue-manual').addEventListener('click', () => {
            container.remove();
            if (this.displayNameField) {
                this.displayNameField.focus();
            }
            this.showNotification('Puedes completar el formulario manualmente', 'info');
        });
    }

    openScanner() {
        if (typeof window.openBarcodeScanner === 'function') {
            window.openBarcodeScanner((code) => {
                this.handleScan(code);
            });
        } else if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            this.showNotification('Iniciando cámara para escaneo...', 'info');
            this.openFallbackScanner();
        } else {
            this.openFallbackScanner();
        }
    }

    openFallbackScanner() {
        const gtin = prompt('Escáner no disponible. Ingresa el código de barras manualmente:');
        if (gtin && gtin.length >= 8) {
            this.handleScan(gtin);
        } else if (gtin) {
            this.showError('El código GTIN debe tener al menos 8 dígitos');
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    const laptopForm = document.getElementById('laptop-form');
    const quickScanInput = document.getElementById('quick-scan-input');

    if (laptopForm || quickScanInput) {
        window.laptopScanner = new LaptopScanner('laptop-form');

        window.scanBarcode = function(gtin) {
            if (window.laptopScanner) {
                window.laptopScanner.handleScan(gtin);
            }
        };

        window.searchIcecat = function(gtin) {
            if (window.laptopScanner) {
                window.laptopScanner.searchInIcecat(gtin);
            }
        };

        console.log('Sistema de escaneo de laptops inicializado - Modo Automático');
    }
});

// Función global para manejar datos de Icecat
if (typeof window.handleIcecatData !== 'function') {
    window.handleIcecatData = function(data) {
        console.log('Datos de Icecat recibidos (automático):', data);

        if (window.laptopScanner) {
            window.laptopScanner.showSuccess('Datos de Icecat cargados automáticamente');
        }
    };
}