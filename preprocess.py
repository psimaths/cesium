#!/usr/bin/env python3
"""
Preprocessing script to convert imagery and point cloud data for Cesium.
This should be run once when the data is updated.

Usage: python preprocess.py <map.tif> <points.laz> [output_dir]
   or: python preprocess.py <map.tif> [output_dir]  (tiles only)
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

def convert_pointcloud_to_heightmap(input_laz, output_tif='cesiumionheightmap.tif', resolution=0.5):
    """Convert LAZ point cloud to georeferenced GeoTIFF heightmap for Cesium ion."""
    print(f"\n{'='*60}")
    print("Converting point cloud to Cesium ion heightmap...")
    print(f"{'='*60}")
    print(f"Input: {input_laz}")
    print(f"Output: {output_tif}")
    print(f"Resolution: {resolution}m per pixel")
    
    # Check if PDAL is available
    try:
        subprocess.run(['pdal', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\nError: PDAL is not installed!")
        print("Install it with: brew install pdal")
        return False
    
    # Get point cloud info
    print("\nExamining point cloud metadata...")
    try:
        result = subprocess.run(
            ['pdal', 'info', input_laz, '--summary'],
            check=True,
            capture_output=True,
            text=True
        )
        info = json.loads(result.stdout)
        bounds = info['summary']['bounds']
        count = info['summary']['num_points']
        
        print(f"  Points: {count:,}")
        print(f"  X range: {bounds['minx']:.2f} - {bounds['maxx']:.2f}")
        print(f"  Y range: {bounds['miny']:.2f} - {bounds['maxy']:.2f}")
        print(f"  Z range: {bounds['minz']:.2f} - {bounds['maxz']:.2f}m")
        
        # Calculate output raster dimensions
        width = int((bounds['maxx'] - bounds['minx']) / resolution)
        height = int((bounds['maxy'] - bounds['miny']) / resolution)
        print(f"  Output size: {width} x {height} pixels")
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not read point cloud metadata: {e}")
    
    # Convert LAZ to GeoTIFF using PDAL
    print("\nConverting to georeferenced GeoTIFF...")
    pdal_cmd = [
        'pdal', 'translate', input_laz, output_tif,
        f'--writers.gdal.resolution={resolution}',
        '--writers.gdal.output_type=mean',
        '--writers.gdal.data_type=float32'
    ]
    
    try:
        result = subprocess.run(
            pdal_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ Heightmap created successfully!")
        
        # Verify the output has proper georeferencing
        verify_result = subprocess.run(
            ['gdalinfo', output_tif],
            check=True,
            capture_output=True,
            text=True
        )
        
        if 'Coordinate System is:' in verify_result.stdout and 'EPSG' in verify_result.stdout:
            print("✓ Georeferencing verified - ready for Cesium ion!")
            
            # Get file size
            size_mb = os.path.getsize(output_tif) / (1024 * 1024)
            print(f"✓ File size: {size_mb:.2f} MB")
            return True
        else:
            print("⚠ Warning: Output file may be missing spatial reference")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
        if e.stderr:
            print(f"Details: {e.stderr}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python preprocess.py <map.tif> <points.laz> [output_dir]")
        print("  python preprocess.py <map.tif> [output_dir]  (tiles only)")
        print("\nExample:")
        print("  python preprocess.py map.tif points.laz tiles")
        sys.exit(1)

    input_tif = sys.argv[1]
    
    # Determine if we have point cloud data
    points_laz = None
    output_dir = 'tiles'
    
    if len(sys.argv) >= 3:
        # Check if second argument is a LAZ file or output directory
        if sys.argv[2].endswith('.laz'):
            points_laz = sys.argv[2]
            output_dir = sys.argv[3] if len(sys.argv) > 3 else 'tiles'
        else:
            output_dir = sys.argv[2]
    
    # Validate input files
    if not os.path.exists(input_tif):
        print(f"Error: {input_tif} not found")
        sys.exit(1)
    
    if points_laz and not os.path.exists(points_laz):
        print(f"Error: {points_laz} not found")
        sys.exit(1)

    print("="*60)
    print("CESIUM DATA PREPROCESSING")
    print("="*60)
    print(f"Map imagery: {input_tif}")
    if points_laz:
        print(f"Point cloud: {points_laz}")
    print(f"Output directory: {output_dir}")
    print("="*60)

    all_success = True
    heightmap_created = False

    # Step 1: Convert point cloud to heightmap if provided
    if points_laz:
        heightmap_success = convert_pointcloud_to_heightmap(points_laz, 'cesiumionheightmap.tif')
        if heightmap_success:
            heightmap_created = True
        else:
            print("⚠ Warning: Heightmap creation failed")
            all_success = False

    # Step 2: Extract bounds from input GeoTIFF
    print(f"\n{'='*60}")
    print("Processing imagery tiles...")
    print(f"{'='*60}")
    bounds = extract_bounds(input_tif)

    if bounds is None:
        print("\nError: Could not extract bounds from GeoTIFF.")
        print("Please ensure GDAL is properly installed (pip install gdal)")
        sys.exit(1)

    # Step 3: Convert to tiles
    success = convert_to_tiles(input_tif, output_dir)

    if success:
        # Create metadata.json with extracted bounds
        create_metadata(bounds, output_dir)

       
    else:
        print("Tile generation failed!")
        all_success = False

    # Final summary
    print("\n" + "="*60)
    print("PREPROCESSING COMPLETE!")
    print("="*60)
    
    if success:
        print(f"✓ Map tiles stored in: {output_dir}")
        print("  → Start server: python server.py")
    
    if heightmap_created:
        print(f"✓ Cesium ion heightmap: cesiumionheightmap.tif")
        print("\n" + "─"*60)
        print("NEXT STEPS - Upload to Cesium ion:")
        print("─"*60)
        print("1. Go to https://ion.cesium.com/")
        print("2. Click 'Add data' and select: cesiumionheightmap.tif")
        print("3. Choose these settings:")
        print("   - Kind of data: 'Raster Terrain'")
        print("   - Height unit: 'Meters'")
        print("   - Height reference: 'Mean sea level'")
        print("4. Click 'Upload'")
        print("5. Once processed, update your Cesium ion web application")
    
    print("="*60)
    
    if not all_success:
        sys.exit(1)

if __name__ == '__main__':
    main()
