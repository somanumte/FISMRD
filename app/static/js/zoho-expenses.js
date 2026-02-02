/**
 * Zoho Expenses Module
 * Handles API interaction, Chart.js rendering, and UI updates
 */

document.addEventListener('DOMContentLoaded', () => {
    initExpensesModule();
});

let charts = {
    daily: null,
    categories: null
};

let state = {
    page: 1,
    per_page: 10,
    filters: {
        search: '',
        status: 'all',
        category_id: 'all'
    }
};

async function initExpensesModule() {
    await loadCategories();
    loadDashboardData();
    loadExpenses();
    setupEventListeners();
}

function setupEventListeners() {
    // Filters
    document.getElementById('searchInput').addEventListener('input', debounce((e) => {
        state.filters.search = e.target.value;
        state.page = 1;
        loadExpenses();
    }, 500));

    document.getElementById('statusFilter').addEventListener('change', (e) => {
        state.filters.status = e.target.value;
        state.page = 1;
        loadExpenses();
    });

    document.getElementById('categoryFilter').addEventListener('change', (e) => {
        state.filters.category_id = e.target.value;
        state.page = 1;
        loadExpenses();
    });

    // Pagination
    document.getElementById('prevPageBtn').addEventListener('click', () => {
        if (state.page > 1) {
            state.page--;
            loadExpenses();
        }
    });

    document.getElementById('nextPageBtn').addEventListener('click', () => {
        state.page++;
        loadExpenses();
    });

    // Form
    document.getElementById('expenseForm').addEventListener('submit', handleFormSubmit);
}

// --- API Calls & Data Loading ---

async function loadCategories() {
    try {
        const response = await fetch('/expenses/api/categories');
        const categories = await response.json();

        // Populate filters and modal select
        const filterSelect = document.getElementById('categoryFilter');
        const modalSelect = document.getElementById('modalCategorySelect');

        // Keep "All" option in filter
        filterSelect.innerHTML = '<option value="all">Todas las categorías</option>';
        modalSelect.innerHTML = '<option value="">Seleccionar...</option>';

        categories.forEach(cat => {
            const option = `<option value="${cat.id}">${cat.name}</option>`;
            filterSelect.innerHTML += option;
            modalSelect.innerHTML += option;
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadDashboardData() {
    try {
        const response = await fetch('/expenses/api/dashboard');
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        // Update KPI Cards
        updateKPI('kpi-total-month', data.kpi.total_month, true);
        updateKPI('kpi-pending-month', data.kpi.pending_month, true);
        updateKPI('kpi-overdue-total', data.kpi.overdue_total, true);
        updateKPI('kpi-upcoming-count', data.kpi.upcoming_count, false);

        // Render Charts
        renderDailyChart(data.charts.daily);
        renderCategoryChart(data.charts.categories);

    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadExpenses() {
    const query = new URLSearchParams({
        page: state.page,
        per_page: state.per_page,
        search: state.filters.search,
        status: state.filters.status,
        category_id: state.filters.category_id
    });

    try {
        console.log('Fetching expenses with query:', query.toString());
        const response = await fetch(`/expenses/api/list?${query}`);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        console.log('Expenses data received:', data);

        if (data.error) {
            throw new Error(data.error);
        }

        renderTable(data.expenses);
        updatePagination(data);

    } catch (error) {
        console.error('Error loading list:', error);
        const tbody = document.getElementById('expensesTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="p-4 text-center text-red-600 bg-red-50">
                        <p class="font-bold">Error al cargar gastos</p>
                        <p class="text-sm">${error.message}</p>
                        <button onclick="loadExpenses()" class="mt-2 text-blue-600 underline text-sm">Intentar de nuevo</button>
                    </td>
                </tr>
            `;
        }
    }
}

// --- Rendering ---

function updateKPI(elementId, value, isCurrency) {
    const el = document.getElementById(elementId);
    if (!el) return;

    if (isCurrency) {
        el.textContent = new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP' }).format(value);
    } else {
        el.textContent = value;
    }
}

function renderTable(expenses) {
    const tbody = document.getElementById('expensesTableBody');
    tbody.innerHTML = '';

    if (expenses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-gray-500">No se encontraron gastos.</td></tr>`;
        return;
    }

    expenses.forEach(expense => {
        const tr = document.createElement('tr');
        tr.className = 'border-b hover:bg-gray-50 transition-colors';

        // Status logic
        let statusBadge = '';
        if (expense.is_paid) {
            statusBadge = `<span class="zoho-badge status-paid">Pagado</span>`;
        } else if (expense.is_overdue) {
            statusBadge = `<span class="zoho-badge status-overdue">Vencido</span>`;
        } else {
            statusBadge = `<span class="zoho-badge status-pending">Pendiente</span>`;
        }

        const amount = new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP' }).format(expense.amount);
        const dateStr = new Date(expense.due_date).toLocaleDateString();

        tr.innerHTML = `
            <td class="p-4 font-medium text-gray-900">${expense.description}
                ${expense.is_recurring ? '<span class="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">Recurrente</span>' : ''}
            </td>
            <td class="p-4 text-gray-600">${expense.category.name || '-'}</td>
            <td class="p-4 text-gray-600">${dateStr}</td>
            <td class="p-4 font-bold text-gray-800">${amount}</td>
            <td class="p-4">${statusBadge}</td>
            <td class="p-4 text-right">
                <div class="flex justify-end gap-2">
                    <button onclick="toggleStatus(${expense.id})" title="${expense.is_paid ? 'Marcar como pendiente' : 'Marcar como pagado'}"
                            class="p-1 rounded hover:bg-gray-200 text-gray-600">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            ${expense.is_paid
                ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>'
                : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>'}
                        </svg>
                    </button>
                    <button onclick="editExpense(${expense.id})" class="p-1 rounded hover:bg-gray-200 text-blue-600">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                        </svg>
                    </button>
                    <button onclick="deleteExpense(${expense.id})" class="p-1 rounded hover:bg-gray-200 text-red-600">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updatePagination(data) {
    document.getElementById('pageInfo').textContent = `Página ${data.current_page} de ${data.pages || 1}`;
    document.getElementById('prevPageBtn').disabled = data.current_page <= 1;
    document.getElementById('nextPageBtn').disabled = data.current_page >= data.pages;
}

// --- Charts ---

function renderDailyChart(data) {
    const ctx = document.getElementById('dailyExpensesChart').getContext('2d');

    if (charts.daily) charts.daily.destroy();

    charts.daily = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Gastos Diarios',
                data: data.data,
                borderColor: '#2D64B3',
                backgroundColor: 'rgba(45, 100, 179, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, grid: { borderDash: [5, 5] } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');

    if (charts.categories) charts.categories.destroy();

    charts.categories = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                data: data.map(item => item.value),
                backgroundColor: data.map(item => item.color),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' }
            },
            cutout: '70%'
        }
    });
}

// --- Modal & Actions ---

function openModal() {
    document.getElementById('expenseModal').classList.remove('hidden');
    document.getElementById('expenseForm').reset();
    document.getElementById('expenseId').value = '';
    document.getElementById('modalTitle').textContent = 'Nuevo Gasto';
    document.getElementById('recurringOptions').classList.add('hidden');
    // Set default date to today
    document.querySelector('input[name="due_date"]').valueAsDate = new Date();
}

function closeModal() {
    document.getElementById('expenseModal').classList.add('hidden');
}

function toggleRecurringOptions() {
    const isRecurring = document.getElementById('checkIsRecurring').checked;
    const options = document.getElementById('recurringOptions');
    if (isRecurring) {
        options.classList.remove('hidden');
    } else {
        options.classList.add('hidden');
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);

    // Prepare payload
    const payload = {
        description: data.description,
        amount: data.amount,
        category_id: data.category_id,
        due_date: data.due_date,
        is_paid: !!data.is_paid,
        is_recurring: !!data.is_recurring,
        notes: data.notes
    };

    if (payload.is_recurring) {
        payload.frequency = data.frequency;
        payload.auto_renew = !!data.auto_renew;
    }

    const id = document.getElementById('expenseId').value;
    const url = id ? `/expenses/api/${id}` : '/expenses/api/create';
    const method = id ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.success) {
            closeModal();
            loadDashboardData();
            loadExpenses();
            // Optional: show toast
        } else {
            alert(result.error || 'Error al guardar');
        }
    } catch (error) {
        console.error('Error saving expense:', error);
    }
}

async function editExpense(id) {
    // We could fetch details from server, or pass data. Fetch is safer.
    try {
        // Since we don't have a specific `get_one` easily accessible without hitting the list, we can just grab it from a new fetch or add a get endpoint.
        // We added /api/expenses/<id> in valid routes, let's use it? No, we didn't add a specific GET /api/expenses/<id> in the final rewrite, 
        // wait, I checked the python file.
        // Actually, looking at the python file rewrite, I removed the individual GET endpoint in favor of cleaning up. 
        // Just kidding, I might have missed it or not included it. 
        // Let's check `api_list_expenses`... 

        // Strategy: To avoid adding more endpoints if not needed, we can just filter from state if we have the full object, 
        // OR simpler: just re-implement GET /api/<id> if I missed it, OR render it into the row data-attributes. 

        // Actually, I should probably add the GET endpoint back if I want to edit cleanly. 
        // But for now, let's just cheat and assume we might not need a server trip if the data is simple.
        // However, robust way: Add GET endpoint. 
        // Let's double check the python file I wrote.

        // I wrote: @bp.route('/api/<int:expense_id>', methods=['PUT', 'DELETE'])
        // I did NOT write a GET for single ID.
        // Use a quick hack: fetch list again or just iterate current list in JS memory.

        // Currently displayed expenses are in memory? No, I strictly render them. 
        // I will add a `expenses` array to state to look them up.

        // Wait, I can't easily edit without data. 
        // I'll update `state` to hold current expenses list.
        alert('Edit functionality requires reloading... please implement global state for expenses or add GET endpoint.');

        // Fixing this on the fly:
        // Updating `renderTable` to store data in a global map
    } catch (e) {
        console.error(e);
    }
}

// Patching editExpense to work with local data for now
let currentExpensesCache = [];

// Override renderTable to cache data
const originalRenderTable = renderTable;
renderTable = function (expenses) {
    currentExpensesCache = expenses;
    originalRenderTable(expenses);
}

// Real edit implementation
editExpense = function (id) {
    const expense = currentExpensesCache.find(e => e.id === id);
    if (!expense) return;

    openModal();
    document.getElementById('modalTitle').textContent = 'Editar Gasto';
    document.getElementById('expenseId').value = expense.id;

    const form = document.getElementById('expenseForm');
    form.querySelector('[name="description"]').value = expense.description;
    form.querySelector('[name="amount"]').value = expense.amount;
    form.querySelector('[name="category_id"]').value = expense.category_id;

    // Date format YYYY-MM-DD
    const dateVal = new Date(expense.due_date).toISOString().split('T')[0];
    form.querySelector('[name="due_date"]').value = dateVal;

    form.querySelector('[name="is_paid"]').checked = expense.is_paid;
    form.querySelector('[name="notes"]').value = expense.notes || '';

    const isRecur = expense.is_recurring;
    const recurCheck = form.querySelector('[name="is_recurring"]');
    recurCheck.checked = isRecur;

    toggleRecurringOptions();
    if (isRecur) {
        form.querySelector('[name="frequency"]').value = expense.frequency;
        form.querySelector('[name="auto_renew"]').checked = expense.auto_renew;
    }
}


async function deleteExpense(id) {
    if (!confirm('¿Seguro que deseas eliminar este gasto?')) return;

    try {
        const response = await fetch(`/expenses/api/${id}`, { method: 'DELETE' });
        const result = await response.json();

        if (result.success) {
            loadDashboardData();
            loadExpenses();
        } else {
            alert('Error al eliminar');
        }
    } catch (error) {
        console.error(error);
    }
}

async function toggleStatus(id) {
    try {
        const response = await fetch(`/expenses/api/${id}/toggle-status`, { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            loadDashboardData();
            loadExpenses();
        }
    } catch (error) {
        console.error(error);
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
