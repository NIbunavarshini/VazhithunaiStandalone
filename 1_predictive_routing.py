import streamlit as st
import folium
from streamlit_folium import st_folium
import random
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os

from utils import create_tamil_nadu_map, display_map, MAJOR_CITIES, generate_routes, get_alternative_routes

def main():
    st.title("🗺️ Predictive Route Management")
    
    # Subtitle
    st.markdown("""
    Plan your journey with AI-powered predictions of traffic patterns and get the most efficient routes.
    """)
    
    # Route Planner Section
    st.header("Route Planner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_location = st.selectbox("Starting Point", 
                                     options=list(MAJOR_CITIES.keys()),
                                     index=0)
    
    with col2:
        end_location = st.selectbox("Destination", 
                                   options=list(MAJOR_CITIES.keys()),
                                   index=1)
    
    # Additional options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        departure_time = st.time_input("Departure Time", 
                                      value=datetime.now().time())
    
    with col2:
        vehicle_type = st.selectbox("Vehicle Type", 
                                   options=["Car", "Motorcycle", "Bus", "Truck"])
    
    with col3:
        route_preference = st.selectbox("Route Preference", 
                                       options=["Fastest", "Shortest", "Least Tolls", "Scenic"])
    
    # Generate routes button
    if st.button("Find Routes"):
        if start_location == end_location:
            st.error("Starting point and destination cannot be the same.")
        else:
            with st.spinner("Calculating optimal routes..."):
                # Get route options
                routes = generate_routes(start_location, end_location)
                
                # Display map with routes
                st.subheader("Route Options")
                m = create_tamil_nadu_map()
                
                # Add markers for start and end locations
                start_coords = MAJOR_CITIES[start_location]
                end_coords = MAJOR_CITIES[end_location]
                
                folium.Marker(
                    location=start_coords,
                    popup=start_location,
                    tooltip=f"Start: {start_location}",
                    icon=folium.Icon(color="green", icon="play", prefix="fa")
                ).add_to(m)
                
                folium.Marker(
                    location=end_coords,
                    popup=end_location,
                    tooltip=f"End: {end_location}",
                    icon=folium.Icon(color="red", icon="stop", prefix="fa")
                ).add_to(m)
                
                # Add route lines
                for i, route in enumerate(routes):
                    # Creating waypoints for the route visualization
                    route_points = [start_coords]
                    
                    # Add some intermediate points for visualization
                    # In a real app, these would be actual waypoints
                    intermediate_points = 3
                    for j in range(intermediate_points):
                        # Create points that deviate slightly from a straight line
                        factor = (j + 1) / (intermediate_points + 1)
                        lat = start_coords[0] + (end_coords[0] - start_coords[0]) * factor
                        lng = start_coords[1] + (end_coords[1] - start_coords[1]) * factor
                        
                        # Add some randomness for different routes
                        lat_offset = (random.random() - 0.5) * 0.5
                        lng_offset = (random.random() - 0.5) * 0.5
                        
                        route_points.append([lat + lat_offset, lng + lng_offset])
                    
                    route_points.append(end_coords)
                    
                    # Add route line
                    folium.PolyLine(
                        locations=route_points,
                        tooltip=f"Route {i+1}: {route['name']}",
                        color=route['color'],
                        weight=5,
                        opacity=0.7
                    ).add_to(m)
                
                # Display the map
                display_map(m)
                
                # Display route details
                st.subheader("Route Details")
                
                for i, route in enumerate(routes):
                    expander_label = f"Option {i+1}: {route['name']} ({route['distance']} km, {route['time']} min)"
                    with st.expander(expander_label):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Distance:** {route['distance']} km")
                            st.markdown(f"**Estimated Time:** {route['time']} minutes")
                            st.markdown(f"**Traffic Conditions:** {route['traffic']}")
                            st.markdown(f"**Toll Plazas:** {route.get('toll_plazas', 'N/A')}")
                            
                        with col2:
                            st.markdown(f"**Estimated Fuel Cost:** ₹{round(route['distance'] * 7.5)}")
                            st.markdown(f"**Estimated Toll Cost:** ₹{route.get('estimated_toll_cost', 'N/A')}")
                            
                            arrival_time = (datetime.combine(datetime.today(), departure_time) + 
                                           timedelta(minutes=route['time'])).time()
                            st.markdown(f"**Estimated Arrival:** {arrival_time.strftime('%I:%M %p')}")
                        
                        # Traffic prediction chart (simplified)
                        st.markdown("#### Traffic Prediction")                        
                        # Generate hourly traffic data with more realistic patterns
                        hours = list(range(24))
                        current_hour = datetime.now().hour
                        current_day = datetime.now().weekday()  # 0 = Monday, 6 = Sunday
                        
                        # Create realistic traffic pattern based on time and day
                        traffic_values = []
                        for hour in hours:
                            # Weekday patterns
                            if current_day < 5:  # Monday to Friday
                                # Early morning rush (6-10 AM)
                                if 6 <= hour <= 10:
                                    base = 60 + (hour - 6) * 15  # Gradually increasing
                                # Lunch time (12-2 PM)
                                elif 12 <= hour <= 14:
                                    base = 70
                                # Evening rush (4-8 PM)
                                elif 16 <= hour <= 20:
                                    base = 85 + (20 - abs(hour - 18)) * 5
                                # Late night (10 PM - 5 AM)
                                elif hour < 5 or hour > 22:
                                    base = 15
                                # Other times
                                else:
                                    base = 50
                            else:  # Weekend pattern
                                # Late morning (9-11 AM)
                                if 9 <= hour <= 11:
                                    base = 65
                                # Shopping hours (12-8 PM)
                                elif 12 <= hour <= 20:
                                    base = 75
                                # Late night
                                elif hour < 6 or hour > 22:
                                    base = 20
                                # Other times
                                else:
                                    base = 45
                            
                            # Add weather impact (example: higher traffic during rain)
                            weather_factor = random.choice([1.0, 1.1, 1.2])  # Normal, Light Rain, Heavy Rain
                            
                            # Add location-based congestion
                            if start_location in ['Chennai', 'Coimbatore', 'Madurai']:
                                location_factor = 1.2  # More traffic in major cities
                            else:
                                location_factor = 1.0
                            
                            # Calculate final traffic value
                            traffic = int(base * weather_factor * location_factor)
                            traffic = max(10, min(100, traffic))  # Ensure within bounds
                            traffic_values.append(traffic)
                        
                        # Create DataFrame for the chart
                        traffic_df = pd.DataFrame({
                            'Hour': [f"{h:02d}:00" for h in hours],
                            'Traffic Density (%)': traffic_values
                        })
                        
                        # Highlight current hour
                        traffic_df['Current Time'] = [
                            True if h == current_hour else False for h in hours
                        ]
                        
                        # Create the chart
                        fig = px.line(
                            traffic_df, 
                            x='Hour', 
                            y='Traffic Density (%)',
                            markers=True,
                            color='Current Time',
                            color_discrete_map={True: 'red', False: 'blue'}
                        )
                        
                        fig.update_layout(
                            height=300,
                            margin=dict(l=0, r=0, t=30, b=0),
                            legend_title_text='',
                            hovermode='x'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Navigation button
                        st.button(f"Navigate via Route {i+1}", key=f"nav_route_{i}")
    
    # Traffic alerts section
    st.header("Live Traffic Alerts")
    
    # Load or generate sample traffic alerts
    try:
        with open("data/events.json", "r") as f:
            events = json.load(f)
            
        # Filter to show only active events
        active_events = [e for e in events if e["status"] == "Active"]
        
        if active_events:
            for event in active_events[:3]:  # Show only top 3 alerts
                alert_type = event["type"]
                alert_color = "red" if event["severity"] == "High" else "orange" if event["severity"] == "Medium" else "blue"
                
                st.warning(f"**{alert_type} Alert:** {event['description']} in {event['location']}. Severity: {event['severity']}")
        else:
            st.info("No major traffic alerts at this time.")
    except (FileNotFoundError, json.JSONDecodeError):
        st.info("No major traffic alerts at this time.")
    
    # Tips section
    st.header("Traffic Tips")
    
    tips = [
        "The best time to travel between Chennai and Coimbatore is early morning (4-6 AM) to avoid traffic.",
        "During monsoon season, coastal roads may experience flooding. Plan alternative routes.",
        "Major cities experience high traffic between 8-10 AM and 5-8 PM on weekdays.",
        "Weekends typically have less traffic in the mornings but more in the evenings near shopping areas.",
        "Plan for additional travel time during festival seasons like Pongal and Diwali."
    ]
    
    tip_index = random.randint(0, len(tips) - 1)
    st.info(f"💡 **Tip of the day:** {tips[tip_index]}")

if __name__ == "__main__":
    main()
