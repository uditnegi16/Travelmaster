# backend/app/mlops/utils/db_utils.py
import os
import logging
import psycopg2
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def read_sql_to_df(query: str, params=None) -> pd.DataFrame:
    logger.info("Running query: %s", query[:80])
    with psycopg2.connect(DB_URL) as conn:
        df = pd.read_sql_query(query, conn, params=params)
    logger.info("Loaded %d rows", len(df))
    return df
def load_hotels_from_db():
    query = """
    SELECT hotel_name, city, rating, price_per_night,
           amenities, star_category
    FROM database_ml.hotels;
    """
    return read_sql_to_df(query)


def load_flights_from_db():
    query = """
    SELECT origin, destination, airline, dep_time, arr_time,
           duration_minutes, price, travel_date, cabin_class
    FROM database_ml.flights;
    """
    return read_sql_to_df(query)


def load_cabs_from_db():
    query = """
    SELECT ride_date, ride_time, pickup_location, drop_location,
           vehicle_type, distance_km, price,
           driver_rating, customer_rating
    FROM database_ml.cabs;
    """
    return read_sql_to_df(query)
