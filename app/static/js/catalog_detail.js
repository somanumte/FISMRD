/**
 * Catalog Detail JS - Hierarchical Child Management
 * Manages Models (for Brands) or Locations (for Stores)
 */

// State
let state = {
    page: 1,
    pageSize: 20,
    search: '',
    items: [],
    loading: false,
    showInactive: false
};

// DOM Elements
const dom = {
    childTableBody: document.getElementById('childTableBody'),
    childStats: document.getElementById('childStats'),
    paginationInfo: document.getElementById('paginationInfo'),
    prevBtn: document.getElementById('prevPageBtn'),
    nextBtn: document.getElementById('nextPageBtn'),
    searchInput: document.getElementById('searchInput'),
    showInactiveCheck: document.getElementById('showInactiveCheck'),
    emptyState: document.getElementById('emptyState'),
    loadingState: document.getElementById('loadingState'),
    itemModal: document.getElementById('itemModal'),
    itemForm: document.getElementById('itemForm'),
    itemId: document.getElementById('itemId'),
    itemName: document.getElementById('itemName'),
    modalTitle: document.getElementById('modalTitle'),
    parentModal: document.getElementById('parentModal'),
    parentForm: document.getElementById('parentForm'),
    parentName: document.getElementById('parentName')
};

// ==========================================
// Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    fetchData();

    // Event Listeners
    dom.searchInput.addEventListener('input', debounce(handleSearch, 300));
    dom.showInactiveCheck.addEventListener('change', handleShowInactive);
    dom.prevBtn.addEventListener('click', () => changePage(-1));
    dom.nextBtn.addEventListener('click', () => changePage(1));

    // Form Submit
    dom.itemForm.addEventListener('submit', handleSaveItem);
    dom.parentForm.addEventListener('submit', handleSaveParent);

    // Close modal on click outside
    document.querySelectorAll('.modal-backdrop').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});

// ==========================================
// Core Logic
// ==========================================

async function fetchData() {
    state.loading = true;
    updateTableUI();

    try {
        const params = new URLSearchParams({
            page: state.page,
            page_size: state.pageSize,
            active_only: (!state.showInactive).toString(),
            q: state.search
        });

        // Add parent filter (brand_id or store_id) - ensure it's passed as integer
        if (CATALOG_TYPE === 'brands' && PARENT_ID) {
            params.append('brand_id', parseInt(PARENT_ID));
        } else if (CATALOG_TYPE === 'stores' && PARENT_ID) {
            params.append('store_id', parseInt(PARENT_ID));
        }

        const url = `/api/catalog/${CHILD_TYPE}?${params}`;
        console.log('Fetching:', url);
        console.log('Filters:', { CATALOG_TYPE, PARENT_ID, CHILD_TYPE });

        const response = await fetch(url);
        if (!response.ok) throw new Error('Error cargando datos');

        const data = await response.json();
        console.log('Data received:', data);

        state.items = data.results;
        state.total = data.total || data.results.length;

        const hasMore = data.pagination?.more || false;

        renderTable();
        updatePagination(hasMore);
        updateStats(state.total);

    } catch (error) {
        console.error('Error in fetchData:', error);
        showToast('Error', 'No se pudieron cargar los datos', 'error');
    } finally {
        state.loading = false;
        updateTableUI();
    }
}

// ==========================================
// Rendering
// ==========================================

function renderTable() {
    dom.childTableBody.innerHTML = '';

    if (state.items.length === 0) {
        dom.emptyState.classList.remove('hidden');
        return;
    }
    dom.emptyState.classList.add('hidden');

    state.items.forEach(item => {
        const tr = document.createElement('tr');

        let html = `
            <td><span class="text-[var(--text-sub)] font-mono text-xs">#${item.id}</span></td>
            <td>
                <div class="font-medium">${item.text}</div>
            </td>
            <td>
                <span class="status-badge ${item.is_active ? 'active' : 'inactive'}">
                    <i class="fa-solid fa-circle text-[0.4rem]"></i>
                    ${item.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td class="text-right">
                <div class="flex items-center justify-end gap-1">
                    ${renderActionButtons(item)}
                </div>
            </td>
        `;

        tr.innerHTML = html;
        dom.childTableBody.appendChild(tr);
    });
}

function renderActionButtons(item) {
    let btns = '';

    if (item.is_active) {
        btns += `
            <button onclick="editItem(${item.id})" class="action-btn edit" title="Editar">
                <i class="fa-solid fa-pen"></i>
            </button>
            <button onclick="deleteItem(${item.id}, '${item.text.replace(/'/g, "\\'")}')" class="action-btn delete" title="Desactivar">
                <i class="fa-solid fa-trash"></i>
            </button>
        `;
    } else {
        btns += `
            <button onclick="reactivateItem(${item.id})" class="action-btn restore" title="Reactivar">
                <i class="fa-solid fa-undo"></i>
            </button>
        `;
    }
    return btns;
}

// ==========================================
// CRUD Logic - Child Items
// ==========================================

function openModal(mode, item = null) {
    dom.itemForm.reset();

    if (mode === 'create') {
        dom.modalTitle.textContent = `Nuevo ${CHILD_TYPE === 'models' ? 'Modelo' : 'Ubicación'}`;
        dom.itemId.value = '';
    } else {
        dom.modalTitle.textContent = 'Editar Elemento';
        dom.itemId.value = item.id;
        dom.itemName.value = item.text;
    }

    dom.itemModal.classList.add('active');
}

function closeModal() {
    dom.itemModal.classList.remove('active');
}

function editItem(id) {
    const item = state.items.find(i => i.id === id);
    if (item) openModal('edit', item);
}

async function handleSaveItem(e) {
    e.preventDefault();

    const formData = new FormData(dom.itemForm);
    const data = Object.fromEntries(formData.entries());
    const id = dom.itemId.value;
    const isEdit = !!id;

    // Add parent relationship
    if (CATALOG_TYPE === 'brands') {
        data.brand_id = PARENT_ID;
    } else if (CATALOG_TYPE === 'stores') {
        data.store_id = PARENT_ID;
    }

    const url = `/api/catalog/${CHILD_TYPE}` + (isEdit ? `/${id}` : '');
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
        const res = await fetch(`/api/catalog/${CHILD_TYPE}/${id}`, {
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
        const res = await fetch(`/api/catalog/${CHILD_TYPE}/${id}/reactivate`, {
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
// CRUD Logic - Parent Item
// ==========================================

function editParent() {
    dom.parentModal.classList.add('active');
}

async function handleSaveParent(e) {
    e.preventDefault();

    const formData = new FormData(dom.parentForm);
    const data = Object.fromEntries(formData.entries());

    try {
        const res = await fetch(`/api/catalog/${CATALOG_TYPE}/${PARENT_ID}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();

        if (!res.ok) throw new Error(result.error || 'Error al guardar');

        showToast('Éxito', result.message);
        dom.parentModal.classList.remove('active');

        // Reload page to update parent name in UI
        setTimeout(() => location.reload(), 1000);

    } catch (err) {
        showToast('Error', err.message, 'error');
    }
}

// ==========================================
// Utils & Helpers
// ==========================================

function updateTableUI() {
    if (state.loading) {
        dom.childTableBody.innerHTML = '';
        dom.loadingState.classList.remove('hidden');
        dom.emptyState.classList.add('hidden');
    } else {
        dom.loadingState.classList.add('hidden');
    }
}

function updateStats(total) {
    dom.childStats.textContent = `${total || 0} registros`;
    dom.paginationInfo.textContent = `Página ${state.page}`;
}

function updatePagination(hasMore) {
    dom.prevBtn.disabled = state.page === 1;
    dom.nextBtn.disabled = !hasMore && (state.items.length < state.pageSize);
}

function changePage(delta) {
    const newPage = state.page + delta;
    if (newPage < 1) return;
    state.page = newPage;
    fetchData();
}

function handleSearch(e) {
    state.search = e.target.value.trim();
    state.page = 1;
    fetchData();
}

function handleShowInactive(e) {
    state.showInactive = e.target.checked;
    state.page = 1;
    fetchData();
}

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Toast Notification
function showToast(title, message, type = 'success') {
    if (typeof window.showToast === 'function') {
        window.showToast(title, message, type);
    } else {
        alert(`${title}: ${message}`);
    }
}
