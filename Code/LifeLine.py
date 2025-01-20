import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.distance import geodesic
import numpy as np
import time
import random
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Emergency Response System Functions
# Replace with your OpenRouteService API key
ORS_API_KEY = "5b3ce3597851110001cf6248ec4d4576570542e5aab0e32c57b1491d"

# Define the geographical boundaries of Bangalore
BANGALORE_BOUNDS = {
    "lat_min": 12.8516,
    "lat_max": 13.0848,
    "lon_min": 77.5697,
    "lon_max": 77.7496,
}

# Generate uniform ambulance locations
def generate_ambulance_locations(n, bounds):
    latitudes = np.random.uniform(bounds['lat_min'], bounds['lat_max'], n)
    longitudes = np.random.uniform(bounds['lon_min'], bounds['lon_max'], n)
    return [("Ambulance {}".format(i + 1), lat, lon) for i, (lat, lon) in enumerate(zip(latitudes, longitudes))]

AMBULANCES = generate_ambulance_locations(2500, BANGALORE_BOUNDS)

# Geocoding function with caching
location_cache = {}

def geocode_location(location):
    if location in location_cache:
        return location_cache[location]
    try:
        geolocator = Nominatim(user_agent="LifeLine - jaydev.cs22@bmsce.ac.in", timeout=10)
        time.sleep(1)  
        loc = geolocator.geocode(location)
        if loc:
            coords = [loc.latitude, loc.longitude]
            location_cache[location] = coords
            return coords
        st.error("Location not found.")
        return None
    except GeocoderTimedOut:
        st.error("Geocoding service timed out. Please try again.")
        return None

# Find the nearest hospital
def find_nearest_hospital(patient_coords, specialization="general", radius=5000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = (
        f'[out:json];node["amenity"="hospital"]'
        f'{"[\"healthcare:speciality\"~\"%s\"]" % specialization if specialization != "general" else ""} '
        f'(around:{radius},{patient_coords[0]},{patient_coords[1]});out body;'
    )
    response = requests.get(overpass_url, params={'data': query})
    data = response.json()
    hospitals = data.get('elements', [])
    if not hospitals:
        return None
    nearest_hospital = None
    min_distance = float('inf')
    for hospital in hospitals:
        hospital_coords = (hospital['lat'], hospital['lon'])
        distance = geodesic(patient_coords, hospital_coords).km
        if distance < min_distance:
            min_distance = distance
            nearest_hospital = hospital
    return nearest_hospital

# Get route between patient and destination
def get_route(start_coords, end_coords):
    ors_url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {'Authorization': ORS_API_KEY}
    params = {'start': f"{start_coords[1]},{start_coords[0]}", 'end': f"{end_coords[1]},{end_coords[0]}"}
    response = requests.get(ors_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching route: {response.status_code} - {response.text}")
        return None

# Function to simulate traffic light state (Green or Red)
def simulate_traffic_light_state():
    return random.choice(["green", "red"])

# Display route on map with traffic signals
# Function to calculate travel time and display along with traffic signals
def display_route_with_traffic(patient_coords, destination_coords, is_hospital=True):
    route_data = get_route(patient_coords, destination_coords)
    if route_data and 'features' in route_data:
        route_map = folium.Map(location=[patient_coords[0], patient_coords[1]], zoom_start=13)
        folium.Marker([patient_coords[0], patient_coords[1]], popup="Patient Location", icon=folium.Icon(color="green")).add_to(route_map)
        folium.Marker([destination_coords[0], destination_coords[1]], popup="Destination", icon=folium.Icon(color="red" if is_hospital else "blue")).add_to(route_map)

        route_geometry = route_data['features'][0]['geometry']['coordinates']
        folium.PolyLine(locations=[(coord[1], coord[0]) for coord in route_geometry], color="red", weight=5).add_to(route_map)

        # Find real traffic signals along the route
        traffic_signals = find_signals_along_route(route_geometry)
        traffic_signal_count = len(traffic_signals)

        # Simulate traffic light state and calculate times
        traffic_signal_details = []
        cumulative_time = 0  # Cumulative travel time in minutes
        average_speed_kmh = 40  # Average ambulance speed in km/h
        speed_km_per_min = average_speed_kmh / 60

        for i, signal_coords in enumerate(traffic_signals):
            state = simulate_traffic_light_state()
            color = "green" if state == "green" else "red"

            # Calculate distance to the current signal
            if i == 0:
                prev_coords = patient_coords
            else:
                prev_coords = traffic_signals[i - 1]
            distance_km = geodesic(prev_coords, signal_coords).km
            travel_time = distance_km / speed_km_per_min
            cumulative_time += travel_time

            # Format arrival time
            arrival_time = time.strftime('%H:%M:%S', time.localtime(time.time() + cumulative_time * 60))

            folium.CircleMarker(
                location=signal_coords,
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.5,
            ).add_to(route_map)

            traffic_signal_details.append({
                "coords": signal_coords,
                "state": state,
                "travel_time": round(travel_time, 2),
                "arrival_time": arrival_time,
            })

        st.write(f"Total Traffic Signals along the route: {traffic_signal_count}")
        st.session_state.traffic_signal_details = traffic_signal_details  # Save traffic signal data in session state

        return route_map
    else:
        st.error("No route found.")
        return None

# Function to find traffic signals along the route
def find_signals_along_route(route_geometry):
    signal_locations = []
    for coord in route_geometry:
        lon, lat = coord[0], coord[1]
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
            [out:json];
            node["highway"="traffic_signals"](around:50,{lat},{lon});
            out body;
        """
        response = requests.get(overpass_url, params={'data': query})
        data = response.json()
        signals = data.get('elements', [])
        for signal in signals:
            signal_coords = (signal['lat'], signal['lon'])
            if signal_coords not in signal_locations:
                signal_locations.append(signal_coords)
    return signal_locations

# Function to display traffic signals along with travel and arrival times
def display_traffic_signals_with_coordinates():
    traffic_signal_details = st.session_state.get('traffic_signal_details', [])
    if traffic_signal_details:
        st.write("List of Traffic Signals along the route:")
        for signal in traffic_signal_details:
            st.write(
                f"Traffic Signal at coordinates: {signal['coords']} | "
                f"State: {signal['state']} | "
                f"Travel Time: {signal['travel_time']} mins | "
                f"Arrival Time: {signal['arrival_time']}"
            )
    else:
        st.write("No traffic signals found along the route.")

# Function to find the nearest ambulance
def find_nearest_ambulance(patient_coords):
    nearest_ambulance = None
    min_distance = float('inf')
    for ambulance in AMBULANCES:
        ambulance_name, lat, lon = ambulance
        ambulance_coords = (lat, lon)
        distance = geodesic(patient_coords, ambulance_coords).km
        if distance < min_distance:
            min_distance = distance
            nearest_ambulance = (ambulance_name, ambulance_coords)
    return nearest_ambulance

# Registration and Login Functionality
def login_or_signup():
    if "registered_users" not in st.session_state:
        st.session_state.registered_users = {}  # Store registered users

    st.subheader("Please Login or Sign Up")

    action = st.radio("Choose an action:", ["Register", "Login"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if action == "Register":
        if st.button("Register"):
            st.session_state.registered_users[username] = password
            st.success("Registration successful! Please login.")
    elif action == "Login":
        if st.button("Login"):
            if username in st.session_state.registered_users and st.session_state.registered_users[username] == password:
                st.session_state.logged_in = True
                st.success("Login successful!")
            else:
                st.error("Invalid username or password.")

# Main application
def main():
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        login_or_signup()
    else:
        st.title("LifeLine - Choose Your Service")
        service_choice = st.selectbox("Select a Service", ["Emergency Response System", "AI Disease Prediction System"])

        if service_choice == "Emergency Response System":
            st.title("Find Nearest Hospital and Ambulance Route")
            st.write("You are logged in! Use the form below to find hospitals and ambulances.")
            if "map_data" not in st.session_state:
                st.session_state.map_data = None

            patient_location = st.text_input("Enter Patient Location", "Koramangala, Bengaluru")
            specialization = st.selectbox("Select Specialization", ["general", "cardiology", "oncology", "neurology", "pulmonology"])

            if st.button("Find Nearest Hospital"):
                patient_coords = geocode_location(patient_location)
                if patient_coords:
                    hospital = find_nearest_hospital(patient_coords, specialization)
                    if hospital:
                        hospital_coords = (hospital['lat'], hospital['lon'])
                        st.success(f"Nearest Hospital: {hospital['tags'].get('name', 'Unnamed Hospital')} at {hospital_coords}")
                        st.session_state.map_data = display_route_with_traffic(patient_coords, hospital_coords, is_hospital=True)
                    else:
                        st.error("No hospitals found nearby.")

            if st.button("Find Nearest Ambulance"):
                patient_coords = geocode_location(patient_location)
                if patient_coords:
                    nearest_ambulance = find_nearest_ambulance(patient_coords)
                    if nearest_ambulance:
                        ambulance_name, ambulance_coords = nearest_ambulance
                        st.success(f"Nearest Ambulance: {ambulance_name} at {ambulance_coords}")
                        st.session_state.map_data = display_route_with_traffic(patient_coords, ambulance_coords, is_hospital=False)
                    else:
                        st.error("No ambulances found nearby.")

            # Display the map from session state
            if st.session_state.map_data:
                st_folium(st.session_state.map_data, width=700, height=500)

            # Display traffic signals after the map
            display_traffic_signals_with_coordinates()

        elif service_choice == "AI Disease Prediction System":
            # AI Disease Prediction System UI
            st.subheader("AI Disease Prediction System")

            # Load and preprocess symptom data
            symptom_file_path = 'symtoms_df.csv'  # Dataset with symptoms and diseases
            description_file_path = 'description.csv'  # Dataset with disease descriptions

            symptom_dataset = pd.read_csv(symptom_file_path)
            description_dataset = pd.read_csv(description_file_path)

            # Handle missing values
            symptom_dataset.fillna('none', inplace=True)

            # Extract unique symptoms
            unique_symptoms = set(symptom_dataset[['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']].stack())
            unique_symptoms = sorted([symptom.strip().lower() for symptom in unique_symptoms])
            unique_symptoms.append('none')  # Add 'none' explicitly to avoid KeyError

            # Create mappings for symptoms
            symptom_to_int = {symptom: i for i, symptom in enumerate(unique_symptoms)}
            int_to_symptom = {i: symptom for symptom, i in symptom_to_int.items()}

            # Encode the dataset
            def encode_symptoms(row):
                return [symptom_to_int.get(row['Symptom_1'].strip().lower(), -1),
                        symptom_to_int.get(row['Symptom_2'].strip().lower(), -1),
                        symptom_to_int.get(row['Symptom_3'].strip().lower(), -1),
                        symptom_to_int.get(row['Symptom_4'].strip().lower(), -1)]

            symptom_dataset['Encoded_Symptoms'] = symptom_dataset.apply(encode_symptoms, axis=1)

            # Remove rows with unknown symptoms
            symptom_dataset = symptom_dataset[~symptom_dataset['Encoded_Symptoms'].apply(lambda x: -1 in x)]

            # Encode diseases
            disease_encoder = LabelEncoder()
            symptom_dataset['Encoded_Disease'] = disease_encoder.fit_transform(symptom_dataset['Disease'])

            # Disease description mapping
            disease_description_mapping = description_dataset.set_index('Disease').to_dict(orient='index')

            st.subheader("Select Symptoms")
            selected_symptoms = st.multiselect("Choose up to 4 symptoms from the list below:", unique_symptoms)

            def get_disease_with_most_matching_symptoms(input_symptoms):
                input_symptoms = [symptom.strip().lower() for symptom in input_symptoms]
                input_set = set(input_symptoms)

                best_match = None
                max_matches = 0

                # Compare input symptoms with each disease's symptoms
                for _, row in symptom_dataset.iterrows():
                    disease_symptoms = {int_to_symptom[s] for s in row['Encoded_Symptoms'] if s != symptom_to_int['none']}
                    common_symptoms = input_set.intersection(disease_symptoms)
                    match_count = len(common_symptoms)

                    if match_count > max_matches:
                        max_matches = match_count
                        best_match = row['Disease']

                return best_match, max_matches

            if st.button("Predict"):
                if selected_symptoms:
                    predicted_disease, match_count = get_disease_with_most_matching_symptoms(selected_symptoms)

                    if predicted_disease:
                        st.subheader("Prediction Result")
                        st.write(f"*Predicted Disease*: {predicted_disease}")

                        # Get disease details from the description dataset
                        description = disease_description_mapping.get(predicted_disease, {}).get('Description', 'No description available.')

                        st.write(f"*Description*: {description}")
                    else:
                        st.warning("No matching disease found.")
                else:
                    st.warning("Please select at least one symptom.")

if __name__ == "__main__":
    main()
