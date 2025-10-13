#!/bin/bash
# Quick setup script for the CesiumJS Map Tile Server

echo "========================================="
echo "CesiumJS Map Tile Server Setup"
echo "========================================="
echo ""

# Check if GDAL is installed
if ! command -v gdalinfo &> /dev/null; then
    echo "❌ GDAL is not installed!"
    echo ""
    echo "Please install GDAL first:"
    echo "  macOS:    brew install gdal"
    echo "  Ubuntu:   sudo apt-get install gdal-bin python3-gdal"
    echo "  Windows:  Download from https://www.gisinternals.com/"
    echo ""
    exit 1
else
    echo "✅ GDAL is installed: $(gdalinfo --version)"
fi

# Check if gdal2tiles.py is available
if ! command -v gdal2tiles.py &> /dev/null; then
    echo "❌ gdal2tiles.py is not found in PATH!"
    echo "Please ensure GDAL Python scripts are installed."
    exit 1
else
    echo "✅ gdal2tiles.py is available"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================="
echo "✅ Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Run: python preprocess.py map.tif"
echo "  2. Run: python server.py"
echo "  3. Open: http://localhost:8000/viewer.html"
echo ""

