import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import random
from datetime import datetime, timedelta

from utils import create_tamil_nadu_map, display_map, MAJOR_CITIES, generate_id

def load_events():
    try:
        with open("data/events.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_events(events):
    from utils import save_json_data
    save_json_data(events, "events.json")

def filter_events(events, event_type=None, location=None, severity=None, status=None):
    filtered = events
    
    if event_type and event_type != "All":
        filtered = [e for e in filtered if e["type"] == event_type]
    
    if location and location != "All":
        filtered = [e for e in filtered if e["location"] == location]
    
    if severity and severity != "All":
        filtered = [e for e in filtered if e["severity"] == severity]
    
    if status and status != "All":
        filtered = [e for e in filtered if e["status"] == status]
    
    return filtered

def calculate_alternative_routes(start, end, event_location):
    """
    Calculate alternative routes to avoid an event
    """
    from utils import generate_routes
    
    # Get standard routes
    standard_routes = generate_routes(start, end, 3)
    
    # Mark the first route as affected
    if standard_routes:
        standard_routes[0]["affected_by_event"] = True
        standard_routes[0]["traffic"] = "Very Heavy"
        standard_routes[0]["color"] = "red"
        standard_routes[0]["time"] = int(standard_routes[0]["time"] * 1.5)  # 50% longer due to event
    
    # Return all routes (first one marked as affected)
    return standard_routes

def main():
    st.title("🚧 Event Reporting")
    
    # Introduction
    st.markdown("""
    Report and view construction, roadblocks, or events that might affect traffic in your area.
    Help fellow travelers avoid traffic delays and find alternative routes.
    """)
    
    # Load existing events
    events = load_events()
    
    # Main navigation tabs
    tab1, tab2, tab3 = st.tabs(["View Reports", "Report Event", "My Reports"])
    
    with tab1:
        st.header("Traffic Event Reports")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            event_types = ["All"] + sorted(list(set(e["type"] for e in events)))
            filter_type = st.selectbox("Event Type", options=event_types)
        
        with col2:
            locations = ["All"] + sorted(list(set(e["location"] for e in events)))
            filter_location = st.selectbox("Location", options=locations)
        
        with col3:
            severities = ["All", "Low", "Medium", "High"]
            filter_severity = st.selectbox("Severity", options=severities)
        
        with col4:
            statuses = ["All", "Active", "Cleared", "Scheduled"]
            filter_status = st.selectbox("Status", options=statuses)
        
        # Apply filters
        filtered_events = filter_events(events, filter_type, filter_location, filter_severity, filter_status)
        
        # Map view
        st.subheader("Event Map")
        
        # Create map centered on Tamil Nadu
        m = create_tamil_nadu_map()
        
        # Add event markers
        for event in filtered_events:
            # Determine marker color based on severity
            if event["severity"] == "High":
                color = "red"
            elif event["severity"] == "Medium":
                color = "orange"
            else:
                color = "blue"
            
            # Determine icon based on type
            if event["type"] == "Construction":
                icon = "wrench"
            elif event["type"] == "Road Closure":
                icon = "road"
            elif event["type"] == "Accident":
                icon = "car-crash"
            elif event["type"] == "Flooding":
                icon = "water"
            elif event["type"] == "Festival" or event["type"] == "Event":
                icon = "calendar"
            elif event["type"] == "Protest":
                icon = "bullhorn"
            elif event["type"] == "VIP Movement":
                icon = "user-tie"
            else:
                icon = "exclamation-triangle"
            
            # Create popup content
            popup_html = f"""
            <div style="width:250px">
                <h4>{event["name"]}</h4>
                <p><b>Type:</b> {event["type"]}</p>
                <p><b>Location:</b> {event["location"]}</p>
                <p><b>Description:</b> {event["description"]}</p>
                <p><b>Severity:</b> {event["severity"]}</p>
                <p><b>Status:</b> {event["status"]}</p>
                <p><b>Dates:</b> {event["start_date"]} to {event["end_date"]}</p>
                <p><b>Affected Routes:</b> {", ".join(event["affected_routes"])}</p>
            </div>
            """
            
            # Add marker
            folium.Marker(
                location=event["coordinates"],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{event['type']}: {event['name']}",
                icon=folium.Icon(color=color, icon=icon, prefix="fa")
            ).add_to(m)
        
        # Display map
        display_map(m)
        
        # List view
        st.subheader(f"Filtered Reports ({len(filtered_events)})")
        
        if filtered_events:
            for event in filtered_events:
                with st.expander(f"{event['type']}: {event['name']} - {event['severity']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Location:** {event['location']}")
                        st.markdown(f"**Description:** {event['description']}")
                        st.markdown(f"**Dates:** {event['start_date']} to {event['end_date']}")
                        st.markdown(f"**Status:** {event['status']}")
                    
                    with col2:
                        st.markdown(f"**Affected Routes:** {', '.join(event['affected_routes'])}")
                        st.markdown(f"**Reported By:** {event['reported_by']}")
                        st.markdown(f"**Reported On:** {event['timestamp']}")
                        
                        # Find alternative routes button
                        if st.button("Find Alternative Routes", key=f"alt_{event['id']}"):
                            # Show alternative routes
                            st.subheader("Alternative Routes")
                            
                            # Randomly select start and end locations near the event
                            all_cities = list(MAJOR_CITIES.keys())
                            
                            # Use event location as start or end
                            if event["location"] in all_cities:
                                if random.choice([True, False]):
                                    start = event["location"]
                                    end_options = [city for city in all_cities if city != start]
                                    end = random.choice(end_options)
                                else:
                                    end = event["location"]
                                    start_options = [city for city in all_cities if city != end]
                                    start = random.choice(start_options)
                            else:
                                # If event location not in major cities, pick random cities
                                start, end = random.sample(all_cities, 2)
                            
                            # Calculate alternative routes
                            alternative_routes = calculate_alternative_routes(
                                start, end, event["coordinates"]
                            )
                            
                            # Create map with routes
                            route_map = create_tamil_nadu_map()
                            
                            # Add event marker
                            folium.Marker(
                                location=event["coordinates"],
                                popup=event["name"],
                                tooltip=f"{event['type']}: {event['name']}",
                                icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
                            ).add_to(route_map)
                            
                            # Add markers for start and end
                            folium.Marker(
                                location=MAJOR_CITIES[start],
                                popup=f"Start: {start}",
                                tooltip=f"Start: {start}",
                                icon=folium.Icon(color="green", icon="play", prefix="fa")
                            ).add_to(route_map)
                            
                            folium.Marker(
                                location=MAJOR_CITIES[end],
                                popup=f"End: {end}",
                                tooltip=f"End: {end}",
                                icon=folium.Icon(color="red", icon="stop", prefix="fa")
                            ).add_to(route_map)
                            
                            # Add routes
                            for i, route in enumerate(alternative_routes):
                                # Create route points
                                route_points = [MAJOR_CITIES[start]]
                                
                                # Add some intermediate points for visualization
                                intermediate_points = 3
                                for j in range(intermediate_points):
                                    # Create points that deviate slightly from a straight line
                                    factor = (j + 1) / (intermediate_points + 1)
                                    lat = MAJOR_CITIES[start][0] + (MAJOR_CITIES[end][0] - MAJOR_CITIES[start][0]) * factor
                                    lng = MAJOR_CITIES[start][1] + (MAJOR_CITIES[end][1] - MAJOR_CITIES[start][1]) * factor
                                    
                                    # Add some randomness for different routes
                                    lat_offset = (random.random() - 0.5) * 0.5
                                    lng_offset = (random.random() - 0.5) * 0.5
                                    
                                    route_points.append([lat + lat_offset, lng + lng_offset])
                                
                                route_points.append(MAJOR_CITIES[end])
                                
                                # Add route line
                                tooltip = f"Route {i+1}: {route['name']} - {'Affected by event' if 'affected_by_event' in route else 'Alternative route'}"
                                folium.PolyLine(
                                    locations=route_points,
                                    tooltip=tooltip,
                                    color=route["color"],
                                    weight=5,
                                    opacity=0.7
                                ).add_to(route_map)
                            
                            # Display map
                            display_map(route_map)
                            
                            # Display route details
                            st.markdown(f"**Routes from {start} to {end}:**")
                            
                            for i, route in enumerate(alternative_routes):
                                affected = "affected_by_event" in route
                                
                                if affected:
                                    st.warning(f"⚠️ Route {i+1}: {route['name']} - {route['distance']} km, {route['time']} min - Affected by event!")
                                else:
                                    st.success(f"✅ Route {i+1}: {route['name']} - {route['distance']} km, {route['time']} min - Recommended alternative")
        else:
            st.info("No events found matching your criteria.")
    
    with tab2:
        st.header("Report Traffic Event")
        
        st.markdown("""
        Help other commuters by reporting construction, road closures, accidents, or other events 
        that might affect traffic in your area.
        """)
        
        # Event reporting form
        col1, col2 = st.columns(2)
        
        with col1:
            event_type = st.selectbox(
                "Event Type",
                options=["Construction", "Road Closure", "Accident", "Flooding", "Festival", "Protest", "VIP Movement", "Other"]
            )
            
            event_name = st.text_input("Event Name", placeholder="e.g., Metro Rail Construction")
            
            event_location = st.selectbox(
                "Location (Nearest City)",
                options=list(MAJOR_CITIES.keys())
            )
        
        with col2:
            severity = st.selectbox(
                "Severity",
                options=["Low", "Medium", "High"]
            )
            
            start_date = st.date_input("Start Date", value=datetime.now().date())
            end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=7))
            
            status = st.selectbox(
                "Status",
                options=["Active", "Scheduled", "Cleared"]
            )
        
        # Affected routes
        affected_routes = st.text_input(
            "Affected Routes (comma separated)",
            placeholder="e.g., Anna Salai, Mount Road"
        )
        
        # Description
        description = st.text_area(
            "Description",
            placeholder="Provide details about the event, including timing and impact on traffic"
        )
        
        # Reporter details
        reporter_name = st.text_input("Your Name (Optional)")
        
        # Submit button
        if st.button("Submit Report"):
            if not event_name or not description or not affected_routes:
                st.error("Please fill in all required fields: Event Name, Description, and Affected Routes.")
            elif start_date > end_date:
                st.error("End date cannot be before start date.")
            else:
                # Parse affected routes
                routes_list = [route.strip() for route in affected_routes.split(",")]
                
                # Create event object
                new_event = {
                    "id": generate_id("event"),
                    "type": event_type,
                    "name": event_name,
                    "location": event_location,
                    "coordinates": MAJOR_CITIES[event_location],
                    "description": description,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "severity": severity,
                    "affected_routes": routes_list,
                    "status": status,
                    "reported_by": reporter_name if reporter_name else "Anonymous",
                    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                }
                
                # Add to events list
                events.append(new_event)
                
                # Save updated events
                save_events(events)
                
                st.success("Event reported successfully! Thank you for helping fellow commuters.")
                
                # Show the event on a map
                st.subheader("Event Location")
                
                event_map = create_tamil_nadu_map(center=MAJOR_CITIES[event_location], zoom=12)
                
                # Determine icon and color
                if severity == "High":
                    color = "red"
                elif severity == "Medium":
                    color = "orange"
                else:
                    color = "blue"
                
                if event_type == "Construction":
                    icon = "wrench"
                elif event_type == "Road Closure":
                    icon = "road"
                elif event_type == "Accident":
                    icon = "car-crash"
                else:
                    icon = "exclamation-triangle"
                
                # Add marker
                folium.Marker(
                    location=MAJOR_CITIES[event_location],
                    popup=event_name,
                    tooltip=f"{event_type}: {event_name}",
                    icon=folium.Icon(color=color, icon=icon, prefix="fa")
                ).add_to(event_map)
                
                # Add circle to indicate affected area
                folium.Circle(
                    location=MAJOR_CITIES[event_location],
                    radius=1000,  # 1km radius
                    color=color,
                    fill=True,
                    fill_opacity=0.2
                ).add_to(event_map)
                
                # Display map
                display_map(event_map)
    
    with tab3:
        st.header("My Reports")
        
        # In a real app, would filter by user
        # For demo, just show the last 3 reports
        my_reports = events[-3:] if len(events) >= 3 else events
        
        if my_reports:
            for report in my_reports:
                with st.expander(f"{report['type']}: {report['name']} - {report['status']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Location:** {report['location']}")
                        st.markdown(f"**Description:** {report['description']}")
                        st.markdown(f"**Dates:** {report['start_date']} to {report['end_date']}")
                        st.markdown(f"**Severity:** {report['severity']}")
                    
                    with col2:
                        st.markdown(f"**Status:** {report['status']}")
                        st.markdown(f"**Affected Routes:** {', '.join(report['affected_routes'])}")
                        st.markdown(f"**Reported On:** {report['timestamp']}")
                        
                        # Update status buttons
                        if report["status"] != "Cleared":
                            if st.button("Mark as Cleared", key=f"clear_{report['id']}"):
                                for e in events:
                                    if e["id"] == report["id"]:
                                        e["status"] = "Cleared"
                                save_events(events)
                                st.success("Event marked as cleared!")
                                st.rerun()
                        
                        if st.button("Delete Report", key=f"delete_{report['id']}"):
                            events = [e for e in events if e["id"] != report["id"]]
                            save_events(events)
                            st.success("Report deleted successfully!")
                            st.rerun()
        else:
            st.info("You haven't submitted any reports yet.")
    
    # Impact statistics
    st.header("Traffic Impact Statistics")
    
    # Calculate statistics
    active_events = [e for e in events if e["status"] == "Active"]
    high_severity = [e for e in active_events if e["severity"] == "High"]
    
    # Create statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Active Events",
            len(active_events),
            delta=None
        )
    
    with col2:
        st.metric(
            "High Severity",
            len(high_severity),
            delta=None
        )
    
    with col3:
        # Most affected city
        city_counts = {}
        for e in active_events:
            city = e["location"]
            city_counts[city] = city_counts.get(city, 0) + 1
        
        most_affected = max(city_counts.items(), key=lambda x: x[1])[0] if city_counts else "None"
        
        st.metric(
            "Most Affected City",
            most_affected,
            delta=None
        )
    
    with col4:
        # Most common event type
        type_counts = {}
        for e in active_events:
            event_type = e["type"]
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        most_common = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "None"
        
        st.metric(
            "Most Common Event",
            most_common,
            delta=None
        )
    
    # Tips for commuters
    st.header("Tips for Commuters")
    
    tips = [
        "Check for reported events along your route before starting your journey.",
        "Allow extra travel time when construction or major events are reported on your route.",
        "Consider using public transportation during high-severity traffic events.",
        "Report any traffic events you encounter to help other commuters.",
        "For long-term construction events, try to find alternative routes to avoid daily delays."
    ]
    
    for tip in tips:
        st.markdown(f"• {tip}")

if __name__ == "__main__":
    main()
