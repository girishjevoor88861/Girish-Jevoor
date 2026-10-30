# CivicAI
### Smart Cities. Smarter Decisions. Faster Resolutions.

CivicAI is an enterprise-grade, fully integrated, AI-powered smart civic issue management platform built for municipal governments, field inspection crews, and citizens. It streamlines the entire municipal lifecycle—from multi-step citizen reporting with GPS tagging, to genuine natural language classification, semantic duplicate matching, explainable 5-factor priority calculation, authority action brief generation, DBSCAN geographic hotspot clustering, officer assignment, on-site resolution evidence, and universal public tracking.

---

## Key Highlights

- **4 Major Role-Based Interfaces**:
  1. **Public Landing Page**: Live civic stats counter, categories grid, recent resolved complaints, how-it-works, FAQ, and testimonials.
  2. **Citizen Portal**: Multi-step reporting wizard with Leaflet GPS location picker, My Complaints with filtering/sorting/pagination, detail drawer with explainable AI scoring breakdown, and in-app notifications.
  3. **Municipal Administration Portal**: 8 real-time KPI cards calculated from database, interactive Chart.js analytics, Complaint Management Center table with bulk assignment, CSV export, duplicate linking drawer, priority overrides, department management, and live activity feed.
  4. **Field Officer Portal**: Dispatch queue, task tabs (Pending Acceptance, In Progress, Critical, Completed), on-site progress notes, and photo evidence verification.
- **Universal Complaint Tracker**: Public timeline verification by Tracking ID (`CIV-2026-XXXXX`).
- **Explainable AI Engine**:
  - **Module 1**: Automatic classification into 7 municipal departments and 35 subcategories with confidence scoring and keyword extraction.
  - **Module 2**: Intelligent duplicate detection fusing Jaccard/N-gram text similarity and Haversine distance (< 350m).
  - **Module 3**: 5-factor priority scoring (Safety Risk 30%, Public Impact 25%, Urgency 20%, Concentration 15%, Frequency 10%) with life-hazard safety overrides.
  - **Module 4**: Authority-ready action brief generator.
  - **Module 5**: DBSCAN geographic clustering for municipal hotspots.
- **Persistent Relational Database**: 18 related SQLite tables with foreign keys, indexes, and constraints. Zero external pip or npm setup required.
- **Automated Verification**: Complete test suite executing all 20 mandatory test cases with a 100% pass rate.

---

## Quick Start (1-Click Launch)

### On Windows
Double-click `start_server.bat` or run in PowerShell:
```powershell
.\start_server.ps1
```
Open your browser to: **[http://localhost:8000](http://localhost:8000)**

### Manual Startup (Any OS with Python 3)
```bash
python backend/app.py
```

---

## Demo Credentials (Pre-Seeded)

| Role | Email | Password | Pre-configured Responsibilities |
| :--- | :--- | :--- | :--- |
| **Municipal Admin** | `admin@civicai.gov` | `Admin@1234` | Full access to KPI dashboard, triage, assignments, duplicate linking, priority overrides |
| **Field Officer** | `officer.john@civicai.gov` | `Officer@1234` | Roads Inspector: accepts assignments, logs on-site notes, submits resolution photos |
| **Field Officer** | `officer.sarah@civicai.gov` | `Officer@1234` | Drainage Operations Lead |
| **Citizen** | `citizen.alice@example.com` | `Citizen@1234` | Lodges complaints, monitors progress, receives notifications, rates resolutions |

> ⚡ **Tip**: You can also switch between roles instantly using the **"⚡ Demo Roles"** menu in the top-right navbar without manually typing credentials!

---

## Documentation Index

- [INSTALLATION.md](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/INSTALLATION.md): Setup, configuration, and dependencies.
- [ARCHITECTURE.md](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/ARCHITECTURE.md): System architecture, RBAC, and data flow.
- [DATABASE_SCHEMA.md](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/DATABASE_SCHEMA.md): Complete 18-table schema and relational diagrams.
- [AI_APPROACH.md](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/AI_APPROACH.md): NLP classification, duplicate detection, explainable priority formulas, and clustering algorithms.
- [API_DOCUMENTATION.md](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/API_DOCUMENTATION.md): Endpoints, payloads, and responses.
- [TESTING_REPORT.md](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/TESTING_REPORT.md): Automated QA test results for all 20 test cases.
- [LIMITATIONS.md](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/LIMITATIONS.md): Operational boundaries and future roadmap.
- [DEMO_GUIDE.md](file:///c:/Users/ASUS/OneDrive/Desktop/hackthon%20floder/DEMO_GUIDE.md): 5-minute end-to-end walkthrough script.
