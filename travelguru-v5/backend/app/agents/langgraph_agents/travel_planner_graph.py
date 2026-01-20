"""
TravelGuru v5 Orchestrator.
Production-grade agentic orchestration system that wires:
Planner → Services → Enrichers → Composer

This orchestrator NEVER calls LLM directly (only through agents).
This orchestrator NEVER contains business logic (only wiring).
"""

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from app.shared.schemas import (
    TripRequest,
    TripResponse,
    FlightOption,
    HotelOption,
    PlaceOption,
    WeatherSummary,
    WeatherInfo,
    BudgetSummary,
    TripPlan,
    DayPlan
)
from app.agents.langgraph_agents.planner_agent import plan_trip as planner_plan_trip
from app.agents.langgraph_agents.composer_agent import ComposerAgent

# Services (domain logic)
from app.agents.langgraph_agents.local_tool_router import call_local_tool

# Enrichers (postprocessing)
from app.agents.postprocessing.flight_enrichment import enrich_flights
from app.agents.postprocessing.hotel_enrichment import enrich_hotels
from app.agents.postprocessing.places_enrichment import enrich_places
from app.agents.postprocessing.weather_enrichment import enrich_weather_forecast
from app.agents.postprocessing.budget_enrichment import enrich_budget
from app.agents.postprocessing.itinerary_enrichment import enrich_itinerary

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS FOR UNWRAPPING ENRICHED RESULTS
# ============================================================================

def _unwrap_flight_results(result):
    """Extract list from FlightEnrichmentResult or return as-is if already a list."""
    if hasattr(result, 'enriched_flights'):
        return [ef.flight for ef in result.enriched_flights]
    elif isinstance(result, list):
        return result
    else:
        return []


def _unwrap_hotel_results(result):
    """Extract list from EnrichmentResult or return as-is if already a list."""
    if hasattr(result, 'enriched_hotels'):
        return [eh.hotel for eh in result.enriched_hotels]
    elif isinstance(result, list):
        return result
    else:
        return []


def _unwrap_places_results(result):
    """Extract list from EnrichmentResult or return as-is if already a list."""
    if hasattr(result, 'enriched_places'):
        return [ep.place for ep in result.enriched_places]
    elif isinstance(result, list):
        return result
    else:
        return []


def _unwrap_weather_results(result):
    """Extract list from TripWeatherAnalysis or return as-is if already a list."""
    if hasattr(result, 'enriched_days'):
        return [ed.weather for ed in result.enriched_days]
    elif isinstance(result, list):
        return result
    else:
        return []


class TravelPlannerOrchestrator:
    """
    Production-grade orchestrator for TravelGuru v5.
    
    Coordinates the complete travel planning pipeline:
    1. Planning (via PlannerAgent)
    2. Service calls (flights, hotels, places, weather, budget)
    3. Enrichment (domain-specific postprocessing)
    4. Itinerary building (deterministic day-by-day planning)
    5. Composition (narrative generation via ComposerAgent)
    
    This is PURE ORCHESTRATION. No LLM calls. No business logic.
    """
    
    def __init__(self):
        """Initialize orchestrator with composer agent."""
        self.composer = ComposerAgent()
        logger.info("TravelPlannerOrchestrator initialized")
    
    def plan_trip_from_text(self, query: str) -> Dict[str, Any]:
        """
        Plan trip from natural language query.
        
        This method:
        1. Calls planner agent to understand the query
        2. Extracts trip metadata from planner output
        3. Creates TripRequest with extracted data
        4. Calls plan_trip() with the structured request
        
        Args:
            query: User's travel request in natural language
            
        Returns:
            Dict with trip_response, narrative, planner_output, and debug info
            
        Raises:
            ValueError: If query is empty or planner fails
            RuntimeError: If planning fails
        """
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        
        logger.info(f"Planning trip from text: {query}")
        start_time = time.time()
        
        # Step 1: Call planner agent to understand the query
        planner_output = planner_plan_trip(query)
        
        if not planner_output:
            raise ValueError("Planner failed to generate output")
        
        # Step 2: Extract trip metadata from planner output
        request = self._extract_trip_metadata_from_plan(planner_output)
        
        # Step 3: Call plan_trip with structured request
        result = self.plan_trip(request, planner_output=planner_output)
        
        # Add planner output to result for debugging
        result["planner_output"] = planner_output
        
        if "debug" in result:
            result["debug"]["timings"]["planner"] = time.time() - start_time
        
        return result
    
    def _extract_trip_metadata_from_plan(self, planner_output) -> TripRequest:
        """
        Extract TripRequest fields from planner output.
        
        This converts the planner's analysis into structured fields.
        Uses smart defaults when information is missing.
        
        Args:
            planner_output: Output from planner agent
            
        Returns:
            TripRequest with extracted/inferred fields
        """
        # Debug: Log planner output structure
        logger.info(f"Planner output has {len(planner_output.tool_calls)} tool calls")
        for tc in planner_output.tool_calls:
            logger.info(f"Tool: {tc.tool_name}, Args: {tc.arguments}")
        
        # Extract from tool_calls
        from_city = None
        to_city = None
        start_date = None
        end_date = None
        budget = 50000  # Default budget
        travelers = 1  # Default travelers
        
        # Iterate through tool calls to extract parameters
        for tool_call in planner_output.tool_calls:
            tool_name = tool_call.tool_name
            tool_args = tool_call.arguments
            
            if tool_name == "search_flights":
                from_city = tool_args.get("from_city")
                to_city = tool_args.get("to_city")
                start_date = tool_args.get("date")
                travelers = tool_args.get("adults", travelers)
            
            elif tool_name == "search_hotels":
                if not to_city:
                    to_city = tool_args.get("city")
                # Hotels typically don't have check-in/out in planner output
                # We'll calculate end_date from days
            
            elif tool_name == "compute_budget":
                nights = tool_args.get("nights")
                if nights and start_date:
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        end_dt = start_dt + timedelta(days=nights)
                        end_date = end_dt.strftime("%Y-%m-%d")
                    except:
                        pass
        
        # Extract preferences from planner reasoning if available
        preferences = {}
        if hasattr(planner_output, 'reasoning') and planner_output.reasoning:
            reasoning_lower = planner_output.reasoning.lower()
            if 'luxury' in reasoning_lower or 'premium' in reasoning_lower:
                preferences['budget_preference'] = 'luxury'
                preferences['accommodation_preference'] = 'luxury'
            elif 'budget' in reasoning_lower or 'cheap' in reasoning_lower:
                preferences['budget_preference'] = 'budget'
        
        # Calculate end_date if not provided (assume 3 nights)
        if start_date and not end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=3)
                end_date = end_dt.strftime("%Y-%m-%d")
            except:
                pass
        
        # Validate required fields
        if not from_city:
            raise ValueError("Could not extract origin city from query")
        if not to_city:
            raise ValueError("Could not extract destination city from query")
        if not start_date:
            raise ValueError("Could not extract travel date from query")
        if not end_date:
            end_date = start_date  # Same day trip if no end date
        
        logger.info(f"Extracted: {from_city} → {to_city}, {start_date} to {end_date}, {travelers} travelers, ₹{budget}")
        
        return TripRequest(
            from_city=from_city,
            to_city=to_city,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            travelers=travelers,
            preferences=preferences if preferences else None
        )
    
    def plan_trip(self, request: TripRequest, planner_output=None) -> Dict[str, Any]:
        """
        Plan trip from structured request.
        
        This is the main orchestration method that:
        1. Calls planner
        2. Executes services
        3. Applies enrichments
        4. Builds itinerary
        5. Generates narrative
        
        Args:
            request: Structured trip request
            
        Returns:
            Dict with:
                - trip: TripResponse object
                - narrative: str (final output)
                - debug: Dict (timings, counts, warnings)
                
        Raises:
            RuntimeError: If any critical step fails
        """
        start_time = time.time()
        debug = {
            "timings": {},
            "counts": {},
            "warnings": []
        }
        
        logger.info("=== STARTING TRAVEL PLANNING ORCHESTRATION ===")
        
        try:
            # Step 1: Planning (use provided or generate query from request)
            if planner_output:
                plan = planner_output
                plan_time = 0  # Already computed
                logger.info("Using pre-computed planner output")
            else:
                # Build query from request
                query = self._build_query_from_request(request)
                plan, plan_time = self._run_planner(query, debug)
                debug["timings"]["planner"] = plan_time
            
            # Step 2: Execute services (flights, hotels, places, weather)
            # Store both enriched and unwrapped versions
            flights_enriched, flights_time = self._run_flights(plan, debug)
            flights = _unwrap_flight_results(flights_enriched)  # For schema compatibility
            debug["timings"]["flights"] = flights_time
            debug["counts"]["flights"] = len(flights) if flights else 0
            debug["enriched"] = {}  # Store enriched data for display
            debug["enriched"]["flights"] = flights_enriched
            
            hotels_enriched, hotels_time = self._run_hotels(plan, debug)
            hotels = _unwrap_hotel_results(hotels_enriched)  # For schema compatibility
            debug["timings"]["hotels"] = hotels_time
            debug["counts"]["hotels"] = len(hotels) if hotels else 0
            debug["enriched"]["hotels"] = hotels_enriched
            
            places_enriched, places_time = self._run_places(plan, debug)
            places = _unwrap_places_results(places_enriched)  # For schema compatibility
            debug["timings"]["places"] = places_time
            debug["counts"]["places"] = len(places) if places else 0
            debug["enriched"]["places"] = places_enriched
            
            weather_enriched, weather_time = self._run_weather(plan, debug)
            weather = _unwrap_weather_results(weather_enriched)  # For schema compatibility
            debug["timings"]["weather"] = weather_time
            debug["counts"]["weather"] = len(weather) if weather else 0
            debug["enriched"]["weather"] = weather_enriched
            
            # Step 3: Compute budget
            budget_summary, budget_time = self._run_budget(
                plan, flights, hotels, places, debug
            )
            debug["timings"]["budget"] = budget_time
            debug["enriched"]["budget"] = budget_summary  # Store budget analysis for composer
            
            # Step 4: Build itinerary (deterministic planning)
            trip_response, itinerary_time = self._build_itinerary(
                plan, flights, hotels, places, weather, budget_summary, debug
            )
            debug["timings"]["itinerary"] = itinerary_time
            
            # Step 5: Generate narrative
            narrative, compose_time = self._run_composer(trip_response, debug)
            debug["timings"]["composer"] = compose_time
            
            # Calculate total time
            total_time = time.time() - start_time
            debug["timings"]["total"] = total_time
            
            logger.info(f"=== ORCHESTRATION COMPLETE ({total_time:.2f}s) ===")
            
            return {
                "trip": trip_response,
                "narrative": narrative,
                "debug": debug
            }
        
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            raise RuntimeError(f"Travel planning orchestration failed: {e}") from e
    
    def _build_query_from_request(self, request: TripRequest) -> str:
        """
        Build natural language query from structured TripRequest.
        
        This is used when calling plan_trip() directly with a TripRequest.
        
        Args:
            request: Structured trip request
            
        Returns:
            Natural language query string
        """
        query_parts = [
            f"Plan a trip from {request.from_city} to {request.to_city}",
            f"from {request.start_date} to {request.end_date}",
            f"for {request.travelers} traveler{'s' if request.travelers > 1 else ''}",
            f"with a budget of ₹{request.budget}"
        ]
        
        if request.preferences:
            prefs = request.preferences
            if prefs.get('accommodation_preference'):
                query_parts.append(f"preferring {prefs['accommodation_preference']} accommodation")
            if prefs.get('budget_preference'):
                query_parts.append(f"({prefs['budget_preference']} budget)")
        
        return ". ".join(query_parts) + "."
    
    def _run_planner(
        self,
        query: str,
        debug: Dict[str, Any]
    ) -> tuple[Any, float]:
        """
        Execute planner agent.
        
        Args:
            query: User query
            debug: Debug dict for warnings
            
        Returns:
            Tuple of (plan, execution_time)
            
        Raises:
            RuntimeError: If planner fails
        """
        logger.info("Step 1: Running planner")
        start = time.time()
        
        try:
            plan = planner_plan_trip(query)
            
            if not plan or not plan.tool_calls:
                debug["warnings"].append("Planner returned empty plan")
                raise RuntimeError("Planner returned empty plan")
            
            elapsed = time.time() - start
            logger.info(f"Planner complete: {len(plan.tool_calls)} tool calls ({elapsed:.2f}s)")
            return plan, elapsed
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Planner failed: {e}")
            raise RuntimeError(f"Planner failed: {e}") from e
    
    def _run_flights(
        self,
        plan: Any,
        debug: Dict[str, Any]
    ) -> tuple[List[FlightOption] | None, float]:
        """
        Execute flight search service and apply enrichment.
        
        Args:
            plan: Planner output
            debug: Debug dict for warnings
            
        Returns:
            Tuple of (flights, execution_time)
        """
        logger.info("Step 2a: Running flight search")
        start = time.time()
        
        try:
            # Find flight tool call in plan
            flight_tool = next(
                (tc for tc in plan.tool_calls if tc.tool_name == "search_flights"),
                None
            )
            
            if not flight_tool:
                debug["warnings"].append("No flight search in plan")
                logger.warning("No flight search requested")
                return None, time.time() - start
            
            # Call service
            flights_raw = call_local_tool("search_flights", flight_tool.arguments)
            
            # Apply enrichment
            if flights_raw and len(flights_raw) > 0:
                flights_enriched = enrich_flights(flights_raw)
                logger.info(f"Enriched {len(flights_raw)} flights")
            else:
                flights_enriched = None
            
            elapsed = time.time() - start
            logger.info(f"Flight search complete: {len(flights_raw) if flights_raw else 0} results ({elapsed:.2f}s)")
            return flights_enriched, elapsed
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Flight search failed: {e}")
            debug["warnings"].append(f"Flight search failed: {e}")
            return None, elapsed
    
    def _run_hotels(
        self,
        plan: Any,
        debug: Dict[str, Any]
    ) -> tuple[List[HotelOption] | None, float]:
        """
        Execute hotel search service and apply enrichment.
        
        Args:
            plan: Planner output
            debug: Debug dict for warnings
            
        Returns:
            Tuple of (hotels, execution_time)
        """
        logger.info("Step 2b: Running hotel search")
        start = time.time()
        
        try:
            # Find hotel tool call in plan
            hotel_tool = next(
                (tc for tc in plan.tool_calls if tc.tool_name == "search_hotels"),
                None
            )
            
            if not hotel_tool:
                debug["warnings"].append("No hotel search in plan")
                logger.warning("No hotel search requested")
                return None, time.time() - start
            
            # Call service
            hotels_raw = call_local_tool("search_hotels", hotel_tool.arguments)
            
            # Apply enrichment
            if hotels_raw and len(hotels_raw) > 0:
                hotels_enriched = enrich_hotels(hotels_raw)
                logger.info(f"Enriched {len(hotels_raw)} hotels")
            else:
                hotels_enriched = None
            
            elapsed = time.time() - start
            logger.info(f"Hotel search complete: {len(hotels_raw) if hotels_raw else 0} results ({elapsed:.2f}s)")
            return hotels_enriched, elapsed
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Hotel search failed: {e}")
            debug["warnings"].append(f"Hotel search failed: {e}")
            return None, elapsed
    
    def _run_places(
        self,
        plan: Any,
        debug: Dict[str, Any]
    ) -> tuple[List[PlaceOption] | None, float]:
        """
        Execute places search service and apply enrichment.
        
        Args:
            plan: Planner output
            debug: Debug dict for warnings
            
        Returns:
            Tuple of (places, execution_time)
        """
        logger.info("Step 2c: Running places search")
        start = time.time()
        
        try:
            # Find places tool call in plan
            places_tool = next(
                (tc for tc in plan.tool_calls if tc.tool_name == "search_places"),
                None
            )
            
            if not places_tool:
                debug["warnings"].append("No places search in plan")
                logger.warning("No places search requested")
                return None, time.time() - start
            
            # Call service
            places_raw = call_local_tool("search_places", places_tool.arguments)
            
            # Apply enrichment
            if places_raw and len(places_raw) > 0:
                places_enriched = enrich_places(places_raw)
                logger.info(f"Enriched {len(places_raw)} places")
            else:
                places_enriched = None
            
            elapsed = time.time() - start
            logger.info(f"Places search complete: {len(places_raw) if places_raw else 0} results ({elapsed:.2f}s)")
            return places_enriched, elapsed
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Places search failed: {e}")
            debug["warnings"].append(f"Places search failed: {e}")
            return None, elapsed
    
    def _run_weather(
        self,
        plan: Any,
        debug: Dict[str, Any]
    ) -> tuple[List[WeatherSummary] | None, float]:
        """
        Execute weather forecast service and apply enrichment.
        
        Args:
            plan: Planner output
            debug: Debug dict for warnings
            
        Returns:
            Tuple of (weather, execution_time)
        """
        logger.info("Step 2d: Running weather forecast")
        start = time.time()
        
        try:
            # Find weather tool call in plan
            weather_tool = next(
                (tc for tc in plan.tool_calls if tc.tool_name == "get_weather_forecast"),
                None
            )
            
            if not weather_tool:
                debug["warnings"].append("No weather forecast in plan")
                logger.warning("No weather forecast requested")
                return None, time.time() - start
            
            # Call service
            weather_raw = call_local_tool("get_weather_forecast", weather_tool.arguments)
            
            # Apply enrichment
            if weather_raw and len(weather_raw) > 0:
                weather_enriched = enrich_weather_forecast(weather_raw)
                logger.info(f"Enriched {len(weather_raw)} weather forecasts")
            else:
                weather_enriched = None
            
            elapsed = time.time() - start
            logger.info(f"Weather forecast complete: {len(weather_raw) if weather_raw else 0} results ({elapsed:.2f}s)")
            return weather_enriched, elapsed
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Weather forecast failed: {e}")
            debug["warnings"].append(f"Weather forecast failed: {e}")
            return None, elapsed
    
    def _run_budget(
        self,
        plan: Any,
        flights: List[FlightOption] | None,
        hotels: List[HotelOption] | None,
        places: List[PlaceOption] | None,
        debug: Dict[str, Any]
    ) -> tuple[BudgetSummary | None, float]:
        """
        Execute budget computation service and apply enrichment.
        
        Args:
            plan: Planner output
            flights: Flight results
            hotels: Hotel results
            places: Places results
            debug: Debug dict for warnings
            
        Returns:
            Tuple of (budget_summary, execution_time)
        """
        logger.info("Step 3: Running budget computation")
        start = time.time()
        
        try:
            # Find budget tool call in plan
            budget_tool = next(
                (tc for tc in plan.tool_calls if tc.tool_name == "compute_budget"),
                None
            )
            
            if not budget_tool:
                debug["warnings"].append("No budget computation in plan")
                logger.warning("No budget computation requested")
                return None, time.time() - start
            
            # Prepare arguments with actual data
            args = budget_tool.arguments.copy()
            args["flight"] = flights[0] if flights and len(flights) > 0 else None
            args["hotel"] = hotels[0] if hotels and len(hotels) > 0 else None
            args["places"] = places if places else []
            
            # Call service (enrichment is built-in to compute_budget)
            budget_summary = call_local_tool("compute_budget", args)
            
            elapsed = time.time() - start
            logger.info(f"Budget computation complete ({elapsed:.2f}s)")
            return budget_summary, elapsed
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Budget computation failed: {e}")
            debug["warnings"].append(f"Budget computation failed: {e}")
            return None, elapsed
    
    def _build_itinerary(
        self,
        plan: Any,
        flights: List[FlightOption] | None,
        hotels: List[HotelOption] | None,
        places: List[PlaceOption] | None,
        weather: List[WeatherSummary] | None,
        budget_summary: BudgetSummary | None,
        debug: Dict[str, Any]
    ) -> tuple[TripResponse, float]:
        """
        Build enriched itinerary and create TripResponse.
        
        Args:
            plan: Planner output (for fallback date extraction)
            flights: Flight results
            hotels: Hotel results
            places: Places results
            weather: Weather results
            budget_summary: Budget summary
            debug: Debug dict for warnings
            
        Returns:
            Tuple of (trip_response, execution_time)
            
        Raises:
            RuntimeError: If itinerary building fails
        """
        logger.info("Step 4: Building enriched itinerary")
        start = time.time()
        
        try:
            # ROBUST DATE DERIVATION with multiple fallbacks:
            # Priority 1: Hotel check-in/check-out (most reliable for trip duration)
            # Priority 2: Flight departure/arrival dates
            # Priority 3: Planner tool arguments (start_date, end_date)
            dates = []
            flight = flights[0] if flights and len(flights) > 0 else None
            hotel = hotels[0] if hotels and len(hotels) > 0 else None
            
            # Try hotel check-in/out first (best for trip duration)
            if hotel and hasattr(hotel, "check_in") and hasattr(hotel, "check_out"):
                try:
                    check_in = datetime.strptime(hotel.check_in, "%Y-%m-%d") if isinstance(hotel.check_in, str) else hotel.check_in
                    check_out = datetime.strptime(hotel.check_out, "%Y-%m-%d") if isinstance(hotel.check_out, str) else hotel.check_out
                    current = check_in
                    while current <= check_out:
                        dates.append(current.strftime("%Y-%m-%d"))
                        current += timedelta(days=1)
                    logger.info(f"Derived {len(dates)} dates from hotel check-in/out")
                except Exception as e:
                    logger.warning(f"Hotel date extraction failed: {e}")
            
            # Fallback to flight dates if hotel dates unavailable
            if not dates and flight:
                # Try departure_time/arrival_time (string ISO format: "2026-02-14T21:35:00")
                if hasattr(flight, "departure_time") and hasattr(flight, "arrival_time"):
                    try:
                        # Parse ISO string to datetime first
                        if isinstance(flight.departure_time, str):
                            start_dt = datetime.fromisoformat(flight.departure_time.replace('Z', '+00:00'))
                            start_date = start_dt.date()
                        else:
                            start_date = flight.departure_time.date() if hasattr(flight.departure_time, 'date') else flight.departure_time
                        
                        if isinstance(flight.arrival_time, str):
                            end_dt = datetime.fromisoformat(flight.arrival_time.replace('Z', '+00:00'))
                            end_date = end_dt.date()
                        else:
                            end_date = flight.arrival_time.date() if hasattr(flight.arrival_time, 'date') else flight.arrival_time
                        
                        current = start_date
                        while current <= end_date:
                            dates.append(current.strftime("%Y-%m-%d"))
                            current += timedelta(days=1)
                        logger.info(f"Derived {len(dates)} dates from flight times")
                    except Exception as e:
                        logger.warning(f"Flight time extraction failed: {e}")
                
                # Fallback: try departure_date/return_date if they exist
                if not dates and hasattr(flight, "departure_date") and hasattr(flight, "return_date"):
                    try:
                        start_date = datetime.strptime(flight.departure_date, "%Y-%m-%d") if isinstance(flight.departure_date, str) else flight.departure_date
                        end_date = datetime.strptime(flight.return_date, "%Y-%m-%d") if isinstance(flight.return_date, str) else flight.return_date
                        current = start_date
                        while current <= end_date:
                            dates.append(current.strftime("%Y-%m-%d"))
                            current += timedelta(days=1)
                        logger.info(f"Derived {len(dates)} dates from flight date fields")
                    except Exception as e:
                        logger.warning(f"Flight date field extraction failed: {e}")
            
            # Final fallback: extract from planner tool arguments
            if not dates and plan and hasattr(plan, "tool_calls"):
                for tool_call in plan.tool_calls:
                    if tool_call.tool_name == "search_flights":
                        args = tool_call.arguments
                        if "start_date" in args and "end_date" in args:
                            try:
                                start_date = datetime.strptime(args["start_date"], "%Y-%m-%d")
                                end_date = datetime.strptime(args["end_date"], "%Y-%m-%d")
                                current = start_date
                                while current <= end_date:
                                    dates.append(current.strftime("%Y-%m-%d"))
                                    current += timedelta(days=1)
                                logger.info(f"Derived {len(dates)} dates from planner arguments")
                                break
                            except Exception as e:
                                logger.warning(f"Planner date extraction failed: {e}")
            
            if not dates:
                debug["warnings"].append("Could not derive trip dates from any source")
                logger.warning("No dates available for itinerary building")
                # Create a minimal date range as fallback
                today = datetime.now()
                for i in range(3):  # Default 3-day trip
                    dates.append((today + timedelta(days=i)).strftime("%Y-%m-%d"))
                logger.info(f"Using fallback dates: {dates}")
            
            # Validate dates
            if not dates or len(dates) == 0:
                raise ValueError("Cannot build itinerary without dates")
            
            # Get places and weather
            places_list = places if places else []
            weather_list = weather if weather else []
            
            # Extract budget info from BudgetSummary (no duplication)
            budget_total = budget_summary.total_cost if budget_summary else 0
            
            # Use BudgetSummary.spent_on_fixed directly (NO manual calculation)
            # BudgetEnrichment already computes this as flights + hotel
            budget_spent = 0
            if budget_summary and hasattr(budget_summary, "enrichment") and budget_summary.enrichment:
                # Prefer enriched spent_on_fixed from budget analysis
                if hasattr(budget_summary.enrichment, "cost_breakdown"):
                    breakdown = budget_summary.enrichment.cost_breakdown
                    budget_spent = breakdown.flights + breakdown.hotel
                    logger.info(f"Using BudgetSummary.spent_on_fixed: {budget_spent}")
            
            # Fallback: calculate from flight + hotel if budget enrichment unavailable
            if budget_spent == 0:
                if flight and hasattr(flight, "price"):
                    budget_spent += flight.price
                if hotel and hasattr(hotel, "total_price"):
                    budget_spent += hotel.total_price
                elif hotel and hasattr(hotel, "price_per_night") and len(dates) > 0:
                    num_nights = len(dates) - 1 if len(dates) > 1 else 1
                    budget_spent += hotel.price_per_night * num_nights
                logger.info(f"Calculated budget_spent manually: {budget_spent}")
            
            # Call itinerary enrichment (places already enriched, no separate dict needed)
            enriched = enrich_itinerary(
                dates=dates,
                flight=flight,
                hotel=hotel,
                places=places_list,
                weather_summaries=weather_list,
                budget_total=budget_total,
                budget_spent_on_flight_hotel=budget_spent
            )
            
            # Build TripPlan with weather information
            # TODO: Later may want to enhance TripPlan to include:
            # - enriched_places per day
            # - weather_forecast per day (currently only in TripResponse)
            # - budget_annotations per day
            
            # Convert DaySchedule to DayPlan (schema mismatch)
            day_plans = []
            if hasattr(enriched, "day_schedules"):
                for day_schedule in enriched.day_schedules:
                    day_plan = DayPlan(
                        date=day_schedule.date,
                        activities=day_schedule.activities
                    )
                    day_plans.append(day_plan)
            
            # Convert WeatherSummary to WeatherInfo (schema mismatch)
            weather_info_list = None
            if weather_list:
                weather_info_list = []
                for ws in weather_list:
                    wi = WeatherInfo(
                        city=ws.city,
                        date=ws.date,
                        condition=ws.condition,
                        temperature_c=ws.temp_avg_c  # Use average temperature
                    )
                    weather_info_list.append(wi)
            
            trip_plan = TripPlan(
                flight=flight,
                hotel=hotel,
                days=day_plans,
                weather=weather_info_list
            )
            
            # Build comprehensive TripResponse with ALL fields
            # CRITICAL: Preserve ALL agent intelligence for composer
            trip_response = TripResponse(
                # Schema-compatible core fields
                trip_plan=trip_plan,
                budget_summary=budget_summary if budget_summary else BudgetSummary(
                    total_cost=0,
                    currency="INR",
                    flights_cost=0,
                    hotel_cost=0,
                    activities_cost=0
                ),
                total_cost=budget_total,
                currency="INR",
                narrative="",  # Will be filled by composer
                
                # Multi-agent enrichment analyses (for composer reasoning)
                flight_analysis=debug.get("enriched", {}).get("flights"),
                hotel_analysis=debug.get("enriched", {}).get("hotels"),
                places_analysis=debug.get("enriched", {}).get("places"),
                weather_analysis=debug.get("enriched", {}).get("weather"),
                budget_analysis=debug.get("enriched", {}).get("budget"),
                itinerary_enrichment=enriched,  # Full itinerary intelligence
            )
            
            # NOTE: Current TripResponse schema only has: trip_plan, budget_summary, total_cost, currency, narrative
            # If UI needs weather/places/flights/hotels separately, update shared/schemas.py first
            
            elapsed = time.time() - start
            logger.info(f"Itinerary building complete ({elapsed:.2f}s)")
            return trip_response, elapsed
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Itinerary building failed: {e}", exc_info=True)
            raise RuntimeError(f"Itinerary building failed: {e}") from e
    
    def _run_composer(
        self,
        trip_response: TripResponse,
        debug: Dict[str, Any]
    ) -> tuple[str, float]:
        """
        Generate narrative via composer agent.
        
        Args:
            trip_response: Complete trip response
            debug: Debug dict for warnings
            
        Returns:
            Tuple of (narrative, execution_time)
            
        Raises:
            RuntimeError: If composition fails
        """
        logger.info("Step 5: Running composer")
        start = time.time()
        
        try:
            narrative = self.composer.compose(trip_response)
            
            elapsed = time.time() - start
            logger.info(f"Composition complete: {len(narrative)} chars ({elapsed:.2f}s)")
            return narrative, elapsed
        
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Composition failed: {e}")
            debug["warnings"].append(f"Composition failed: {e}")
            raise RuntimeError(f"Composition failed: {e}") from e


# ============================================================================
# PUBLIC API - Product Entrypoint
# ============================================================================

_orchestrator = TravelPlannerOrchestrator()


def generate_trip_plan(user_query: str = None, trip_request: TripRequest = None) -> dict:
    """
    Public API for generating a full trip plan.
    
    This is the PRODUCT ENTRYPOINT - what UI / Streamlit / API / CLI should call.
    
    Architecture:
        UI (Streamlit / API)
                ↓
        generate_trip_plan()   ← (PUBLIC PRODUCT API)
                ↓
        TravelPlannerOrchestrator
                ↓
        Planner → Tools → Enrichers → Itinerary → Composer
    
    Args:
        user_query: User's travel request in natural language (optional if trip_request provided)
        trip_request: Structured TripRequest object (optional if user_query provided)
        
    Returns:
        Dict containing:
            - narrative (str): Human-readable trip description
            - trip (TripResponse): Structured trip data with flights, hotels, etc.
            - debug (dict): Debug information including timings and metadata
            
    Raises:
        ValueError: If both user_query and trip_request are None
        RuntimeError: If planning fails
        
    Example:
        >>> # Using natural language
        >>> result = generate_trip_plan("Plan a 3-day trip to Paris from London")
        >>> 
        >>> # Using structured request (RECOMMENDED for better accuracy)
        >>> from app.shared.schemas import TripRequest
        >>> req = TripRequest(
        ...     from_city="Delhi",
        ...     to_city="Goa",
        ...     start_date="2026-01-22",
        ...     end_date="2026-01-24",
        ...     budget=100000,
        ...     travelers=2
        ... )
        >>> result = generate_trip_plan(trip_request=req)
        >>> print(result["narrative"])
        >>> print(result["trip"].trip_plan.days)
        >>> print(result["debug"]["timings"])
    """
    if not user_query and not trip_request:
        raise ValueError("Either user_query or trip_request must be provided")
    
    # Use structured request if provided (more accurate)
    if trip_request:
        result = _orchestrator.plan_trip(trip_request)
    else:
        # Fall back to natural language extraction
        result = _orchestrator.plan_trip_from_text(user_query)
    
    return {
        "narrative": result["narrative"],
        "trip": result["trip"],
        "debug": result["debug"]
    }


# ============================================================================
# Legacy function interface for backward compatibility
# ============================================================================


def run_travel_planner(user_query: str) -> str:
    """
    Legacy interface for running travel planner.
    
    Returns only the narrative string for backward compatibility with existing tests.
    
    For new code, use generate_trip_plan() instead to get structured output.
    
    Args:
        user_query: User's travel request
        
    Returns:
        Final narrative string
        
    Raises:
        ValueError: If query is empty
        RuntimeError: If planning fails
    """
    return generate_trip_plan(user_query)["narrative"]
