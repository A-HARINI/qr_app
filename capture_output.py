"""Capture and display server output"""
import sys
import os
from datetime import datetime

class OutputCapture:
    def __init__(self, log_file='server_output.log'):
        self.log_file = log_file
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def start_capture(self):
        """Start capturing output"""
        log_file = open(self.log_file, 'a', encoding='utf-8')
        sys.stdout = TeeOutput(self.original_stdout, log_file)
        sys.stderr = TeeOutput(self.original_stderr, log_file)
        
    def stop_capture(self):
        """Stop capturing output"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

class TeeOutput:
    """Write to both console and file"""
    def __init__(self, console, log_file):
        self.console = console
        self.log_file = log_file
        
    def write(self, text):
        self.console.write(text)
        self.log_file.write(text)
        self.log_file.flush()
        
    def flush(self):
        self.console.flush()
        self.log_file.flush()

if __name__ == '__main__':
    # Start capturing
    capture = OutputCapture()
    capture.start_capture()
    
    # Import and run app
    from app import app
    import socket
    
    print("\n" + "="*70)
    print("STARTING FLASK SERVER WITH OUTPUT CAPTURE")
    print("="*70)
    print(f"Output is being saved to: server_output.log")
    print("="*70 + "\n")
    
    # Get network IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    port = 5000
    print(f"[INFO] Server starting on http://127.0.0.1:{port}")
    print(f"[INFO] Network access: http://{local_ip}:{port}")
    print(f"[INFO] Output log: server_output.log")
    print("="*70 + "\n")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    finally:
        capture.stop_capture()



