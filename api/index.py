"""
CivicAI - Vercel Serverless Function Entrypoint
Routes all /api/* requests to the CivicAI REST API handler.
"""

import sys
from pathlib import Path

# Add project root to sys.path so backend imports work seamlessly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import CivicAIRequestHandler

class handler(CivicAIRequestHandler):
    """Vercel Python serverless handler class."""
    pass
