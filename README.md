# **LifeLine: Emergency Response and AI Disease Prediction System**

#### **Overview**
LifeLine is a comprehensive web application built using Streamlit, designed to streamline emergency medical services and assist in disease prediction. The system integrates features for real-time ambulance allocation, optimized hospital routing, and symptom-based AI disease prediction, ensuring faster and more efficient healthcare responses.

---

#### **Key Features**
1. **Emergency Response System**:
   - **Find Nearest Ambulance**: Dynamically locate the closest ambulance to the patient using geospatial analysis.
   - **Optimized Route Navigation**: Fetch the fastest route from the patient's location to the nearest hospital or ambulance.
   - **Traffic Signal Simulation**: Incorporate simulated traffic signals along the route, displaying travel times and delays.
   - **Hospital Specialization**: Search for hospitals based on required specialization (e.g., cardiology, neurology, pulmonology).

2. **AI Disease Prediction System**:
   - Predict the most probable disease based on user-selected symptoms.
   - Provide detailed descriptions of diseases using a preloaded dataset.
   - Handle multiple symptoms efficiently with a symptom-to-disease matching algorithm.

3. **User Authentication**:
   - Register and log in to access services.
   - Securely store user session data during the application runtime.

4. **Interactive Map Visualizations**:
   - Display ambulance and hospital locations using Folium maps.
   - Highlight optimized routes and traffic signals for better user understanding.

---

#### **Technologies Used**
- **Python**: Core logic implementation.
- **Streamlit**: Web application framework for interactive user interfaces.
- **Folium**: For map rendering and visualization.
- **Geopy**: Geocoding and distance calculations.
- **OpenRouteService API**: For route optimization and directions.
- **Overpass API**: For real-time hospital and traffic signal data.

---

#### **How It Works**
1. **Emergency Response Workflow**:
   - Input the patient's location and desired hospital specialization.
   - The system geocodes the location, finds the nearest hospital or ambulance, and calculates the fastest route.
   - Simulated traffic signals are displayed along the route to visualize travel delays.

2. **Disease Prediction Workflow**:
   - Select up to 4 symptoms from a predefined list.
   - The system matches the input symptoms with known diseases in the dataset.
   - Displays the predicted disease and provides its description.

---

#### **Installation and Usage**
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lifeline.git
   ```
2. Navigate to the project directory:
   ```bash
   cd lifeline
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```
5. Access the application at `http://localhost:8501`.

---

#### **Future Enhancements**
- Integrate real-time traffic data for more accurate travel time estimation.
- Expand the disease prediction system using machine learning models.
- Implement GPS-based live ambulance tracking.
- Enhance scalability to include multiple cities.
