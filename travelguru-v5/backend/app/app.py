import streamlit as st
import sys
from pathlib import Path

# Add travelguru-v5 directory to path so backend.app.* imports work
travelguru_v5_dir = Path(__file__).resolve().parent.parent.parent
if str(travelguru_v5_dir) not in sys.path:
    sys.path.insert(0, str(travelguru_v5_dir))

from backend.app.agents.langgraph_agents.travel_planner_graph import generate_trip_plan
from backend.app.shared.schemas import TripRequest

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
max_price_per_night = st.sidebar.number_input(
    "Max Price per Night (₹)", 1000, 20000, 5000
)

st.sidebar.subheader("🚕 Cab Preferences")
vehicle_type = st.sidebar.selectbox(
    "Vehicle Type", ["Sedan", "SUV", "Luxury"]
)

plan_btn = st.sidebar.button("🚀 Plan My Trip")

# -------------------------------
# MAIN CONTENT
# -------------------------------
st.title("🌍 TravelGuru Trip Planner")

if plan_btn:
    # Build structured TripRequest for better accuracy (RECOMMENDED)
    # This bypasses natural language extraction issues and ensures exact dates/budget
    trip_request = TripRequest(
        from_city=from_city,
        to_city=to_city,
        start_date=str(start_date),  # Convert date object to string
        end_date=str(end_date),
        budget=budget,
        travelers=people,
        preferences={
            "star_category": star_category,
            "max_price_per_night": max_price_per_night,
            "prefer_direct_flights": prefer_direct,
            "vehicle_type": vehicle_type
        }
    )
    
    # Also build natural language query for display
    user_query = f"""
Plan a trip from {from_city} to {to_city}
from {start_date} to {end_date}
for {people} people
with a total budget of {budget} INR.
Prefer {star_category} star hotels with maximum {max_price_per_night} INR per night.
Prefer {'direct flights' if prefer_direct else 'any flights'}.
Vehicle preference: {vehicle_type}.
""".strip()

    # Show the query being sent to the AI
    with st.expander("📝 Trip Request Details"):
        st.text(user_query)
        st.json({
            "from_city": from_city,
            "to_city": to_city,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "budget": budget,
            "travelers": people
        })

    # Call the AI orchestrator with STRUCTURED request (more accurate than NL extraction)
    with st.spinner("🧠 Planning your trip using AI agents... This may take 1-2 minutes..."):
        try:
            result = generate_trip_plan(trip_request=trip_request)

            narrative = result["narrative"]
            trip_response = result["trip"]
            debug = result["debug"]

            st.success("✅ Trip planned successfully!")

            # Display the AI-generated narrative
            st.header("🧳 Your AI-Curated Trip Plan")
            st.markdown(narrative)

            # Optional: Display structured data
            with st.expander("📊 Structured Trip Data"):
                st.subheader("✈️ Selected Flight")
                if trip_response.trip_plan.flight:
                    flight = trip_response.trip_plan.flight
                    st.write(f"**{flight.airline}** - {flight.origin} → {flight.destination}")
                    st.write(f"**Price:** ₹{flight.price} {flight.currency}")
                    st.write(f"**Duration:** {flight.duration}")
                    st.write(f"**Departure:** {flight.departure_time}")
                    st.write(f"**Arrival:** {flight.arrival_time}")
                    st.write(f"**Stops:** {flight.stops}")
                    st.divider()
                else:
                    st.info("No flight selected")

                st.subheader("🏨 Selected Hotel")
                if trip_response.trip_plan.hotel:
                    hotel = trip_response.trip_plan.hotel
                    st.write(f"**{hotel.name}** ({hotel.stars}⭐)")
                    st.write(f"**Price per Night:** ₹{hotel.price_per_night}")
                    st.write(f"**Location:** {hotel.city}")
                    if hotel.check_in and hotel.check_out:
                        st.write(f"**Check-in:** {hotel.check_in} | **Check-out:** {hotel.check_out}")
                    if hotel.amenities:
                        st.write(f"**Amenities:** {', '.join(hotel.amenities)}")
                    st.divider()
                else:
                    st.info("No hotel selected")

                st.subheader("📅 Day-by-Day Itinerary")
                if trip_response.trip_plan.days:
                    for day_idx, day in enumerate(trip_response.trip_plan.days, 1):
                        st.write(f"### Day {day_idx} - {day.date}")
                        if day.activities:
                            for activity_idx, place in enumerate(day.activities, 1):
                                st.write(f"**{activity_idx}. {place.name}** - {place.category}")
                                st.write(f"   ⭐ Rating: {place.rating}/5.0")
                                if place.description:
                                    st.write(f"   📝 {place.description}")
                                if place.entry_fee > 0:
                                    st.write(f"   💰 Entry Fee: ₹{place.entry_fee}")
                                if place.opening_hours:
                                    st.write(f"   🕒 Hours: {place.opening_hours}")
                                if place.recommended_duration:
                                    st.write(f"   ⏱️ Duration: {place.recommended_duration}")
                        else:
                            st.info(f"No activities planned for Day {day_idx}")
                        st.divider()
                else:
                    st.info("No itinerary available")

                st.subheader("🌦 Weather Forecast")
                if trip_response.trip_plan.weather:
                    for idx, weather in enumerate(trip_response.trip_plan.weather, 1):
                        st.write(f"**{weather.date}:** {weather.temperature_c}°C - {weather.condition}")
                        st.write(f"   📍 {weather.city}")
                        st.divider()
                else:
                    st.info("No weather data available")

                st.subheader("💰 Budget Summary")
                if trip_response.budget_summary:
                    st.write(f"**Total Trip Cost:** ₹{trip_response.budget_summary.total_cost} {trip_response.budget_summary.currency}")
                    st.write(f"**Flights Cost:** ₹{trip_response.budget_summary.flights_cost}")
                    st.write(f"**Hotel Cost:** ₹{trip_response.budget_summary.hotel_cost}")
                    st.write(f"**Activities Cost:** ₹{trip_response.budget_summary.activities_cost}")
                    
                    # Show enrichment data if available
                    if trip_response.budget_summary.enrichment:
                        enrichment = trip_response.budget_summary.enrichment
                        st.divider()
                        st.write("**💡 Budget Intelligence:**")
                        
                        # Health Score
                        if enrichment.health_score:
                            st.write(f"**Health Score:** {enrichment.health_score.score}/10 - {enrichment.health_score.severity}")
                        
                        # Classification
                        if enrichment.classification:
                            st.write(f"**Trip Type:** {enrichment.classification.classification}")
                        
                        # Detailed breakdown
                        if enrichment.cost_breakdown:
                            breakdown = enrichment.cost_breakdown
                            st.write("\n**Detailed Cost Breakdown:**")
                            st.write(f"  - Flights: ₹{breakdown.flights}")
                            st.write(f"  - Hotel: ₹{breakdown.hotel}")
                            st.write(f"  - Activities: ₹{breakdown.activities}")
                            if breakdown.local_transport > 0:
                                st.write(f"  - Local Transport: ₹{breakdown.local_transport}")
                            if breakdown.food > 0:
                                st.write(f"  - Food: ₹{breakdown.food}")
                            if breakdown.buffer > 0:
                                st.write(f"  - Buffer: ₹{breakdown.buffer}")
                        
                        # Recommendations
                        if enrichment.recommendations:
                            st.write("\n**💡 Recommendations:**")
                            for rec in enrichment.recommendations[:3]:  # Show top 3
                                st.write(f"  - {rec.action} (Save: ₹{rec.savings})")
                else:
                    st.info("No budget data available")
                
                # Show additional notes if available
                if trip_response.trip_plan.notes:
                    st.subheader("📝 Additional Notes")
                    st.info(trip_response.trip_plan.notes)

            # Debug information
            with st.expander("🔍 Debug Info & Performance Metrics"):
                st.json(debug)

        except Exception as e:
            st.error(f"❌ Planning failed: {str(e)}")
            st.exception(e)
