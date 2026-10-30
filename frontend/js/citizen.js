/**
 * CivicAI - Citizen Portal Controller
 * Manages citizen dashboard, 3-step report wizard with Leaflet GPS location,
 * My Complaints table/cards, detailed complaint drawer, and feedback submission.
 */

window.CitizenController = {
  currentStep: 1,
  map: null,
  marker: null,
  reportData: {
    title: '',
    description: '',
    category: 'Roads & Infrastructure',
    subcategory: 'Potholes & Surface Damage',
    latitude: 12.971598,
    longitude: 77.594566,
    address: 'Central Civic District, Metro City',
    ward: 'Ward 12 - Downtown',
    images: []
  },
  filters: {
    status: 'all',
    category: 'all',
    priority: 'all',
    search: '',
    page: 1,
    limit: 6
  },

  async load() {
    this.resetReportForm();
    await this.fetchDashboardStats();
    await this.fetchMyComplaints();
  },

  async fetchDashboardStats() {
    try {
      const user = window.CivicAI.currentUser;
      const url = user ? `/complaints?user_id=${user.id}&limit=100` : `/complaints?limit=100`;
      const res = await window.CivicAI.apiFetch(url);
      if (!res.success) return;

      const complaints = res.data;
      const total = complaints.length;
      const pending = complaints.filter(c => ['submitted', 'ai_analyzed', 'under_review'].includes(c.status)).length;
      const inProgress = complaints.filter(c => ['assigned', 'in_progress'].includes(c.status)).length;
      const resolved = complaints.filter(c => ['resolved', 'closed'].includes(c.status)).length;

      document.getElementById('cit-stat-total').innerText = total;
      document.getElementById('cit-stat-pending').innerText = pending;
      document.getElementById('cit-stat-progress').innerText = inProgress;
      document.getElementById('cit-stat-resolved').innerText = resolved;
    } catch (e) {
      console.error('Error loading citizen stats:', e);
    }
  },

  async fetchMyComplaints() {
    try {
      const { status, category, priority, search, page, limit } = this.filters;
      const user = window.CivicAI.currentUser;
      let url = `/complaints?page=${page}&limit=${limit}`;
      if (user) url += `&user_id=${user.id}`;
      if (status !== 'all') url += `&status=${status}`;
      if (category !== 'all') url += `&category=${encodeURIComponent(category)}`;
      if (priority !== 'all') url += `&priority=${priority}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;

      const res = await window.CivicAI.apiFetch(url);
      const container = document.getElementById('citizen-complaints-list');
      const paginationEl = document.getElementById('citizen-complaints-pagination');
      if (!container) return;

      if (!res.success || res.data.length === 0) {
        container.innerHTML = `
          <div class="col-span-full py-16 text-center text-slate-400 glass-panel rounded-2xl">
            <div class="text-4xl mb-3">📋</div>
            <h4 class="text-lg font-bold text-slate-200">No Complaints Found</h4>
            <p class="text-sm mt-1">Try adjusting your filters or submit a new civic issue report.</p>
          </div>
        `;
        if (paginationEl) paginationEl.innerHTML = '';
        return;
      }

      container.innerHTML = res.data.map(c => `
        <div class="glass-panel p-5 rounded-2xl hover:border-cyan-500/40 transition-all flex flex-col justify-between group">
          <div>
            <div class="flex items-center justify-between gap-2 mb-3">
              <span class="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/80 px-2.5 py-1 rounded-md border border-cyan-800">
                ${c.tracking_id}
              </span>
              <span class="px-2 py-0.5 rounded-full text-xs font-semibold badge-status-${c.status}">
                ${c.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <h4 class="font-bold text-slate-100 text-base mb-1 line-clamp-1 group-hover:text-cyan-400 transition-colors">
              ${c.title}
            </h4>
            <p class="text-slate-400 text-xs line-clamp-2 mb-4">${c.description}</p>
          </div>
          <div>
            <div class="flex items-center justify-between text-xs text-slate-400 py-2 border-t border-slate-800/80 mb-3">
              <span class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full ${
                  c.priority === 'critical' ? 'bg-red-500' :
                  c.priority === 'high' ? 'bg-orange-500' :
                  c.priority === 'medium' ? 'bg-yellow-500' : 'bg-emerald-500'
                }"></span>
                <span class="capitalize font-medium text-slate-300">${c.priority} Priority</span>
              </span>
              <span>${new Date(c.created_at).toLocaleDateString()}</span>
            </div>
            <button onclick="CitizenController.openDetailsModal('${c.tracking_id}')" class="w-full py-2 bg-slate-800 hover:bg-cyan-600/20 text-cyan-400 hover:text-cyan-300 border border-slate-700 hover:border-cyan-500/50 rounded-xl text-xs font-bold transition-all">
              View Status & Timeline &rarr;
            </button>
          </div>
        </div>
      `).join('');

      // Pagination
      if (paginationEl) {
        const { total_pages, page } = res.pagination;
        paginationEl.innerHTML = `
          <div class="flex items-center justify-between w-full text-xs text-slate-400">
            <span>Showing page ${page} of ${total_pages} (${res.pagination.total} reports)</span>
            <div class="flex gap-2">
              <button ${page <= 1 ? 'disabled class="opacity-40 cursor-not-allowed"' : ''} onclick="CitizenController.changePage(${page - 1})" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200">Previous</button>
              <button ${page >= total_pages ? 'disabled class="opacity-40 cursor-not-allowed"' : ''} onclick="CitizenController.changePage(${page + 1})" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200">Next</button>
            </div>
          </div>
        `;
      }
    } catch (e) {
      console.error('Error fetching complaints:', e);
    }
  },

  changePage(newPage) {
    this.filters.page = newPage;
    this.fetchMyComplaints();
  },

  applyFilters() {
    this.filters.search = document.getElementById('cit-search-input')?.value.trim() || '';
    this.filters.category = document.getElementById('cit-cat-filter')?.value || 'all';
    this.filters.status = document.getElementById('cit-status-filter')?.value || 'all';
    this.filters.priority = document.getElementById('cit-priority-filter')?.value || 'all';
    this.filters.page = 1;
    this.fetchMyComplaints();
  },

  // -------------------------------------------------------------
  // Multi-Step Report an Issue Wizard
  // -------------------------------------------------------------
  goToStep(step) {
    if (step === 2) {
      const title = document.getElementById('report-title')?.value.trim();
      const desc = document.getElementById('report-description')?.value.trim();
      if (!title || !desc) {
        window.CivicAI.toast('Please provide a complaint title and detailed description', 'warning');
        return;
      }
      this.reportData.title = title;
      this.reportData.description = desc;
      this.reportData.category = document.getElementById('report-category')?.value;
      this.reportData.subcategory = document.getElementById('report-subcategory')?.value;
    }

    if (step === 3) {
      const address = document.getElementById('report-address')?.value.trim();
      if (address) this.reportData.address = address;
      this.populateReviewStep();
    }

    this.currentStep = step;
    document.querySelectorAll('.report-step-content').forEach(el => el.classList.add('hidden'));
    document.getElementById(`report-step-${step}`)?.classList.remove('hidden');

    // Update wizard step indicators
    for (let i = 1; i <= 3; i++) {
      const circle = document.getElementById(`step-indicator-${i}`);
      if (circle) {
        if (i < step) {
          circle.className = 'w-9 h-9 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center font-bold text-sm';
          circle.innerText = '✓';
        } else if (i === step) {
          circle.className = 'w-9 h-9 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center font-bold text-sm shadow-glow';
          circle.innerText = i;
        } else {
          circle.className = 'w-9 h-9 rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center justify-center font-bold text-sm';
          circle.innerText = i;
        }
      }
    }

    if (step === 2) {
      setTimeout(() => this.initReportMap(), 150);
    }
  },

  initReportMap() {
    const mapContainer = document.getElementById('report-location-map');
    if (!mapContainer) return;

    if (!this.map) {
      this.map = L.map('report-location-map').setView([this.reportData.latitude, this.reportData.longitude], 14);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(this.map);

      this.marker = L.marker([this.reportData.latitude, this.reportData.longitude], { draggable: true }).addTo(this.map);
      
      this.marker.on('dragend', (e) => {
        const pos = e.target.getLatLng();
        this.updateCoords(pos.lat, pos.lng);
      });

      this.map.on('click', (e) => {
        this.marker.setLatLng(e.latlng);
        this.updateCoords(e.latlng.lat, e.latlng.lng);
      });
    } else {
      this.map.invalidateSize();
    }
  },

  updateCoords(lat, lng) {
    this.reportData.latitude = parseFloat(lat.toFixed(6));
    this.reportData.longitude = parseFloat(lng.toFixed(6));
    const coordEl = document.getElementById('report-coords-readout');
    if (coordEl) coordEl.innerText = `GPS: ${this.reportData.latitude}, ${this.reportData.longitude}`;
  },

  detectGpsLocation() {
    if (!navigator.geolocation) {
      window.CivicAI.toast('Geolocation is not supported by your browser', 'error');
      return;
    }
    window.CivicAI.toast('Acquiring precise GPS location...', 'info');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        this.updateCoords(lat, lng);
        if (this.map && this.marker) {
          this.map.setView([lat, lng], 16);
          this.marker.setLatLng([lat, lng]);
        }
        window.CivicAI.toast('GPS location locked!', 'success');
      },
      (err) => {
        window.CivicAI.toast(`Could not access GPS: ${err.message}. Defaulting to city center.`, 'warning');
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  },

  handleImageUpload(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const previewContainer = document.getElementById('report-image-preview');
    if (!previewContainer) return;
    previewContainer.innerHTML = '';
    this.reportData.images = [];

    Array.from(files).slice(0, 3).forEach(file => {
      const reader = new FileReader();
      reader.onload = (loadEvent) => {
        const base64Data = loadEvent.target.result;
        this.reportData.images.push(base64Data);
        const thumb = document.createElement('div');
        thumb.className = 'w-20 h-20 rounded-xl overflow-hidden border border-cyan-500/40 relative shadow-md';
        thumb.innerHTML = `<img src="${base64Data}" class="w-full h-full object-cover">`;
        previewContainer.appendChild(thumb);
      };
      reader.readAsDataURL(file);
    });
  },

  populateReviewStep() {
    document.getElementById('review-title').innerText = this.reportData.title;
    document.getElementById('review-desc').innerText = this.reportData.description;
    document.getElementById('review-cat').innerText = this.reportData.category;
    document.getElementById('review-subcat').innerText = this.reportData.subcategory;
    document.getElementById('review-address').innerText = this.reportData.address;
    document.getElementById('review-coords').innerText = `${this.reportData.latitude}, ${this.reportData.longitude}`;

    // Live AI Preview classification
    window.CivicAI.apiFetch('/ai/classify', {
      method: 'POST',
      body: JSON.stringify({ title: this.reportData.title, description: this.reportData.description })
    }).then(res => {
      if (res.success) {
        document.getElementById('review-ai-dept').innerText = res.classification.department;
        document.getElementById('review-ai-urgency').innerText = res.classification.urgency.toUpperCase();
        document.getElementById('review-ai-confidence').innerText = `${Math.round(res.classification.confidence * 100)}%`;
      }
    }).catch(() => {});
  },

  async submitComplaint() {
    const submitBtn = document.getElementById('report-submit-btn');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = 'AI Engine Processing & Submitting...';
    }

    try {
      const res = await window.CivicAI.apiFetch('/complaints', {
        method: 'POST',
        body: JSON.stringify(this.reportData)
      });

      if (res.success) {
        window.CivicAI.toast(`Complaint registered with ID ${res.data.tracking_id}!`, 'success');
        this.showSubmissionConfirmation(res.data);
        await this.fetchDashboardStats();
        await this.fetchMyComplaints();
      }
    } catch (e) {
      window.CivicAI.toast(`Submission failed: ${e.message}`, 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Confirm & Submit to City Authority';
      }
    }
  },

  showSubmissionConfirmation(data) {
    document.querySelectorAll('.report-step-content').forEach(el => el.classList.add('hidden'));
    const confirmEl = document.getElementById('report-confirmation-screen');
    if (!confirmEl) return;
    confirmEl.classList.remove('hidden');

    document.getElementById('confirm-tracking-id').innerText = data.tracking_id;
    document.getElementById('confirm-priority').innerText = `${data.priority.toUpperCase()} (Score: ${data.priority_score}/100)`;
    document.getElementById('confirm-brief').innerText = data.action_brief || 'Dispatched to Department';
  },

  resetReportForm() {
    this.currentStep = 1;
    this.goToStep(1);
    const form = document.getElementById('new-complaint-form');
    if (form) form.reset();
    document.getElementById('report-image-preview').innerHTML = '';
    document.getElementById('report-confirmation-screen')?.classList.add('hidden');
  },

  // -------------------------------------------------------------
  // Complaint Details Drawer & Feedback
  // -------------------------------------------------------------
  async openDetailsModal(trackingId) {
    try {
      const res = await window.CivicAI.apiFetch(`/complaints/${trackingId}`);
      if (!res.success) return;

      const c = res.data;
      const modal = document.getElementById('complaint-detail-modal');
      const content = document.getElementById('complaint-detail-content');
      if (!modal || !content) return;

      const prioColors = {
        critical: 'text-red-400 bg-red-950/80 border-red-500/50',
        high: 'text-orange-400 bg-orange-950/80 border-orange-500/50',
        medium: 'text-yellow-400 bg-yellow-950/80 border-yellow-500/50',
        low: 'text-emerald-400 bg-emerald-950/80 border-emerald-500/50'
      };

      content.innerHTML = `
        <div class="space-y-6">
          <!-- Header Banner -->
          <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div class="flex items-center gap-3 mb-1">
                <span class="font-mono text-sm font-bold text-cyan-400 bg-cyan-950 px-3 py-1 rounded-lg border border-cyan-800">
                  ${c.tracking_id}
                </span>
                <span class="px-3 py-1 rounded-lg text-xs font-bold border ${prioColors[c.priority] || prioColors.medium}">
                  ${c.priority.toUpperCase()} PRIORITY (${c.ai_analysis ? c.ai_analysis.total_priority_score : 50}/100)
                </span>
                <span class="px-3 py-1 rounded-lg text-xs font-semibold badge-status-${c.status}">
                  ${c.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <h3 class="text-xl font-bold text-slate-100">${c.title}</h3>
              <p class="text-xs text-slate-400 mt-1">Reported on ${new Date(c.created_at).toLocaleString()} • ${c.location ? c.location.address : 'Downtown'}</p>
            </div>
            <div class="text-right">
              <span class="text-xs text-slate-400 block">Assigned Authority</span>
              <span class="text-sm font-bold text-cyan-400">${c.department ? c.department.name : 'Municipal Triage'}</span>
            </div>
          </div>

          <!-- AI Action Brief -->
          ${c.ai_analysis ? `
            <div class="glass-panel p-4 rounded-xl border-cyan-500/30 bg-cyan-950/20">
              <div class="flex items-center gap-2 text-xs font-bold text-cyan-400 mb-2">
                <span>🤖</span> AI INTELLIGENCE ACTION BRIEF
              </div>
              <pre class="font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">${c.ai_analysis.action_brief || 'Action brief generated.'}</pre>
            </div>
          ` : ''}

          <!-- Priority Score Breakdown (5 Factors) -->
          ${c.ai_analysis && c.ai_analysis.factor_breakdown ? `
            <div class="glass-panel p-4 rounded-xl">
              <h5 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Explainable Priority Factors</h5>
              <div class="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
                ${Object.entries(c.ai_analysis.factor_breakdown).map(([factor, data]) => `
                  <div class="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                    <div class="flex justify-between text-slate-400 mb-1">
                      <span class="capitalize font-medium">${factor.replace('_', ' ')}</span>
                      <span class="font-mono text-cyan-400">${data.weight}</span>
                    </div>
                    <div class="w-full bg-slate-800 rounded-full h-1.5 mb-1.5">
                      <div class="bg-cyan-500 h-1.5 rounded-full" style="width: ${data.score}%"></div>
                    </div>
                    <span class="font-bold text-slate-200">${data.score}/100</span>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <!-- Before / After Resolution Evidence -->
          ${c.resolution_evidence ? `
            <div class="glass-panel p-5 rounded-2xl border-emerald-500/30 bg-emerald-950/10">
              <h5 class="text-sm font-bold text-emerald-400 mb-3 flex items-center gap-2">
                <span>✓</span> OFFICIAL RESOLUTION EVIDENCE
              </h5>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                <div class="rounded-xl overflow-hidden border border-red-500/30 bg-slate-900">
                  <div class="px-3 py-1.5 bg-red-950/80 text-red-300 text-xs font-bold">BEFORE REMEDIATION</div>
                  <img src="${c.resolution_evidence.before_image_url || '/uploads/before_work.svg'}" class="w-full h-40 object-cover">
                </div>
                <div class="rounded-xl overflow-hidden border border-emerald-500/30 bg-slate-900">
                  <div class="px-3 py-1.5 bg-emerald-950/80 text-emerald-300 text-xs font-bold">AFTER REMEDIATION</div>
                  <img src="${c.resolution_evidence.after_image_url || '/uploads/after_work.svg'}" class="w-full h-40 object-cover">
                </div>
              </div>
              <p class="text-xs text-slate-300 font-medium">${c.resolution_evidence.resolution_summary}</p>
              <div class="flex items-center justify-between text-xs text-slate-400 mt-2 pt-2 border-t border-emerald-900/40">
                <span>Labor Hours: ${c.resolution_evidence.labor_hours} hrs</span>
                <span>Equipment: ${c.resolution_evidence.equipment_used}</span>
              </div>
            </div>
          ` : ''}

          <!-- Complete Audit Status Timeline -->
          <div class="glass-panel p-5 rounded-2xl">
            <h5 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4">Official Verification Timeline</h5>
            <div class="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-700">
              ${c.status_history.map(h => `
                <div class="relative">
                  <div class="absolute -left-6 top-1 w-3 h-3 rounded-full bg-cyan-500 border-2 border-slate-900"></div>
                  <div class="flex items-center justify-between text-xs">
                    <span class="font-bold text-slate-200 capitalize">${h.new_status.replace('_', ' ')}</span>
                    <span class="text-slate-500">${new Date(h.timestamp).toLocaleString()}</span>
                  </div>
                  <p class="text-xs text-slate-400 mt-0.5">${h.explanation || 'Status updated'}</p>
                  <span class="text-[10px] text-cyan-400/80">By ${h.author_name || 'System'} (${h.user_role})</span>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Citizen Satisfaction Feedback Form (If Resolved) -->
          ${c.status === 'resolved' || c.status === 'closed' ? `
            <div class="glass-panel p-5 rounded-2xl border-slate-700">
              <h5 class="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">Citizen Feedback & Reopen</h5>
              <div class="flex items-center gap-3 mb-3">
                <span class="text-xs text-slate-400">Rate resolution quality:</span>
                <select id="feedback-rating" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1 text-xs text-slate-200">
                  <option value="5">⭐⭐⭐⭐⭐ Excellent (5/5)</option>
                  <option value="4">⭐⭐⭐⭐ Good (4/5)</option>
                  <option value="3">⭐⭐⭐ Acceptable (3/5)</option>
                  <option value="2">⭐⭐ Poor (2/5)</option>
                  <option value="1">⭐ Unsatisfied (1/5)</option>
                </select>
              </div>
              <textarea id="feedback-comments" placeholder="Add comments regarding this resolution..." class="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 h-16 mb-3"></textarea>
              <div class="flex items-center justify-between">
                <label class="flex items-center gap-2 text-xs text-rose-400">
                  <input type="checkbox" id="feedback-reopen" class="rounded bg-slate-900 border-rose-500">
                  <span>Reopen this complaint (Work incomplete)</span>
                </label>
                <button onclick="CitizenController.submitFeedback(${c.id})" class="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs">
                  Submit Feedback
                </button>
              </div>
            </div>
          ` : ''}
        </div>
      `;

      modal.classList.remove('hidden');
      modal.classList.add('flex');
    } catch (e) {
      console.error('Failed to open complaint details:', e);
    }
  },

  async submitFeedback(complaintId) {
    const rating = document.getElementById('feedback-rating')?.value;
    const comments = document.getElementById('feedback-comments')?.value;
    const reopen = document.getElementById('feedback-reopen')?.checked;

    try {
      const res = await window.CivicAI.apiFetch(`/complaints/${complaintId}/feedback`, {
        method: 'POST',
        body: JSON.stringify({ rating, comments, reopen_requested: reopen })
      });
      if (res.success) {
        window.CivicAI.toast(reopen ? 'Complaint reopened for reinspection' : 'Feedback recorded! Thank you.', 'success');
        window.CivicAI.closeModal('complaint-detail-modal');
        await this.fetchMyComplaints();
      }
    } catch (e) {
      window.CivicAI.toast(`Feedback submission error: ${e.message}`, 'error');
    }
  }
};
