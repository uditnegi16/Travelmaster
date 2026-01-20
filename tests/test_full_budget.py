"""
Test Budget Service with Enrichment
Demonstrates comprehensive budget analysis with intelligence and recommendations.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1] / "travelguru-v5" / "backend"
sys.path.insert(0, str(project_root))

from app.shared.schemas import FlightOption, HotelOption, PlaceOption
from app.agents.langgraph_agents.tools.budget.service import compute_budget


def test_budget_with_enrichment():
    """Test budget computation with full enrichment."""
    
    print("\n" + "="*80)
    print("BUDGET ENRICHMENT TEST - SCENARIO 1: Over Budget Trip")
    print("="*80)
    
    # Sample trip data
    flight = FlightOption(
        id="FL001",
        airline="AI",
        origin="DEL",
        destination="GOA",
        departure_time="2026-02-01T10:00:00Z",
        arrival_time="2026-02-01T12:30:00Z",
        duration="2h 30m",
        price=12000,
        currency="INR"
    )
    
    hotel = HotelOption(
        id="HTL001",
        name="Luxury Beach Resort",
        city="Goa",
        stars=5,
        price_per_night=8000,
        amenities=["Pool", "Spa", "Beach Access"]
    )
    
    places = [
        PlaceOption(id="P1", name="Fort Aguada", city="Goa", category="Historical", rating=4.5, entry_fee=100),
        PlaceOption(id="P2", name="Baga Beach", city="Goa", category="Beach", rating=4.3, entry_fee=0),
        PlaceOption(id="P3", name="Dudhsagar Falls", city="Goa", category="Nature", rating=4.7, entry_fee=400),
    ]
    
    # Compute budget with enrichment
    budget = compute_budget(
        flight=flight,
        hotel=hotel,
        nights=4,
        places=places,
        num_travelers=2,
        user_budget=50000,
        enable_enrichment=True
    )
    
    # Display basic summary
    print("\nBASIC BUDGET SUMMARY")
    print("-" * 80)
    print(f"Flights Cost:    Rs. {budget.flights_cost:,}")
    print(f"Hotel Cost:      Rs. {budget.hotel_cost:,}")
    print(f"Activities Cost: Rs. {budget.activities_cost:,}")
    print(f"Total Cost:      Rs. {budget.total_cost:,}")
    print(f"Currency:        {budget.currency}")
    
    # Display enrichment details
    if budget.enrichment:
        enrichment = budget.enrichment
        
        print("\n" + "="*80)
        print("ENRICHMENT DETAILS")
        print("="*80)
        
        # Verdict (at top)
        print("\nVERDICT:")
        print("-" * 80)
        verdict_symbol = "X" if enrichment.verdict.status == "needs_optimization" else "✓"
        print(f"{verdict_symbol} {enrichment.verdict.message}")
        
        # Budget Health Score
        print("\nBUDGET HEALTH SCORE:")
        print("-" * 80)
        print(f"Score: {enrichment.health_score.score:.1f} / 10 ({enrichment.health_score.severity})")
        if enrichment.health_score.factors:
            print("\nBased on:")
            for factor in enrichment.health_score.factors:
                print(f"  - {factor}")
        
        # Cost breakdown
        print("\nFULL COST BREAKDOWN:")
        print("-" * 80)
        breakdown = enrichment.cost_breakdown
        print(f"Flights:         Rs. {breakdown.flights:,}")
        print(f"Hotel:           Rs. {breakdown.hotel:,}")
        print(f"Activities:      Rs. {breakdown.activities:,}")
        print(f"Local Transport: Rs. {breakdown.local_transport:,}")
        print(f"Food:            Rs. {breakdown.food:,}")
        print(f"Buffer (10%):    Rs. {breakdown.buffer:,}")
        total_with_estimates = (breakdown.flights + breakdown.hotel + breakdown.activities + 
                               breakdown.local_transport + breakdown.food + breakdown.buffer)
        print(f"{'':16} {'-' * 20}")
        print(f"TOTAL ESTIMATED: Rs. {total_with_estimates:,}")
        
        # Intelligence metrics
        print("\nINTELLIGENCE METRICS:")
        print("-" * 80)
        metrics = enrichment.intelligence_metrics
        print(f"Cost per Day:    Rs. {metrics.cost_per_day:,.2f}")
        print(f"Cost per Person: Rs. {metrics.cost_per_person:,.2f}")
        print(f"Dominant Driver: {metrics.dominant_cost_driver} ({metrics.dominant_cost_percentage:.1f}%)")
        
        print("\nCategory Distribution:")
        for category, percentage in metrics.category_percentages.items():
            bar_length = int(percentage / 2)
            bar = "#" * bar_length
            print(f"  {category:15} {percentage:5.1f}% {bar}")
        
        # Classification
        print("\nTRIP CLASSIFICATION:")
        print("-" * 80)
        print(f"Type:       {enrichment.classification.classification}")
        print(f"Threshold:  {enrichment.classification.threshold_info}")
        
        # Issues
        print(f"\nISSUES DETECTED ({len(enrichment.issues)}):")
        print("-" * 80)
        if enrichment.issues:
            for issue in enrichment.issues:
                severity = issue.severity.upper()
                print(f"[{severity}] {issue.category}")
                print(f"  {issue.description}")
                if issue.impact_amount:
                    print(f"  Impact: Rs. {issue.impact_amount:,}")
                print()
        else:
            print("No issues detected.")
        
        # Recommendations
        print(f"RECOMMENDATIONS ({len(enrichment.recommendations)}):")
        print("-" * 80)
        if enrichment.recommendations:
            for i, rec in enumerate(enrichment.recommendations, 1):
                priority = rec.priority.upper()
                print(f"{i}. [{priority}] {rec.category.upper()}")
                print(f"   Action: {rec.action}")
                if rec.savings > 0:
                    print(f"   Savings: Rs. {rec.savings:,}")
                elif rec.savings < 0:
                    print(f"   Spend: Rs. {abs(rec.savings):,}")
                print()
        else:
            print("No recommendations.")
        
        # Simulation
        if enrichment.simulation:
            print("\nSIMULATION - If you apply top recommendations:")
            print("=" * 80)
            sim = enrichment.simulation
            print(f"\nApplying {len(sim.applied_recommendations)} recommendation(s):")
            for i, rec in enumerate(sim.applied_recommendations, 1):
                print(f"  {i}. {rec}")
            
            print(f"\nOriginal Total:      Rs. {sim.original_total:,}")
            print(f"Total Savings:       Rs. {sim.total_savings:,}")
            print(f"New Estimated Total: Rs. {sim.new_total:,}")
            
            status_symbol = "✓" if sim.within_budget else "X"
            print(f"\nStatus: {status_symbol} {sim.verdict_message}")
    
    print("="*80)
    print("TEST COMPLETED")
    print("="*80 + "\n")


def test_balanced_budget():
    """Test a well-balanced budget scenario."""
    
    print("\n" + "="*80)
    print("BUDGET ENRICHMENT TEST - SCENARIO 2: Well-Balanced Trip")
    print("="*80)
    
    # Sample trip data - more balanced
    flight = FlightOption(
        id="FL002",
        airline="6E",
        origin="BLR",
        destination="JAI",
        departure_time="2026-03-15T06:00:00Z",
        arrival_time="2026-03-15T08:30:00Z",
        duration="2h 30m",
        price=3500,
        currency="INR"
    )
    
    hotel = HotelOption(
        id="HTL002",
        name="Heritage Stay",
        city="Jaipur",
        stars=3,
        price_per_night=2000,
        amenities=["WiFi", "Breakfast", "AC"]
    )
    
    places = [
        PlaceOption(id="P1", name="Amber Fort", city="Jaipur", category="Historical", rating=4.8, entry_fee=500),
        PlaceOption(id="P2", name="City Palace", city="Jaipur", category="Palace", rating=4.6, entry_fee=700),
        PlaceOption(id="P3", name="Hawa Mahal", city="Jaipur", category="Monument", rating=4.5, entry_fee=200),
        PlaceOption(id="P4", name="Jantar Mantar", city="Jaipur", category="Observatory", rating=4.4, entry_fee=200),
    ]
    
    # Compute budget with enrichment
    budget = compute_budget(
        flight=flight,
        hotel=hotel,
        nights=3,
        places=places,
        num_travelers=1,
        user_budget=25000,
        enable_enrichment=True
    )
    
    # Display basic summary
    print("\nBASIC BUDGET SUMMARY")
    print("-" * 80)
    print(f"Flights Cost:    Rs. {budget.flights_cost:,}")
    print(f"Hotel Cost:      Rs. {budget.hotel_cost:,}")
    print(f"Activities Cost: Rs. {budget.activities_cost:,}")
    print(f"Total Cost:      Rs. {budget.total_cost:,}")
    print(f"Currency:        {budget.currency}")
    
    # Display enrichment details
    if budget.enrichment:
        enrichment = budget.enrichment
        
        print("\n" + "="*80)
        print("ENRICHMENT DETAILS")
        print("="*80)
        
        # Verdict
        print("\nVERDICT:")
        print("-" * 80)
        verdict_symbol = "X" if enrichment.verdict.status == "needs_optimization" else "✓"
        print(f"{verdict_symbol} {enrichment.verdict.message}")
        
        # Budget Health Score
        print("\nBUDGET HEALTH SCORE:")
        print("-" * 80)
        print(f"Score: {enrichment.health_score.score:.1f} / 10 ({enrichment.health_score.severity})")
        if enrichment.health_score.factors:
            print("\nBased on:")
            for factor in enrichment.health_score.factors:
                print(f"  - {factor}")
        
        # Cost breakdown
        print("\nFULL COST BREAKDOWN:")
        print("-" * 80)
        breakdown = enrichment.cost_breakdown
        total_with_estimates = (breakdown.flights + breakdown.hotel + breakdown.activities + 
                               breakdown.local_transport + breakdown.food + breakdown.buffer)
        print(f"Flights:         Rs. {breakdown.flights:,}")
        print(f"Hotel:           Rs. {breakdown.hotel:,}")
        print(f"Activities:      Rs. {breakdown.activities:,}")
        print(f"Local Transport: Rs. {breakdown.local_transport:,}")
        print(f"Food:            Rs. {breakdown.food:,}")
        print(f"Buffer (10%):    Rs. {breakdown.buffer:,}")
        print(f"{'':16} {'-' * 20}")
        print(f"TOTAL ESTIMATED: Rs. {total_with_estimates:,}")
        
        # Intelligence metrics
        print("\nINTELLIGENCE METRICS:")
        print("-" * 80)
        metrics = enrichment.intelligence_metrics
        print(f"Cost per Day:    Rs. {metrics.cost_per_day:,.2f}")
        print(f"Dominant Driver: {metrics.dominant_cost_driver} ({metrics.dominant_cost_percentage:.1f}%)")
        
        # Classification
        print("\nTRIP CLASSIFICATION:")
        print("-" * 80)
        print(f"Type: {enrichment.classification.classification}")
        
        # Issues
        if enrichment.issues:
            print(f"\nISSUES: {len(enrichment.issues)}")
            print("-" * 80)
            for issue in enrichment.issues:
                print(f"  - [{issue.severity.upper()}] {issue.description}")
        
        # Simulation
        if enrichment.simulation:
            print("\nSIMULATION - If you apply top recommendations:")
            print("=" * 80)
            sim = enrichment.simulation
            print(f"New Estimated Total: Rs. {sim.new_total:,}")
            print(f"Total Savings:       Rs. {sim.total_savings:,}")
            status_symbol = "✓" if sim.within_budget else "X"
            print(f"Status: {status_symbol} {sim.verdict_message}")
    
    print("="*80)
    print("TEST COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_budget_with_enrichment()
    test_balanced_budget()
