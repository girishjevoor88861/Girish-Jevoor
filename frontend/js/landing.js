/**
 * CivicAI - Public Landing Page Controller
 * Handles live KPI statistics, category overview, quick tracking, FAQ toggles, and hero interactions.
 */

window.LandingController = {
  async load() {
    await this.fetchLiveStats();
    await this.fetchCategoryStats();
    await this.fetchRecentResolved();
  },

  async fetchLiveStats() {
    try {
      const res = await window.CivicAI.apiFetch('/analytics/kpis');
      if (res && res.success) {
        const d = res.data;
        this.animateCounter('stat-total-reports', d.total_reports);
        this.animateCounter('stat-resolved-reports', d.resolved_reports);
        this.animateCounter('stat-resolution-rate', `${d.resolution_rate_pct}%`);
        this.animateCounter('stat-avg-time', `${d.average_resolution_hours}h`);
        
        // Update hero badges
        const heroResolved = document.getElementById('hero-badge-resolved');
        if (heroResolved) heroResolved.innerText = `${d.resolved_reports} Issues Restored`;
      }
    } catch (e) {
      console.error('Could not load landing KPIs:', e);
    }
  },

  async fetchCategoryStats() {
    try {
      const res = await window.CivicAI.apiFetch('/analytics/charts');
      if (res && res.success && res.data.by_category) {
        const container = document.getElementById('landing-category-cards');
        if (!container) return;

        const icons = {
          'Roads & Infrastructure': '🛣️',
          'Drainage & Water Management': '🌊',
          'Sanitation': '🗑️',
          'Electricity & Streetlights': '⚡',
          'Public Safety': '🛡️',
          'Water Supply': '🚰',
          'Parks & Public Spaces': '🌳'
        };

        container.innerHTML = res.data.by_category.map(cat => `
          <div class="glass-panel p-6 rounded-2xl hover:border-cyan-500/40 transition-all hover:scale-[1.02] cursor-pointer group" onclick="CivicAI.navigateTo('citizen')">
            <div class="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform">
              ${icons[cat.name] || '🏛️'}
            </div>
            <h4 class="text-lg font-bold text-slate-100 mb-1 group-hover:text-cyan-400 transition-colors">${cat.name}</h4>
            <div class="flex items-center justify-between mt-3 text-sm">
              <span class="text-slate-400">Total Reports</span>
              <span class="px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800">${cat.value}</span>
            </div>
          </div>
        `).join('');
      }
    } catch (e) {
      console.error('Could not load categories:', e);
    }
  },

  async fetchRecentResolved() {
    try {
      const res = await window.CivicAI.apiFetch('/complaints?status=resolved&limit=3');
      const container = document.getElementById('landing-resolved-preview');
      if (!container || !res.success) return;

      container.innerHTML = res.data.map(comp => `
        <div class="glass-panel rounded-2xl overflow-hidden border border-slate-700/50 hover:border-emerald-500/40 transition-all">
          <div class="relative h-48 bg-slate-900 overflow-hidden">
            <img src="/uploads/after_work.svg" alt="Resolved evidence" class="w-full h-full object-cover">
            <div class="absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500 text-slate-950 shadow-lg">
              RESTORED & VERIFIED
            </div>
          </div>
          <div class="p-6">
            <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span class="font-mono text-cyan-400">${comp.tracking_id}</span>
              <span>${comp.ward || 'Downtown'}</span>
            </div>
            <h4 class="text-base font-bold text-slate-100 line-clamp-1 mb-2">${comp.title}</h4>
            <p class="text-sm text-slate-400 line-clamp-2 mb-4">${comp.description}</p>
            <div class="flex items-center justify-between pt-4 border-t border-slate-800 text-xs">
              <span class="text-emerald-400 font-semibold">${comp.department_name || 'Municipal Works'}</span>
              <button onclick="CivicAI.navigateTo('tracker', { trackingId: '${comp.tracking_id}' })" class="text-cyan-400 hover:text-cyan-300 font-medium">View Timeline &rarr;</button>
            </div>
          </div>
        </div>
      `).join('');
    } catch (e) {
      console.error('Could not load recent resolved:', e);
    }
  },

  animateCounter(elId, targetVal) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.innerText = targetVal;
  },

  quickTrack() {
    const input = document.getElementById('hero-quick-track-input');
    if (!input || !input.value.trim()) {
      window.CivicAI.toast('Please enter a tracking ID (e.g. CIV-2026-1001)', 'warning');
      return;
    }
    const trackingId = input.value.trim().toUpperCase();
    window.CivicAI.navigateTo('tracker', { trackingId });
  },

  toggleFaq(btn) {
    const answer = btn.nextElementSibling;
    const icon = btn.querySelector('.faq-icon');
    if (answer.classList.contains('hidden')) {
      answer.classList.remove('hidden');
      if (icon) icon.style.transform = 'rotate(180deg)';
    } else {
      answer.classList.add('hidden');
      if (icon) icon.style.transform = 'rotate(0deg)';
    }
  }
};
