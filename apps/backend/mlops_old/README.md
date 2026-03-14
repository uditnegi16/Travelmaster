# TravelGuru – MLOps Pipeline (End‑to‑End)

This document describes **all MLOps work completed so far** in the TravelGuru project.
It is written so that **any developer can clone the repo, understand the system, and run it on a new machine without prior context**.

---

## 1. Project Purpose

The MLOps layer of TravelGuru is responsible for:

* Training **ML‑based recommendation models** (Flights & Hotels)
* Managing **offline experiments and artifacts**
* Serving **online ranking & scoring APIs**
* Acting as a **bridge between Agents and ML models**
* Ensuring the system remains **agent‑agnostic, testable, and production‑ready**

The system is designed so that:

> **Agents discover options** → **MLOps ranks & scores them** → **UI shows recommendations**

---

## 2. Evolution of the System

### Phase 1 – Data & Training (Offline MLOps)

1. Dummy / historical travel data was collected
2. Data stored in **Supabase** (used as the primary database)
3. Data pulled into notebooks for:

   * EDA
   * Feature engineering
   * Target definition
4. Separate ML models trained for:

   * Flights recommendation
   * Hotels recommendation
5. Models tracked using **MLflow**
6. Artifacts saved:

   * Preprocessors
   * Feature configs
   * Scoring logic

This phase is **complete and frozen**.

---

### Phase 2 – Online MLOps (Serving & Ranking)

Offline‑trained models were wrapped into **deterministic Python pipelines** that:

* Accept structured candidate options
* Normalize features
* Score each option
* Rank results

These pipelines are exposed via **FastAPI** for real‑time use.

---

### Phase 3 – Agent‑Ready Refactor (Current)

The system was refactored so that:

* Agents (LLM / API based) provide **raw options**
* MLOps **does NOT fetch from DB anymore** for online flow
* DB is now used only for:

  * Training
  * Monitoring
  * Logging

MLOps now acts as a **pure scoring & ranking engine**.

---

## 3. Folder‑by‑Folder Explanation (mlops/)

### mlops/api/

**Purpose:** Public FastAPI layer

Files:

* `main.py`

  * Initializes FastAPI app
  * Adds CORS
  * Registers routes

* `plan_trip.py`

  * Core orchestration endpoint `/plan-trip`
  * Flow:

    1. Receive user input
    2. Call Agent via adapter
    3. Validate agent output
    4. Rank flights & hotels
    5. Return structured response

* `schemas.py`

  * Request schemas for APIs
  * Defines `PlanTripRequest`

---

### mlops/adapters/

**Purpose:** Isolation layer between MLOps and Agents

Files:

* `agent_adapter.py`

  * Calls agent endpoint
  * Validates agent response using strict schema
  * Logs latency & failures
  * Provides **fallback response** if agent fails

This guarantees:

> MLOps never crashes because an agent fails.

---

### mlops/contracts/

**Purpose:** Hard contracts between Agent → MLOps → UI

Files:

* `agent_output_schema.py`

  * Defines EXACT structure agent must return
  * Flights, Hotels, Places, Weather

* `trip_input_schema.py`

  * Defines normalized user input

* `recommendation_response_schema.py`

  * Defines final API response format

---

### mlops/pipelines/

**Purpose:** ML scoring & ranking logic

Files:

* `flight_ranking.py`

  * Loads trained flight model
  * Scores candidate flights

* `hotel_ranking.py`

  * Loads trained hotel model
  * Scores candidate hotels

* `pipelines.py`

  * Public functions:

    * `recommend_flights()`
    * `recommend_hotels()`

No agent logic exists here.
No DB access exists here.

---

### mlops/components/

**Purpose:** Supporting MLOps components

* `training/` – training scripts (offline only)
* `monitoring/` – drift & metrics logging
* `evaluation/` – offline evaluation utilities

---

### mlops/artifacts/

**Purpose:** Stored ML artifacts

* Preprocessors
* Feature definitions
* Drift reports

Generated automatically by training & monitoring jobs.

---

### mlops/logs/

* Central logging (`mlops.log`)
* Agent latency & failure logs

---

### mlops/mlruns/

* MLflow experiment tracking
* Offline & online runs

---

## 4. Online Execution Flow (Exact)

```
Streamlit UI
   ↓
POST /plan-trip
   ↓
api/plan_trip.py
   ↓
AgentAdapter.call_agent()
   ↓
Agent (real or mock)
   ↓
AgentOutputSchema validation
   ↓
recommend_flights()
recommend_hotels()
   ↓
Ranked recommendations
   ↓
JSON response to UI
```

---

## 5. What the Agent Must Do (Strict)

Agent responsibility:

* Discover available options
* Add booking links
* Add prices, currency

Agent **must return exactly**:

```
{
  flights: [...],
  hotels: [...],
  places: [...],
  weather: {...}
}
```

No ranking.
No filtering.
No ML logic.

---

## 6. What MLOps Does (Strict)

* Validate agent output
* Normalize features
* Score options
* Rank options
* Log metrics
* Handle failures gracefully

---

## 7. Running the System (Local)

### Prerequisites

* Python 3.10+
* pip
* Node.js (only if UI used)

---

### Step 1 –# activate virtualenv and Install Dependencies
```bash
 cd TravelGuru
 .\venv\scripts\activate
pip install -r requirements.txt
```
---

### Step 2 – Start Agent (for testing)

```bash
cd D:\labmentix\major\TravelGuru\travelguru-v5\backend
uvicorn app.agents.langgraph_agents.api:app --host 0.0.0.0 --port 8001 --reload
```

---

### Step 3 – Start MLOps Backend


```bash
cd mlops
uvicorn api.main:app --reload --port 8000
```

---

### Step 4 – Start Streamlit UI

```bash
cd ..\frontend
streamlit run app.py
```

---

## 8. Current Status

✅ Offline ML training complete
✅ Online ML pipelines stable
✅ Agent adapter implemented
✅ Mock agent tested
✅ Streamlit integrated

---

## 9. What Is NOT Done Yet

* Real agent integration (only mock tested)
* Contract tests automation
* Load testing
* Production deployment

---

## 10. Next Planned Work

1. Contract tests for agent output
2. Agent failure replay tests
3. Agent latency metrics in MLflow
4. Replace mock agent with real agent

---

## Final Note

This MLOps system is **agent‑agnostic, production‑safe, and extensible**.

Any agent team can integrate by **only respecting the output schema**.

No internal MLOps changes are required.
