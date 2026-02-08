/**
 * Catalog Manager JS - Hierarchical Navigation
 * Manages 10 top-level catalogs. Brands and Stores are clickable to view their nested items.
 */

// 10 Catalogs (Models and Locations are managed hierarchically)
const CATALOG_CONFIG = {
    'brands': { label: 'Marcas', icon: 'fa-tag', hierarchical: true },
    'processors': { label: 'Generaciones de Procesador', icon: 'fa-microchip' },
    'operating-systems': { label: 'Sistemas Operativos', icon: 'fa-compact-disc' },
    'screens': { label: 'Pantallas', icon: 'fa-desktop' },
    'graphics-cards': { label: 'Tarjetas Gráficas', icon: 'fa-memory' },
    'storage': { label: 'Almacenamiento', icon: 'fa-hdd' },
    'ram': { label: 'Memoria RAM', icon: 'fa-memory' },
    'stores': { label: 'Tiendas', icon: 'fa-store', hierarchical: true },
    'suppliers': { label: 'Proveedores', icon: 'fa-truck' },
    'expense-categories': { label: 'Categorías de Gastos', icon: 'fa-file-invoice-dollar' }
};

// State
let currentState = {
    currentCatalog: 'brands',
    page: 1,
    pageSize: 20,
    search: '',
    items: [],
    loading: false,
    showInactive: false
};

// DOM Elements
const dom = {
    sidebar: document.getElementById('catalogNav'),
    mobileSelect: document.getElementById('mobileCatalogSelect'),
    title: document.getElementById('currentCatalogTitle'),
    stats: document.getElementById('catalogStats'),
    tableBody: document.getElementById('catalogTableBody'),
    paginationInfo: document.getElementById('paginationInfo'),
    prevBtn: document.getElementById('prevPageBtn'),
    nextBtn: document.getElementById('nextPageBtn'),
    searchInput: document.getElementById('searchInput'),
    showInactiveCheck: document.getElementById('showInactiveCheck'),
    emptyState: document.getElementById('emptyState'),
    loadingState: document.getElementById('loadingState'),
    itemModal: document.getElementById('itemModal'),
    itemForm: document.getElementById('itemForm'),
    dynamicFields: document.getElementById('dynamicFields'),
    itemId: document.getElementById('itemId'),
    itemName: document.getElementById('itemName'),
    modalTitle: document.getElementById('modalTitle'),
    mergeModal: document.getElementById('mergeModal'),
    mergeForm: document.getElementById('mergeForm'),
    mergeSourceName: document.getElementById('mergeSourceName'),
    mergeSourceId: document.getElementById('mergeSourceId'),
    mergeTargetSelect: document.getElementById('mergeTargetSelect')
};

// ==========================================
// Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();

    // Load initial catalog
    const urlParams = new URLSearchParams(window.location.search);
    const initialCatalog = urlParams.get('type') || 'brands';
    loadCatalog(initialCatalog);

    // Event Listeners
    dom.searchInput.addEventListener('input', debounce(handleSearch, 300));
    dom.showInactiveCheck.addEventListener('change', handleShowInactive);
    dom.prevBtn.addEventListener('click', () => changePage(-1));
    dom.nextBtn.addEventListener('click', () => changePage(1));

    // Form Submit
    dom.itemForm.addEventListener('submit', handleSaveItem);
    dom.mergeForm.addEventListener('submit', handleMerge);

    // Close modal on click outside
    document.querySelectorAll('.modal-backdrop').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});

function initSidebar() {
    dom.sidebar.innerHTML = '';

    // Add "Close" button for mobile
    const closeBtn = document.createElement('div');
    closeBtn.className = 'flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-700 lg:hidden mb-4';
    closeBtn.innerHTML = `
        <span class="font-bold text-gray-900 dark:text-white">Menú Catálogos</span>
        <button onclick="toggleSidebar()" class="p-2 text-gray-500"><i class="fa-solid fa-times text-xl"></i></button>
    `;
    dom.sidebar.appendChild(closeBtn);

    for (const [key, config] of Object.entries(CATALOG_CONFIG)) {
        // Desktop Sidebar
        const item = document.createElement('div');
        item.className = 'catalog-nav-item';
        item.dataset.type = key;
        item.innerHTML = `<i class="fa-solid ${config.icon}"></i> <span>${config.label}</span>`;
        item.onclick = () => {
            loadCatalog(key);
            if (window.innerWidth <= 1024) toggleSidebar();
        };
        dom.sidebar.appendChild(item);
    }
}

// ==========================================
// Core Logic
// ==========================================

function loadCatalog(type) {
    if (!CATALOG_CONFIG[type]) return;

    currentState.currentCatalog = type;
    currentState.page = 1;
    currentState.search = '';
    dom.searchInput.value = '';

    // Update URL
    const url = new URL(window.location);
    url.searchParams.set('type', type);
    window.history.pushState({}, '', url);

    // Update UI Active State
    document.querySelectorAll('.catalog-nav-item').forEach(el => {
        el.classList.toggle('active', el.dataset.type === type);
    });

    dom.title.textContent = CATALOG_CONFIG[type].label;

    fetchData();
}

async function fetchData() {
    currentState.loading = true;
    updateTableUI();

    try {
        const params = new URLSearchParams({
            page: currentState.page,
            page_size: currentState.pageSize,
            active_only: (!currentState.showInactive).toString(),
            q: currentState.search
        });

        const response = await fetch(`/api/catalog/${currentState.currentCatalog}?${params}`);
        if (!response.ok) throw new Error('Error cargando datos');

        const data = await response.json();

        currentState.items = data.results;
        currentState.total = data.total || data.results.length;

        const hasMore = data.pagination?.more || false;

        renderTable();
        updatePagination(hasMore);
        updateStats(currentState.total);

    } catch (error) {
        console.error(error);
        showToast('Error', 'No se pudieron cargar los datos', 'error');
    } finally {
        currentState.loading = false;
        updateTableUI();
    }
}

// ==========================================
// Rendering
// ==========================================

function renderTable() {
    dom.tableBody.innerHTML = '';

    if (currentState.items.length === 0) {
        dom.emptyState.classList.remove('hidden');
        return;
    }
    dom.emptyState.classList.add('hidden');

    const isHierarchical = CATALOG_CONFIG[currentState.currentCatalog].hierarchical;

    currentState.items.forEach(item => {
        const tr = document.createElement('tr');
        if (isHierarchical) {
            tr.classList.add('clickable');
            tr.onclick = () => navigateToDetail(item.id, item.text);
        }

        let html = `
            <td data-label="ID"><span class="text-[var(--text-sub)] font-mono text-xs">#${item.id}</span></td>
            <td data-label="Nombre">
                <div class="font-medium">${item.text}</div>
                ${renderExtraInfo(item)}
            </td>
            <td data-label="Estado">
                <span class="status-badge ${item.is_active ? 'active' : 'inactive'}">
                    <i class="fa-solid fa-circle text-[0.4rem]"></i>
                    ${item.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td data-label="Acciones" class="text-right">
                <div class="flex items-center justify-end gap-1">
                    ${renderActionButtons(item, isHierarchical)}
                </div>
            </td>
        `;

        tr.innerHTML = html;
        dom.tableBody.appendChild(tr);
    });
}

function renderExtraInfo(item) {
    if (currentState.currentCatalog === 'suppliers') {
        return item.phone ? `<span class="text-xs text-[var(--text-sub)]"><i class="fa-solid fa-phone mr-1"></i>${item.phone}</span>` : '';
    }
    if (currentState.currentCatalog === 'expense-categories' && item.color) {
        return `<span class="inline-block w-4 h-4 rounded-full border border-[var(--border-subtle)]" style="background:${item.color}"></span>`;
    }
    if (currentState.currentCatalog === 'stores' && item.address) {
        return `<span class="text-xs text-[var(--text-sub)]">${item.address}</span>`;
    }
    return '';
}

function renderActionButtons(item, isHierarchical) {
    let btns = '';

    // For hierarchical items (Brands, Stores), show "View Details" icon
    if (isHierarchical) {
        btns += `
            <button onclick="event.stopPropagation(); navigateToDetail(${item.id}, '${item.text.replace(/'/g, "\\'")}')" class="action-btn" title="Ver Detalles">
                <i class="fa-solid fa-arrow-right"></i>
            </button>
        `;
    }

    if (item.is_active) {
        btns += `
            <button onclick="event.stopPropagation(); editItem(${item.id})" class="action-btn edit" title="Editar">
                <i class="fa-solid fa-pen"></i>
            </button>
            <button onclick="event.stopPropagation(); openMergeModal(${item.id}, '${item.text.replace(/'/g, "\\'")}')" class="action-btn merge" title="Fusionar">
                <i class="fa-solid fa-code-merge"></i>
            </button>
            <button onclick="event.stopPropagation(); deleteItem(${item.id}, '${item.text.replace(/'/g, "\\'")}')" class="action-btn delete" title="Desactivar">
                <i class="fa-solid fa-trash"></i>
            </button>
        `;
    } else {
        btns += `
            <button onclick="event.stopPropagation(); reactivateItem(${item.id})" class="action-btn restore" title="Reactivar">
                <i class="fa-solid fa-undo"></i>
            </button>
        `;
    }
    return btns;
}

function navigateToDetail(id, name) {
    // Navigate to detail page for Brand or Store
    window.location.href = `/admin/catalogs/${currentState.currentCatalog}/${id}`;
}

// ==========================================
// CRUD Logic
// ==========================================

function openModal(mode, item = null) {
    dom.itemForm.reset();
    dom.dynamicFields.innerHTML = '';

    if (mode === 'create') {
        dom.modalTitle.textContent = `Nuevo ${CATALOG_CONFIG[currentState.currentCatalog].label.slice(0, -1)}`;
        dom.itemId.value = '';
    } else {
        dom.modalTitle.textContent = 'Editar Elemento';
        dom.itemId.value = item.id;
        dom.itemName.value = item.text;

        // Populate extra fields for specific catalogs
        if (currentState.currentCatalog === 'suppliers') {
            if (item.contact_name) createInput('contact_name', 'Contacto', item.contact_name);
            if (item.email) createInput('email', 'Email', item.email, 'email');
            if (item.phone) createInput('phone', 'Teléfono', item.phone);
            if (item.address) createTextarea('address', 'Dirección', item.address);
            if (item.website) createInput('website', 'Sitio Web', item.website);
        } else if (currentState.currentCatalog === 'expense-categories') {
            createInput('color', 'Color', item.color || '#6366f1', 'color');
            if (item.description) createTextarea('description', 'Descripción', item.description);
        } else if (currentState.currentCatalog === 'stores') {
            if (item.phone) createInput('phone', 'Teléfono', item.phone);
            if (item.address) createTextarea('address', 'Dirección', item.address);
        }
    }

    // Add extra fields for create mode
    if (mode === 'create') {
        if (currentState.currentCatalog === 'suppliers') {
            createInput('contact_name', 'Nombre de Contacto');
            createInput('email', 'Email', '', 'email');
            createInput('phone', 'Teléfono');
            createTextarea('address', 'Dirección');
            createInput('website', 'Sitio Web');
        } else if (currentState.currentCatalog === 'expense-categories') {
            createInput('color', 'Color', '#6366f1', 'color');
            createTextarea('description', 'Descripción');
        } else if (currentState.currentCatalog === 'stores') {
            createInput('phone', 'Teléfono');
            createTextarea('address', 'Dirección');
        }
    }

    dom.itemModal.classList.add('active');
}

function closeModal() {
    dom.itemModal.classList.remove('active');
}

function editItem(id) {
    const item = currentState.items.find(i => i.id === id);
    if (item) openModal('edit', item);
}

async function handleSaveItem(e) {
    e.preventDefault();

    const formData = new FormData(dom.itemForm);
    const data = Object.fromEntries(formData.entries());
    const id = dom.itemId.value;
    const isEdit = !!id;

    const url = `/api/catalog/${currentState.currentCatalog}` + (isEdit ? `/${id}` : '');
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        if (!res.ok) throw new Error(result.error || 'Error al guardar');

        showToast('Éxito', result.message);
        dom.itemModal.classList.remove('active');
        fetchData();

    } catch (err) {
        showToast('Error', err.message, 'error');
    }
}

async function deleteItem(id, name) {
    if (!confirm(`¿Estás seguro de desactivar "${name}"?`)) return;

    try {
        const res = await fetch(`/api/catalog/${currentState.currentCatalog}/${id}`, {
            method: 'DELETE'
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.error);

        showToast('Desactivado', result.message);
        fetchData();
    } catch (err) {
        showToast('Error', err.message, 'error');
    }
}

async function reactivateItem(id) {
    try {
        const res = await fetch(`/api/catalog/${currentState.currentCatalog}/${id}/reactivate`, {
            method: 'POST'
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.error);

        showToast('Reactivado', result.message);
        fetchData();
    } catch (err) {
        showToast('Error', err.message, 'error');
    }
}

// ==========================================
// Merge Logic
// ==========================================

async function openMergeModal(id, name) {
    dom.mergeSourceName.textContent = name;
    dom.mergeSourceId.value = id;

    dom.mergeTargetSelect.innerHTML = '<option>Cargando...</option>';

    try {
        const res = await fetch(`/api/catalog/${currentState.currentCatalog}?active_only=true&page_size=100`);
        const data = await res.json();

        dom.mergeTargetSelect.innerHTML = '<option value="">Seleccionar destino...</option>';
        data.results.forEach(item => {
            if (item.id != id) {
                dom.mergeTargetSelect.innerHTML += `<option value="${item.id}">${item.text}</option>`;
            }
        });

        dom.mergeModal.classList.add('active');
    } catch (e) {
        showToast('Error', 'No se pudieron cargar los destinos', 'error');
    }
}

async function handleMerge(e) {
    e.preventDefault();

    const sourceId = dom.mergeSourceId.value;
    const targetId = dom.mergeTargetSelect.value;

    if (!targetId) {
        showToast('Atención', 'Selecciona un registro destino', 'warning');
        return;
    }

    if (!confirm('Esta acción es irreversible. Se eliminará el registro origen y se moverán todas sus relaciones. ¿Continuar?')) return;

    try {
        const res = await fetch(`/api/catalog/${currentState.currentCatalog}/merge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_id: sourceId, target_id: targetId })
        });

        const result = await res.json();
        if (!res.ok) throw new Error(result.error);

        showToast('Fusión Exitosa', result.message);
        dom.mergeModal.classList.remove('active');
        fetchData();

    } catch (err) {
        showToast('Error', err.message, 'error');
    }
}

// ==========================================
// Utils & Helpers
// ==========================================

function updateTableUI() {
    if (currentState.loading) {
        dom.tableBody.innerHTML = '';
        dom.loadingState.classList.remove('hidden');
        dom.emptyState.classList.add('hidden');
    } else {
        dom.loadingState.classList.add('hidden');
    }
}

function updateStats(total) {
    dom.stats.textContent = `${total || 0} registros`;
    dom.paginationInfo.textContent = `Página ${currentState.page}`;
}

function updatePagination(hasMore) {
    dom.prevBtn.disabled = currentState.page === 1;
    dom.nextBtn.disabled = !hasMore && (currentState.items.length < currentState.pageSize);
}

function changePage(delta) {
    const newPage = currentState.page + delta;
    if (newPage < 1) return;
    currentState.page = newPage;
    fetchData();
}

function handleSearch(e) {
    currentState.search = e.target.value.trim();
    currentState.page = 1;
    fetchData();
}

function handleShowInactive(e) {
    currentState.showInactive = e.target.checked;
    currentState.page = 1;
    fetchData();
}

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Dynamic Form Helpers
function createInput(name, label, value = '', type = 'text') {
    const div = document.createElement('div');
    div.innerHTML = `
        <label class="block text-sm font-medium text-[var(--text-sub)] mb-1">${label}</label>
        <input type="${type}" name="${name}" value="${value}" class="w-full px-4 py-2 bg-[var(--bg-body)] border border-[var(--border-subtle)] rounded-xl text-[var(--text-main)] focus:border-purple-500 outline-none">
    `;
    dom.dynamicFields.appendChild(div);
}

function createTextarea(name, label, value = '') {
    const div = document.createElement('div');
    div.innerHTML = `
        <label class="block text-sm font-medium text-[var(--text-sub)] mb-1">${label}</label>
        <textarea name="${name}" rows="3" class="w-full px-4 py-2 bg-[var(--bg-body)] border border-[var(--border-subtle)] rounded-xl text-[var(--text-main)] focus:border-purple-500 outline-none">${value}</textarea>
    `;
    dom.dynamicFields.appendChild(div);
}

// Toast Notification (assumes showToast is globally available from base.html)
function showToast(title, message, type = 'success') {
    if (typeof window.showToast === 'function') {
        window.showToast(title, message, type);
    } else {
        alert(`${title}: ${message}`);
    }
}

function toggleSidebar() {
    const sidebar = document.querySelector('.catalog-sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar) sidebar.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');

    if (sidebar && sidebar.classList.contains('active')) {
        document.body.style.overflow = 'hidden';
    } else {
        document.body.style.overflow = '';
    }
}
