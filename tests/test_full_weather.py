"""
Weather Agent Test - Comprehensive Enrichment Display
Shows weather intelligence with all enrichment layers.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1] / "travelguru-v5" / "backend"
sys.path.insert(0, str(project_root))

from app.agents.langgraph_agents.tools.weather.service import get_weather_forecast

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def format_score(value: float) -> str:
    """Format numeric 0-10 scores into labeled ranges.

    Ranges:
      9-10 -> excellent
      7-9  -> good
      5-7  -> moderate
      0-5  -> poor
    """
    try:
        s = float(value)
    except Exception:
        return str(value)
    if s >= 9:
        label = "excellent"
    elif s >= 7:
        label = "good"
    elif s >= 5:
        label = "moderate"
    else:
        label = "poor"
    return f"{s:.1f}/10 ({label})"

def display_weather_enrichment(analysis):
    """Display enriched weather forecast with all intelligence layers."""
    
    print("\n" + "=" * 80)
    print(f"  WEATHER FORECAST INTELLIGENCE - {analysis.enriched_days[0].weather.city.upper()}")
    print("=" * 80)
    
    # Trip-level summary
    print(f"\nTRIP OVERVIEW:")
    print(f"  {analysis.trip_summary}")
    print(f"  Overall Comfort: {analysis.overall_comfort}")
    if analysis.best_day:
        print(f"  Best Day: {analysis.best_day}")
    if analysis.worst_day:
        print(f"  Worst Day: {analysis.worst_day}")
    
    # Trip-level insights
    if analysis.trip_insights:
        print(f"\nTRIP INSIGHTS:")
        for insight in analysis.trip_insights:
            symbol = "!" if insight.type == "warning" else "i" if insight.type == "tip" else "+"
            print(f"  [{symbol}] {insight.message}")
    
    # Travel tips
    if analysis.travel_tips:
        print(f"\nTRAVEL TIPS:")
        for tip in analysis.travel_tips:
            print(f"  - {tip}")
    
    # Packing checklist
    if analysis.packing_checklist:
        print(f"\nPACKING CHECKLIST:")
        for item in analysis.packing_checklist:
            print(f"  [ ] {item}")
    
    # Daily forecasts
    print("\n" + "=" * 80)
    print("DAILY WEATHER BREAKDOWN")
    print("=" * 80)
    
    for day in analysis.enriched_days:
        weather = day.weather
        comfort = day.comfort_score
        suitability = day.travel_suitability
        risk = day.risk_assessment
        packing = day.packing_advice
        
        print(f"\n{'-' * 80}")
        print(f"DATE: {weather.date}")
        print(f"{'-' * 80}")
        
        # Basic weather
        print(f"\nWEATHER:")
        print(f"  Condition: {weather.condition}")
        print(f"  Temperature: {weather.temp_min_c}C - {weather.temp_max_c}C (avg {weather.temp_avg_c}C)")
        print(f"  Rain Chance: {int(weather.rain_chance * 100)}%")
        
        # Daily summary
        print(f"\nSUMMARY: {day.daily_summary}")
        print(f"Best Time: {day.best_time_of_day}")
        
        # Comfort score
        print(f"\nCOMFORT ANALYSIS:")
        print(f"  Overall: {format_score(comfort.overall_score)}")
        print(f"  Temperature: {format_score(comfort.temperature_comfort)}")
        print(f"  Precipitation: {format_score(comfort.precipitation_comfort)}")
        print(f"  {comfort.explanation}")
        
        # Travel suitability
        print(f"\nTRAVEL SUITABILITY: {suitability.overall_rating}")
        print(f"  Outdoor Activities: {format_score(suitability.outdoor_score)}")
        print(f"  Sightseeing: {format_score(suitability.sightseeing_score)}")
        print(f"  Beach Activities: {format_score(suitability.beach_score)}")
        
        # Activity Suitability
        print(f"\nACTIVITY SUITABILITY:")
        if suitability.best_activities:
            print(f"  Best Activities:")
            for activity in suitability.best_activities:
                print(f"    - {activity}")
        if suitability.avoid_activities:
            print(f"  Activities to Avoid:")
            for activity in suitability.avoid_activities:
                print(f"    - {activity}")
        if not suitability.best_activities and not suitability.avoid_activities:
            print(f"  All general activities suitable")
        
        # Risk assessment
        print(f"\nRISK ASSESSMENT: {risk.risk_level}")
        if risk.rain_risk:
            print(f"  Rain Risk: Yes")
        if risk.extreme_heat:
            print(f"  Extreme Heat: Yes")
        if risk.extreme_cold:
            print(f"  Extreme Cold: Yes")
        if risk.storm_risk:
            print(f"  Storm Risk: Yes")
        
        if risk.warnings:
            print(f"  Warnings:")
            for warning in risk.warnings:
                print(f"    - {warning}")
        
        if risk.precautions:
            print(f"  Precautions:")
            for precaution in risk.precautions:
                print(f"    - {precaution}")
        
        # Packing advice
        print(f"\nPACKING ADVICE:")
        if packing.essential_items:
            print(f"  Essential: {', '.join(packing.essential_items)}")
        if packing.recommended_items:
            print(f"  Recommended: {', '.join(packing.recommended_items)}")
        if packing.clothing_suggestions:
            print(f"  Clothing: {', '.join(packing.clothing_suggestions)}")
        if packing.accessories:
            print(f"  Accessories: {', '.join(packing.accessories)}")
        
        # Travel Advice
        print(f"\nTRAVEL ADVICE:")
        print(f"  Best time for outdoor activities: {day.best_time_of_day}")
        if risk.precautions:
            print(f"  Safety Precautions:")
            for precaution in risk.precautions:
                print(f"    - {precaution}")
        if comfort.comfort_level in ["excellent", "good"]:
            print(f"  Great day for exploring - {comfort.explanation}")
        elif comfort.comfort_level in ["poor", "challenging"]:
            print(f"  Consider indoor activities - {comfort.explanation}")
        
        # Wind/Humidity/UV/AQI (if available)
        if day.wind_impact:
            print(f"\nWIND IMPACT:")
            print(f"  Category: {day.wind_impact.category} ({day.wind_impact.speed_kmh} km/h)")
            print(f"  Impact Score: {format_score(day.wind_impact.impact_score)}")
            if day.wind_impact.considerations:
                for consideration in day.wind_impact.considerations:
                    print(f"  - {consideration}")
        
        if day.humidity_comfort:
            print(f"\nHUMIDITY COMFORT:")
            print(f"  Level: {day.humidity_comfort.category} ({day.humidity_comfort.humidity_percent}%)")
            print(f"  Comfort Score: {format_score(day.humidity_comfort.comfort_score)}")
            if day.humidity_comfort.health_notes:
                for note in day.humidity_comfort.health_notes:
                    print(f"  - {note}")
        
        if day.uv_assessment:
            print(f"\nUV INDEX:")
            print(f"  Level: {day.uv_assessment.category} (UV {day.uv_assessment.uv_index})")
            print(f"  Risk: {day.uv_assessment.risk_level}")
            if day.uv_assessment.protection_advice:
                for advice in day.uv_assessment.protection_advice:
                    print(f"  - {advice}")
        
        if day.air_quality:
            print(f"\nAIR QUALITY:")
            print(f"  AQI: {day.air_quality.category} ({day.air_quality.aqi_value})")
            print(f"  Impact: {day.air_quality.health_impact}")
            if day.air_quality.recommendations:
                for rec in day.air_quality.recommendations:
                    print(f"  - {rec}")
        
        # Daily insights
        if day.insights:
            print(f"\nDAILY INSIGHTS:")
            for insight in day.insights:
                symbol = "!" if insight.type == "warning" else "i" if insight.type == "tip" else "+"
                print(f"  [{symbol}] {insight.message}")


def main():
    """Run weather enrichment test."""
    
    print("\n" + "=" * 80)
    print("  WEATHER AGENT - ENRICHMENT TEST")
    print("=" * 80)
    
    city = "Delhi"
    days = 5
    
    print(f"\nQuerying weather for: {city} (next {days} days)")
    print("Fetching forecast and applying intelligence enrichment...\n")
    
    try:
        # Get weather forecast (automatically enriched)
        forecast = get_weather_forecast(city=city, days=days)
        
        # The service returns enriched data via TripWeatherAnalysis
        # We need to access it through the service's enrichment
        from app.agents.postprocessing.weather_enrichment import enrich_weather_forecast
        
        analysis = enrich_weather_forecast(forecast)
        
        # Display enriched forecast
        display_weather_enrichment(analysis)
        
        print("\n" + "=" * 80)
        print("  TEST COMPLETED SUCCESSFULLY")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nTEST FAILED\n")


if __name__ == "__main__":
    main()
