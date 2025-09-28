#!/usr/bin/env python3
"""
Startup script for Route Optimization Microservice
This script starts both the main API server and Socket.IO server
"""

import subprocess
import sys
import time
import os
from threading import Thread

def start_api_server():
    """Start the main Flask API server"""
    print("Starting API server...")
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("API server stopped")
    except Exception as e:
        print(f"Error starting API server: {e}")

def start_socketio_server():
    """Start the Socket.IO server"""
    print("Starting Socket.IO server...")
    try:
        subprocess.run([sys.executable, "socketio_server.py"], check=True)
    except KeyboardInterrupt:
        print("Socket.IO server stopped")
    except Exception as e:
        print(f"Error starting Socket.IO server: {e}")

def main():
    """Start both servers"""
    print("=" * 50)
    print("NourishNet Route Optimization Microservice")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("Warning: .env file not found. Using default configuration.")
        print("Create a .env file with your configuration for production use.")
    
    # Start API server in a separate thread
    api_thread = Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait a moment for API server to start
    time.sleep(2)
    
    # Start Socket.IO server in main thread
    try:
        start_socketio_server()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        print("Goodbye!")

if __name__ == "__main__":
    main()
