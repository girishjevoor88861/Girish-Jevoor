"""
CivicAI - Authentication & Security Module
Handles password hashing (PBKDF2-HMAC-SHA256), secure bearer tokens, session verification, and role-based access control (RBAC).
"""

import hashlib
import hmac
import base64
import json
import time
import secrets
from backend.config import SECRET_KEY, SESSION_EXPIRE_HOURS
from backend.database import get_db_connection, row_to_dict

def hash_password(password: str) -> str:
    """Generate a secure PBKDF2 salt and hash string."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    return f"pbkdf2:sha256:{iterations}${salt}${hash_bytes.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against the PBKDF2 hash string."""
    try:
        parts = hashed.split("$")
        if len(parts) != 3:
            return False
        meta, salt, stored_hash = parts
        iterations = int(meta.split(":")[-1])
        calculated_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        ).hex()
        return hmac.compare_digest(stored_hash, calculated_hash)
    except Exception:
        return False

def generate_token(user_id: int, email: str, role: str) -> str:
    """Creates a cryptographically signed session token with expiry."""
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": int(time.time()) + (SESSION_EXPIRE_HOURS * 3600),
        "nonce": secrets.token_hex(8)
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip('=')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"

def verify_token(token: str):
    """Verifies cryptographic signature and expiry of the session token. Returns payload dict or None."""
    if not token or "." not in token:
        return None
    try:
        payload_b64, signature = token.split(".", 1)
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Add padding back if necessary
        pad = len(payload_b64) % 4
        if pad:
            payload_b64 += '=' * (4 - pad)
        
        payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        
        if payload.get("exp", 0) < time.time():
            return None # Expired
        
        return payload
    except Exception:
        return None

def authenticate_user(email: str, password: str):
    """Authenticate email and password against users table."""
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email.strip().lower(),)).fetchone()
        if not user:
            return None, "Invalid email or password"
        user_dict = row_to_dict(user)
        if not verify_password(password, user_dict["password_hash"]):
            return None, "Invalid email or password"
        
        # Include officer details if role is officer
        officer_info = None
        if user_dict["role"] == "officer":
            off = conn.execute("""
                SELECT o.*, d.name as department_name, d.code as department_code 
                FROM officers o 
                JOIN departments d ON o.department_id = d.id 
                WHERE o.user_id = ?
            """, (user_dict["id"],)).fetchone()
            if off:
                officer_info = row_to_dict(off)
                
        user_dict.pop("password_hash", None)
        user_dict["officer_info"] = officer_info
        token = generate_token(user_dict["id"], user_dict["email"], user_dict["role"])
        return {"user": user_dict, "token": token}, None
    finally:
        conn.close()

def register_citizen(email: str, password: str, full_name: str, phone: str = ""):
    """Register a new citizen with encrypted password."""
    email = email.strip().lower()
    if not email or "@" not in email:
        return None, "Valid email address is required"
    if len(password) < 6:
        return None, "Password must be at least 6 characters"
    if not full_name.strip():
        return None, "Full name is required"

    conn = get_db_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return None, "An account with this email already exists"

        hashed = hash_password(password)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (email, password_hash, role, full_name, phone)
            VALUES (?, ?, 'citizen', ?, ?)
        """, (email, hashed, full_name.strip(), phone.strip()))
        user_id = cursor.lastrowid

        # Create basic profile
        cursor.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
        
        # Create welcome notification
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type)
            VALUES (?, 'Welcome to CivicAI', 'Your citizen account has been successfully created. You can now report civic issues, track resolutions in real-time, and help improve your city.', 'success')
        """, (user_id,))

        # Log audit
        cursor.execute("""
            INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
            VALUES (?, 'REGISTER', 'USER', ?, 'Citizen registered account')
        """, (user_id, str(user_id)))

        conn.commit()

        user = conn.execute("SELECT id, email, role, full_name, phone, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        user_dict = row_to_dict(user)
        token = generate_token(user_dict["id"], user_dict["email"], user_dict["role"])
        return {"user": user_dict, "token": token}, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()

def get_current_user_from_token(token: str):
    """Retrieve user record from database based on validated token."""
    payload = verify_token(token)
    if not payload:
        return None
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT id, email, role, full_name, phone, is_active, created_at FROM users WHERE id = ?", (payload["sub"],)).fetchone()
        if not user or user["is_active"] != 1:
            return None
        user_dict = row_to_dict(user)
        
        if user_dict["role"] == "officer":
            off = conn.execute("""
                SELECT o.*, d.name as department_name, d.code as department_code 
                FROM officers o 
                JOIN departments d ON o.department_id = d.id 
                WHERE o.user_id = ?
            """, (user_dict["id"],)).fetchone()
            if off:
                user_dict["officer_info"] = row_to_dict(off)
                
        return user_dict
    finally:
        conn.close()
