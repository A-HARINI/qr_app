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

# Set Vercel environment variables (check if already set to avoid overwriting)
if not os.environ.get('VERCEL_ENV'):
    os.environ['VERCEL_ENV'] = '1'
if not os.environ.get('VERCEL'):
    os.environ['VERCEL'] = '1'

# Initialize handler variable to None (will be set below)
handler = None

try:
    # Import app - this should not fail
    print("=== VERCEL FUNCTION INITIALIZATION ===")
    print("Importing Flask app...")
    from app import app, ensure_db_initialized
    print("✓ Flask app imported successfully")
    
    # Add before_request hook to initialize database on first request
    @app.before_request
    def init_database_before_request():
        """Ensure database is initialized before each request"""
        try:
            ensure_db_initialized()
        except Exception as e:
            print(f"⚠ Database init error in before_request: {e}")
            traceback.print_exc()
            # Don't fail the request, just log - database will be created on first use
    
    # Try to initialize immediately (non-blocking)
    try:
        print("Attempting database initialization...")
        ensure_db_initialized()
        print("✓ Database initialization completed")
    except Exception as e:
        print(f"⚠ Initial DB init failed (will retry on request): {e}")
        traceback.print_exc()
        # Will initialize on first request via before_request hook
    
    # Export the Flask app for Vercel
    # Vercel's @vercel/python builder expects a WSGI application
    # The Flask app IS a WSGI application, so we can export it directly
    handler = app
    print("✓ Handler exported successfully")
    print("=== INITIALIZATION COMPLETE ===")
    
except ImportError as e:
    # Import error - show helpful message
    error_msg = f"Import Error: {str(e)}"
    error_trace = traceback.format_exc()
    print(f"❌ CRITICAL IMPORT ERROR: {error_msg}")
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
        print("✓ Error handler created (Import Error)")
    except Exception as fallback_error:
        print(f"❌ Failed to create error handler: {fallback_error}")
        traceback.print_exc()
        # Last resort - create a simple WSGI handler
        def fallback_handler(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-type', 'text/html')]
            body = f"<h1>500 Error</h1><p>{error_msg}</p><pre>{error_trace}</pre>"
            start_response(status, headers)
            return [body.encode()]
        handler = fallback_handler

except Exception as e:
    # Any other error during initialization
    error_msg = f"Unexpected Error: {str(e)}"
    error_trace = traceback.format_exc()
    print(f"❌ CRITICAL UNEXPECTED ERROR: {error_msg}")
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
        print("✓ Error handler created (Unexpected Error)")
    except Exception as fallback_error:
        print(f"❌ Failed to create error handler: {fallback_error}")
        traceback.print_exc()
        def fallback_handler(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-type', 'text/html')]
            body = f"<h1>500 Error</h1><p>{error_msg}</p><pre>{error_trace}</pre>"
            start_response(status, headers)
            return [body.encode()]
        handler = fallback_handler

# Ensure handler is always defined (safety check)
if handler is None:
    print("❌ WARNING: Handler is None! Creating fallback handler.")
    def fallback_handler(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html')]
        body = "<h1>500 Error</h1><p>Handler not properly initialized. Check Vercel logs.</p>"
        start_response(status, headers)
        return [body.encode()]
    handler = fallback_handler

# Final verification - handler must be callable
if not callable(handler):
    print(f"❌ CRITICAL: Handler is not callable! Type: {type(handler)}")
    def final_fallback(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html')]
        body = f"<h1>500 Error</h1><p>Handler initialization failed. Type: {type(handler)}</p>"
        start_response(status, headers)
        return [body.encode()]
    handler = final_fallback

print(f"✓ Final handler type: {type(handler)}, callable: {callable(handler)}")
