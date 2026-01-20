import os
import pandas as pd

from evidently import Report, Dataset, DataDefinition
from evidently.presets import DataDriftPreset

import mlflow


import mlflow

mlflow.set_tracking_uri("file:./mlruns")
mlflow.set_experiment("travelguru-drift-monitoring")



# =========================
# HOTEL DRIFT MONITORING
# =========================
def run_hotel_drift_monitoring(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    report_path: str = "artifacts/drift/hotel/hotel_drift_report.html",
):
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    hotel_features = ["city", "rating", "price_per_night", "star_category"]
    reference_df = reference_df[hotel_features].copy()
    current_df = current_df[hotel_features].copy()

    # Define column types
    data_def = DataDefinition(
        categorical_columns=["city", "star_category"],
        numerical_columns=["rating", "price_per_night"],
    )  # [web:17]

    ref_dataset = Dataset.from_pandas(reference_df, data_definition=data_def)
    cur_dataset = Dataset.from_pandas(current_df, data_definition=data_def)  # [web:17]

    report = Report(metrics=[DataDriftPreset()])  # [web:21]
    evaluation = report.run(current_data=cur_dataset, reference_data=ref_dataset)  # [web:15]

    evaluation.save_html(report_path)  # [web:13]

    # MLflow logging
    with mlflow.start_run(run_name="hotel_data_drift"):
        mlflow.log_artifact(report_path, artifact_path="drift_reports/hotel")
        mlflow.log_param("entity", "hotel")
        mlflow.log_param("monitored_features", ",".join(hotel_features))

    print("✅ Hotel drift monitoring completed:", report_path)


# =========================
# FLIGHT DRIFT MONITORING
# =========================
def run_flight_drift_monitoring(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    artifact_dir: str = "artifacts/drift/flight",
):
    os.makedirs(artifact_dir, exist_ok=True)

    features = [
        "duration_minutes",
        "price",
        "airline",
        "origin",
        "destination",
        "cabin_class",
    ]
    reference = reference_df[features].copy()
    current = current_df[features].copy()

    data_def = DataDefinition(
        numerical_columns=["duration_minutes", "price"],
        categorical_columns=["airline", "origin", "destination", "cabin_class"],
    )  # [web:17]

    ref_dataset = Dataset.from_pandas(reference, data_definition=data_def)
    cur_dataset = Dataset.from_pandas(current, data_definition=data_def)  # [web:17]

    report = Report(metrics=[DataDriftPreset()])  # [web:21]
    evaluation = report.run(current_data=cur_dataset, reference_data=ref_dataset)  # [web:15]

    report_path = os.path.join(artifact_dir, "flight_drift_report.html")
    evaluation.save_html(report_path)  # [web:13]

    with mlflow.start_run(run_name="flight_data_drift"):
        mlflow.log_artifact(report_path, artifact_path="drift_reports/flight")
        mlflow.log_param("entity", "flight")
        mlflow.log_param("monitored_features", ",".join(features))

    print("✅ Flight drift report generated:", report_path)


# =========================
# CAB DRIFT MONITORING
# =========================
def run_cab_drift_monitoring(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    artifact_dir: str = "artifacts/drift/cab",
):
    os.makedirs(artifact_dir, exist_ok=True)

    features = [
        "distance_km",
        "price",
        "vehicle_type",
        "pickup_location",
        "drop_location",
        "driver_rating",
    ]
    reference = reference_df[features].copy()
    current = current_df[features].copy()

    data_def = DataDefinition(
        numerical_columns=["distance_km", "price", "driver_rating"],
        categorical_columns=["vehicle_type", "pickup_location", "drop_location"],
    )  # [web:17]

    ref_dataset = Dataset.from_pandas(reference, data_definition=data_def)
    cur_dataset = Dataset.from_pandas(current, data_definition=data_def)  # [web:17]

    report = Report(metrics=[DataDriftPreset()])  # [web:21]
    evaluation = report.run(current_data=cur_dataset, reference_data=ref_dataset)  # [web:15]

    report_path = os.path.join(artifact_dir, "cab_drift_report.html")
    evaluation.save_html(report_path)  # [web:13]

    with mlflow.start_run(run_name="cab_data_drift"):
        mlflow.log_artifact(report_path, artifact_path="drift_reports/cab")
        mlflow.log_param("entity", "cab")
        mlflow.log_param("monitored_features", ",".join(features))

    print("✅ Cab drift report generated:", report_path)
