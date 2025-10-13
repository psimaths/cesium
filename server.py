#!/usr/bin/env python3
"""
Lightweight server to serve tiles and the CesiumJS viewer.
This has minimal startup time and just serves static files.

Usage: python server.py [port] [tiles_dir]
"""

import sys
import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

class TileServerHandler(SimpleHTTPRequestHandler):
    """Custom handler to serve tiles with proper CORS headers."""
    
    def end_headers(self):
        # Enable CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    tiles_dir = sys.argv[2] if len(sys.argv) > 2 else 'tiles'
    
    # Change to tiles directory
    if os.path.exists(tiles_dir):
        os.chdir(tiles_dir)
    else:
        print(f"Warning: Tiles directory '{tiles_dir}' not found!")
        print("Please run preprocess.py first to generate tiles.")
        print(f"Usage: python preprocess.py map.tif {tiles_dir}")
        sys.exit(1)
    
    # Check if metadata exists
    if not os.path.exists('metadata.json'):
        print("Warning: metadata.json not found. The viewer may not center correctly.")
    
    print(f"Starting tile server on port {port}...")
    print(f"Serving tiles from: {os.getcwd()}")
    print(f"\nOpen the viewer at: http://localhost:{port}/viewer.html")
    print("Press Ctrl+C to stop the server.\n")
    
    try:
        with socketserver.TCPServer(("", port), TileServerHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)

if __name__ == '__main__':
    main()

