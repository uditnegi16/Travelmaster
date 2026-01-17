import json
import os
import joblib
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer


def load_feature_config(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def parse_features(feature_config: dict):
    numeric = []
    categorical = []

    for feature, meta in feature_config["features"].items():
        if meta["type"] == "numeric":
            numeric.append(feature)
        elif meta["type"] == "categorical":
            categorical.append(feature)

    return numeric, categorical


def build_preprocessor(numeric, categorical):
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )


def train_flight_preprocessor(flights_df, artifact_dir: str):
    config_path = os.path.join(
        artifact_dir, "flight_features.json"
    )

    feature_config = load_feature_config(config_path)
    numeric, categorical = parse_features(feature_config)

    model_df = flights_df[numeric + categorical].copy()

    preprocessor = build_preprocessor(numeric, categorical)
    preprocessor.fit(model_df)

    os.makedirs(artifact_dir, exist_ok=True)
    joblib.dump(
        preprocessor,
        os.path.join(artifact_dir, "flight_preprocessor.pkl"),
    )

    return preprocessor
