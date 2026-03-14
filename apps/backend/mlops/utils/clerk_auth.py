# utils/clerk_auth.py

import os
import time
import logging
from typing import Any, Dict

import requests
from jose import jwt, JWTError
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_jwks_cache: Dict[str, Any] = {"data": None, "ts": 0.0, "url": None}
_JWKS_TTL_SEC = 600  # 10 minutes


def _get_jwks_url() -> str:
    url = (os.getenv("CLERK_JWKS_URL") or "").strip()
    if not url:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: CLERK_JWKS_URL is not set",
        )
    return url


def _get_jwks() -> dict:
    now = time.time()
    url = _get_jwks_url()

    # Return cached JWKS if still fresh
    if (
        _jwks_cache["data"]
        and _jwks_cache["url"] == url
        and (now - _jwks_cache["ts"] < _JWKS_TTL_SEC)
    ):
        return _jwks_cache["data"]

    # Fetch with retry once
    for attempt in range(2):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if not isinstance(data, dict) or "keys" not in data:
                raise ValueError(f"JWKS response missing 'keys': {data}")

            _jwks_cache["data"] = data
            _jwks_cache["ts"] = now
            _jwks_cache["url"] = url
            return data

        except HTTPException:
            raise
        except Exception as e:
            logger.warning("JWKS fetch attempt %d failed: %s", attempt + 1, e)
            if attempt == 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch Clerk JWKS from {url}: {e}",
                )
            time.sleep(0.5)

    raise HTTPException(status_code=500, detail="Failed to fetch Clerk JWKS")


def get_clerk_payload(token: str) -> dict:
    """
    Verify a Clerk JWT and return its payload.
    Raises HTTPException 401 on any auth failure.
    """
    # Basic sanity — must be a 3-part JWT
    if not token or token.count(".") != 2:
        raise HTTPException(status_code=401, detail="Malformed Bearer token")

    try:
        jwks = _get_jwks()

        # Peek at header to find the right key
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Token header missing 'kid'")

        # Find matching key in JWKS
        keys = jwks.get("keys", [])
        key = next((k for k in keys if k.get("kid") == kid), None)
        if key is None:
            # kid mismatch → force JWKS refresh once and retry
            _jwks_cache["ts"] = 0.0
            jwks = _get_jwks()
            keys = jwks.get("keys", [])
            key = next((k for k in keys if k.get("kid") == kid), None)

        if key is None:
            raise HTTPException(
                status_code=401,
                detail="Token signing key not found in Clerk JWKS",
            )

        # Decode + verify signature
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk tokens don't always have aud
        )
        return payload

    except HTTPException:
        raise
    except JWTError as e:
        logger.warning("JWT decode failed: %s", e)
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except Exception as e:
        logger.exception("Unexpected auth error")
        raise HTTPException(status_code=401, detail=f"Auth error: {e}")
