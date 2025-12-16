"""
Vercel serverless function entry point for Flask app
"""
import sys
import os
import traceback

# Add parent directory to path to import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set Vercel environment variables
os.environ['VERCEL_ENV'] = '1'
os.environ['VERCEL'] = '1'

try:
    # Import app - this should not fail
    print("Importing Flask app...")
    from app import app, ensure_db_initialized
    print("Flask app imported successfully")
    
    # Add before_request hook to initialize database on first request
    @app.before_request
    def init_database_before_request():
        """Ensure database is initialized before each request"""
        try:
            ensure_db_initialized()
        except Exception as e:
            print(f"Database init error in before_request: {e}")
            # Don't fail the request, just log
    
    # Try to initialize immediately (non-blocking)
    try:
        ensure_db_initialized()
        print("Database initialization attempted")
    except Exception as e:
        print(f"Initial DB init failed (will retry on request): {e}")
        # Will initialize on first request via before_request hook
    
    # Export the Flask app for Vercel
    # Vercel expects a WSGI application
    handler = app
    print("Handler exported successfully")
    
except ImportError as e:
    # Import error - show helpful message
    error_msg = f"Import Error: {str(e)}"
    error_trace = traceback.format_exc()
    print(f"CRITICAL: {error_msg}")
    print(error_trace)
    
    # Create minimal error handler
    try:
        from flask import Flask, Response
        error_app = Flask(__name__)
        
        @error_app.route('/', defaults={'path': ''})
        @error_app.route('/<path:path>')
        def error_handler(path):
            return Response(
                f"<h1>500 Internal Server Error</h1>"
                f"<h2>Import Error</h2>"
                f"<p><strong>{error_msg}</strong></p>"
                f"<pre style='background:#f5f5f5;padding:20px;overflow:auto;'>{error_trace}</pre>"
                f"<p>Check Vercel function logs for details.</p>",
                status=500,
                mimetype='text/html'
            )
        
        handler = error_app
    except:
        # Last resort - create a simple handler
        def handler(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-type', 'text/html')]
            body = f"<h1>500 Error</h1><p>{error_msg}</p>"
            start_response(status, headers)
            return [body.encode()]

except Exception as e:
    # Any other error
    error_msg = f"Unexpected Error: {str(e)}"
    error_trace = traceback.format_exc()
    print(f"CRITICAL: {error_msg}")
    print(error_trace)
    
    # Try to create error handler
    try:
        from flask import Flask, Response
        error_app = Flask(__name__)
        
        @error_app.route('/', defaults={'path': ''})
        @error_app.route('/<path:path>')
        def error_handler(path):
            return Response(
                f"<h1>500 Internal Server Error</h1>"
                f"<h2>Unexpected Error</h2>"
                f"<p><strong>{error_msg}</strong></p>"
                f"<pre style='background:#f5f5f5;padding:20px;overflow:auto;'>{error_trace}</pre>",
                status=500,
                mimetype='text/html'
            )
        
        handler = error_app
    except:
        def handler(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-type', 'text/html')]
            body = f"<h1>500 Error</h1><p>{error_msg}</p>"
            start_response(status, headers)
            return [body.encode()]
