/**
 * CivicAI - Core Application Framework
 * Handles global state, client-side routing, JWT authentication, toasts, API requests, and modals.
 */

const API_BASE = '/api';

// Global Application State
window.CivicAI = {
  currentUser: null,
  token: localStorage.getItem('civicai_token') || null,
  currentView: 'landing', // 'landing', 'citizen', 'admin', 'officer', 'tracker'
  theme: localStorage.getItem('civicai_theme') || 'dark',

  // Initialize Application
  async init() {
    this.applyTheme(this.theme);
    await this.checkAuth();
    this.setupEventListeners();
    this.route();
  },

  // Apply Light/Dark Theme
  applyTheme(theme) {
    this.theme = theme;
    localStorage.setItem('civicai_theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
      themeBtn.innerHTML = theme === 'dark' 
        ? `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>`
        : `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>`;
    }
  },

  toggleTheme() {
    this.applyTheme(this.theme === 'dark' ? 'light' : 'dark');
  },

  // Authenticate Current Session
  async checkAuth() {
    if (!this.token) {
      this.currentUser = null;
      this.updateAuthUI();
      return;
    }
    try {
      const res = await this.apiFetch('/auth/me');
      if (res && res.success) {
        this.currentUser = res.user;
      } else {
        this.logout(false);
      }
    } catch (e) {
      this.currentUser = null;
    }
    this.updateAuthUI();
  },

  // Generic Authenticated API Fetch
  async apiFetch(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || `HTTP error ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Fetch Error [${endpoint}]:`, err);
      throw err;
    }
  },

  // Save Authentication
  setAuth(user, token) {
    this.currentUser = user;
    this.token = token;
    localStorage.setItem('civicai_token', token);
    this.updateAuthUI();
  },

  // Logout
  logout(notify = true) {
    this.currentUser = null;
    this.token = null;
    localStorage.removeItem('civicai_token');
    this.updateAuthUI();
    this.navigateTo('landing');
    if (notify) this.toast('Logged out successfully', 'info');
  },

  // Update Navigation Bar according to Auth Role
  updateAuthUI() {
    const userRoleBadge = document.getElementById('nav-user-role');
    const userName = document.getElementById('nav-user-name');
    const authActions = document.getElementById('nav-auth-actions');
    const userMenu = document.getElementById('nav-user-menu');
    const portalNavLinks = document.getElementById('portal-nav-links');

    if (this.currentUser) {
      if (authActions) authActions.classList.add('hidden');
      if (userMenu) userMenu.classList.remove('hidden');
      if (userName) userName.innerText = this.currentUser.full_name;
      if (userRoleBadge) {
        userRoleBadge.innerText = this.currentUser.role.toUpperCase();
        userRoleBadge.className = `px-2 py-0.5 rounded text-xs font-semibold ${
          this.currentUser.role === 'admin' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
          this.currentUser.role === 'officer' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
          'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
        }`;
      }
      this.fetchNotificationsCount();
    } else {
      if (authActions) authActions.classList.remove('hidden');
      if (userMenu) userMenu.classList.add('hidden');
    }
  },

  // Fetch Unread Notifications Count
  async fetchNotificationsCount() {
    if (!this.currentUser) return;
    try {
      const res = await this.apiFetch('/notifications');
      const badge = document.getElementById('notif-badge');
      if (badge && res.unread_count > 0) {
        badge.innerText = res.unread_count;
        badge.classList.remove('hidden');
      } else if (badge) {
        badge.classList.add('hidden');
      }
    } catch (e) {}
  },

  // View Navigation Router
  navigateTo(viewId, params = {}) {
    this.currentView = viewId;
    
    // Hide all view containers
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));

    // Update active nav links
    document.querySelectorAll('.portal-nav-btn').forEach(btn => {
      btn.classList.remove('text-cyan-400', 'border-b-2', 'border-cyan-400');
      btn.classList.add('text-slate-400');
    });

    const activeBtn = document.getElementById(`nav-link-${viewId}`);
    if (activeBtn) {
      activeBtn.classList.remove('text-slate-400');
      activeBtn.classList.add('text-cyan-400', 'border-b-2', 'border-cyan-400');
    }

    // Role Guard Check
    if (viewId === 'admin' && (!this.currentUser || this.currentUser.role !== 'admin')) {
      this.toast('Admin authentication required', 'warning');
      this.openAuthModal('admin');
      return;
    }
    if (viewId === 'officer' && (!this.currentUser || (this.currentUser.role !== 'officer' && this.currentUser.role !== 'admin'))) {
      this.toast('Field Officer authentication required', 'warning');
      this.openAuthModal('officer');
      return;
    }

    // Show selected view
    const targetEl = document.getElementById(`view-${viewId}`);
    if (targetEl) {
      targetEl.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Trigger view-specific renderers
    if (viewId === 'landing' && window.LandingController) window.LandingController.load();
    if (viewId === 'citizen' && window.CitizenController) window.CitizenController.load();
    if (viewId === 'admin' && window.AdminController) window.AdminController.load();
    if (viewId === 'officer' && window.OfficerController) window.OfficerController.load();
    if (viewId === 'tracker' && window.TrackerController) window.TrackerController.load(params.trackingId);
  },

  route() {
    const hash = window.location.hash.replace('#', '') || 'landing';
    if (hash.startsWith('track/')) {
      const trackingId = hash.replace('track/', '');
      this.navigateTo('tracker', { trackingId });
    } else {
      this.navigateTo(hash);
    }
  },

  // Toast Notification System
  toast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const colors = {
      success: 'bg-emerald-950/90 text-emerald-200 border-emerald-500/40 shadow-emerald-950/50',
      error: 'bg-rose-950/90 text-rose-200 border-rose-500/40 shadow-rose-950/50',
      warning: 'bg-amber-950/90 text-amber-200 border-amber-500/40 shadow-amber-950/50',
      info: 'bg-slate-900/90 text-cyan-200 border-cyan-500/40 shadow-cyan-950/50'
    };

    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };

    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-md shadow-lg text-sm font-medium fade-in ${colors[type] || colors.info}`;
    toast.innerHTML = `
      <span class="w-5 h-5 flex items-center justify-center rounded-full bg-white/10 font-bold">${icons[type]}</span>
      <span class="flex-1">${message}</span>
      <button onclick="this.parentElement.remove()" class="text-white/60 hover:text-white ml-2 text-base font-bold">&times;</button>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      toast.style.transition = 'all 0.3s ease-out';
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  },

  // Quick 1-Click Role Switcher for Demo
  async quickLoginAs(role) {
    const accounts = {
      admin: { email: 'admin@civicai.gov', pass: 'Admin@1234' },
      officer: { email: 'officer.john@civicai.gov', pass: 'Officer@1234' },
      citizen: { email: 'citizen.alice@example.com', pass: 'Citizen@1234' }
    };
    const creds = accounts[role];
    if (!creds) return;

    try {
      const res = await this.apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: creds.email, password: creds.pass })
      });
      if (res.success) {
        this.setAuth(res.data.user, res.data.token);
        this.toast(`Authenticated as ${role.toUpperCase()}: ${res.data.user.full_name}`, 'success');
        this.closeModal('auth-modal');
        if (role === 'admin') this.navigateTo('admin');
        else if (role === 'officer') this.navigateTo('officer');
        else this.navigateTo('citizen');
      }
    } catch (e) {
      this.toast(`Demo login failed: ${e.message}`, 'error');
    }
  },

  openAuthModal(defaultRole = 'citizen') {
    const modal = document.getElementById('auth-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    this.switchAuthTab('login');
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  },

  switchAuthTab(tab) {
    const loginForm = document.getElementById('auth-login-form');
    const registerForm = document.getElementById('auth-register-form');
    const forgotForm = document.getElementById('auth-forgot-form');
    const tabLogin = document.getElementById('tab-btn-login');
    const tabRegister = document.getElementById('tab-btn-register');

    if (loginForm) loginForm.classList.add('hidden');
    if (registerForm) registerForm.classList.add('hidden');
    if (forgotForm) forgotForm.classList.add('hidden');

    if (tab === 'login') {
      if (loginForm) loginForm.classList.remove('hidden');
      if (tabLogin) tabLogin.className = 'flex-1 py-2 text-center font-semibold text-cyan-400 border-b-2 border-cyan-400';
      if (tabRegister) tabRegister.className = 'flex-1 py-2 text-center font-medium text-slate-400 hover:text-slate-200';
    } else if (tab === 'register') {
      if (registerForm) registerForm.classList.remove('hidden');
      if (tabRegister) tabRegister.className = 'flex-1 py-2 text-center font-semibold text-cyan-400 border-b-2 border-cyan-400';
      if (tabLogin) tabLogin.className = 'flex-1 py-2 text-center font-medium text-slate-400 hover:text-slate-200';
    } else if (tab === 'forgot') {
      if (forgotForm) forgotForm.classList.remove('hidden');
    }
  },

  setupEventListeners() {
    // Listen for hash changes
    window.addEventListener('hashchange', () => this.route());
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.CivicAI.init();
});
