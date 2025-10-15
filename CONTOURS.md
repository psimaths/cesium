# Contour Lines Quick Reference

This guide explains how to use the topographic contour line feature in your Cesium map.

## What Are Contour Lines?

Contour lines are lines connecting points of equal elevation on a map. They help visualize terrain elevation and topography in 2D, similar to how they appear on traditional topographic maps.

## Quick Start

### 1. Generate Contours

```bash
python3 generate_contours.py topo.tif
```

This generates contour lines from your elevation data with a 10-meter interval.

### 2. Start the Server

```bash
python3 server.py
```

### 3. View in Browser

Open http://localhost:8000/viewer.html

The contour lines will automatically appear on your map!

## Customizing Contours

### Change Contour Interval

The contour interval determines the elevation difference between adjacent contour lines:

```bash
# More detailed (5m intervals)
python3 generate_contours.py topo.tif 5

# Less detailed (20m intervals)  
python3 generate_contours.py topo.tif 20

# Custom interval (e.g., 50m)
python3 generate_contours.py topo.tif 50
```

**Choosing the right interval:**
- **Dense/mountainous terrain**: Use smaller intervals (5-10m) for detail
- **Flat terrain**: Use larger intervals (20-50m) to avoid clutter
- **Large area**: Use larger intervals to reduce file size and improve performance

### Contour Line Styling

The viewer automatically styles contours with:
- **Regular contours** (10m, 20m, 30m, etc.): Lighter brown, thin lines
- **Major contours** (50m, 100m, 150m, etc.): Darker brown, thicker lines with elevation labels

To customize the styling, edit `viewer.html` in the `loadContours` function:

```javascript
// Line 300-306: Change colors
const color = Cesium.Color.fromCssColorString(
    isMajor ? '#5c3317' : '#8B4513'  // Change these hex colors
).withAlpha(isMajor ? 0.9 : 0.6);   // Adjust transparency

// Line 310-311: Change line widths
width: isMajor ? 2.5 : 1.5,  // Adjust thickness
```

### Major Contour Interval

By default, every 50m contour is styled as a "major" contour (thicker, darker, labeled).

To change this, edit line 300 in `viewer.html`:

```javascript
// Change 50 to your preferred interval (e.g., 100 for every 100m)
const isMajor = elevation % 50 === 0;
```

## Using the Map Controls

### Toggle Contours On/Off

Use the "Contour Lines" checkbox in the top-left controls panel to show/hide contours without reloading the page.

### Click for Elevation

Click any contour line to see its elevation value in a popup.

## Understanding the Output

When you run `generate_contours.py`, you'll see:

```
✓ Contours generated successfully!
  Output file: tiles/contours.json (38.5 KB)
  Number of contour lines: 21
  Elevation range: 0.0m to 80.0m
```

This tells you:
- **File size**: Larger = more contours (may affect performance)
- **Number of lines**: Total contour lines generated
- **Elevation range**: Min and max elevation in your data

## Performance Tips

### Large Contour Files

If your contours.json file is very large (>1MB):
1. Increase the contour interval: `python3 generate_contours.py topo.tif 20`
2. The map will load faster with fewer contours
3. You can still see detailed elevation in 3D mode (future feature)

### Optimal Settings by Area Size

| Area Size | Terrain Type | Recommended Interval |
|-----------|-------------|---------------------|
| < 1 km² | Any | 5-10m |
| 1-10 km² | Flat | 10-20m |
| 1-10 km² | Mountainous | 5-10m |
| > 10 km² | Flat | 20-50m |
| > 10 km² | Mountainous | 10-20m |

## Troubleshooting

### "Error: Contours file not found"

**Solution**: Run `python3 generate_contours.py topo.tif` to generate the contours.

### No contours visible on map

**Possible causes:**
1. Zoom level too high/low - zoom in to see contours
2. Contours outside map bounds - verify topo.tif covers the same area as map.tif
3. Check browser console (F12) for errors

### Contours in wrong location

**Cause**: The topo.tif and map.tif must cover the same geographic area.

**Solution**: Ensure both files have compatible:
- Coordinate reference systems (CRS)
- Geographic bounds
- Resolution

Use `gdalinfo` to check:
```bash
gdalinfo map.tif
gdalinfo topo.tif
```

### Too cluttered/too sparse

Adjust the contour interval:
- **Too cluttered**: Increase interval (e.g., from 10 to 20)
- **Too sparse**: Decrease interval (e.g., from 20 to 10)

## Next Steps: 3D Elevation

The current implementation shows contours in 2D. The next phase will add true 3D terrain elevation:

1. **Contour lines** (current): 2D visualization of elevation ✅
2. **3D terrain mesh** (future): Full 3D relief like Google Earth 🚧
3. **Draping imagery** (future): Map texture on 3D terrain 🚧

Stay tuned for the 3D elevation update!

## Technical Details

### GeoJSON Format

The contours are stored as GeoJSON with:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "elevation": 50.0
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [[lon, lat], ...]
      }
    }
  ]
}
```

### Coordinate System

- Input: Whatever CRS your topo.tif uses
- Output: WGS84 (EPSG:4326) for web display
- GDAL automatically handles the reprojection

### Elevation Data Requirements

Your `topo.tif` should be:
- A Digital Elevation Model (DEM) or Digital Terrain Model (DTM)
- Single-band raster with elevation values
- Same geographic extent as your map.tif (or larger)
- Any projection (GDAL will reproject)

Common sources:
- SRTM (30m or 90m resolution)
- ASTER GDEM (30m resolution)
- USGS NED (10m resolution in USA)
- LiDAR-derived DEMs (high resolution)

