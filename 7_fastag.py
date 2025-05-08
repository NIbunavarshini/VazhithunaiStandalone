import streamlit as st
import pandas as pd
import json
import random
from datetime import datetime, timedelta
import plotly.express as px
import folium
from streamlit_folium import st_folium

from utils import create_tamil_nadu_map, display_map, MAJOR_CITIES

def load_fastag_data():
    try:
        with open("data/fastag_data.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty data structure if file not found
        return {
            "user_data": {
                "name": "",
                "email": "",
                "phone": "",
                "vehicles": []
            },
            "recent_transactions": [],
            "recharge_history": []
        }

def load_toll_plazas():
    try:
        with open("data/toll_plazas.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def show_toll_plazas():
    toll_plazas = load_toll_plazas()
    
    if not toll_plazas:
        st.warning("Toll plaza data is not available. Please check your connection.")
        return
    
    st.subheader("Toll Plaza Map")
    
    # Create map
    m = create_tamil_nadu_map()
    
    # Add toll plaza markers
    for plaza in toll_plazas:
        # Create popup content
        popup_html = f"""
        <div style="width:250px">
            <h4>{plaza["name"]}</h4>
            <p><b>Location:</b> {plaza["location"]}</p>
            <p><b>Nearest City:</b> {plaza["nearest_city"]} ({plaza["distance_from_city"]} km)</p>
            <p><b>FASTag Lanes:</b> {plaza["fastag_lanes"]}</p>
            <p><b>Cash Lanes:</b> {plaza["cash_lanes"]}</p>
            <p><b>Current Wait Time:</b> {plaza["current_waiting_time"]}</p>
            <br>
            <p><b>Fees:</b></p>
            <ul>
                <li>Car/Jeep/Van: ₹{plaza["fees"]["Car/Jeep/Van"]}</li>
                <li>LCV: ₹{plaza["fees"]["LCV"]}</li>
                <li>Bus/Truck: ₹{plaza["fees"]["Bus/Truck"]}</li>
                <li>Heavy Vehicle: ₹{plaza["fees"]["Heavy Vehicle"]}</li>
            </ul>
        </div>
        """
        
        # Add marker
        folium.Marker(
            location=plaza["coordinates"],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=plaza["name"],
            icon=folium.Icon(color="blue", icon="road", prefix="fa")
        ).add_to(m)
    
    # Display map
    display_map(m)
    
    # Toll plaza list
    st.subheader("Toll Plaza List")
    
    # Sort by nearest city
    toll_plazas.sort(key=lambda x: x["nearest_city"])
    
    for plaza in toll_plazas:
        with st.expander(f"{plaza['name']} - {plaza['location']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Nearest City:** {plaza['nearest_city']} ({plaza['distance_from_city']} km)")
                st.markdown(f"**FASTag Lanes:** {plaza['fastag_lanes']}")
                st.markdown(f"**Cash Lanes:** {plaza['cash_lanes']}")
                st.markdown(f"**Current Wait Time:** {plaza['current_waiting_time']}")
                st.markdown(f"**Status:** {plaza['status']}")
            
            with col2:
                st.markdown("**Toll Fees:**")
                st.markdown(f"- Car/Jeep/Van: ₹{plaza['fees']['Car/Jeep/Van']}")
                st.markdown(f"- LCV: ₹{plaza['fees']['LCV']}")
                st.markdown(f"- Bus/Truck: ₹{plaza['fees']['Bus/Truck']}")
                st.markdown(f"- Heavy Vehicle: ₹{plaza['fees']['Heavy Vehicle']}")
            
            # Show FASTag vs Cash comparison
            st.markdown("**FASTag vs Cash Time Savings:**")
            
            # Generate random wait times for comparison
            fastag_wait = int(plaza["current_waiting_time"].split(" ")[0])
            cash_wait = fastag_wait * random.uniform(2.5, 4)  # Cash is 2.5-4x slower
            
            # Create data for comparison
            comparison_data = pd.DataFrame({
                "Payment Method": ["FASTag", "Cash"],
                "Wait Time (minutes)": [fastag_wait, int(cash_wait)]
            })
            
            # Create bar chart
            fig = px.bar(
                comparison_data,
                x="Payment Method",
                y="Wait Time (minutes)",
                color="Payment Method",
                color_discrete_map={"FASTag": "green", "Cash": "red"},
                text="Wait Time (minutes)"
            )
            
            fig.update_layout(
                height=250,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

def show_fastag_balance():
    # Load FASTag data
    fastag_data = load_fastag_data()
    
    user_data = fastag_data["user_data"]
    vehicles = user_data["vehicles"]
    
    if not vehicles:
        st.warning("No registered vehicles found.")
        return
    
    st.subheader("FASTag Balance")
    
    # Select vehicle
    if len(vehicles) > 1:
        selected_vehicle_reg = st.selectbox(
            "Select Vehicle",
            options=[v["registration"] for v in vehicles]
        )
        
        selected_vehicle = next(v for v in vehicles if v["registration"] == selected_vehicle_reg)
    else:
        selected_vehicle = vehicles[0]
    
    # Display vehicle information and balance
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.metric(
            "FASTag Balance",
            f"₹{selected_vehicle['balance']:.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Last Recharge",
            f"₹{next((r['amount'] for r in fastag_data['recharge_history'] if r['vehicle_reg'] == selected_vehicle['registration']), 0):.2f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Last Transaction",
            f"₹{selected_vehicle['last_transaction']['amount']:.2f}",
            delta=None
        )
    
    # Vehicle details
    with st.expander("Vehicle Details"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Vehicle Type:** {selected_vehicle['type']}")
            st.markdown(f"**Make:** {selected_vehicle['make']}")
            st.markdown(f"**Model:** {selected_vehicle['model']}")
            st.markdown(f"**Registration:** {selected_vehicle['registration']}")
        
        with col2:
            st.markdown(f"**FASTag ID:** {selected_vehicle['fastag_id']}")
            st.markdown(f"**Bank:** {selected_vehicle['bank']}")
            st.markdown(f"**Last Transaction Date:** {selected_vehicle['last_transaction']['date']}")
            st.markdown(f"**Last Transaction Location:** {selected_vehicle['last_transaction']['location']}")
    
    # Low balance warning
    if selected_vehicle['balance'] < 200:
        st.warning(f"⚠️ Low Balance Alert! Your FASTag balance is below ₹200. Please recharge to avoid inconvenience.")
    
    # Recharge section
    st.subheader("Recharge FASTag")
    
    # Recharge amount selection
    col1, col2 = st.columns(2)
    
    with col1:
        recharge_amount = st.selectbox(
            "Select Amount",
            options=[200, 500, 1000, 1500, 2000, "Other"]
        )
        
        if recharge_amount == "Other":
            recharge_amount = st.number_input(
                "Enter Amount",
                min_value=100,
                max_value=10000,
                value=500,
                step=100
            )
    
    with col2:
        payment_method = st.selectbox(
            "Payment Method",
            options=["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"]
        )
    
    # Recharge button
    if st.button("Recharge Now"):
        st.success(f"FASTag recharge of ₹{recharge_amount} successful! Your updated balance is ₹{selected_vehicle['balance'] + recharge_amount:.2f}")
    
    # Recent transactions
    st.subheader("Recent Transactions")
    
    # Filter transactions for selected vehicle
    vehicle_transactions = [t for t in fastag_data["recent_transactions"] if t["vehicle_reg"] == selected_vehicle["registration"]]
    
    if vehicle_transactions:
        transactions_df = pd.DataFrame(vehicle_transactions)
        transactions_df = transactions_df[["date", "time", "toll_plaza", "amount", "status"]]
        transactions_df.columns = ["Date", "Time", "Toll Plaza", "Amount (₹)", "Status"]
        
        st.dataframe(transactions_df, use_container_width=True)
        
        # Transaction analysis
        st.subheader("Transaction Analysis")
        
        # Create monthly spending chart
        # For demo, group transactions by month (fabricated for illustration)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        monthly_spending = [350, 410, 280, 520, 380, 460]
        
        monthly_data = pd.DataFrame({
            "Month": months,
            "Spending (₹)": monthly_spending
        })
        
        fig = px.line(
            monthly_data,
            x="Month",
            y="Spending (₹)",
            markers=True,
            labels={"Spending (₹)": "Monthly Toll Expenses (₹)"}
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recent transactions found for this vehicle.")

def show_trip_calculator():
    st.subheader("Toll Trip Calculator")
    
    st.markdown("""
    Calculate the total toll expenses for your journey between cities in Tamil Nadu.
    """)
    
    # Route selection
    col1, col2 = st.columns(2)
    
    with col1:
        start_city = st.selectbox(
            "Starting Point",
            options=list(MAJOR_CITIES.keys()),
            key="toll_start"
        )
    
    with col2:
        end_city = st.selectbox(
            "Destination",
            options=list(MAJOR_CITIES.keys()),
            key="toll_end"
        )
    
    # Vehicle type
    vehicle_type = st.selectbox(
        "Vehicle Type",
        options=["Car/Jeep/Van", "LCV", "Bus/Truck", "Heavy Vehicle"]
    )
    
    # Return journey option
    return_journey = st.checkbox("Include Return Journey")
    
    # Calculate button
    if st.button("Calculate Toll Cost"):
        if start_city == end_city:
            st.error("Starting point and destination cannot be the same.")
        else:
            # Load routes data
            try:
                with open("data/routes.json", "r") as f:
                    routes = json.load(f)
                    
                # Find matching route
                matching_routes = [r for r in routes if r["start"] == start_city and r["end"] == end_city]
                
                if not matching_routes:
                    # Try reverse route
                    matching_routes = [r for r in routes if r["start"] == end_city and r["end"] == start_city]
                
                if matching_routes:
                    selected_route = matching_routes[0]
                    
                    # Get toll plazas
                    toll_plazas = load_toll_plazas()
                    
                    # Create map
                    m = create_tamil_nadu_map()
                    
                    # Add start and end markers
                    folium.Marker(
                        location=MAJOR_CITIES[start_city],
                        popup=start_city,
                        tooltip=f"Start: {start_city}",
                        icon=folium.Icon(color="green", icon="play", prefix="fa")
                    ).add_to(m)
                    
                    folium.Marker(
                        location=MAJOR_CITIES[end_city],
                        popup=end_city,
                        tooltip=f"End: {end_city}",
                        icon=folium.Icon(color="red", icon="stop", prefix="fa")
                    ).add_to(m)
                    
                    # Create route line
                    route_points = [MAJOR_CITIES[start_city]]
                    
                    # Add toll plazas along route
                    toll_count = selected_route.get("toll_plazas", 0)
                    total_distance = selected_route.get("distance", 0)
                    
                    # For demo purposes, randomly position toll plazas along route
                    route_toll_plazas = []
                    
                    for i in range(toll_count):
                        # Random position along route
                        progress = (i + 1) / (toll_count + 1)
                        
                        start_coords = MAJOR_CITIES[start_city]
                        end_coords = MAJOR_CITIES[end_city]
                        
                        toll_lat = start_coords[0] + progress * (end_coords[0] - start_coords[0])
                        toll_lng = start_coords[1] + progress * (end_coords[1] - start_coords[1])
                        
                        # Choose a random toll plaza
                        if toll_plazas:
                            toll_plaza = random.choice(toll_plazas)
                            
                            # Add to route points
                            route_points.append([toll_lat, toll_lng])
                            
                            # Add toll marker
                            folium.Marker(
                                location=[toll_lat, toll_lng],
                                popup=toll_plaza["name"],
                                tooltip=f"Toll: {toll_plaza['name']}",
                                icon=folium.Icon(color="blue", icon="usd", prefix="fa")
                            ).add_to(m)
                            
                            # Add to list
                            route_toll_plazas.append({
                                "name": toll_plaza["name"],
                                "distance": round(total_distance * progress, 1),
                                "fee": toll_plaza["fees"][vehicle_type]
                            })
                    
                    # Add end point to route
                    route_points.append(MAJOR_CITIES[end_city])
                    
                    # Add route line
                    folium.PolyLine(
                        locations=route_points,
                        color="blue",
                        weight=4,
                        opacity=0.7
                    ).add_to(m)
                    
                    # Display map
                    display_map(m)
                    
                    # Calculate total cost
                    total_cost = sum(plaza["fee"] for plaza in route_toll_plazas)
                    if return_journey:
                        total_cost *= 2
                    
                    # Display results
                    st.subheader("Toll Cost Breakdown")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Total Distance",
                            f"{selected_route['distance']} km",
                            delta=None
                        )
                    
                    with col2:
                        st.metric(
                            "Number of Tolls",
                            str(toll_count),
                            delta=None
                        )
                    
                    with col3:
                        st.metric(
                            "Total Toll Cost",
                            f"₹{total_cost}",
                            delta=None
                        )
                    
                    # Display toll breakdown
                    st.markdown("### Toll Plaza Details")
                    
                    toll_df = pd.DataFrame(route_toll_plazas)
                    toll_df.columns = ["Toll Plaza", "Distance (km)", "Fee (₹)"]
                    
                    if return_journey:
                        toll_df["Return Fee (₹)"] = toll_df["Fee (₹)"]
                        toll_df["Total Fee (₹)"] = toll_df["Fee (₹)"] * 2
                    
                    st.dataframe(toll_df, use_container_width=True)
                    
                    # Show FASTag savings
                    st.subheader("FASTag Savings")
                    
                    # Calculate savings (FASTag users typically save 5-10% due to discounts)
                    cash_cost = total_cost
                    fastag_cost = total_cost * 0.9  # 10% discount
                    
                    savings_data = pd.DataFrame({
                        "Payment Method": ["Cash", "FASTag"],
                        "Cost (₹)": [cash_cost, fastag_cost]
                    })
                    
                    fig = px.bar(
                        savings_data,
                        x="Payment Method",
                        y="Cost (₹)",
                        color="Payment Method",
                        color_discrete_map={"Cash": "red", "FASTag": "green"},
                        text="Cost (₹)"
                    )
                    
                    fig.update_layout(
                        height=300,
                        margin=dict(l=10, r=10, t=30, b=10),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.success(f"Using FASTag saves you approximately ₹{cash_cost - fastag_cost:.2f} on this journey!")
                else:
                    st.warning(f"No direct route information available for {start_city} to {end_city}.")
            except (FileNotFoundError, json.JSONDecodeError):
                st.error("Route data is not available. Please check your connection.")

def main():
    st.title("💳 FASTag Management")
    
    # Introduction
    st.markdown("""
    Manage your FASTag account, check balance, view transaction history, and find toll plazas 
    across Tamil Nadu.
    """)
    
    # Main navigation tabs
    tab1, tab2, tab3 = st.tabs(["FASTag Balance", "Toll Plazas", "Trip Calculator"])
    
    with tab1:
        show_fastag_balance()
    
    with tab2:
        show_toll_plazas()
    
    with tab3:
        show_trip_calculator()
    
    # Tips section
    st.header("FASTag Tips")
    
    tips = [
        "Always maintain a minimum balance of ₹200 in your FASTag to avoid inconvenience.",
        "Link your FASTag to a UPI ID for quick and easy recharges.",
        "FASTag is mandatory for all vehicles in India. Non-compliance may result in paying double the toll fee.",
        "Your FASTag can be used at all electronic toll plazas across India.",
        "FASTag transactions are processed within 10-15 seconds, significantly reducing waiting time at toll plazas."
    ]
    
    for tip in tips:
        st.markdown(f"• {tip}")

if __name__ == "__main__":
    main()
