"""
Test Composer Output - Verify comprehensive 6000-9000 word generation
"""

import sys
import codecs
from pathlib import Path

# Fix UTF-8 encoding for Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.app.agents.langgraph_agents.travel_planner_graph import TravelPlannerOrchestrator


def test_composer_comprehensive_output():
    """Test that composer generates comprehensive 6000-9000 word output"""
    
    print("="*100)
    print(" >> TESTING COMPOSER COMPREHENSIVE OUTPUT GENERATION")
    print("="*100)
    print()
    
    # User query for 5-day trip
    user_query = "Create a 5 day romantic plan for 2 adults from 12 Feb 2026 from Delhi to Goa"
    
    print(f"User Query: {user_query}")
    print()
    print("Executing travel planning orchestration...")
    print("(This will call: Planner -> Services -> Enrichers -> Itinerary Builder -> Composer)")
    print()
    
    try:
        # Execute full orchestration
        orchestrator = TravelPlannerOrchestrator()
        result = orchestrator.plan_trip_from_text(user_query)
        
        # Extract data
        trip_response = result.get("trip")
        narrative = result.get("narrative")
        debug = result.get("debug", {})
        
        # Display timings
        print("-" * 100)
        print("ORCHESTRATION TIMINGS:")
        print("-" * 100)
        timings = debug.get("timings", {})
        for agent, duration in timings.items():
            print(f"  {agent:20s}: {duration:6.2f}s")
        print()
        
        # Display enrichment data availability
        print("-" * 100)
        print("ENRICHMENT DATA AVAILABLE:")
        print("-" * 100)
        enriched = debug.get("enriched", {})
        for key in ["flights", "hotels", "places", "weather", "budget"]:
            status = "YES" if enriched.get(key) else "NO"
            print(f"  {key:20s}: {status}")
        print()
        
        # Display narrative
        print("=" * 100)
        print(" >> COMPOSER-GENERATED NARRATIVE OUTPUT")
        print("=" * 100)
        print()
        
        if narrative:
            # Display the narrative
            print(narrative)
            print()
            
            # Count words
            word_count = len(narrative.split())
            char_count = len(narrative)
            
            print()
            print("=" * 100)
            print(" >> OUTPUT METRICS")
            print("=" * 100)
            print(f"  Total Words:      {word_count:,}")
            print(f"  Total Characters: {char_count:,}")
            print(f"  Target Range:     6,000 - 9,000 words (for 5-day trip)")
            print()
            
            # Evaluation
            if word_count >= 6000 and word_count <= 9000:
                print("  STATUS: ✓ PASS - Output meets comprehensive word budget")
            elif word_count >= 3000:
                print(f"  STATUS: ~ PARTIAL - Output is {word_count} words (needs {6000-word_count} more)")
            else:
                print(f"  STATUS: X FAIL - Output is only {word_count} words (needs {6000-word_count} more)")
            
            print("=" * 100)
            
        else:
            print("  ERROR: No narrative generated!")
            print()
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_composer_comprehensive_output()
