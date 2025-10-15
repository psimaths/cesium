#!/usr/bin/env python3
"""
Generate contour lines from topographic data for overlay on the Cesium map.

Usage: python generate_contours.py <topo.tif> [interval] [output.json]
"""

import sys
import os
import subprocess
import json

def generate_contours(input_tif, interval=10, output_file='contours.json'):
    """
    Generate contour lines from a DEM/topographic GeoTIFF.
    
    Args:
        input_tif: Path to the topographic GeoTIFF
        interval: Contour interval in meters (default: 10m)
        output_file: Output GeoJSON file path
    """
    print(f"Generating contour lines from {input_tif}")
    print(f"Contour interval: {interval}m")
    print(f"Output: {output_file}")
    
    if not os.path.exists(input_tif):
        print(f"Error: {input_tif} not found")
        return False
    
    # Generate contours using gdal_contour
    # -a: attribute name for elevation values
    # -i: contour interval
    # -f: output format (GeoJSON)
    contour_cmd = [
        'gdal_contour',
        '-a', 'elevation',  # Attribute name for elevation
        '-i', str(interval),  # Contour interval
        '-f', 'GeoJSON',  # Output format
        input_tif,
        output_file
    ]
    
    try:
        print("Running gdal_contour...")
        result = subprocess.run(
            contour_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        if os.path.exists(output_file):
            # Get file size for feedback
            file_size = os.path.getsize(output_file)
            print(f"✓ Contours generated successfully!")
            print(f"  Output file: {output_file} ({file_size / 1024:.1f} KB)")
            
            # Load and display some stats
            with open(output_file, 'r') as f:
                data = json.load(f)
                num_features = len(data.get('features', []))
                print(f"  Number of contour lines: {num_features}")
                
                # Get elevation range if available
                if num_features > 0:
                    elevations = [f['properties']['elevation'] 
                                for f in data['features'] 
                                if 'elevation' in f['properties']]
                    if elevations:
                        min_elev = min(elevations)
                        max_elev = max(elevations)
                        print(f"  Elevation range: {min_elev}m to {max_elev}m")
            
            return True
        else:
            print("Error: Output file was not created")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error during contour generation: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_contours.py <topo.tif> [interval] [output.json]")
        print("\nExamples:")
        print("  python generate_contours.py topo.tif              # 10m interval, output to contours.json")
        print("  python generate_contours.py topo.tif 5            # 5m interval")
        print("  python generate_contours.py topo.tif 20 mycontours.json  # Custom interval and output")
        sys.exit(1)
    
    input_tif = sys.argv[1]
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    output_file = sys.argv[3] if len(sys.argv) > 3 else 'tiles/contours.json'
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    success = generate_contours(input_tif, interval, output_file)
    
    if success:
        print("\n" + "="*60)
        print("Contour generation complete!")
        print(f"Contour file: {output_file}")
        print("\nNext steps:")
        print("1. Start the server: python server.py")
        print("2. Open http://localhost:8000/viewer.html")
        print("3. Contour lines will be displayed on the map")
        print("="*60)
    else:
        print("Contour generation failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

