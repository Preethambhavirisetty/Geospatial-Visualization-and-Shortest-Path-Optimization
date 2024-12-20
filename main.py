import folium
import json
import requests
import math

def create_map_html(locations, edges):
    custom_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>World Route Planner</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"/>
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            #map {
                position: absolute;
                top: 0;
                bottom: 0;
                right: 0;
                left: 0;
                height: 100vh !important;
                width: 100vw !important;
            }
            .control-panel {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                background-color: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                max-width: 320px;
                backdrop-filter: blur(10px);
            }
            .theme-controls {
                position: fixed;
                bottom: 30px;
                right: 20px;
                z-index: 1000;
                background-color: rgba(255, 255, 255, 0.95);
                padding: 10px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                display: flex;
                gap: 10px;
            }
            select {
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
            }
            .calculate-btn {
                width: 100%;
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                cursor: pointer;
                margin-top: 15px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .calculate-btn:hover {
                background-color: #45a049;
            }
            .stats-panel {
                position: fixed;
                bottom: 30px;
                left: 20px;
                z-index: 1000;
                background-color: rgba(255, 255, 255, 0.95);
                padding: 15px;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                display: none;
                backdrop-filter: blur(10px);
                min-width: 250px;
            }
            .theme-btn {
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                background-color: #f8f9fa;
                transition: all 0.3s ease;
            }
            .theme-btn.active {
                background-color: #4CAF50;
                color: white;
            }
            .zoom-controls {
                position: fixed;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                z-index: 1000;
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            .zoom-btn {
                display: block;
                width: 40px;
                height: 40px;
                border: none;
                background-color: white;
                cursor: pointer;
                font-size: 18px;
                color: #333;
            }
            .route-line {
                stroke-dasharray: 8, 8;
                animation: dash 20s linear infinite;
            }
            @keyframes dash {
                to {
                    stroke-dashoffset: -1000;
                }
            }
        </style>
    </head>
    <body>
        <div id="map"></div>
        
        <div class="control-panel">
            <h3 style="margin-top: 0; color: #333;">Route Planner</h3>
            <select id="source">
                <option value="">Select Source City</option>
                ''' + "\n".join([f'<option value="{city}">{city}</option>' for city in sorted(locations.keys())]) + '''
            </select>
            <select id="destination">
                <option value="">Select Destination City</option>
                ''' + "\n".join([f'<option value="{city}">{city}</option>' for city in sorted(locations.keys())]) + '''
            </select>
            <button class="calculate-btn" onclick="calculateRoute()">
                <i class="fas fa-route"></i> Calculate Route
            </button>
        </div>

        <div class="stats-panel" id="statsPanel">
            <h4 style="margin-top: 0; color: #333;">Route Information</h4>
            <div id="routeStats"></div>
        </div>

        <div class="zoom-controls">
            <button class="zoom-btn" onclick="map.zoomIn()"><i class="fas fa-plus"></i></button>
            <button class="zoom-btn" onclick="map.zoomOut()"><i class="fas fa-minus"></i></button>
        </div>

        <div class="theme-controls">
            <button class="theme-btn active" onclick="setMapTheme('light')">
                <i class="fas fa-sun"></i> Light
            </button>
            <button class="theme-btn" onclick="setMapTheme('dark')">
                <i class="fas fa-moon"></i> Dark
            </button>
        </div>

        <script>
        // Initialize map with fixed bounds and no repetition
        let map = L.map('map', {
            center: [20, 0],
            zoom: 2,
            minZoom: 2,
            maxZoom: 8,
            maxBounds: [[-90, -180], [90, 180]],
            maxBoundsViscosity: 1.0,
            worldCopyJump: false,
            zoomControl: false
        });

        // Store current theme and map elements
        let currentTheme = 'light';
        let currentTileLayer = null;
        let currentMarkers = [];
        let currentPath = null;
        const locations = ''' + json.dumps(locations) + ''';

        // Initialize with light theme
        setMapTheme('light');

        function setMapTheme(theme) {
            // Remove current tile layer if exists
            if (currentTileLayer) {
                map.removeLayer(currentTileLayer);
            }

            // Update theme buttons
            document.querySelectorAll('.theme-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`.theme-btn:${theme === 'light' ? 'first-child' : 'last-child'}`).classList.add('active');

            // Set new tile layer based on theme
            const tileUrl = theme === 'light' 
                ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
                : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

            currentTileLayer = L.tileLayer(tileUrl, {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                subdomains: 'abcd',
                maxZoom: 8,
                minZoom: 2,
                noWrap: true,
                bounds: [[-90, -180], [90, 180]],
                maxBounds: [[-90, -180], [90, 180]],
                maxBoundsViscosity: 1.0
            }).addTo(map);

            currentTheme = theme;

            // Update path color if exists
            if (currentPath) {
                currentPath.setStyle({
                    color: theme === 'light' ? '#4CAF50' : '#69f0ae'
                });
            }
        }

        function calculateRoute() {
            // Clear previous route
            clearRoute();

            const source = document.getElementById('source').value;
            const destination = document.getElementById('destination').value;

            if (!source || !destination) {
                alert('Please select both source and destination cities');
                return;
            }

            if (source === destination) {
                alert('Please select different cities for source and destination');
                return;
            }

            const sourceCoords = locations[source];
            const destCoords = locations[destination];

            // Add markers
            addMarker(sourceCoords, '#4CAF50', source);
            addMarker(destCoords, '#f44336', destination);

            // Draw route
            drawRoute(sourceCoords, destCoords);

            // Calculate and display stats
            updateStats(source, destination);

            // Fit bounds with restrictions
            const bounds = L.latLngBounds([sourceCoords, destCoords]);
            map.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 8,
                animate: true
            });
        }

        function addMarker(coords, color, city) {
            const marker = L.marker(coords, {
                icon: L.divIcon({
                    className: 'custom-marker',
                    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.3);"></div>`,
                    iconSize: [16, 16]
                })
            }).addTo(map);

            marker.bindPopup(`<b>${city}</b><br>Lat: ${coords[0].toFixed(4)}<br>Lon: ${coords[1].toFixed(4)}`);
            currentMarkers.push(marker);
        }

        function drawRoute(start, end) {
            // Calculate the two possible paths
            const path1 = [start, end];
            const path2 = [
                start,
                [end[0], end[1] + (end[1] < start[1] ? 360 : -360)]
            ];

            // Calculate which path is shorter
            const d1 = Math.abs(start[1] - end[1]);
            const d2 = Math.abs(start[1] - (end[1] + (end[1] < start[1] ? 360 : -360)));

            currentPath = L.polyline(d1 < d2 ? path1 : path2, {
                color: currentTheme === 'light' ? '#4CAF50' : '#69f0ae',
                weight: 3,
                opacity: 0.8,
                className: 'route-line'
            }).addTo(map);
        }

        function calculateDistance(lat1, lon1, lat2, lon2) {
            const R = 6371; // Earth's radius in km
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = 
                Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
                Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return Math.round(R * c);
        }

        function updateStats(source, dest) {
            const [lat1, lon1] = locations[source];
            const [lat2, lon2] = locations[dest];
            const distance = calculateDistance(lat1, lon1, lat2, lon2);
            
            // Calculate flight time (assuming 800 km/h average speed)
            const hours = Math.floor(distance / 800);
            const minutes = Math.round((distance / 800 % 1) * 60);
            
            // Calculate time difference based on longitude
            const timeDiff = Math.round((lon2 - lon1) * 24 / 360);

            document.getElementById('routeStats').innerHTML = `
                <div style="margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                        <span>Distance:</span>
                        <strong>${distance.toLocaleString()} km</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                        <span>Est. Flight Time:</span>
                        <strong>${hours}h ${minutes}m</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                        <span>Time Difference:</span>
                        <strong>${Math.abs(timeDiff)}h ${timeDiff >= 0 ? 'ahead' : 'behind'}</strong>
                    </div>
                </div>
            `;
            
            document.getElementById('statsPanel').style.display = 'block';
        }

        function clearRoute() {
            currentMarkers.forEach(marker => map.removeLayer(marker));
            currentMarkers = [];
            if (currentPath) {
                map.removeLayer(currentPath);
                currentPath = null;
            }
            document.getElementById('statsPanel').style.display = 'none';
        }
        </script>
    </body>
    </html>
    '''

    with open("World_Map.html", "w", encoding="utf-8") as f:
        f.write(custom_html)

# Define locations and edges
locations = {
    "New York, USA": [40.712776, -74.005974],
    "London, UK": [51.507351, -0.127758],
    "Tokyo, Japan": [35.689487, 139.691711],
    "Paris, France": [48.856613, 2.352222],
    "Beijing, China": [39.904202, 116.407394],
    "Sydney, Australia": [-33.868820, 151.209290],
    "Dubai, UAE": [25.276987, 55.296249],
    "Singapore, Singapore": [1.352083, 103.819839],
    "Mumbai, India": [19.076090, 72.877426],
    "Istanbul, Turkey": [41.008240, 28.978359],
    "São Paulo, Brazil": [-23.550520, -46.633308],
    "Cairo, Egypt": [30.044420, 31.235712],
    "Cape Town, South Africa": [-33.924870, 18.424055],
    "Moscow, Russia": [55.755825, 37.617298],
    "Berlin, Germany": [52.520008, 13.404954]
}

edges = [
    ("New York, USA", "London, UK", 5571),
    ("London, UK", "Paris, France", 344),
    ("Paris, France", "Berlin, Germany", 878),
    ("Berlin, Germany", "Moscow, Russia", 1609),
    ("Moscow, Russia", "Beijing, China", 5800),
    ("Beijing, China", "Tokyo, Japan", 2098),
    ("Dubai, UAE", "Mumbai, India", 1921),
    ("Mumbai, India", "Singapore, Singapore", 3915),
    ("Singapore, Singapore", "Sydney, Australia", 6298)
]

# Create the map
create_map_html(locations, edges)
print('World Map has been created and saved as "World_Map.html"')