import folium
import json
from collections import defaultdict
import heapq

def create_map_html(locations, edges):
    # Create graph for Dijkstra's algorithm
    graph = defaultdict(dict)
    for src, dst, dist in edges:
        graph[src][dst] = dist
        graph[dst][src] = dist

    custom_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Advanced Route Planner</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>
            :root {
                --bg-color: #ffffff;
                --text-color: #333333;
                --card-bg: #ffffff;
                --border-color: #e0e0e0;
            }
            
            [data-theme="dark"] {
                --bg-color: #1a1a1a;
                --text-color: #ffffff;
                --card-bg: #2d2d2d;
                --border-color: #404040;
            }
            
            body {
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-color);
                transition: background-color 0.3s, color 0.3s;
            }
            
            #map { 
                height: 100vh; 
                width: 100%;
                position: absolute;
                top: 0;
                left: 0;
                z-index: 1;
            }
            
            .control-container {
                position: absolute;
                top: 20px;
                right: 20px;
                z-index: 1000;
                background: var(--card-bg);
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                width: 320px;
                backdrop-filter: blur(10px);
                border: 1px solid var(--border-color);
            }
            
            .title {
                margin: 0 0 15px 0;
                font-size: 1.5em;
                font-weight: 600;
                color: var(--text-color);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            select {
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                background: var(--bg-color);
                color: var(--text-color);
                font-size: 14px;
                appearance: none;
            }
            
            .find-route-btn {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: none;
                border-radius: 8px;
                background: #4CAF50;
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            .find-route-btn:hover {
                background: #45a049;
            }
            
            #routeInfo {
                margin-top: 15px;
                padding: 15px;
                background: var(--card-bg);
                border-radius: 8px;
                border: 1px solid var(--border-color);
                display: none;
            }
            
            .theme-toggle {
                position: absolute;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                padding: 10px;
                border-radius: 8px;
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                color: var(--text-color);
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .route-step {
                padding: 8px;
                margin: 4px 0;
                background: var(--bg-color);
                border-radius: 4px;
                border: 1px solid var(--border-color);
            }
            
            .stats-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            .stat-card {
                background: var(--bg-color);
                padding: 10px;
                border-radius: 8px;
                border: 1px solid var(--border-color);
                text-align: center;
            }
            
            .stat-value {
                font-size: 1.2em;
                font-weight: 600;
                color: #4CAF50;
            }
            
            .animation {
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="control-container animation">
            <div class="title">
                <span><i class="fas fa-route"></i> Route Planner</span>
            </div>
            <select id="start">
                <option value="">Select Start City</option>
                ''' + '\n'.join([f'<option value="{city}">{city}</option>' for city in sorted(locations.keys())]) + '''
            </select>
            <select id="end">
                <option value="">Select End City</option>
                ''' + '\n'.join([f'<option value="{city}">{city}</option>' for city in sorted(locations.keys())]) + '''
            </select>
            <button class="find-route-btn" onclick="findRoute()">
                <i class="fas fa-search"></i> Find Shortest Route
            </button>
            <div id="routeInfo"></div>
        </div>
        
        <button class="theme-toggle" onclick="toggleTheme()">
            <i class="fas fa-moon"></i> <span id="themeText">Dark Mode</span>
        </button>

        <script>
            // Initialize map with no wrapping
            var map = L.map('map', {
                worldCopyJump: false,
                maxBounds: [[-90, -180], [90, 180]],
                maxBoundsViscosity: 1.0
            }).setView([20, 0], 2);

            var lightTiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                noWrap: true,
                bounds: [[-90, -180], [90, 180]],
                attribution: '© OpenStreetMap contributors'
            });
            
            var darkTiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                noWrap: true,
                bounds: [[-90, -180], [90, 180]],
                attribution: '© OpenStreetMap contributors'
            });
            
            lightTiles.addTo(map);

            var currentTheme = 'light';
            var currentTiles = lightTiles;

            function toggleTheme() {
                const body = document.body;
                const themeText = document.getElementById('themeText');
                const themeIcon = document.querySelector('.theme-toggle i');
                
                if (currentTheme === 'light') {
                    body.setAttribute('data-theme', 'dark');
                    map.removeLayer(currentTiles);
                    darkTiles.addTo(map);
                    currentTiles = darkTiles;
                    currentTheme = 'dark';
                    themeText.textContent = 'Light Mode';
                    themeIcon.className = 'fas fa-sun';
                } else {
                    body.setAttribute('data-theme', 'light');
                    map.removeLayer(currentTiles);
                    lightTiles.addTo(map);
                    currentTiles = lightTiles;
                    currentTheme = 'light';
                    themeText.textContent = 'Dark Mode';
                    themeIcon.className = 'fas fa-moon';
                }
            }

            var markers = [];
            var paths = [];
            const locations = ''' + json.dumps(locations) + ''';
            const graph = ''' + json.dumps(dict(graph)) + ''';

            function dijkstra(start, end) {
                const distances = {};
                const previous = {};
                const pq = [];
                
                Object.keys(graph).forEach(vertex => {
                    distances[vertex] = Infinity;
                    previous[vertex] = null;
                });
                
                distances[start] = 0;
                pq.push([0, start]);
                
                while (pq.length > 0) {
                    pq.sort((a, b) => a[0] - b[0]);
                    const [currentDistance, currentVertex] = pq.shift();
                    
                    if (currentVertex === end) break;
                    if (currentDistance > distances[currentVertex]) continue;
                    
                    Object.entries(graph[currentVertex] || {}).forEach(([neighbor, weight]) => {
                        const distance = currentDistance + weight;
                        if (distance < distances[neighbor]) {
                            distances[neighbor] = distance;
                            previous[neighbor] = currentVertex;
                            pq.push([distance, neighbor]);
                        }
                    });
                }
                
                const path = [];
                let current = end;
                while (current !== null) {
                    path.unshift(current);
                    current = previous[current];
                }
                
                return [path, distances[end]];
            }

            function clearMap() {
                markers.forEach(marker => map.removeLayer(marker));
                paths.forEach(path => map.removeLayer(path));
                markers = [];
                paths = [];
            }

            function findRoute() {
                const start = document.getElementById('start').value;
                const end = document.getElementById('end').value;
                
                if (!start || !end) {
                    alert('Please select both cities');
                    return;
                }
                
                clearMap();
                
                const [path, distance] = dijkstra(start, end);
                
                if (!path.length) {
                    alert('No route found');
                    return;
                }
                
                // Add markers and path
                path.forEach((city, index) => {
                    const marker = L.circleMarker(locations[city], {
                        radius: 8,
                        fillColor: index === 0 ? '#4CAF50' : (index === path.length - 1 ? '#f44336' : '#2196F3'),
                        color: '#fff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.8
                    }).addTo(map);
                    marker.bindPopup(`<b>${city}</b>`);
                    markers.push(marker);
                });
                
                // Draw path with animation
                for (let i = 0; i < path.length - 1; i++) {
                    const line = L.polyline([
                        locations[path[i]],
                        locations[path[i + 1]]
                    ], {
                        color: '#4CAF50',
                        weight: 3,
                        opacity: 0.8,
                        dashArray: '10, 10'
                    }).addTo(map);
                    paths.push(line);
                }
                
                // Calculate estimated flight time (assuming 800 km/h average speed)
                const flightHours = Math.floor(distance / 800);
                const flightMinutes = Math.round((distance / 800 % 1) * 60);
                
                // Show route info
                const routeInfo = document.getElementById('routeInfo');
                routeInfo.style.display = 'block';
                routeInfo.innerHTML = `
                    <div class="stats-container">
                        <div class="stat-card">
                            <div class="stat-value">${distance.toLocaleString()} km</div>
                            <div>Total Distance</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${flightHours}h ${flightMinutes}m</div>
                            <div>Est. Flight Time</div>
                        </div>
                    </div>
                    <div style="font-weight: 600; margin-bottom: 8px;">Route Details:</div>
                    ${path.map((city, index) => `
                        <div class="route-step">
                            ${index + 1}. ${city}
                        </div>
                    `).join('')}
                `;
                
                // Fit map to show entire route
                const bounds = L.latLngBounds(path.map(city => locations[city]));
                map.fitBounds(bounds, { padding: [50, 50] });
            }
        </script>
    </body>
    </html>
    '''

    with open("World_Map.html", "w", encoding="utf-8") as f:
        f.write(custom_html)

# Rest of the code (locations and edges) remains the same...
# Previous code remains same until locations definition...

# Define locations with multiple cities per country
locations = {
    # United States
    "New York": [40.7128, -74.0060],
    "Los Angeles": [34.0522, -118.2437],
    "Chicago": [41.8781, -87.6298],
    "Miami": [25.7617, -80.1918],
    "San Francisco": [37.7749, -122.4194],
    "Houston": [29.7604, -95.3698],
    "Seattle": [47.6062, -122.3321],

    # United Kingdom
    "London": [51.5074, -0.1278],
    "Manchester": [53.4808, -2.2426],
    "Birmingham": [52.4862, -1.8904],
    "Edinburgh": [55.9533, -3.1883],

    # Germany
    "Berlin": [52.5200, 13.4050],
    "Munich": [48.1351, 11.5820],
    "Frankfurt": [50.1109, 8.6821],
    "Hamburg": [53.5511, 9.9937],

    # France
    "Paris": [48.8566, 2.3522],
    "Lyon": [45.7640, 4.8357],
    "Marseille": [43.2965, 5.3698],
    "Nice": [43.7102, 7.2620],

    # Spain
    "Madrid": [40.4168, -3.7038],
    "Barcelona": [41.3851, 2.1734],
    "Valencia": [39.4699, -0.3763],
    "Seville": [37.3891, -5.9845],

    # Italy
    "Rome": [41.9028, 12.4964],
    "Milan": [45.4642, 9.1900],
    "Venice": [45.4408, 12.3155],
    "Naples": [40.8518, 14.2681],

    # Japan
    "Tokyo": [35.6762, 139.6503],
    "Osaka": [34.6937, 135.5023],
    "Nagoya": [35.1815, 136.9066],
    "Fukuoka": [33.5902, 130.4017],
    "Sapporo": [43.0618, 141.3545],

    # China
    "Beijing": [39.9042, 116.4074],
    "Shanghai": [31.2304, 121.4737],
    "Guangzhou": [23.1291, 113.2644],
    "Shenzhen": [22.5431, 114.0579],
    "Chengdu": [30.5728, 104.0668],
    "Xi'an": [34.3416, 108.9398],

    # India
    "Mumbai": [19.0760, 72.8777],
    "Delhi": [28.6139, 77.2090],
    "Bangalore": [12.9716, 77.5946],
    "Chennai": [13.0827, 80.2707],
    "Kolkata": [22.5726, 88.3639],
    "Hyderabad": [17.3850, 78.4867],

    # Australia
    "Sydney": [-33.8688, 151.2093],
    "Melbourne": [-37.8136, 144.9631],
    "Brisbane": [-27.4705, 153.0260],
    "Perth": [-31.9505, 115.8605],
    "Adelaide": [-34.9285, 138.6007],

    # Russia
    "Moscow": [55.7558, 37.6173],
    "St Petersburg": [59.9311, 30.3609],
    "Novosibirsk": [55.0084, 82.9357],
    "Yekaterinburg": [56.8389, 60.6057],

    # South Korea
    "Seoul": [37.5665, 126.9780],
    "Busan": [35.1796, 129.0756],
    "Incheon": [37.4563, 126.7052],

    # Singapore
    "Singapore": [1.3521, 103.8198],

    # UAE
    "Dubai": [25.2048, 55.2708],
    "Abu Dhabi": [24.4539, 54.3773],
    "Sharjah": [25.3462, 55.4211],

    # Thailand
    "Bangkok": [13.7563, 100.5018],
    "Phuket": [7.8804, 98.3923],
    "Chiang Mai": [18.7883, 98.9853],

    # Brazil
    "Rio de Janeiro": [-22.9068, -43.1729],
    "São Paulo": [-23.5505, -46.6333],
    "Brasília": [-15.7975, -47.8919],
    "Salvador": [-12.9714, -38.5014],

    # Canada
    "Toronto": [43.6532, -79.3832],
    "Vancouver": [49.2827, -123.1207],
    "Montreal": [45.5017, -73.5673],
    "Calgary": [51.0447, -114.0719],

    # Netherlands
    "Amsterdam": [52.3676, 4.9041],
    "Rotterdam": [51.9244, 4.4777],
    "The Hague": [52.0705, 4.3007],

    # Turkey
    "Istanbul": [41.0082, 28.9784],
    "Ankara": [39.9334, 32.8597],
    "Antalya": [36.8969, 30.7133],
    "Izmir": [38.4237, 27.1428],

    # Malaysia
    "Kuala Lumpur": [3.1390, 101.6869],
    "Penang": [5.4141, 100.3288],
    "Johor Bahru": [1.4927, 103.7414],

    # Indonesia
    "Jakarta": [-6.2088, 106.8456],
    "Bali": [-8.3405, 115.0920],
    "Surabaya": [-7.2575, 112.7521],

    # Vietnam
    "Ho Chi Minh City": [10.8231, 106.6297],
    "Hanoi": [21.0285, 105.8542],
    "Da Nang": [16.0544, 108.2022],

    # South Africa
    "Cape Town": [-33.9249, 18.4241],
    "Johannesburg": [-26.2041, 28.0473],
    "Durban": [-29.8587, 31.0218],

    # Egypt
    "Cairo": [30.0444, 31.2357],
    "Alexandria": [31.2001, 29.9187],
    "Sharm El Sheikh": [27.9158, 34.3300]
}

# Define edges - Creating connections between cities
edges = [
    # US Internal Routes
    ("New York", "Chicago", 1190),
    ("New York", "Miami", 1757),
    ("Los Angeles", "San Francisco", 629),
    ("Chicago", "Houston", 1514),
    ("Miami", "Houston", 1565),
    ("Seattle", "San Francisco", 1300),
    
    # UK Internal Routes
    ("London", "Manchester", 261),
    ("London", "Edinburgh", 534),
    ("Birmingham", "Manchester", 116),
    
    # Germany Internal Routes
    ("Berlin", "Munich", 584),
    ("Frankfurt", "Hamburg", 495),
    ("Munich", "Hamburg", 776),
    
    # Major International Routes - North America to Europe
    ("New York", "London", 5570),
    ("New York", "Paris", 5837),
    ("Chicago", "London", 6347),
    ("Los Angeles", "London", 8780),
    ("Toronto", "London", 5711),
    ("Miami", "Madrid", 7103),
    
    # European Routes
    ("London", "Paris", 344),
    ("Paris", "Berlin", 878),
    ("Amsterdam", "Paris", 431),
    ("Madrid", "Paris", 1052),
    ("Rome", "Paris", 1106),
    ("Frankfurt", "Amsterdam", 355),
    
    # Asia Routes
    ("Tokyo", "Seoul", 1157),
    ("Beijing", "Tokyo", 2098),
    ("Shanghai", "Tokyo", 1766),
    ("Hong Kong", "Shanghai", 1255),
    ("Singapore", "Bangkok", 1430),
    ("Kuala Lumpur", "Singapore", 316),
    ("Jakarta", "Singapore", 880),
    
    # Middle East Connections
    ("Dubai", "Mumbai", 1920),
    ("Delhi", "Dubai", 2200),
    ("Abu Dhabi", "Mumbai", 1967),
    ("Istanbul", "Dubai", 3010),
    
    # Australia Internal Routes
    ("Sydney", "Melbourne", 713),
    ("Brisbane", "Sydney", 753),
    ("Perth", "Sydney", 3290),
    
    # Major Routes to Australia
    ("Singapore", "Perth", 3915),
    ("Dubai", "Sydney", 12051),
    ("Hong Kong", "Sydney", 7398),
    
    # South America Routes
    ("São Paulo", "Rio de Janeiro", 429),
    ("São Paulo", "Brasília", 873),
    ("Rio de Janeiro", "Salvador", 1209),
    
    # Africa Routes
    ("Cairo", "Dubai", 2520),
    ("Johannesburg", "Cairo", 6310),
    ("Cape Town", "Johannesburg", 1270),
    
    # Additional Major International Routes
    ("London", "Hong Kong", 9647),
    ("Dubai", "Bangkok", 4890),
    ("Singapore", "Sydney", 6300),
    ("Tokyo", "Los Angeles", 8819),
    ("New York", "São Paulo", 7658),
    ("London", "Cape Town", 9670),
    ("Moscow", "Beijing", 5800),
    ("Singapore", "Shanghai", 3840),
    ("Dubai", "London", 5502),
    
    # Add more edges as needed...
]

# Create the map
create_map_html(locations, edges)
print('Enhanced map has been created as "World_Map.html"')