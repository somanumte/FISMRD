/**
 * Laptop Form Reactive Name Updates
 * Automatically updates "Nombre completo" fields when individual component specs change.
 */

(function () {
    'use strict';

    const utils = {
        cleanJoin: function (parts) {
            const cleanParts = [];
            parts.filter(Boolean).forEach(p => {
                const part = String(p).trim();
                if (!part) return;
                if (cleanParts.length === 0 || part.toLowerCase() !== cleanParts[cleanParts.length - 1].toLowerCase()) {
                    cleanParts.push(part);
                }
            });
            return cleanParts.join(' ');
        },
        mapResolution: function (res) {
            if (!res) return null;
            const match = String(res).match(/(\d{3,4})/);
            if (!match) return null;
            const hRes = parseInt(match[1]);
            if (hRes >= 1800 && hRes <= 2000) return "FHD";
            if (hRes > 2000 && hRes <= 2600) return "2K";
            if (hRes > 2600 && hRes <= 2900) return "2.5K";
            if (hRes > 2900 && hRes <= 3400) return "3K";
            if (hRes > 3400 && hRes <= 4500) return "4K";
            if (hRes > 7000 && hRes <= 8500) return "8K";
            return null;
        }
    };

    const reactiveLogic = {
        // --- PROCESSOR ---
        updateProcessor: function () {
            const family = document.getElementById('processor_family')?.value || '';
            const generation = document.getElementById('processor_generation')?.value || '';
            const model = document.getElementById('processor_model')?.value || '';

            let parts = [];
            if (generation) parts.push(generation);
            if (family && !generation.toLowerCase().includes(family.toLowerCase())) {
                parts.push(family);
            }
            parts.push(model);

            const fullName = utils.cleanJoin(parts);
            const target = document.getElementById('processor_full_name');
            if (target) target.value = fullName;
        },

        // --- SCREEN ---
        updateScreen: function () {
            const diagonal = document.getElementById('screen_diagonal_inches')?.value || '';
            const resolution = document.getElementById('screen_resolution')?.value || '';
            const hdType = document.getElementById('screen_hd_type')?.value || '';
            const panel = document.getElementById('screen_panel_type')?.value || '';
            const refresh = document.getElementById('screen_refresh_rate')?.value || '';
            const touch = document.getElementById('screen_touchscreen_override')?.checked;

            const resLabel = utils.mapResolution(resolution);

            const parts = [];
            if (diagonal) parts.push(`${diagonal}"`);
            if (resLabel) parts.push(resLabel);

            if (hdType) {
                // Evitar duplicados (ej: FHD FHD)
                if (!resLabel || hdType.toLowerCase() !== resLabel.toLowerCase()) {
                    parts.push(hdType);
                }
            }

            if (panel) parts.push(panel.replace(/-Level/g, ''));
            if (refresh && parseInt(refresh) > 60) parts.push(`${refresh}Hz`);
            if (touch) parts.push('Touch');

            const fullName = utils.cleanJoin(parts);
            const target = document.getElementById('screen_full_name');
            if (target) target.value = fullName;
        },

        // --- DISCRETE GPU ---
        updateDiscreteGPU: function () {
            const hasDiscrete = document.getElementById('has_discrete_gpu')?.checked;
            if (!hasDiscrete) {
                const target = document.getElementById('discrete_gpu_full_name');
                if (target) target.value = '';
                return;
            }

            const brand = document.getElementById('discrete_gpu_brand')?.value || '';
            const model = document.getElementById('discrete_gpu_model')?.value || '';
            const memory = document.getElementById('discrete_gpu_memory_gb')?.value || '';
            const type = document.getElementById('discrete_gpu_memory_type')?.value || '';

            let parts = [];
            if (brand && !model.toLowerCase().includes(brand.toLowerCase())) {
                parts.push(brand);
            }
            parts.push(model);
            if (memory) parts.push(`${memory}GB`);
            if (type) parts.push(type);

            const fullName = utils.cleanJoin(parts);
            const target = document.getElementById('discrete_gpu_full_name');
            if (target) target.value = fullName;
        },

        // --- ONBOARD GPU ---
        updateOnboardGPU: function () {
            const brand = document.getElementById('onboard_gpu_brand')?.value || '';
            const model = document.getElementById('onboard_gpu_model')?.value || '';
            const family = document.getElementById('onboard_gpu_family')?.value || '';
            const memory = document.getElementById('onboard_gpu_memory_gb')?.value || '';

            let parts = [];
            if (brand && !model.toLowerCase().includes(brand.toLowerCase())) {
                parts.push(brand);
            }
            parts.push(model);
            if (family && !model.toLowerCase().includes(family.toLowerCase())) {
                parts.push(family);
            }
            if (memory) parts.push(`${memory}GB`);

            const fullName = utils.cleanJoin(parts);
            const target = document.getElementById('onboard_gpu_full_name');
            if (target) target.value = fullName;
        },

        // --- STORAGE ---
        updateStorage: function () {
            const capacity = document.getElementById('storage_capacity')?.value || '';
            const media = document.getElementById('storage_media')?.value || '';
            const nvme = document.getElementById('storage_nvme')?.checked;
            const formFactor = document.getElementById('storage_form_factor')?.value || '';

            let capStr = capacity;
            if (capacity && parseInt(capacity) >= 1024) {
                capStr = `${(parseInt(capacity) / 1024).toFixed(1)}TB`.replace('.0', '');
            } else if (capacity) {
                capStr = `${capacity}GB`;
            }

            const parts = [capStr, media, nvme ? 'NVMe' : '', formFactor];
            const fullName = utils.cleanJoin(parts);

            const target = document.getElementById('storage_full_name');
            if (target) target.value = fullName;
        },

        // --- RAM ---
        updateRAM: function () {
            const capacity = document.getElementById('ram_capacity')?.value || '';
            const type = document.getElementById('ram_type_detailed')?.value || '';
            const speed = document.getElementById('ram_speed_mhz')?.value || '';
            const transfer = document.getElementById('ram_transfer_rate')?.value || '';

            const parts = [];
            if (capacity) parts.push(`${capacity}GB`);
            if (type) parts.push(type);
            if (speed) parts.push(`${speed}MHz`);
            if (transfer) parts.push(`${transfer}MT/s`);

            const fullName = utils.cleanJoin(parts);
            const target = document.getElementById('ram_full_name');
            if (target) target.value = fullName;
        }
    };

    function init() {
        console.log("LaptopReactiveNames: Initializing listeners...");

        const listeners = [
            { ids: ['processor_family', 'processor_generation', 'processor_model'], callback: reactiveLogic.updateProcessor },
            { ids: ['screen_diagonal_inches', 'screen_resolution', 'screen_hd_type', 'screen_panel_type', 'screen_refresh_rate', 'screen_touchscreen_override'], callback: reactiveLogic.updateScreen },
            { ids: ['has_discrete_gpu', 'discrete_gpu_brand', 'discrete_gpu_model', 'discrete_gpu_memory_gb', 'discrete_gpu_memory_type'], callback: reactiveLogic.updateDiscreteGPU },
            { ids: ['onboard_gpu_brand', 'onboard_gpu_model', 'onboard_gpu_family', 'onboard_gpu_memory_gb'], callback: reactiveLogic.updateOnboardGPU },
            { ids: ['storage_capacity', 'storage_media', 'storage_nvme', 'storage_form_factor'], callback: reactiveLogic.updateStorage },
            { ids: ['ram_capacity', 'ram_type_detailed', 'ram_speed_mhz', 'ram_transfer_rate'], callback: reactiveLogic.updateRAM }
        ];

        listeners.forEach(group => {
            group.ids.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    const eventType = el.type === 'checkbox' ? 'change' : 'input';
                    el.addEventListener(eventType, group.callback);
                    // Also listen for change in case of programmatic updates not triggering input
                    if (eventType !== 'change') el.addEventListener('change', group.callback);
                }
            });
        });

        // Initial run to populate only if fields are empty (e.g. new laptop)
        // If they have values (edit mode), we respect the DB value and only update on manual change
        if (!document.getElementById('processor_full_name')?.value) reactiveLogic.updateProcessor();
        if (!document.getElementById('screen_full_name')?.value) reactiveLogic.updateScreen();
        if (!document.getElementById('discrete_gpu_full_name')?.value) reactiveLogic.updateDiscreteGPU();
        if (!document.getElementById('onboard_gpu_full_name')?.value) reactiveLogic.updateOnboardGPU();
        if (!document.getElementById('storage_full_name')?.value) reactiveLogic.updateStorage();
        if (!document.getElementById('ram_full_name')?.value) reactiveLogic.updateRAM();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
