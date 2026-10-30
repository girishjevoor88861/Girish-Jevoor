# CivicAI - REST API Documentation

Base URL: `http://localhost:8000/api`

All requests and responses use standard JSON (`application/json`). Authentication is handled via Bearer tokens passed in the `Authorization` header.

---

## 1. Authentication Endpoints

### Register Citizen
- **`POST /api/auth/register`**
- **Payload**:
  ```json
  {
    "email": "citizen@example.com",
    "password": "Password@123",
    "full_name": "Alice Morgan",
    "phone": "+1 555-0192"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "success": true,
    "data": {
      "user": { "id": 18, "email": "citizen@example.com", "role": "citizen", "full_name": "Alice Morgan" },
      "token": "eyJzdWIiOjE4LCJlbWFpbCI6...<signature>"
    }
  }
  ```

### User Login
- **`POST /api/auth/login`**
- **Payload**:
  ```json
  { "email": "admin@civicai.gov", "password": "Admin@1234" }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "user": { "id": 1, "email": "admin@civicai.gov", "role": "admin", "full_name": "Commissioner Sarah Mitchell" },
      "token": "..."
    }
  }
  ```

### Current User Profile
- **`GET /api/auth/me`** (Requires Bearer Token)

---

## 2. Complaint Endpoints

### List Complaints (with Search, Filters, Sorting, Pagination)
- **`GET /api/complaints`**
- **Query Parameters**:
  - `category`: Filter by category (e.g. `Roads & Infrastructure`)
  - `status`: Filter by status (`submitted`, `assigned`, `in_progress`, `resolved`, `closed`)
  - `priority`: Filter by priority (`critical`, `high`, `medium`, `low`)
  - `department_id`: Department ID
  - `search`: Universal search (tracking ID, title, address, citizen name)
  - `sort_by`: `created_at`, `priority`, `status`, `title`
  - `sort_order`: `asc` or `desc`
  - `page`: Page number (default: 1)
  - `limit`: Items per page (default: 20)
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": [ ... ],
    "pagination": { "total": 55, "page": 1, "limit": 20, "total_pages": 3 }
  }
  ```

### Get Complaint Details
- **`GET /api/complaints/<id_or_tracking_id>`**
- **Response (200 OK)**:
  Returns full complaint object including location, citizen details, images, AI analysis with 5-factor breakdown, duplicate matches, audit timeline, resolution evidence, and citizen feedback.

### Submit New Complaint
- **`POST /api/complaints`**
- **Payload**:
  ```json
  {
    "title": "Severe waterlogging outside Central Metro",
    "description": "Deep stormwater accumulation blocking road...",
    "category": "Drainage & Water Management",
    "subcategory": "Severe Waterlogging",
    "address": "400 Central Metro Avenue",
    "ward": "Ward 12 - Downtown",
    "latitude": 12.9725,
    "longitude": 77.5955,
    "images": ["/uploads/complaint_sample.svg"]
  }
  ```

### Update Complaint Status
- **`PATCH /api/complaints/<id>/status`** (Requires Token)
- **Payload**:
  ```json
  {
    "status": "in_progress",
    "explanation": "Field crew arrived on site with equipment"
  }
  ```

### Assign Officer & Department
- **`PATCH /api/complaints/<id>/assign`** (Admin only)
- **Payload**:
  ```json
  {
    "officer_id": 1,
    "notes": "Dispatch drainage vacuum truck within 24h SLA"
  }
  ```

### Priority Override
- **`PATCH /api/complaints/<id>/priority`** (Admin only)
- **Payload**:
  ```json
  {
    "priority": "critical",
    "priority_score": 92.0,
    "reason": "School zone child pedestrian hazard"
  }
  ```

### Duplicate Action (Confirm / Link / Reject)
- **`POST /api/complaints/<id>/duplicate-action`** (Admin only)
- **Payload**:
  ```json
  {
    "duplicate_id": 6,
    "action": "link",
    "explanation": "Identical waterlogging reported by neighboring store"
  }
  ```

### Export CSV
- **`GET /api/complaints/export/csv`**
- Returns downloadable CSV file `civicai_complaints_export.csv`.

---

## 3. AI Engine Endpoints

### On-the-fly Classification
- **`POST /api/ai/classify`**
- **Payload**: `{ "title": "...", "description": "..." }`

### On-the-fly Priority Scoring
- **`POST /api/ai/priority`**
- **Payload**: `{ "title": "...", "description": "...", "category": "...", "latitude": 12.97, "longitude": 77.59 }`

### Candidate Duplicate Search
- **`POST /api/ai/duplicates`**
- **Payload**: `{ "title": "...", "description": "...", "category": "...", "latitude": 12.97, "longitude": 77.59 }`

### Get Geographic Hotspots
- **`GET /api/ai/hotspots`**
- Returns list of DBSCAN clusters with centroid lat/lng, radius in km, complaint count, and dominant category.

---

## 4. Analytics & Officer Endpoints

### Dashboard KPIs
- **`GET /api/analytics/kpis`**
- Returns: `total_reports`, `new_reports_today`, `pending_reports`, `critical_reports`, `active_assignments`, `resolved_reports`, `resolution_rate_pct`, `average_resolution_hours`.

### Analytics Charts
- **`GET /api/analytics/charts?days=30`**
- Returns category breakdown, priority distribution, weekly trends, and department performance.

### Officer Workload & Tasks
- **`GET /api/officers/me/tasks`** (Officer / Admin)

### Submit Resolution Evidence
- **`POST /api/officers/evidence`** (Officer / Admin)
- **Payload**:
  ```json
  {
    "complaint_id": 55,
    "resolution_summary": "Asphalt patch completed and compacted.",
    "equipment_used": "Compactor & Road Roller",
    "labor_hours": 3.0,
    "before_image_url": "/uploads/before_work.svg",
    "after_image_url": "/uploads/after_work.svg"
  }
  ```
