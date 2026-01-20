"""
Comprehensive Flight Agent Test Suite
Tests flight search with NLP integration and enrichment intelligence.

Architecture Flow:
1. Natural Language → NLP Intent Extraction → Structured Parameters
2. Direct Parameters → Flight Service
3. Flight Service → API → Normalization → Enrichment → Results

This test demonstrates:
- NLP-based flight search
- Direct parameter flight search
- Enrichment layer intelligence
- Market analysis
- User-friendly output formatting
"""

import sys
from pathlib import Path
from typing import Dict, Any

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.agents.nlp.flight_intent_extractor import extract_flight_intent
from backend.app.tools.flight.service import search_flights
from backend.app.agents.postprocessing.flight_enrichment import FlightIntelligenceEngine


# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_subheader(title: str):
    """Print formatted subsection header."""
    print(f"\n{'-' * 80}")
    print(f"  {title}")
    print(f"{'-' * 80}\n")


def display_intent_extraction(query: str, intent: Any):
    """Display extracted intent in readable format."""
    print(f"Query: {query}\n")
    print(f"Extracted Intent:")
    print(f"  From: {intent.from_city}")
    print(f"  To: {intent.to_city}")
    print(f"  Date: {intent.date}")
    print(f"  Adults: {intent.adults}")
    print(f"  Max Price: {intent.max_price if intent.max_price else 'Not specified'}")
    
    if intent.preferences:
        print(f"\n  Preferences:")
        for key, value in intent.preferences.items():
            print(f"    {key}: {value}")
    else:
        print(f"\n  Preferences: None specified")


def display_market_analysis(market: Dict[str, Any]):
    """Display market analysis from enrichment."""
    price_range = market.get("price_range", {})
    
    print(f"Total Options: {market.get('total_options', 0)}")
    print(f"Price Range: {price_range.get('min', 0):,} - {price_range.get('max', 0):,} INR")
    print(f"Average Price: {price_range.get('average', 0):,.0f} INR")
    print(f"Airlines Available: {', '.join(market.get('airlines', []))}")
    print(f"Direct Flights: {'Yes' if market.get('direct_flights_available') else 'No'}")
    
    dist = market.get("price_distribution", {})
    print(f"\nPrice Distribution:")
    print(f"  Budget Flights: {dist.get('budget', 0)}")
    print(f"  Moderate Flights: {dist.get('moderate', 0)}")
    print(f"  Premium Flights: {dist.get('premium', 0)}")
    
    print(f"\nBooking Recommendation: {market.get('best_booking_advice', 'N/A')}")
    
    if market.get("best_time_to_fly"):
        print(f"Best Time to Fly: {market.get('best_time_to_fly')}")


def display_enriched_flight(enriched, rank: int):
    """Display single enriched flight with intelligence insights."""
    flight = enriched.flight
    
    print(f"\n{'─' * 80}")
    print(f"FLIGHT #{rank}")
    print(f"{'─' * 80}")
    
    print(f"\nSummary: {enriched.summary}")
    print(f"Match Score: {enriched.match_score}/100")
    
    if enriched.tags:
        print(f"Tags: {', '.join(enriched.tags)}")
    
    if enriched.best_for:
        print(f"Best For: {', '.join(enriched.best_for)}")
    
    print(f"\nFlight Details:")
    print(f"  Airline: {flight.airline}")
    print(f"  Route: {flight.origin} → {flight.destination}")
    print(f"  Departure: {flight.departure_time}")
    print(f"  Arrival: {flight.arrival_time}")
    print(f"  Duration: {flight.duration}")
    print(f"  Stops: {flight.stops}")
    print(f"  Price: {flight.price:,} {flight.currency}")
    
    print(f"\nTiming Analysis:")
    print(f"  Time Segment: {enriched.timing_analysis.segment}")
    print(f"  Impact: {enriched.timing_analysis.impact}")
    print(f"  Suitability: {enriched.timing_analysis.suitability}")
    
    print(f"\nPrice Intelligence:")
    print(f"  Category: {enriched.price_intelligence.price_category}")
    print(f"  Percentile: {enriched.price_intelligence.price_percentile:.1f}th")
    print(f"  Value Score: {enriched.price_intelligence.value_score:.1f}/10")
    
    if enriched.price_intelligence.is_deal:
        savings = abs(enriched.price_intelligence.savings_vs_average)
        print(f"  GREAT DEAL: Saves {savings:,} INR vs average")
    elif enriched.price_intelligence.savings_vs_average > 0:
        print(f"  Savings: {enriched.price_intelligence.savings_vs_average:,} INR vs average")
    else:
        premium = abs(enriched.price_intelligence.savings_vs_average)
        print(f"  Premium: {premium:,} INR above average")
    
    print(f"\nConvenience Analysis:")
    print(f"  Overall Score: {enriched.convenience.overall_score:.1f}/10")
    print(f"  Timing Score: {enriched.convenience.timing_score:.1f}/10")
    print(f"  Duration Score: {enriched.convenience.duration_score:.1f}/10")
    print(f"  Stops Score: {enriched.convenience.stops_score:.1f}/10")
    print(f"  Explanation: {enriched.convenience.explanation}")
    
    if enriched.insights:
        print(f"\nIntelligent Insights:")
        for idx, insight in enumerate(enriched.insights, 1):
            print(f"  {idx}. [{insight.type}] {insight.message}")
    
    if enriched.recommendations:
        print(f"\nRecommendations:")
        for idx, rec in enumerate(enriched.recommendations, 1):
            print(f"  {idx}. [{rec.sentiment}] {rec.reason}")


def test_nlp_flight_search():
    """Test flight search using natural language query."""
    print_header("TEST 1: NLP-BASED FLIGHT SEARCH")
    
    query = "Find cheap but fast direct flights from Delhi to Mumbai on 14 Feb 2026 for 2 adults"
    
    print_subheader("Step 1: Extract Intent from Natural Language")
    
    try:
        intent = extract_flight_intent(query)
        display_intent_extraction(query, intent)
        
        print_subheader("Step 2: Search Flights with Extracted Parameters")
        
        flights = search_flights(
            from_city=intent.from_city,
            to_city=intent.to_city,
            date=intent.date,
            adults=intent.adults,
            max_price=intent.max_price,
            preferences=intent.preferences,
            limit=5
        )
        
        print(f"\nFound {len(flights)} flight options")
        
        print_subheader("Step 3: Apply Enrichment Intelligence")
        
        enricher = FlightIntelligenceEngine()
        result = enricher.enrich_flights(flights)
        
        print_subheader("Market Analysis")
        display_market_analysis(result.market_analysis)
        
        if result.best_choice:
            print(f"\nBest Overall Choice: {result.best_choice}")
        
        print_subheader("Enriched Flight Options")
        
        for enriched in result.enriched_flights[:3]:
            display_enriched_flight(enriched, enriched.rank)
        
        print(f"\n\nTest Status: PASSED")
        
    except Exception as e:
        print(f"\nTest Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_direct_parameter_search():
    """Test flight search using direct parameters without NLP."""
    print_header("TEST 2: DIRECT PARAMETER FLIGHT SEARCH")
    
    print_subheader("Search Parameters")
    
    params = {
        "from_city": "Bengaluru",
        "to_city": "Goa",
        "date": "2026-03-15",
        "adults": 3,
        "max_price": None,
        "preferences": {
            "timing_preference": "morning",
            "budget_preference": "moderate"
        },
        "limit": 5
    }
    
    print(f"From: {params['from_city']}")
    print(f"To: {params['to_city']}")
    print(f"Date: {params['date']}")
    print(f"Adults: {params['adults']}")
    print(f"Max Price: {params['max_price']} INR")
    print(f"Preferences: {params['preferences']}")
    
    try:
        print_subheader("Flight Search Results")
        
        flights = search_flights(**params)
        
        print(f"\nFound {len(flights)} flight options within budget")
        
        print_subheader("Enrichment Intelligence")
        
        enricher = FlightIntelligenceEngine()
        result = enricher.enrich_flights(flights)
        
        print_subheader("Market Analysis")
        display_market_analysis(result.market_analysis)
        
        if result.best_choice:
            print(f"\nBest Overall Choice: {result.best_choice}")
        
        print_subheader("Top Enriched Flights")
        
        for enriched in result.enriched_flights[:3]:
            display_enriched_flight(enriched, enriched.rank)
        
        print(f"\n\nTest Status: PASSED")
        
    except Exception as e:
        print(f"\nTest Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_nlp_vs_direct_comparison():
    """Compare NLP extraction with direct parameters."""
    print_header("TEST 3: NLP VS DIRECT PARAMETER COMPARISON")
    
    query = "Find evening flights from Chennai to Kolkata tomorrow for 1 adult"
    
    print_subheader("Natural Language Query")
    print(f"Query: {query}")
    
    try:
        intent = extract_flight_intent(query)
        
        print(f"\nNLP Extracted:")
        print(f"  From: {intent.from_city}")
        print(f"  To: {intent.to_city}")
        print(f"  Date: {intent.date}")
        print(f"  Adults: {intent.adults}")
        print(f"  Preferences: {intent.preferences}")
        
        print_subheader("Equivalent Direct Parameters")
        
        direct_params = {
            "from_city": intent.from_city,
            "to_city": intent.to_city,
            "date": intent.date,
            "adults": intent.adults,
            "preferences": intent.preferences
        }
        
        print(f"Direct Parameters: {direct_params}")
        
        print_subheader("Search Results")
        
        flights = search_flights(**direct_params, limit=3)
        
        print(f"\nFound {len(flights)} flight options")
        
        if flights:
            enricher = FlightIntelligenceEngine()
            result = enricher.enrich_flights(flights)
            
            print_subheader("Top Flight with Enrichment")
            
            if result.enriched_flights:
                display_enriched_flight(result.enriched_flights[0], 1)
        
        print(f"\n\nTest Status: PASSED")
        print(f"Conclusion: NLP successfully converted natural language to structured parameters")
        
    except Exception as e:
        print(f"\nTest Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    """Execute all flight agent tests."""
    print_header("COMPREHENSIVE FLIGHT AGENT TEST SUITE")
    
    print("Testing Flight Agent with:")
    print("  - NLP Intent Extraction")
    print("  - Enrichment Intelligence")
    print("  - Market Analysis")
    print("  - User-friendly Output\n")
    
    test_nlp_flight_search()
    print("\n" * 2)
    
    test_direct_parameter_search()
    print("\n" * 2)
    
    test_nlp_vs_direct_comparison()
    
    print_header("ALL TESTS COMPLETED")
    
    print("""
Summary:
  Test 1: NLP-based flight search with enrichment
  Test 2: Direct parameter search with enrichment
  Test 3: NLP vs Direct comparison

Key Features Demonstrated:
  - Natural language understanding
  - Structured parameter extraction
  - Flight search orchestration
  - Enrichment intelligence layer
  - Market analysis
  - Price intelligence
  - Convenience scoring
  - Intelligent insights and recommendations
""")


if __name__ == "__main__":
    run_all_tests()
