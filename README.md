# CesiumJS Map Tile Server

A lightweight map server that efficiently serves large GeoTIFF files using CesiumJS by converting them into tiles.

## Features

- Handles large GeoTIFF files (tested up to 20GB+)
- Efficient tile-based serving - only loads visible tiles
- Two-step process: preprocessing and serving
- Minimal server startup time
- Modern web-based viewer with CesiumJS
- Topographic contour line overlay support
- Interactive contour lines with elevation labels

## Prerequisites

Install the required dependencies:

```bash
# Install GDAL (required for tile generation)
# On macOS:
brew install gdal

# On Ubuntu/Debian:
sudo apt-get install gdal-bin python3-gdal

# On Windows:
# Download from https://www.gisinternals.com/

# Install Python dependencies
pip install -r requirements.txt
```

## Usage

### Step 1: Preprocess the TIF file (one-time operation)

This step converts your GeoTIFF into tiles. Run this whenever you update the map:

```bash
python preprocess.py map.tif [output_dir]
```

Example:
```bash
python preprocess.py map.tif tiles
```

This will:
- Reproject the TIF to Web Mercator (EPSG:3857)
- Generate tiles at zoom levels 0-18
- Create metadata for the viewer
- Store everything in the `tiles` directory

**Note:** This can take several minutes for large files (110MB) and up to an hour for very large files (20GB).

### Step 2: Generate contour lines (optional)

If you have a topographic/elevation GeoTIFF (DEM), you can generate contour lines to overlay on your map:

```bash
python3 generate_contours.py topo.tif [interval] [output.json]
```

Examples:
```bash
# Generate 10m contour intervals (default)
python3 generate_contours.py topo.tif

# Generate 5m contour intervals
python3 generate_contours.py topo.tif 5

# Custom output location
python3 generate_contours.py topo.tif 10 tiles/contours.json
```

This will:
- Extract contour lines from the elevation data
- Create a GeoJSON file with elevation information
- Store it in the tiles directory for serving

The contour lines will automatically:
- Display on the map with brown coloring
- Show labels for major contours (every 50m)
- Be toggleable via the map controls
- Show elevation on click

### Step 3: Start the server

Once tiles are generated, start the lightweight server:

```bash
python server.py [port] [tiles_dir]
```

Example:
```bash
python server.py 8000 tiles
```

Then open your browser to:
```
http://localhost:8000/
```

The server starts instantly and just serves static files. For security, only tiles, JSON metadata, and the viewer are accessible - source code and configuration files are blocked.

## Map Controls

The viewer includes interactive controls:

- **Contour Lines Toggle**: Show/hide topographic contour lines
- **Navigation**: Mouse controls for pan, zoom, rotate, and tilt
- **Info Box**: Click contour lines to see elevation data

## Performance

- **110MB TIF**: Preprocessing takes ~5-10 minutes, serving is instant
- **20GB TIF**: Preprocessing takes ~30-60 minutes, serving is still instant
- Viewer only loads tiles for the visible area and zoom level
- No need to load the entire file into memory

## Updating the Map

When you need to update the map:

1. Replace the TIF file
2. Run the preprocessing script again: `python3 preprocess.py new_map.tif tiles`
3. If you have elevation data, regenerate contours: `python3 generate_contours.py topo.tif`
4. Restart the server (if it was running)

The server itself doesn't need any reconfiguration.

## Customization

### Adjust tile generation settings

Edit `preprocess.py` to modify:
- Zoom levels (default: 0-18)
- Compression quality (default: JPEG 85%)
- Number of processes (default: 4)

### Adjust viewer settings

Edit `viewer.html` to customize:
- Base map layers
- Camera position
- UI controls
- Styling
- Contour line appearance (colors, widths, label intervals)

## Security

The server includes built-in security to prevent access to sensitive files:

### Accessible Resources
- ✅ `index.html` (viewer application)
- ✅ `tiles/` directory (map tiles and metadata)
- ✅ `terrain/` directory (terrain data)
- ✅ `.png` files (tile images)
- ✅ `.json` files (metadata and contours)

### Blocked Resources
- ❌ Python source files (`.py`)
- ❌ Shell scripts (`.sh`)
- ❌ Configuration files (`.txt`, `.gitignore`)
- ❌ Source data files (`.tif`)
- ❌ Documentation files (`.md`)
- ❌ Git directory (`.git`)
- ❌ Hidden files (`.DS_Store`, etc.)

### Testing Security

To verify security is working, run the test script:

```bash
# Start the server
python server.py

# In another terminal, test security
./test_security.sh
```

You should see:
- **200 OK** for allowed resources (index.html, tiles, etc.)
- **403 Forbidden** for blocked resources (server.py, README.md, etc.)

## Troubleshooting

**GDAL not found:**
- Make sure GDAL is installed and in your PATH
- Try `gdal-config --version` to verify installation

**Tiles not loading:**
- Check that `metadata.json` exists in the tiles directory
- Verify tiles were generated successfully
- Check browser console for errors

**Out of memory during preprocessing:**
- The preprocessing script streams data, so it shouldn't use much memory
- If issues persist, reduce the maximum zoom level in `preprocess.py`

**Contour lines not showing:**
- Make sure `contours.json` exists in the tiles directory
- Check browser console for loading errors
- Verify the topo.tif has valid elevation data
- Try regenerating with a larger contour interval: `python3 generate_contours.py topo.tif 20`

**Too many or too few contours:**
- Adjust the contour interval parameter
- Lower interval (e.g., 5) = more contours, more detail
- Higher interval (e.g., 20) = fewer contours, less cluttered

