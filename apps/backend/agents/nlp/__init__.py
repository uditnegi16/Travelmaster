"""
NLP Module - Natural Language Understanding for TravelGuru

Provides intent extraction and query parsing capabilities for natural language queries.
"""

from agents.nlp.flight_intent_extractor import (
    FlightIntentExtractor,
    FlightIntent,
    ExtractedPreferences,
    extract_flight_intent,
)

__all__ = [
    "FlightIntentExtractor",
    "FlightIntent",
    "ExtractedPreferences",
    "extract_flight_intent",
]
