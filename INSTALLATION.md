# CivicAI Installation & Configuration Guide

This guide details the setup and deployment procedures for the CivicAI platform.

---

## 1. Prerequisites

- **Python 3.10+** (Python 3.14 tested and verified).
- No external packages (pip) or build tools (npm) are required. CivicAI leverages Python's high-performance standard library (`http.server.ThreadingHTTPServer`, `sqlite3`, `hashlib`, `hmac`, `json`, `math`).
- Modern web browser (Chrome, Edge, Firefox, Safari) with JavaScript enabled.

---

## 2. Directory Layout

```
hackthon floder/
├── backend/
│   ├── app.py              # Multi-threaded REST API server & routing
│   ├── config.py           # Configurable thresholds, weights, and file paths
│   ├── database.py         # Relational database initialization & connection manager
│   ├── auth.py             # PBKDF2 password hashing & token RBAC middleware
│   ├── ai_engine.py        # 5 genuine AI modules (classification, duplicates, priority, etc.)
│   ├── seed_data.py        # Demo generator (50+ complaints, deliberate duplicates, hotspots)
│   └── civicai.db          # Persistent SQLite database file
├── frontend/
│   ├── index.html          # Main application SPA (4 portals + tracker)
│   ├── css/
│   │   └── styles.css      # Enterprise design system & glassmorphism
│   └── js/
│       ├── app.js          # Core router, state, toasts, and auth modal
│       ├── landing.js      # Public landing controller & stats counters
│       ├── citizen.js      # 3-step report wizard & complaints tracker
│       ├── admin.js        # Admin dashboard, KPIs, Chart.js, and table
│       ├── officer.js      # Field officer workspace & resolution evidence
│       ├── map_view.js     # Leaflet interactive map & hotspot layers
│       └── tracker.js      # Universal complaint tracker
├── uploads/                # Photo evidence storage
├── tests/
│   └── test_suite.py       # Automated verification test suite (20 test cases)
├── start_server.bat        # Windows 1-click launch batch script
└── start_server.ps1        # PowerShell launch script
```

---

## 3. Installation Steps

1. **Clone or Download the Repository**:
   Ensure you are in the project root directory.

2. **Verify Database Initialization**:
   The database seeds automatically upon first run, or you can re-seed anytime with:
   ```powershell
   & "$env:LOCALAPPDATA\Python\bin\python.exe" -m backend.seed_data
   ```

3. **Start the CivicAI Application Server**:
   - Double-click `start_server.bat`, OR
   - Run in PowerShell:
     ```powershell
     .\start_server.ps1
     ```

4. **Access the Web Application**:
   Navigate to `http://localhost:8000` in your web browser.

---

## 4. Environment Variables (Optional)

You can override defaults by setting the following environment variables:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `CIVICAI_PORT` | `8000` | HTTP port on which the server listens |
| `CIVICAI_HOST` | `0.0.0.0` | Network binding interface |
| `CIVICAI_SECRET_KEY` | `civicai_super_secret...` | HMAC cryptographic signing key for session tokens |

---

## 5. Running the QA Test Suite

To run all 20 automated tests:
```powershell
& "$env:LOCALAPPDATA\Python\bin\python.exe" tests/test_suite.py
```
Expected output: `20/20 PASSED, 0/20 FAILED`.
