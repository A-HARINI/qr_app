"""Simple script to start Flask server with network diagnostics"""
import sys
import socket
from app import app

def get_local_ip():
    """Get the local network IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return None

def check_port_available(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

if __name__ == '__main__':
    port = 5000
    
    print("\n" + "="*70)
    print("FLASK SERVER STARTUP")
    print("="*70)
    
    # Check if port is available
    if not check_port_available(port):
        print(f"\n[WARNING] Port {port} may already be in use!")
        print("Another process might be using this port.")
        print("Try:")
        print("  1. Close other Flask/Python processes")
        print("  2. Use a different port: python start_server.py 5001")
        print("  3. Find and kill the process using port 5000")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Get network IP
    local_ip = get_local_ip()
    
    print(f"\n[INFO] Starting Flask server...")
    print(f"[INFO] Port: {port}")
    print(f"[INFO] Host: 0.0.0.0 (accessible from network)")
    
    if local_ip:
        print(f"\n[SUCCESS] Server will be accessible at:")
        print(f"  Local:    http://127.0.0.1:{port}")
        print(f"  Network:  http://{local_ip}:{port}")
        print(f"\n[MOBILE] To access from mobile device:")
        print(f"  Use: http://{local_ip}:{port}")
        print(f"  Make sure mobile is on the SAME Wi-Fi network!")
    else:
        print(f"\n[WARNING] Could not detect network IP")
        print(f"  Local access: http://127.0.0.1:{port}")
        print(f"  Network access may not work")
    
    print(f"\n[TEST] After starting, test these URLs:")
    print(f"  - http://127.0.0.1:{port}/test/network")
    print(f"  - http://{local_ip}:{port}/test/network (from mobile)")
    
    print("\n" + "="*70)
    print("Starting server... Press CTRL+C to stop")
    print("="*70 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to start server: {e}")
        print("\nTroubleshooting:")
        print("1. Check if another process is using port 5000")
        print("2. Check Windows Firewall settings")
        print("3. Try running as Administrator")
        sys.exit(1)




