# Agent Service — Setup & Run

## 1. Install dependencies
```bash
pip install fastapi uvicorn amadeus openai requests python-dotenv python-jose pydantic
```

## 2. Configure environment
```bash
cp .env.example .env
# Fill in your keys in .env
```

## 3. Run
```bash
# From the project root (one level above agent_in_update/)
uvicorn agent_in_update.langgraph_agents.api:app --reload --port 8001
```

## Amadeus keys — test vs production
- **Test (sandbox)**: Set `AMADEUS_HOSTNAME=test` — limited routes, no real bookings
- **Production**: Set `AMADEUS_HOSTNAME=production` — full data, requires approval

**Sandbox limitations** (why flights/hotels may return empty):
- Only specific city pairs have data (e.g., MAD→NYC, LON→NYC)
- Indian routes (DEL→GOI) may return empty — this is expected in sandbox
- Use `USE_AMADEUS_API=false` to force dataset fallback for testing

## Amadeus type — how to check
Look at your key on https://developers.amadeus.com/my-apps:
- If the app shows "Test" badge → use `AMADEUS_HOSTNAME=test`  
- If it shows "Production" → use `AMADEUS_HOSTNAME=production`

## Architecture
```
POST /agent/plan-trip
    → TravelPlannerOrchestrator
        → PlannerAgent (OpenAI GPT)
        → search_flights (Amadeus)
        → search_hotels (Amadeus)
        → search_places (Google Places)
        → get_weather_forecast (OpenWeather)
        → compute_budget
        → ComposerAgent (OpenAI GPT)
    → Returns: flights, hotels, places, weather, budget, narrative
```
