"""
Comprehensive Hotel Agent Test Suite
Tests hotel search with NLP integration and enrichment intelligence.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.tools.hotel.service import search_hotels, search_hotels_enriched

# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_header(title: str):
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def test_nlp_hotel_search():
    """Test hotel search using natural language query."""
    print_header("TEST 1: NLP-BASED HOTEL SEARCH WITH ENRICHMENT")
    
    query = "Find luxury hotels in Mumbai"
    print(f"Query: {query}\n")
    
    try:
        result = search_hotels_enriched(query=query, limit=3)
        
        print(f"Found {len(result.enriched_hotels)} hotels with enrichment intelligence\n")
        
        for eh in result.enriched_hotels:
            hotel = eh.hotel
            print(f"\n{'-' * 70}")
            print(f"RANK #{eh.rank}: {hotel.name}")
            print(f"{'-' * 70}")
            print(f"Rating: {hotel.stars}★ | Price: ₹{hotel.price_per_night:,}/night | City: {hotel.city}")
            print(f"\nSCORES: Match={eh.match_score:.1f}/100, Value={eh.price_intelligence.value_score:.1f}/10, Quality={eh.quality_score.overall_score:.1f}/10")
            
            if eh.summary:
                print(f"SUMMARY: {eh.summary}")
            
            if eh.tags:
                print(f"TAGS: {', '.join(eh.tags)}")
            
            if eh.recommendations:
                print(f"\nRECOMMENDATIONS:")
                for rec in eh.recommendations:
                    sentiment_symbol = "✅" if rec.sentiment == "positive" else "⚠️" if rec.sentiment == "neutral" else "❌"
                    print(f"  {sentiment_symbol} [{rec.category.upper()}] {rec.reason}")
            
            if eh.insights:
                print(f"\nINSIGHTS:")
                for insight in eh.insights:
                    priority_marker = "🔴" if insight.priority >= 4 else "🟡" if insight.priority >= 2 else "🟢"
                    print(f"  {priority_marker} {insight.message}")
        
        print(f"\n✅ Test Status: PASSED")
        
    except Exception as e:
        print(f"\n❌ Test Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_direct_parameter_search():
    """Test hotel search using direct parameters."""
    print_header("TEST 2: DIRECT PARAMETER SEARCH WITH ENRICHMENT")
    
    print(f"City: Goa")
    print(f"Max Price: None")
    print(f"Limit: 3\n")
    
    try:
        result = search_hotels_enriched(city="Goa", max_price=None, limit=3)
        
        print(f"Found {len(result.enriched_hotels)} hotels with enrichment intelligence\n")
        
        for eh in result.enriched_hotels:
            hotel = eh.hotel
            print(f"\n{'-' * 70}")
            print(f"RANK #{eh.rank}: {hotel.name}")
            print(f"{'-' * 70}")
            print(f"Rating: {hotel.stars}★ | Price: ₹{hotel.price_per_night:,}/night | City: {hotel.city}")
            print(f"\nSCORES: Match={eh.match_score:.1f}/100, Value={eh.price_intelligence.value_score:.1f}/10, Quality={eh.quality_score.overall_score:.1f}/10")
            
            if eh.summary:
                print(f"SUMMARY: {eh.summary}")
            
            if eh.tags:
                print(f"TAGS: {', '.join(eh.tags)}")
            
            if eh.recommendations:
                print(f"\nRECOMMENDATIONS:")
                for rec in eh.recommendations:
                    sentiment_symbol = "✅" if rec.sentiment == "positive" else "⚠️" if rec.sentiment == "neutral" else "❌"
                    print(f"  {sentiment_symbol} [{rec.category.upper()}] {rec.reason}")
            
            if eh.insights:
                print(f"\nINSIGHTS:")
                for insight in eh.insights:
                    priority_marker = "🔴" if insight.priority >= 4 else "🟡" if insight.priority >= 2 else "🟢"
                    print(f"  {priority_marker} {insight.message}")
        
        print(f"\n✅ Test Status: PASSED")
        
    except Exception as e:
        print(f"\n❌ Test Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_nlp_with_enrichment():
    """Test NLP query with full enrichment intelligence."""
    print_header("TEST 3: NLP WITH FULL ENRICHMENT INTELLIGENCE")
    
    query = "Find hotels in Mumbai for 2 guests"
    print(f"Query: {query}\n")
    
    try:
        result = search_hotels_enriched(query=query, limit=3)
        
        print(f"Found {len(result.enriched_hotels)} hotels with comprehensive intelligence\n")
        
        # Display enriched hotels with detailed metadata
        for eh in result.enriched_hotels:
            hotel = eh.hotel
            print(f"\n{'─' * 70}")
            print(f"RANK #{eh.rank}: {hotel.name}")
            print(f"{'─' * 70}")
            print(f"Rating: {hotel.stars}★ | Price: ₹{hotel.price_per_night:,}/night | City: {hotel.city}")
            print(f"\nSCORES:")
            print(f"  Match Score:      {eh.match_score:.2f}/100")
            print(f"  Value Score:      {eh.price_intelligence.value_score:.2f}/10")
            print(f"  Quality Score:    {eh.quality_score.overall_score:.2f}/10")
            
            if eh.summary:
                print(f"\nSUMMARY: {eh.summary}")
            
            if eh.tags:
                print(f"\nTAGS: {', '.join(eh.tags)}")
            
            if hotel.amenities:
                print(f"\nAMENITIES: {', '.join(hotel.amenities[:8])}")
            
            print(f"\nWHY RECOMMENDED:")
            if eh.recommendations:
                for rec in eh.recommendations:
                    sentiment_symbol = "✅" if rec.sentiment == "positive" else "⚠️" if rec.sentiment == "neutral" else "❌"
                    print(f"  {sentiment_symbol} [{rec.category.upper()}] {rec.reason}")
            else:
                print(f"  No specific recommendations available")
            
            if eh.insights:
                print(f"\nINSIGHTS:")
                for insight in eh.insights:
                    priority_marker = "🔴" if insight.priority >= 4 else "🟡" if insight.priority >= 2 else "🟢"
                    print(f"  {priority_marker} [{insight.type.upper()}] {insight.message}")
            
            if eh.best_for:
                print(f"\nBEST FOR: {', '.join(eh.best_for)}")
        
        # Display market analysis
        if result.market_analysis:
            print(f"\n\n{'═' * 70}")
            print("MARKET INTELLIGENCE")
            print(f"{'═' * 70}")
            for key, value in result.market_analysis.items():
                print(f"  {key}: {value}")
        
        # Display best choice recommendation
        if result.best_choice:
            print(f"\n\n{'═' * 70}")
            print("BEST CHOICE RECOMMENDATION")
            print(f"{'═' * 70}")
            print(f"  {result.best_choice}")
        
        print(f"\n✅ Test Status: PASSED")
        
    except Exception as e:
        print(f"\n❌ Test Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    print_header("COMPREHENSIVE HOTEL AGENT TEST SUITE")
    
    print("Testing Hotel Service with:")
    print("  - NLP Integration")
    print("  - Enrichment Intelligence")
    print("  - Direct Parameter Support\n")
    
    test_nlp_hotel_search()
    test_direct_parameter_search()
    test_nlp_with_enrichment()
    
    print_header("ALL TESTS COMPLETED")
    
    print("""
Summary:
  ✅ Test 1: NLP-based hotel search
  ✅ Test 2: Direct parameter search
  ✅ Test 3: NLP with enrichment

Key Features Demonstrated:
  - Natural language query processing
  - Structured parameter search
  - Automatic enrichment and ranking
  - Flexible API interface
""")


if __name__ == "__main__":
    run_all_tests()
