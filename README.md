# CesiumJS Map Tile Server

A lightweight map server that efficiently serves large GeoTIFF files using CesiumJS by converting them into tiles.

## Features

- Handles large GeoTIFF files (tested up to 20GB+)
- Efficient tile-based serving - only loads visible tiles
- Two-step process: preprocessing and serving
- Minimal server startup time
- Modern web-based viewer with CesiumJS

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

### Step 2: Start the server

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

## Performance

- **110MB TIF**: Preprocessing takes ~5-10 minutes, serving is instant
- **20GB TIF**: Preprocessing takes ~30-60 minutes, serving is still instant
- Viewer only loads tiles for the visible area and zoom level
- No need to load the entire file into memory

## Updating the Map

When you need to update the map:

1. Replace the TIF file
2. Run the preprocessing script again: `python3 preprocess.py new_map.tif tiles`
3. Restart the server (if it was running)

The server itself doesn't need any reconfiguration.

## Customization

### Adjust tile generation settings

Edit `preprocess.py` to modify:
- Zoom levels (default: 0-18)
- Compression quality (default: JPEG 85%)
- Number of processes (default: 4)

### Adjust viewer settings

Edit `index.html` to customize:
- Base map layers
- Camera position
- UI controls
- Styling

## Security

The server includes built-in security to prevent access to sensitive files:

### Accessible Resources
- ✅ `index.html` (viewer application)
- ✅ `tiles/` directory (map tiles and metadata)
- ✅ `terrain/` directory (terrain data)
- ✅ `.png` files (tile images)
- ✅ `.json` files (metadata)

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

