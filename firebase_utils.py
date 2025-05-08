import streamlit as st
import json
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, db, firestore
from firebase_admin.exceptions import FirebaseError

# Load environment variables
load_dotenv()

# Firebase configuration
FIREBASE_CONFIG = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
}

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Initialize Firebase Admin SDK
cred = credentials.Certificate(FIREBASE_CONFIG)
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
})

# Get database and firestore instances
rtdb = db.reference()
db_store = firestore.client()

def init_firebase():
    """Initialize Firebase in the Streamlit session state"""
    if 'firebase_initialized' not in st.session_state:
        st.session_state.firebase_initialized = True

def auth_required():
    """Check if user is authenticated and redirect to login if not"""
    if 'user' not in st.session_state or not st.session_state.user:
        st.warning("Please log in to access this feature")
        st.page_link("pages/0_login.py", label="Go to Login", icon="🔐")
        return False
    return True

def sign_in_with_email_and_password(email, password):
    """Sign in user with email and password"""
    try:
        user = auth.get_user_by_email(email)
        # In a production environment, you should use proper password hashing
        # This is a simplified version for demonstration
        user_data = {
            'uid': user.uid,
            'email': user.email,
            'displayName': user.display_name or email.split('@')[0],
            'isLoggedIn': True
        }
        st.session_state.user = user_data
        return {'success': True, 'user': user_data}
    except FirebaseError as e:
        return {'success': False, 'error': str(e)}

def sign_up_with_email_and_password(email, password):
    """Create new user with email and password"""
    try:
        user = auth.create_user(email=email, password=password)
        user_data = {
            'uid': user.uid,
            'email': user.email,
            'displayName': email.split('@')[0],
            'isLoggedIn': True
        }
        st.session_state.user = user_data
        return {'success': True, 'user': user_data}
    except FirebaseError as e:
        return {'success': False, 'error': str(e)}

def sign_out():
    """Sign out current user"""
    try:
        st.session_state.user = None
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def save_to_firestore(collection, document_id, data):
    """Save data to Firestore database"""
    try:
        doc_ref = db_store.collection(collection).document(document_id)
        doc_ref.set(data)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_from_firestore(collection, document_id):
    """Get data from Firestore database"""
    try:
        doc_ref = db_store.collection(collection).document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            return {'success': True, 'data': doc.to_dict()}
        return {'success': True, 'data': None}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def query_firestore(collection, field, operator, value):
    """Query data from Firestore database"""
    try:
        query = db_store.collection(collection)
        if operator == '==':
            query = query.where(field, '==', value)
        elif operator == '>':
            query = query.where(field, '>', value)
        elif operator == '<':
            query = query.where(field, '<', value)
        
        docs = query.stream()
        results = [{'id': doc.id, **doc.to_dict()} for doc in docs]
        return {'success': True, 'data': results}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def save_to_rtdb(path, data):
    """Save data to Realtime Database"""
    try:
        ref = db.reference(path)
        ref.set(data)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def push_to_rtdb(path, data):
    """Push data to Realtime Database with auto-generated key"""
    try:
        ref = db.reference(path)
        new_ref = ref.push(data)
        return {'success': True, 'key': new_ref.key}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_from_rtdb(path):
    """Get data from Realtime Database"""
    try:
        ref = db.reference(path)
        data = ref.get()
        return {'success': True, 'data': data}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_in_rtdb(path, data):
    """Update data in Realtime Database"""
    try:
        ref = db.reference(path)
        ref.update(data)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def remove_from_rtdb(path):
    """Remove data from Realtime Database"""
    try:
        ref = db.reference(path)
        ref.delete()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Function to initialize Google Maps
def init_google_maps():
    """Initialize Google Maps API"""
    maps_js = f"""
    <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}&libraries=places,directions,geometry"></script>
    """
    st.components.v1.html(maps_js, height=0)

# Function to create a Google Maps component
def create_google_map(map_id, center, zoom=10, height=400):
    """Create a Google Maps component"""
    map_html = f"""
    <div style="width: 100%; height: {height}px;">
        <div id="{map_id}" style="width: 100%; height: 100%;"></div>
    </div>
    <script>
        var map = new google.maps.Map(document.getElementById('{map_id}'), {{
            center: {center},
            zoom: {zoom}
        }});
    </script>
    """
    st.components.v1.html(map_html, height=height)
    return map_id

# Function to add a marker to a Google Map
def add_marker(map_id, position, title):
    """Add a marker to a Google Map"""
    marker_js = f"""
    <script>
        new google.maps.Marker({{
            position: {position},
            map: map,
            title: '{title}'
        }});
    </script>
    """
    st.components.v1.html(marker_js, height=0)

# Function to calculate and display a route on Google Maps
def calculate_route(map_id, origin, destination, waypoints=None, travel_mode='DRIVING'):
    """Calculate and display a route on Google Maps"""
    if waypoints is None:
        waypoints = []
    
    route_js = f"""
    <script>
        var directionsService = new google.maps.DirectionsService();
        var directionsRenderer = new google.maps.DirectionsRenderer();
        directionsRenderer.setMap(map);
        
        var request = {{
            origin: {origin},
            destination: {destination},
            waypoints: {json.dumps(waypoints)},
            travelMode: '{travel_mode}'
        }};
        
        directionsService.route(request, function(result, status) {{
            if (status == 'OK') {{
                directionsRenderer.setDirections(result);
            }}
        }});
    </script>
    """
    st.components.v1.html(route_js, height=0)

# Function to geocode an address
def geocode_address(address):
    """Convert address to coordinates using Google Maps Geocoding API"""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return {'lat': location['lat'], 'lng': location['lng']}
    return None