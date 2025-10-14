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
import multiprocessing

def convert_to_tiles(input_tif, output_dir='tiles'):
    """Convert GeoTIFF to tiles using gdal2tiles with maximum performance."""
    print(f"Converting {input_tif} to tiles...")
    print(f"Output directory: {output_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get number of CPU cores for maximum parallelization
    num_processes = multiprocessing.cpu_count()
    print(f"Using {num_processes} CPU cores for processing")
    
    # Set up GDAL environment variables for maximum performance
    env = os.environ.copy()
    env['GDAL_CACHEMAX'] = '2048'  # 2GB cache
    env['GDAL_NUM_THREADS'] = 'ALL_CPUS'  # Use all CPUs
    env['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'  # Speed up opening
    env['CPL_VSIL_CURL_ALLOWED_EXTENSIONS'] = '.tif,.tiff'
    
    # Generate tiles using gdal2tiles with optimized settings
    print("Generating tiles with maximum speed...")
    
    gdal2tiles_cmd = [
        'gdal2tiles.py',
        '--zoom=10-22',  # Zoom levels 0-22 for high resolution
        f'--processes={num_processes}',  # Use all available CPU cores
        '--webviewer=none',  # No web viewer (we have our own)
        '--resampling=average',  # Faster resampling (average is much faster than lanczos)
        '--tiledriver=PNG',  # Explicit PNG driver
        '--xyz',  # Use XYZ tile scheme for better compatibility
        input_tif,
        output_dir
    ]
    
    try:
        result = subprocess.run(
            gdal2tiles_cmd, 
            check=True, 
            capture_output=True, 
            text=True,
            env=env
        )
        print("Tiles generated successfully!")
        if result.stdout:
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
