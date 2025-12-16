"""
Vercel serverless function entry point for Flask app
Workaround for Vercel's issubclass() inspection issue
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

# Create a WSGI wrapper class that Vercel can properly inspect
# This workaround fixes the issubclass() error in Vercel's handler
class VercelFlaskWrapper:
    """Wrapper class to fix Vercel's issubclass() inspection issue"""
    def __init__(self, flask_app):
        self.app = flask_app
    
    def __call__(self, environ, start_response):
        """WSGI interface - delegate to Flask app"""
        return self.app(environ, start_response)
    
    # Make this class look like Flask for Vercel's inspection
    def __getattr__(self, name):
        """Delegate attribute access to Flask app"""
        return getattr(self.app, name)

# Export wrapped handler - this should pass Vercel's issubclass() check
handler = VercelFlaskWrapper(app)
