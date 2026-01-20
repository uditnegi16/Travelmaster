# TravelGuru - Developer Instructions

##  Overview

**TravelGuru** is a multi-agent AI travel planning system that uses LangGraph orchestration to plan complete trips. It takes a natural language query like *"Plan a 5-day trip from Delhi to Goa"* and generates:

-  Flight recommendations with market analysis
-  Hotel recommendations with intelligent scoring
-  Places to visit with detailed information
-  Weather forecasts
-  Budget breakdown with health score and optimization recommendations
-  Day-by-day itinerary
-  Comprehensive narrative (6,000-13,000 words)

**Total execution time**: ~8-10 minutes for a 5-day trip

---

##  System Architecture

### Multi-Agent Workflow

```
User Query
    ↓
┌─────────────────────────────────────────────────────┐
│  PLANNER AGENT                                      │
│  - Parses user input                                │
│  - Creates execution plan                           │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  SERVICE LAYER (Parallel Execution)                 │
│  - Flights Service     (6-7 seconds)                │
│  - Hotels Service      (27-32 seconds)              │
│  - Places Service      (2 seconds)                  │
│  - Weather Service     (0.5 seconds)                │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  ENRICHMENT AGENTS (Add Intelligence)               │
│  - Flight Enricher     (market analysis)            │
│  - Hotel Enricher      (scoring & ranking)          │
│  - Places Enricher     (curation & metadata)        │
│  - Weather Enricher    (impact analysis)            │
│  - Budget Enricher     (health score, recommendations)│
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  ITINERARY BUILDER                                  │
│  - Creates day-by-day schedule                      │
│  - Optimizes activity sequence                      │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│  COMPOSER AGENT (480-510 seconds)                   │
│  - Generates comprehensive narrative                │
│  - Explains reasoning and tradeoffs                 │
│  - Creates 6,000-13,000 word output                 │
└─────────────────────────────────────────────────────┘
    ↓
Final Trip Plan (JSON + Markdown)
```

---

### Installation Steps

```bash
# 1. Navigate to the backend directory
cd travelguru-v5/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
# Create a .env file or set in your system:
export OPENAI_API_KEY="your-api-key-here"

# 4. Verify installation
python -c "from app.agents.langgraph_agents.travel_planner_graph import TravelPlannerOrchestrator; print(' Setup complete!')"
```

---

##  How to Use the System

### Method 1: Quick Test (Recommended for First-Time Users)

Run one of the test files to see the system in action:

```bash
# Test individual components
python tests/test_full_flight.py      # Test flight enrichment
python tests/test_full_hotel.py       # Test hotel enrichment
python tests/test_full_places.py      # Test places enrichment
python tests/test_full_budget.py      # Test budget enrichment

# Test complete trip planning with output saved to markdown
python tests/test_comprehensive_trip_output.py
```

**Output**: Creates a markdown file in `tests/outputs/` with the complete trip plan.

### Method 2: Programmatic Usage

```python
from app.agents.langgraph_agents.travel_planner_graph import TravelPlannerOrchestrator

# Initialize orchestrator
orchestrator = TravelPlannerOrchestrator()

# Plan a trip from natural language
result = orchestrator.plan_trip_from_text(
    "Plan a 5 day romantic trip for 2 adults from Delhi to Goa starting February 12, 2026 with a budget of 80000 rupees"
)

# Access results
trip = result["trip"]              # TripResponse object with all data
narrative = result["narrative"]    # Comprehensive text output
debug = result["debug"]           # Timing and enrichment info

# Print the narrative
print(narrative)
```

##  Testing

### Available Test Files

| Test File | Purpose | Output |
|-----------|---------|--------|
| `test_full_flight.py` | Tests flight enrichment with market analysis | Console output with scoring |
| `test_full_hotel.py` | Tests hotel scoring and ranking | Console output with scores |
| `test_full_places.py` | Tests places curation and metadata | Console output with enrichment |
| `test_full_budget.py` | Tests budget analysis with health score | Console output with recommendations |
| `test_full_trip.py` | Tests complete orchestration | Console output |
| `test_comprehensive_trip_output.py` | **Full trip plan + saves to .md file** | **Markdown file in `tests/outputs/`** |
| `test_schemas.py` | Validates all Pydantic schemas | Pytest results |
| `test_composer_output.py` | Tests composer narrative generation | Console output with word count |

### Running Tests

```bash
# Run a specific test
python tests/test_full_budget.py

# Run all tests with pytest
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run a specific test file with pytest
pytest tests/test_schemas.py -v
```

##  Understanding the Output

### 1. TripResponse Object Structure

```python
TripResponse:
  - trip_plan: TripPlan
      - flight: FlightOption
      - hotel: HotelOption
      - days: List[DayPlan]
          - date: str
          - activities: List[PlaceOption]
      - weather: List[WeatherInfo]
  
  - budget_summary: BudgetSummary
      - flights_cost: int
      - hotel_cost: int
      - activities_cost: int
      - total_cost: int
      - enrichment: BudgetEnrichment (health score, recommendations)
  
  - narrative: str (comprehensive 6000-13000 word output)
  
  - flight_analysis: dict (market analysis)
  - hotel_analysis: dict (scoring data)
  - places_analysis: dict (curation data)
  - weather_analysis: dict (impact analysis)
  - budget_analysis: dict (optimization data)
```

### 2. Budget Enrichment Fields

```python
BudgetEnrichment:
  - cost_breakdown: CostBreakdown
      - flights, hotel, activities
      - local_transport, food, buffer
  
  - intelligence_metrics: IntelligenceMetrics
      - cost_per_day, cost_per_person
      - category_percentages
      - dominant_cost_driver
  
  - health_score: BudgetHealthScore (0-10)
      - score, severity, factors
  
  - verdict: BudgetVerdict
      - status: approved/needs_optimization
      - message
  
  - issues: List[BudgetIssue]
      - severity, category, description
  
  - recommendations: List[BudgetRecommendation]
      - action, savings, priority
  
  - simulation: BudgetSimulation
      - applied_recommendations
      - new_total, total_savings
```

### 3. Markdown Output Sections

When you run `test_comprehensive_trip_output.py`, the generated markdown file includes:

1. **Executive Summary** - Budget, costs, currency
2. **Flight Details** - Airline, route, timings, price
3. **Hotel Details** - Name, stars, amenities, check-in/out
4. **Day-by-Day Itinerary** - All activities with:
   - Name, category, rating
   - Entry fees, opening hours
   - Recommended duration, best time to visit
   - Transport modes, special notes
5. **Weather Forecast** - Daily conditions and temperatures
6. **Budget Breakdown** - Table with all costs
7. **Budget Intelligence** - Health score, issues, recommendations
8. **Comprehensive Narrative** - Full AI-generated text (6000-13000 words)
9. **Orchestration Metrics** - Execution timings, enrichment status

---

##  Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'app'
# Solution: Make sure you're running from the correct directory
cd travelguru-v5/backend
python -m pytest tests/
```

#### 2. OpenAI API Errors
```bash
# Error: AuthenticationError: Invalid API key
# Solution: Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"
```

#### 3. Long Execution Time
```
# The composer takes 8-10 minutes - this is normal
# It generates 6,000-13,000 words with detailed analysis

# If it's too slow, you can:
# 1. Use a faster model (change in composer_agent.py)
# 2. Reduce the word count target
# 3. Skip enrichment for faster results
```

#### 4. Schema Validation Errors
```bash
# Error: ValidationError from Pydantic
# Solution: Check the schemas.py file for correct structure
# Run schema tests to identify issues:
pytest tests/test_schemas.py -v
```

#### 5. Empty or Missing Data
```bash
# If flight/hotel/places are empty:
# 1. Check data files in backend/data/
# 2. Verify search parameters match available data
# 3. Check logs for search errors
```

---

##  UI Integration Guide

### Main Function to Call

```python
from app.agents.langgraph_agents.travel_planner_graph import TravelPlannerOrchestrator

# Initialize once (can reuse)
orchestrator = TravelPlannerOrchestrator()

# Call this function with user query
result = orchestrator.plan_trip_from_text(user_query)
```

### Input Format

```python
# User query as plain text
user_query = "Plan a 5 day trip for 2 adults from Delhi to Goa starting 24 Jan, 2026 with a budget of 70000 rupees"
```

### Output Format

```python
result = {
    "trip": TripResponse,      # Pydantic object - use .model_dump() to convert to dict
    "narrative": str,          # Full 6000-13000 word narrative
    "debug": {
        "timings": {...},      # Execution times for each agent
        "enriched": {...}      # Status of enrichments (True/False)
    }
}
```

### How to Use the Output

```python
# Get trip data
trip = result["trip"]

# Convert Pydantic model to dictionary (IMPORTANT!)
if hasattr(trip, 'model_dump'):
    trip_data = trip.model_dump()
else:
    trip_data = trip

# Access data
total_cost = trip_data['total_cost']
currency = trip_data['currency']
narrative = result["narrative"]

# Trip plan details
trip_plan = trip_data['trip_plan']
flight = trip_plan['flight']          # Flight details
hotel = trip_plan['hotel']            # Hotel details
days = trip_plan['days']              # List of daily itineraries
weather = trip_plan['weather']        # Weather forecast

# Budget details
budget = trip_data['budget_summary']
flights_cost = budget['flights_cost']
hotel_cost = budget['hotel_cost']
activities_cost = budget['activities_cost']

# Budget enrichment (health score, recommendations)
enrichment = budget['enrichment']
health_score = enrichment['health_score']['score']  # 0-10
issues = enrichment['issues']                        # List of budget issues
recommendations = enrichment['recommendations']      # List of optimization tips
```

### Important Notes

**⚠️ DO NOT:**
- Don't call individual services directly (flights_service, hotels_service, etc.)
- Don't call enrichers separately - orchestrator handles everything
- Don't forget to convert Pydantic model to dict using `.model_dump()`

**✅ DO:**
- Only call `orchestrator.plan_trip_from_text(query)`
- Convert response to dict for UI rendering
- Handle 8-10 minute execution time (show loading spinner)
- Cache results to avoid re-processing same queries

### Integration Examples

#### Streamlit
```python
import streamlit as st
result = orchestrator.plan_trip_from_text(user_query)
trip_data = result["trip"].model_dump()
st.write(trip_data)
```

#### Flask API
```python
@app.route('/api/plan-trip', methods=['POST'])
def plan_trip():
    query = request.json['query']
    result = orchestrator.plan_trip_from_text(query)
    trip_data = result["trip"].model_dump()
    return jsonify({'trip': trip_data, 'narrative': result["narrative"]})
```

#### FastAPI
```python
@app.post("/api/plan-trip")
async def plan_trip(query: str):
    result = orchestrator.plan_trip_from_text(query)
    trip_data = result["trip"].model_dump()
    return {'trip': trip_data, 'narrative': result["narrative"]}
```
