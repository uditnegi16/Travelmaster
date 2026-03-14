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
    if filters.get("pickup_location_required", False):
        df = df[
            df["pickup_location"]
            == user_pref["pickup_location"]
        ]

    if filters.get("drop_location_required", False):
        df = df[
            df["drop_location"]
            == user_pref["drop_location"]
        ]

    if filters.get("max_price") is not None:
        df = df[df["price"] <= filters["max_price"]]

    return df


def rank_cabs(df, user_pref, top_k=10):

    df = df[df["pickup_location"] == user_pref.pickup_location]
    df = df[df["drop_location"] == user_pref.drop_location]

    # Normalize
    df["price_norm"] = (df["price"] - df["price"].min()) / (df["price"].max() - df["price"].min())
    df["rating_norm"] = (df["driver_rating"] - df["driver_rating"].min()) / (
        df["driver_rating"].max() - df["driver_rating"].min()
    )

    # Score
    df["score"] = 0.6 * (1 - df["price_norm"]) + 0.4 * df["rating_norm"]

    df = df.sort_values(by="score", ascending=False)

    return df.head(top_k).to_dict(orient="records")
