from chatbot.state import ConversationState
from chatbot.prompts import PROMPTS
from contracts.trip_input_schema import TripInput

class ChatOrchestrator:

    def __init__(self):
        self.state = ConversationState()

    def handle_message(self, user_message: str):
        s = self.state

        if s.step == "greeting":
            s.origin = user_message
            s.step = "destination"
            return PROMPTS["destination"]

        if s.step == "destination":
            s.destination = user_message
            s.hotel_city = user_message
            s.step = "departure_date"
            return PROMPTS["departure_date"]

        if s.step == "departure_date":
            s.departure_date = user_message
            s.step = "flight_pref"
            return PROMPTS["flight_pref"]

        if s.step == "flight_pref":
            s.flight_preference = user_message.lower()
            s.step = "hotel"
            return PROMPTS["hotel"]

        if s.step == "hotel":
            # Expected: "3 stars, 4000"
            parts = user_message.split(",")
            s.preferred_star_category = int(parts[0].strip()[0])
            s.max_price_per_night = float(parts[1].strip())
            s.step = "cab"
            return PROMPTS["cab"]

        if s.step == "cab":
            # Expected: "Airport to Hotel"
            pickup, drop = user_message.split("to")
            s.pickup_location = pickup.strip()
            s.drop_location = drop.strip()
            s.step = "budget"
            return PROMPTS["budget"]

        if s.step == "budget":
            s.budget = float(user_message)
            s.step = "confirm"
            return PROMPTS["confirm"]

        if s.step == "confirm":
            if user_message.lower() == "yes":
                return self.build_trip_input()
            else:
                return "Okay, let me know when you’re ready!"

    def build_trip_input(self):
        return TripInput(
            origin=self.state.origin,
            destination=self.state.destination,
            departure_date=self.state.departure_date,
            max_stops=2,
            flight_preference=self.state.flight_preference,
            hotel_city=self.state.hotel_city,
            preferred_star_category=self.state.preferred_star_category,
            max_price_per_night=self.state.max_price_per_night,
            pickup_location=self.state.pickup_location,
            drop_location=self.state.drop_location,
            budget=self.state.budget,
            top_k=self.state.top_k,
        )
