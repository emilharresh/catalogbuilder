import os
import sys
import time
import socket
import threading
import webbrowser
from waitress import serve
from app import app, BASE_DIR

def find_available_port(start_port=5001, max_attempts=10):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def open_browser(port):
    time.sleep(1.0)
    url = f"http://127.0.0.1:{port}"
    print(f"\nOpening {url} in your default browser...")
    webbrowser.open(url)

def main():
    port = find_available_port(5001)
    
    banner = f"""
============================================================
              FINAPACK CATALOG BUILDER
============================================================
 [OK] Catalog Builder is running!
 [OK] Local Address: http://127.0.0.1:{port}
 [OK] Working Directory: {BASE_DIR}

 * Your default web browser will open automatically.
 * Please KEEP THIS WINDOW OPEN while using the application.
 * To exit, simply close this window or press Ctrl+C.
============================================================
"""
    print(banner)

    # Launch browser in a background thread once server starts
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Serve using production WSGI server Waitress
    serve(app, host='127.0.0.1', port=port, threads=6)

if __name__ == '__main__':
    main()
