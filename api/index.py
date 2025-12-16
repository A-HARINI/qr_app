"""
Vercel serverless function - Flask app entry point
Official Vercel Flask pattern
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app
from app import app, ensure_db_initialized

# Initialize database on first request
@app.before_request
def init_database():
    try:
        ensure_db_initialized()
    except Exception:
        pass

# Global exception handler
@app.errorhandler(Exception)
def handle_exceptions(e):
    from flask import jsonify
    return jsonify({'error': 'Internal server error'}), 500

# Export Flask app directly - Vercel's official pattern
# Vercel auto-detects Flask apps and handles them correctly
handler = app
