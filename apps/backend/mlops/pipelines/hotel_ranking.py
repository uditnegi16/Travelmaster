from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple, Optional

import math

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def _artifact_path(filename: str) -> str:
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
    mm = _min_max(values)
    return [1.0 - x for x in mm]


def _normalize(values: List[Optional[float]], method: str) -> List[float]:
    method = (method or "").lower()
    if method == "min_max":
        return _min_max(values)
    if method == "inverse_min_max":
        return _inverse_min_max(values)
    return [0.0 if v is None else float(v) for v in values]


def _load_scoring_config() -> Dict[str, Any]:
    path = _artifact_path("hotel_scoring.yaml")
    if yaml is None:
        raise RuntimeError("PyYAML not installed. Add `pyyaml` to mlops requirements.")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def score_and_rank_hotels(
    hotels: List[Dict[str, Any]],
    user_pref: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns:
      (recommended_hotels, other_hotels, metadata)

    Preserves all original keys (including booking links).
    Adds:
      - score
      - score_breakdown
    """
    user_pref = user_pref or {}
    cfg = _load_scoring_config()

    weights: Dict[str, float] = cfg.get("weights") or {}
    normalization: Dict[str, str] = cfg.get("normalization") or {}
    filters: Dict[str, Any] = cfg.get("filters") or {}
    ranking: Dict[str, Any] = cfg.get("ranking") or {}

    top_k = int((ranking.get("top_k") or 10))

    min_rating = _safe_float(filters.get("min_rating"))
    max_price = _safe_float(filters.get("max_price_per_night"))
    city_required = bool(filters.get("city_required", False))

    preferred_city = (user_pref.get("preferred_city") or user_pref.get("city") or "").strip().lower()

    filtered: List[Dict[str, Any]] = []
    for row in hotels or []:
        city = str(row.get("city") or row.get("location_city") or "").strip().lower()
        rating = _safe_float(row.get("rating"))
        price = _safe_float(row.get("price_per_night") or row.get("price"))
        # star_category can be "5" / 5 / "5-star"
        star = row.get("star_category")
        try:
            if isinstance(star, str):
                star_num = float("".join(ch for ch in star if ch.isdigit() or ch == ".") or "0")
            else:
                star_num = float(star) if star is not None else 0.0
        except Exception:
            star_num = 0.0

        if city_required and not city:
            continue
        if min_rating is not None and rating is not None and rating < min_rating:
            continue
        if max_price is not None and price is not None and price > max_price:
            continue

        # store parsed numeric star for scoring (but keep original too)
        new_row = dict(row)
        new_row["_star_num"] = star_num
        filtered.append(new_row)

    if not filtered:
        meta = {
            "entity": "hotel",
            "method": "weighted_sum",
            "count_in": len(hotels or []),
            "count_used": 0,
            "top_k": top_k,
            "note": "No hotels after filtering",
        }
        return [], [], meta

    ratings = [_safe_float(r.get("rating")) for r in filtered]
    prices = [_safe_float(r.get("price_per_night") or r.get("price")) for r in filtered]
    stars = [_safe_float(r.get("_star_num")) for r in filtered]

    norm_rating = _normalize(ratings, normalization.get("rating", "min_max"))
    norm_star = _normalize(stars, normalization.get("star_category", "min_max"))
    norm_price = _normalize(prices, normalization.get("price_per_night", "inverse_min_max"))

    w_rating = float(weights.get("rating", 0.0))
    w_star = float(weights.get("star_category", 0.0))
    w_price = float(weights.get("price_per_night", 0.0))

    scored: List[Dict[str, Any]] = []
    for i, row in enumerate(filtered):
        breakdown = {
            "rating": norm_rating[i],
            "star_category": norm_star[i],
            "price_per_night": norm_price[i],
        }
        score = (
            w_rating * breakdown["rating"]
            + w_star * breakdown["star_category"]
            + w_price * breakdown["price_per_night"]
        )

        new_row = dict(row)
        new_row.pop("_star_num", None)
        new_row["score"] = float(score)
        new_row["score_breakdown"] = breakdown
        scored.append(new_row)

    scored.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)

    recommended = scored[:top_k]
    others = scored[top_k:]

    meta = {
        "entity": "hotel",
        "method": "weighted_sum_yaml",
        "count_in": len(hotels or []),
        "count_used": len(filtered),
        "top_k": top_k,
        "weights": weights,
        "normalization": normalization,
        "filters": filters,
        "user_pref_used": {k: user_pref.get(k) for k in ["preferred_city", "city"] if k in user_pref},
    }
    return recommended, others, meta