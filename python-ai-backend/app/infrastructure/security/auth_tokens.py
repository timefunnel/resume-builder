import base64
import hashlib
import hmac
import json
import time
from typing import Any


class AuthTokenError(Exception):
    pass


def _b64encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64decode(payload: str) -> bytes:
    padding = '=' * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def create_auth_token(*, user_id: int, secret_key: str, expires_in_seconds: int) -> str:
    body = {
        "sub": str(user_id),
        "exp": int(time.time()) + max(60, int(expires_in_seconds)),
    }
    encoded = _b64encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret_key.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def parse_auth_token(token: str, *, secret_key: str) -> dict[str, Any]:
    try:
        encoded, signature = token.split(".", 1)
    except ValueError as exc:
        raise AuthTokenError("invalid token format") from exc
    expected = hmac.new(secret_key.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise AuthTokenError("invalid token signature")
    try:
        payload = json.loads(_b64decode(encoded).decode("utf-8"))
    except Exception as exc:
        raise AuthTokenError("invalid token payload") from exc
    exp = int(payload.get("exp") or 0)
    if exp <= int(time.time()):
        raise AuthTokenError("token expired")
    return payload
