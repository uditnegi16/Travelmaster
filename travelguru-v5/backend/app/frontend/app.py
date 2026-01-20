import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="TravelGuru Planner",
    layout="wide"
)

# -------------------------------
# SIDEBAR — USER INPUT
# -------------------------------
st.sidebar.title("🧳 Plan Your Trip")

from_city = st.sidebar.text_input("From City", "Delhi")
to_city = st.sidebar.text_input("To City", "Goa")

start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

budget = st.sidebar.number_input("Total Budget (₹)", 5000, 200000, 20000)
people = st.sidebar.number_input("Number of People", 1, 10, 2)

st.sidebar.subheader("✈️ Flight Preferences")
prefer_direct = st.sidebar.checkbox("Prefer Direct Flights", True)

st.sidebar.subheader("🏨 Hotel Preferences")
star_category = st.sidebar.selectbox("Preferred Star Category", [3, 4, 5])

plan_btn = st.sidebar.button("🚀 Plan My Trip")

# -------------------------------
# MAIN CONTENT
# -------------------------------
st.title("🌍 TravelGuru Trip Planner")

if plan_btn:

    payload = {
        "user_input": {
            "origin": from_city,
            "destination": to_city,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "budget": budget,
            "people": people,
            "prefer_direct": prefer_direct,
            "preferred_star_category": star_category
        },
        "top_k_flights": 3,
        "top_k_hotels": 3
    }

    with st.spinner("🤖 Talking to travel agent..."):
        res = requests.post(
            f"{API_BASE}/plan-trip",
            json=payload
        )

    if res.status_code != 200:
        st.error("❌ Failed to plan trip")
        st.stop()

    data = res.json()

    # -------------------------------
    # FLIGHTS
    # -------------------------------
    st.header("✈️ Flights")

    flights = pd.DataFrame(data["recommended"]["flights"])

    st.subheader("⭐ Recommended Flights")
    st.dataframe(flights[flights["recommended"] == True])

    st.subheader("Other Options")
    st.dataframe(flights[flights["recommended"] == False])

    # -------------------------------
    # HOTELS
    # -------------------------------
    st.header("🏨 Hotels")

    hotels = pd.DataFrame(data["recommended"]["hotels"])

    st.subheader("⭐ Recommended Hotels")
    st.dataframe(hotels[hotels["recommended"] == True])

    st.subheader("Other Options")
    st.dataframe(hotels[hotels["recommended"] == False])

    # -------------------------------
    # PLACES (AGENT ONLY)
    # -------------------------------
    st.header("📍 Places to Visit")

    places = data["others"].get("places", [])
    if places:
        st.dataframe(pd.DataFrame(places))
    else:
        st.info("No places data returned by agent")

    # -------------------------------
    # WEATHER (AGENT ONLY)
    # -------------------------------
    st.header("🌦 Weather Forecast")

    weather = data["others"].get("weather", {})
    if weather:
        st.json(weather)
    else:
        st.info("No weather data returned by agent")
