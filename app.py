import streamlit as st
from PIL import Image
import base64

st.set_page_config(
    page_title="Vazhitunai - Traffic Management",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main application header
st.title("🚦 Vazhitunai")
st.subheader("Comprehensive Traffic Management System")

# App description
st.markdown("""
Welcome to Vazhitunai, your comprehensive traffic management companion. 
Our application offers a range of services to make your travel experience smoother and safer.
""")

# Main dashboard content
col1, col2, col3 = st.columns(3)

with col1:
    st.info("### 🗺️ Predictive Routing")
    st.markdown("""
    Get intelligent route suggestions with real-time traffic updates and predictive analytics to avoid congestion.
    """)
    st.page_link("pages/1_predictive_routing.py", label="Plan Your Route", icon="🗺️")
    
    st.info("### 🚌 Public Transportation")
    st.markdown("""
    Track public transport in real-time and plan your journey with accurate arrival predictions.
    """)
    st.page_link("pages/3_public_transportation.py", label="Track Public Transport", icon="🚌")
    
    st.info("### 🚗 Carpooling")
    st.markdown("""
    Join the community-driven carpooling network to share rides, reduce costs, and minimize traffic.
    """)
    st.page_link("pages/6_carpooling.py", label="Find Carpool Options", icon="🚗")

with col2:
    st.info("### 🅿️ Parking Management")
    st.markdown("""
    Find and reserve parking spaces in advance with our IoT-integrated parking management system.
    """)
    st.page_link("pages/2_parking_management.py", label="Find Parking", icon="🅿️")
    
    st.info("### 🚑 Accident Management")
    st.markdown("""
    Access first aid instructions, emergency contacts, and alternative routes in case of accidents.
    """)
    st.page_link("pages/4_accident_management.py", label="Accident Resources", icon="🚑")
    
    st.info("### 💳 FASTag Management")
    st.markdown("""
    Check your FASTag balance, locate toll plazas, and manage your toll payments efficiently.
    """)
    st.page_link("pages/7_fastag.py", label="FASTag Services", icon="💳")

with col3:
    st.info("### ⚡ EV Charging Stations")
    st.markdown("""
    Locate the nearest EV charging stations, check availability, and plan your charging stops.
    """)
    st.page_link("pages/5_ev_charging.py", label="Find Charging Stations", icon="⚡")
    
    st.info("### 🚧 Event Reporting")
    st.markdown("""
    Report and view construction, roadblocks, or events that might affect traffic in your area.
    """)
    st.page_link("pages/8_event_reporting.py", label="Report Events", icon="🚧")

# About section
st.markdown("---")
st.markdown("### About Vazhitunai")
st.markdown("""
Vazhitunai is designed to provide comprehensive traffic management solutions. 
Our mission is to make commuting safer, more efficient, and stress-free by leveraging 
modern technology and community participation.
""")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("#### Vazhitunai © 2023 | Traffic Management")
    st.markdown("For feedback and support: support@vazhitunai.com")
