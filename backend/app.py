"""
CivicAI - Main Application Server & REST API
Multi-threaded HTTP REST API server with JWT authentication, role-based authorization,
complete CRUD operations, AI pipeline integration, and static file serving.
"""

import sys
import os
import json
import mimetypes
import urllib.parse
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import csv
import io
import uuid
import random
import math

# Add parent directory to sys.path so imports work seamlessly
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import HOST, PORT, UPLOAD_DIR, CITY_CENTER
from backend.database import get_db_connection, row_to_dict, rows_to_list
from backend.auth import (
    authenticate_user, register_citizen, get_current_user_from_token,
    verify_token, hash_password
)
from backend.ai_engine import (
    classify_complaint_text, calculate_priority_score, generate_action_brief,
    detect_duplicates, analyze_hotspots, haversine_distance_meters
)
from backend.seed_data import seed_database

class CivicAIRequestHandler(BaseHTTPRequestHandler):
    """Handles REST API requests, authentication, authorization, and static file serving."""

    def log_message(self, format, *args):
        # Override to keep logs clean and informative
        if "/api/" in self.path or self.command != "GET":
            sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {self.command} {self.path} - {args[0]}\n")

    def send_cors_headers(self):
        """Sends permissive CORS headers for web client interactions."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status_code=200):
        """Helper to send JSON response with appropriate headers."""
        body = json.dumps(data, indent=2, default=str).encode('utf-8')
        self.send_response(status_code)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status_code=400, details=None):
        """Helper to send standardized error JSON."""
        res = {"success": False, "error": message}
        if details:
            res["details"] = details
        self.send_json(res, status_code=status_code)

    def get_auth_user(self):
        """Extracts and verifies Bearer token from Authorization header."""
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[7:].strip()
        return get_current_user_from_token(token)

    def read_json_body(self):
        """Reads and parses JSON body from request."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length <= 0:
                return {}
            raw_data = self.rfile.read(content_length).decode('utf-8')
            return json.loads(raw_data)
        except Exception as e:
            return None

    # -------------------------------------------------------------
    # GET Router
    # -------------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API Endpoints
        if path.startswith("/api/"):
            self.handle_api_get(path, query)
            return

        # 2. Static File Serving
        self.handle_static_file(path)

    def handle_api_get(self, path, query):
        user = self.get_auth_user()

        # Auth: Me
        if path == "/api/auth/me":
            if not user:
                return self.send_error_json("Unauthorized", 401)
            return self.send_json({"success": True, "user": user})

        # Complaints: List with filters, search, sort, pagination
        if path == "/api/complaints":
            return self.api_list_complaints(query, user)

        # Complaints: Export CSV
        if path == "/api/complaints/export/csv":
            return self.api_export_csv(query, user)

        # Complaints: Details by ID or Tracking ID
        if path.startswith("/api/complaints/"):
            param = path.replace("/api/complaints/", "").strip()
            return self.api_get_complaint_details(param, user)

        # Analytics: KPIs
        if path == "/api/analytics/kpis":
            return self.api_get_kpis(query)

        # Analytics: Charts
        if path == "/api/analytics/charts":
            return self.api_get_charts(query)

        # Analytics: Activity Feed
        if path == "/api/analytics/activity-feed":
            return self.api_get_activity_feed(query)

        # AI: Hotspots
        if path == "/api/ai/hotspots":
            return self.api_get_hotspots()

        # Departments
        if path == "/api/departments":
            return self.api_get_departments()

        # Officers
        if path == "/api/officers":
            return self.api_get_officers(query)

        # Officer: My Tasks
        if path == "/api/officers/me/tasks":
            if not user or user["role"] not in ["officer", "admin"]:
                return self.send_error_json("Officer access required", 403)
            return self.api_get_officer_tasks(user)

        # Notifications
        if path == "/api/notifications":
            if not user:
                return self.send_error_json("Unauthorized", 401)
            return self.api_get_notifications(user)

        return self.send_error_json("API Endpoint Not Found", 404)

    # -------------------------------------------------------------
    # POST Router
    # -------------------------------------------------------------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        if body is None:
            return self.send_error_json("Invalid JSON body", 400)

        # Auth
        if path == "/api/auth/register":
            return self.api_auth_register(body)
        if path == "/api/auth/login":
            return self.api_auth_login(body)
        if path == "/api/auth/forgot-password":
            return self.api_auth_forgot_password(body)
        if path == "/api/auth/reset-password":
            return self.api_auth_reset_password(body)
        if path == "/api/auth/logout":
            return self.send_json({"success": True, "message": "Logged out successfully"})

        # Complaints: Create
        if path == "/api/complaints":
            return self.api_create_complaint(body)

        # AI On-the-fly Classification & Duplicate Checking
        if path == "/api/ai/classify":
            title = body.get("title", "")
            desc = body.get("description", "")
            res = classify_complaint_text(title, desc)
            return self.send_json({"success": True, "classification": res})

        if path == "/api/ai/priority":
            title = body.get("title", "")
            desc = body.get("description", "")
            cat = body.get("category", "Roads & Infrastructure")
            lat = float(body.get("latitude", CITY_CENTER["latitude"]))
            lng = float(body.get("longitude", CITY_CENTER["longitude"]))
            res = calculate_priority_score(title, desc, cat, lat, lng)
            return self.send_json({"success": True, "priority": res})

        if path == "/api/ai/duplicates":
            title = body.get("title", "")
            desc = body.get("description", "")
            cat = body.get("category", "Roads & Infrastructure")
            lat = float(body.get("latitude", CITY_CENTER["latitude"]))
            lng = float(body.get("longitude", CITY_CENTER["longitude"]))
            exclude = body.get("exclude_id")
            dups = detect_duplicates(None, title, desc, cat, lat, lng, exclude_id=exclude)
            return self.send_json({"success": True, "duplicates": dups})

        if path == "/api/ai/hotspots/recalculate":
            user = self.get_auth_user()
            if not user or user["role"] != "admin":
                return self.send_error_json("Admin permission required", 403)
            hotspots = analyze_hotspots()
            return self.send_json({"success": True, "hotspots": hotspots})

        # File Upload
        if path == "/api/upload":
            return self.api_upload_file(body)

        # Complaint Notes
        if path.startswith("/api/complaints/") and path.endswith("/notes"):
            comp_id = int(path.split("/")[3])
            return self.api_add_internal_note(comp_id, body)

        # Complaint Duplicate Action
        if path.startswith("/api/complaints/") and path.endswith("/duplicate-action"):
            comp_id = int(path.split("/")[3])
            return self.api_duplicate_action(comp_id, body)

        # Citizen Feedback
        if path.startswith("/api/complaints/") and path.endswith("/feedback"):
            comp_id = int(path.split("/")[3])
            return self.api_add_feedback(comp_id, body)

        # Field Officer: Submit Resolution Evidence
        if path == "/api/officers/evidence":
            return self.api_submit_resolution_evidence(body)

        # Notifications: Mark all as read
        if path == "/api/notifications/read-all":
            user = self.get_auth_user()
            if not user:
                return self.send_error_json("Unauthorized", 401)
            conn = get_db_connection()
            conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user["id"],))
            conn.commit()
            conn.close()
            return self.send_json({"success": True, "message": "All notifications marked as read"})

        # Admin: Reset Demo Data
        if path == "/api/admin/reset-demo":
            user = self.get_auth_user()
            if not user or user["role"] != "admin":
                return self.send_error_json("Admin permission required", 403)
            seed_database(force=True)
            return self.send_json({"success": True, "message": "Database and demo data successfully reset to fresh factory state."})

        return self.send_error_json("API Endpoint Not Found", 404)

    # -------------------------------------------------------------
    # PATCH / PUT Router
    # -------------------------------------------------------------
    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body() or {}

        # Update Status
        if path.startswith("/api/complaints/") and path.endswith("/status"):
            comp_id = int(path.split("/")[3])
            return self.api_update_complaint_status(comp_id, body)

        # Assign Officer & Department
        if path.startswith("/api/complaints/") and path.endswith("/assign"):
            comp_id = int(path.split("/")[3])
            return self.api_assign_complaint(comp_id, body)

        # Adjust Priority
        if path.startswith("/api/complaints/") and path.endswith("/priority"):
            comp_id = int(path.split("/")[3])
            return self.api_adjust_priority(comp_id, body)

        # Mark notification read
        if path.startswith("/api/notifications/") and path.endswith("/read"):
            notif_id = int(path.split("/")[3])
            user = self.get_auth_user()
            if not user:
                return self.send_error_json("Unauthorized", 401)
            conn = get_db_connection()
            conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, user["id"]))
            conn.commit()
            conn.close()
            return self.send_json({"success": True})

        return self.send_error_json("API Endpoint Not Found", 404)

    # -------------------------------------------------------------
    # Controller Implementations
    # -------------------------------------------------------------
    def api_auth_register(self, body):
        email = body.get("email", "")
        password = body.get("password", "")
        full_name = body.get("full_name", "")
        phone = body.get("phone", "")
        res, err = register_citizen(email, password, full_name, phone)
        if err:
            return self.send_error_json(err, 400)
        return self.send_json({"success": True, "data": res}, 201)

    def api_auth_login(self, body):
        email = body.get("email", "")
        password = body.get("password", "")
        res, err = authenticate_user(email, password)
        if err:
            return self.send_error_json(err, 401)
        return self.send_json({"success": True, "data": res})

    def api_auth_forgot_password(self, body):
        email = body.get("email", "").strip().lower()
        conn = get_db_connection()
        user = conn.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if not user:
            return self.send_error_json("No account registered with this email", 404)
        return self.send_json({
            "success": True,
            "message": f"Password reset instructions and verification code sent to {email}. (For demo: use code 882910)",
            "reset_code": "882910"
        })

    def api_auth_reset_password(self, body):
        email = body.get("email", "").strip().lower()
        new_password = body.get("new_password", "")
        if len(new_password) < 6:
            return self.send_error_json("Password must be at least 6 characters", 400)
        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            conn.close()
            return self.send_error_json("User not found", 404)
        hashed = hash_password(new_password)
        conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed, email))
        conn.commit()
        conn.close()
        return self.send_json({"success": True, "message": "Password reset successfully. You may now log in."})

    def api_list_complaints(self, query, user):
        """Lists complaints with comprehensive search, filters, sorting, and pagination."""
        category = query.get("category", [None])[0]
        priority = query.get("priority", [None])[0]
        status = query.get("status", [None])[0]
        dept_id = query.get("department_id", [None])[0]
        search = query.get("search", [None])[0]
        user_id = query.get("user_id", [None])[0]
        sort_by = query.get("sort_by", ["created_at"])[0]
        sort_order = query.get("sort_order", ["desc"])[0].upper()
        page = max(1, int(query.get("page", [1])[0]))
        limit = min(100, max(1, int(query.get("limit", [20])[0])))
        offset = (page - 1) * limit

        # Restrict citizen to their complaints unless role is admin or officer or querying by specific tracking_id
        if user and user["role"] == "citizen" and not user_id:
            user_id = user["id"]

        where_clauses = ["1=1"]
        params = []

        if category and category != "all":
            where_clauses.append("c.category = ?")
            params.append(category)
        if priority and priority != "all":
            where_clauses.append("c.priority = ?")
            params.append(priority)
        if status and status != "all":
            where_clauses.append("c.status = ?")
            params.append(status)
        if dept_id and dept_id != "all":
            where_clauses.append("c.department_id = ?")
            params.append(int(dept_id))
        if user_id:
            where_clauses.append("c.user_id = ?")
            params.append(int(user_id))
        if search:
            s = f"%{search.strip()}%"
            where_clauses.append("""
                (c.tracking_id LIKE ? OR c.title LIKE ? OR c.description LIKE ? 
                 OR l.address LIKE ? OR l.ward LIKE ? OR d.name LIKE ? OR u.full_name LIKE ?)
            """)
            params.extend([s, s, s, s, s, s, s])

        allowed_sort = {
            "created_at": "c.created_at",
            "priority": "a.total_priority_score",
            "status": "c.status",
            "title": "c.title",
            "tracking_id": "c.tracking_id"
        }
        order_col = allowed_sort.get(sort_by, "c.created_at")
        if sort_order not in ["ASC", "DESC"]:
            sort_order = "DESC"

        where_sql = " AND ".join(where_clauses)
        conn = get_db_connection()
        try:
            total_count = conn.execute(f"""
                SELECT COUNT(*) as count
                FROM complaints c
                LEFT JOIN complaint_locations l ON c.id = l.complaint_id
                LEFT JOIN departments d ON c.department_id = d.id
                LEFT JOIN users u ON c.user_id = u.id
                WHERE {where_sql}
            """, params).fetchone()["count"]

            sql = f"""
                SELECT c.*, l.latitude, l.longitude, l.address, l.ward,
                       d.name as department_name, d.code as department_code,
                       u.full_name as citizen_name, u.email as citizen_email,
                       o_u.full_name as officer_name, o.badge_number as officer_badge,
                       a.total_priority_score, a.confidence as ai_confidence, a.short_summary
                FROM complaints c
                LEFT JOIN complaint_locations l ON c.id = l.complaint_id
                LEFT JOIN departments d ON c.department_id = d.id
                LEFT JOIN users u ON c.user_id = u.id
                LEFT JOIN officers o ON c.assigned_officer_id = o.id
                LEFT JOIN users o_u ON o.user_id = o_u.id
                LEFT JOIN ai_analysis a ON c.id = a.complaint_id
                WHERE {where_sql}
                ORDER BY {order_col} {sort_order}
                LIMIT ? OFFSET ?
            """
            rows = conn.execute(sql, params + [limit, offset]).fetchall()
            complaints = rows_to_list(rows)

            return self.send_json({
                "success": True,
                "data": complaints,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "limit": limit,
                    "total_pages": math.ceil(total_count / limit) if total_count > 0 else 1
                }
            })
        finally:
            conn.close()

    def api_get_complaint_details(self, param, user):
        """Fetches full complaint details including images, AI breakdown, duplicates, history, notes, and evidence."""
        conn = get_db_connection()
        try:
            if param.isdigit():
                query = "SELECT * FROM complaints WHERE id = ?"
                c_row = conn.execute(query, (int(param),)).fetchone()
            else:
                query = "SELECT * FROM complaints WHERE tracking_id = ?"
                c_row = conn.execute(query, (param.strip().upper(),)).fetchone()

            if not c_row:
                return self.send_error_json("Complaint not found", 404)

            complaint = row_to_dict(c_row)
            comp_id = complaint["id"]

            # Location
            loc_row = conn.execute("SELECT * FROM complaint_locations WHERE complaint_id = ?", (comp_id,)).fetchone()
            complaint["location"] = row_to_dict(loc_row)

            # Citizen
            cit_row = conn.execute("SELECT id, full_name, email, phone FROM users WHERE id = ?", (complaint["user_id"],)).fetchone()
            complaint["citizen"] = row_to_dict(cit_row)

            # Department
            if complaint["department_id"]:
                dept_row = conn.execute("SELECT * FROM departments WHERE id = ?", (complaint["department_id"],)).fetchone()
                complaint["department"] = row_to_dict(dept_row)
            else:
                complaint["department"] = None

            # Officer
            if complaint["assigned_officer_id"]:
                off_row = conn.execute("""
                    SELECT o.*, u.full_name as officer_name, u.email as officer_email, u.phone as officer_phone
                    FROM officers o
                    JOIN users u ON o.user_id = u.id
                    WHERE o.id = ?
                """, (complaint["assigned_officer_id"],)).fetchone()
                complaint["officer"] = row_to_dict(off_row)
            else:
                complaint["officer"] = None

            # Images
            img_rows = conn.execute("SELECT * FROM complaint_images WHERE complaint_id = ? ORDER BY uploaded_at ASC", (comp_id,)).fetchall()
            complaint["images"] = rows_to_list(img_rows)

            # AI Analysis
            ai_row = conn.execute("SELECT * FROM ai_analysis WHERE complaint_id = ?", (comp_id,)).fetchone()
            if ai_row:
                ai_dict = row_to_dict(ai_row)
                # Reconstruct factor breakdown dynamically
                weights = {"safety_risk": 0.30, "public_impact": 0.25, "urgency": 0.20, "geographic_concentration": 0.15, "report_frequency": 0.10}
                ai_dict["factor_breakdown"] = {
                    "safety_risk": {"score": ai_dict["safety_score"], "weight": "30%", "reason": "Immediate hazard & injury risk assessment"},
                    "public_impact": {"score": ai_dict["public_impact_score"], "weight": "25%", "reason": "Zone traffic & population affected"},
                    "urgency": {"score": ai_dict["urgency_score"], "weight": "20%", "reason": "Temporal sensitivity & escalation risk"},
                    "geographic_concentration": {"score": ai_dict["concentration_score"], "weight": "15%", "reason": "Density of nearby civic complaints"},
                    "report_frequency": {"score": ai_dict["frequency_score"], "weight": "10%", "reason": "Corroborated by duplicate reports"}
                }
                complaint["ai_analysis"] = ai_dict
            else:
                complaint["ai_analysis"] = None

            # Duplicates
            dup_rows = conn.execute("""
                SELECT d.*, c2.tracking_id as duplicate_tracking_id, c2.title as duplicate_title,
                       c2.priority as duplicate_priority, c2.status as duplicate_status,
                       l2.address as duplicate_address
                FROM duplicate_matches d
                JOIN complaints c2 ON d.duplicate_complaint_id = c2.id
                JOIN complaint_locations l2 ON c2.id = l2.complaint_id
                WHERE d.primary_complaint_id = ?
            """, (comp_id,)).fetchall()
            complaint["duplicates"] = rows_to_list(dup_rows)

            # Status History (Audit Timeline)
            history_rows = conn.execute("""
                SELECT h.*, u.full_name as author_name
                FROM status_history h
                JOIN users u ON h.changed_by = u.id
                WHERE h.complaint_id = ?
                ORDER BY h.timestamp ASC
            """, (comp_id,)).fetchall()
            complaint["status_history"] = rows_to_list(history_rows)

            # Resolution Evidence
            res_row = conn.execute("""
                SELECT r.*, u.full_name as officer_name
                FROM resolution_evidence r
                JOIN officers o ON r.officer_id = o.id
                JOIN users u ON o.user_id = u.id
                WHERE r.complaint_id = ?
            """, (comp_id,)).fetchone()
            complaint["resolution_evidence"] = row_to_dict(res_row)

            # Internal Notes (Hidden from citizens)
            if user and user["role"] in ["admin", "officer"]:
                notes_rows = conn.execute("""
                    SELECT n.*, u.full_name as author_name, u.role as author_role
                    FROM internal_notes n
                    JOIN users u ON n.author_id = u.id
                    WHERE n.complaint_id = ?
                    ORDER BY n.created_at DESC
                """, (comp_id,)).fetchall()
                complaint["internal_notes"] = rows_to_list(notes_rows)
            else:
                complaint["internal_notes"] = []

            # Public Updates
            updates_rows = conn.execute("""
                SELECT p.*, u.full_name as author_name
                FROM public_updates p
                JOIN users u ON p.author_id = u.id
                WHERE p.complaint_id = ?
                ORDER BY p.created_at ASC
            """, (comp_id,)).fetchall()
            complaint["public_updates"] = rows_to_list(updates_rows)

            # Citizen Feedback
            feedback_row = conn.execute("SELECT * FROM citizen_feedback WHERE complaint_id = ?", (comp_id,)).fetchone()
            complaint["feedback"] = row_to_dict(feedback_row)

            return self.send_json({"success": True, "data": complaint})
        finally:
            conn.close()

    def api_create_complaint(self, body):
        """Creates a new complaint through the 3-step workflow, executing AI processing immediately."""
        user = self.get_auth_user()
        user_id = user["id"] if user else None

        title = body.get("title", "").strip()
        description = body.get("description", "").strip()
        address = body.get("address", "").strip()
        ward = body.get("ward", "Ward 12 - Downtown")
        lat = float(body.get("latitude", CITY_CENTER["latitude"]))
        lng = float(body.get("longitude", CITY_CENTER["longitude"]))
        images = body.get("images", []) # array of URLs or base64

        if not title or not description:
            return self.send_error_json("Title and description are required", 400)
        if not address:
            address = f"Civic Zone near {lat:.4f}, {lng:.4f}"

        # If guest reporting or not logged in, assign to default citizen Alice or create anonymous citizen user
        conn = get_db_connection()
        try:
            if not user_id:
                guest = conn.execute("SELECT id FROM users WHERE role = 'citizen' LIMIT 1").fetchone()
                user_id = guest["id"] if guest else 2

            # 1. Run AI Module 1: Classification & Department Routing
            ai_class = classify_complaint_text(title, description)
            category = body.get("category") or ai_class["category"]
            subcategory = body.get("subcategory") or ai_class["subcategory"]
            dept_name = ai_class["department"]

            # Lookup department ID
            dept_row = conn.execute("SELECT id FROM departments WHERE name = ?", (dept_name,)).fetchone()
            dept_id = dept_row["id"] if dept_row else 1

            # 2. Run AI Module 3: Explainable Priority Scoring
            priority_res = calculate_priority_score(title, description, category, lat, lng, recent_complaints_count=1)
            priority_level = priority_res["priority_level"]

            # 3. Run AI Module 4: Action Brief
            action_brief = generate_action_brief(
                title=title,
                location_address=address,
                priority_level=priority_level,
                priority_score=priority_res["total_score"],
                related_reports_count=1,
                department=dept_name,
                category=category,
                public_impact_desc=priority_res["factor_breakdown"]["public_impact"]["reasons"][0],
                recommended_action=priority_res["recommended_action"]
            )

            # Generate Unique Tracking ID: CIV-2026-XXXXX
            random_num = random.randint(10000, 99999)
            tracking_id = f"CIV-2026-{random_num}"

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO complaints (
                    tracking_id, user_id, title, description, category, subcategory,
                    priority, status, department_id, public_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'submitted', ?, 'Initial AI triage completed. Queued for municipal review.')
            """, (tracking_id, user_id, title, description, category, subcategory, priority_level, dept_id))
            complaint_id = cursor.lastrowid

            # Insert Location
            cursor.execute("""
                INSERT INTO complaint_locations (complaint_id, latitude, longitude, address, landmark, ward)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (complaint_id, lat, lng, address, body.get("landmark", ""), ward))

            # Insert Images
            if images:
                for img_url in images:
                    cursor.execute("""
                        INSERT INTO complaint_images (complaint_id, image_url, image_type, caption)
                        VALUES (?, ?, 'report', 'Citizen submitted field photo')
                    """, (complaint_id, img_url))
            else:
                cursor.execute("""
                    INSERT INTO complaint_images (complaint_id, image_url, image_type, caption)
                    VALUES (?, ?, 'report', 'Standard civic incident reference')
                """, (complaint_id, "/uploads/complaint_sample.svg"))

            # Insert AI Analysis
            cursor.execute("""
                INSERT INTO ai_analysis (
                    complaint_id, category, subcategory, department, short_summary,
                    keywords, urgency, confidence, safety_score, public_impact_score,
                    urgency_score, concentration_score, frequency_score, total_priority_score,
                    priority_level, action_brief, human_reviewed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                complaint_id, category, subcategory, dept_name,
                ai_class["short_summary"], ai_class["keywords"], ai_class["urgency"],
                ai_class["confidence"], priority_res["safety_score"], priority_res["public_impact_score"],
                priority_res["urgency_score"], priority_res["concentration_score"], priority_res["frequency_score"],
                priority_res["total_score"], priority_level, action_brief
            ))

            # Insert Initial Timeline History
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, explanation)
                VALUES (?, NULL, 'submitted', ?, 'citizen', 'Complaint officially lodged via CivicAI Mobile/Web')
            """, (complaint_id, user_id))

            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, explanation)
                VALUES (?, 'submitted', 'ai_analyzed', ?, 'system', ?)
            """, (complaint_id, user_id, f"AI processed: Category '{category}', Priority '{priority_level.upper()}' ({priority_res['total_score']}/100)"))

            # Notifications
            cursor.execute("""
                INSERT INTO notifications (user_id, complaint_id, title, message, type)
                VALUES (?, ?, 'Complaint Lodged Successfully', ?, 'success')
            """, (user_id, complaint_id, f"Your issue '{title}' has been registered with tracking ID {tracking_id}."))

            # Audit Log
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
                VALUES (?, 'CREATE_COMPLAINT', 'COMPLAINT', ?, ?)
            """, (user_id, str(complaint_id), f"Created {tracking_id} ({category})"))

            conn.commit()

            # 4. Run AI Module 2: Duplicate Detection
            dups = detect_duplicates(complaint_id, title, description, category, lat, lng, exclude_id=complaint_id)
            if dups:
                for d in dups:
                    cursor.execute("""
                        INSERT INTO duplicate_matches (primary_complaint_id, duplicate_complaint_id, similarity_score, geo_distance_m, status, explanation)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (complaint_id, d["duplicate_complaint_id"], d["similarity_score"], d["geo_distance_m"], d["status"], d["explanation"]))
                conn.commit()

            return self.send_json({
                "success": True,
                "data": {
                    "id": complaint_id,
                    "tracking_id": tracking_id,
                    "title": title,
                    "category": category,
                    "priority": priority_level,
                    "priority_score": priority_res["total_score"],
                    "status": "submitted",
                    "action_brief": action_brief,
                    "potential_duplicates": len(dups)
                }
            }, 201)
        finally:
            conn.close()

    def api_update_complaint_status(self, comp_id, body):
        """Updates complaint status with full audit logging, permissions, and citizen notification."""
        user = self.get_auth_user()
        if not user:
            return self.send_error_json("Unauthorized", 401)

        new_status = body.get("status")
        explanation = body.get("explanation", "").strip() or f"Status changed to {new_status}"
        
        valid_statuses = [
            'submitted', 'ai_analyzed', 'under_review', 'assigned',
            'in_progress', 'resolved', 'closed', 'reopened',
            'rejected', 'more_info_required', 'duplicate_linked'
        ]
        if new_status not in valid_statuses:
            return self.send_error_json(f"Invalid status '{new_status}'", 400)

        conn = get_db_connection()
        try:
            comp = conn.execute("SELECT * FROM complaints WHERE id = ?", (comp_id,)).fetchone()
            if not comp:
                return self.send_error_json("Complaint not found", 404)

            # Role permissions
            if user["role"] == "citizen" and new_status not in ["reopened", "closed"]:
                return self.send_error_json("Citizens can only close or reopen their own complaints", 403)
            if user["role"] == "officer" and comp["assigned_officer_id"] != user.get("officer_info", {}).get("id") and user["role"] != "admin":
                return self.send_error_json("You can only update complaints assigned to you", 403)

            prev_status = comp["status"]
            resolved_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if new_status in ["resolved", "closed"] else None

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE complaints
                SET status = ?, updated_at = CURRENT_TIMESTAMP, resolved_at = COALESCE(?, resolved_at)
                WHERE id = ?
            """, (new_status, resolved_at, comp_id))

            # Audit History
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (comp_id, prev_status, new_status, user["id"], user["role"], explanation))

            # Notification to Citizen
            cursor.execute("""
                INSERT INTO notifications (user_id, complaint_id, title, message, type)
                VALUES (?, ?, 'Complaint Status Updated', ?, 'info')
            """, (comp["user_id"], comp_id, f"Complaint {comp['tracking_id']} status updated to '{new_status.replace('_', ' ').title()}': {explanation}"))

            # Audit Log
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
                VALUES (?, 'UPDATE_STATUS', 'COMPLAINT', ?, ?)
            """, (user["id"], str(comp_id), f"{prev_status} -> {new_status}: {explanation}"))

            conn.commit()
            return self.send_json({"success": True, "message": f"Status updated to {new_status}"})
        finally:
            conn.close()

    def api_assign_complaint(self, comp_id, body):
        """Assigns complaint to a department and specific field officer."""
        user = self.get_auth_user()
        if not user or user["role"] != "admin":
            return self.send_error_json("Administrator privileges required", 403)

        dept_id = body.get("department_id")
        officer_id = body.get("officer_id")
        notes = body.get("notes", "Assigned for immediate field inspection and remediation.")

        if not officer_id:
            return self.send_error_json("Officer ID is required", 400)

        conn = get_db_connection()
        try:
            comp = conn.execute("SELECT * FROM complaints WHERE id = ?", (comp_id,)).fetchone()
            if not comp:
                return self.send_error_json("Complaint not found", 404)

            officer = conn.execute("SELECT o.*, u.full_name FROM officers o JOIN users u ON o.user_id = u.id WHERE o.id = ?", (officer_id,)).fetchone()
            if not officer:
                return self.send_error_json("Officer not found", 404)

            target_dept_id = dept_id or officer["department_id"]

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE complaints
                SET department_id = ?, assigned_officer_id = ?, status = 'assigned', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (target_dept_id, officer_id, comp_id))

            # Assignment record
            cursor.execute("""
                INSERT INTO assignments (complaint_id, officer_id, assigned_by, status, notes)
                VALUES (?, ?, ?, 'pending', ?)
            """, (comp_id, officer_id, user["id"], notes))

            # History
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, explanation)
                VALUES (?, ?, 'assigned', ?, 'admin', ?)
            """, (comp_id, comp["status"], user["id"], f"Assigned to {officer['full_name']} ({officer['badge_number']}): {notes}"))

            # Notify Officer
            cursor.execute("""
                INSERT INTO notifications (user_id, complaint_id, title, message, type)
                VALUES (?, ?, 'New Task Assigned', ?, 'warning')
            """, (officer["user_id"], comp_id, f"You have been assigned to complaint {comp['tracking_id']}: '{comp['title']}'."))

            # Notify Citizen
            cursor.execute("""
                INSERT INTO notifications (user_id, complaint_id, title, message, type)
                VALUES (?, ?, 'Officer Dispatched', ?, 'info')
            """, (comp["user_id"], comp_id, f"Officer {officer['full_name']} has been assigned to your report {comp['tracking_id']}."))

            conn.commit()
            return self.send_json({"success": True, "message": f"Successfully assigned to {officer['full_name']}"})
        finally:
            conn.close()

    def api_adjust_priority(self, comp_id, body):
        """Allows administrators to manually adjust or override priority with reasoning."""
        user = self.get_auth_user()
        if not user or user["role"] != "admin":
            return self.send_error_json("Administrator privileges required", 403)

        new_priority = body.get("priority")
        new_score = float(body.get("priority_score", 75.0))
        reason = body.get("reason", "Administrative review adjustment").strip()

        if new_priority not in ["critical", "high", "medium", "low"]:
            return self.send_error_json("Invalid priority level", 400)

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE complaints SET priority = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_priority, comp_id))
            cursor.execute("""
                UPDATE ai_analysis
                SET priority_level = ?, total_priority_score = ?, human_reviewed = 1, reviewed_by = ?
                WHERE complaint_id = ?
            """, (new_priority, new_score, user["id"], comp_id))

            cursor.execute("""
                INSERT INTO internal_notes (complaint_id, author_id, note_text)
                VALUES (?, ?, ?)
            """, (comp_id, user["id"], f"PRIORITY OVERRIDE: Changed to {new_priority.upper()} (Score: {new_score}). Reason: {reason}"))

            conn.commit()
            return self.send_json({"success": True, "message": "Priority updated successfully"})
        finally:
            conn.close()

    def api_duplicate_action(self, comp_id, body):
        """Handles admin confirmation, linking, or rejection of duplicate matches."""
        user = self.get_auth_user()
        if not user or user["role"] != "admin":
            return self.send_error_json("Admin privileges required", 403)

        duplicate_id = body.get("duplicate_id")
        action = body.get("action") # 'confirm', 'reject', 'link'
        explanation = body.get("explanation", "").strip()

        if action not in ["confirm", "reject", "link"]:
            return self.send_error_json("Invalid action", 400)

        status_map = {"confirm": "confirmed", "reject": "rejected", "link": "confirmed"}
        target_status = status_map[action]

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE duplicate_matches
                SET status = ?
                WHERE (primary_complaint_id = ? AND duplicate_complaint_id = ?)
                   OR (primary_complaint_id = ? AND duplicate_complaint_id = ?)
            """, (target_status, comp_id, duplicate_id, duplicate_id, comp_id))

            if action in ["confirm", "link"]:
                cursor.execute("UPDATE complaints SET status = 'duplicate_linked' WHERE id = ?", (comp_id,))
                cursor.execute("""
                    INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, explanation)
                    VALUES (?, 'submitted', 'duplicate_linked', ?, 'admin', ?)
                """, (comp_id, user["id"], f"Linked as confirmed duplicate of complaint #{duplicate_id}. {explanation}"))

            conn.commit()
            return self.send_json({"success": True, "message": f"Duplicate action '{action}' recorded."})
        finally:
            conn.close()

    def api_add_internal_note(self, comp_id, body):
        """Adds internal note visible only to admins and officers."""
        user = self.get_auth_user()
        if not user or user["role"] not in ["admin", "officer"]:
            return self.send_error_json("Admin/Officer access required", 403)

        note_text = body.get("note_text", "").strip()
        if not note_text:
            return self.send_error_json("Note text cannot be empty", 400)

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO internal_notes (complaint_id, author_id, note_text)
                VALUES (?, ?, ?)
            """, (comp_id, user["id"], note_text))
            conn.commit()
            return self.send_json({"success": True, "message": "Note added successfully"})
        finally:
            conn.close()

    def api_add_feedback(self, comp_id, body):
        """Allows citizen to submit satisfaction rating and comments."""
        user = self.get_auth_user()
        if not user:
            return self.send_error_json("Unauthorized", 401)

        rating = int(body.get("rating", 5))
        comments = body.get("comments", "").strip()
        reopen = 1 if body.get("reopen_requested") else 0

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO citizen_feedback (complaint_id, user_id, rating, comments, reopen_requested)
                VALUES (?, ?, ?, ?, ?)
            """, (comp_id, user["id"], rating, comments, reopen))

            if reopen:
                cursor.execute("UPDATE complaints SET status = 'reopened' WHERE id = ?", (comp_id,))
                cursor.execute("""
                    INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, explanation)
                    VALUES (?, 'resolved', 'reopened', ?, 'citizen', ?)
                """, (comp_id, user["id"], f"Citizen reopened issue: {comments}"))

            conn.commit()
            return self.send_json({"success": True, "message": "Feedback submitted successfully"})
        finally:
            conn.close()

    def api_submit_resolution_evidence(self, body):
        """Field officer submits before/after photo evidence, summary, and marks completed."""
        user = self.get_auth_user()
        if not user or user["role"] not in ["officer", "admin"]:
            return self.send_error_json("Officer access required", 403)

        comp_id = int(body.get("complaint_id", 0))
        summary = body.get("resolution_summary", "").strip()
        equipment = body.get("equipment_used", "Standard municipal remediation tools")
        hours = float(body.get("labor_hours", 2.0))
        before_img = body.get("before_image_url") or "/uploads/before_work.svg"
        after_img = body.get("after_image_url") or "/uploads/after_work.svg"

        if not comp_id or not summary:
            return self.send_error_json("Complaint ID and resolution summary required", 400)

        conn = get_db_connection()
        try:
            comp = conn.execute("SELECT * FROM complaints WHERE id = ?", (comp_id,)).fetchone()
            if not comp:
                return self.send_error_json("Complaint not found", 404)

            officer_id = comp["assigned_officer_id"] or 1

            cursor = conn.cursor()
            # Insert or replace resolution evidence
            cursor.execute("""
                INSERT OR REPLACE INTO resolution_evidence (
                    complaint_id, officer_id, before_image_url, after_image_url,
                    resolution_summary, equipment_used, labor_hours, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (comp_id, officer_id, before_img, after_img, summary, equipment, hours))

            # Update Complaint to Resolved
            cursor.execute("""
                UPDATE complaints
                SET status = 'resolved', updated_at = CURRENT_TIMESTAMP, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (comp_id,))

            # Update Assignment
            cursor.execute("""
                UPDATE assignments SET status = 'completed' WHERE complaint_id = ? AND officer_id = ?
            """, (comp_id, officer_id))

            # Update Officer resolved count
            cursor.execute("""
                UPDATE officers SET total_resolved = total_resolved + 1 WHERE id = ?
            """, (officer_id,))

            # Status History
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, explanation)
                VALUES (?, 'in_progress', 'resolved', ?, 'officer', ?)
            """, (comp_id, user["id"], f"Remediation verified with photographic evidence: {summary}"))

            # Notify Citizen
            cursor.execute("""
                INSERT INTO notifications (user_id, complaint_id, title, message, type)
                VALUES (?, ?, 'Issue Resolved!', ?, 'success')
            """, (comp["user_id"], comp_id, f"Your complaint {comp['tracking_id']} has been officially resolved with verified photo evidence."))

            conn.commit()
            return self.send_json({"success": True, "message": "Resolution evidence submitted and complaint resolved."})
        finally:
            conn.close()

    def api_upload_file(self, body):
        """Accepts base64 encoded image or creates realistic SVG file on disk."""
        data_uri = body.get("data", "")
        file_name = body.get("filename", f"upload_{uuid.uuid4().hex[:8]}.svg")

        # Ensure upload dir exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_path = Path(UPLOAD_DIR) / file_name

        try:
            if data_uri.startswith("data:image"):
                # Decode base64
                header, base64_data = data_uri.split(",", 1)
                import base64
                file_bytes = base64.b64decode(base64_data)
                with open(safe_path, "wb") as f:
                    f.write(file_bytes)
            else:
                # Default SVG representation
                with open(safe_path, "w", encoding="utf-8") as f:
                    f.write(f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
                    <rect width="400" height="300" fill="#1e293b"/>
                    <text x="200" y="150" fill="#f8fafc" text-anchor="middle" font-family="sans-serif" font-weight="700">Uploaded Civic Photo: {file_name}</text>
                    </svg>""")

            url = f"/uploads/{file_name}"
            return self.send_json({"success": True, "url": url})
        except Exception as e:
            return self.send_error_json(f"File upload error: {str(e)}", 500)

    def api_get_kpis(self, query):
        """Calculates live dashboard KPIs directly from persistent SQLite records."""
        conn = get_db_connection()
        try:
            total_reports = conn.execute("SELECT COUNT(*) as c FROM complaints").fetchone()["c"]
            new_today = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE date(created_at) = date('now')").fetchone()["c"]
            pending = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE status IN ('submitted', 'ai_analyzed', 'under_review')").fetchone()["c"]
            critical = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE priority = 'critical' AND status NOT IN ('closed', 'resolved')").fetchone()["c"]
            active_assignments = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE status IN ('assigned', 'in_progress')").fetchone()["c"]
            resolved = conn.execute("SELECT COUNT(*) as c FROM complaints WHERE status IN ('resolved', 'closed')").fetchone()["c"]
            
            resolution_rate = round((resolved / total_reports * 100), 1) if total_reports > 0 else 0.0
            
            # Average resolution time in hours for resolved complaints
            avg_time_row = conn.execute("""
                SELECT AVG((julianday(resolved_at) - julianday(created_at)) * 24.0) as avg_hrs
                FROM complaints
                WHERE resolved_at IS NOT NULL
            """).fetchone()
            avg_res_time = round(avg_time_row["avg_hrs"], 1) if avg_time_row and avg_time_row["avg_hrs"] else 18.5

            return self.send_json({
                "success": True,
                "data": {
                    "total_reports": total_reports,
                    "new_reports_today": new_today,
                    "pending_reports": pending,
                    "critical_reports": critical,
                    "active_assignments": active_assignments,
                    "resolved_reports": resolved,
                    "resolution_rate_pct": resolution_rate,
                    "average_resolution_hours": avg_res_time
                }
            })
        finally:
            conn.close()

    def api_get_charts(self, query):
        """Computes chart datasets across categories, priorities, trends, departments, and wards."""
        days = int(query.get("days", [30])[0])
        conn = get_db_connection()
        try:
            # 1. By Category
            cat_rows = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM complaints
                GROUP BY category
                ORDER BY count DESC
            """).fetchall()
            by_category = [{"name": r["category"], "value": r["count"]} for r in cat_rows]

            # 2. By Priority
            pri_rows = conn.execute("""
                SELECT priority, COUNT(*) as count
                FROM complaints
                GROUP BY priority
            """).fetchall()
            by_priority = [{"priority": r["priority"], "count": r["count"]} for r in pri_rows]

            # 3. Weekly Trends
            trend_rows = conn.execute("""
                SELECT strftime('%Y-%W', created_at) as week, COUNT(*) as count
                FROM complaints
                GROUP BY week
                ORDER BY week ASC
                LIMIT 8
            """).fetchall()
            weekly_trends = [{"week": f"Week {r['week'].split('-')[-1]}", "reports": r["count"]} for r in trend_rows]

            # 4. Department Performance
            dept_rows = conn.execute("""
                SELECT d.name, d.code,
                       COUNT(c.id) as total,
                       SUM(CASE WHEN c.status IN ('resolved', 'closed') THEN 1 ELSE 0 END) as resolved
                FROM departments d
                LEFT JOIN complaints c ON d.id = c.department_id
                GROUP BY d.id
                ORDER BY total DESC
            """).fetchall()
            department_perf = [{
                "department": r["name"],
                "code": r["code"],
                "total": r["total"],
                "resolved": r["resolved"] or 0,
                "rate": round(((r["resolved"] or 0) / r["total"] * 100), 1) if r["total"] > 0 else 0
            } for r in dept_rows]

            # 5. Status Distribution
            status_rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM complaints
                GROUP BY status
            """).fetchall()
            status_dist = [{"status": r["status"].replace('_', ' ').title(), "count": r["count"]} for r in status_rows]

            # 6. Area / Ward Breakdown
            ward_rows = conn.execute("""
                SELECT l.ward, COUNT(*) as count
                FROM complaint_locations l
                JOIN complaints c ON l.complaint_id = c.id
                GROUP BY l.ward
                ORDER BY count DESC
            """).fetchall()
            ward_breakdown = [{"ward": r["ward"] or "Downtown", "count": r["count"]} for r in ward_rows]

            return self.send_json({
                "success": True,
                "data": {
                    "by_category": by_category,
                    "by_priority": by_priority,
                    "weekly_trends": weekly_trends,
                    "department_performance": department_perf,
                    "status_distribution": status_dist,
                    "ward_breakdown": ward_breakdown
                }
            })
        finally:
            conn.close()

    def api_get_activity_feed(self, query):
        """Recent administrative actions, status updates, and resolutions."""
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT h.*, c.tracking_id, c.title, u.full_name as user_name
                FROM status_history h
                JOIN complaints c ON h.complaint_id = c.id
                JOIN users u ON h.changed_by = u.id
                ORDER BY h.timestamp DESC
                LIMIT 25
            """).fetchall()
            return self.send_json({"success": True, "data": rows_to_list(rows)})
        finally:
            conn.close()

    def api_get_hotspots(self):
        """Fetches geographic clusters for map overlays."""
        conn = get_db_connection()
        try:
            rows = conn.execute("SELECT * FROM hotspot_clusters ORDER BY complaint_count DESC").fetchall()
            hotspots = rows_to_list(rows)
            for h in hotspots:
                if h.get("complaint_ids_json"):
                    try:
                        h["complaint_ids"] = json.loads(h["complaint_ids_json"])
                    except Exception:
                        h["complaint_ids"] = []
            return self.send_json({"success": True, "data": hotspots})
        finally:
            conn.close()

    def api_get_departments(self):
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT d.*, 
                       COUNT(c.id) as total_complaints,
                       SUM(CASE WHEN c.status IN ('resolved', 'closed') THEN 1 ELSE 0 END) as resolved_complaints
                FROM departments d
                LEFT JOIN complaints c ON d.id = c.department_id
                GROUP BY d.id
                ORDER BY d.id ASC
            """).fetchall()
            return self.send_json({"success": True, "data": rows_to_list(rows)})
        finally:
            conn.close()

    def api_get_officers(self, query):
        dept_id = query.get("department_id", [None])[0]
        conn = get_db_connection()
        try:
            sql = """
                SELECT o.*, u.full_name, u.email, u.phone, d.name as department_name, d.code as department_code,
                       (SELECT COUNT(*) FROM complaints c WHERE c.assigned_officer_id = o.id AND c.status IN ('assigned', 'in_progress')) as active_tasks
                FROM officers o
                JOIN users u ON o.user_id = u.id
                JOIN departments d ON o.department_id = d.id
            """
            params = []
            if dept_id and dept_id != "all":
                sql += " WHERE o.department_id = ?"
                params.append(int(dept_id))
            sql += " ORDER BY active_tasks ASC, u.full_name ASC"
            rows = conn.execute(sql, params).fetchall()
            return self.send_json({"success": True, "data": rows_to_list(rows)})
        finally:
            conn.close()

    def api_get_officer_tasks(self, user):
        """Fetches workload statistics and categorized tasks for the logged in field officer."""
        conn = get_db_connection()
        try:
            off_row = conn.execute("SELECT * FROM officers WHERE user_id = ?", (user["id"],)).fetchone()
            if not off_row:
                # If admin viewing, select first officer for convenience
                off_row = conn.execute("SELECT * FROM officers LIMIT 1").fetchone()
            
            officer_id = off_row["id"]
            
            # Fetch assigned complaints
            sql = """
                SELECT c.*, l.latitude, l.longitude, l.address, l.ward,
                       d.name as department_name, a.total_priority_score, a.action_brief
                FROM complaints c
                JOIN complaint_locations l ON c.id = l.complaint_id
                JOIN departments d ON c.department_id = d.id
                LEFT JOIN ai_analysis a ON c.id = a.complaint_id
                WHERE c.assigned_officer_id = ?
                ORDER BY CASE WHEN c.priority = 'critical' THEN 1 WHEN c.priority = 'high' THEN 2 ELSE 3 END, c.created_at DESC
            """
            rows = rows_to_list(conn.execute(sql, (officer_id,)).fetchall())

            assigned = [r for r in rows if r["status"] == "assigned"]
            in_progress = [r for r in rows if r["status"] == "in_progress"]
            critical = [r for r in rows if r["priority"] == "critical" and r["status"] not in ["resolved", "closed"]]
            completed = [r for r in rows if r["status"] in ["resolved", "closed"]]

            return self.send_json({
                "success": True,
                "officer": row_to_dict(off_row),
                "stats": {
                    "total_assigned": len(rows),
                    "pending_acceptance": len(assigned),
                    "in_progress": len(in_progress),
                    "critical": len(critical),
                    "completed": len(completed)
                },
                "tasks": {
                    "assigned": assigned,
                    "in_progress": in_progress,
                    "critical": critical,
                    "completed": completed
                }
            })
        finally:
            conn.close()

    def api_get_notifications(self, user):
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT * FROM notifications
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 50
            """, (user["id"],)).fetchall()
            unread_count = conn.execute("SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND is_read = 0", (user["id"],)).fetchone()["c"]
            return self.send_json({
                "success": True,
                "data": rows_to_list(rows),
                "unread_count": unread_count
            })
        finally:
            conn.close()

    def api_export_csv(self, query, user):
        """Generates downloadable CSV of complaints."""
        conn = get_db_connection()
        try:
            rows = conn.execute("""
                SELECT c.tracking_id, c.title, c.category, c.subcategory, c.priority, c.status,
                       d.name as department, l.address, l.ward, c.created_at, c.resolved_at
                FROM complaints c
                LEFT JOIN departments d ON c.department_id = d.id
                LEFT JOIN complaint_locations l ON c.id = l.complaint_id
                ORDER BY c.created_at DESC
            """).fetchall()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Tracking ID", "Title", "Category", "Subcategory", "Priority", "Status", "Department", "Address", "Ward", "Created At", "Resolved At"])
            for r in rows:
                writer.writerow([r["tracking_id"], r["title"], r["category"], r["subcategory"], r["priority"], r["status"], r["department"], r["address"], r["ward"], r["created_at"], r["resolved_at"]])

            csv_data = output.getvalue().encode('utf-8')
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=civicai_complaints_export.csv")
            self.send_header("Content-Length", str(len(csv_data)))
            self.end_headers()
            self.wfile.write(csv_data)
        finally:
            conn.close()

    # -------------------------------------------------------------
    # Static File Server
    # -------------------------------------------------------------
    def handle_static_file(self, path):
        """Serves HTML, CSS, JS, and image assets securely."""
        if path == "/" or path == "":
            path = "/index.html"

        # Determine target file
        if path.startswith("/uploads/"):
            target = Path(BASE_DIR) / path.lstrip("/")
        elif path.startswith("/css/") or path.startswith("/js/") or path.startswith("/assets/"):
            target = Path(BASE_DIR) / "frontend" / path.lstrip("/")
        else:
            target = Path(BASE_DIR) / "frontend" / path.lstrip("/")

        # Security check: prevent directory traversal
        try:
            resolved = target.resolve()
            if not str(resolved).startswith(str(BASE_DIR)):
                return self.send_error_json("Access Denied", 403)
        except Exception:
            return self.send_error_json("Invalid path", 400)

        if not resolved.exists() or resolved.is_dir():
            # Fallback to index.html for Single Page Application routing
            fallback = Path(BASE_DIR) / "frontend" / "index.html"
            if fallback.exists():
                resolved = fallback
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not Found")
                return

        mime_type, _ = mimetypes.guess_type(str(resolved))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(resolved, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error_json(f"File read error: {e}", 500)

def run_server():
    """Starts the CivicAI REST Server."""
    print("=" * 70)
    print(" CIVICAI - PROFESSIONAL AI-POWERED SMART CIVIC MANAGEMENT PLATFORM")
    print(" Smart Cities. Smarter Decisions. Faster Resolutions.")
    print("=" * 70)
    print(f"-> Local Address: http://localhost:{PORT}")
    print(f"-> Network Address: http://127.0.0.1:{PORT}")
    print(f"-> Database File: {Path(BASE_DIR) / 'backend' / 'civicai.db'}")
    print(f"-> Multi-threaded HTTP Server running on port {PORT}...")
    print("=" * 70)

    server = ThreadingHTTPServer((HOST, PORT), CivicAIRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CivicAI server gracefully...")
        server.server_close()

if __name__ == "__main__":
    run_server()
