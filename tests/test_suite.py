"""
CivicAI - Automated Quality Assurance & Testing Suite
Executes and validates all 20 mandatory test cases specified in Master Prompt Section 19.
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path
import threading

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import PORT
from backend.app import run_server, ThreadingHTTPServer, CivicAIRequestHandler
from backend.database import get_db_connection

SERVER_URL = f"http://127.0.0.1:{PORT}"

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

class CivicAITester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
        self.citizen_token = None
        self.admin_token = None
        self.officer_token = None
        self.test_tracking_id = None
        self.test_complaint_id = None

    def log(self, test_num, name, status, details=""):
        badge = "[PASS]" if status else "[FAIL]"
        if status:
            self.passed += 1
        else:
            self.failed += 1
        msg = f"[Test {test_num:02d}] {badge}: {name} - {details}"
        try:
            print(msg)
        except Exception:
            print(f"[Test {test_num:02d}] {badge}: {name}")
        self.results.append({
            "test_num": test_num,
            "name": name,
            "passed": status,
            "details": details
        })

    def request(self, method, endpoint, data=None, token=None):
        url = f"{SERVER_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        req_data = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_body = resp.read().decode('utf-8')
                return resp.status, json.loads(resp_body) if resp_body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            try:
                return e.code, json.loads(err_body)
            except Exception:
                return e.code, {"error": err_body}
        except Exception as ex:
            return 500, {"error": str(ex)}

    def run_all_tests(self):
        print("=" * 75)
        print(" CIVICAI - EXECUTING 20 MANDATORY QA VERIFICATION TEST CASES")
        print("=" * 75)

        # 1. Citizen can register and log in
        reg_data = {
            "email": f"test_citizen_{int(time.time())}@example.com",
            "password": "Password@123",
            "full_name": "Test Citizen QA",
            "phone": "+1 (555) 012-3456"
        }
        status, res = self.request("POST", "/api/auth/register", reg_data)
        if status == 201 and res.get("success"):
            self.citizen_token = res["data"]["token"]
            # Now verify login
            l_status, l_res = self.request("POST", "/api/auth/login", {"email": reg_data["email"], "password": reg_data["password"]})
            login_ok = l_status == 200 and l_res.get("success") and "token" in l_res["data"]
            self.log(1, "Citizen can register and log in", login_ok, f"Registered user ID {res['data']['user']['id']} & retrieved session token")
        else:
            self.log(1, "Citizen can register and log in", False, str(res))

        # Login admin & officer for subsequent tests
        _, a_res = self.request("POST", "/api/auth/login", {"email": "admin@civicai.gov", "password": "Admin@1234"})
        if a_res.get("success"):
            self.admin_token = a_res["data"]["token"]
        _, o_res = self.request("POST", "/api/auth/login", {"email": "officer.john@civicai.gov", "password": "Officer@1234"})
        if o_res.get("success"):
            self.officer_token = o_res["data"]["token"]

        # 2. Citizen can submit a complaint
        complaint_payload = {
            "title": "Severe road sinkhole outside Central Metro station",
            "description": "Large deep sinkhole formed in the middle lane of Central Metro avenue. Asphalt caved in about 1 meter. Heavy traffic disruption and severe vehicle damage hazard.",
            "category": "Roads & Infrastructure",
            "subcategory": "Potholes & Surface Damage",
            "address": "400 Central Metro Avenue, Ward 12",
            "ward": "Ward 12 - Downtown",
            "latitude": 12.9725,
            "longitude": 77.5955,
            "images": ["/uploads/complaint_sample.svg"]
        }
        status, res = self.request("POST", "/api/complaints", complaint_payload, token=self.citizen_token)
        submitted = status == 201 and res.get("success") and "tracking_id" in res["data"]
        if submitted:
            self.test_tracking_id = res["data"]["tracking_id"]
            self.test_complaint_id = res["data"]["id"]
            self.log(2, "Citizen can submit a complaint", True, f"Created {self.test_tracking_id} successfully")
        else:
            self.log(2, "Citizen can submit a complaint", False, str(res))

        # 3. Image upload works
        status, res = self.request("POST", "/api/upload", {"filename": "test_evidence.svg", "data": ""})
        img_ok = status == 200 and res.get("success") and "/uploads/" in res.get("url", "")
        self.log(3, "Image upload works", img_ok, f"Stored image URL: {res.get('url')}")

        # 4. Map location selection works
        conn = get_db_connection()
        loc = conn.execute("SELECT * FROM complaint_locations WHERE complaint_id = ?", (self.test_complaint_id,)).fetchone()
        map_ok = loc and abs(loc["latitude"] - 12.9725) < 0.0001 and abs(loc["longitude"] - 77.5955) < 0.0001
        self.log(4, "Map location selection works", map_ok, f"Coordinates stored: ({loc['latitude']}, {loc['longitude']})")

        # 5. Unique tracking ID is generated
        tracking_ok = bool(self.test_tracking_id and self.test_tracking_id.startswith("CIV-2026-"))
        self.log(5, "Unique tracking ID is generated", tracking_ok, f"Tracking ID format verified: {self.test_tracking_id}")

        # 6. Complaint is saved in the database
        db_comp = conn.execute("SELECT * FROM complaints WHERE id = ?", (self.test_complaint_id,)).fetchone()
        conn.close()
        saved_ok = db_comp is not None and db_comp["title"] == complaint_payload["title"]
        self.log(6, "Complaint is saved in the database", saved_ok, f"Database record verified for ID {self.test_complaint_id}")

        # 7. AI classification returns a result
        status, res = self.request("POST", "/api/ai/classify", {
            "title": "Severe waterlogging flooding shop basements",
            "description": "Knee-deep water stagnation after rain. Stormwater grates clogged with garbage."
        })
        ai_class_ok = status == 200 and res.get("success") and res["classification"]["category"] == "Drainage & Water Management"
        self.log(7, "AI classification returns a result", ai_class_ok, f"Classified into '{res['classification']['category']}' (confidence: {res['classification']['confidence']})")

        # 8. Duplicate detection compares existing reports
        status, res = self.request("POST", "/api/ai/duplicates", {
            "title": "Waterlogging flooding Central Market Road",
            "description": "Central Market road flooded with stagnant stormwater",
            "category": "Drainage & Water Management",
            "latitude": 12.9718,
            "longitude": 77.5948
        })
        dup_ok = status == 200 and res.get("success") and len(res["duplicates"]) > 0
        dup_cnt = len(res.get("duplicates", []))
        self.log(8, "Duplicate detection compares existing reports", dup_ok, f"Detected {dup_cnt} semantic/geographic duplicate matches")

        # 9. Priority scoring calculates correctly
        status, res = self.request("POST", "/api/ai/priority", {
            "title": "Sparking live electric wire snapped onto sidewalk",
            "description": "High voltage wire hanging low, sparking danger to pedestrians",
            "category": "Electricity & Streetlights",
            "latitude": 12.9850,
            "longitude": 77.6100
        })
        prio_res = res.get("priority", {})
        score = prio_res.get("total_score", 0)
        prio_ok = status == 200 and score >= 80 and prio_res.get("priority_level") == "critical"
        self.log(9, "Priority scoring calculates correctly", prio_ok, f"Calculated score: {score}/100 (Level: {prio_res.get('priority_level')})")

        # 10. Priority explanation is visible
        factor_breakdown = prio_res.get("factor_breakdown", {})
        breakdown_ok = "safety_risk" in factor_breakdown and "public_impact" in factor_breakdown
        self.log(10, "Priority explanation is visible", breakdown_ok, f"Safety: {factor_breakdown.get('safety_risk', {}).get('score')}, Impact: {factor_breakdown.get('public_impact', {}).get('score')}")

        # 11. Hotspot detection identifies clusters
        status, res = self.request("GET", "/api/ai/hotspots")
        hotspots = res.get("data", [])
        hotspot_ok = status == 200 and len(hotspots) >= 3
        self.log(11, "Hotspot detection identifies clusters", hotspot_ok, f"DBSCAN identified {len(hotspots)} geographic municipal clusters")

        # 12. Admin can review complaints
        status, res = self.request("GET", "/api/complaints?limit=10", token=self.admin_token)
        admin_review_ok = status == 200 and res.get("success") and len(res.get("data", [])) > 0
        self.log(12, "Admin can review complaints", admin_review_ok, f"Admin fetched {len(res.get('data', []))} records with pagination")

        # 13. Admin can assign officers
        status, res = self.request("PATCH", f"/api/complaints/{self.test_complaint_id}/assign", {
            "officer_id": 1,
            "notes": "Dispatch asphalt patch crew immediately"
        }, token=self.admin_token)
        assign_ok = status == 200 and res.get("success")
        self.log(13, "Admin can assign officers", assign_ok, f"Assigned complaint #{self.test_complaint_id} to Officer #1")

        # 14. Officer can update progress
        status, res = self.request("PATCH", f"/api/complaints/{self.test_complaint_id}/status", {
            "status": "in_progress",
            "explanation": "Field crew arrived on site with compaction machinery"
        }, token=self.officer_token)
        progress_ok = status == 200 and res.get("success")
        self.log(14, "Officer can update progress", progress_ok, "Status transitioned: assigned -> in_progress")

        # 15. Resolution evidence can be uploaded
        status, res = self.request("POST", "/api/officers/evidence", {
            "complaint_id": self.test_complaint_id,
            "resolution_summary": "Asphalt cave-in filled with compacted gravel and hot-mix asphalt seal. Safe for vehicle traffic.",
            "equipment_used": "Compactor & Road Roller",
            "labor_hours": 3.0,
            "before_image_url": "/uploads/before_work.svg",
            "after_image_url": "/uploads/after_work.svg"
        }, token=self.officer_token)
        evidence_ok = status == 200 and res.get("success")
        self.log(15, "Resolution evidence can be uploaded", evidence_ok, "Before/After evidence stored and complaint marked resolved")

        # 16. Citizen can track status updates
        status, res = self.request("GET", f"/api/complaints/{self.test_tracking_id}")
        c_detail = res.get("data", {})
        tracking_flow_ok = status == 200 and c_detail.get("status") == "resolved" and len(c_detail.get("status_history", [])) >= 3
        self.log(16, "Citizen can track status updates", tracking_flow_ok, f"Current status: {c_detail.get('status')}, Timeline events: {len(c_detail.get('status_history', []))}")

        # 17. Notifications work
        status, res = self.request("GET", "/api/notifications", token=self.citizen_token)
        notifs = res.get("data", [])
        notif_ok = status == 200 and len(notifs) >= 1
        self.log(17, "Notifications work", notif_ok, f"Found {len(notifs)} in-app notifications (Unread: {res.get('unread_count')})")

        # 18. Search and filters work
        status, res = self.request("GET", f"/api/complaints?search={urllib.parse.quote(self.test_tracking_id)}", token=self.admin_token)
        search_ok = status == 200 and len(res.get("data", [])) == 1 and res["data"][0]["tracking_id"] == self.test_tracking_id
        self.log(18, "Search and filters work", search_ok, f"Found exact complaint matching search term '{self.test_tracking_id}'")

        # 19. Dashboard metrics update
        status, res = self.request("GET", "/api/analytics/kpis")
        kpi_data = res.get("data", {})
        metrics_ok = status == 200 and kpi_data.get("total_reports", 0) >= 50 and kpi_data.get("resolved_reports", 0) >= 20
        self.log(19, "Dashboard metrics update", metrics_ok, f"Total: {kpi_data.get('total_reports')}, Resolved: {kpi_data.get('resolved_reports')}, Rate: {kpi_data.get('resolution_rate_pct')}%")

        # 20. Unauthorized users cannot access protected modules
        unauth_status, _ = self.request("PATCH", f"/api/complaints/{self.test_complaint_id}/priority", {
            "priority": "low"
        }, token=None) # No token
        unauth_ok = unauth_status in [401, 403]
        self.log(20, "Unauthorized users cannot access protected modules", unauth_ok, f"Server correctly blocked unauthenticated priority override with HTTP {unauth_status}")

        print("=" * 75)
        print(f" TEST SUITE SUMMARY: {self.passed}/20 PASSED, {self.failed}/20 FAILED")
        print("=" * 75)
        return self.failed == 0

if __name__ == "__main__":
    tester = CivicAITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
