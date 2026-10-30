"""
CivicAI - Enterprise Configuration Module
Configuration settings for CivicAI Smart Civic Management Platform.
"""

import os
import shutil
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

# Vercel and Serverless environment support: only /tmp is writable
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or not os.access(BACKEND_DIR, os.W_OK):
    DATABASE_PATH = "/tmp/civicai.db"
    UPLOAD_DIR = "/tmp/uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    source_db = BACKEND_DIR / "civicai.db"
    if source_db.exists() and not os.path.exists(DATABASE_PATH):
        try:
            shutil.copyfile(str(source_db), DATABASE_PATH)
        except Exception:
            pass
else:
    DATABASE_PATH = str(BACKEND_DIR / "civicai.db")
    UPLOAD_DIR = str(BASE_DIR / "uploads")

# Server settings
HOST = "0.0.0.0"
PORT = 8000

# Security
SECRET_KEY = os.environ.get("CIVICAI_SECRET_KEY", "civicai_super_secret_jwt_key_2026_enterprise_civic_platform")
SESSION_EXPIRE_HOURS = 72

# AI Engine Scoring Weights (Configurable)
# Must sum to 1.0 (Safety: 30%, Public Impact: 25%, Urgency: 20%, Concentration: 15%, Frequency: 10%)
PRIORITY_WEIGHTS = {
    "safety_risk": 0.30,
    "public_impact": 0.25,
    "urgency": 0.20,
    "geographic_concentration": 0.15,
    "report_frequency": 0.10
}

# Priority Thresholds
PRIORITY_THRESHOLDS = {
    "critical": 80,
    "high": 60,
    "medium": 35,
    "low": 0
}

# Duplicate Detection Settings
DUPLICATE_CONFIG = {
    "max_distance_meters": 350.0,
    "time_window_days": 60,
    "similarity_threshold_potential": 0.45,
    "similarity_threshold_high": 0.75
}

# Hotspot Clustering Settings
HOTSPOT_CONFIG = {
    "eps_km": 0.65,         # Clustering neighborhood radius in km
    "min_samples": 3        # Minimum complaints to form a municipal cluster
}

# Default City Center (Metro Civic Center)
CITY_CENTER = {
    "latitude": 12.971598,
    "longitude": 77.594566,
    "city_name": "Metro Civic City"
}
