import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import random
from datetime import datetime, timedelta
import plotly.express as px

from utils import create_tamil_nadu_map, display_map, MAJOR_CITIES, get_alternative_routes

def load_first_aid_data():
    try:
        with open("data/first_aid.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_accident_types():
    try:
        with open("data/accident_types.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def main():
    st.title("🚑 Accident Management")
    
    # Introduction
    st.markdown("""
    Get emergency assistance, first aid instructions, and alternative routes in case of accidents.
    This module helps you handle accident situations efficiently and safely.
    """)
    
    # Main navigation tabs
    tab1, tab2, tab3 = st.tabs(["Report Accident", "First Aid Guide", "Emergency Services"])
    
    with tab1:
        st.header("Report an Accident")
        
        st.markdown("""
        Report an accident to alert emergency services and other road users. This will also
        help us provide alternative routes to other commuters.
        """)
        
        # Form to report accident
        col1, col2 = st.columns(2)
        
        with col1:
            accident_location = st.selectbox(
                "Accident Location (Nearest City)",
                options=list(MAJOR_CITIES.keys())
            )
            
            # Load accident types
            accident_types = load_accident_types()
            accident_type_options = [t["type"] for t in accident_types]
            
            accident_type = st.selectbox(
                "Type of Accident",
                options=accident_type_options
            )
            
            # Get severity based on selected type
            selected_accident = next((t for t in accident_types if t["type"] == accident_type), None)
            severity = selected_accident["severity"] if selected_accident else "Medium"
            
            st.selectbox(
                "Severity",
                options=["Low", "Medium", "High"],
                index=["Low", "Medium", "High"].index(severity)
            )
        
        with col2:
            road_name = st.text_input("Road/Street Name")
            
            landmark = st.text_input("Nearest Landmark")
            
            injuries = st.radio(
                "Are there any injuries?",
                options=["Yes, serious injuries", "Yes, minor injuries", "No injuries", "Unknown"]
            )
        
        additional_info = st.text_area("Additional Information", height=100)
        
        reporter_phone = st.text_input("Your Contact Number (Optional)")
        
        if st.button("Report Accident"):
            # In a real application, this would send the information to emergency services
            st.success("Accident reported successfully. Emergency services have been notified.")
            
            # Show emergency instructions based on accident type
            if selected_accident:
                st.subheader("Emergency Instructions")
                
                for i, instruction in enumerate(selected_accident["instructions"]):
                    st.markdown(f"{i+1}. {instruction}")
                
                if selected_accident["first_aid_required"]:
                    st.info("First aid may be required. See the First Aid Guide tab for instructions.")
            
            # Show alternative routes for other users
            st.subheader("Alternative Routes For Other Commuters")
            
            # Create map with accident location
            m = create_tamil_nadu_map(center=MAJOR_CITIES[accident_location], zoom=12)
            
            # Add accident marker
            folium.Marker(
                location=MAJOR_CITIES[accident_location],
                popup="Accident Site",
                tooltip="Accident Site",
                icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
            ).add_to(m)
            
            # Add 50m radius circle around accident
            folium.Circle(
                location=MAJOR_CITIES[accident_location],
                radius=500,  # 500m radius
                color="red",
                fill=True,
                fill_opacity=0.2
            ).add_to(m)
            
            # Display map
            display_map(m)
            
            # Show alternative routes
            # For demo, just get routes from this city to another random city
            other_cities = list(MAJOR_CITIES.keys())
            other_cities.remove(accident_location)
            destination = random.choice(other_cities)
            
            alternative_routes = get_alternative_routes(
                accident_location, 
                destination,
                event_location=MAJOR_CITIES[accident_location]
            )
            
            st.markdown(f"Alternative routes from {accident_location} to {destination}:")
            
            for i, route in enumerate(alternative_routes[1:]):  # Skip the affected route
                st.markdown(f"**Route {i+1}:** via {route['name']} ({route['distance']} km, {route['time']} min)")
    
    with tab2:
        st.header("First Aid Guide")
        
        # Load first aid data
        first_aid_data = load_first_aid_data()
        
        if first_aid_data:
            # Create filter by emergency level
            emergency_levels = sorted(list(set(item["emergency_level"] for item in first_aid_data)))
            
            selected_level = st.selectbox(
                "Filter by Emergency Level",
                options=["All"] + emergency_levels
            )
            
            # Filter data based on selection
            if selected_level != "All":
                filtered_data = [item for item in first_aid_data if item["emergency_level"] == selected_level]
            else:
                filtered_data = first_aid_data
            
            # Display first aid guides
            for item in filtered_data:
                # Determine color based on emergency level
                if item["emergency_level"] == "Critical":
                    header_color = "red"
                elif item["emergency_level"] == "High":
                    header_color = "orange"
                else:
                    header_color = "blue"
                
                with st.expander(f"{item['title']} - {item['emergency_level']}"):
                    st.markdown(f"<h4 style='color:{header_color};'>{item['title']}</h4>", unsafe_allow_html=True)
                    
                    # Display steps
                    st.subheader("Steps")
                    for i, step in enumerate(item["steps"]):
                        st.markdown(f"{i+1}. {step}")
                    
                    # Notes and warnings
                    if "notes" in item:
                        st.info(f"**Note:** {item['notes']}")
                    
                    if "warning" in item:
                        st.warning(f"**Warning:** {item['warning']}")
                    
                    # Add animation/video placeholder
                    # In a real app, this would show actual first aid videos
                    st.markdown("### Demonstration")
                    st.markdown(f"<div style='background-color:#f0f0f0; height:200px; display:flex; justify-content:center; align-items:center;'><p>Animation for {item['title']} would appear here</p></div>", unsafe_allow_html=True)
        else:
            st.warning("First aid information is not available. Please check your internet connection.")
        
        # Common emergency numbers
        st.header("Emergency Contact Numbers")
        
        emergency_contacts = {
            "Ambulance": "108",
            "Police": "100",
            "Fire Service": "101",
            "Highway Patrol": "1073",
            "Women Helpline": "1091",
            "Child Helpline": "1098",
            "Disaster Management": "1077"
        }
        
        # Display contacts in a grid
        col1, col2 = st.columns(2)
        
        count = 0
        for service, number in emergency_contacts.items():
            if count % 2 == 0:
                with col1:
                    st.markdown(f"**{service}:** {number}")
            else:
                with col2:
                    st.markdown(f"**{service}:** {number}")
            count += 1
        
        # Additional resources
        st.header("Additional Resources")
        
        st.markdown("""
        - [St. John Ambulance First Aid Guide](https://www.sja.org.uk/get-advice/free-first-aid-guide/)
        - [Red Cross First Aid App](https://www.redcross.org/get-help/how-to-prepare-for-emergencies/mobile-apps.html)
        - [WHO Road Safety Guidelines](https://www.who.int/roadsafety/en/)
        """)
    
    with tab3:
        st.header("Emergency Services")
        
        # Nearest emergency services
        st.subheader("Find Nearest Emergency Services")
        
        selected_location = st.selectbox(
            "Select Your Location",
            options=list(MAJOR_CITIES.keys()),
            key="emergency_location"
        )
        
        service_type = st.selectbox(
            "Service Type",
            options=["Hospital", "Police Station", "Fire Station", "All"]
        )
        
        if st.button("Find Services"):
            # Create map centered on selected location
            m = create_tamil_nadu_map(center=MAJOR_CITIES[selected_location], zoom=12)
            
            # Add user location marker
            folium.Marker(
                location=MAJOR_CITIES[selected_location],
                popup="Your Location",
                tooltip="Your Location",
                icon=folium.Icon(color="blue", icon="user", prefix="fa")
            ).add_to(m)
            
            # Simulate emergency services (in a real app, this would come from a database)
            services = []
            
            if service_type in ["Hospital", "All"]:
                # Generate random hospitals
                for i in range(3):
                    lat_offset = (random.random() - 0.5) * 0.1
                    lng_offset = (random.random() - 0.5) * 0.1
                    
                    location = [
                        MAJOR_CITIES[selected_location][0] + lat_offset,
                        MAJOR_CITIES[selected_location][1] + lng_offset
                    ]
                    
                    services.append({
                        "name": f"{selected_location} General Hospital {i+1}",
                        "type": "Hospital",
                        "location": location,
                        "contact": f"044-2345{i+1}000",
                        "distance": round(random.uniform(1.5, 8.0), 1)
                    })
            
            if service_type in ["Police Station", "All"]:
                # Generate random police stations
                for i in range(2):
                    lat_offset = (random.random() - 0.5) * 0.1
                    lng_offset = (random.random() - 0.5) * 0.1
                    
                    location = [
                        MAJOR_CITIES[selected_location][0] + lat_offset,
                        MAJOR_CITIES[selected_location][1] + lng_offset
                    ]
                    
                    services.append({
                        "name": f"{selected_location} Police Station {i+1}",
                        "type": "Police Station",
                        "location": location,
                        "contact": f"044-2346{i+1}000",
                        "distance": round(random.uniform(1.0, 5.0), 1)
                    })
            
            if service_type in ["Fire Station", "All"]:
                # Generate random fire stations
                for i in range(1):
                    lat_offset = (random.random() - 0.5) * 0.1
                    lng_offset = (random.random() - 0.5) * 0.1
                    
                    location = [
                        MAJOR_CITIES[selected_location][0] + lat_offset,
                        MAJOR_CITIES[selected_location][1] + lng_offset
                    ]
                    
                    services.append({
                        "name": f"{selected_location} Fire Station {i+1}",
                        "type": "Fire Station",
                        "location": location,
                        "contact": f"044-2347{i+1}000",
                        "distance": round(random.uniform(2.0, 7.0), 1)
                    })
            
            # Sort services by distance
            services.sort(key=lambda x: x["distance"])
            
            # Add service markers to map
            for service in services:
                # Choose icon and color based on service type
                if service["type"] == "Hospital":
                    icon = "hospital"
                    color = "red"
                elif service["type"] == "Police Station":
                    icon = "shield"
                    color = "blue"
                else:  # Fire Station
                    icon = "fire-extinguisher"
                    color = "orange"
                
                # Create popup
                popup_html = f"""
                <div style="width:200px">
                    <h4>{service["name"]}</h4>
                    <p><b>Type:</b> {service["type"]}</p>
                    <p><b>Distance:</b> {service["distance"]} km</p>
                    <p><b>Contact:</b> {service["contact"]}</p>
                </div>
                """
                
                # Add marker
                folium.Marker(
                    location=service["location"],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{service['name']} ({service['distance']} km)",
                    icon=folium.Icon(color=color, icon=icon, prefix="fa")
                ).add_to(m)
            
            # Display map
            display_map(m)
            
            # List services
            st.subheader("Nearby Emergency Services")
            
            for service in services:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{service['name']}**")
                    st.markdown(f"Type: {service['type']}")
                
                with col2:
                    st.markdown(f"**Distance**")
                    st.markdown(f"{service['distance']} km")
                
                with col3:
                    st.markdown(f"**Contact**")
                    st.markdown(f"{service['contact']}")
                    
                    # Call button
                    st.button("Call", key=f"call_{service['name'].replace(' ', '_')}")
                
                st.divider()
        
        # Emergency preparedness tips
        st.subheader("Emergency Preparedness Tips")
        
        tips = [
            "Keep a first aid kit in your vehicle at all times.",
            "Save emergency contact numbers on speed dial.",
            "Memorize at least one emergency contact number.",
            "Learn basic first aid and CPR.",
            "Keep emergency services updated with your exact location."
        ]
        
        for tip in tips:
            st.markdown(f"• {tip}")

if __name__ == "__main__":
    main()
