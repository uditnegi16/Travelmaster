import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="TravelGuru Planner", layout="wide")
st.sidebar.title("🧳 Plan Your Trip")

from_city = st.sidebar.text_input("From City", "Delhi")
to_city = st.sidebar.text_input("To City", "Goa")

start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

budget = st.sidebar.number_input("Total Budget (₹)", 5000, 1000000, 20000)
travelers = st.sidebar.number_input("Number of People", 1, 10, 2)

st.sidebar.subheader("✈️ Flight Preferences")
prefer_direct = st.sidebar.checkbox("Prefer Direct Flights", True)

st.sidebar.subheader("🏨 Hotel Preferences")
star_category = st.sidebar.selectbox("Preferred Star Category", [3, 4, 5])

plan_btn = st.sidebar.button("🚀 Plan My Trip")

st.title("🌍 TravelGuru Trip Planner")

if plan_btn:
    payload = {
        "user_input": {
            "origin": from_city,
            "destination": to_city,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "budget": budget,
            "preferences": {
                "prefer_direct": prefer_direct,
                "preferred_star_category": star_category,
            }
        },
        "top_k_flights": 3,
        "top_k_hotels": 3
    }

    with st.spinner("🤖 Planning your trip..."):
        resp = requests.post("http://localhost:8000/plan-trip", json=payload)

        if resp.status_code != 200:
            st.error(f"❌ Failed to plan trip: {resp.text}")
            st.stop()

        data = resp.json()

    st.success("Trip planned successfully!")

    st.header("✈️ Flights")
    st.dataframe(pd.DataFrame(data.get("flights", [])), use_container_width=True)

    st.header("🏨 Hotels")
    st.dataframe(pd.DataFrame(data.get("hotels", [])), use_container_width=True)

    # ❌ REMOVE CABS (agent doesn't return them)
    # st.header("🚕 Cabs") ...

    st.header("📍 Places to Visit")
    places = data.get("places", [])
    st.dataframe(pd.DataFrame(places), use_container_width=True) if places else st.info("No places returned")

    st.header("🌦 Weather")
    st.dataframe(pd.DataFrame(data.get("weather", [])), use_container_width=True)

    st.header("💰 Budget")
    st.json(data.get("budget", {}))

    st.header("📝 Narrative")
    st.write(data.get("narrative", ""))

