"""
Hotel Search API Adapter.

This module is a pure API adapter for the Amadeus Hotel Search using the correct 2-step flow.
It handles direct communication with the Amadeus API and returns raw JSON data.

IMPORTANT: Amadeus hotel search requires two steps:
1. Get hotel IDs by city (reference-data/locations/hotels/by-city)
2. Get offers for those hotel IDs (shopping/hotel-offers)

Responsibilities:
- Execute 2-step Amadeus hotel search flow
- Validate and sanitize input parameters
- Handle API errors gracefully
- Return raw JSON dictionaries (no normalization or schema validation)

Architecture Layer: Adapter
- NO business logic
- NO data normalization
- NO schema validation
- NO filtering or sorting
- ONLY raw API calls and error handling
"""

from core.amadeus_client import (
    AmadeusAPIError,
    call_amadeus,
    ensure_amadeus_healthy,
    get_amadeus_client,
)
from core.logging import get_logger

logger = get_logger(__name__)


class HotelSearchAPIError(RuntimeError):
    """
    Custom exception raised when the Amadeus Hotel Search API call fails.

    This exception wraps all API-related errors including network issues,
    authentication failures, rate limiting, and invalid responses.
    """
    pass


def search_hotels_api(
    city_iata: str,
    adults: int = 1,
    check_in: str | None = None,
    check_out: str | None = None,
    radius_km: int = 50,
    max_results: int = 50,
) -> list[dict]:
    """
    Search for hotels using the Amadeus 2-step Hotel Search flow.

    This function implements the correct Amadeus hotel search flow:
    Step 1: Get hotel IDs by city using reference-data API
    Step 2: Get offers for those hotels using shopping API

    This is a pure API adapter that returns raw JSON data without any
    transformation or validation.

    Args:
        city_iata: IATA code of the city (e.g., 'DEL' for Delhi).
                   Must be a non-empty string.
        adults: Number of adult guests. Minimum 1. Defaults to 1.
        radius_km: Search radius parameter (currently not used in 2-step flow).
                   Kept for API compatibility. Defaults to 50.
        max_results: Maximum number of hotel offers to return.
                     Will be clamped to 200 (Amadeus limit). Defaults to 50.

    Returns:
        List of raw hotel offer dictionaries from Amadeus API.
        If offers cannot be fetched, returns a fallback list containing hotel objects
        from Step 1 (with empty offers lists) so downstream doesn't become empty.

    Raises:
        ValueError: If city_iata is empty or not a string.
        HotelSearchAPIError: If any Amadeus API call fails (non-recoverable).
    """
    ensure_amadeus_healthy()

    # Input validation
    if not isinstance(city_iata, str) or not city_iata.strip():
        raise ValueError("city_iata must be a non-empty string")

    # Sanitize and clamp parameters
    city_iata = city_iata.strip().upper()
    adults = max(1, int(adults))
    max_results = min(200, max(1, int(max_results)))  # Amadeus limit

    logger.info(
        f"Starting 2-step hotel search for city={city_iata}, "
        f"adults={adults}, max_results={max_results}"
    )

    try:
        # Get Amadeus client
        ensure_amadeus_healthy()
        client = get_amadeus_client()

        # ============================================================
        # STEP 1: Get hotel IDs by city
        # ============================================================
        logger.debug(f"Step 1: Fetching hotel IDs for city={city_iata}")

        hotels_by_city_response = call_amadeus(
            fn=client.reference_data.locations.hotels.by_city.get,
            cityCode=city_iata,
        )

        # Extract hotel IDs from response
        if not hasattr(hotels_by_city_response, "data"):
            logger.warning(
                f"Step 1: Response has no 'data' attribute for city={city_iata}"
            )
            return []

        hotel_data = hotels_by_city_response.data
        if not hotel_data:
            logger.info(f"Step 1: No hotels found in city={city_iata}")
            return []

        # Normalize hotel_data into dict list (Step-1 fallback list)
        hotel_items: list[dict] = []
        for x in hotel_data:
            if isinstance(x, dict):
                hotel_items.append(x)
            else:
                # try object-like item -> dict-like
                hid = getattr(x, "hotelId", None)
                name = getattr(x, "name", None)
                geo = getattr(x, "geoCode", None)
                addr = getattr(x, "address", None)
                # keep minimal useful fields
                d: dict = {}
                if hid:
                    d["hotelId"] = hid
                if name:
                    d["name"] = name
                if geo:
                    d["geoCode"] = geo
                if addr:
                    d["address"] = addr
                if d:
                    hotel_items.append(d)

        hotel_ids: list[str] = []
        fallback_raw_hotels: list[dict] = []
        for item in hotel_items:
            hid = item.get("hotelId")
            if isinstance(hid, str) and hid.strip():
                hid = hid.strip()
                hotel_ids.append(hid)
                # fallback shape expected by your normalize.py:
                # {"hotel": {...}, "offers": [...]}
                fallback_raw_hotels.append({"hotel": item, "offers": []})

        if not hotel_ids:
            logger.warning(
                f"Step 1: No valid hotel IDs found in {len(hotel_items)} items "
                f"for city={city_iata}"
            )
            return []

        logger.info(
            f"Step 1: Found {len(hotel_ids)} hotel ID(s) for city={city_iata}"
        )

        # ============================================================
        # STEP 2: Get offers for hotel IDs (TOP-UP LOOP)
        # ============================================================
        target_offers = max_results  # already clamped to <= 200 above

        collected: list[dict] = []
        seen_hotel_ids: set[str] = set()

        batch_size = 25  # safe batch (avoids oversized requests)
        idx = 0

        while len(collected) < target_offers and idx < len(hotel_ids):
            batch_ids = hotel_ids[idx: idx + batch_size]
            idx += batch_size

            logger.debug(
                f"Step 2: Fetching offers batch: ids={len(batch_ids)}, "
                f"collected={len(collected)}/{target_offers}"
            )

            hotel_ids_param = ",".join(str(hid) for hid in batch_ids)

            params: dict = {"hotelIds": hotel_ids_param, "adults": adults}
            if check_in:
                params["checkInDate"] = check_in
            if check_out:
                params["checkOutDate"] = check_out

            params["roomQuantity"] = 1
            params["currency"] = "INR"
            params["bestRateOnly"] = True

            try:
                offers_response = call_amadeus(
                    fn=client.shopping.hotel_offers_search.get,
                    **params
                )
            except AmadeusAPIError as e:
                msg = str(e).upper()

                # Valid property but no inventory for dates -> skip this batch
                if "NO ROOMS AVAILABLE" in msg:
                    continue

                # Transient provider errors -> skip this batch
                if "[500]" in msg or "INTERNAL SERVER ERROR" in msg:
                    continue

                # Sandbox data gap: hotel IDs exist in directory but have no
                # valid offers inventory (INVALID PROPERTY CODE). Skip batch,
                # keep collecting from remaining IDs.
                if "INVALID PROPERTY CODE" in msg or "INVALID_PROPERTY" in msg:
                    logger.warning(
                        f"Batch skipped — sandbox has no offer data for these "
                        f"hotel IDs (INVALID PROPERTY CODE). Trying next batch."
                    )
                    continue

                # Any other 400 from this batch: skip it, don't crash the tool
                if "[400]" in msg:
                    logger.warning(f"Batch 400 error, skipping: {str(e)[:120]}")
                    continue

                raise

            if not hasattr(offers_response, "data") or not offers_response.data:
                continue

            for offer in offers_response.data:
                hid = None
                if isinstance(offer, dict):
                    hid = offer.get("hotel", {}).get("hotelId")

                if hid and hid in seen_hotel_ids:
                    continue
                if hid:
                    seen_hotel_ids.add(hid)

                collected.append(offer)

                if len(collected) >= target_offers:
                    break

        if not collected:
            logger.info(
                f"Step 2: No offers found after checking {len(hotel_ids)} hotel IDs. "
                f"Returning Step-1 fallback hotels."
            )
            return fallback_raw_hotels[:max_results]

        logger.info(
            f"Step 2: Successfully retrieved {len(collected)} offer(s) "
            f"for city={city_iata}"
        )

        return collected

    except ValueError:
        raise

    except HotelSearchAPIError:
        raise

    except Exception as e:
        error_msg = (
            f"Failed to search hotels for city={city_iata}: "
            f"{type(e).__name__}: {str(e)}"
        )
        logger.error(error_msg, exc_info=True)
        # Return empty list instead of crashing — hotel results are optional.
        # The pipeline still returns flights, places, weather and budget.
        return []

