import os
import time
from typing import Any, Dict, Optional

import requests
from jose import jwt
from fastapi import HTTPException


_jwks_cache: Dict[str, Any] = {"data": None, "ts": 0, "url": None}
_JWKS_TTL_SEC = 60 * 10  # 10 minutes


def _get_jwks_url() -> str:
    url = (os.getenv("CLERK_JWKS_URL") or "").strip()
    if not url:
        raise HTTPException(status_code=500, detail="Missing CLERK_JWKS_URL on server")
    return url


def _get_jwks() -> dict:
    now = time.time()
    url = _get_jwks_url()

    if (
        _jwks_cache["data"]
        and _jwks_cache["url"] == url
        and (now - _jwks_cache["ts"] < _JWKS_TTL_SEC)
    ):
        return _jwks_cache["data"]

    try:
        data = requests.get(url, timeout=10).json()
        if not isinstance(data, dict) or "keys" not in data:
            raise ValueError("JWKS missing 'keys'")
        _jwks_cache["data"] = data
        _jwks_cache["ts"] = now
        _jwks_cache["url"] = url
        return data
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch Clerk JWKS")


def get_clerk_payload(token: str) -> dict:
    # quick sanity: must look like JWT
    if not token or token.count(".") != 2:
        raise HTTPException(status_code=401, detail="Invalid Clerk token")

    try:
        jwks = _get_jwks()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Invalid Clerk token")

        keys = jwks.get("keys", [])
        key = next((k for k in keys if k.get("kid") == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid Clerk token")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Clerk token")