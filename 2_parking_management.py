import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px
import json
import random
from datetime import datetime, timedelta

from utils import create_tamil_nadu_map, display_map, MAJOR_CITIES

def load_parking_data():
    try:
        with open("data/parking_data.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty data structure if file not found
        return {"parking_facilities": [], "street_parking": []}

def update_parking_availability(data):
    """Simulate changes in parking availability for demo purposes"""
    current_time = datetime.now()
    
    for facility in data["parking_facilities"]:
        # Update only if last update was more than 5 minutes ago (for demo purposes)
        last_update = datetime.strptime(facility["last_updated"], "%Y-%m-%dT%H:%M:%S")
        if (current_time - last_update).seconds > 300:
            # Randomly update available spaces
            change = random.randint(-5, 5)
            new_available = facility["available_spaces"] + change
            
            # Ensure available spaces is within bounds
            facility["available_spaces"] = max(0, min(facility["total_spaces"], new_available))
            
            # Update status based on availability
            if facility["available_spaces"] == 0:
                facility["status"] = "Full"
            elif facility["available_spaces"] < 0.1 * facility["total_spaces"]:
                facility["status"] = "Almost Full"
            elif facility["available_spaces"] < 0.3 * facility["total_spaces"]:
                facility["status"] = "Crowded"
            else:
                facility["status"] = "Open"
                
            # Update timestamp
            facility["last_updated"] = current_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Similarly update street parking
    for spot in data["street_parking"]:
        last_update = datetime.strptime(spot["last_updated"], "%Y-%m-%dT%H:%M:%S")
        if (current_time - last_update).seconds > 300:
            change = random.randint(-2, 2)
            new_available = spot["available_spaces"] + change
            
            spot["available_spaces"] = max(0, min(spot["total_spaces"], new_available))
            
            if spot["available_spaces"] == 0:
                spot["status"] = "Full"
            elif spot["available_spaces"] < 0.2 * spot["total_spaces"]:
                spot["status"] = "Almost Full"
            elif spot["available_spaces"] < 0.4 * spot["total_spaces"]:
                spot["status"] = "Crowded"
            else:
                spot["status"] = "Available"
                
            spot["last_updated"] = current_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    return data

def main():
    st.title("🅿️ Parking Management")
    
    # Introduction
    st.markdown("""
    Find and reserve parking spaces across Tamil Nadu with our IoT-integrated parking management system.
    Get real-time availability updates and reserve your spot in advance.
    """)
    
    # Load and update parking data
    parking_data = load_parking_data()
    parking_data = update_parking_availability(parking_data)
    
    # City selection
    selected_city = st.selectbox(
        "Select a City",
        options=list(MAJOR_CITIES.keys()),
        index=0
    )
    
    # Filter parking facilities by selected city
    city_facilities = [f for f in parking_data["parking_facilities"] 
                     if f["location"] == selected_city]
    
    city_street_parking = [s for s in parking_data["street_parking"] 
                         if s["location"] == selected_city]
    
    # Map showing parking facilities
    st.header(f"Parking Facilities in {selected_city}")
    
    # Create map centered on selected city
    m = folium.Map(
        location=MAJOR_CITIES[selected_city],
        zoom_start=13,
        tiles="OpenStreetMap"
    )
    
    # Add markers for parking facilities
    for facility in city_facilities:
        # Determine marker color based on availability
        if facility["status"] == "Full":
            color = "red"
        elif facility["status"] == "Crowded":
            color = "orange"
        else:
            color = "green"
            
        # Calculate percentage availability
        availability_pct = round((facility["available_spaces"] / facility["total_spaces"]) * 100)
        
        # Create popup content
        popup_html = f"""
        <div style="width:200px">
            <h4>{facility["name"]}</h4>
            <p><b>Available:</b> {facility["available_spaces"]}/{facility["total_spaces"]} spaces</p>
            <p><b>Status:</b> {facility["status"]}</p>
            <p><b>Rate:</b> ₹{facility["hourly_rate"]}/hour</p>
            <p><b>Hours:</b> {facility["operating_hours"]}</p>
            <p><b>Features:</b> {", ".join(facility["features"])}</p>
        </div>
        """
        
        # Add marker to map
        folium.Marker(
            location=facility["coordinates"],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{facility['name']}: {availability_pct}% available",
            icon=folium.Icon(color=color, icon="parking", prefix="fa")
        ).add_to(m)
    
    # Add markers for street parking
    for spot in city_street_parking:
        # Determine marker color
        if spot["status"] == "Full":
            color = "red"
        elif spot["status"] == "Crowded":
            color = "orange"
        else:
            color = "blue"
            
        # Calculate percentage availability
        availability_pct = round((spot["available_spaces"] / spot["total_spaces"]) * 100)
        
        # Create popup content
        popup_html = f"""
        <div style="width:200px">
            <h4>{spot["name"]} (Street Parking)</h4>
            <p><b>Available:</b> {spot["available_spaces"]}/{spot["total_spaces"]} spaces</p>
            <p><b>Status:</b> {spot["status"]}</p>
            <p><b>Rate:</b> ₹{spot["hourly_rate"]}/hour</p>
            <p><b>Restrictions:</b> {spot["restrictions"]}</p>
            <p><b>Payment:</b> {", ".join(spot["payment_methods"])}</p>
        </div>
        """
        
        # Add marker to map
        folium.Marker(
            location=spot["coordinates"],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{spot['name']}: {availability_pct}% available",
            icon=folium.Icon(color=color, icon="road", prefix="fa")
        ).add_to(m)
        
    # Display the map
    display_map(m)
    
    # Parking facilities list
    st.header(f"Available Parking in {selected_city}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parking Facilities")
        
        if city_facilities:
            for facility in city_facilities:
                # Determine status color
                if facility["status"] == "Full":
                    status_color = "red"
                elif facility["status"] == "Crowded":
                    status_color = "orange"
                else:
                    status_color = "green"
                
                # Create expandable card for each facility
                with st.expander(f"{facility['name']} - {facility['available_spaces']}/{facility['total_spaces']} spaces"):
                    st.markdown(f"**Rate:** ₹{facility['hourly_rate']}/hour")
                    st.markdown(f"**Hours:** {facility['operating_hours']}")
                    st.markdown(f"**Features:** {', '.join(facility['features'])}")
                    st.markdown(f"**Status:** <span style='color:{status_color};'>{facility['status']}</span>", unsafe_allow_html=True)
                    
                    # Add "Reserve" button with time slot selection
                    if facility["status"] != "Full":
                        current_hour = datetime.now().hour
                        time_slots = [f"{h}:00" for h in range(current_hour, min(current_hour + 8, 24))]
                        
                        selected_time = st.selectbox("Select arrival time", time_slots, key=f"time_{facility['id']}")
                        duration = st.slider("Duration (hours)", 1, 8, 2, key=f"duration_{facility['id']}")
                        
                        total_cost = facility["hourly_rate"] * duration
                        st.markdown(f"**Total Cost:** ₹{total_cost}")
                        
                        if st.button("Reserve Now", key=f"reserve_{facility['id']}"):
                            st.success(f"Parking reserved at {facility['name']} for {selected_time} for {duration} hours. Total: ₹{total_cost}")
                    else:
                        st.error("This parking facility is currently full.")
        else:
            st.info(f"No parking facilities found in {selected_city}")
    
    with col2:
        st.subheader("Street Parking")
        
        if city_street_parking:
            for spot in city_street_parking:
                # Determine status color
                if spot["status"] == "Full":
                    status_color = "red"
                elif spot["status"] == "Crowded":
                    status_color = "orange"
                else:
                    status_color = "blue"
                
                # Create expandable card for each spot
                with st.expander(f"{spot['name']} - {spot['available_spaces']}/{spot['total_spaces']} spaces"):
                    st.markdown(f"**Rate:** ₹{spot['hourly_rate']}/hour")
                    st.markdown(f"**Restrictions:** {spot['restrictions']}")
                    st.markdown(f"**Payment Methods:** {', '.join(spot['payment_methods'])}")
                    st.markdown(f"**Status:** <span style='color:{status_color};'>{spot['status']}</span>", unsafe_allow_html=True)
                    
                    # Add real-time availability chart
                    if spot["status"] != "Full":
                        # Generate hourly availability prediction
                        hours = list(range(24))
                        current_hour = datetime.now().hour
                        
                        # Create data for availability chart
                        availability_data = []
                        total_spaces = spot["total_spaces"]
                        current_spaces = spot["available_spaces"]
                        
                        for h in hours:
                            # Morning decrease (7-10 AM)
                            if 7 <= h <= 10:
                                factor = 0.6 - (h - 7) * 0.15
                            # Lunch time (12-2 PM)
                            elif 12 <= h <= 14:
                                factor = 0.3
                            # Evening rush (5-8 PM)
                            elif 17 <= h <= 20:
                                factor = 0.2
                            # Late night (10 PM - 6 AM)
                            elif h < 6 or h > 22:
                                factor = 0.9
                            # Other times
                            else:
                                factor = 0.5
                                
                            # Add some randomness
                            factor += (random.random() - 0.5) * 0.2
                            factor = max(0, min(1, factor))
                            
                            # Calculate spaces
                            spaces = int(total_spaces * factor)
                            
                            # If current hour, use actual data
                            if h == current_hour:
                                spaces = current_spaces
                                
                            availability_data.append({
                                "Hour": f"{h:02d}:00",
                                "Available Spaces": spaces,
                                "Current Hour": h == current_hour
                            })
                        
                        # Create DataFrame for chart
                        df = pd.DataFrame(availability_data)
                        
                        # Create chart
                        fig = px.line(
                            df,
                            x="Hour",
                            y="Available Spaces",
                            markers=True,
                            color="Current Hour",
                            color_discrete_map={True: "red", False: "blue"}
                        )
                        
                        fig.update_layout(
                            height=200,
                            margin=dict(l=0, r=0, t=20, b=0),
                            legend_title_text="",
                            hovermode="x"
                        )
                        
                        # Add capacity line
                        fig.add_shape(
                            type="line",
                            x0=0,
                            y0=total_spaces,
                            x1=1,
                            y1=total_spaces,
                            xref="paper",
                            line=dict(color="green", dash="dash"),
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No street parking information available for {selected_city}")
    
    # Parking tips section
    st.header("Parking Tips")
    
    tips = [
        "Use digital payment options like UPI for contactless parking payments.",
        "Chennai's T. Nagar and Anna Nagar areas are most congested during weekends.",
        "Many shopping malls offer free parking for the first hour.",
        "Consider parking slightly away from commercial centers and walking the last few minutes to save on parking fees.",
        "Always carry change for parking meters that don't accept digital payments."
    ]
    
    st.info(f"💡 **Tip:** {random.choice(tips)}")

if __name__ == "__main__":
    main()
