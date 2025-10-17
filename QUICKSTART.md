# 0. Get your map.tif and points.laz from OpenDroneMap
Thats what this entire repo was build for :)

# 1. One command to install everything
./setup.sh

# 2. Process your data
python3 preprocess.py map.tif points.laz

# 3. Upload to Cesium ion and get Asset ID

# 4. Update script.js line 8 with Asset ID

# 5. Start server
python3 server.py

# 6. Open http://localhost:8000/