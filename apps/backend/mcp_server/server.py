"""
MCP Tool Server for TravelGuru v5.
Exposes flight and hotel search tools via MCP protocol.
This is a thin tool-exposure layer with no business logic.
"""

import sys
from pathlib import Path

# Add project root to Python path
# File is at: travelguru-v5/backend/app/mcp/server.py
# We need: travelguru-v5/ to be in path for "from app..." imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.logging import setup_logging
setup_logging(level="INFO")

import logging
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from app.tools.flight.service import search_flights as search_flights_service
from app.tools.hotel.service import search_hotels as search_hotels_service
from app.tools.places.service import search_places as search_places_service
from app.tools.weather.service import get_weather as get_weather_service
from app.tools.budget.service import compute_budget as compute_budget_service
from app.shared.schemas import FlightOption, HotelOption, PlaceOption, WeatherInfo, BudgetSummary

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("TravelGuru Tools")


@mcp.tool()
def search_flights(
    from_city: str,
    to_city: str,
    date: Optional[str] = None,
    max_price: Optional[int] = None,
    limit: int = 5,
    sort_by_price: bool = True
) -> List[FlightOption]:
    """
    Search for flights matching the specified criteria.
    
    Args:
        from_city: Departure city name
        to_city: Arrival city name
        date: Optional departure date filter (ISO 8601 format)
        max_price: Optional maximum price filter (in INR)
        limit: Maximum number of results to return (default: 5)
        sort_by_price: Whether to sort results by price ascending (default: True)
        
    Returns:
        List of FlightOption matching criteria
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if not from_city or not from_city.strip():
        raise ValueError("from_city cannot be empty")
    
    if not to_city or not to_city.strip():
        raise ValueError("to_city cannot be empty")
    
    if max_price is not None and max_price < 0:
        raise ValueError(f"max_price must be non-negative, got {max_price}")
    
    if limit < 0:
        raise ValueError(f"limit must be non-negative, got {limit}")
    
    logger.info(
        f"search_flights_tool called: from_city={from_city}, to_city={to_city}, "
        f"date={date}, max_price={max_price}, limit={limit}, sort_by_price={sort_by_price}"
    )
    
    try:
        results = search_flights_service(
            from_city=from_city.strip(),
            to_city=to_city.strip(),
            date=date,
            max_price=max_price,
            limit=limit,
            sort_by_price=sort_by_price
        )
        logger.info(f"search_flights_tool returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"search_flights_tool failed: {e}")
        raise


@mcp.tool()
def search_hotels(
    city: str,
    min_stars: Optional[int] = None,
    max_price: Optional[int] = None,
    amenities: Optional[List[str]] = None,
    limit: int = 5,
    sort_by_price: bool = True
) -> List[HotelOption]:
    """
    Search for hotels matching the specified criteria.
    
    Args:
        city: City to search hotels in
        min_stars: Optional minimum star rating filter (1-5)
        max_price: Optional maximum price per night filter (in INR)
        amenities: Optional list of required amenities
        limit: Maximum number of results to return (default: 5)
        sort_by_price: Whether to sort results by price ascending (default: True)
        
    Returns:
        List of HotelOption matching criteria
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if not city or not city.strip():
        raise ValueError("city cannot be empty")
    
    if min_stars is not None and (min_stars < 1 or min_stars > 5):
        raise ValueError(f"min_stars must be between 1 and 5, got {min_stars}")
    
    if max_price is not None and max_price < 0:
        raise ValueError(f"max_price must be non-negative, got {max_price}")
    
    if limit < 0:
        raise ValueError(f"limit must be non-negative, got {limit}")
    
    logger.info(
        f"search_hotels_tool called: city={city}, min_stars={min_stars}, "
        f"max_price={max_price}, amenities={amenities}, limit={limit}, "
        f"sort_by_price={sort_by_price}"
    )
    
    try:
        results = search_hotels_service(
            city=city.strip(),
            min_stars=min_stars,
            max_price=max_price,
            amenities=amenities,
            limit=limit,
            sort_by_price=sort_by_price
        )
        logger.info(f"search_hotels_tool returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"search_hotels_tool failed: {e}")
        raise


@mcp.tool()
def search_places(
    city: str,
    category: Optional[str] = None,
    max_entry_fee: Optional[int] = None,
    limit: int = 5,
    sort_by_fee: bool = True
) -> List[PlaceOption]:
    """
    Search for places/attractions matching the specified criteria.
    
    Args:
        city: City to search places in
        category: Optional category filter (e.g., beach, temple, museum, market)
        max_entry_fee: Optional maximum entry fee filter (in INR)
        limit: Maximum number of results to return (default: 5)
        sort_by_fee: Whether to sort results by entry fee ascending (default: True)
        
    Returns:
        List of PlaceOption matching criteria
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if not city or not city.strip():
        raise ValueError("city cannot be empty")
    
    if max_entry_fee is not None and max_entry_fee < 0:
        raise ValueError(f"max_entry_fee must be non-negative, got {max_entry_fee}")
    
    if limit < 0:
        raise ValueError(f"limit must be non-negative, got {limit}")
    
    logger.info(
        f"search_places_tool called: city={city}, category={category}, "
        f"max_entry_fee={max_entry_fee}, limit={limit}, sort_by_fee={sort_by_fee}"
    )
    
    try:
        results = search_places_service(
            city=city.strip(),
            category=category,
            max_entry_fee=max_entry_fee,
            limit=limit,
            sort_by_fee=sort_by_fee
        )
        logger.info(f"search_places_tool returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"search_places_tool failed: {e}", exc_info=True)
        raise RuntimeError(f"Tool search_places failed: {e}")


@mcp.tool()
def get_weather(
    city: str,
    month: int
) -> Optional[WeatherInfo]:
    """
    Get weather information for a specific city and month.
    
    Args:
        city: City name
        month: Month number (1-12)
        
    Returns:
        WeatherInfo if data found, None otherwise
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if not city or not city.strip():
        raise ValueError("city cannot be empty")
    
    if not isinstance(month, int) or month < 1 or month > 12:
        raise ValueError(f"month must be an integer between 1 and 12, got {month}")
    
    logger.info(f"get_weather_tool called: city={city}, month={month}")
    
    try:
        result = get_weather_service(
            city=city.strip(),
            month=month
        )
        if result:
            logger.info(f"get_weather_tool returned weather data for {city}, month {month}")
        else:
            logger.info(f"get_weather_tool returned None (no data found)")
        return result
    except Exception as e:
        logger.error(f"get_weather_tool failed: {e}", exc_info=True)
        raise RuntimeError(f"Tool get_weather failed: {e}")


@mcp.tool()
def compute_budget(
    flight: Optional[dict] = None,
    hotel: Optional[dict] = None,
    nights: int = 0,
    places: Optional[List[dict]] = None
) -> BudgetSummary:
    """
    Compute budget summary for a trip.
    
    Args:
        flight: Optional flight option as dict or FlightOption
        hotel: Optional hotel option as dict or HotelOption
        nights: Number of nights for hotel stay (must be >= 0)
        places: Optional list of places as dicts or PlaceOption instances
        
    Returns:
        BudgetSummary with cost breakdown
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if nights < 0:
        raise ValueError(f"nights must be non-negative, got {nights}")
    
    logger.info(
        f"compute_budget_tool called: flight={flight is not None}, "
        f"hotel={hotel is not None}, nights={nights}, places={len(places) if places else 0}"
    )
    
    try:
        # Convert dict inputs to Pydantic models if needed
        flight_obj = None
        if flight is not None:
            if isinstance(flight, dict):
                flight_obj = FlightOption(**flight)
            else:
                flight_obj = flight
        
        hotel_obj = None
        if hotel is not None:
            if isinstance(hotel, dict):
                hotel_obj = HotelOption(**hotel)
            else:
                hotel_obj = hotel
        
        places_obj = None
        if places is not None:
            places_obj = []
            for place in places:
                if isinstance(place, dict):
                    places_obj.append(PlaceOption(**place))
                else:
                    places_obj.append(place)
        
        result = compute_budget_service(
            flight=flight_obj,
            hotel=hotel_obj,
            nights=nights,
            places=places_obj
        )
        logger.info(f"compute_budget_tool returned total_cost={result.total_cost} {result.currency}")
        return result
    except Exception as e:
        logger.error(f"compute_budget_tool failed: {e}", exc_info=True)
        raise RuntimeError(f"Tool compute_budget failed: {e}")


# Log registered tools
logger.info("Registered tool: search_flights")
logger.info("Registered tool: search_hotels")
logger.info("Registered tool: search_places")
logger.info("Registered tool: get_weather")
logger.info("Registered tool: compute_budget")


if __name__ == "__main__":
    mcp.run()
