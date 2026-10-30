"""
CivicAI - Relational Database Management
SQLite database with full relational schema, foreign key enforcement, indexes, and connection helpers.
"""

import sqlite3
import os
import json
from contextlib import contextmanager
from backend.config import DATABASE_PATH

def get_db_connection():
    """Returns a SQLite connection with row_factory set to sqlite3.Row and foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def db_session():
    """Context manager for automatic commit and rollback."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def row_to_dict(row):
    """Convert a sqlite3.Row to a standard python dict."""
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}

def rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [row_to_dict(r) for r in rows]

def init_db(force_recreate=False):
    """Initializes the database schema with all required tables, constraints, and indexes."""
    if force_recreate and os.path.exists(DATABASE_PATH):
        try:
            os.remove(DATABASE_PATH)
        except Exception as e:
            print(f"Warning: could not remove DB file: {e}")

    with db_session() as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('citizen', 'admin', 'officer')),
            full_name TEXT NOT NULL,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Profiles Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            avatar_url TEXT,
            department_id INTEGER,
            badge_number TEXT,
            address TEXT,
            emergency_contact TEXT,
            bio TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
        );
        """)

        # 3. Departments Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL,
            description TEXT,
            contact_email TEXT,
            head_name TEXT,
            active_officers_count INTEGER DEFAULT 0,
            sla_hours INTEGER DEFAULT 48,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 4. Officers Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            department_id INTEGER NOT NULL,
            badge_number TEXT UNIQUE NOT NULL,
            rank TEXT DEFAULT 'Field Inspector',
            status TEXT DEFAULT 'available' CHECK(status IN ('available', 'on_field', 'off_duty')),
            total_assigned INTEGER DEFAULT 0,
            total_resolved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT
        );
        """)

        # 5. Complaints Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('critical', 'high', 'medium', 'low')),
            status TEXT DEFAULT 'submitted' CHECK(status IN (
                'submitted', 'ai_analyzed', 'under_review', 'assigned', 
                'in_progress', 'resolved', 'closed', 'reopened', 
                'rejected', 'more_info_required', 'duplicate_linked'
            )),
            department_id INTEGER,
            assigned_officer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            public_notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_officer_id) REFERENCES officers(id) ON DELETE SET NULL
        );
        """)

        # 6. Complaint Images Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            image_type TEXT DEFAULT 'report' CHECK(image_type IN ('report', 'before', 'after')),
            caption TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
        );
        """)

        # 7. Complaint Locations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaint_locations (
            complaint_id INTEGER PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            address TEXT NOT NULL,
            landmark TEXT,
            ward TEXT,
            postal_code TEXT,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
        );
        """)

        # 8. AI Analysis Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER UNIQUE NOT NULL,
            category TEXT,
            subcategory TEXT,
            department TEXT,
            short_summary TEXT,
            keywords TEXT,
            urgency TEXT,
            confidence REAL DEFAULT 0.0,
            safety_score REAL DEFAULT 0.0,
            public_impact_score REAL DEFAULT 0.0,
            urgency_score REAL DEFAULT 0.0,
            concentration_score REAL DEFAULT 0.0,
            frequency_score REAL DEFAULT 0.0,
            total_priority_score REAL DEFAULT 0.0,
            priority_level TEXT,
            action_brief TEXT,
            human_reviewed INTEGER DEFAULT 0,
            reviewed_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
        );
        """)

        # 9. Duplicate Matches Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS duplicate_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            primary_complaint_id INTEGER NOT NULL,
            duplicate_complaint_id INTEGER NOT NULL,
            similarity_score REAL NOT NULL,
            geo_distance_m REAL NOT NULL,
            status TEXT DEFAULT 'potential' CHECK(status IN ('potential', 'confirmed', 'rejected')),
            explanation TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (primary_complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (duplicate_complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
        );
        """)

        # 10. Hotspot Clusters Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotspot_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_name TEXT NOT NULL,
            center_lat REAL NOT NULL,
            center_lng REAL NOT NULL,
            radius_km REAL NOT NULL,
            complaint_count INTEGER DEFAULT 0,
            dominant_category TEXT,
            severity_level TEXT,
            complaint_ids_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 11. Assignments Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            officer_id INTEGER NOT NULL,
            assigned_by INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'in_progress', 'completed', 'reassigned')),
            notes TEXT,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE RESTRICT,
            FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)

        # 12. Status History Table (Audit Trail)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            previous_status TEXT,
            new_status TEXT NOT NULL,
            changed_by INTEGER NOT NULL,
            user_role TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            explanation TEXT,
            is_public INTEGER DEFAULT 1,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)

        # 13. Internal Notes Table (Admin/Officer only)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS internal_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            note_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)

        # 14. Public Updates Table (Citizen visible)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS public_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            update_type TEXT DEFAULT 'status_change',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)

        # 15. Notifications Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            complaint_id INTEGER,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE SET NULL
        );
        """)

        # 16. Resolution Evidence Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resolution_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER UNIQUE NOT NULL,
            officer_id INTEGER NOT NULL,
            before_image_url TEXT,
            after_image_url TEXT,
            resolution_summary TEXT NOT NULL,
            equipment_used TEXT,
            labor_hours REAL DEFAULT 0.0,
            resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE RESTRICT
        );
        """)

        # 17. Citizen Feedback Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS citizen_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comments TEXT,
            reopen_requested INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
        );
        """)

        # 18. Audit Logs Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """)

        # Create Indexes for High Performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_tracking ON complaints(tracking_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_priority ON complaints(priority);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_department ON complaints(department_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_user ON complaints(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_created ON complaints(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_lat_lng ON complaint_locations(latitude, longitude);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_history_comp ON status_history(complaint_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);")

        conn.commit()
    print("CivicAI Database initialized successfully with all 18 relational tables and indexes.")

if __name__ == "__main__":
    init_db()
