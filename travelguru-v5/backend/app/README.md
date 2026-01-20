# TravelGuru v5 – Agentic AI Architecture Overview

TravelGuru v5 is a **modular, agentic AI travel planning backend**.  
Each part of the trip is handled by a **specialized intelligent agent** with:

- API integration
- Normalization layer
- Enrichment & intelligence layer
- Scoring & ranking
- Structured outputs

A **LangGraph Orchestrator** coordinates all agents to produce a full travel plan.

---

#  High-Level Flow

User Query (Natural Language)
        ↓
Planner Agent (understands intent, extracts constraints)
        ↓
Orchestrator (LangGraph)
        ↓
┌───────────────┬───────────────┬───────────────┬───────────────┐
│ Flight Agent  │ Hotel Agent   │ Places Agent  │ Weather Agent │
└───────────────┴───────────────┴───────────────┴───────────────┘
        ↓
     Budget Agent
        ↓
  Itinerary Agent
        ↓
   Composer Agent (Narrative Generator)
        ↓
   Final Travel Plan (Human-like Story)

---

#  Agents Overview

---

##  Flight Agent

### Responsibility
- Finds arrival & return flights
- Ranks them by:
  - Price
  - Duration
  - Stops
  - Convenience
  - User preferences

### Tech
- ✅ API: **Amadeus Flight API**
- ✅ NLP: `flight_intent_extractor.py`
- ✅ Enrichment: `flight_enrichment.py`
- ✅ Scoring:
  - Deal score
  - Convenience score
  - Value score
  - Match score

### Output
- Multiple ranked flight options
- Market analysis
- Price intelligence
- Recommendations

---

##  Hotel Agent

### Responsibility
- Finds hotels
- Scores them by:
  - Price
  - Rating
  - Amenities
  - Value for money
  - Budget fit

### Tech
- ✅ API: (Booking / dataset / provider API)
- ✅ Enrichment: `hotel_enrichment.py`
- ✅ NLP: `hotel_intent_extractor.py`

### Output
- Ranked hotels
- Value analysis
- Quality vs price reasoning

---

##  Places Agent

### Responsibility
- Selects best attractions
- Understands:
  - Who should visit
  - When to visit
  - Why visit
  - Crowd, weather, timing, pacing

### Tech
- ✅ API: Google Places / dataset
- ✅ NLP: `places_intent_extractor.py`
- ✅ Enrichment:
  - `places_enrichment.py`
  - Wikipedia fetcher
  - Knowledge cache
  - GPT fallback (optional)

### Output
- Deep place profiles
- Travel advice
- Day-fit analysis
- Cultural context

---

##  Weather Agent

### Responsibility
- Analyzes weather day-by-day
- Decides:
  - Which days are good/bad
  - Which activities to avoid
  - Packing list
  - Comfort scores

### Tech
- ✅ API: OpenWeather / Weather API
- ✅ Enrichment: `weather_enrichment.py`

### Output
- Daily comfort scoring
- Activity suitability
- Risk warnings
- Packing & planning advice

---

##  Budget Agent

### Responsibility
- Combines:
  - Flights
  - Hotels
  - Activities
  - Food
  - Transport
- Detects:
  - Overbudget
  - Bad allocation
  - Waste
- Simulates optimizations

### Tech
- ✅ Enrichment: `budget_enrichment.py`
- ❌ No NLP (budget intent comes from Planner)

### Output
- Full cost breakdown
- Budget health score
- Warnings
- Optimization recommendations
- Savings simulation

---

##  Itinerary Enrichment

### Responsibility
- Builds:
  - Day-by-day schedule
  - Morning / Afternoon / Evening blocks
  - Logical routing
  - Pace control

### Tech
- ✅ Enrichment: `itinerary_enrichment.py`

### Output
- Structured multi-day plan
- Day logic
- Flow optimization

---

##  Planner Agent

### Responsibility
- Understands user intent:
  - Cities
  - Dates
  - People
  - Budget
  - Style (luxury, budget, romantic, etc)
- Decides:
  - What agents to call
  - With what parameters

### Tech
- ✅ LLM: OpenAI / GPT
- ✅ Prompt: `planner.txt`
- ✅ Code: `planner_agent.py`

---

##  Composer Agent

### Responsibility
- Converts **raw agent data** into:
  - A human-readable
  - Professional
  - Story-like travel plan

### Tech
- ✅ LLM: OpenAI / GPT
- ✅ Prompt: `composer.txt`
- ✅ Code: `composer_agent.py`

### Output
- Full travel document
- Like a real travel consultant wrote it

---

#  Orchestrator (LangGraph)

### Responsibility
- Controls execution order:
  1. Planner
  2. Flights / Hotels / Places / Weather
  3. Budget
  4. Itinerary
  5. Composer

### Tech
- ✅ LangGraph
- ✅ File: `travel_planner_graph.py`

---

#  Architecture Principles

- ✅ Agents are independent
- ✅ Tools are pure Python
- ✅ LLM is only used in:
  - Planner
  - Composer
- ✅ Business logic is deterministic
- ✅ Enrichment = Intelligence Layer
- ✅ APIs are swappable

---

#  What This System Is

- Not a chatbot
- Not a prompt script
- Not a toy demo

> This is a **real AI planning engine**.

---

#  Future Extensions

- User memory & personalization
- Price tracking
- Real booking links
- Multi-city trips
- Group optimization
- Dynamic replanning

---

#  Summary

TravelGuru v5 is a **full agentic AI travel backend** that:
- Thinks
- Analyzes
- Optimizes
- Explains
- And presents like a human travel expert.
