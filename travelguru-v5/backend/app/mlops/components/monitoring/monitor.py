import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

import mlflow
import os


def run_hotel_drift_monitoring(reference_df, current_df, report_path="hotel_drift_report.html"):
    hotel_features = ["city", "rating", "price_per_night", "star_category"]
    reference_df = reference_df[hotel_features].copy()
    current_df = current_df[hotel_features].copy()

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference_df, current_data=current_df)
    report.save_html(report_path)

    # MLflow logging
    with mlflow.start_run(run_name="hotel_data_drift"):
        mlflow.log_artifact(report_path, artifact_path="drift_reports")
        mlflow.log_param("entity", "hotel")
        mlflow.log_param("monitored_features", ",".join(hotel_features))

    print("✅ Hotel drift monitoring completed")


# HOW TO CALL THIS (FROM PIPELINE OR NOTEBOOK)

# from components.monitoring.monitor import run_hotel_drift_monitoring

# # Reference = historical hotel data (training time)
# reference_hotels = hotels_df_model.copy()

# # Current = new hotel data (latest DB pull)
# current_hotels = latest_hotels_df.copy()

# run_hotel_drift_monitoring(
#     reference_df=reference_hotels,
#     current_df=current_hotels
# )


def run_flight_drift_monitoring(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    artifact_dir: str = "artifacts/drift/flight"
):
    os.makedirs(artifact_dir, exist_ok=True)

    features = [
        "duration_minutes",
        "price",
        "airline",
        "origin",
        "destination",
        "cabin_class"
    ]

    reference = reference_df[features]
    current = current_df[features]

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)

    report_path = os.path.join(artifact_dir, "flight_drift_report.html")
    report.save_html(report_path)

    mlflow.log_artifact(report_path, artifact_path="flight_drift")

    print("✅ Flight drift report generated")
    
    
    
def run_cab_drift_monitoring(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    artifact_dir: str = "artifacts/drift/cab"
):
    os.makedirs(artifact_dir, exist_ok=True)

    features = [
        "distance_km",
        "price",
        "vehicle_type",
        "pickup_location",
        "drop_location",
        "driver_rating"
    ]

    reference = reference_df[features]
    current = current_df[features]

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)

    report_path = os.path.join(artifact_dir, "cab_drift_report.html")
    report.save_html(report_path)

    mlflow.log_artifact(report_path, artifact_path="cab_drift")

    print("✅ Cab drift report generated")



# from components.monitoring.monitor import (
#     run_flight_drift_monitoring,
#     run_hotel_drift_monitoring,
#     run_cab_drift_monitoring
# )

# run_flight_drift_monitoring(train_flights_df, latest_flights_df)
# run_hotel_drift_monitoring(train_hotels_df, latest_hotels_df)
# run_cab_drift_monitoring(train_cabs_df, latest_cabs_df)
