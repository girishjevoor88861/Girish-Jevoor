/**
 * CivicAI - Advanced Interactive Map Controller
 * Leaflet map visualization with priority-coded markers, DBSCAN hotspot overlays,
 * cluster layers, category/priority/status filters, and side panel drawer.
 */

window.MapViewController = {
  map: null,
  markerLayer: null,
  hotspotLayer: null,
  complaintsData: [],
  hotspotsData: [],
  filters: {
    category: 'all',
    priority: 'all',
    status: 'all',
    showHotspots: true
  },

  async load() {
    this.initMap();
    await this.fetchMapData();
    this.renderMap();
  },

  initMap() {
    const container = document.getElementById('civic-interactive-map');
    if (!container) return;

    if (!this.map) {
      // Default City Center: Metro Civic Center (12.9716, 77.5946)
      this.map = L.map('civic-interactive-map', {
        zoomControl: true,
        attributionControl: true
      }).setView([12.971598, 77.594566], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | CivicAI Intelligence',
        maxZoom: 19
      }).addTo(this.map);

      this.markerLayer = L.layerGroup().addTo(this.map);
      this.hotspotLayer = L.layerGroup().addTo(this.map);
    } else {
      this.map.invalidateSize();
    }
  },

  async fetchMapData() {
    try {
      const [compRes, hotRes] = await Promise.all([
        window.CivicAI.apiFetch('/complaints?limit=100'),
        window.CivicAI.apiFetch('/ai/hotspots')
      ]);

      if (compRes.success) this.complaintsData = compRes.data;
      if (hotRes.success) this.hotspotsData = hotRes.data;
    } catch (e) {
      console.error('Error fetching map data:', e);
    }
  },

  renderMap() {
    if (!this.map) return;
    this.markerLayer.clearLayers();
    this.hotspotLayer.clearLayers();

    // 1. Render Hotspot Clusters (Overlays)
    if (this.filters.showHotspots && this.hotspotsData.length > 0) {
      this.hotspotsData.forEach(h => {
        const radiusMeters = (h.radius_km || 0.6) * 1000;
        const color = h.severity_level === 'critical' ? '#ef4444' :
                      h.severity_level === 'high' ? '#f97316' : '#00b4d8';

        const circle = L.circle([h.center_lat, h.center_lng], {
          color: color,
          fillColor: color,
          fillOpacity: 0.18,
          weight: 2,
          dashArray: '4, 6'
        }).addTo(this.hotspotLayer);

        circle.bindPopup(`
          <div class="custom-map-popup p-1">
            <div class="text-xs font-bold text-cyan-400 mb-1">🔥 CIVIC HOTSPOT CLUSTER</div>
            <div class="font-bold text-sm text-slate-100">${h.cluster_name}</div>
            <div class="text-xs text-slate-300 mt-1">Concentration: <strong>${h.complaint_count} reports</strong></div>
            <div class="text-xs text-slate-400">Dominant Category: ${h.dominant_category}</div>
            <div class="text-[11px] text-slate-400 mt-1">Radius: ${h.radius_km} km • Severity: <span class="capitalize text-red-400 font-bold">${h.severity_level}</span></div>
          </div>
        `);
      });
    }

    // 2. Render Complaint Markers
    const filtered = this.complaintsData.filter(c => {
      if (this.filters.category !== 'all' && c.category !== this.filters.category) return false;
      if (this.filters.priority !== 'all' && c.priority !== this.filters.priority) return false;
      if (this.filters.status !== 'all' && c.status !== this.filters.status) return false;
      return true;
    });

    const markerColors = {
      critical: '#ef4444',
      high: '#f97316',
      medium: '#eab308',
      low: '#10b981'
    };

    filtered.forEach(c => {
      if (!c.latitude || !c.longitude) return;

      const color = markerColors[c.priority] || '#00b4d8';
      const isCritical = c.priority === 'critical';

      // Custom HTML Pin Marker
      const icon = L.divIcon({
        className: 'custom-div-icon',
        html: `
          <div style="
            background-color: ${color};
            width: ${isCritical ? '22px' : '18px'};
            height: ${isCritical ? '22px' : '18px'};
            border-radius: 50%;
            border: 2px solid #ffffff;
            box-shadow: 0 0 10px ${color};
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
          " class="${isCritical ? 'animate-pulse-critical' : ''}">
            <div style="width: 6px; height: 6px; background: white; border-radius: 50%;"></div>
          </div>
        `,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });

      const marker = L.marker([c.latitude, c.longitude], { icon }).addTo(this.markerLayer);

      // Popup
      marker.bindPopup(`
        <div class="custom-map-popup p-1 min-w-[200px]">
          <div class="flex items-center justify-between text-[10px] text-slate-400 mb-1">
            <span class="font-mono text-cyan-400 font-bold">${c.tracking_id}</span>
            <span class="capitalize font-bold text-${c.priority === 'critical' ? 'red-400' : 'slate-200'}">${c.priority}</span>
          </div>
          <h5 class="text-xs font-bold text-slate-100 mb-1">${c.title}</h5>
          <p class="text-[11px] text-slate-400 line-clamp-2 mb-2">${c.description}</p>
          <div class="text-[10px] text-slate-400 mb-2">📍 ${c.address || 'Metro Ward'}</div>
          <button onclick="CitizenController.openDetailsModal('${c.tracking_id}')" class="w-full py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-[11px] transition-colors">
            Inspect Action Brief &rarr;
          </button>
        </div>
      `);

      marker.on('click', () => {
        this.showComplaintSideDrawer(c);
      });
    });

    const countEl = document.getElementById('map-displayed-count');
    if (countEl) countEl.innerText = `${filtered.length} visible complaints (${this.hotspotsData.length} hotspots)`;
  },

  showComplaintSideDrawer(comp) {
    const drawer = document.getElementById('map-side-drawer');
    const content = document.getElementById('map-side-content');
    if (!drawer || !content) return;

    content.innerHTML = `
      <div class="p-4 space-y-3 text-xs">
        <div class="flex items-center justify-between">
          <span class="font-mono text-cyan-400 font-bold bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
            ${comp.tracking_id}
          </span>
          <span class="px-2 py-0.5 rounded-full font-bold badge-priority-${comp.priority}">
            ${comp.priority.toUpperCase()}
          </span>
        </div>
        <h4 class="font-bold text-sm text-slate-100">${comp.title}</h4>
        <p class="text-slate-400 text-xs">${comp.description}</p>
        <div class="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
          <div><strong>Category:</strong> ${comp.category}</div>
          <div><strong>Address:</strong> ${comp.address || 'Downtown'}</div>
          <div><strong>Status:</strong> ${comp.status.replace('_', ' ').toUpperCase()}</div>
        </div>
        <button onclick="CitizenController.openDetailsModal('${comp.tracking_id}')" class="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-md">
          Open Full Details & Timeline &rarr;
        </button>
      </div>
    `;

    drawer.classList.remove('hidden');
  },

  closeSideDrawer() {
    const drawer = document.getElementById('map-side-drawer');
    if (drawer) drawer.classList.add('hidden');
  },

  applyFilters() {
    this.filters.category = document.getElementById('map-filter-category')?.value || 'all';
    this.filters.priority = document.getElementById('map-filter-priority')?.value || 'all';
    this.filters.status = document.getElementById('map-filter-status')?.value || 'all';
    this.filters.showHotspots = document.getElementById('map-toggle-hotspots')?.checked ?? true;
    this.renderMap();
  }
};
