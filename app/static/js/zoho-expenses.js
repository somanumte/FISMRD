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
        category_id: 'all',
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
        is_recurring: 'all'
    }
};

async function initExpensesModule() {
    initPeriodFilters();
    await loadCategories();
    await syncRecurringExpenses();
    loadDashboardData();
    loadExpenses();
    setupEventListeners();
}

function initPeriodFilters() {
    const monthSelect = document.getElementById('monthFilter');
    const yearSelect = document.getElementById('yearFilter');

    // Set current month
    monthSelect.value = state.filters.month;

    // Populate years (2 before, up to 2 after)
    const currentYear = new Date().getFullYear();
    yearSelect.innerHTML = '';
    for (let y = currentYear - 2; y <= currentYear + 2; y++) {
        const option = document.createElement('option');
        option.value = y;
        option.textContent = y;
        if (y === state.filters.year) option.selected = true;
        yearSelect.appendChild(option);
    }
}

async function syncRecurringExpenses() {
    const query = new URLSearchParams({
        month: state.filters.month,
        year: state.filters.year
    });
    try {
        const response = await fetch(`/expenses/api/sync-recurring?${query}`, { method: 'POST' });
        const result = await response.json();
        if (result.created_count > 0) {
            console.log('Gastos recurrentes sincronizados:', result.message);
        }
    } catch (error) {
        console.error('Error sincronizando gastos recurrentes:', error);
    }
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

    document.getElementById('monthFilter').addEventListener('change', async (e) => {
        state.filters.month = parseInt(e.target.value);
        state.page = 1;
        await syncRecurringExpenses();
        loadDashboardData();
        loadExpenses();
    });

    document.getElementById('yearFilter').addEventListener('change', async (e) => {
        state.filters.year = parseInt(e.target.value);
        state.page = 1;
        await syncRecurringExpenses();
        loadDashboardData();
        loadExpenses();
    });

    document.getElementById('recurringFilter').addEventListener('change', (e) => {
        state.filters.is_recurring = e.target.value;
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
    const query = new URLSearchParams({
        month: state.filters.month,
        year: state.filters.year
    });
    try {
        const response = await fetch(`/expenses/api/dashboard?${query}`);
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
        category_id: state.filters.category_id,
        month: state.filters.month,
        year: state.filters.year,
        is_recurring: state.filters.is_recurring
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
        const formatted = new Intl.NumberFormat('es-DO', {
            style: 'currency',
            currency: 'DOP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
        el.textContent = formatted;
    } else {
        el.textContent = value;
    }
}

function renderTable(expenses) {
    const tbody = document.getElementById('expensesTableBody');
    const mobileContainer = document.getElementById('expensesMobileCards');

    tbody.innerHTML = '';
    mobileContainer.innerHTML = '';

    if (expenses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-12 text-center text-slate-400 font-bold">No se encontraron registros en este periodo.</td></tr>`;
        mobileContainer.innerHTML = `<div class="p-12 text-center text-slate-400 font-bold">Sin registros.</div>`;
        return;
    }

    expenses.forEach(expense => {
        // --- Desktop Row ---
        const tr = document.createElement('tr');
        tr.className = 'border-b dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group';

        let statusClass = '';
        let statusText = '';
        if (expense.is_paid) {
            statusClass = 'status-paid';
            statusText = 'Pagado';
        } else if (expense.is_overdue) {
            statusClass = 'status-overdue';
            statusText = 'Vencido';
        } else {
            statusClass = 'status-pending';
            statusText = 'Pendiente';
        }

        const amount = new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP' }).format(expense.amount);
        const dateStr = new Date(expense.due_date).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });

        tr.innerHTML = `
            <td class="px-6 py-4 font-bold text-slate-900 dark:text-white">
                <div class="flex flex-col">
                    <span>${expense.description}</span>
                    ${expense.is_recurring ? '<span class="text-[9px] uppercase tracking-tighter text-blue-500 font-black">Recurrente</span>' : ''}
                </div>
            </td>
            <td class="px-6 py-4">
                <span class="text-xs font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-lg">${expense.category.name || '-'}</span>
            </td>
            <td class="px-6 py-4 text-slate-600 dark:text-slate-400 font-medium">${dateStr}</td>
            <td class="px-6 py-4 font-black text-slate-900 dark:text-white">${amount}</td>
            <td class="px-6 py-4"><span class="zoho-badge ${statusClass}">${statusText}</span></td>
            <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="toggleStatus(${expense.id})" class="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            ${expense.is_paid ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path>' : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path>'}
                        </svg>
                    </button>
                    <button onclick="editExpense(${expense.id})" class="p-2 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                    </button>
                    <button onclick="deleteExpense(${expense.id})" class="p-2 rounded-lg hover:bg-rose-100 dark:hover:bg-rose-900/30 text-rose-600 dark:text-rose-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);

        // --- Mobile Cards ---
        const card = document.createElement('div');
        card.className = 'metric-card !p-4 flex flex-col gap-3 relative';
        card.innerHTML = `
            <div class="flex justify-between items-start">
                <div class="flex flex-col">
                    <span class="text-xs font-black uppercase text-slate-400 tracking-tighter mb-1">${expense.category.name || 'General'}</span>
                    <span class="text-lg font-black dark:text-white leading-tight">${expense.description}</span>
                </div>
                <span class="zoho-badge ${statusClass} scale-90 translate-x-2 -translate-y-1">${statusText}</span>
            </div>
            
            <div class="flex justify-between items-end border-t border-slate-100 dark:border-slate-800 pt-3 mt-1">
                <div class="flex flex-col">
                    <span class="text-[10px] font-bold text-slate-400 uppercase">Vence</span>
                    <span class="text-sm font-black dark:text-slate-300">${dateStr}</span>
                </div>
                <div class="flex flex-col items-end">
                    <span class="text-[10px] font-bold text-slate-400 uppercase">Total</span>
                    <span class="text-xl font-black text-slate-900 dark:text-white">${amount}</span>
                </div>
            </div>

            <div class="flex gap-2 mt-2">
                <button onclick="toggleStatus(${expense.id})" class="flex-1 py-2 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs font-bold dark:text-white">
                    ${expense.is_paid ? 'Pendiente' : 'Pagar'}
                </button>
                <button onclick="editExpense(${expense.id})" class="p-2 bg-blue-50 dark:bg-blue-900/20 text-blue-600 rounded-xl">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                </button>
                <button onclick="deleteExpense(${expense.id})" class="p-2 bg-rose-50 dark:bg-rose-900/20 text-rose-600 rounded-xl">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
            </div>
        `;
        mobileContainer.appendChild(card);
    });
}

function updatePagination(data) {
    document.getElementById('pageInfo').textContent = `Página ${data.current_page} de ${data.pages || 1}`;
    document.getElementById('prevPageBtn').disabled = data.current_page <= 1;
    document.getElementById('nextPageBtn').disabled = data.current_page >= data.pages;
}

// --- Charts ---

// Watch for theme changes to re-render charts
const themeObserver = new MutationObserver(() => {
    if (charts.daily || charts.categories) {
        loadDashboardData();
    }
});
themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

function renderDailyChart(data) {
    const ctx = document.getElementById('dailyExpensesChart').getContext('2d');
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#ffffff' : '#1e293b';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';

    if (charts.daily) charts.daily.destroy();

    charts.daily = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Gastos Diarios',
                data: data.data,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 0,
                pointHoverRadius: 6,
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#fff',
                    titleColor: isDark ? '#ffffff' : '#1e293b',
                    bodyColor: isDark ? '#ffffff' : '#1e293b',
                    borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { weight: 'bold', size: 10 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: textColor, font: { weight: 'bold', size: 10 } }
                }
            }
        }
    });
}

function renderCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#ffffff' : '#1e293b';

    if (charts.categories) charts.categories.destroy();

    charts.categories = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.name),
            datasets: [{
                data: data.map(item => item.value),
                backgroundColor: data.map(item => item.color),
                borderWidth: isDark ? 4 : 2,
                borderColor: isDark ? '#1e293b' : '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: textColor,
                        padding: 15,
                        font: { size: 12, weight: 'bold' },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                }
            },
            cutout: '75%'
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

function toggleFilters() {
    const sidebar = document.getElementById('filters-sidebar');
    const overlay = document.getElementById('filters-overlay');
    if (!sidebar || !overlay) return;

    const isOpen = !sidebar.classList.contains('-translate-x-full');

    if (isOpen) {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden', 'opacity-0');
        document.body.style.overflow = '';
    } else {
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
        setTimeout(() => overlay.classList.remove('opacity-0'), 10);
        document.body.style.overflow = 'hidden';
    }
}
