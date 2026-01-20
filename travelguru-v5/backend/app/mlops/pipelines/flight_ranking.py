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


def rank_flights(df, user_pref, top_k=10):

    df = df[df["origin"] == user_pref.origin]
    df = df[df["destination"] == user_pref.destination]

    # Normalize
    df["price_norm"] = (df["price"] - df["price"].min()) / (df["price"].max() - df["price"].min())
    df["duration_norm"] = (df["duration_minutes"] - df["duration_minutes"].min()) / (
        df["duration_minutes"].max() - df["duration_minutes"].min()
    )

    # Score
    df["score"] = 0.6 * (1 - df["price_norm"]) + 0.4 * (1 - df["duration_norm"])

    df = df.sort_values(by="score", ascending=False)

    return df.head(top_k).to_dict(orient="records")


