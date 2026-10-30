/**
 * CivicAI - Public Universal Complaint Tracker
 * Live tracking screen for citizens and evaluators using tracking ID.
 */

window.TrackerController = {
  async load(trackingId) {
    const input = document.getElementById('tracker-input-field');
    if (trackingId && input) {
      input.value = trackingId;
      await this.trackComplaint(trackingId);
    }
  },

  async trackComplaint(explicitId = null) {
    const input = document.getElementById('tracker-input-field');
    const trackingId = explicitId || input?.value.trim().toUpperCase();
    const resultContainer = document.getElementById('tracker-results-container');
    if (!trackingId || !resultContainer) return;

    resultContainer.innerHTML = `
      <div class="py-16 text-center text-slate-400">
        <div class="animate-spin text-3xl mb-3">⚙️</div>
        <p class="text-sm">Fetching verified civic record for <strong>${trackingId}</strong>...</p>
      </div>
    `;

    try {
      const res = await window.CivicAI.apiFetch(`/complaints/${trackingId}`);
      if (!res.success) {
        resultContainer.innerHTML = `
          <div class="glass-panel p-8 text-center rounded-2xl border-rose-500/30">
            <div class="text-3xl mb-2">🔍</div>
            <h4 class="text-lg font-bold text-rose-300">Complaint Not Found</h4>
            <p class="text-xs text-slate-400 mt-1">No municipal record matching tracking ID '${trackingId}'. Please verify your reference number.</p>
          </div>
        `;
        return;
      }

      const c = res.data;
      const statuses = ['submitted', 'ai_analyzed', 'under_review', 'assigned', 'in_progress', 'resolved', 'closed'];
      const currentIndex = statuses.indexOf(c.status);

      resultContainer.innerHTML = `
        <div class="glass-panel p-6 rounded-2xl border border-cyan-500/30 space-y-6 fade-in">
          <!-- Header -->
          <div class="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div class="flex items-center gap-2 mb-2">
                <span class="font-mono text-xs font-bold text-cyan-400 bg-cyan-950 px-3 py-1 rounded-md border border-cyan-800">
                  ${c.tracking_id}
                </span>
                <span class="px-2.5 py-0.5 rounded-full text-xs font-bold badge-status-${c.status}">
                  ${c.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <h3 class="text-xl font-bold text-slate-100">${c.title}</h3>
              <p class="text-xs text-slate-400 mt-1">📍 ${c.location ? c.location.address : 'Downtown'} • Category: ${c.category}</p>
            </div>
            <div class="text-right">
              <span class="text-xs text-slate-400 block">Assigned Department</span>
              <span class="text-sm font-bold text-cyan-400">${c.department ? c.department.name : 'Municipal Works'}</span>
            </div>
          </div>

          <!-- Visual Progress Lifecycle -->
          <div class="py-2">
            <div class="flex items-center justify-between relative text-xs">
              <div class="absolute left-0 right-0 top-3 h-1 bg-slate-800 -z-0"></div>
              <div class="absolute left-0 top-3 h-1 bg-cyan-500 -z-0 transition-all duration-500" style="width: ${Math.max(0, (currentIndex / (statuses.length - 1)) * 100)}%"></div>

              ${statuses.slice(0, 6).map((st, i) => `
                <div class="flex flex-col items-center relative z-10">
                  <div class="w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${
                    i <= currentIndex ? 'bg-cyan-500 text-slate-950 shadow-glow' : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }">
                    ${i <= currentIndex ? '✓' : i + 1}
                  </div>
                  <span class="text-[10px] mt-1.5 capitalize font-medium ${i <= currentIndex ? 'text-cyan-300' : 'text-slate-500'}">
                    ${st.replace('_', ' ')}
                  </span>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- AI Summary & Priority -->
          ${c.ai_analysis ? `
            <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
              <div class="flex items-center gap-2 font-bold text-cyan-400 mb-1">
                <span>🤖</span> AI Executive Summary
              </div>
              <p class="text-slate-300">${c.ai_analysis.short_summary}</p>
              <div class="flex items-center gap-4 mt-2 text-slate-400 text-[11px]">
                <span>Priority Score: <strong class="text-slate-200">${c.ai_analysis.total_priority_score}/100</strong></span>
                <span>Urgency: <strong class="text-slate-200 uppercase">${c.ai_analysis.urgency}</strong></span>
                <span>AI Confidence: <strong class="text-slate-200">${Math.round(c.ai_analysis.confidence * 100)}%</strong></span>
              </div>
            </div>
          ` : ''}

          <!-- Resolution Evidence If Completed -->
          ${c.resolution_evidence ? `
            <div class="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/40">
              <h5 class="text-xs font-bold text-emerald-400 mb-2">✓ Verified Field Resolution Evidence</h5>
              <div class="grid grid-cols-2 gap-3 mb-2">
                <img src="${c.resolution_evidence.before_image_url || '/uploads/before_work.svg'}" class="rounded-lg h-28 w-full object-cover border border-slate-800">
                <img src="${c.resolution_evidence.after_image_url || '/uploads/after_work.svg'}" class="rounded-lg h-28 w-full object-cover border border-slate-800">
              </div>
              <p class="text-xs text-slate-300">${c.resolution_evidence.resolution_summary}</p>
            </div>
          ` : ''}

          <!-- Audit Timeline -->
          <div>
            <h5 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Live Status Audit Log</h5>
            <div class="space-y-3">
              ${c.status_history.map(h => `
                <div class="flex items-start gap-3 text-xs p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/80">
                  <div class="w-2 h-2 rounded-full bg-cyan-400 mt-1 flex-shrink-0"></div>
                  <div class="flex-1">
                    <div class="flex items-center justify-between">
                      <span class="font-bold text-slate-200 capitalize">${h.new_status.replace('_', ' ')}</span>
                      <span class="text-[10px] text-slate-500">${new Date(h.timestamp).toLocaleString()}</span>
                    </div>
                    <p class="text-slate-400 text-[11px] mt-0.5">${h.explanation || 'Status milestone updated'}</p>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `;
    } catch (e) {
      console.error('Track error:', e);
    }
  }
};
