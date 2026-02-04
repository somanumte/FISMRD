// ============================================
// SISTEMA DE ESCANEO INTELIGENTE PARA LAPTOPS
// ============================================
// Integra:
// - Escaneo de códigos de barras (EAN/UPC)
// - Búsqueda automática en Icecat
// - Detección de códigos conocidos en la base de datos
// - Compleción automática de campos

class LaptopScanner {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.scanHistory = [];
        this.currentGtin = null;

        // Elementos del formulario
        this.gtinField = document.getElementById('gtin');
        this.skuField = document.getElementById('sku');
        this.displayNameField = document.getElementById('display_name');

        // Modal de resultados
        this.createResultsModal();

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
                if (now - lastTime < 200 && value.length > 5) {
                    this.handleScan(value);
                }

                lastValue = value;
                lastTime = now;
            });
        }

        // Botón de escaneo manual
        const scanBtn = document.getElementById('btn-scan');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => this.openScanner());
        }

        // Botón de búsqueda en Icecat
        const icecatBtn = document.getElementById('btn-search-icecat');
        if (icecatBtn) {
            icecatBtn.addEventListener('click', () => this.searchInIcecat());
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
        this.gtinField.value = gtin;
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
        const searchGtin = gtin || this.gtinField.value.trim();

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
                this.showIcecatResults(data);
            } else {
                this.showError(data.error || 'Producto no encontrado en Icecat');
                this.offerManualEntry(searchGtin);
            }
        } catch (error) {
            this.showError('Error de conexión con Icecat');
            this.offerManualEntry(searchGtin);
        }
    }

    showIcecatResults(data) {
        this.hideLoading();

        // Mostrar modal con resultados
        const modal = document.getElementById('icecat-results-modal');
        const modalContent = document.getElementById('icecat-results-content');

        // Llenar contenido del modal
        modalContent.innerHTML = this.renderIcecatProduct(data);

        // Mostrar modal
        modal.classList.remove('hidden');

        // Configurar botones
        document.getElementById('btn-import-icecat').onclick = () => {
            this.importIcecatData(data);
            modal.classList.add('hidden');
        };

        document.getElementById('btn-edit-manually').onclick = () => {
            modal.classList.add('hidden');
            this.prefillForm(data);
        };
    }

    renderIcecatProduct(data) {
        const product = data.product;
        const mapped = data.mapped_data;

        return `
            <div class="space-y-4">
                <div class="flex items-start space-x-4">
                    ${product.main_image ? `
                        <img src="${product.main_image.medium_url || product.main_image.url}" 
                             alt="${product.title}" 
                             class="w-32 h-32 object-cover rounded-lg">
                    ` : ''}
                    
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold">${product.title}</h3>
                        <div class="flex items-center space-x-2 mt-2">
                            <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">${product.brand}</span>
                            <span class="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">${product.category || 'Laptop'}</span>
                        </div>
                        
                        <div class="grid grid-cols-2 gap-2 mt-3 text-sm">
                            <div><span class="font-medium">GTIN:</span> ${product.gtin || 'N/A'}</div>
                            <div><span class="font-medium">Part Number:</span> ${product.product_code || 'N/A'}</div>
                            <div><span class="font-medium">Icecat ID:</span> ${product.icecat_id || 'N/A'}</div>
                        </div>
                    </div>
                </div>
                
                <div class="border-t pt-4">
                    <h4 class="font-medium mb-2">Especificaciones principales:</h4>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        ${mapped.processor_name ? `<div><span class="font-medium">Procesador:</span> ${mapped.processor_name}</div>` : ''}
                        ${mapped.ram_name ? `<div><span class="font-medium">RAM:</span> ${mapped.ram_name}</div>` : ''}
                        ${mapped.storage_name ? `<div><span class="font-medium">Almacenamiento:</span> ${mapped.storage_name}</div>` : ''}
                        ${mapped.screen_name ? `<div><span class="font-medium">Pantalla:</span> ${mapped.screen_name}</div>` : ''}
                    </div>
                </div>
                
                <div class="border-t pt-4">
                    <p class="text-sm text-gray-600">${product.short_description || product.summary_short || ''}</p>
                </div>
            </div>
        `;
    }

    importIcecatData(data) {
        // Configurar datos ocultos de Icecat
        document.getElementById('icecat_data_id').value = data.icecat_data_id;
        document.getElementById('data_source').value = 'icecat';

        // Pre-llenar el formulario
        this.prefillForm(data);

        // Mostrar notificación
        this.showSuccess('Datos de Icecat importados. Puedes ajustar cualquier campo antes de guardar.');
    }

    prefillForm(data) {
        const mapped = data.mapped_data;

        // Campos básicos
        if (mapped.display_name) {
            this.displayNameField.value = mapped.display_name;
        }

        if (mapped.short_description) {
            document.getElementById('short_description').value = mapped.short_description;
        }

        if (mapped.long_description_html) {
            document.getElementById('long_description_html').value = mapped.long_description_html;
        }

        // Configurar selects (marcas, modelos, etc.)
        this.prefillCatalogSelect('brand_id', mapped.brand_id, mapped.brand_name);
        this.prefillCatalogSelect('model_id', mapped.model_id, mapped.model_name);
        this.prefillCatalogSelect('processor_id', mapped.processor_id, mapped.processor_name);
        this.prefillCatalogSelect('ram_id', mapped.ram_id, mapped.ram_name);
        this.prefillCatalogSelect('storage_id', mapped.storage_id, mapped.storage_name);
        this.prefillCatalogSelect('screen_id', mapped.screen_id, mapped.screen_name);
        this.prefillCatalogSelect('graphics_card_id', mapped.graphics_card_id, mapped.graphics_card_name);
        this.prefillCatalogSelect('os_id', mapped.os_id, mapped.os_name);

        // Otros campos
        if (mapped.weight_kg) {
            document.getElementById('weight_kg').value = mapped.weight_kg;
        }

        if (mapped.category) {
            document.getElementById('category').value = mapped.category;
        }

        // Generar SKU automático si no existe
        if (!this.skuField.value) {
            this.generateAutoSku();
        }
    }

    async prefillCatalogSelect(selectId, catalogId, catalogName) {
        const select = document.getElementById(selectId);
        if (!select || !catalogName) return;

        // Si ya hay un ID, seleccionarlo
        if (catalogId) {
            select.value = catalogId;
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

                // Actualizar opciones del select
                const option = new Option(catalogName, data.id, true, true);
                select.appendChild(option);

                // Trigger change para Select2
                $(select).trigger('change');
            }
        } catch (error) {
            console.error('Error prellenando select:', error);
        }
    }

    generateAutoSku() {
        const brand = document.getElementById('brand_id').options[document.getElementById('brand_id').selectedIndex]?.text || 'GEN';
        const category = document.getElementById('category').value || 'LAP';
        const timestamp = Date.now().toString().slice(-4);

        const sku = `${brand.slice(0, 3).toUpperCase()}-${category.slice(0, 3).toUpperCase()}-${timestamp}`;
        this.skuField.value = sku;
    }

    createResultsModal() {
        const modalHTML = `
            <div id="icecat-results-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 hidden">
                <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-2/3 lg:w-1/2 shadow-lg rounded-md bg-white">
                    <div class="mt-3">
                        <div class="flex justify-between items-center pb-3 border-b">
                            <h3 class="text-xl font-bold text-gray-900">
                                <i class="fas fa-cloud-download-alt text-blue-600 mr-2"></i>
                                Producto Encontrado en Icecat
                            </h3>
                            <button onclick="document.getElementById('icecat-results-modal').classList.add('hidden')" 
                                    class="text-gray-400 hover:text-gray-600">
                                <i class="fas fa-times text-2xl"></i>
                            </button>
                        </div>
                        
                        <div class="mt-4" id="icecat-results-content">
                            <!-- Contenido dinámico -->
                        </div>
                        
                        <div class="flex justify-end space-x-3 mt-6 border-t pt-4">
                            <button id="btn-edit-manually" class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
                                <i class="fas fa-edit mr-2"></i> Editar Manualmente
                            </button>
                            <button id="btn-import-icecat" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                                <i class="fas fa-download mr-2"></i> Importar Datos
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    showLoading(message) {
        // Crear o mostrar overlay de carga
        let loader = document.getElementById('scan-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'scan-loader';
            loader.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            loader.innerHTML = `
                <div class="bg-white p-6 rounded-lg shadow-lg">
                    <div class="flex items-center">
                        <svg class="animate-spin h-8 w-8 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
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
            loader.classList.add('hidden');
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        const colors = {
            error: 'bg-red-100 border-red-400 text-red-700',
            success: 'bg-green-100 border-green-400 text-green-700',
            info: 'bg-blue-100 border-blue-400 text-blue-700'
        };

        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-4 py-3 rounded border ${colors[type]} z-50 shadow-lg`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    showProductFound(product) {
        this.showNotification(`Producto ya existe en inventario: ${product.sku}`, 'info');

        // Opcional: Redirigir a la edición del producto existente
        // window.location.href = `/inventory/laptops/${product.id}/edit`;
    }

    showDuplicateWarning(product) {
        const warning = document.createElement('div');
        warning.className = 'mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded';
        warning.innerHTML = `
            <div class="flex items-start">
                <i class="fas fa-exclamation-triangle text-yellow-600 mt-1 mr-2"></i>
                <div>
                    <p class="text-yellow-800 font-medium">Producto ya registrado</p>
                    <p class="text-yellow-700 text-sm">SKU: ${product.sku} - ${product.display_name}</p>
                    <a href="/inventory/laptops/${product.id}/edit" 
                       class="text-blue-600 hover:underline text-sm mt-1 inline-block">
                        Ver producto existente
                    </a>
                </div>
            </div>
        `;

        // Insertar después del campo GTIN
        this.gtinField.parentNode.appendChild(warning);

        // Auto-remover después de 10 segundos
        setTimeout(() => warning.remove(), 10000);
    }

    offerManualEntry(gtin) {
        const container = document.createElement('div');
        container.className = 'mt-4 p-4 bg-gray-50 rounded border';
        container.innerHTML = `
            <p class="text-gray-700 mb-2">No encontrado en Icecat. ¿Deseas agregarlo manualmente?</p>
            <div class="flex space-x-2">
                <button onclick="this.parentElement.parentElement.remove()" 
                        class="px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">
                    Cancelar
                </button>
                <button onclick="document.getElementById('display_name').focus()" 
                        class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
                    Continuar Manualmente
                </button>
            </div>
        `;

        // Insertar después del campo GTIN
        this.gtinField.parentNode.appendChild(container);
    }

    openScanner() {
        // Implementar escáner de cámara si está disponible
        if (typeof window.openBarcodeScanner === 'function') {
            window.openBarcodeScanner((code) => {
                this.gtinField.value = code;
                this.handleScan(code);
            });
        } else {
            // Simular escáner con campo de texto
            this.gtinField.focus();
            this.gtinField.select();
            this.showNotification('Escanea el código de barras o ingrésalo manualmente', 'info');
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.laptopScanner = new LaptopScanner('laptop-form');
});