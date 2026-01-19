"""
Flight search service.
Business orchestrator for flight search operations.
"""

from backend.app.core.config import DEFAULT_CURRENCY
from backend.app.core.logging import get_logger
from backend.app.shared.schemas import FlightOption
from backend.app.tools.flight.adapters.api import search_flights_api
from backend.app.tools.flight.normalize import normalize_flight_offers
from backend.app.core.amadeus_iata import resolve_city_to_iata, UnknownCityError


logger = get_logger(__name__)

class FlightSearchError(RuntimeError):
    """Raised when flight search operation fails."""

    pass

def search_flights(
    from_city: str,
    to_city: str,
    date: str | None = None,
    max_price: int | None = None,
    limit: int = 5,
    sort_by_price: bool = True,
) -> list[FlightOption]:
    """
    Search for flights using Amadeus API.
    
    This is the main business orchestrator that coordinates flight search operations
    by validating inputs, calling the API adapter, normalizing results,
    and applying business logic (filtering, sorting, limiting).
    
    Args:
        from_city: Departure city name
        to_city: Arrival city name
        date: Departure date in YYYY-MM-DD format (optional)
        max_price: Maximum price filter in INR (optional)
        limit: Maximum number of results to return (default: 5)
        sort_by_price: Whether to sort by price ascending (default: True)
        
    Returns:
        List of FlightOption objects matching the search criteria
        
    Raises:
        UnknownCityError: If city names are invalid or unsupported
        FlightSearchError: If flight search operation fails
    """
    logger.info(
        f"Flight search requested: {from_city} → {to_city}, date={date}, "
        f"max_price={max_price}, limit={limit}"
    )
    
    try:
        origin_iata = resolve_city_to_iata(from_city)
        destination_iata = resolve_city_to_iata(to_city)
        
        logger.info(f"Resolved cities: {from_city} → {origin_iata}, {to_city} → {destination_iata}")
        
        raw_offers = search_flights_api(
            origin_iata=origin_iata,
            destination_iata=destination_iata,
            departure_date=date if date else "",
            adults=1,
            currency=DEFAULT_CURRENCY,
        )
        
        flights = normalize_flight_offers(raw_offers)
        
        if max_price is not None:
            logger.info(f"Filtering flights by max_price: {max_price}")
            flights = [f for f in flights if f.price <= max_price]
        
        if sort_by_price:
            flights.sort(key=lambda f: f.price)
        
        flights = flights[:limit]
        
        logger.info(f"Returning {len(flights)} flights")
        return flights
    
    except UnknownCityError as e:
        logger.error(f"City resolution failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Flight search failed: {e}")
        raise FlightSearchError(f"Failed to search flights: {e}") from e
    
    except UnknownCityError:
        # Re-raise UnknownCityError as-is for better error messages
        raise
        
    except Exception as e:
        # Log error and raise FlightSearchError
        error_msg = f"Flight search failed: {str(e)}"
        logger.error(error_msg)
        raise FlightSearchError(error_msg) from e
