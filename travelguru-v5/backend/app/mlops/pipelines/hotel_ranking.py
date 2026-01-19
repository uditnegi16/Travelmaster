import yaml
import os
import pandas as pd


def load_scoring_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def normalize(series: pd.Series, method: str):
    if method == "min_max":
        return (series - series.min()) / (series.max() - series.min())

    if method == "inverse_min_max":
        return 1 - (
            (series - series.min())
            / (series.max() - series.min())
        )

    raise ValueError(f"Unknown normalization: {method}")


def apply_filters(df, filters, user_pref):
    if filters.get("min_rating") is not None:
        df = df[df["rating"] >= filters["min_rating"]]

    if filters.get("max_price_per_night") is not None:
        df = df[df["price_per_night"] <= filters["max_price_per_night"]]

    if filters.get("city_required", False):
        city = user_pref.get("preferred_city")
        if city:
            df = df[df["city"] == city]

    return df


def rank_hotels(hotels_df, user_pref, artifact_dir):
    scoring_path = os.path.join(
        artifact_dir, "hotel_scoring.yaml"
    )

    scoring = load_scoring_config(scoring_path)

    df = hotels_df.copy()

    # 1️⃣ Apply filters
    df = apply_filters(
        df, scoring["filters"], user_pref
    )

    # 2️⃣ Normalize features
    for feature, method in scoring["normalization"].items():
        df[feature] = normalize(df[feature], method)

    # 3️⃣ Compute weighted score
    df["score"] = 0.0
    for feature, weight in scoring["weights"].items():
        df["score"] += weight * df[feature]

    # 4️⃣ Rank
    ranking = scoring["ranking"]

    df = df.sort_values(
        ranking["sort_by"],
        ascending=(ranking["order"] == "ascending"),
    )

    return df.head(ranking["top_k"])
