"""
Vercel serverless function entry point for Flask app
Using Flask's wsgi_app directly to avoid Vercel's issubclass() inspection issue
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set Vercel environment
os.environ.setdefault('VERCEL_ENV', '1')
os.environ.setdefault('VERCEL', '1')

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

# Export Flask's wsgi_app directly - this is the actual WSGI callable
# This avoids Vercel's issubclass() inspection of the Flask app class
handler = app.wsgi_app
