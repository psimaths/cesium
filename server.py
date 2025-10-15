#!/usr/bin/env python3
"""
Lightweight server to serve tiles and the CesiumJS viewer.
This has minimal startup time and just serves static files.

Usage: python server.py [port]
"""

import sys
import os
import socketserver
from http.server import SimpleHTTPRequestHandler
from urllib.parse import unquote

class TileServerHandler(SimpleHTTPRequestHandler):
    """Custom handler to serve tiles with proper CORS headers and security restrictions."""
    
    def is_path_allowed(self, path):
        """Check if a path should be allowed to be served."""
        decoded_path = unquote(path).lstrip('/')
        
        # Allow root and index.html
        if not decoded_path or decoded_path == 'index.html':
            return True
        
        # Allow tiles and terrain directories
        if decoded_path.startswith(('tiles/', 'terrain/')):
            return True
        
        # Block everything else (Python files, shell scripts, docs, etc.)
        return False
    
    def do_GET(self):
        """Handle GET requests with security checks."""
        if not self.is_path_allowed(self.path):
            self.send_error(403, "Forbidden - Access to this resource is not allowed")
            return
        
        # Path is allowed, proceed with normal handling
        super().do_GET()
    
    def end_headers(self):
        # Enable CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        # Ensure JSON files have correct content type
        if self.path.endswith('.json'):
            self.send_header('Content-Type', 'application/json')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    # Check if required files exist
    if not os.path.exists('tiles'):
        print("Error: tiles directory not found!")
        print("Please run preprocess.py first to generate tiles.")
        sys.exit(1)
    
    if not os.path.exists('index.html'):
        print("Warning: index.html not found.")
    
    if not os.path.exists('tiles/metadata.json'):
        print("Warning: metadata.json not found. The viewer may not center correctly.")
    
    print(f"Starting tile server on port {port}...")
    print(f"Serving from: {os.getcwd()}")
    print(f"\nOpen the viewer at: http://localhost:{port}/")
    print("🔒 Security: Only tiles/, terrain/, and index.html are accessible")
    print("Press Ctrl+C to stop the server.\n")
    
    try:
        with socketserver.TCPServer(("", port), TileServerHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)

if __name__ == '__main__':
    main()

