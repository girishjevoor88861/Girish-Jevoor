/**
 * CivicAI - Field Officer Portal Controller
 * Workload metrics, task dispatch queue, on-site action execution, before/after evidence upload, and resolution completion.
 */

window.OfficerController = {
  currentTab: 'assigned', // 'assigned', 'in_progress', 'critical', 'completed'
  tasksData: null,

  async load() {
    await this.fetchOfficerTasks();
  },

  async fetchOfficerTasks() {
    try {
      const res = await window.CivicAI.apiFetch('/officers/me/tasks');
      if (!res.success) return;
      this.tasksData = res;

      const s = res.stats;
      document.getElementById('off-stat-total').innerText = s.total_assigned;
      document.getElementById('off-stat-pending').innerText = s.pending_acceptance;
      document.getElementById('off-stat-progress').innerText = s.in_progress;
      document.getElementById('off-stat-critical').innerText = s.critical;
      document.getElementById('off-stat-completed').innerText = s.completed;

      const offName = document.getElementById('off-profile-name');
      const offBadge = document.getElementById('off-profile-badge');
      if (offName && res.officer) offName.innerText = `Officer ${res.officer.rank || 'Inspector'}`;
      if (offBadge && res.officer) offBadge.innerText = `Badge: ${res.officer.badge_number}`;

      this.renderTasks(this.currentTab);
    } catch (e) {
      console.error('Error fetching officer tasks:', e);
    }
  },

  switchTab(tab) {
    this.currentTab = tab;
    document.querySelectorAll('.officer-tab-btn').forEach(btn => {
      btn.classList.remove('bg-cyan-500/20', 'text-cyan-400', 'border-cyan-500/40');
      btn.classList.add('text-slate-400', 'border-transparent');
    });
    const active = document.getElementById(`off-tab-btn-${tab}`);
    if (active) {
      active.classList.add('bg-cyan-500/20', 'text-cyan-400', 'border-cyan-500/40');
      active.classList.remove('text-slate-400', 'border-transparent');
    }
    this.renderTasks(tab);
  },

  renderTasks(tab) {
    if (!this.tasksData) return;
    const list = this.tasksData.tasks[tab] || [];
    const container = document.getElementById('officer-tasks-container');
    if (!container) return;

    if (list.length === 0) {
      container.innerHTML = `
        <div class="py-16 text-center text-slate-400 glass-panel rounded-2xl col-span-full">
          <div class="text-4xl mb-2">🎉</div>
          <h4 class="text-base font-bold text-slate-200">No tasks in '${tab.replace('_', ' ')}'</h4>
          <p class="text-xs text-slate-400 mt-1">All work items up to date or assigned to other crews.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = list.map(t => `
      <div class="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-cyan-500/40 transition-all flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between gap-2 mb-3">
            <span class="font-mono text-xs font-bold text-cyan-400 bg-cyan-950 px-2.5 py-1 rounded border border-cyan-800">
              ${t.tracking_id}
            </span>
            <span class="px-2 py-0.5 rounded-full text-xs font-semibold badge-priority-${t.priority}">
              ${t.priority.toUpperCase()}
            </span>
          </div>
          <h4 class="font-bold text-slate-100 text-base mb-1">${t.title}</h4>
          <p class="text-xs text-slate-400 mb-3 line-clamp-2">${t.description}</p>
          <div class="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 text-xs text-slate-300 mb-4">
            <div class="text-slate-400 text-[11px] mb-0.5">Location & Landmark:</div>
            <div class="font-medium">${t.address || 'Downtown'} (${t.ward || ''})</div>
          </div>
        </div>

        <div class="space-y-2 pt-3 border-t border-slate-800">
          ${t.status === 'assigned' ? `
            <button onclick="OfficerController.acceptAssignment(${t.id})" class="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-md transition-all">
              Accept Assignment & Dispatch Crew &rarr;
            </button>
          ` : ''}

          ${t.status === 'in_progress' ? `
            <div class="flex gap-2">
              <button onclick="OfficerController.openEvidenceModal(${t.id}, '${t.tracking_id}', '${t.title.replace(/'/g, "\\'")}')" class="flex-1 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-all">
                Submit Resolution Evidence & Finish
              </button>
            </div>
          ` : ''}

          <div class="flex gap-2">
            <button onclick="CitizenController.openDetailsModal('${t.tracking_id}')" class="flex-1 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium">
              View Details
            </button>
            <button onclick="OfficerController.addProgressNote(${t.id})" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium">
              Add Note
            </button>
          </div>
        </div>
      </div>
    `).join('');
  },

  async acceptAssignment(complaintId) {
    try {
      const res = await window.CivicAI.apiFetch(`/complaints/${complaintId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({
          status: 'in_progress',
          explanation: 'Officer arrived on-site and initiated active remediation work.'
        })
      });
      if (res.success) {
        window.CivicAI.toast('Assignment accepted! Status updated to In Progress.', 'success');
        await this.fetchOfficerTasks();
        this.switchTab('in_progress');
      }
    } catch (e) {
      window.CivicAI.toast(`Action failed: ${e.message}`, 'error');
    }
  },

  async addProgressNote(complaintId) {
    const note = prompt('Enter on-site field progress note:');
    if (!note || !note.trim()) return;

    try {
      const res = await window.CivicAI.apiFetch(`/complaints/${complaintId}/notes`, {
        method: 'POST',
        body: JSON.stringify({ note_text: note.trim() })
      });
      if (res.success) {
        window.CivicAI.toast('Field note added to record', 'success');
      }
    } catch (e) {
      window.CivicAI.toast(`Failed to add note: ${e.message}`, 'error');
    }
  },

  openEvidenceModal(complaintId, trackingId, title) {
    const modal = document.getElementById('officer-evidence-modal');
    if (!modal) return;

    document.getElementById('evidence-target-id').value = complaintId;
    document.getElementById('evidence-target-tracking').innerText = trackingId;
    document.getElementById('evidence-target-title').innerText = title;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
  },

  async submitEvidence() {
    const complaintId = document.getElementById('evidence-target-id').value;
    const summary = document.getElementById('evidence-summary').value.trim();
    const equipment = document.getElementById('evidence-equipment').value.trim();
    const laborHours = parseFloat(document.getElementById('evidence-hours').value) || 2.5;

    if (!summary) {
      window.CivicAI.toast('Please provide a resolution summary', 'warning');
      return;
    }

    try {
      const res = await window.CivicAI.apiFetch('/officers/evidence', {
        method: 'POST',
        body: JSON.stringify({
          complaint_id: complaintId,
          resolution_summary: summary,
          equipment_used: equipment || 'Standard departmental repair equipment',
          labor_hours: laborHours,
          before_image_url: '/uploads/before_work.svg',
          after_image_url: '/uploads/after_work.svg'
        })
      });

      if (res.success) {
        window.CivicAI.toast('Resolution evidence saved! Complaint marked as Resolved.', 'success');
        window.CivicAI.closeModal('officer-evidence-modal');
        await this.fetchOfficerTasks();
        this.switchTab('completed');
      }
    } catch (e) {
      window.CivicAI.toast(`Evidence submission failed: ${e.message}`, 'error');
    }
  }
};
