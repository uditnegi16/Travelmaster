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
    ordinal = []
    categorical = []

    for feature, meta in feature_config["features"].items():
        if meta["type"] == "numeric":
            numeric.append(feature)
        elif meta["type"] == "ordinal":
            ordinal.append(feature)
        elif meta["type"] == "categorical":
            categorical.append(feature)

    return numeric, ordinal, categorical


def build_preprocessor(numeric, ordinal, categorical):
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric),
            ("ord", StandardScaler(), ordinal),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )


def train_hotel_preprocessor(hotels_df, artifact_dir: str):
    feature_config_path = os.path.join(
        artifact_dir, "hotel_features.json"
    )

    feature_config = load_feature_config(feature_config_path)

    numeric, ordinal, categorical = parse_features(feature_config)

    model_df = hotels_df[numeric + ordinal + categorical].copy()

    preprocessor = build_preprocessor(
        numeric, ordinal, categorical
    )

    preprocessor.fit(model_df)

    os.makedirs(artifact_dir, exist_ok=True)
    joblib.dump(
        preprocessor,
        os.path.join(artifact_dir, "hotel_preprocessor.pkl"),
    )

    return preprocessor
