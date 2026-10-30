/**
 * CivicAI - Municipal Administration Portal Controller
 * Controls KPI metrics, Chart.js analytics, Complaint Management table,
 * bulk assignments, duplicate review drawer, priority overrides, and department management.
 */

window.AdminController = {
  charts: {},
  tableFilters: {
    category: 'all',
    status: 'all',
    priority: 'all',
    department_id: 'all',
    search: '',
    sort_by: 'created_at',
    sort_order: 'desc',
    page: 1,
    limit: 10
  },
  selectedComplaints: new Set(),

  async load() {
    await this.fetchAdminKPIs();
    await this.loadCharts(30);
    await this.loadComplaintsTable();
    await this.loadDepartments();
    await this.loadActivityFeed();
  },

  async fetchAdminKPIs() {
    try {
      const res = await window.CivicAI.apiFetch('/analytics/kpis');
      if (!res.success) return;
      const d = res.data;

      document.getElementById('admin-kpi-total').innerText = d.total_reports;
      document.getElementById('admin-kpi-today').innerText = d.new_reports_today;
      document.getElementById('admin-kpi-pending').innerText = d.pending_reports;
      document.getElementById('admin-kpi-critical').innerText = d.critical_reports;
      document.getElementById('admin-kpi-active').innerText = d.active_assignments;
      document.getElementById('admin-kpi-resolved').innerText = d.resolved_reports;
      document.getElementById('admin-kpi-rate').innerText = `${d.resolution_rate_pct}%`;
      document.getElementById('admin-kpi-avg-time').innerText = `${d.average_resolution_hours}h`;
    } catch (e) {
      console.error('Error fetching admin KPIs:', e);
    }
  },

  async loadCharts(days = 30) {
    try {
      const res = await window.CivicAI.apiFetch(`/analytics/charts?days=${days}`);
      if (!res.success) return;
      const data = res.data;

      // 1. Category Chart (Doughnut)
      const catCtx = document.getElementById('chart-category')?.getContext('2d');
      if (catCtx) {
        if (this.charts.category) this.charts.category.destroy();
        this.charts.category = new Chart(catCtx, {
          type: 'doughnut',
          data: {
            labels: data.by_category.map(c => c.name),
            datasets: [{
              data: data.by_category.map(c => c.value),
              backgroundColor: ['#00b4d8', '#0077b6', '#06d6a0', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'],
              borderColor: '#131d35',
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 12, font: { size: 10 } } }
            }
          }
        });
      }

      // 2. Priority Chart (Bar)
      const prioCtx = document.getElementById('chart-priority')?.getContext('2d');
      if (prioCtx) {
        if (this.charts.priority) this.charts.priority.destroy();
        const prioOrder = ['critical', 'high', 'medium', 'low'];
        const prioMap = Object.fromEntries(data.by_priority.map(p => [p.priority, p.count]));
        
        this.charts.priority = new Chart(prioCtx, {
          type: 'bar',
          data: {
            labels: ['Critical', 'High', 'Medium', 'Low'],
            datasets: [{
              label: 'Complaints',
              data: prioOrder.map(p => prioMap[p] || 0),
              backgroundColor: ['#ef4444', '#f97316', '#eab308', '#10b981'],
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
              y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
          }
        });
      }

      // 3. Weekly Trends (Line)
      const trendCtx = document.getElementById('chart-trends')?.getContext('2d');
      if (trendCtx) {
        if (this.charts.trends) this.charts.trends.destroy();
        this.charts.trends = new Chart(trendCtx, {
          type: 'line',
          data: {
            labels: data.weekly_trends.map(t => t.week),
            datasets: [{
              label: 'Reports Filed',
              data: data.weekly_trends.map(t => t.reports),
              borderColor: '#00b4d8',
              backgroundColor: 'rgba(0, 180, 216, 0.1)',
              fill: true,
              tension: 0.35,
              borderWidth: 3,
              pointBackgroundColor: '#38bdf8'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
              y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
          }
        });
      }

      // 4. Department Performance (Horizontal Bar)
      const deptCtx = document.getElementById('chart-department')?.getContext('2d');
      if (deptCtx) {
        if (this.charts.department) this.charts.department.destroy();
        this.charts.department = new Chart(deptCtx, {
          type: 'bar',
          data: {
            labels: data.department_performance.map(d => d.code),
            datasets: [
              {
                label: 'Total Received',
                data: data.department_performance.map(d => d.total),
                backgroundColor: '#334155',
                borderRadius: 4
              },
              {
                label: 'Resolved',
                data: data.department_performance.map(d => d.resolved),
                backgroundColor: '#10b981',
                borderRadius: 4
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 } } }
            },
            scales: {
              x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
              y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
          }
        });
      }
    } catch (e) {
      console.error('Error loading charts:', e);
    }
  },

  // -------------------------------------------------------------
  // Complaint Management Table
  // -------------------------------------------------------------
  async loadComplaintsTable() {
    const f = this.tableFilters;
    let url = `/complaints?page=${f.page}&limit=${f.limit}&sort_by=${f.sort_by}&sort_order=${f.sort_order}`;
    if (f.category !== 'all') url += `&category=${encodeURIComponent(f.category)}`;
    if (f.status !== 'all') url += `&status=${f.status}`;
    if (f.priority !== 'all') url += `&priority=${f.priority}`;
    if (f.department_id !== 'all') url += `&department_id=${f.department_id}`;
    if (f.search) url += `&search=${encodeURIComponent(f.search)}`;

    try {
      const res = await window.CivicAI.apiFetch(url);
      const tbody = document.getElementById('admin-complaints-tbody');
      const countEl = document.getElementById('admin-table-count');
      const paginationEl = document.getElementById('admin-table-pagination');
      if (!tbody) return;

      if (!res.success || res.data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="py-12 text-center text-slate-400">No complaints matching filter criteria.</td></tr>`;
        if (countEl) countEl.innerText = '0 reports found';
        if (paginationEl) paginationEl.innerHTML = '';
        return;
      }

      if (countEl) countEl.innerText = `${res.pagination.total} total reports`;

      tbody.innerHTML = res.data.map(c => `
        <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors text-xs text-slate-300">
          <td class="py-3 px-3">
            <input type="checkbox" onchange="AdminController.toggleSelectRow(${c.id}, this.checked)" ${this.selectedComplaints.has(c.id) ? 'checked' : ''} class="rounded bg-slate-900 border-slate-700">
          </td>
          <td class="py-3 px-3 font-mono font-bold text-cyan-400 cursor-pointer hover:underline" onclick="CitizenController.openDetailsModal('${c.tracking_id}')">
            ${c.tracking_id}
          </td>
          <td class="py-3 px-3">
            <div class="font-bold text-slate-100 max-w-[180px] truncate" title="${c.title}">${c.title}</div>
            <div class="text-[11px] text-slate-400 truncate max-w-[180px]">${c.category}</div>
          </td>
          <td class="py-3 px-3">
            <div class="truncate max-w-[140px]" title="${c.address || ''}">${c.address || 'Downtown'}</div>
            <div class="text-[10px] text-slate-500">${c.ward || ''}</div>
          </td>
          <td class="py-3 px-3">
            <span class="px-2 py-0.5 rounded-full font-semibold badge-priority-${c.priority}">
              ${c.priority.toUpperCase()}
            </span>
          </td>
          <td class="py-3 px-3">
            <span class="px-2 py-0.5 rounded-full font-semibold badge-status-${c.status}">
              ${c.status.replace('_', ' ').toUpperCase()}
            </span>
          </td>
          <td class="py-3 px-3">
            <div class="font-medium text-slate-200">${c.department_name || 'Unassigned'}</div>
            <div class="text-[10px] text-slate-400">${c.officer_name || 'No Officer'}</div>
          </td>
          <td class="py-3 px-3 text-slate-400">${new Date(c.created_at).toLocaleDateString()}</td>
          <td class="py-3 px-3">
            <div class="flex items-center gap-1.5">
              <button onclick="CitizenController.openDetailsModal('${c.tracking_id}')" title="Details" class="p-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400">
                👁️
              </button>
              <button onclick="AdminController.openAssignModal(${c.id}, '${c.tracking_id}', ${c.department_id || 1})" title="Assign Officer" class="p-1 rounded bg-slate-800 hover:bg-slate-700 text-amber-400">
                👤
              </button>
              <button onclick="AdminController.openPriorityModal(${c.id}, '${c.tracking_id}', '${c.priority}', ${c.total_priority_score || 50})" title="Override Priority" class="p-1 rounded bg-slate-800 hover:bg-slate-700 text-rose-400">
                ⚖️
              </button>
            </div>
          </td>
        </tr>
      `).join('');

      // Render Pagination
      if (paginationEl) {
        const { total_pages, page } = res.pagination;
        paginationEl.innerHTML = `
          <div class="flex items-center justify-between w-full text-xs text-slate-400 mt-3">
            <span>Page ${page} of ${total_pages}</span>
            <div class="flex gap-2">
              <button ${page <= 1 ? 'disabled class="opacity-40 cursor-not-allowed"' : ''} onclick="AdminController.changeTablePage(${page - 1})" class="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200">Prev</button>
              <button ${page >= total_pages ? 'disabled class="opacity-40 cursor-not-allowed"' : ''} onclick="AdminController.changeTablePage(${page + 1})" class="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200">Next</button>
            </div>
          </div>
        `;
      }
    } catch (e) {
      console.error('Error loading complaints table:', e);
    }
  },

  changeTablePage(newPage) {
    this.tableFilters.page = newPage;
    this.loadComplaintsTable();
  },

  applyTableFilters() {
    this.tableFilters.search = document.getElementById('admin-table-search')?.value.trim() || '';
    this.tableFilters.category = document.getElementById('admin-filter-category')?.value || 'all';
    this.tableFilters.status = document.getElementById('admin-filter-status')?.value || 'all';
    this.tableFilters.priority = document.getElementById('admin-filter-priority')?.value || 'all';
    this.tableFilters.department_id = document.getElementById('admin-filter-department')?.value || 'all';
    this.tableFilters.page = 1;
    this.loadComplaintsTable();
  },

  toggleSelectAll(checked) {
    const checkboxes = document.querySelectorAll('#admin-complaints-tbody input[type="checkbox"]');
    checkboxes.forEach(cb => {
      cb.checked = checked;
    });
    // Add all visible IDs
    if (checked) {
      document.querySelectorAll('#admin-complaints-tbody tr').forEach(row => {
        const trk = row.querySelector('.font-mono')?.innerText.trim();
        if (trk) this.selectedComplaints.add(trk);
      });
    } else {
      this.selectedComplaints.clear();
    }
    this.updateBulkActionBar();
  },

  toggleSelectRow(id, checked) {
    if (checked) this.selectedComplaints.add(id);
    else this.selectedComplaints.delete(id);
    this.updateBulkActionBar();
  },

  updateBulkActionBar() {
    const bar = document.getElementById('admin-bulk-bar');
    const countEl = document.getElementById('admin-bulk-count');
    if (!bar) return;

    if (this.selectedComplaints.size > 0) {
      bar.classList.remove('hidden');
      if (countEl) countEl.innerText = `${this.selectedComplaints.size} selected`;
    } else {
      bar.classList.add('hidden');
    }
  },

  exportCSV() {
    window.location.href = '/api/complaints/export/csv';
    window.CivicAI.toast('Generating civic complaints CSV export...', 'info');
  },

  // -------------------------------------------------------------
  // Modals: Assign Officer & Override Priority
  // -------------------------------------------------------------
  async openAssignModal(complaintId, trackingId, currentDeptId) {
    const modal = document.getElementById('admin-assign-modal');
    if (!modal) return;

    document.getElementById('assign-target-id').value = complaintId;
    document.getElementById('assign-target-tracking').innerText = trackingId;

    // Fetch officers for dropdown
    const res = await window.CivicAI.apiFetch('/officers');
    const select = document.getElementById('assign-officer-select');
    if (select && res.success) {
      select.innerHTML = res.data.map(o => `
        <option value="${o.id}">
          ${o.full_name} (${o.badge_number}) • ${o.department_name} • ${o.active_tasks} active
        </option>
      `).join('');
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
  },

  async confirmAssignment() {
    const compId = document.getElementById('assign-target-id').value;
    const officerId = document.getElementById('assign-officer-select').value;
    const notes = document.getElementById('assign-notes').value.trim();

    try {
      const res = await window.CivicAI.apiFetch(`/complaints/${compId}/assign`, {
        method: 'PATCH',
        body: JSON.stringify({ officer_id: officerId, notes })
      });
      if (res.success) {
        window.CivicAI.toast(res.message, 'success');
        window.CivicAI.closeModal('admin-assign-modal');
        await this.loadComplaintsTable();
        await this.fetchAdminKPIs();
      }
    } catch (e) {
      window.CivicAI.toast(`Assignment error: ${e.message}`, 'error');
    }
  },

  openPriorityModal(complaintId, trackingId, currPriority, currScore) {
    const modal = document.getElementById('admin-priority-modal');
    if (!modal) return;

    document.getElementById('priority-target-id').value = complaintId;
    document.getElementById('priority-target-tracking').innerText = trackingId;
    document.getElementById('priority-select').value = currPriority;
    document.getElementById('priority-score-input').value = currScore;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
  },

  async confirmPriorityOverride() {
    const compId = document.getElementById('priority-target-id').value;
    const priority = document.getElementById('priority-select').value;
    const priorityScore = parseFloat(document.getElementById('priority-score-input').value);
    const reason = document.getElementById('priority-reason').value.trim();

    try {
      const res = await window.CivicAI.apiFetch(`/complaints/${compId}/priority`, {
        method: 'PATCH',
        body: JSON.stringify({ priority, priority_score: priorityScore, reason })
      });
      if (res.success) {
        window.CivicAI.toast('Priority successfully updated', 'success');
        window.CivicAI.closeModal('admin-priority-modal');
        await this.loadComplaintsTable();
        await this.fetchAdminKPIs();
      }
    } catch (e) {
      window.CivicAI.toast(`Priority error: ${e.message}`, 'error');
    }
  },

  // -------------------------------------------------------------
  // Department Management
  // -------------------------------------------------------------
  async loadDepartments() {
    try {
      const res = await window.CivicAI.apiFetch('/departments');
      const container = document.getElementById('admin-departments-grid');
      const deptFilter = document.getElementById('admin-filter-department');
      if (!res.success) return;

      if (deptFilter) {
        deptFilter.innerHTML = '<option value="all">All Departments</option>' +
          res.data.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
      }

      if (container) {
        container.innerHTML = res.data.map(d => `
          <div class="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-cyan-500/30 transition-all">
            <div class="flex items-center justify-between mb-3">
              <span class="px-2.5 py-1 rounded-md bg-cyan-950 text-cyan-300 font-mono text-xs font-bold border border-cyan-800">
                ${d.code}
              </span>
              <span class="text-xs text-slate-400">SLA: ${d.sla_hours} hrs</span>
            </div>
            <h4 class="font-bold text-slate-100 text-sm mb-1">${d.name}</h4>
            <p class="text-slate-400 text-xs mb-3 line-clamp-2">${d.description || ''}</p>
            <div class="flex items-center justify-between text-xs pt-3 border-t border-slate-800/80 text-slate-400">
              <span>Active Officers: <strong class="text-slate-200">${d.active_officers_count}</strong></span>
              <span>Resolved: <strong class="text-emerald-400">${d.resolved_complaints || 0}</strong></span>
            </div>
          </div>
        `).join('');
      }
    } catch (e) {
      console.error('Error loading departments:', e);
    }
  },

  // -------------------------------------------------------------
  // Activity Feed
  // -------------------------------------------------------------
  async loadActivityFeed() {
    try {
      const res = await window.CivicAI.apiFetch('/analytics/activity-feed');
      const container = document.getElementById('admin-activity-feed');
      if (!container || !res.success) return;

      container.innerHTML = res.data.map(a => `
        <div class="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start gap-3 text-xs">
          <div class="w-2 h-2 rounded-full bg-cyan-400 mt-1.5 flex-shrink-0"></div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <span class="font-bold text-slate-200">${a.tracking_id}</span>
              <span class="text-[10px] text-slate-500">${new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <p class="text-slate-400 mt-0.5">${a.explanation || a.new_status}</p>
            <span class="text-[10px] text-cyan-400/80">${a.user_name} (${a.user_role})</span>
          </div>
        </div>
      `).join('');
    } catch (e) {
      console.error('Error loading activity feed:', e);
    }
  },

  // -------------------------------------------------------------
  // Reset Demo Data
  // -------------------------------------------------------------
  async resetDemoData() {
    if (!confirm('Are you sure you want to reset all records to the pristine factory demo dataset?')) return;
    try {
      window.CivicAI.toast('Resetting civic database to fresh demo state...', 'info');
      const res = await window.CivicAI.apiFetch('/admin/reset-demo', { method: 'POST' });
      if (res.success) {
        window.CivicAI.toast(res.message, 'success');
        await this.load();
        if (window.MapViewController) window.MapViewController.load();
      }
    } catch (e) {
      window.CivicAI.toast(`Reset failed: ${e.message}`, 'error');
    }
  }
};
