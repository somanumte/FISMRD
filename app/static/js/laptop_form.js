// ============================================
// FORMULARIO DE LAPTOPS - FUNCIONALIDAD PRINCIPAL
// ============================================

$(document).ready(function () {

    // ===== FUNCIONES HELPER PARA ESTILO ZOHO =====

    // Obtener iniciales del texto (máximo 2 caracteres)
    function getInitials(text) {
        if (!text) return '?';
        var cleanText = text.replace('+ Crear: "', '').replace('"', '').trim();
        var words = cleanText.split(/\s+/);
        if (words.length >= 2) {
            return (words[0][0] + words[1][0]).toUpperCase();
        }
        return cleanText.substring(0, 2).toUpperCase();
    }

    // Colores para avatares (rotación basada en ID)
    function getAvatarColor(id) {
        var colors = [
            { bg: '#e0e7ff', text: '#4f46e5' },  // Indigo
            { bg: '#dbeafe', text: '#2563eb' },  // Blue
            { bg: '#d1fae5', text: '#059669' },  // Green
            { bg: '#fef3c7', text: '#d97706' },  // Amber
            { bg: '#fce7f3', text: '#db2777' },  // Pink
            { bg: '#e0f2fe', text: '#0284c7' },  // Sky
            { bg: '#f3e8ff', text: '#9333ea' },  // Purple
            { bg: '#ffedd5', text: '#ea580c' }   // Orange
        ];
        var index = 0;
        if (id && !isNaN(id)) {
            index = parseInt(id) % colors.length;
        } else if (typeof id === 'string') {
            // Para IDs tipo "new:texto", usar hash del texto
            var hash = 0;
            for (var i = 0; i < id.length; i++) {
                hash = ((hash << 5) - hash) + id.charCodeAt(i);
                hash |= 0;
            }
            index = Math.abs(hash) % colors.length;
        }
        return colors[index];
    }

    // Template para mostrar items en el dropdown (con avatar)
    function formatResultWithAvatar(data) {
        if (data.loading) {
            return $('<div class="select2-item-wrapper"><span>Buscando...</span></div>');
        }

        // Opción para crear nuevo
        if (data.newTag) {
            var newText = data.text.replace('+ Crear: "', '').replace('"', '');
            return $(
                '<div class="select2-create-new">' +
                '<span class="select2-create-new-icon">+</span>' +
                '<span class="select2-create-new-text">Nuevo: ' + escapeHtml(newText) + '</span>' +
                '</div>'
            );
        }

        // Opción normal con avatar
        var initials = getInitials(data.text);
        var color = getAvatarColor(data.id);

        return $(
            '<div class="select2-item-wrapper">' +
            '<span class="select2-item-avatar" style="background-color: ' + color.bg + '; color: ' + color.text + ';">' +
            escapeHtml(initials) +
            '</span>' +
            '<div class="select2-item-content">' +
            '<div class="select2-item-name">' + escapeHtml(data.text) + '</div>' +
            '</div>' +
            '</div>'
        );
    }

    // Template para mostrar selección (con avatar pequeño)
    function formatSelectionWithAvatar(data) {
        if (!data.id || data.id === '0' || data.id === '') {
            return data.text; // Placeholder
        }

        // Si es un nuevo item, mostrar sin avatar
        if (data.id && data.id.toString().startsWith('new:')) {
            var newText = data.text.replace('+ Crear: "', '').replace('"', '');
            return $('<span class="select2-selection-text">' + escapeHtml(newText) + '</span>');
        }

        var initials = getInitials(data.text);
        var color = getAvatarColor(data.id);

        return $(
            '<span class="select2-selection-item">' +
            '<span class="select2-selection-avatar" style="background-color: ' + color.bg + '; color: ' + color.text + ';">' +
            escapeHtml(initials) +
            '</span>' +
            '<span class="select2-selection-text">' + escapeHtml(data.text) + '</span>' +
            '</span>'
        );
    }

    // Escapar HTML para prevenir XSS
    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Envolver Select2 con botón de búsqueda (lupa)
    function wrapWithSearchButton(selector) {
        var $select2Container = $(selector).next('.select2-container');
        if ($select2Container.length && !$select2Container.parent().hasClass('select2-zoho-container')) {
            $select2Container.wrap('<div class="select2-zoho-container"></div>');
            $select2Container.after(
                '<button type="button" class="select2-search-btn" tabindex="-1">' +
                '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">' +
                '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>' +
                '</svg>' +
                '</button>'
            );

            // Al hacer clic en la lupa, abrir el dropdown
            $select2Container.next('.select2-search-btn').on('click', function () {
                $(selector).select2('open');
            });
        }
    }

    // ===== CONFIGURACION DE SELECT2 CON TAGS =====
    function initSelect2WithTags(selector, endpoint, placeholder) {
        $(selector).select2({
            tags: true,
            placeholder: placeholder || 'Buscar o escribir para crear...',
            allowClear: true,
            width: '100%',
            ajax: {
                url: endpoint,
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        q: params.term || '',
                        page: params.page || 1
                    };
                },
                processResults: function (data, params) {
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
            createTag: function (params) {
                var term = $.trim(params.term);
                if (term === '') {
                    return null;
                }
                return {
                    id: 'new:' + term,
                    text: '+ Crear: "' + term + '"',
                    newTag: true
                };
            },
            templateResult: formatResultWithAvatar,
            templateSelection: formatSelectionWithAvatar
        });

        // Creación inmediata al seleccionar una opción "new:"
        $(selector).on('select2:select', function (e) {
            var data = e.params.data;
            if (data.id && data.id.toString().startsWith('new:')) {
                var newName = data.id.substring(4);
                var postData = { name: newName };

                $.ajax({
                    url: endpoint,
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify(postData),
                    success: function (response) {
                        if (response && response.id) {
                            var newOption = new Option(newName, response.id, true, true);
                            $(selector).append(newOption).trigger('change');
                        }
                    },
                    error: function (xhr, status, error) {
                        console.error('Error creando item:', error);
                        alert('Error al crear: ' + newName + '. Intente de nuevo.');
                        $(selector).val(null).trigger('change');
                    }
                });
            }
        });

        // Envolver con botón de búsqueda después de inicializar
        wrapWithSearchButton(selector);
    }

    // ===== INICIALIZAR CAMPOS SELECT2 =====
    // Los campos de especificaciones técnicas (brand, model, processor, etc.) 
    // ahora son StringFields (Inputs simples) para facilitar el auto-llenado de Icecat.
    // Solo inicializamos Select2 para campos de catálogo real que siguen siendo IDs.

    // Se elimina la creación inmediata para campos que ahora son texto libre.

    // Se elimina el trigger de cambio de marca que limpiaba el modelo Select2.

    // Otros campos de catalogo
    // Otros campos que ahora son de texto libre
    // (Ya no se inicializan como Select2)
    initSelect2WithTags('#store_id', '/api/catalog/stores', 'Buscar o crear tienda...');

    // Ubicación necesita manejo especial por store_id
    $('#location_id').select2({
        tags: true,
        placeholder: 'Buscar o crear ubicación...',
        allowClear: true,
        width: '100%',
        ajax: {
            url: '/api/catalog/locations',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                var storeId = $('#store_id').val();
                return {
                    q: params.term || '',
                    page: params.page || 1,
                    store_id: storeId && !storeId.toString().startsWith('new:') ? storeId : ''
                };
            },
            processResults: function (data, params) {
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
        createTag: function (params) {
            var term = $.trim(params.term);
            if (term === '') {
                return null;
            }
            return {
                id: 'new:' + term,
                text: '+ Crear: "' + term + '"',
                newTag: true
            };
        },
        templateResult: formatResultWithAvatar,
        templateSelection: formatSelectionWithAvatar
    });
    wrapWithSearchButton('#location_id');

    // Creación inmediata para ubicaciones
    $('#location_id').on('select2:select', function (e) {
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
                success: function (response) {
                    if (response && response.id) {
                        var newOption = new Option(newName, response.id, true, true);
                        $('#location_id').append(newOption).trigger('change');
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Error creando ubicación:', error);
                    alert('Error al crear ubicación: ' + newName + '. Intente de nuevo.');
                    $('#location_id').val(null).trigger('change');
                }
            });
        }
    });

    initSelect2WithTags('#supplier_id', '/api/catalog/suppliers', 'Buscar o crear proveedor...');



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

    // ===== AUTO-GENERAR SLUG =====
    function generateSlug(text) {
        return text.toString().toLowerCase()
            .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // Quitar acentos
            .replace(/\s+/g, '-')           // Reemplazar espacios con -
            .replace(/[^\w\-]+/g, '')       // Eliminar caracteres no alfanuméricos
            .replace(/\-\-+/g, '-')         // Reemplazar múltiples - con uno solo
            .replace(/^-+/, '')             // Eliminar - al inicio
            .replace(/-+$/, '');            // Eliminar - al final
    }

    var $displayName = $('#display_name');
    var $slug = $('#slug');
    var isEditMode = window.location.pathname.includes('/edit/');
    var slugManualOverride = isEditMode && $slug.val() !== '';

    // Detectar si el usuario edita el slug manualmente
    $slug.on('input', function () {
        slugManualOverride = true;
    });

    $displayName.on('input', function () {
        if (!slugManualOverride) {
            $slug.val(generateSlug($(this).val()));
        }
    });
});