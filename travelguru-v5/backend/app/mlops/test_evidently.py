from components.monitoring.monitor import run_hotel_drift_monitoring
from utils.db_utils import load_hotels_from_db

# Reference = training-time data
reference_hotels = load_hotels_from_db()

# Simulate "current" data
current_hotels = load_hotels_from_db().sample(frac=0.8, random_state=42)

run_hotel_drift_monitoring(
    reference_df=reference_hotels,
    current_df=current_hotels
)
