"""
Vercel serverless function entry point for Flask app
"""
import sys
import os
import traceback

# Add parent directory to path to import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Set Vercel environment
os.environ['VERCEL_ENV'] = '1'

try:
    # Import app
    from app import app, init_db
    
    # Initialize database (for Vercel serverless)
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database init warning (non-fatal): {e}")
        import traceback
        traceback.print_exc()
    
    # Export the Flask app for Vercel
    # Vercel expects a WSGI application
    handler = app
    
except Exception as e:
    # Error handler for import failures - show detailed error
    error_msg = f"Failed to import app: {str(e)}"
    error_trace = traceback.format_exc()
    full_error = f"{error_msg}\n\n{error_trace}"
    print(full_error)
    
    # Create a minimal error handler that shows the error
    from flask import Flask, Response
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return Response(
            f"<h1>500 Internal Server Error</h1>"
            f"<h2>Import Error</h2>"
            f"<pre style='background:#f5f5f5;padding:20px;overflow:auto;'>{full_error}</pre>"
            f"<p><strong>Check Vercel logs for more details.</strong></p>",
            status=500,
            mimetype='text/html'
        )
    
    handler = error_app
