"""
Vercel serverless function entry point for Flask app
Direct Flask app export - simplest possible approach
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

# CRITICAL FIX: Export Flask app's __call__ method directly
# This creates a bound method that Vercel should handle correctly
# The bound method's class is types.MethodType, not Flask, so issubclass() won't fail
import types
handler = types.MethodType(app.__call__, app)
