<<<<<<< HEAD
"# Vazhithunai Standalone" 
=======
# Vazhitunai - Traffic Management System

A comprehensive traffic management application built with Streamlit that provides predictive routing, parking management, public transportation tracking, and more.

## Features

- **Predictive Routing**: AI-powered route suggestions with real-time traffic updates
- **Parking Management**: Find and reserve parking spaces with IoT integration
- **Public Transportation**: Real-time tracking of buses, trains, and metros
- **Accident Management**: First aid instructions and emergency service locations
- **EV Charging Stations**: Locate and check availability of charging stations
- **Carpooling**: Community-driven ride sharing platform
- **FASTag Management**: Check balance and locate toll plazas
- **Event Reporting**: Report and view traffic events like construction, roadblocks, etc.

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/vazhitunai.git
   cd vazhitunai
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root directory
   - Add your Firebase and Google Maps API credentials:
     ```
     FIREBASE_API_KEY=your_firebase_api_key
     FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
     FIREBASE_DATABASE_URL=your_firebase_database_url
     FIREBASE_PROJECT_ID=your_firebase_project_id
     FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
     FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
     FIREBASE_APP_ID=your_firebase_app_id
     FIREBASE_MEASUREMENT_ID=your_firebase_measurement_id
     GOOGLE_MAPS_API_KEY=your_google_maps_api_key
     ```

4. Run the application:
   ```
   # Run on default port 8501
   streamlit run app.py

   # Or specify a custom port if 8501 is in use
   streamlit run app.py --server.port 8502
   ```

   Note: If you encounter a port conflict, try using a different port number using the `--server.port` option.

## Deployment

This application is designed to be deployed on Render. Follow these steps:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false`

## Technologies Used

- Streamlit
- Folium (for interactive maps)
- Plotly (for data visualization)
- Pandas (for data handling)

## License

[MIT License](LICENSE)
>>>>>>> dd1bd38a (Checkpoint before revert - Build the initial prototype)
