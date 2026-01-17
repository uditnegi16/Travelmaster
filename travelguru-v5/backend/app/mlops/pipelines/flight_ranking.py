import yaml
import os
import pandas as pd


def load_scoring_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def normalize(series: pd.Series, method: str):
    if method == "inverse_min_max":
        return 1 - (
            (series - series.min())
            / (series.max() - series.min())
        )
    if method == "min_max":
        return (series - series.min()) / (series.max() - series.min())

    raise ValueError(f"Unknown normalization: {method}")


def apply_filters(df, filters, user_pref):
    if filters.get("origin_required", False):
        df = df[df["origin"] == user_pref["origin"]]

    if filters.get("destination_required", False):
        df = df[df["destination"] == user_pref["destination"]]

    if filters.get("max_price") is not None:
        df = df[df["price"] <= filters["max_price"]]

    if filters.get("max_duration_minutes") is not None:
        df = df[df["duration_minutes"] <= filters["max_duration_minutes"]]

    return df


def rank_flights(flights_df, user_pref, artifact_dir):
    scoring_path = os.path.join(
        artifact_dir, "flight_scoring.yaml"
    )

    scoring = load_scoring_config(scoring_path)

    df = flights_df.copy()

    # 1️⃣ Filters
    df = apply_filters(
        df, scoring["filters"], user_pref
    )

    # 2️⃣ Normalize numeric features
    for feature, method in scoring["normalization"].items():
        df[feature] = normalize(df[feature], method)

    # 3️⃣ Score
    df["score"] = 0.0
    for feature, weight in scoring["weights"].items():
        if feature in df.columns:
            df["score"] += weight * df[feature]

    # 4️⃣ Rank
    ranking = scoring["ranking"]
    df = df.sort_values(
        ranking["sort_by"],
        ascending=(ranking["order"] == "ascending"),
    )

    return df.head(ranking["top_k"])
