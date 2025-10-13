#!/usr/bin/env python3
"""
Preprocessing script to convert a GeoTIFF into tiles for efficient serving.
This should be run once when the map is updated.

Usage: python preprocess.py <input.tif> [output_dir]
"""

import sys
import os
import subprocess
import json
import shutil

def convert_to_tiles(input_tif, output_dir='tiles'):
    """Convert GeoTIFF to tiles using gdal2tiles."""
    print(f"Converting {input_tif} to tiles...")
    print(f"Output directory: {output_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate tiles using gdal2tiles with leaflet profile
    print("Generating tiles (this may take a while)...")
    
    gdal2tiles_cmd = [
        'gdal2tiles.py',
        '--zoom=0-22',  # Zoom levels 0-22 for high resolution
        '--processes=4',  # Use 4 processes for faster generation
        '--webviewer=none',  # No web viewer (we have our own)
        '--resampling=lanczos',  # High quality resampling
        input_tif,
        output_dir
    ]
    
    try:
        result = subprocess.run(gdal2tiles_cmd, check=True, capture_output=True, text=True)
        print("Tiles generated successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during tile generation: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python preprocess.py <input.tif> [output_dir]")
        sys.exit(1)
    
    input_tif = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'tiles'
    
    if not os.path.exists(input_tif):
        print(f"Error: {input_tif} not found")
        sys.exit(1)
    
    success = convert_to_tiles(input_tif, output_dir)
    
    if success:
        # Copy viewer.html to the output directory
        viewer_src = 'viewer.html'
        viewer_dst = os.path.join(output_dir, 'viewer.html')
        if os.path.exists(viewer_src):
            shutil.copy2(viewer_src, viewer_dst)
            print(f"Copied viewer.html to {output_dir}")
        else:
            print("Warning: viewer.html not found in current directory")
        
        print("\n" + "="*60)
        print("Preprocessing complete!")
        print(f"Tiles are stored in: {output_dir}")
        print("You can now start the server with: python server.py")
        print("="*60)
    else:
        print("Preprocessing failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
