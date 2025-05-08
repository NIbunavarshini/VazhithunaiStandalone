import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import random
from datetime import datetime, timedelta
import plotly.express as px

from utils import create_tamil_nadu_map, display_map, MAJOR_CITIES, generate_routes

def load_charging_stations():
    try:
        with open("data/charging_stations.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def update_station_availability(stations):
    """Simulate changes in charging station availability for demo purposes"""
    current_time = datetime.now()
    
    for station in stations:
        # Randomly update available ports
        change = random.randint(-1, 1)
        new_available = station["available_ports"] + change
        
        # Ensure available ports is within bounds
        station["available_ports"] = max(0, min(station["total_ports"], new_available))
        
        # Update status based on availability
        if station["available_ports"] == 0:
            station["status"] = "Fully Occupied"
        elif station["available_ports"] < 0.3 * station["total_ports"]:
            station["status"] = "Limited Availability"
        else:
            station["status"] = "Operational"
    
    return stations

def main():
    st.title("⚡ EV Charging Stations")
    
    # Introduction
    st.markdown("""
    Find electric vehicle charging stations across Tamil Nadu. Get real-time availability updates 
    and plan your charging stops efficiently.
    """)
    
    # Load and update charging station data
    charging_stations = load_charging_stations()
    charging_stations = update_station_availability(charging_stations)
    
    # Main navigation tabs
    tab1, tab2, tab3 = st.tabs(["Find Stations", "Route Planner", "Charging Tips"])
    
    with tab1:
        st.header("Find Charging Stations")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # City filter
            locations = sorted(list(set(station["location"] for station in charging_stations)))
            selected_location = st.selectbox(
                "Location",
                options=["All"] + locations
            )
        
        with col2:
            # Charger type filter
            all_charger_types = []
            for station in charging_stations:
                all_charger_types.extend(station["charger_types"])
            charger_types = sorted(list(set(all_charger_types)))
            
            selected_charger_type = st.selectbox(
                "Charger Type",
                options=["All"] + charger_types
            )
        
        with col3:
            # Availability filter
            availability_filter = st.selectbox(
                "Availability",
                options=["All", "Available Now", "Fully Occupied"]
            )
        
        # Apply filters
        filtered_stations = charging_stations
        
        if selected_location != "All":
            filtered_stations = [s for s in filtered_stations if s["location"] == selected_location]
        
        if selected_charger_type != "All":
            filtered_stations = [s for s in filtered_stations if selected_charger_type in s["charger_types"]]
        
        if availability_filter == "Available Now":
            filtered_stations = [s for s in filtered_stations if s["available_ports"] > 0]
        elif availability_filter == "Fully Occupied":
            filtered_stations = [s for s in filtered_stations if s["available_ports"] == 0]
        
        # Map view
        st.subheader("Charging Station Map")
        
        # Create map
        if selected_location != "All" and selected_location in MAJOR_CITIES:
            map_center = MAJOR_CITIES[selected_location]
            zoom = 12
        else:
            map_center = [11.1271, 78.6569]  # Center of Tamil Nadu
            zoom = 7
        
        m = folium.Map(location=map_center, zoom_start=zoom, tiles="OpenStreetMap")
        
        # Add station markers
        for station in filtered_stations:
            # Determine marker color based on availability
            if station["available_ports"] == 0:
                color = "red"
            elif station["available_ports"] < station["total_ports"] / 2:
                color = "orange"
            else:
                color = "green"
            
            # Create popup content
            popup_html = f"""
            <div style="width:250px">
                <h4>{station["name"]}</h4>
                <p><b>Operator:</b> {station["operator"]}</p>
                <p><b>Availability:</b> {station["available_ports"]}/{station["total_ports"]} ports</p>
                <p><b>Charger Types:</b> {', '.join(station["charger_types"])}</p>
                <p><b>Power Levels:</b> {', '.join(station["power_levels"])}</p>
                <p><b>Hours:</b> {station["operating_hours"]}</p>
                <p><b>Payment:</b> {', '.join(station["payment_methods"])}</p>
                <p><b>Amenities:</b> {', '.join(station["amenities"])}</p>
                <p><b>Address:</b> {station["address"]}</p>
            </div>
            """
            
            # Add marker
            folium.Marker(
                location=station["coordinates"],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{station['name']} ({station['available_ports']}/{station['total_ports']} available)",
                icon=folium.Icon(color=color, icon="plug", prefix="fa")
            ).add_to(m)
        
        # Display the map
        display_map(m)
        
        # List view
        st.subheader("Charging Station List")
        
        if filtered_stations:
            for station in filtered_stations:
                # Determine status color
                if station["available_ports"] == 0:
                    status_color = "red"
                elif station["available_ports"] < station["total_ports"] / 2:
                    status_color = "orange"
                else:
                    status_color = "green"
                
                # Create expandable card
                with st.expander(f"{station['name']} - {station['location']} ({station['available_ports']}/{station['total_ports']} available)"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Operator:** {station['operator']}")
                        st.markdown(f"**Address:** {station['address']}")
                        st.markdown(f"**Charger Types:** {', '.join(station['charger_types'])}")
                        st.markdown(f"**Power Levels:** {', '.join(station['power_levels'])}")
                        st.markdown(f"**Operating Hours:** {station['operating_hours']}")
                    
                    with col2:
                        st.markdown(f"**Status:** <span style='color:{status_color};'>{station['status']}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Payment Methods:** {', '.join(station['payment_methods'])}")
                        st.markdown(f"**Amenities:** {', '.join(station['amenities'])}")
                        
                        # Check-in button
                        if st.button("Navigate Here", key=f"nav_{station['id']}"):
                            st.success(f"Navigating to {station['name']}. Directions would be shown here in a real app.")
                        
                        # Reserve button
                        if station["available_ports"] > 0:
                            if st.button("Reserve Port", key=f"reserve_{station['id']}"):
                                st.success(f"Charging port reserved at {station['name']}. You have 30 minutes to arrive.")
                        else:
                            st.error("No ports available for reservation at this station.")
        else:
            st.info("No charging stations found matching your criteria.")
    
    with tab2:
        st.header("EV Route Planner")
        
        st.markdown("""
        Plan your journey with charging stops along the way. This intelligent route planner will suggest
        the most efficient charging stops based on your vehicle's range and charging requirements.
        """)
        
        # Route planning form
        col1, col2 = st.columns(2)
        
        with col1:
            start_location = st.selectbox(
                "Starting Point",
                options=list(MAJOR_CITIES.keys()),
                key="ev_start"
            )
        
        with col2:
            end_location = st.selectbox(
                "Destination",
                options=list(MAJOR_CITIES.keys()),
                key="ev_end"
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vehicle_range = st.number_input(
                "Vehicle Range (km)",
                min_value=100,
                max_value=800,
                value=300,
                step=50
            )
        
        with col2:
            current_charge = st.slider(
                "Current Charge (%)",
                min_value=10,
                max_value=100,
                value=80,
                step=5
            )
        
        with col3:
            preferred_charger = st.selectbox(
                "Preferred Charger Type",
                options=["Any", "Type 2 AC", "CCS DC", "CHAdeMO"]
            )
        
        if st.button("Plan Route"):
            if start_location == end_location:
                st.error("Starting point and destination cannot be the same.")
            else:
                # Calculate route details
                st.subheader("Route Overview")
                
                # Get routes
                routes = generate_routes(start_location, end_location)
                
                # Select best route for EV
                selected_route = routes[0]  # In a real app, would select best route for EV
                
                # Display route map
                m = create_tamil_nadu_map()
                
                # Add markers for start and end
                folium.Marker(
                    location=MAJOR_CITIES[start_location],
                    popup=start_location,
                    tooltip=f"Start: {start_location}",
                    icon=folium.Icon(color="green", icon="play", prefix="fa")
                ).add_to(m)
                
                folium.Marker(
                    location=MAJOR_CITIES[end_location],
                    popup=end_location,
                    tooltip=f"End: {end_location}",
                    icon=folium.Icon(color="red", icon="stop", prefix="fa")
                ).add_to(m)
                
                # Calculate charge requirements
                total_distance = selected_route["distance"]
                range_at_current_charge = vehicle_range * (current_charge / 100)
                
                # Determine if charging stops are needed
                num_charging_stops = 0
                remaining_range = range_at_current_charge
                
                charging_stations_on_route = []
                
                while remaining_range < total_distance:
                    # Find an appropriate charging station
                    # In a real app, would use actual locations along route
                    # For demo, just pick random stations
                    
                    # Filter stations based on preferred charger
                    available_stations = [
                        station for station in charging_stations 
                        if station["available_ports"] > 0 and
                        (preferred_charger == "Any" or preferred_charger in station["charger_types"])
                    ]
                    
                    if available_stations:
                        selected_station = random.choice(available_stations)
                        
                        # Calculate distance covered before this stop (simplified)
                        distance_covered = remaining_range * 0.8  # Leave 20% buffer
                        
                        # Calculate progress along route (0-1)
                        progress = min(1.0, distance_covered / total_distance)
                        
                        # Interpolate position along route
                        start_coords = MAJOR_CITIES[start_location]
                        end_coords = MAJOR_CITIES[end_location]
                        
                        station_lat = start_coords[0] + progress * (end_coords[0] - start_coords[0])
                        station_lng = start_coords[1] + progress * (end_coords[1] - start_coords[1])
                        
                        # Override station coordinates for demo purposes
                        selected_station["interpolated_coords"] = [station_lat, station_lng]
                        
                        # Track this station
                        charging_stations_on_route.append({
                            "station": selected_station,
                            "distance_from_start": distance_covered,
                            "charge_needed": 90 - (current_charge - (distance_covered / vehicle_range * 100)),
                            "charging_time": random.randint(20, 45)  # minutes
                        })
                        
                        # Update remaining range
                        remaining_range = vehicle_range - (total_distance - distance_covered)
                        
                        num_charging_stops += 1
                    else:
                        st.warning("Not enough charging stations available for this route. Consider a different vehicle or charger type.")
                        break
                
                # Add route line
                route_coords = [MAJOR_CITIES[start_location]]
                
                # Add charging stops to route
                for stop in charging_stations_on_route:
                    route_coords.append(stop["station"]["interpolated_coords"])
                
                route_coords.append(MAJOR_CITIES[end_location])
                
                # Add polyline
                folium.PolyLine(
                    locations=route_coords,
                    color=selected_route["color"],
                    weight=5,
                    opacity=0.7
                ).add_to(m)
                
                # Add charging station markers
                for i, stop in enumerate(charging_stations_on_route):
                    station = stop["station"]
                    
                    # Create popup
                    popup_html = f"""
                    <div style="width:250px">
                        <h4>{station["name"]} (Stop {i+1})</h4>
                        <p><b>Distance from start:</b> {round(stop["distance_from_start"], 1)} km</p>
                        <p><b>Charge needed:</b> {round(stop["charge_needed"])}%</p>
                        <p><b>Estimated charging time:</b> {stop["charging_time"]} minutes</p>
                        <p><b>Operator:</b> {station["operator"]}</p>
                        <p><b>Charger Types:</b> {', '.join(station["charger_types"])}</p>
                        <p><b>Amenities:</b> {', '.join(station["amenities"])}</p>
                    </div>
                    """
                    
                    # Add marker
                    folium.Marker(
                        location=station["interpolated_coords"],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"Charging Stop {i+1}: {station['name']}",
                        icon=folium.Icon(color="blue", icon="plug", prefix="fa")
                    ).add_to(m)
                
                # Display map
                display_map(m)
                
                # Display route summary
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Distance", f"{selected_route['distance']} km")
                
                with col2:
                    st.metric("Estimated Time", f"{selected_route['time']} min")
                
                with col3:
                    st.metric("Charging Stops", str(num_charging_stops))
                
                # Display charging stops details
                if charging_stations_on_route:
                    st.subheader("Charging Stops")
                    
                    for i, stop in enumerate(charging_stations_on_route):
                        station = stop["station"]
                        
                        with st.expander(f"Stop {i+1}: {station['name']} (at {round(stop['distance_from_start'], 1)} km)"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**Charge Needed:** {round(stop['charge_needed'])}%")
                                st.markdown(f"**Charging Time:** {stop['charging_time']} minutes")
                                st.markdown(f"**Operator:** {station['operator']}")
                                st.markdown(f"**Charger Types:** {', '.join(station['charger_types'])}")
                            
                            with col2:
                                st.markdown(f"**Power Levels:** {', '.join(station['power_levels'])}")
                                st.markdown(f"**Payment Methods:** {', '.join(station['payment_methods'])}")
                                st.markdown(f"**Amenities:** {', '.join(station['amenities'])}")
                                
                                # Reserve button
                                if st.button("Reserve Charger", key=f"reserve_route_{station['id']}"):
                                    st.success(f"Charger reserved at {station['name']}. You will receive a confirmation code.")
                
                # Battery status visualization
                st.subheader("Battery Status During Journey")
                
                # Generate battery level data points
                battery_data = []
                
                # Starting point
                battery_data.append({
                    "Distance": 0,
                    "Location": start_location,
                    "Battery": current_charge
                })
                
                remaining_charge = current_charge
                current_distance = 0
                
                # Add data for each segment
                for i, stop in enumerate(charging_stations_on_route):
                    # Calculate battery drain
                    segment_distance = stop["distance_from_start"] - current_distance
                    charge_used = (segment_distance / vehicle_range) * 100
                    remaining_charge -= charge_used
                    
                    # Add data point before charging
                    battery_data.append({
                        "Distance": stop["distance_from_start"],
                        "Location": f"Arriving at Stop {i+1}",
                        "Battery": max(0, remaining_charge)
                    })
                    
                    # Add data point after charging
                    remaining_charge = 90  # Assume charging to 90%
                    current_distance = stop["distance_from_start"]
                    
                    battery_data.append({
                        "Distance": stop["distance_from_start"],
                        "Location": f"Leaving Stop {i+1}",
                        "Battery": remaining_charge
                    })
                
                # Add end point
                final_segment_distance = selected_route["distance"] - current_distance
                final_charge_used = (final_segment_distance / vehicle_range) * 100
                remaining_charge -= final_charge_used
                
                battery_data.append({
                    "Distance": selected_route["distance"],
                    "Location": end_location,
                    "Battery": max(0, remaining_charge)
                })
                
                # Create DataFrame
                battery_df = pd.DataFrame(battery_data)
                
                # Create chart
                fig = px.line(
                    battery_df,
                    x="Distance",
                    y="Battery",
                    markers=True,
                    labels={"Battery": "Battery Charge (%)", "Distance": "Distance (km)"},
                    hover_data=["Location"]
                )
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=30, b=10),
                    hovermode="x"
                )
                
                # Add danger threshold line
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=20,
                    x1=selected_route["distance"],
                    y1=20,
                    line=dict(color="red", dash="dash"),
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Save route button
                if st.button("Save Route"):
                    st.success("Route saved successfully. You can access it from your saved routes.")
    
    with tab3:
        st.header("EV Charging Tips")
        
        # Charging tips
        tips = [
            {
                "title": "Optimal Charging Levels",
                "content": "For daily use, it's best to charge your EV to 80-90% rather than 100% to extend battery life. Similarly, try not to let it drop below 20% regularly."
            },
            {
                "title": "Peak Hours",
                "content": "Most charging stations are busiest between 5-7 PM. Try to plan your charging sessions outside these hours to avoid waiting."
            },
            {
                "title": "Fast Charging",
                "content": "While fast charging is convenient, frequent use can degrade your battery faster. Use it primarily for long trips and rely on slower charging for regular use."
            },
            {
                "title": "Battery Health",
                "content": "Extreme temperatures can affect battery performance. During summer in Tamil Nadu, try to charge in shaded areas or during cooler parts of the day."
            },
            {
                "title": "Charging Etiquette",
                "content": "Once your vehicle is charged, move it promptly to allow others to use the station. Avoid using EV charging spots as regular parking spaces."
            }
        ]
        
        for tip in tips:
            with st.expander(tip["title"]):
                st.markdown(tip["content"])
        
        # Charging time calculator
        st.subheader("Charging Time Calculator")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            battery_capacity = st.number_input(
                "Battery Capacity (kWh)",
                min_value=20,
                max_value=150,
                value=60,
                step=5
            )
        
        with col2:
            start_soc = st.slider(
                "Starting Charge (%)",
                min_value=10,
                max_value=90,
                value=30,
                step=5
            )
        
        with col3:
            target_soc = st.slider(
                "Target Charge (%)",
                min_value=start_soc + 10,
                max_value=100,
                value=80,
                step=5
            )
        
        charger_power = st.selectbox(
            "Charger Power",
            options=["3.3 kW (Home Charging)", "7.4 kW (AC Charging)", "22 kW (Fast AC)", "50 kW (DC Fast Charging)", "150 kW (Ultrafast DC)"]
        )
        
        # Extract power value
        power_kw = float(charger_power.split(" ")[0])
        
        # Calculate charging time
        energy_required = battery_capacity * (target_soc - start_soc) / 100
        charging_time_hours = energy_required / power_kw
        
        # Account for charging inefficiency and tapering
        if power_kw >= 50:  # DC fast charging
            # Fast charging slows down above 80%
            if target_soc > 80 and start_soc < 80:
                energy_to_80 = battery_capacity * (80 - start_soc) / 100
                energy_above_80 = battery_capacity * (target_soc - 80) / 100
                
                time_to_80 = energy_to_80 / power_kw
                time_above_80 = energy_above_80 / (power_kw * 0.5)  # 50% slower above 80%
                
                charging_time_hours = time_to_80 + time_above_80
            
            efficiency = 0.85  # 85% efficiency for DC fast charging
        else:
            efficiency = 0.9  # 90% efficiency for AC charging
        
        # Adjust for efficiency
        charging_time_hours = charging_time_hours / efficiency
        
        # Convert to hours and minutes
        hours = int(charging_time_hours)
        minutes = int((charging_time_hours - hours) * 60)
        
        # Display results
        st.subheader("Estimated Charging Time")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Time Required", f"{hours}h {minutes}m")
        
        with col2:
            energy_kwh = round(energy_required, 1)
            cost_per_kwh = 8.5  # Assume ₹8.5 per kWh
            charging_cost = round(energy_kwh * cost_per_kwh, 2)
            
            st.metric("Estimated Cost", f"₹{charging_cost}")
        
        # Charging speed comparison
        st.subheader("Charging Speed Comparison")
        
        # Create comparison data
        charger_types = [
            "3.3 kW (Home)",
            "7.4 kW (AC)",
            "22 kW (Fast AC)",
            "50 kW (DC Fast)",
            "150 kW (Ultrafast DC)"
        ]
        
        powers = [3.3, 7.4, 22, 50, 150]
        
        comparison_data = []
        
        for type_name, power in zip(charger_types, powers):
            # Calculate time
            basic_time = energy_required / power
            
            # Apply efficiency and tapering
            if power >= 50:
                if target_soc > 80 and start_soc < 80:
                    energy_to_80 = battery_capacity * (80 - start_soc) / 100
                    energy_above_80 = battery_capacity * (target_soc - 80) / 100
                    
                    time_to_80 = energy_to_80 / power
                    time_above_80 = energy_above_80 / (power * 0.5)
                    
                    adjusted_time = (time_to_80 + time_above_80) / 0.85
                else:
                    adjusted_time = basic_time / 0.85
            else:
                adjusted_time = basic_time / 0.9
            
            # Convert to minutes for easier comparison
            time_minutes = round(adjusted_time * 60)
            
            # Range added per minute
            range_per_minute = round(vehicle_range * (target_soc - start_soc) / 100 / time_minutes, 1)
            
            comparison_data.append({
                "Charger Type": type_name,
                "Time (Minutes)": time_minutes,
                "Range Added Per Minute (km)": range_per_minute,
                "Is Selected": type_name.startswith(str(power_kw))
            })
        
        # Create DataFrame
        comparison_df = pd.DataFrame(comparison_data)
        
        # Create chart
        fig = px.bar(
            comparison_df,
            x="Charger Type",
            y="Time (Minutes)",
            color="Is Selected",
            color_discrete_map={True: "red", False: "blue"},
            labels={"Time (Minutes)": "Charging Time (Minutes)"}
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=False
        )
        
        # Invert y-axis (less time is better)
        fig.update_yaxes(autorange="reversed")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Range per minute chart
        fig2 = px.bar(
            comparison_df,
            x="Charger Type",
            y="Range Added Per Minute (km)",
            color="Is Selected",
            color_discrete_map={True: "red", False: "blue"},
            labels={"Range Added Per Minute (km)": "Range Added Per Minute (km)"}
        )
        
        fig2.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
