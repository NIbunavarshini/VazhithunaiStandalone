import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import random
from datetime import datetime, timedelta
import plotly.express as px

from utils import create_tamil_nadu_map, display_map, MAJOR_CITIES, generate_id

def load_carpool_data():
    try:
        with open("data/carpools.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_carpool_data(data):
    from utils import save_json_data
    save_json_data(data, "carpools.json")

def filter_carpools(carpools, start=None, end=None, date=None):
    filtered = carpools
    
    if start and start != "Any":
        filtered = [c for c in filtered if c["start_point"] == start]
    
    if end and end != "Any":
        filtered = [c for c in filtered if c["end_point"] == end]
    
    if date:
        filtered = [c for c in filtered if c["date"] == date.strftime("%Y-%m-%d")]
    
    return filtered

def main():
    st.title("🚗 Carpooling Community")
    
    # Introduction
    st.markdown("""
    Join the community-driven carpooling network to share rides, reduce costs, and help minimize traffic congestion.
    Find rides or offer your own to connect with fellow travelers.
    """)
    
    # Load carpool data
    carpools = load_carpool_data()
    
    # Main navigation tabs
    tab1, tab2, tab3 = st.tabs(["Find a Ride", "Offer a Ride", "My Rides"])
    
    with tab1:
        st.header("Find a Ride")
        
        # Search form
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_points = ["Any"] + sorted(list(set(c["start_point"] for c in carpools)))
            start_point = st.selectbox("From", options=start_points)
        
        with col2:
            end_points = ["Any"] + sorted(list(set(c["end_point"] for c in carpools)))
            end_point = st.selectbox("To", options=end_points)
        
        with col3:
            travel_date = st.date_input("Date", value=datetime.now().date())
        
        # Filter carpools
        filtered_carpools = filter_carpools(carpools, start_point, end_point, travel_date)
        
        # Display results
        if filtered_carpools:
            st.subheader(f"Available Rides ({len(filtered_carpools)})")
            
            # Map view
            m = create_tamil_nadu_map()
            
            # Add markers and routes for each carpool
            for carpool in filtered_carpools:
                # Add markers for start and end
                start_coords = MAJOR_CITIES.get(carpool["start_point"], [0, 0])
                end_coords = MAJOR_CITIES.get(carpool["end_point"], [0, 0])
                
                # Start marker
                folium.Marker(
                    location=start_coords,
                    popup=f"Start: {carpool['start_point']}",
                    tooltip=f"Start: {carpool['start_point']}",
                    icon=folium.Icon(color="green", icon="play", prefix="fa")
                ).add_to(m)
                
                # End marker
                folium.Marker(
                    location=end_coords,
                    popup=f"End: {carpool['end_point']}",
                    tooltip=f"End: {carpool['end_point']}",
                    icon=folium.Icon(color="red", icon="stop", prefix="fa")
                ).add_to(m)
                
                # Route line with via points
                route_points = [start_coords]
                
                # Add via points if any
                for via in carpool.get("via", []):
                    if via in MAJOR_CITIES:
                        route_points.append(MAJOR_CITIES[via])
                
                route_points.append(end_coords)
                
                # Add route line
                folium.PolyLine(
                    locations=route_points,
                    color=random.choice(["blue", "green", "purple", "orange"]),
                    weight=3,
                    opacity=0.7,
                    tooltip=f"{carpool['route']} - {carpool['time']}"
                ).add_to(m)
            
            # Display the map
            display_map(m)
            
            # List view
            for carpool in filtered_carpools:
                with st.expander(f"{carpool['route']} - {carpool['time']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Driver:** {carpool['driver_name']} (Rating: {carpool['driver_rating']}⭐)")
                        st.markdown(f"**Vehicle:** {carpool['vehicle']} ({carpool['vehicle_number']})")
                        st.markdown(f"**Date:** {carpool['date']}")
                        st.markdown(f"**Time:** {carpool['time']}")
                        
                        if "via" in carpool and carpool["via"]:
                            st.markdown(f"**Via:** {', '.join(carpool['via'])}")
                    
                    with col2:
                        st.markdown(f"**Seats Available:** {carpool['seats_available']}")
                        st.markdown(f"**Price per Seat:** ₹{carpool['price_per_seat']}")
                        st.markdown(f"**Contact:** {carpool['phone']}")
                        
                        if "preferences" in carpool:
                            st.markdown(f"**Preferences:** {', '.join(carpool['preferences'])}")
                    
                    # Book button
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if st.button("Book Seat", key=f"book_{carpool['id']}"):
                            st.success(f"Booking request sent to {carpool['driver_name']}. You will receive confirmation shortly.")
                    
                    with col2:
                        if st.button("Message Driver", key=f"msg_{carpool['id']}"):
                            st.info(f"Message feature will be available in the next update.")
        else:
            st.info("No carpools found matching your criteria. Try different search parameters or offer a ride yourself.")
            
            # Suggest offering a ride
            st.markdown("#### Can't find a suitable ride?")
            if st.button("Offer a Ride Instead"):
                st.switch_page("pages/6_carpooling.py")
                # This doesn't actually work in Streamlit as is, but simulates the intent
    
    with tab2:
        st.header("Offer a Ride")
        
        st.markdown("""
        Share your journey with others. Offer a ride to help fellow travelers and reduce 
        your travel costs.
        """)
        
        # Offer form
        col1, col2 = st.columns(2)
        
        with col1:
            offer_start = st.selectbox("From", options=sorted(list(MAJOR_CITIES.keys())), key="offer_start")
        
        with col2:
            offer_end = st.selectbox("To", options=sorted(list(MAJOR_CITIES.keys())), key="offer_end")
        
        # Via points (optional)
        all_cities = sorted(list(MAJOR_CITIES.keys()))
        # Remove start and end points from via options
        via_options = [city for city in all_cities if city != offer_start and city != offer_end]
        
        via_points = st.multiselect("Via (Optional)", options=via_options)
        
        col1, col2 = st.columns(2)
        
        with col1:
            offer_date = st.date_input("Date", value=datetime.now().date() + timedelta(days=1), key="offer_date")
        
        with col2:
            offer_time = st.time_input("Time", value=datetime.strptime("08:00", "%H:%M").time(), key="offer_time")
        
        # Vehicle details
        col1, col2 = st.columns(2)
        
        with col1:
            vehicle_type = st.selectbox("Vehicle Type", options=["Car", "SUV", "Hatchback", "Sedan"])
            vehicle_model = st.text_input("Vehicle Model", placeholder="e.g., Toyota Innova")
        
        with col2:
            vehicle_number = st.text_input("Vehicle Number", placeholder="e.g., TN 01 AB 1234")
            seats_available = st.number_input("Seats Available", min_value=1, max_value=7, value=2)
        
        # Price and preferences
        col1, col2 = st.columns(2)
        
        with col1:
            price_per_seat = st.number_input("Price per Seat (₹)", min_value=50, max_value=2000, value=200, step=50)
        
        with col2:
            preferences = st.multiselect(
                "Preferences",
                options=[
                    "No smoking", 
                    "Women only", 
                    "Share fuel cost", 
                    "AC ride", 
                    "Pets allowed", 
                    "No pets", 
                    "Music allowed",
                    "Luggage space available",
                    "No food in vehicle"
                ]
            )
        
        # Contact details
        phone = st.text_input("Contact Number", placeholder="e.g., 9876543210")
        
        # Submit button
        if st.button("Offer Ride"):
            if offer_start == offer_end:
                st.error("Starting point and destination cannot be the same.")
            elif not vehicle_model or not vehicle_number or not phone:
                st.error("Please fill all required fields.")
            elif len(phone) != 10 or not phone.isdigit():
                st.error("Please enter a valid 10-digit phone number.")
            else:
                # Create new carpool offer
                new_carpool = {
                    "id": generate_id("carpool"),
                    "driver_name": "Your Name",  # In a real app, would use user profile
                    "driver_rating": 5.0,        # New drivers start with 5.0
                    "vehicle": vehicle_model,
                    "vehicle_number": vehicle_number.upper(),
                    "route": f"{offer_start} to {offer_end}",
                    "start_point": offer_start,
                    "end_point": offer_end,
                    "via": via_points,
                    "date": offer_date.strftime("%Y-%m-%d"),
                    "time": offer_time.strftime("%I:%M %p"),
                    "seats_available": seats_available,
                    "price_per_seat": price_per_seat,
                    "phone": phone,
                    "preferences": preferences
                }
                
                # Add to carpools list
                carpools.append(new_carpool)
                
                # Save updated data
                save_carpool_data(carpools)
                
                st.success("Your ride has been offered successfully!")
                
                # Show preview
                st.subheader("Ride Preview")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Route:** {new_carpool['route']}")
                    
                    if via_points:
                        st.markdown(f"**Via:** {', '.join(via_points)}")
                        
                    st.markdown(f"**Date:** {new_carpool['date']}")
                    st.markdown(f"**Time:** {new_carpool['time']}")
                
                with col2:
                    st.markdown(f"**Vehicle:** {new_carpool['vehicle']}")
                    st.markdown(f"**Seats Available:** {new_carpool['seats_available']}")
                    st.markdown(f"**Price per Seat:** ₹{new_carpool['price_per_seat']}")
                    
                    if preferences:
                        st.markdown(f"**Preferences:** {', '.join(preferences)}")
                
                # Show on map
                m = create_tamil_nadu_map()
                
                # Add markers and route
                start_coords = MAJOR_CITIES[offer_start]
                end_coords = MAJOR_CITIES[offer_end]
                
                # Start marker
                folium.Marker(
                    location=start_coords,
                    popup=f"Start: {offer_start}",
                    tooltip=f"Start: {offer_start}",
                    icon=folium.Icon(color="green", icon="play", prefix="fa")
                ).add_to(m)
                
                # End marker
                folium.Marker(
                    location=end_coords,
                    popup=f"End: {offer_end}",
                    tooltip=f"End: {offer_end}",
                    icon=folium.Icon(color="red", icon="stop", prefix="fa")
                ).add_to(m)
                
                # Route line with via points
                route_points = [start_coords]
                
                # Add via points if any
                for via in via_points:
                    if via in MAJOR_CITIES:
                        # Add via point marker
                        via_coords = MAJOR_CITIES[via]
                        
                        folium.Marker(
                            location=via_coords,
                            popup=f"Via: {via}",
                            tooltip=f"Via: {via}",
                            icon=folium.Icon(color="blue", icon="arrow-right", prefix="fa")
                        ).add_to(m)
                        
                        route_points.append(via_coords)
                
                route_points.append(end_coords)
                
                # Add route line
                folium.PolyLine(
                    locations=route_points,
                    color="blue",
                    weight=3,
                    opacity=0.7
                ).add_to(m)
                
                # Display the map
                display_map(m)
    
    with tab3:
        st.header("My Rides")
        
        # In a real app, would filter by user ID
        # For demo, just show all rides
        
        # Create tabs for offered and booked rides
        ride_tab1, ride_tab2 = st.tabs(["My Offered Rides", "My Booked Rides"])
        
        with ride_tab1:
            st.subheader("Rides You've Offered")
            
            # For demo, use first 2 carpools as examples
            my_offers = carpools[:2]
            
            if my_offers:
                for carpool in my_offers:
                    with st.expander(f"{carpool['route']} - {carpool['date']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Route:** {carpool['route']}")
                            
                            if "via" in carpool and carpool["via"]:
                                st.markdown(f"**Via:** {', '.join(carpool['via'])}")
                                
                            st.markdown(f"**Date:** {carpool['date']}")
                            st.markdown(f"**Time:** {carpool['time']}")
                            st.markdown(f"**Price per Seat:** ₹{carpool['price_per_seat']}")
                        
                        with col2:
                            # Display booked passengers
                            st.markdown("**Passengers:**")
                            
                            # Generate random passenger data for demo
                            num_passengers = random.randint(1, carpool['seats_available'])
                            passengers = []
                            
                            for i in range(num_passengers):
                                passenger_name = f"Passenger {i+1}"
                                passenger_rating = round(random.uniform(3.5, 5.0), 1)
                                passenger_status = random.choice(["Confirmed", "Pending"])
                                
                                passengers.append({
                                    "name": passenger_name,
                                    "rating": passenger_rating,
                                    "status": passenger_status
                                })
                            
                            # Display passengers
                            if passengers:
                                for passenger in passengers:
                                    status_color = "green" if passenger["status"] == "Confirmed" else "orange"
                                    st.markdown(f"{passenger['name']} ({passenger['rating']}⭐) - <span style='color:{status_color};'>{passenger['status']}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("No passengers yet.")
                        
                        # Action buttons
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Cancel Ride", key=f"cancel_{carpool['id']}"):
                                st.warning("Are you sure you want to cancel this ride? This action cannot be undone.")
                                
                                if st.button("Yes, Cancel", key=f"confirm_cancel_{carpool['id']}"):
                                    st.success("Ride cancelled successfully. All passengers have been notified.")
                        
                        with col2:
                            if st.button("Edit Details", key=f"edit_{carpool['id']}"):
                                st.info("Edit functionality will be available in the next update.")
            else:
                st.info("You haven't offered any rides yet.")
        
        with ride_tab2:
            st.subheader("Rides You've Booked")
            
            # For demo, use next 2 carpools as examples
            my_bookings = carpools[2:4] if len(carpools) > 3 else []
            
            if my_bookings:
                for carpool in my_bookings:
                    with st.expander(f"{carpool['route']} - {carpool['date']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Driver:** {carpool['driver_name']} ({carpool['driver_rating']}⭐)")
                            st.markdown(f"**Vehicle:** {carpool['vehicle']} ({carpool['vehicle_number']})")
                            st.markdown(f"**Route:** {carpool['route']}")
                            
                            if "via" in carpool and carpool["via"]:
                                st.markdown(f"**Via:** {', '.join(carpool['via'])}")
                        
                        with col2:
                            st.markdown(f"**Date:** {carpool['date']}")
                            st.markdown(f"**Time:** {carpool['time']}")
                            st.markdown(f"**Price:** ₹{carpool['price_per_seat']}")
                            st.markdown(f"**Status:** <span style='color:green;'>Confirmed</span>", unsafe_allow_html=True)
                            st.markdown(f"**Contact:** {carpool['phone']}")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("Cancel Booking", key=f"cancel_booking_{carpool['id']}"):
                                st.warning("Are you sure you want to cancel this booking? Cancellation may be subject to a fee.")
                                
                                if st.button("Yes, Cancel", key=f"confirm_booking_cancel_{carpool['id']}"):
                                    st.success("Booking cancelled successfully.")
                        
                        with col2:
                            if st.button("Message Driver", key=f"msg_driver_{carpool['id']}"):
                                st.info("Messaging feature will be available in the next update.")
                        
                        with col3:
                            if st.button("Track Ride", key=f"track_{carpool['id']}"):
                                st.info("Live tracking will be available on the day of the ride.")
            else:
                st.info("You haven't booked any rides yet.")
    
    # Community statistics and tips
    st.header("Carpooling Benefits")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Average Savings",
            "₹1,250/month",
            "40% vs driving alone"
        )
    
    with col2:
        st.metric(
            "CO₂ Reduction",
            "120 kg/month",
            "per regular carpooler"
        )
    
    with col3:
        st.metric(
            "Traffic Reduction",
            "15-20%",
            "with 20% carpooling adoption"
        )
    
    # Tips
    st.subheader("Carpooling Tips")
    
    tips = [
        "Always verify the driver's identity and vehicle details before starting the journey.",
        "Share your trip details with a friend or family member for safety.",
        "Be punctual and respectful of your fellow carpoolers' time.",
        "Keep the vehicle clean and avoid bringing strong-smelling food.",
        "If you're a driver, ensure your vehicle is well-maintained for a safe journey."
    ]
    
    for tip in tips:
        st.markdown(f"• {tip}")

if __name__ == "__main__":
    main()
