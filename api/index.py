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

# Import Flask app directly - this is what Vercel expects
# Vercel's handler inspects the handler using issubclass(), so it must be a class instance
# Flask app is a WSGI application instance, which Vercel can inspect correctly
print("=== VERCEL FUNCTION INITIALIZATION ===")
print("Importing Flask app...")

try:
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
    # CRITICAL: Export app directly - Vercel inspects handler using issubclass()
    # Flask app is a WSGI application instance that Vercel can inspect correctly
    # Do NOT wrap it in a function or it will fail issubclass() check
    handler = app
    print(f"✓ Handler type: {type(handler).__name__}, module: {type(handler).__module__}")
    
    # CRITICAL: Add global exception handler to prevent FUNCTION_INVOCATION_FAILED
    # This catches ALL unhandled exceptions that would otherwise crash the function
    try:
        @app.errorhandler(Exception)
        def handle_all_exceptions(e):
            """Catch all unhandled exceptions to prevent function crashes"""
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e)
            print(f"❌ Unhandled exception in request: {error_msg}")
            print(error_trace)
            
            # Return a proper HTTP response instead of crashing
            try:
                from flask import jsonify, Response
                # Safely check debug mode
                try:
                    is_debug = app.debug
                except:
                    is_debug = False
                
                # Try to return JSON response
                try:
                    return jsonify({
                        'error': 'Internal server error',
                        'message': error_msg if is_debug else 'An error occurred. Please try again later.'
                    }), 500
                except Exception:
                    # If JSON fails, return plain text Response
                    return Response(
                        f"Internal Server Error: {error_msg}",
                        status=500,
                        mimetype='text/plain'
                    )
            except Exception as handler_error:
                # Last resort: return minimal WSGI response
                print(f"❌ Exception handler itself failed: {handler_error}")
                from flask import Response
                return Response(
                    "Internal Server Error",
                    status=500,
                    mimetype='text/plain'
                )
        print("✓ Global exception handler registered")
    except Exception as handler_reg_error:
        print(f"⚠ Warning: Failed to register exception handler: {handler_reg_error}")
        traceback.print_exc()
        # Continue anyway - at least we have the handler exported
    
    print("✓ Handler exported successfully")
    print("=== INITIALIZATION COMPLETE ===")
    
except ImportError as e:
    # Import error - show helpful message
    error_msg = f"Import Error: {str(e)}"
    error_trace = traceback.format_exc()
    print(f"❌ CRITICAL IMPORT ERROR: {error_msg}")
    print(error_trace)
    
    # Create Flask app for error handling (must be Flask instance, not function)
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
        
        handler = error_app  # Flask instance - passes issubclass() check
        print("✓ Error handler created (Import Error)")
    except Exception as fallback_error:
        print(f"❌ Failed to create Flask error handler: {fallback_error}")
        traceback.print_exc()
        # If we can't create Flask app, we MUST still export a Flask instance
        # Create minimal Flask app
        from flask import Flask
        handler = Flask(__name__)
        @handler.route('/<path:path>')
        @handler.route('/')
        def error_route(path=''):
            return f"<h1>500 Error</h1><p>{error_msg}</p>", 500

except Exception as e:
    # Any other error during initialization
    error_msg = f"Unexpected Error: {str(e)}"
    error_trace = traceback.format_exc()
    print(f"❌ CRITICAL UNEXPECTED ERROR: {error_msg}")
    print(error_trace)
    
    # Try to create Flask error handler (must be Flask instance, not function)
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
        
        handler = error_app  # Flask instance - passes issubclass() check
        print("✓ Error handler created (Unexpected Error)")
    except Exception as fallback_error:
        print(f"❌ Failed to create Flask error handler: {fallback_error}")
        traceback.print_exc()
        # Last resort: create minimal Flask app (must be Flask instance)
        from flask import Flask
        handler = Flask(__name__)
        @handler.route('/<path:path>')
        @handler.route('/')
        def error_route(path=''):
            return f"<h1>500 Error</h1><p>{error_msg}</p>", 500

# Ensure handler is always defined (safety check)
# CRITICAL: Handler MUST be a Flask instance, not a function, for Vercel's issubclass() check
if handler is None:
    print("❌ WARNING: Handler is None! Creating Flask fallback handler.")
    from flask import Flask
    handler = Flask(__name__)
    @handler.route('/<path:path>')
    @handler.route('/')
    def fallback_route(path=''):
        return "<h1>500 Error</h1><p>Handler not properly initialized. Check Vercel logs.</p>", 500

# Final verification - handler must be callable and a Flask instance
if not callable(handler):
    print(f"❌ CRITICAL: Handler is not callable! Type: {type(handler)}")
    from flask import Flask
    handler = Flask(__name__)
    @handler.route('/<path:path>')
    @handler.route('/')
    def final_fallback_route(path=''):
        return f"<h1>500 Error</h1><p>Handler initialization failed. Type: {type(handler)}</p>", 500

# Verify handler is a Flask instance (not a function)
# This is critical - Vercel uses issubclass() which requires a class instance
try:
    from flask import Flask
    if not isinstance(handler, Flask):
        print(f"⚠ WARNING: Handler is not a Flask instance! Type: {type(handler)}")
        print(f"⚠ This may cause issubclass() errors in Vercel's handler")
        # Try to fix it
        try:
            handler = Flask(__name__)
            @handler.route('/<path:path>')
            @handler.route('/')
            def warning_route(path=''):
                return "<h1>500 Error</h1><p>Handler type error. Check logs.</p>", 500
            print("✓ Created Flask instance as fallback")
        except Exception as fix_error:
            print(f"❌ Could not create Flask fallback: {fix_error}")
except Exception as check_error:
    print(f"⚠ Could not verify handler type: {check_error}")

print(f"✓ Final handler type: {type(handler).__name__}, callable: {callable(handler)}")
print(f"✓ Handler is Flask instance: {isinstance(handler, Flask) if 'Flask' in dir() else 'unknown'}")

# NOTE: We do NOT wrap the handler in a function because Vercel's handler
# performs type checking using issubclass() which fails on function wrappers.
# Instead, we rely on Flask's built-in error handling (@app.errorhandler(Exception))
# which is registered above and will catch all exceptions in route handlers.
# The Flask app itself is a proper WSGI application that Vercel can inspect correctly.
