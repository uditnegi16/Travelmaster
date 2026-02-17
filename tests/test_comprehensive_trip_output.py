"""
Comprehensive Trip Planning Test
Executes a full trip planning workflow and saves the complete output to a markdown file.
"""

import sys
import codecs
from pathlib import Path
from datetime import datetime

# Fix UTF-8 encoding for Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')

# Add project root to path
project_root = Path(__file__).resolve().parents[1] / "travelguru-v5" / "backend"
sys.path.insert(0, str(project_root))

from app.agents.langgraph_agents.travel_planner_graph import TravelPlannerOrchestrator


def save_trip_output_to_markdown(user_query: str, result: dict, output_file: str):
    """
    Save comprehensive trip planning output to a markdown file.
    
    Args:
        user_query: The original user query
        result: The full result from the orchestrator
        output_file: Path to the output markdown file
    """
    trip_response = result.get("trip")
    narrative = result.get("narrative")
    debug = result.get("debug", {})
    
    # Convert Pydantic model to dict if needed
    if trip_response and hasattr(trip_response, 'model_dump'):
        trip_data = trip_response.model_dump()
    else:
        trip_data = trip_response or {}
    
    # Create markdown content
    markdown_lines = []
    
    # Header
    markdown_lines.append("# TravelGuru - Comprehensive Trip Plan\n")
    markdown_lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
    markdown_lines.append(f"**Query:** {user_query}\n")
    markdown_lines.append("\n---\n\n")
    
    # Executive Summary
    if trip_data:
        markdown_lines.append("## 📋 Executive Summary\n\n")
        
        # Extract trip request data if available
        trip_plan = trip_data.get('trip_plan', {})
        budget_summary = trip_data.get('budget_summary', {})
        
        markdown_lines.append(f"- **Total Cost:** ₹{trip_data.get('total_cost', 0):,}\n")
        markdown_lines.append(f"- **Currency:** {trip_data.get('currency', 'INR')}\n")
        
        if budget_summary:
            markdown_lines.append(f"- **Flights Cost:** ₹{budget_summary.get('flights_cost', 0):,}\n")
            markdown_lines.append(f"- **Hotel Cost:** ₹{budget_summary.get('hotel_cost', 0):,}\n")
            markdown_lines.append(f"- **Activities Cost:** ₹{budget_summary.get('activities_cost', 0):,}\n")
        
        markdown_lines.append("\n---\n\n")
    
    # Trip Plan Details
    if trip_data and trip_data.get('trip_plan'):
        trip_plan = trip_data['trip_plan']
        
        # Flight Details
        if trip_plan.get('flight'):
            markdown_lines.append("## ✈️ Flight Details\n\n")
            flight = trip_plan['flight']
            markdown_lines.append(f"- **Airline:** {flight.get('airline', 'N/A')}\n")
            markdown_lines.append(f"- **Flight ID:** {flight.get('id', 'N/A')}\n")
            markdown_lines.append(f"- **Route:** {flight.get('origin', 'N/A')} → {flight.get('destination', 'N/A')}\n")
            markdown_lines.append(f"- **Departure:** {flight.get('departure_time', 'N/A')}\n")
            markdown_lines.append(f"- **Arrival:** {flight.get('arrival_time', 'N/A')}\n")
            markdown_lines.append(f"- **Duration:** {flight.get('duration', 'N/A')}\n")
            markdown_lines.append(f"- **Stops:** {flight.get('stops', 0)}\n")
            markdown_lines.append(f"- **Price:** ₹{flight.get('price', 0):,}\n\n")
            markdown_lines.append("---\n\n")
        
        # Hotel Details
        if trip_plan.get('hotel'):
            markdown_lines.append("## 🏨 Hotel Details\n\n")
            hotel = trip_plan['hotel']
            markdown_lines.append(f"- **Hotel Name:** {hotel.get('name', 'N/A')}\n")
            markdown_lines.append(f"- **Hotel ID:** {hotel.get('id', 'N/A')}\n")
            markdown_lines.append(f"- **Location:** {hotel.get('city', 'N/A')}\n")
            markdown_lines.append(f"- **Star Rating:** {'⭐' * hotel.get('stars', 0)}\n")
            markdown_lines.append(f"- **Price per Night:** ₹{hotel.get('price_per_night', 0):,}\n")
            markdown_lines.append(f"- **Check-in:** {hotel.get('check_in', 'N/A')}\n")
            markdown_lines.append(f"- **Check-out:** {hotel.get('check_out', 'N/A')}\n")
            
            amenities = hotel.get('amenities', [])
            if amenities:
                markdown_lines.append(f"- **Amenities:** {', '.join(amenities)}\n")
            
            markdown_lines.append("\n---\n\n")
        
        # Day-by-Day Itinerary
        if trip_plan.get('days'):
            markdown_lines.append("## 📅 Day-by-Day Itinerary\n\n")
            
            for idx, day in enumerate(trip_plan['days'], 1):
                markdown_lines.append(f"### Day {idx} - {day.get('date', 'N/A')}\n\n")
                
                activities = day.get('activities', [])
                if activities:
                    for activity in activities:
                        markdown_lines.append(f"#### 📍 {activity.get('name', 'Unknown Place')}\n\n")
                        markdown_lines.append(f"- **Category:** {activity.get('category', 'N/A')}\n")
                        markdown_lines.append(f"- **Rating:** {'⭐' * int(activity.get('rating', 0))} ({activity.get('rating', 'N/A')}/5.0)\n")
                        
                        if activity.get('entry_fee', 0) > 0:
                            markdown_lines.append(f"- **Entry Fee:** ₹{activity.get('entry_fee', 0)}\n")
                        else:
                            markdown_lines.append(f"- **Entry Fee:** Free\n")
                        
                        if activity.get('opening_hours'):
                            markdown_lines.append(f"- **Opening Hours:** {activity['opening_hours']}\n")
                        
                        if activity.get('recommended_duration'):
                            markdown_lines.append(f"- **Recommended Duration:** {activity['recommended_duration']}\n")
                        
                        if activity.get('best_time_to_visit'):
                            markdown_lines.append(f"- **Best Time to Visit:** {activity['best_time_to_visit']}\n")
                        
                        if activity.get('description'):
                            markdown_lines.append(f"- **Description:** {activity['description']}\n")
                        
                        if activity.get('address'):
                            markdown_lines.append(f"- **Address:** {activity['address']}\n")
                        
                        if activity.get('transport_modes'):
                            markdown_lines.append(f"- **How to Reach:** {', '.join(activity['transport_modes'])}\n")
                        
                        if activity.get('special_notes'):
                            markdown_lines.append(f"- **Special Notes:** {activity['special_notes']}\n")
                        
                        markdown_lines.append("\n")
                else:
                    markdown_lines.append("*No activities planned for this day*\n\n")
            
            markdown_lines.append("---\n\n")
        
        # Weather Information
        if trip_plan.get('weather'):
            markdown_lines.append("## 🌤️ Weather Forecast\n\n")
            for weather in trip_plan['weather']:
                markdown_lines.append(f"- **{weather.get('date', 'N/A')}:** {weather.get('condition', 'N/A')}, {weather.get('temperature_c', 'N/A')}°C\n")
            markdown_lines.append("\n---\n\n")
    
    # Budget Breakdown
    if trip_data and trip_data.get('budget_summary'):
        budget = trip_data['budget_summary']
        markdown_lines.append("## 💰 Budget Breakdown\n\n")
        markdown_lines.append(f"| Category | Cost |\n")
        markdown_lines.append(f"|----------|------|\n")
        markdown_lines.append(f"| Flights | ₹{budget.get('flights_cost', 0):,} |\n")
        markdown_lines.append(f"| Hotel | ₹{budget.get('hotel_cost', 0):,} |\n")
        markdown_lines.append(f"| Activities | ₹{budget.get('activities_cost', 0):,} |\n")
        markdown_lines.append(f"| **Total** | **₹{budget.get('total_cost', 0):,}** |\n")
        markdown_lines.append("\n")
        
        # Budget Enrichment
        if budget.get('enrichment'):
            enrichment = budget['enrichment']
            markdown_lines.append("### Budget Intelligence\n\n")
            
            # Health Score
            if enrichment.get('health_score'):
                health = enrichment['health_score']
                markdown_lines.append(f"**Budget Health Score:** {health.get('score', 0)}/10 ({health.get('severity', 'N/A')})\n\n")
            
            # Verdict
            if enrichment.get('verdict'):
                verdict = enrichment['verdict']
                status_icon = "✅" if verdict.get('status') == 'approved' else "⚠️"
                markdown_lines.append(f"{status_icon} **Status:** {verdict.get('message', 'N/A')}\n\n")
            
            # Issues
            if enrichment.get('issues'):
                markdown_lines.append("#### ⚠️ Budget Issues\n\n")
                for issue in enrichment['issues']:
                    severity_icon = "🔴" if issue.get('severity') == 'critical' else "🟡"
                    markdown_lines.append(f"{severity_icon} **{issue.get('category', 'N/A').upper()}:** {issue.get('description', 'N/A')}\n")
                markdown_lines.append("\n")
            
            # Recommendations
            if enrichment.get('recommendations'):
                markdown_lines.append("#### 💡 Recommendations\n\n")
                for rec in enrichment['recommendations']:
                    priority_icon = "🔴" if rec.get('priority') == 'high' else "🟡" if rec.get('priority') == 'medium' else "🟢"
                    markdown_lines.append(f"{priority_icon} **{rec.get('category', 'N/A').upper()}:** {rec.get('action', 'N/A')} (Save ₹{rec.get('savings', 0):,})\n")
                markdown_lines.append("\n")
        
        markdown_lines.append("---\n\n")
    
    # Comprehensive Narrative
    if narrative:
        markdown_lines.append("## 📖 Comprehensive Trip Narrative\n\n")
        markdown_lines.append(narrative)
        markdown_lines.append("\n\n---\n\n")
        
        # Output Metrics
        word_count = len(narrative.split())
        char_count = len(narrative)
        markdown_lines.append("### 📊 Narrative Metrics\n\n")
        markdown_lines.append(f"- **Word Count:** {word_count:,}\n")
        markdown_lines.append(f"- **Character Count:** {char_count:,}\n")
        markdown_lines.append("\n---\n\n")
    
    # Orchestration Metrics
    if debug:
        markdown_lines.append("## ⚙️ Orchestration Metrics\n\n")
        
        # Timings
        timings = debug.get('timings', {})
        if timings:
            markdown_lines.append("### ⏱️ Execution Timings\n\n")
            markdown_lines.append("| Agent | Duration |\n")
            markdown_lines.append("|-------|----------|\n")
            for agent, duration in timings.items():
                markdown_lines.append(f"| {agent} | {duration:.2f}s |\n")
            markdown_lines.append("\n")
        
        # Enrichment Status
        enriched = debug.get('enriched', {})
        if enriched:
            markdown_lines.append("### 🎯 Enrichment Status\n\n")
            for key, value in enriched.items():
                status = "✅" if value else "❌"
                markdown_lines.append(f"{status} {key.capitalize()}\n")
            markdown_lines.append("\n")
    
    # Footer
    markdown_lines.append("\n---\n\n")
    markdown_lines.append("*Generated by TravelGuru AI Multi-Agent System*\n")
    
    # Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(markdown_lines))
    
    return output_path


def test_comprehensive_trip_planning():
    """
    Test comprehensive trip planning with full output saved to markdown.
    """
    print("="*100)
    print(" >> COMPREHENSIVE TRIP PLANNING TEST")
    print("="*100)
    print()
    
    # Define user query
    user_query = "Plan a 1 day romantic trip for 2 adults from Delhi to Goa starting February 12, 2026 with a budget of 80000 rupees"
    
    print(f"📋 User Query: {user_query}")
    print()
    print("🚀 Executing full travel planning orchestration...")
    print("   (Planner → Services → Enrichers → Itinerary → Composer)")
    print()
    
    try:
        # Initialize orchestrator
        orchestrator = TravelPlannerOrchestrator()
        
        # Execute full trip planning
        print("⏳ Processing... (this may take 30-60 seconds)\n")
        result = orchestrator.plan_trip_from_text(user_query)
        
        # Display execution summary
        debug = result.get("debug", {})
        timings = debug.get("timings", {})
        
        print("✅ Trip planning completed!\n")
        print("-" * 100)
        print("EXECUTION TIMINGS:")
        print("-" * 100)
        total_time = 0
        for agent, duration in timings.items():
            print(f"  {agent:30s}: {duration:8.2f}s")
            total_time += duration
        print(f"  {'TOTAL':30s}: {total_time:8.2f}s")
        print()
        
        # Display enrichment status
        enriched = debug.get("enriched", {})
        print("-" * 100)
        print("ENRICHMENT STATUS:")
        print("-" * 100)
        for key in ["flights", "hotels", "places", "weather", "budget"]:
            status = "✅ YES" if enriched.get(key) else "❌ NO "
            print(f"  {key.capitalize():20s}: {status}")
        print()
        
        # Display output metrics
        narrative = result.get("narrative", "")
        word_count = len(narrative.split()) if narrative else 0
        
        print("-" * 100)
        print("OUTPUT METRICS:")
        print("-" * 100)
        print(f"  Narrative Word Count:  {word_count:,}")
        print(f"  Narrative Char Count:  {len(narrative):,}")
        print()
        
        # Save to markdown file
        output_dir = Path(__file__).parent / "outputs"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"comprehensive_trip_plan_{timestamp}.md"
        
        print("-" * 100)
        print("SAVING OUTPUT TO MARKDOWN FILE:")
        print("-" * 100)
        saved_path = save_trip_output_to_markdown(user_query, result, str(output_file))
        print(f"  ✅ Saved to: {saved_path}")
        print(f"  📊 File size: {saved_path.stat().st_size:,} bytes")
        print()
        
        # Display trip summary
        trip_response = result.get("trip", {})
        
        # Convert to dict if Pydantic model
        if hasattr(trip_response, 'model_dump'):
            trip_data = trip_response.model_dump()
        else:
            trip_data = trip_response
        
        budget_summary = trip_data.get("budget_summary", {})
        
        print("="*100)
        print(" >> TRIP SUMMARY")
        print("="*100)
        print()
        print(f"  Total Cost:   ₹{trip_data.get('total_cost', 0):,}")
        print(f"  Currency:     {trip_data.get('currency', 'INR')}")
        
        # Budget status
        if budget_summary.get('enrichment', {}).get('verdict'):
            verdict = budget_summary['enrichment']['verdict']
            status_icon = "✅" if verdict.get('status') == 'approved' else "⚠️"
            print(f"  Status:       {status_icon} {verdict.get('message', 'N/A')}")
        
        print()
        print("="*100)
        print(" >> TEST COMPLETED SUCCESSFULLY")
        print("="*100)
        print()
        print(f"📄 View the complete output in: {saved_path.name}")
        print()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_comprehensive_trip_planning()
