import os
import time
import requests
from jose import jwt
from fastapi import HTTPException


CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")
if not CLERK_JWKS_URL:
    raise RuntimeError("Missing CLERK_JWKS_URL")

_jwks_cache = {"data": None, "ts": 0}
_JWKS_TTL_SEC = 60 * 10  # 10 minutes

def _get_jwks():
    now = time.time()
    if _jwks_cache["data"] and (now - _jwks_cache["ts"] < _JWKS_TTL_SEC):
        return _jwks_cache["data"]

    url: str = CLERK_JWKS_URL
    data = requests.get(url, timeout=10).json()
    _jwks_cache["data"] = data
    _jwks_cache["ts"] = now
    return data

def get_clerk_payload(token: str) -> dict:
    try:
        jwks = _get_jwks()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        key = next(k for k in jwks["keys"] if k["kid"] == kid)

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # ok for now
        )
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Clerk token")
