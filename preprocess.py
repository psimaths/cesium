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

try:
    from osgeo import gdal, osr
    GDAL_AVAILABLE = True
except ImportError:
    GDAL_AVAILABLE = False
    print("Warning: GDAL Python bindings not available. Will try using gdalinfo command.")

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

def extract_bounds(input_tif):
    """Extract geographic bounds from GeoTIFF file."""
    print(f"Extracting bounds from {input_tif}...")

    if GDAL_AVAILABLE:
        # Use GDAL Python bindings (preferred method)
        try:
            dataset = gdal.Open(input_tif)
            if dataset is None:
                raise Exception(f"Could not open {input_tif}")

            # Get geotransform
            gt = dataset.GetGeoTransform()
            width = dataset.RasterXSize
            height = dataset.RasterYSize

            # Calculate corner coordinates
            minx = gt[0]
            maxy = gt[3]
            maxx = gt[0] + width * gt[1]
            miny = gt[3] + height * gt[5]

            # Get projection
            proj = dataset.GetProjection()
            src_srs = osr.SpatialReference()
            src_srs.ImportFromWkt(proj)

            # Create WGS84 coordinate system
            tgt_srs = osr.SpatialReference()
            tgt_srs.ImportFromEPSG(4326)

            # Create coordinate transformation
            transform = osr.CoordinateTransformation(src_srs, tgt_srs)

            # Transform corners to WGS84
            min_lon, min_lat, _ = transform.TransformPoint(minx, miny)
            max_lon, max_lat, _ = transform.TransformPoint(maxx, maxy)

            bounds = {
                'west': min(min_lat, max_lat),
                'south': min(min_lon, max_lon),
                'east': max(min_lat, max_lat),
                'north': max(min_lon, max_lon),
            }

            dataset = None  # Close dataset
            print(f"Extracted bounds: {bounds}")
            return bounds

        except Exception as e:
            print(f"Error using GDAL Python: {e}")
            print("Falling back to gdalinfo command...")

    # Fallback: use gdalinfo command
    try:
        result = subprocess.run(
            ['gdalinfo', '-json', input_tif],
            check=True,
            capture_output=True,
            text=True
        )

        info = json.loads(result.stdout)

        # Extract corner coordinates
        corners = info['cornerCoordinates']

        # Get WGS84 coordinates (they're in the second element of each corner array)
        lower_left = corners['lowerLeft']
        upper_right = corners['upperRight']

        bounds = {
            'west': lower_left[0],
            'south': lower_left[1],
            'east': upper_right[0],
            'north': upper_right[1]
        }

        print(f"Extracted bounds: {bounds}")
        return bounds

    except subprocess.CalledProcessError as e:
        print(f"Error running gdalinfo: {e}")
        print("Cannot extract bounds automatically.")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing gdalinfo output: {e}")
        return None

def create_metadata(bounds, output_dir):
    """Create metadata.json file with map bounds."""
    metadata = {
        'west': bounds['west'],
        'south': bounds['south'],
        'east': bounds['east'],
        'north': bounds['north'],
        'description': 'Custom map tiles generated by preprocess.py'
    }

    metadata_path = os.path.join(output_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Created {metadata_path}")
    print(f"  West: {bounds['west']:.6f}°")
    print(f"  South: {bounds['south']:.6f}°")
    print(f"  East: {bounds['east']:.6f}°")
    print(f"  North: {bounds['north']:.6f}°")

def main():
    if len(sys.argv) < 2:
        print("Usage: python preprocess.py <input.tif> [output_dir]")
        sys.exit(1)

    input_tif = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'tiles'

    if not os.path.exists(input_tif):
        print(f"Error: {input_tif} not found")
        sys.exit(1)

    # Extract bounds from input GeoTIFF
    bounds = extract_bounds(input_tif)

    if bounds is None:
        print("\nError: Could not extract bounds from GeoTIFF.")
        print("Please ensure GDAL is properly installed (pip install gdal)")
        sys.exit(1)

    # Convert to tiles
    success = convert_to_tiles(input_tif, output_dir)

    if success:
        # Create metadata.json with extracted bounds
        create_metadata(bounds, output_dir)

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
