import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta

# Coordinates for Tamil Nadu
TAMIL_NADU_CENTER = [11.1271, 78.6569]
TAMIL_NADU_ZOOM = 7

# Major cities in Tamil Nadu with coordinates
MAJOR_CITIES = {
    "Chennai": [13.0827, 80.2707],
    "Coimbatore": [11.0168, 76.9558],
    "Madurai": [9.9252, 78.1198],
    "Tiruchirappalli": [10.7905, 78.7047],
    "Salem": [11.6643, 78.1460],
    "Vellore": [12.9165, 79.1325],
    "Tirunelveli": [8.7139, 77.7567],
    "Thoothukudi": [8.7642, 78.1348],
    "Erode": [11.3410, 77.7172],
    "Thanjavur": [10.7870, 79.1378]
}

# Traffic conditions
TRAFFIC_CONDITIONS = ["Light", "Moderate", "Heavy", "Very Heavy", "Gridlock"]
TRAFFIC_COLORS = {
    "Light": "green",
    "Moderate": "blue",
    "Heavy": "orange",
    "Very Heavy": "red",
    "Gridlock": "darkred"
}

# Function to create a base Tamil Nadu map
def create_tamil_nadu_map(center=TAMIL_NADU_CENTER, zoom=TAMIL_NADU_ZOOM):
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
    
    # Add major cities
    for city, coords in MAJOR_CITIES.items():
        folium.Marker(
            location=coords,
            popup=city,
            tooltip=city,
            icon=folium.Icon(icon="city", prefix="fa")
        ).add_to(m)
    
    return m

# Function to display a folium map in Streamlit
def display_map(map_object):
    return st_folium(map_object, width=800, height=500, returned_objects=[])

# Function to generate routes between two locations
def generate_routes(start, end, num_routes=3):
    # Load routes from JSON file
    try:
        with open("data/routes.json", "r") as f:
            routes_data = json.load(f)
            
        # Filter routes based on start and end
        filtered_routes = [r for r in routes_data if r["start"] == start and r["end"] == end]
        
        # If routes exist, return them
        if filtered_routes:
            return filtered_routes[:num_routes]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Generate synthetic routes if none exist in file
    base_distance = calculate_distance(MAJOR_CITIES.get(start, TAMIL_NADU_CENTER), 
                                     MAJOR_CITIES.get(end, TAMIL_NADU_CENTER))
    
    routes = []
    for i in range(num_routes):
        # Variation in distance and time
        distance_factor = 1 + (random.random() - 0.5) * 0.4  # ±20% variation
        time_factor = 1 + (random.random() - 0.3) * 0.6      # +30%/-30% variation
        
        distance = round(base_distance * distance_factor, 1)
        time = round(distance * 1.5 * time_factor)  # Approx. 1.5 min per km
        
        traffic_index = min(4, int(time_factor * 2.5))
        traffic = TRAFFIC_CONDITIONS[traffic_index]
        
        route = {
            "id": f"{start}-{end}-{i+1}",
            "name": f"Via {random.choice(list(MAJOR_CITIES.keys()))}",
            "start": start,
            "end": end,
            "distance": distance,
            "time": time,
            "traffic": traffic,
            "color": TRAFFIC_COLORS[traffic]
        }
        routes.append(route)
    
    return routes

# Function to calculate distance between two coordinates (in km)
def calculate_distance(coord1, coord2):
    # Simple Euclidean distance - not accurate for actual distances but good enough for simulation
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return round(c * r, 1)

# Function to get alternative routes
def get_alternative_routes(start, end, event_location=None, num_routes=3):
    routes = generate_routes(start, end, num_routes + 1)
    
    # If there's an event, mark the most affected route
    if event_location:
        # Find the route most likely to be affected by the event
        # For simplicity, we'll just mark the shortest route as affected
        routes.sort(key=lambda x: x["distance"])
        routes[0]["affected_by_event"] = True
        routes[0]["traffic"] = "Very Heavy"
        routes[0]["color"] = "red"
        routes[0]["time"] = round(routes[0]["time"] * 1.5)  # 50% longer due to event
    
    return routes

# Function to load JSON data
def load_json_data(filename):
    try:
        with open(f"data/{filename}", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Function to save JSON data
def save_json_data(data, filename):
    os.makedirs("data", exist_ok=True)
    with open(f"data/{filename}", "w") as f:
        json.dump(data, f, indent=4)

# Function to generate a unique ID
def generate_id(prefix="item"):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices('0123456789', k=4))
    return f"{prefix}_{timestamp}_{random_suffix}"
