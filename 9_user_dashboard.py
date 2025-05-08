import streamlit as st
from firebase_utils import init_firebase, auth_required, get_from_rtdb, save_to_rtdb, push_to_rtdb

# Initialize Firebase
init_firebase()

def load_user_data(user_id):
    """Load user data from Realtime Database"""
    result = get_from_rtdb(f'users/{user_id}')
    if result['success']:
        return result['data']
    return None

def save_user_data(user_id, data):
    """Save user data to Realtime Database"""
    result = save_to_rtdb(f'users/{user_id}', data)
    if result['success']:
        st.success('Profile updated successfully!')
        st.rerun()
    else:
        st.error(f'Failed to update profile: {result["error"]}')

def main():
    st.title("👤 User Dashboard")
    
    # Check if user is logged in
    if 'user' not in st.session_state or not st.session_state.user:
        st.warning("Please login to access your dashboard")
        st.page_link("pages/0_login.py", label="Go to Login", icon="🔐")
        return
    
    # Load user data
    user_id = st.session_state.user['uid']
    user_data = load_user_data(user_id)
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["Profile", "Vehicles", "History"])
    
    with tab1:
        st.header("Profile Information")
        profile_data = user_data.get('profile', {}) if user_data else {}
        
        # Profile form
        with st.form("profile_form"):
            name = st.text_input("Full Name", value=profile_data.get('name', ''))
            phone = st.text_input("Phone Number", value=profile_data.get('phone', ''))
            address = st.text_area("Address", value=profile_data.get('address', ''))
            emergency_contact = st.text_input("Emergency Contact", value=profile_data.get('emergency_contact', ''))
            
            if st.form_submit_button("Update Profile"):
                profile_data = {
                    "name": name,
                    "phone": phone,
                    "address": address,
                    "emergency_contact": emergency_contact,
                    "email": st.session_state.user['email']
                }
                save_user_data(user_id, {"profile": profile_data})
    
    with tab2:
        st.header("Vehicle Information")
        
        # Add new vehicle form
        with st.form("vehicle_form"):
            vehicle_type = st.selectbox(
                "Vehicle Type",
                ["Car", "Motorcycle", "Bus", "Truck", "Other"]
            )
            registration = st.text_input("Registration Number")
            make = st.text_input("Make")
            model = st.text_input("Model")
            year = st.number_input("Year", min_value=1900, max_value=2024)
            fastag_id = st.text_input("FASTag ID (Optional)")
            
            if st.form_submit_button("Add Vehicle"):
                vehicle_data = {
                    "type": vehicle_type,
                    "registration": registration,
                    "make": make,
                    "model": model,
                    "year": year,
                    "fastag_id": fastag_id
                }
                result = push_to_rtdb(f'users/{user_id}/vehicles', vehicle_data)
                if result['success']:
                    st.success('Vehicle added successfully!')
                    st.rerun()
                else:
                    st.error(f'Failed to add vehicle: {result["error"]}')
        
        # Display existing vehicles
        st.subheader("Your Vehicles")
        vehicles = user_data.get('vehicles', {}) if user_data else {}
        if vehicles:
            for vehicle_id, vehicle in vehicles.items():
                with st.expander(f"{vehicle['make']} {vehicle['model']} ({vehicle['registration']})"):
                    st.write(f"Type: {vehicle['type']}")
                    st.write(f"Year: {vehicle['year']}")
                    if vehicle.get('fastag_id'):
                        st.write(f"FASTag ID: {vehicle['fastag_id']}")
        else:
            st.info("No vehicles added yet")
    
    with tab3:
        st.header("Activity History")
        
        # Activity type filter
        activity_type = st.selectbox(
            "Filter by Activity",
            ["All", "Parking", "FASTag", "EV Charging", "Public Transport"]
        )
        
        # Display activity history
        history = user_data.get('history', {}) if user_data else {}
        if history:
            for activity_id, activity in history.items():
                if activity_type == "All" or activity['type'] == activity_type:
                    with st.expander(f"{activity['type']} - {activity['date']}"):
                        for key, value in activity.items():
                            if key not in ['type', 'date']:
                                st.write(f"{key.title()}: {value}")
        else:
            st.info("No activity history available")

if __name__ == "__main__":
    main()