from fastapi import Cookie, HTTPException

from app.bootstrap.container import build_user_repository, resolve_settings
from app.infrastructure.security.auth_tokens import AuthTokenError, parse_auth_token


def get_current_user(claw_auth: str | None = Cookie(default=None)):
    if not claw_auth:
        raise HTTPException(status_code=401, detail="Authentication required")
    settings = resolve_settings()
    try:
        payload = parse_auth_token(claw_auth, secret_key=settings.auth_secret_key)
    except AuthTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    user_id_raw = payload.get("sub")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid auth subject") from exc
    repository = build_user_repository(settings)
    user = repository.find_by_id(user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="User not available")
    return user
