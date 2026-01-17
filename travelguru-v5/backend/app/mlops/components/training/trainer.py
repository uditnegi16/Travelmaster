import mlflow
import mlflow.sklearn
import os
import json
import yaml
import joblib

MLFLOW_EXPERIMENT_NAME = "TravelGuru-Recommender"

mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

def log_hotel_artifacts():
    with mlflow.start_run(run_name="hotel_offline_pipeline"):

        # Log preprocessor
        mlflow.log_artifact(
            "components/training/artifacts/hotel_preprocessor.pkl",
            artifact_path="hotel/preprocessor"
        )

        # Log feature schema
        mlflow.log_artifact(
            "components/training/artifacts/hotel_features.json",
            artifact_path="hotel/schema"
        )

        # Log scoring config
        mlflow.log_artifact(
            "components/training/artifacts/hotel_scoring.yaml",
            artifact_path="hotel/scoring"
        )

        mlflow.set_tags({
            "entity": "hotel",
            "pipeline": "offline",
            "model_type": "rule_based_ranking"
        })

        print("✅ Hotel artifacts logged to MLflow")
def log_flight_artifacts():
    with mlflow.start_run(run_name="flight_offline_pipeline"):

        mlflow.log_artifact(
            "components/training/artifacts/flight_preprocessor.pkl",
            artifact_path="flight/preprocessor"
        )

        mlflow.log_artifact(
            "components/training/artifacts/flight_features.json",
            artifact_path="flight/schema"
        )

        mlflow.log_artifact(
            "components/training/artifacts/flight_scoring.yaml",
            artifact_path="flight/scoring"
        )

        mlflow.set_tags({
            "entity": "flight",
            "pipeline": "offline",
            "model_type": "rule_based_ranking"
        })

        print("✅ Flight artifacts logged to MLflow")
def log_cab_artifacts():
    with mlflow.start_run(run_name="cab_offline_pipeline"):

        mlflow.log_artifact(
            "components/training/artifacts/cab_preprocessor.pkl",
            artifact_path="cab/preprocessor"
        )

        mlflow.log_artifact(
            "components/training/artifacts/cab_features.json",
            artifact_path="cab/schema"
        )

        mlflow.log_artifact(
            "components/training/artifacts/cab_scoring.yaml",
            artifact_path="cab/scoring"
        )

        mlflow.set_tags({
            "entity": "cab",
            "pipeline": "offline",
            "model_type": "rule_based_ranking"
        })

        print("✅ Cab artifacts logged to MLflow")
# ▶️ HOW YOU RUN THIS (ONCE)

# From project root:

# mlflow ui


# Then in Python / pipeline:

# from components.training.trainer import (
#     log_hotel_artifacts,
#     log_flight_artifacts,
#     log_cab_artifacts
# )

# log_hotel_artifacts()
# log_flight_artifacts()
# log_cab_artifacts()


# Open 👉 http://127.0.0.1:5000

# You’ll see:

# 3 runs

# Each with artifacts

# Fully versioned