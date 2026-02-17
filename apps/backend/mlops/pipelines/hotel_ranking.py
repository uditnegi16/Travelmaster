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


def rank_hotels(df, user_pref, top_k=10):
    """
    Rank hotels based on scoring config and user preferences
    """

    import yaml
    import json
    import os

    base_path = os.path.dirname(__file__)
    artifact_path = os.path.join(base_path, "..", "components", "training", "artifacts")

    # ---------- Load configs ----------
    with open(os.path.join(artifact_path, "hotel_scoring.yaml"), "r") as f:
        scoring_cfg = yaml.safe_load(f)

    with open(os.path.join(artifact_path, "hotel_features.json"), "r") as f:
        feature_cfg = json.load(f)

    # ---------- Filtering ----------
    if scoring_cfg["filters"]["city_required"]:
        df = df[df["city"] == user_pref["city"]]

    if scoring_cfg["filters"]["min_rating"]:
        df = df[df["rating"] >= scoring_cfg["filters"]["min_rating"]]

    # ---------- Normalization ----------
    def min_max(series):
        return (series - series.min()) / (series.max() - series.min())

    def inverse_min_max(series):
        return 1 - min_max(series)

    df["rating_norm"] = min_max(df["rating"])
    df["star_norm"] = min_max(df["star_category"])
    df["price_norm"] = inverse_min_max(df["price_per_night"])

    # ---------- Scoring ----------
    w = scoring_cfg["weights"]

    df["score"] = (
        w["rating"] * df["rating_norm"] +
        w["star_category"] * df["star_norm"] +
        w["price_per_night"] * df["price_norm"]
    )

    # ---------- Ranking ----------
    df = df.sort_values(by="score", ascending=False)

    return df.head(top_k).to_dict(orient="records")

