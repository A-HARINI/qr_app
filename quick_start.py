"""Quick start script - simplest way to start Flask server"""
from app import app
import socket

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    ip = get_ip()
    print("\n" + "="*60)
    print("STARTING FLASK SERVER")
    print("="*60)
    print(f"\nServer starting...")
    print(f"Local:    http://127.0.0.1:5000")
    if ip != "127.0.0.1":
        print(f"Network:  http://{ip}:5000")
    print(f"\nPress CTRL+C to stop")
    print("="*60 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Port 5000 might be in use - try: netstat -ano | findstr :5000")
        print("2. Check if another Flask app is running")
        print("3. Try a different port (modify port=5000 to port=5001)")




