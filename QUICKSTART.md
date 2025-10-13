# Quick Start Guide

## Step 1: Install GDAL

GDAL is required for converting the TIF file into tiles.

### macOS (recommended):
```bash
brew install gdal
```

### Verify installation:
```bash
gdalinfo --version
gdal2tiles.py --version
```

You should see version information for both commands.

## Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or use pip3 if you have both Python 2 and 3:
```bash
pip3 install -r requirements.txt
```

## Step 3: Generate Tiles (One-Time Setup)

This converts your `map.tif` into tiles. **This only needs to be run once**, or when you update the map.

```bash
python preprocess.py map.tif
```

This will:
- Create a `tiles/` directory
- Generate tiles at various zoom levels
- Take approximately 5-10 minutes for a 110MB file
- Output progress information

**Note:** For a 20GB file, this could take 30-60 minutes. That's normal!

## Step 4: Start the Server

Once tiles are generated, start the lightweight server:

```bash
python server.py
```

By default, the server runs on port 8000.

## Step 5: View Your Map

Open your browser to:
```
http://localhost:8000/viewer.html
```

You should see your map loaded in the CesiumJS viewer!

## Common Issues

### "GDAL not found"
- Make sure you installed GDAL correctly
- Try restarting your terminal after installation
- Verify with: `which gdalinfo`

### "gdal2tiles.py not found"
- On some systems, you may need to install GDAL Python bindings separately
- Try: `pip install gdal` or `pip3 install gdal`

### "Tiles not loading in viewer"
- Make sure you ran `preprocess.py` first
- Check that the `tiles/` directory contains numbered folders (0, 1, 2, etc.)
- Look for `metadata.json` in the `tiles/` directory

### Port already in use
Start the server on a different port:
```bash
python server.py 8080
```

Then visit: `http://localhost:8080/viewer.html`

## What's Next?

- The viewer will only load tiles for the visible area
- Zoom in/out to see different levels of detail
- The entire TIF is never loaded into memory
- You can update `map.tif` and re-run `preprocess.py` anytime

## Performance Tips

For very large files (10GB+):
1. The preprocessing will take longer, but only needs to be done once
2. Consider reducing the maximum zoom level in `preprocess.py` if you don't need extreme detail
3. The server performance is independent of file size - it's always fast!

