// ============================================
// FORMULARIO DE LAPTOPS - FUNCIONALIDAD PRINCIPAL
// ============================================

$(document).ready(function() {
    // ===== CONFIGURACION DE SELECT2 CON TAGS =====
    function initSelect2WithTags(selector, endpoint, placeholder) {
        $(selector).select2({
            tags: true,
            placeholder: placeholder || 'Busca o escribe para crear un nuevo elemento...',
            allowClear: true,
            width: '100%',
            ajax: {
                url: endpoint,
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        q: params.term || '',
                        page: params.page || 1
                    };
                },
                processResults: function(data, params) {
                    params.page = params.page || 1;
                    return {
                        results: data.results,
                        pagination: {
                            more: data.pagination && data.pagination.more
                        }
                    };
                },
                cache: true
            },
            createTag: function(params) {
                var term = $.trim(params.term);
                if (term === '') {
                    return null;
                }
                return {
                    id: 'new:' + term,
                    text: '+ Crear: "' + term + '"',
                    newTag: true
                };
            }
        });

        // Creación inmediata al seleccionar una opción "new:"
        $(selector).on('select2:select', function(e) {
            var data = e.params.data;
            if (data.id && data.id.toString().startsWith('new:')) {
                var newName = data.id.substring(4);
                var postData = { name: newName };

                $.ajax({
                    url: endpoint,
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(postData),
                    success: function(response) {
                        if (response && response.id) {
                            var newOption = new Option(newName, response.id, true, true);
                            $(selector).append(newOption).trigger('change');
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('Error creando item:', error);
                        alert('Error al crear: ' + newName + '. Intente de nuevo.');
                        $(selector).val(null).trigger('change');
                    }
                });
            }
        });
    }

    // ===== INICIALIZAR CAMPOS SELECT2 =====
    initSelect2WithTags('#brand_id', '/api/catalog/brands', 'Selecciona o crea una marca...');

    $('#model_id').select2({
        tags: true,
        placeholder: 'Busca o escribe para crear un modelo... (primero selecciona marca)',
        allowClear: true,
        width: '100%',
        ajax: {
            url: '/api/catalog/models',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                var brandId = $('#brand_id').val();
                return {
                    q: params.term || '',
                    page: params.page || 1,
                    brand_id: brandId && !brandId.toString().startsWith('new:') ? brandId : ''
                };
            },
            processResults: function(data, params) {
                params.page = params.page || 1;
                return {
                    results: data.results,
                    pagination: {
                        more: data.pagination && data.pagination.more
                    }
                };
            },
            cache: true
        },
        createTag: function(params) {
            var term = $.trim(params.term);
            if (term === '') {
                return null;
            }
            return {
                id: 'new:' + term,
                text: '+ Crear: "' + term + '"',
                newTag: true
            };
        }
    });

    // Creación inmediata para modelos
    $('#model_id').on('select2:select', function(e) {
        var data = e.params.data;
        if (data.id && data.id.toString().startsWith('new:')) {
            var newName = data.id.substring(4);
            var postData = { name: newName };
            var brandId = $('#brand_id').val();
            if (brandId && !brandId.toString().startsWith('new:')) {
                postData.brand_id = brandId;
            }

            $.ajax({
                url: '/api/catalog/models',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(postData),
                success: function(response) {
                    if (response && response.id) {
                        var newOption = new Option(newName, response.id, true, true);
                        $('#model_id').append(newOption).trigger('change');
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error creando modelo:', error);
                    alert('Error al crear modelo: ' + newName + '. Intente de nuevo.');
                    $('#model_id').val(null).trigger('change');
                }
            });
        }
    });

    // Cuando cambia la marca, limpiar el modelo
    $('#brand_id').on('change', function() {
        var brandVal = $(this).val();
        $('#model_id').val(null).trigger('change');

        if (brandVal && !brandVal.toString().startsWith('new:')) {
            $('#model_id').data('select2').options.options.placeholder = 'Busca o escribe para crear un modelo...';
        } else {
            $('#model_id').data('select2').options.options.placeholder = 'Busca o escribe para crear un modelo... (primero selecciona marca)';
        }
    });

    // Otros campos de catalogo
    initSelect2WithTags('#processor_id', '/api/catalog/processors', 'Selecciona o crea un procesador...');
    initSelect2WithTags('#os_id', '/api/catalog/operating-systems', 'Selecciona o crea un SO...');
    initSelect2WithTags('#screen_id', '/api/catalog/screens', 'Selecciona o crea una pantalla...');
    initSelect2WithTags('#graphics_card_id', '/api/catalog/graphics-cards', 'Selecciona o crea una GPU...');
    initSelect2WithTags('#storage_id', '/api/catalog/storage', 'Selecciona o crea almacenamiento...');
    initSelect2WithTags('#ram_id', '/api/catalog/ram', 'Selecciona o crea RAM...');
    initSelect2WithTags('#store_id', '/api/catalog/stores', 'Selecciona o crea una tienda...');

    // Ubicación necesita manejo especial por store_id
    $('#location_id').select2({
        tags: true,
        placeholder: 'Selecciona o crea una ubicación...',
        allowClear: true,
        width: '100%',
        ajax: {
            url: '/api/catalog/locations',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                var storeId = $('#store_id').val();
                return {
                    q: params.term || '',
                    page: params.page || 1,
                    store_id: storeId && !storeId.toString().startsWith('new:') ? storeId : ''
                };
            },
            processResults: function(data, params) {
                params.page = params.page || 1;
                return {
                    results: data.results,
                    pagination: {
                        more: data.pagination && data.pagination.more
                    }
                };
            },
            cache: true
        },
        createTag: function(params) {
            var term = $.trim(params.term);
            if (term === '') {
                return null;
            }
            return {
                id: 'new:' + term,
                text: '+ Crear: "' + term + '"',
                newTag: true
            };
        }
    });

    // Creación inmediata para ubicaciones
    $('#location_id').on('select2:select', function(e) {
        var data = e.params.data;
        if (data.id && data.id.toString().startsWith('new:')) {
            var newName = data.id.substring(4);
            var postData = { name: newName };
            var storeId = $('#store_id').val();
            if (storeId && !storeId.toString().startsWith('new:')) {
                postData.store_id = storeId;
            }

            $.ajax({
                url: '/api/catalog/locations',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(postData),
                success: function(response) {
                    if (response && response.id) {
                        var newOption = new Option(newName, response.id, true, true);
                        $('#location_id').append(newOption).trigger('change');
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error creando ubicación:', error);
                    alert('Error al crear ubicación: ' + newName + '. Intente de nuevo.');
                    $('#location_id').val(null).trigger('change');
                }
            });
        }
    });

    initSelect2WithTags('#supplier_id', '/api/catalog/suppliers', 'Selecciona o crea un proveedor...');

    // ===== GENERAR DISPLAY_NAME AUTOMATICAMENTE =====
    function generateDisplayName() {
        var parts = [];

        // Obtener texto de cada campo Select2
        var brand = $('#brand_id').select2('data')[0];
        var model = $('#model_id').select2('data')[0];
        var processor = $('#processor_id').select2('data')[0];
        var ram = $('#ram_id').select2('data')[0];
        var storage = $('#storage_id').select2('data')[0];
        var screen = $('#screen_id').select2('data')[0];
        var category = $('#category').val();

        // Agregar marca
        if (brand && brand.text && brand.id != 0) {
            var brandText = brand.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(brandText);
        }

        // Agregar modelo
        if (model && model.text && model.id != 0) {
            var modelText = model.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(modelText);
        }

        // Agregar procesador
        if (processor && processor.text && processor.id != 0) {
            var processorText = processor.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(processorText);
        }

        // Agregar RAM
        if (ram && ram.text && ram.id != 0) {
            var ramText = ram.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(ramText);
        }

        // Agregar almacenamiento
        if (storage && storage.text && storage.id != 0) {
            var storageText = storage.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(storageText);
        }

        // Agregar pantalla
        if (screen && screen.text && screen.id != 0) {
            var screenText = screen.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(screenText);
        }

        // Agregar categoria
        if (category) {
            var categoryLabels = {
                'laptop': 'Laptop',
                'workstation': 'Workstation',
                'gaming': 'Gaming'
            };
            if (categoryLabels[category]) {
                parts.push(categoryLabels[category]);
            }
        }

        // Generar nombre
        var displayName = parts.join(' - ');
        $('#display_name').val(displayName);
    }

    // Escuchar cambios en los campos
    $('#brand_id, #model_id, #processor_id, #ram_id, #storage_id, #screen_id, #category').on('change', function() {
        generateDisplayName();
    });

    // Generar al cargar
    setTimeout(generateDisplayName, 100);

    // ===== CALCULAR MARGEN AUTOMATICAMENTE =====
    function calculateMargin() {
        var purchaseCost = parseFloat($('#purchase_cost').val()) || 0;
        var salePrice = parseFloat($('#sale_price').val()) || 0;

        if (salePrice > 0 && purchaseCost > 0) {
            var profit = salePrice - purchaseCost;
            var margin = (profit / salePrice) * 100;

            $('#margin-display').text(margin.toFixed(1) + '%');
            $('#profit-display').text('Ganancia: $' + profit.toFixed(2));

            // Cambiar color segun el margen
            $('#margin-display').removeClass('text-green-600 text-yellow-600 text-red-600 dark:text-green-400 dark:text-yellow-400 dark:text-red-400');
            if (margin < 15) {
                $('#margin-display').addClass('text-red-600 dark:text-red-400');
            } else if (margin < 25) {
                $('#margin-display').addClass('text-yellow-600 dark:text-yellow-400');
            } else {
                $('#margin-display').addClass('text-green-600 dark:text-green-400');
            }
        } else {
            $('#margin-display').text('0%').removeClass('text-yellow-600 text-red-600 dark:text-yellow-400 dark:text-red-400').addClass('text-green-600 dark:text-green-400');
            $('#profit-display').text('Ganancia: $0.00');
        }
    }

    $('#purchase_cost, #sale_price').on('input', calculateMargin);
    calculateMargin();
});