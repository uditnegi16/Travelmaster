import pandas as pd
import joblib
import yaml
import json
import mlflow
from typing import Dict, List


# 1️⃣ Load artifacts (shared utility)

def load_artifacts(entity: str):
    base = f"components/training/artifacts"

    preprocessor = joblib.load(f"{base}/{entity}_preprocessor.pkl")

    with open(f"{base}/{entity}_features.json") as f:
        feature_schema = json.load(f)

    with open(f"{base}/{entity}_scoring.yaml") as f:
        scoring_cfg = yaml.safe_load(f)

    return preprocessor, feature_schema, scoring_cfg

# 🏨 HOTEL

def score_hotel(row: pd.Series, user_pref: Dict, scoring_cfg: Dict) -> float:
    score = 0.0
    w = scoring_cfg["weights"]

    score += w["rating"] * row["rating"]
    score += w["star_category"] * row["star_category"]
    score += w["price_per_night"] * (-row["price_per_night"])

    if row["city"] == user_pref.get("preferred_city"):
        score += 0.2

    return score

def recommend_hotels(
    hotels_df: pd.DataFrame,
    agent_output: Dict,
    top_k: int = 5
) -> pd.DataFrame:
    user_pref = agent_output.get("hotel_preferences", {})

    _, _, scoring_cfg = load_artifacts("hotel")

    df = hotels_df.copy()

    if user_pref.get("max_price"):
        df = df[df["price_per_night"] <= user_pref["max_price"]]

    df["score"] = df.apply(
        lambda r: score_hotel(r, user_pref, scoring_cfg),
        axis=1
    )

    df = df.sort_values("score", ascending=False)
    df["recommended"] = False
    df.iloc[:top_k, df.columns.get_loc("recommended")] = True

    return df

# ✈️ FLIGHT

def score_flight(row: pd.Series, user_pref: Dict) -> float:
    score = 0.0

    score += -0.5 * row["price"]
    score += -0.2 * row["duration_minutes"]

    if row["origin"] == user_pref.get("origin"):
        score += 0.2

    return score

def recommend_flights(
    flights_df: pd.DataFrame,
    agent_output: Dict,
    top_k: int = 3
) -> pd.DataFrame:
    user_pref = agent_output

    df = flights_df.copy()

    df["score"] = df.apply(
        lambda r: score_flight(r, user_pref),
        axis=1
    )

    df = df.sort_values("score", ascending=False)
    df["recommended"] = False
    df.iloc[:top_k, df.columns.get_loc("recommended")] = True

    return df

# 🚕 CAB

def score_cab(row: pd.Series, user_pref: Dict) -> float:
    score = 0.0

    # 1️⃣ Route match (MOST IMPORTANT)
    if (
        row["pickup_location"] == user_pref.get("pickup_location")
        and row["drop_location"] == user_pref.get("drop_location")
    ):
        score += 1.0
    else:
        score -= 0.5

    # 2️⃣ Vehicle type preference (optional)
    if user_pref.get("vehicle_type") and row["vehicle_type"] == user_pref["vehicle_type"]:
        score += 0.3

    # 3️⃣ Lower price preferred
    score += -0.4 * row["price"]

    # 4️⃣ Shorter distance preferred
    score += -0.3 * row["distance_km"]

    return score


def recommend_cabs(
    cabs_df: pd.DataFrame,
    agent_output: dict,
    top_k: int = 2
) -> pd.DataFrame:

    user_pref = agent_output

    df = cabs_df.copy()

    df["score"] = df.apply(
        lambda r: score_cab(r, user_pref),
        axis=1
    )

    df = df.sort_values("score", ascending=False)
    df["recommended"] = False
    df.iloc[:top_k, df.columns.get_loc("recommended")] = True

    return df
