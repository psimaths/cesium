#!/bin/bash
# Quick setup script for the Cesium Terrain and Imagery Server

echo "============================================================"
echo "Cesium Terrain and Imagery Server Setup"
echo "============================================================"
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
fi

echo "Detected OS: $OS"
echo ""

# Function to install on macOS
install_macos() {
    echo "Installing dependencies for macOS using Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed!"
        echo "Install it from: https://brew.sh/"
        exit 1
    fi
    
    # Install GDAL
    if ! command -v gdalinfo &> /dev/null; then
        echo "Installing GDAL..."
        brew install gdal
    else
        echo "✅ GDAL is already installed"
    fi
    
    # Install PDAL
    if ! command -v pdal &> /dev/null; then
        echo "Installing PDAL..."
        brew install pdal
    else
        echo "✅ PDAL is already installed"
    fi
}

# Function to install on Linux
install_linux() {
    echo "Installing dependencies for Linux using apt..."
    
    # Install GDAL
    if ! command -v gdalinfo &> /dev/null; then
        echo "Installing GDAL..."
        sudo apt-get update
        sudo apt-get install -y gdal-bin python3-gdal
    else
        echo "✅ GDAL is already installed"
    fi
    
    # Install PDAL
    if ! command -v pdal &> /dev/null; then
        echo "Installing PDAL..."
        sudo apt-get install -y pdal
    else
        echo "✅ PDAL is already installed"
    fi
}

# Install based on OS
echo "============================================================"
echo "Installing System Dependencies"
echo "============================================================"
echo ""

if [ "$OS" == "macos" ]; then
    install_macos
elif [ "$OS" == "linux" ]; then
    install_linux
else
    echo "⚠️  Unsupported OS. Please install manually:"
    echo "   - GDAL: https://gdal.org/download.html"
    echo "   - PDAL: https://pdal.io/download.html"
    echo ""
fi

# Verify installations
echo ""
echo "============================================================"
echo "Verifying Installations"
echo "============================================================"
echo ""

HAS_ERRORS=0

# Check GDAL
if ! command -v gdalinfo &> /dev/null; then
    echo "❌ GDAL is not installed!"
    HAS_ERRORS=1
else
    echo "✅ GDAL: $(gdalinfo --version)"
fi

# Check gdal2tiles.py
if ! command -v gdal2tiles.py &> /dev/null; then
    echo "❌ gdal2tiles.py is not found in PATH!"
    HAS_ERRORS=1
else
    echo "✅ gdal2tiles.py is available"
fi

# Check PDAL
if ! command -v pdal &> /dev/null; then
    echo "❌ PDAL is not installed!"
    HAS_ERRORS=1
else
    echo "✅ PDAL: $(pdal --version 2>&1 | head -n 1)"
fi

# Exit if there were errors
if [ $HAS_ERRORS -eq 1 ]; then
    echo ""
    echo "❌ Some dependencies are missing. Please install them manually."
    exit 1
fi

# Install Python dependencies
echo ""
echo "============================================================"
echo "Installing Python Dependencies"
echo "============================================================"
echo ""

if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    echo "⚠️  pip is not found. Skipping Python dependencies."
fi

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Process your data:"
echo "   python3 preprocess.py map.tif points.laz"
echo ""
echo "2. Upload terrain to Cesium ion:"
echo "   - Go to https://ion.cesium.com/"
echo "   - Upload cesiumionheightmap.tif as 'Raster Terrain'"
echo "   - Copy the Asset ID"
echo ""
echo "3. Update script.js:"
echo "   - Edit line 8: TERRAIN_ASSET_ID with your Asset ID"
echo ""
echo "4. Start the server:"
echo "   python3 server.py"
echo ""
echo "5. Open in browser:"
echo "   http://localhost:8000/"
echo ""
echo "============================================================"

