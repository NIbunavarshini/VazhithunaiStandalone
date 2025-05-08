import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import random
from datetime import datetime, timedelta
import plotly.express as px

from utils import create_tamil_nadu_map, display_map, MAJOR_CITIES

def load_transportation_data():
    try:
        with open("data/transportation.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty data structure if file not found
        return {"buses": [], "trains": [], "metros": []}

def update_vehicle_locations(data):
    """Simulate movement of vehicles with realistic traffic conditions"""
    current_time = datetime.now()
    
    # Traffic factors based on time of day
    hour = current_time.hour
    if 6 <= hour <= 10:  # Morning rush
        traffic_factor = 1.4
    elif 16 <= hour <= 20:  # Evening rush
        traffic_factor = 1.5
    elif hour < 5 or hour > 22:  # Late night
        traffic_factor = 0.8
    else:  # Normal hours
        traffic_factor = 1.0
        
    # Weather impact (simulated)
    weather_conditions = ['clear', 'rain', 'heavy_rain']
    current_weather = random.choice(weather_conditions)
    weather_factor = 1.0 if current_weather == 'clear' else 1.2 if current_weather == 'rain' else 1.4
    
    # Update bus locations
    for bus in data["buses"]:
        # Simulate movement along route
        start_coords = MAJOR_CITIES.get(bus["route"].split(" to ")[0].strip(), [0, 0])
        end_coords = MAJOR_CITIES.get(bus["route"].split(" to ")[-1].strip(), [0, 0])
        
        # Calculate progress based on schedule with traffic and weather impacts
        schedule = bus["schedule"]
        start_time = datetime.strptime(schedule[0]["time"], "%H:%M").replace(
            year=current_time.year, month=current_time.month, day=current_time.day
        )
        end_time = datetime.strptime(schedule[-1]["time"], "%H:%M").replace(
            year=current_time.year, month=current_time.month, day=current_time.day
        )
        
        # Handle overnight routes
        if end_time < start_time:
            end_time += timedelta(days=1)
        
        # Calculate total duration in seconds with real-time factors
        base_duration = (end_time - start_time).total_seconds()
        total_duration = base_duration * traffic_factor * weather_factor
        
        # Adjust for route type and location
        route_type = "urban" if any(city in bus["route"] for city in ["Chennai", "Coimbatore", "Madurai"]) else "rural"
        route_factor = 1.3 if route_type == "urban" else 1.0
        total_duration *= route_factor
        
        # Calculate elapsed time
        elapsed_time = (current_time - start_time).total_seconds()
        if elapsed_time < 0:  # If before start time
            elapsed_time = 0
        elif elapsed_time > total_duration:  # If after end time
            elapsed_time = total_duration
        
        # Calculate progress (0 to 1)
        progress = elapsed_time / total_duration if total_duration > 0 else 0
        
        # Calculate new position
        new_lat = start_coords[0] + (end_coords[0] - start_coords[0]) * progress
        new_lng = start_coords[1] + (end_coords[1] - start_coords[1]) * progress
        
        # Add some randomness to simulate actual route
        lat_offset = (random.random() - 0.5) * 0.05
        lng_offset = (random.random() - 0.5) * 0.05
        
        bus["current_location"] = [new_lat + lat_offset, new_lng + lng_offset]
        
        # Update ETA
        remaining_time = int((total_duration - elapsed_time) / 60)  # in minutes
        if remaining_time <= 0:
            bus["eta_to_next_stop"] = "Arrived"
        else:
            bus["eta_to_next_stop"] = f"{remaining_time} minutes"
        
        # Randomly update status
        if random.random() < 0.1:  # 10% chance to be delayed
            delay_minutes = random.randint(5, 20)
            bus["current_status"] = f"Delayed by {delay_minutes} minutes"
        else:
            bus["current_status"] = "On Time"
    
    # Similarly update train locations
    for train in data["trains"]:
        start_station = train["schedule"][0]["station"]
        end_station = train["schedule"][-1]["station"]
        
        start_coords = MAJOR_CITIES.get(start_station.split(" ")[0], [0, 0])
        end_coords = MAJOR_CITIES.get(end_station.split(" ")[0], [0, 0])
        
        # Parse departure and arrival times
        try:
            departure_time = train["schedule"][0]["departure"]
            if departure_time == "-":
                departure_time = train["schedule"][1]["departure"]
            
            arrival_time = train["schedule"][-1]["arrival"]
            if arrival_time == "-":
                arrival_time = train["schedule"][-2]["arrival"]
            
            # Convert to datetime objects
            departure_dt = datetime.strptime(departure_time, "%H:%M").replace(
                year=current_time.year, month=current_time.month, day=current_time.day
            )
            arrival_dt = datetime.strptime(arrival_time, "%H:%M").replace(
                year=current_time.year, month=current_time.month, day=current_time.day
            )
            
            # Handle overnight trains
            if arrival_dt < departure_dt:
                arrival_dt += timedelta(days=1)
            
            # Calculate progress
            total_duration = (arrival_dt - departure_dt).total_seconds()
            elapsed_time = (current_time - departure_dt).total_seconds()
            
            if elapsed_time < 0:
                elapsed_time = 0
            elif elapsed_time > total_duration:
                elapsed_time = total_duration
            
            progress = elapsed_time / total_duration if total_duration > 0 else 0
            
            # Calculate new position with some randomness
            new_lat = start_coords[0] + (end_coords[0] - start_coords[0]) * progress
            new_lng = start_coords[1] + (end_coords[1] - start_coords[1]) * progress
            
            lat_offset = (random.random() - 0.5) * 0.1
            lng_offset = (random.random() - 0.5) * 0.1
            
            train["current_location"] = [new_lat + lat_offset, new_lng + lng_offset]
            
            # Update next station and ETA
            for i, stop in enumerate(train["schedule"][:-1]):
                next_stop = train["schedule"][i+1]
                next_arrival = datetime.strptime(next_stop["arrival"], "%H:%M").replace(
                    year=current_time.year, month=current_time.month, day=current_time.day
                )
                
                if next_arrival < departure_dt:
                    next_arrival += timedelta(days=1)
                
                if current_time < next_arrival:
                    train["next_station"] = next_stop["station"]
                    eta_minutes = int((next_arrival - current_time).total_seconds() / 60)
                    train["eta_to_next_station"] = f"{eta_minutes} minutes"
                    break
            
            # Random delays (10% chance)
            if random.random() < 0.1:
                delay_minutes = random.randint(5, 30)
                train["current_status"] = f"Delayed by {delay_minutes} minutes"
            else:
                train["current_status"] = "On Time"
                
        except (ValueError, KeyError):
            # If there's an error parsing times, just keep current values
            pass
    
    # Update metro locations similarly
    for metro in data["metros"]:
        # Metro movement is more predictable, just randomize a bit
        coords = MAJOR_CITIES.get(metro["operator"].split(" ")[0], [0, 0])
        
        # Small random movement around the city
        lat_offset = (random.random() - 0.5) * 0.05
        lng_offset = (random.random() - 0.5) * 0.05
        
        metro["current_location"] = [coords[0] + lat_offset, coords[1] + lng_offset]
        
        # Update ETA (metros are usually more punctual)
        eta_minutes = random.randint(1, 5)
        metro["eta_to_next_station"] = f"{eta_minutes} minutes"
        
        # Usually on time
        if random.random() < 0.05:  # 5% chance to be delayed
            delay_minutes = random.randint(2, 10)
            metro["current_status"] = f"Delayed by {delay_minutes} minutes"
        else:
            metro["current_status"] = "On Time"
    
    return data

def main():
    st.title("🚌 Public Transportation")
    
    # Introduction
    st.markdown("""
    Track public transportation in real-time across Tamil Nadu. Get accurate arrival predictions
    and plan your journey with confidence.
    """)
    
    # Load and update transportation data
    transport_data = load_transportation_data()
    transport_data = update_vehicle_locations(transport_data)
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["Buses", "Trains", "Metro"])
    
    with tab1:
        st.header("Bus Tracking")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            # Extract unique operators and routes
            operators = set(bus["operator"] for bus in transport_data["buses"])
            selected_operator = st.selectbox("Select Operator", ["All"] + list(operators))
        
        with col2:
            # Extract routes
            routes = set(bus["route"] for bus in transport_data["buses"])
            selected_route = st.selectbox("Select Route", ["All"] + list(routes))
        
        # Filter buses based on selection
        filtered_buses = transport_data["buses"]
        if selected_operator != "All":
            filtered_buses = [bus for bus in filtered_buses if bus["operator"] == selected_operator]
        if selected_route != "All":
            filtered_buses = [bus for bus in filtered_buses if bus["route"] == selected_route]
        
        # Bus map
        st.subheader("Live Bus Locations")
        
        # Create a map
        m = create_tamil_nadu_map()
        
        # Add bus markers
        for bus in filtered_buses:
            # Determine color based on status
            color = "green" if "On Time" in bus["current_status"] else "red"
            
            # Create popup content
            popup_html = f"""
            <div style="width:200px">
                <h4>{bus["operator"]} - {bus["route_number"]}</h4>
                <p><b>Route:</b> {bus["route"]}</p>
                <p><b>Type:</b> {bus["type"]}</p>
                <p><b>Status:</b> {bus["current_status"]}</p>
                <p><b>Next Stop:</b> {bus["next_stop"]}</p>
                <p><b>ETA:</b> {bus["eta_to_next_stop"]}</p>
            </div>
            """
            
            # Add marker
            folium.Marker(
                location=bus["current_location"],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{bus['operator']} {bus['route_number']} - {bus['route']}",
                icon=folium.Icon(color=color, icon="bus", prefix="fa")
            ).add_to(m)
        
        # Display the map
        display_map(m)
        
        # List of buses
        st.subheader("Bus Schedule")
        
        if filtered_buses:
            for bus in filtered_buses:
                with st.expander(f"{bus['operator']} {bus['route_number']} - {bus['route']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Type:** {bus['type']}")
                        st.markdown(f"**Vehicle Number:** {bus['vehicle_number']}")
                        st.markdown(f"**Capacity:** {bus['capacity']} seats")
                        st.markdown(f"**Current Status:** {bus['current_status']}")
                        st.markdown(f"**Next Stop:** {bus['next_stop']}")
                        st.markdown(f"**ETA:** {bus['eta_to_next_stop']}")
                    
                    with col2:
                        # Show schedule
                        st.markdown("**Schedule:**")
                        schedule_df = pd.DataFrame(bus["schedule"])
                        st.table(schedule_df)
                        
                        # Add a "Track" button
                        if st.button("Track This Bus", key=f"track_{bus['id']}"):
                            st.success("You will receive notifications about this bus's location.")
        else:
            st.info("No buses found matching your criteria.")
    
    with tab2:
        st.header("Train Tracking")
        
        # Filter options
        train_routes = set(train["route"] for train in transport_data["trains"])
        selected_train_route = st.selectbox("Select Route", ["All"] + list(train_routes), key="train_route")
        
        # Filter trains
        filtered_trains = transport_data["trains"]
        if selected_train_route != "All":
            filtered_trains = [train for train in filtered_trains if train["route"] == selected_train_route]
        
        # Train map
        st.subheader("Live Train Locations")
        
        # Create map
        m = create_tamil_nadu_map()
        
        # Add train markers
        for train in filtered_trains:
            # Determine color
            color = "green" if "On Time" in train["current_status"] else "red"
            
            # Create popup
            popup_html = f"""
            <div style="width:200px">
                <h4>{train["name"]} ({train["train_number"]})</h4>
                <p><b>Route:</b> {train["route"]}</p>
                <p><b>Type:</b> {train["type"]}</p>
                <p><b>Status:</b> {train["current_status"]}</p>
                <p><b>Next Station:</b> {train["next_station"]}</p>
                <p><b>ETA:</b> {train["eta_to_next_station"]}</p>
            </div>
            """
            
            # Add marker
            folium.Marker(
                location=train["current_location"],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{train['name']} - {train['route']}",
                icon=folium.Icon(color=color, icon="train", prefix="fa")
            ).add_to(m)
        
        # Display map
        display_map(m)
        
        # List of trains
        st.subheader("Train Schedule")
        
        if filtered_trains:
            for train in filtered_trains:
                with st.expander(f"{train['name']} ({train['train_number']}) - {train['route']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Type:** {train['type']}")
                        st.markdown(f"**Operator:** {train['operator']}")
                        st.markdown(f"**Current Status:** {train['current_status']}")
                        st.markdown(f"**Next Station:** {train['next_station']}")
                        st.markdown(f"**ETA:** {train['eta_to_next_station']}")
                    
                    with col2:
                        # Show schedule
                        st.markdown("**Schedule:**")
                        schedule_df = pd.DataFrame(train["schedule"])
                        st.table(schedule_df)
                        
                        # Add tracking button
                        if st.button("Track This Train", key=f"track_{train['id']}"):
                            st.success("You will receive notifications about this train's location.")
        else:
            st.info("No trains found matching your criteria.")
    
    with tab3:
        st.header("Metro Tracking")
        
        # Metro map
        st.subheader("Live Metro Locations")
        
        # Only show if there are metros
        if transport_data["metros"]:
            # Create map centered on first metro city
            first_metro = transport_data["metros"][0]
            city_name = first_metro["operator"].split(" ")[0]
            
            m = folium.Map(
                location=MAJOR_CITIES.get(city_name, [13.0827, 80.2707]),
                zoom_start=12,
                tiles="OpenStreetMap"
            )
            
            # Add metro markers
            for metro in transport_data["metros"]:
                # Determine color
                color = "green" if "On Time" in metro["current_status"] else "red"
                
                # Create popup
                popup_html = f"""
                <div style="width:200px">
                    <h4>{metro["line"]}</h4>
                    <p><b>Route:</b> {metro["route"]}</p>
                    <p><b>Operator:</b> {metro["operator"]}</p>
                    <p><b>Status:</b> {metro["current_status"]}</p>
                    <p><b>Next Station:</b> {metro["next_station"]}</p>
                    <p><b>ETA:</b> {metro["eta_to_next_station"]}</p>
                    <p><b>Frequency:</b> {metro["frequency"]}</p>
                </div>
                """
                
                # Add marker
                folium.Marker(
                    location=metro["current_location"],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{metro['line']} - {metro['route']}",
                    icon=folium.Icon(color=color, icon="subway", prefix="fa")
                ).add_to(m)
            
            # Display map
            display_map(m)
            
            # Metro schedule
            st.subheader("Metro Schedule")
            
            for metro in transport_data["metros"]:
                with st.expander(f"{metro['line']} - {metro['route']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Operator:** {metro['operator']}")
                        st.markdown(f"**Current Status:** {metro['current_status']}")
                        st.markdown(f"**Next Station:** {metro['next_station']}")
                        st.markdown(f"**ETA:** {metro['eta_to_next_station']}")
                        st.markdown(f"**Frequency:** {metro['frequency']}")
                    
                    with col2:
                        # Show first/last train times
                        st.markdown("**Station Timings:**")
                        
                        # Create dataframe for station times
                        stations = [station["station"] for station in metro["schedule"]]
                        first_trains = [station["first_train"] for station in metro["schedule"]]
                        last_trains = [station["last_train"] for station in metro["schedule"]]
                        
                        timing_df = pd.DataFrame({
                            "Station": stations,
                            "First Train": first_trains,
                            "Last Train": last_trains
                        })
                        
                        st.table(timing_df)
        else:
            st.info("No metro service information available.")
    
    # Journey Planner
    st.header("Journey Planner")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_point = st.selectbox("Starting Point", list(MAJOR_CITIES.keys()))
    
    with col2:
        end_point = st.selectbox("Destination", list(MAJOR_CITIES.keys()))
    
    travel_date = st.date_input("Travel Date", value=datetime.now().date())
    
    if st.button("Find Routes"):
        if start_point == end_point:
            st.error("Starting point and destination cannot be the same.")
        else:
            st.subheader("Available Routes")
            
            # Simulate route search results
            results = []
            
            # Check if we have any buses on this route
            matching_buses = [
                bus for bus in transport_data["buses"] 
                if start_point in bus["route"] and end_point in bus["route"]
            ]
            
            for bus in matching_buses:
                results.append({
                    "type": "Bus",
                    "operator": bus["operator"],
                    "route": bus["route"],
                    "departure": "08:30 AM",  # Simulated time
                    "arrival": "11:30 AM",    # Simulated time
                    "duration": "3h 0m",
                    "cost": "₹ 150",
                    "details": bus
                })
            
            # Check for train routes
            matching_trains = [
                train for train in transport_data["trains"]
                if start_point in train["route"] and end_point in train["route"]
            ]
            
            for train in matching_trains:
                results.append({
                    "type": "Train",
                    "operator": train["operator"],
                    "route": train["route"],
                    "departure": "09:45 AM",  # Simulated time
                    "arrival": "01:20 PM",    # Simulated time
                    "duration": "3h 35m",
                    "cost": "₹ 350",
                    "details": train
                })
            
            # If no direct matches, generate some dummy routes
            if not results:
                # Generate 2-3 options
                options = ["Bus", "Train", "Bus + Train"]
                durations = ["3h 15m", "4h 0m", "4h 45m"]
                costs = ["₹ 180", "₹ 380", "₹ 250"]
                
                for i in range(min(3, len(options))):
                    results.append({
                        "type": options[i],
                        "operator": "TNSTC" if "Bus" in options[i] else "Southern Railway",
                        "route": f"{start_point} to {end_point}",
                        "departure": "09:00 AM",
                        "arrival": "12:15 PM" if i == 0 else "01:00 PM" if i == 1 else "01:45 PM",
                        "duration": durations[i],
                        "cost": costs[i],
                        "details": None
                    })
            
            # Display results
            for i, result in enumerate(results):
                col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{result['type']}**")
                    st.markdown(f"{result['operator']}")
                
                with col2:
                    st.markdown(f"**{result['route']}**")
                    st.markdown(f"Departure: {result['departure']} • Arrival: {result['arrival']}")
                
                with col3:
                    st.markdown(f"**Duration**")
                    st.markdown(f"{result['duration']}")
                
                with col4:
                    st.markdown(f"**Cost**")
                    st.markdown(f"{result['cost']}")
                    
                    # Book button
                    if st.button("Book", key=f"book_{i}"):
                        st.success(f"Booking initiated for {result['type']} from {start_point} to {end_point} on {travel_date}")
                
                st.divider()
    
    # Tips section
    st.header("Public Transportation Tips")
    
    tips = [
        "Most TNSTC buses accept online bookings through the official website or app.",
        "Chennai Metro offers a 10% discount for payments made through smart cards.",
        "Train tickets can be booked up to 120 days in advance.",
        "Avoid peak hours (8-10 AM and 5-7 PM) for more comfortable travel on public transport.",
        "Download the IRCTC app for easy train ticket booking and live tracking."
    ]
    
    st.info(f"💡 **Tip:** {random.choice(tips)}")

if __name__ == "__main__":
    main()
