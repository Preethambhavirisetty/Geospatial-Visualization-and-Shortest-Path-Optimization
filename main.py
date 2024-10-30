import folium
import networkx as nx
from folium.raster_layers import TileLayer
from folium.features import LatLngPopup
import json
import requests

def create_map_html(locations, edges):
    # Download GeoJSON data for countries
    geojson_url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json'
    countries_geojson = requests.get(geojson_url).json()
    
    # Create the graph
    G = nx.Graph()
    for edge in edges:
        G.add_edge(edge[0], edge[1], weight=edge[2])
    
    # Initial map creation
    world_map = folium.Map(
        location=[0, 0],
        zoom_start=2,
        tiles=None,
        control_scale=True,
        min_zoom=2
    )

    # Add custom black and white tile layer
    TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name='CartoDB Positron',
        max_zoom=19,
        no_wrap=True,
        control=True,
        bounds=[[-90, -180], [90, 180]]
    ).add_to(world_map)

    # Create the locations dropdown options
    location_options = "\n".join([f'<option value="{city}">{city}</option>' for city in locations.keys()])

    # Create custom HTML with form inputs and styling
    custom_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>World Map Route Planner</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css"/>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
        <style>
            body {
                margin: 0;
                padding: 0;
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
            .input-container {
                position: fixed;
                bottom: 50px;
                left: 50px;
                z-index: 1000;
                background-color: white;
                padding: 15px;
                border: 2px solid #343a40;
                border-radius: 5px;
                font-family: Arial, sans-serif;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            select {
                width: 200px;
                padding: 5px;
                margin: 5px 0;
                border: 1px solid #343a40;
                border-radius: 3px;
            }
            button {
                background-color: #343a40;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                cursor: pointer;
                margin-top: 10px;
            }
            button:hover {
                background-color: #23272b;
            }
            .distance-display {
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid #dee2e6;
            }
            .distance-label {
                background-color: white;
                border: 1px solid #343a40;
                border-radius: 3px;
                padding: 2px 5px;
                font-size: 12px;
                white-space: nowrap;
            }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="input-container">
            <div>
                <select id="source">
                    <option value="">Select Source</option>
                    ''' + location_options + '''
                </select>
            </div>
            <div>
                <select id="destination">
                    <option value="">Select Destination</option>
                    ''' + location_options + '''
                </select>
            </div>
            <button onclick="calculateRoute()">Calculate Route</button>
            <div id="distance" class="distance-display"></div>
        </div>

        <script>
        // Initialize the map
        var map = L.map('map', {
            center: [0, 0],
            zoom: 2,
            minZoom: 2,
            worldCopyJump: true
        });

        // Add the tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            maxZoom: 19,
            noWrap: true,
            bounds: [[-90, -180], [90, 180]]
        }).addTo(map);

        // Add GeoJSON data
        const countriesData = ''' + json.dumps(countries_geojson) + ''';
        let geojsonLayer = L.geoJSON(countriesData, {
            style: {
                fillColor: '#f8f9fa',
                color: '#343a40',
                weight: 0.5,
                fillOpacity: 0.3
            }
        }).addTo(map);

        // Store the locations and graph data
        const locations = ''' + str(locations) + ''';
        const edges = ''' + str(edges) + ''';
        
        let currentMarkers = [];
        let currentPath = null;
        let currentLabel = null;
        
        function getCountryForCity(cityName) {
            return cityName.split(', ')[1];
        }

        function highlightCountries(sourceCountry, destCountry) {
            geojsonLayer.remove();
            geojsonLayer = L.geoJSON(countriesData, {
                style: function(feature) {
                    const countryName = feature.properties.name;
                    if (countryName === sourceCountry) {
                        return {
                            fillColor: '#90EE90',  // Light green
                            color: '#343a40',
                            weight: 2,
                            fillOpacity: 0.5
                        };
                    } else if (countryName === destCountry) {
                        return {
                            fillColor: '#FFB6C1',  // Light red
                            color: '#343a40',
                            weight: 2,
                            fillOpacity: 0.5
                        };
                    } else {
                        return {
                            fillColor: '#f8f9fa',
                            color: '#343a40',
                            weight: 0.5,
                            fillOpacity: 0.3
                        };
                    }
                }
            }).addTo(map);
        }
        
        function calculateRoute() {
            // Clear existing markers and paths
            currentMarkers.forEach(marker => map.removeLayer(marker));
            currentMarkers = [];
            if (currentPath) {
                map.removeLayer(currentPath);
            }
            if (currentLabel) {
                map.removeLayer(currentLabel);
            }

            const source = document.getElementById('source').value;
            const destination = document.getElementById('destination').value;

            if (!source || !destination) {
                alert('Please select both source and destination');
                return;
            }

            // Add markers for source and destination
            const sourceMarker = L.marker(locations[source], {
                icon: L.divIcon({
                    className: 'custom-div-icon',
                    html: '<div style="background-color: green; width: 10px; height: 10px; border-radius: 50%;"></div>',
                    iconSize: [10, 10]
                })
            }).addTo(map).bindPopup(source);
            currentMarkers.push(sourceMarker);

            const destMarker = L.marker(locations[destination], {
                icon: L.divIcon({
                    className: 'custom-div-icon',
                    html: '<div style="background-color: red; width: 10px; height: 10px; border-radius: 50%;"></div>',
                    iconSize: [10, 10]
                })
            }).addTo(map).bindPopup(destination);
            currentMarkers.push(destMarker);

            // Draw path
            const path = [locations[source], locations[destination]];
            currentPath = L.polyline(path, {
                color: '#343a40',
                weight: 3,
                opacity: 0.7
            }).addTo(map);

            // Calculate rough distance
            const lat1 = locations[source][0];
            const lon1 = locations[source][1];
            const lat2 = locations[destination][0];
            const lon2 = locations[destination][1];
            
            const R = 6371; // Earth's radius in km
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = 
                Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
                Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            const distance = Math.round(R * c);

            // Add distance label at midpoint
            const midLat = (lat1 + lat2) / 2;
            const midLon = (lon1 + lon2) / 2;
            currentLabel = L.marker([midLat, midLon], {
                icon: L.divIcon({
                    className: 'distance-label',
                    html: distance + ' km',
                    iconSize: [50, 20],
                    iconAnchor: [25, 10]
                })
            }).addTo(map);

            document.getElementById('distance').innerHTML = 
                'Approximate Distance: ' + distance + ' km';

            // Highlight countries
            const sourceCountry = getCountryForCity(source);
            const destCountry = getCountryForCity(destination);
            highlightCountries(sourceCountry, destCountry);

            // Fit bounds to show the entire route
            const bounds = L.latLngBounds([locations[source], locations[destination]]);
            map.fitBounds(bounds, {padding: [50, 50]});
        }
        </script>
    </body>
    </html>
    '''

    # Save the custom HTML
    with open("World_Map_with_Custom_Path.html", "w", encoding="utf-8") as f:
        f.write(custom_html)

# Define locations and edges (same as before)
locations = {
    "New York, USA": [40.712776, -74.005974],
    "London, UK": [51.507351, -0.127758],
    "Tokyo, Japan": [35.689487, 139.691711],
    "Paris, France": [48.856613, 2.352222],
    "Berlin, Germany": [52.520008, 13.404954],
    "Sydney, Australia": [-33.868820, 151.209290],
    "Cape Town, South Africa": [-33.924870, 18.424055],
    "Beijing, China": [39.904202, 116.407394],
    "Moscow, Russia": [55.755825, 37.617298],
    "Dubai, UAE": [25.276987, 55.296249],
    "São Paulo, Brazil": [-23.550520, -46.633308],
    "Mumbai, India": [19.076090, 72.877426],
    "Mexico City, Mexico": [19.432608, -99.133209],
    "Toronto, Canada": [43.651070, -79.347015],
    "Buenos Aires, Argentina": [-34.603722, -58.381592],
    "Cairo, Egypt": [30.044420, 31.235712],
    "Istanbul, Turkey": [41.008240, 28.978359],
    "Seoul, South Korea": [37.566536, 126.977966],
    "Singapore, Singapore": [1.352083, 103.819839],
    "Rome, Italy": [41.902782, 12.496366]
}

edges = [
    ("New York, USA", "London, UK", 5571), ("London, UK", "Tokyo, Japan", 9565),
    ("Tokyo, Japan", "Sydney, Australia", 7822), ("Paris, France", "Berlin, Germany", 878),
    ("Berlin, Germany", "Moscow, Russia", 1609), ("Sydney, Australia", "Cape Town, South Africa", 11075),
    ("Cape Town, South Africa", "São Paulo, Brazil", 6454), ("Beijing, China", "Seoul, South Korea", 953),
    ("Moscow, Russia", "Istanbul, Turkey", 1755), ("Dubai, UAE", "Mumbai, India", 1921),
    ("Mumbai, India", "Singapore, Singapore", 3915), ("Mexico City, Mexico", "Toronto, Canada", 3261),
    ("Toronto, Canada", "Buenos Aires, Argentina", 8935), ("Buenos Aires, Argentina", "Cairo, Egypt", 11689),
    ("Cairo, Egypt", "Rome, Italy", 2132), ("Rome, Italy", "Paris, France", 1105),
    ("Istanbul, Turkey", "Dubai, UAE", 2997), ("Seoul, South Korea", "Tokyo, Japan", 1158),
    ("Sydney, Australia", "Singapore, Singapore", 6298), ("Mexico City, Mexico", "New York, USA", 3362)
]

# Create the map
create_map_html(locations, edges)
print('Map has been created and saved as "World_Map_with_Custom_Path.html"')