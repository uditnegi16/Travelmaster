"""
Comprehensive Places Agent Test Suite
Tests places search with NLP, enrichment, and knowledge intelligence.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1] / "travelguru-v5" / "backend"
sys.path.insert(0, str(project_root))

from app.agents.nlp.places_intent_extractor import extract_places_intent
from app.agents.langgraph_agents.tools.places.service import search_places
from app.agents.postprocessing.places_enrichment import enrich_places

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_header(title: str):
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_subheader(title: str):
    print(f"\n{'-' * 80}")
    print(f"  {title}")
    print(f"{'-' * 80}\n")


def display_intent(query: str, intent):
    """Display extracted NLP intent."""
    print(f"Query: {query}\n")
    print(f"Extracted Intent:")
    print(f"  City: {intent.city}")
    print(f"  Categories: {intent.categories if intent.categories else 'All'}")
    print(f"  Max Entry Fee: {intent.max_entry_fee if intent.max_entry_fee is not None else 'No limit'}")
    print(f"  Min Rating: {intent.min_rating if intent.min_rating is not None else 'Default 4.0'}")
    print(f"  Radius: {intent.radius_km} km")
    print(f"  Limit: {intent.limit}")
    if intent.preferences:
        print(f"  Preferences: {intent.preferences}")


def display_place_enriched(enriched, rank):
    """Display place with full enrichment intelligence."""
    place = enriched.place
    ctx = enriched.contextual_info
    timing = enriched.timing_intelligence
    audience = enriched.audience_suitability
    weather = enriched.weather_crowd_analysis
    priority = enriched.priority_assessment
    practical = enriched.practical_details
    effort = enriched.effort_reward_balance
    accessibility = enriched.accessibility_info
    day_plan = enriched.day_plan_fit
    
    print(f"\n{'=' * 80}")
    print(f"RANK #{rank}: {place.name}")
    print(f"{'=' * 80}")
    print(f"Match Score: {enriched.match_score:.1f}/100 | {enriched.one_line_verdict}")
    
    print(f"\nWHAT IT IS:")
    print(f"  {ctx.short_summary}")
    print(f"  {ctx.detailed_description}")
    
    if ctx.famous_for:
        print(f"\nWHY IT'S FAMOUS:")
        for item in ctx.famous_for:
            print(f"  - {item}")
    
    print(f"\nBEST TIME TO VISIT:")
    print(f"  Time of Day: {timing.best_time_of_day}")
    print(f"  Duration: {timing.recommended_duration}")
    print(f"  Reasoning: {timing.reasoning}")
    if timing.time_to_avoid:
        print(f"  Avoid: {timing.time_to_avoid}")
    if timing.opening_hours:
        print(f"  Hours: {timing.opening_hours}")
    
    print(f"\nWHO SHOULD GO:")
    print(f"  Couples: {audience.couples['verdict']} ({audience.couples['score']}/10) - {audience.couples['reason']}")
    print(f"  Families: {audience.families['verdict']} ({audience.families['score']}/10) - {audience.families['reason']}")
    print(f"  Kids: {audience.kids['verdict']} ({audience.kids['score']}/10) - {audience.kids['reason']}")
    print(f"  Solo: {audience.solo_travelers['verdict']} ({audience.solo_travelers['score']}/10) - {audience.solo_travelers['reason']}")
    print(f"  Elderly: {audience.elderly['verdict']} ({audience.elderly['score']}/10) - {audience.elderly['reason']}")
    
    if ctx.what_makes_special:
        print(f"\nWHAT MAKES IT SPECIAL:")
        print(f"  {ctx.what_makes_special}")
    
    if enriched.insights:
        print(f"\nTIPS & WARNINGS:")
        for insight in enriched.insights:
            symbol = "!" if insight.type == "warning" else "i" if insight.type == "tip" else "+"
            print(f"  [{symbol}] {insight.message}")
    
    print(f"\nWEATHER & CROWD ADVICE:")
    print(f"  Weather: {weather.weather_dependency} ({weather.weather_sensitivity} sensitivity)")
    print(f"  Crowd: {weather.crowd_level} - {weather.crowd_type}")
    print(f"  Ambiance: {', '.join(weather.ambiance)}")
    
    # ========== NEW: KEY PLANNING INSIGHTS ==========
    print(f"\n{'-' * 40}")
    print(f"QUICK PLANNING GUIDE")
    print(f"{'-' * 40}")
    
    # 1. How long should I spend here?
    print(f"\nDURATION:")
    print(f"  How long: {timing.recommended_duration}")
    
    # 2. How to reach?
    print(f"\nHOW TO REACH:")
    print(f"  Best way: {accessibility.recommended_transport}")
    print(f"  Options: {', '.join(accessibility.transport_modes)}")
    if accessibility.estimated_travel_time:
        print(f"  Travel time: {accessibility.estimated_travel_time}")
    
    # 3. Where does it fit in the day plan?
    print(f"\nDAY PLAN FIT:")
    print(f"  Position: {day_plan.position_in_day}")
    print(f"  Location: {day_plan.distance_category}")
    print(f"  Tip: {day_plan.sequence_recommendation}")
    if day_plan.can_combine_with:
        print(f"  Combine with: {', '.join(day_plan.can_combine_with[:3])}")
    
    # 4. Weather sensitivity?
    print(f"\nWEATHER SENSITIVITY:")
    print(f"  Type: {weather.weather_dependency}")
    print(f"  Sensitivity: {weather.weather_sensitivity}")
    
    # 5. Crowd analysis
    print(f"\nCROWD ANALYSIS:")
    print(f"  Level: {weather.crowd_level}")
    print(f"  Type: {weather.crowd_type}")
    print(f"  Vibe: {', '.join(weather.ambiance)}")
    
    # 6. Is it skippable or must-visit?
    print(f"\nPRIORITY:")
    print(f"  Rating: {priority.priority_level} ({priority.priority_score:.1f}/10)")
    if priority.must_visit_because:
        print(f"  Why must-visit: {priority.must_visit_because}")
    if priority.skip_if:
        print(f"  Can skip if: {', '.join(priority.skip_if)}")
    
    # 7. Open/Close timing
    print(f"\nOPERATING HOURS:")
    if timing.opening_hours:
        print(f"  Hours: {timing.opening_hours}")
    else:
        if timing.opening_time and timing.closing_time:
            print(f"  Hours: {timing.opening_time} - {timing.closing_time}")
        elif timing.opening_time:
            print(f"  Opens: {timing.opening_time}")
        elif timing.closing_time:
            print(f"  Closes: {timing.closing_time}")
        else:
            print(f"  Hours: Not specified")
    if timing.closed_on:
        print(f"  Closed: {timing.closed_on}")
    if timing.peak_hours:
        print(f"  Peak hours: {timing.peak_hours}")
    
    print(f"{'-' * 40}\n")
    
    if ctx.historical_significance or ctx.cultural_significance:
        print(f"\nCULTURAL/HISTORICAL CONTEXT:")
        if ctx.historical_significance:
            print(f"  History: {ctx.historical_significance}")
        if ctx.cultural_significance:
            print(f"  Culture: {ctx.cultural_significance}")
    
    print(f"\nPRACTICAL INFO:")
    print(f"  Entry Fee: INR {practical.entry_fee:,}")
    print(f"  Queue: {practical.queue_situation}")
    if practical.dress_code:
        print(f"  Dress Code: {practical.dress_code}")
    if practical.restrictions:
        print(f"  Restrictions: {', '.join(practical.restrictions)}")
    
    print(f"\nEFFORT vs REWARD:")
    print(f"  Effort: {effort.effort_level} | Reward: {effort.reward_level}")
    print(f"  Worth It: {'Yes' if effort.worth_it else 'No'} - {effort.reasoning}")
    
    if enriched.tags:
        print(f"\nTAGS: {', '.join(enriched.tags)}")


def test_nlp_parameters():
    """TEST 1: NLP-based search with natural language query."""
    print_header("TEST 1: NLP PARAMETERS")
    
    query = "Show me top-rated attractions in Paris suitable for families with kids, preferably outdoor places with low entry fees."
    
    try:
        intent = extract_places_intent(query)
        display_intent(query, intent)
        
        print_subheader("SEARCH RESULTS")
        
        places = search_places(query=query, limit=3)
        
        if not places:
            print("No places found.")
            print("\nTest Status: PASSED (No results)")
            return
        
        enrichment_result = enrich_places(places, intent.preferences)
        
        print(f"Found {len(enrichment_result.enriched_places)} places with full enrichment intelligence\n")
        
        for enriched in enrichment_result.enriched_places:
            display_place_enriched(enriched, enriched.rank)
        
        print(f"\n\nTest Status: PASSED")
        
    except Exception as e:
        print(f"\n\nTest Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_direct_parameters():
    """TEST 2: Direct parameter search without NLP."""
    print_header("TEST 2: DIRECT PARAMETERS")
    
    print(f"Search Parameters:")
    print(f"  City: Goa")
    print(f"  Max Entry Fee: 1000 INR")
    print(f"  Min Rating: 4.0")
    print(f"  Radius: 20 km")
    print(f"  Limit: 3")
    
    try:
        print_subheader("SEARCH RESULTS")
        
        places = search_places(
            city="Goa",
            max_entry_fee=1000,
            min_rating=4.0,
            radius_km=20,
            limit=3
        )
        
        if not places:
            print("No places found.")
            print("\nTest Status: PASSED (No results)")
            return
        
        enrichment_result = enrich_places(places)
        
        print(f"Found {len(enrichment_result.enriched_places)} places with full enrichment intelligence\n")
        
        for enriched in enrichment_result.enriched_places:
            display_place_enriched(enriched, enriched.rank)
        
        print(f"\n\nTest Status: PASSED")
        
    except Exception as e:
        print(f"\n\nTest Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_nlp_vs_direct():
    """TEST 3: Compare NLP extraction vs Direct parameters."""
    print_header("TEST 3: NLP VS DIRECT PARAMETERS")
    
    query = "Show me budget-friendly tourist attractions in Goa"
    
    try:
        intent = extract_places_intent(query)
        
        print_subheader("NLP EXTRACTION")
        display_intent(query, intent)
        
        print_subheader("DIRECT EQUIVALENT")
        print(f"City: {intent.city}")
        print(f"Categories: {intent.categories if intent.categories else 'All'}")
        print(f"Max Entry Fee: {intent.max_entry_fee if intent.max_entry_fee is not None else 'No limit'}")
        print(f"Min Rating: {intent.min_rating if intent.min_rating is not None else 'Default 4.0'}")
        print(f"Preferences: {intent.preferences if intent.preferences else 'None'}")
        
        print_subheader("NLP SEARCH RESULTS")
        
        nlp_places = search_places(query=query, limit=3)
        
        if nlp_places:
            nlp_enrichment = enrich_places(nlp_places, intent.preferences)
            print(f"Found {len(nlp_enrichment.enriched_places)} places via NLP with full enrichment\n")
            for enriched in nlp_enrichment.enriched_places:
                display_place_enriched(enriched, enriched.rank)
        else:
            print("No places found via NLP")
        
        print_subheader("COMPARISON SUMMARY")
        print(f"NLP returned {len(nlp_places)} fully enriched results")
        print(f"Each result includes: contextual info, timing intelligence, audience suitability,")
        print(f"weather/crowd analysis, cultural context, tips & warnings, and priority assessment")
        
        print(f"\n\nTest Status: PASSED")
        
    except Exception as e:
        print(f"\n\nTest Status: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_nlp_parameters()
    test_direct_parameters()
    test_nlp_vs_direct()
    
    print_header("ALL TESTS COMPLETED")
