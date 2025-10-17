// ============================================================
// CONFIGURATION - UPDATE THESE VALUES AFTER UPLOADING TO CESIUM ION
// ============================================================
// Get your access token from: https://ion.cesium.com/tokens
// Get your terrain Asset ID from: https://ion.cesium.com/assets (after uploading cesiumionheightmap.tif)
const CONFIG = {
    CESIUM_ION_ACCESS_TOKEN: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkZjBjNjUxZS1lNDRhLTQwYTMtYjNhOS01ZmE4MmJhMTc4NDEiLCJpZCI6MzUxMzkwLCJpYXQiOjE3NjA2ODAzMjZ9.I6gP9sgtFWWDdjuXwCLk1GlqQIzDL2mh-lcqeA8QKqk',
    TERRAIN_ASSET_ID: 3925137  // ← UPDATE THIS with your Asset ID from Cesium ion
};
// ============================================================

// Set Cesium Ion access token
Cesium.Ion.defaultAccessToken = CONFIG.CESIUM_ION_ACCESS_TOKEN;

// Load metadata.json for map bounds (with cache busting)
fetch('tiles/metadata.json?v=' + Date.now())
    .then(response => response.json())
    .then(metadata => {
        console.log('Loaded metadata:', metadata);
        initializeViewer(metadata);
    })
    .catch(error => {
        console.warn('Could not load metadata.json:', error);
        console.log('Using fallback coordinates');
        // Fallback to default coordinates
        initializeViewer({
            west: 0,
            south: 0,
            east: 1,
            north: 1
        });
    });

async function initializeViewer(metadata) {
    // Use metadata directly (now has correct coordinates)
    const west = metadata.west;     // longitude
    const south = metadata.south;   // latitude
    const east = metadata.east;     // longitude
    const north = metadata.north;   // latitude
    
    console.log('Map bounds:', { west, south, east, north });
    
    // Create the Cesium viewer
    const viewer = new Cesium.Viewer('cesiumContainer', {
        // Imagery settings
        baseLayerPicker: false,  // No base layer picker (we're only using custom tiles)
        imageryProvider: false,  // We'll add our custom provider manually
        
        // Terrain will be set after viewer creation
        terrainProvider: false,

        // UI controls
        animation: false,  // No animation timeline
        timeline: false,  // No timeline
        fullscreenButton: true,
        vrButton: false,
        geocoder: false,  // No geocoder (would require Ion services)
        homeButton: true,
        infoBox: true,
        sceneModePicker: true,  // Allow 2D/3D switching
        selectionIndicator: false,
        navigationHelpButton: true,
        
        // Scene settings
        scene3DOnly: false,  // Allow 2D and 3D modes
        shadows: false,  // No shadows for better performance
        
        // Credit settings
        creditContainer: document.createElement('div'),  // Hide credits in custom div
    });
    
    // Set terrain provider using Cesium Ion asset (using configured Asset ID)
    viewer.scene.setTerrain(
        new Cesium.Terrain(
            Cesium.CesiumTerrainProvider.fromIonAssetId(CONFIG.TERRAIN_ASSET_ID),
        ),
    );
    
    // Configure scene for better visuals with terrain
    viewer.scene.globe.enableLighting = true;  // Enable lighting to see terrain relief
    viewer.scene.globe.depthTestAgainstTerrain = true;  // Proper depth testing with terrain
    viewer.scene.fog.enabled = true;
    viewer.scene.fog.density = 0.0001;
    
    // Optional: Add vertical exaggeration to make terrain more visible
    // Adjust this value (1.0 = no exaggeration, 2.0 = 2x height, etc.)
    viewer.scene.verticalExaggeration = 2.0;

    // Customize camera controls for intuitive navigation
    const scene = viewer.scene;
    const camera = viewer.camera;
    const controller = scene.screenSpaceCameraController;
    
    // Configure custom mouse controls:
    // - Left drag (no modifier) = Pan/translate
    // - Shift + left drag = Rotate/look around
    // - Right drag or Ctrl + left drag = Tilt
    // - Scroll = Zoom
    
    // Keep zoom and translation enabled
    controller.enableZoom = true;
    controller.enableTranslate = true;
    controller.enableLook = true;
    controller.enableTilt = true;
    controller.enableRotate = true;
    
    // Set up the event mappings - must use correct object syntax for modifiers
    controller.translateEventTypes = Cesium.CameraEventType.LEFT_DRAG;
    
    controller.lookEventTypes = {
        eventType: Cesium.CameraEventType.LEFT_DRAG,
        modifier: Cesium.KeyboardEventModifier.SHIFT
    };
    
    controller.tiltEventTypes = [
        Cesium.CameraEventType.RIGHT_DRAG,
        Cesium.CameraEventType.MIDDLE_DRAG,
        {
            eventType: Cesium.CameraEventType.LEFT_DRAG,
            modifier: Cesium.KeyboardEventModifier.CTRL
        }
    ];
    
    controller.zoomEventTypes = [
        Cesium.CameraEventType.WHEEL,
        Cesium.CameraEventType.PINCH
    ];
    
    // Enable keyboard controls (arrow keys, +/-, spacebar for stopping inertia)
    controller.enableInputs = true;
    
    console.log('Custom camera controls enabled: Drag=Pan, Shift+Drag=Look, Right/Ctrl+Drag=Tilt');
    
    // Calculate bounds for custom tiles using corrected coordinates
    const rectangle = Cesium.Rectangle.fromDegrees(
        west,
        south,
        east,
        north
    );
    
    // Add custom imagery layer from our tiles
    // Using XYZ tile scheme (matches gdal2tiles --xyz output)
    const customImageryProvider = new Cesium.UrlTemplateImageryProvider({
        url: window.location.origin + '/tiles/{z}/{x}/{y}.png',
        tilingScheme: new Cesium.WebMercatorTilingScheme(),
        rectangle: rectangle,  // Constrain to actual map bounds
        minimumLevel: 10,
        maximumLevel: 22,
        tileWidth: 256,
        tileHeight: 256,
        hasAlphaChannel: true,
        credit: 'Custom Map Data'
    });
    
    // Add the custom imagery layer
    const customLayer = viewer.imageryLayers.addImageryProvider(customImageryProvider);
    customLayer.alpha = 1.0;  // Full opacity
    
    // No base layer needed - just showing custom tiles on blank globe
    // (Cesium's base layer would require Ion token/subscription)
    
    // Calculate center of the map bounds
    const centerLon = (west + east) / 2;
    const centerLat = (south + north) / 2;
    
    console.log(`Map center: Lon=${centerLon.toFixed(6)}, Lat=${centerLat.toFixed(6)}`);
    
    // Set camera height for small area (zoom in close to see tiles)
    let cameraHeight = 1500;  // 1.5km height - close view
    
    // Set camera position immediately (no fly animation) 
    viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(centerLon, centerLat, cameraHeight),
        orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-90),  // Look straight down initially
            roll: 0.0
        }
    });
    
   
    
    // Set home view to our custom area
    viewer.homeButton.viewModel.command.beforeExecute.addEventListener(function(e) {
        e.cancel = true;
        viewer.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(centerLon, centerLat, cameraHeight),
            orientation: {
                heading: Cesium.Math.toRadians(0),
                pitch: Cesium.Math.toRadians(-90),
                roll: 0.0
            }
        });
    });
    
    // Add keyboard controls - Space to reset view
    document.addEventListener('keydown', function(e) {
        if (e.code === 'Space' && !e.repeat) {
            e.preventDefault();
            // Reset to home view
            viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(centerLon, centerLat, cameraHeight),
                orientation: {
                    heading: Cesium.Math.toRadians(0),
                    pitch: Cesium.Math.toRadians(-90),
                    roll: 0.0
                },
                duration: 1.0  // 1 second animation
            });
        }
    });
    
    console.log('Cesium viewer initialized successfully!');
    console.log(`Map bounds: [${west.toFixed(6)}, ${south.toFixed(6)}] to [${east.toFixed(6)}, ${north.toFixed(6)}]`);
    console.log(`Camera position: Lon=${centerLon.toFixed(6)}, Lat=${centerLat.toFixed(6)}, Height=${cameraHeight}m`);
}

