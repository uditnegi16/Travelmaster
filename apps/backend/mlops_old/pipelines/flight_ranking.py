from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple, Optional

import math

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


# -----------------------------
# Helpers
# -----------------------------
def _artifact_path(filename: str) -> str:
    """
    Resolve artifacts path:
    mlops/components/training/artifacts/<filename>
    This file lives in: mlops/pipelines/flight_ranking.py
    """
    base = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "components", "training", "artifacts")
    )
    return os.path.join(base, filename)


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, bool):
            return None
        return float(v)
    except Exception:
        return None


def _min_max(values: List[Optional[float]]) -> List[float]:
    xs = [v for v in values if v is not None and not math.isnan(v)]
    if not xs:
        return [0.0 for _ in values]
    lo, hi = min(xs), max(xs)
    if hi == lo:
        return [1.0 if v is not None else 0.0 for v in values]
    out: List[float] = []
    for v in values:
        if v is None or math.isnan(v):
            out.append(0.0)
        else:
            out.append((v - lo) / (hi - lo))
    return out


def _inverse_min_max(values: List[Optional[float]]) -> List[float]:
    # lower is better
    mm = _min_max(values)
    return [1.0 - x for x in mm]


def _normalize(values: List[Optional[float]], method: str) -> List[float]:
    method = (method or "").lower()
    if method == "min_max":
        return _min_max(values)
    if method == "inverse_min_max":
        return _inverse_min_max(values)
    # fallback: no normalization
    return [0.0 if v is None else float(v) for v in values]


def _cabin_score(cabin: Any) -> float:
    """
    Cabin class is categorical; we map it to an ordinal score.
    Adjust mapping anytime.
    """
    if not cabin:
        return 0.0
    s = str(cabin).strip().lower().replace(" ", "_")
    mapping = {
        "economy": 0.2,
        "basic_economy": 0.15,
        "premium_economy": 0.5,
        "business": 0.8,
        "first": 1.0,
        "first_class": 1.0,
    }
    return float(mapping.get(s, 0.0))


def _airline_score(airline: Any, user_pref: Dict[str, Any]) -> float:
    """
    Airline categorical scoring.
    If user_pref has preferred_airlines or airline, reward matches.
    """
    if not airline:
        return 0.0
    a = str(airline).strip().lower()

    pref_list = user_pref.get("preferred_airlines")
    pref_one = user_pref.get("airline")

    if isinstance(pref_list, list) and pref_list:
        norm = [str(x).strip().lower() for x in pref_list]
        return 1.0 if a in norm else 0.4
    if isinstance(pref_one, str) and pref_one.strip():
        return 1.0 if a == pref_one.strip().lower() else 0.4

    # neutral if no preference provided
    return 0.6


def _load_scoring_config() -> Dict[str, Any]:
    path = _artifact_path("flight_scoring.yaml")
    if yaml is None:
        raise RuntimeError("PyYAML not installed. Add `pyyaml` to mlops requirements.")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# -----------------------------
# Public API
# -----------------------------
def score_and_rank_flights(
    flights: List[Dict[str, Any]],
    user_pref: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns:
      (recommended_flights, other_flights, metadata)

    NOTE: We DO NOT drop any original keys (like booking links).
    We only add:
      - score (float)
      - score_breakdown (dict)
    """
    user_pref = user_pref or {}
    cfg = _load_scoring_config()

    weights: Dict[str, float] = cfg.get("weights") or {}
    normalization: Dict[str, str] = cfg.get("normalization") or {}
    filters: Dict[str, Any] = cfg.get("filters") or {}
    ranking: Dict[str, Any] = cfg.get("ranking") or {}

    top_k = int((ranking.get("top_k") or 2))

    # --- filtering (basic, safe) ---
    origin_required = bool(filters.get("origin_required", False))
    destination_required = bool(filters.get("destination_required", False))
    max_price = _safe_float(filters.get("max_price"))
    max_dur = _safe_float(filters.get("max_duration_minutes"))

    filtered: List[Dict[str, Any]] = []
    for row in flights or []:
        origin = (row.get("origin") or row.get("from") or "").strip()
        dest = (row.get("destination") or row.get("to") or "").strip()

        if origin_required and not origin:
            continue
        if destination_required and not dest:
            continue

        price = _safe_float(row.get("price"))
        dur = _safe_float(row.get("duration_minutes"))

        if max_price is not None and price is not None and price > max_price:
            continue
        if max_dur is not None and dur is not None and dur > max_dur:
            continue

        filtered.append(row)

    if not filtered:
        meta = {
            "entity": "flight",
            "method": "weighted_sum",
            "count_in": len(flights or []),
            "count_used": 0,
            "top_k": top_k,
            "note": "No flights after filtering",
        }
        return [], [], meta

    # --- prepare numeric vectors for normalization ---
    prices = [_safe_float(r.get("price")) for r in filtered]
    durs = [_safe_float(r.get("duration_minutes")) for r in filtered]

    norm_price = _normalize(prices, normalization.get("price", "inverse_min_max"))
    norm_dur = _normalize(durs, normalization.get("duration_minutes", "inverse_min_max"))

    # airline / cabin are categorical
    airline_raw = [_airline_score(r.get("airline"), user_pref) for r in filtered]
    cabin_raw = [_cabin_score(r.get("cabin_class")) for r in filtered]

    # normalize airline/cabin to 0..1 (already in 0..1 but keep consistent)
    norm_airline = _normalize([float(x) for x in airline_raw], "min_max")
    norm_cabin = _normalize([float(x) for x in cabin_raw], "min_max")

    # --- compute final score ---
    w_price = float(weights.get("price", 0.0))
    w_dur = float(weights.get("duration_minutes", 0.0))
    w_air = float(weights.get("airline", 0.0))
    w_cab = float(weights.get("cabin_class", 0.0))

    scored: List[Dict[str, Any]] = []
    for i, row in enumerate(filtered):
        breakdown = {
            "price": norm_price[i],
            "duration_minutes": norm_dur[i],
            "airline": norm_airline[i],
            "cabin_class": norm_cabin[i],
        }
        score = (
            w_price * breakdown["price"]
            + w_dur * breakdown["duration_minutes"]
            + w_air * breakdown["airline"]
            + w_cab * breakdown["cabin_class"]
        )

        new_row = dict(row)  # preserve all original keys (including `link`)
        new_row["score"] = float(score)
        new_row["score_breakdown"] = breakdown
        scored.append(new_row)

    # --- sort ---
    scored.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)

    recommended = scored[:top_k]
    others = scored[top_k:]

    meta = {
        "entity": "flight",
        "method": "weighted_sum_yaml",
        "count_in": len(flights or []),
        "count_used": len(filtered),
        "top_k": top_k,
        "weights": weights,
        "normalization": normalization,
        "filters": filters,
        "user_pref_used": {k: user_pref.get(k) for k in ["origin", "destination", "preferred_airlines", "airline"] if k in user_pref},
    }
    return recommended, others, meta