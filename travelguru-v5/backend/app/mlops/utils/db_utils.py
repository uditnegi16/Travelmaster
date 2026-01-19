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
