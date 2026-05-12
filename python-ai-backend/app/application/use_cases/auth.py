from fastapi import HTTPException

from app.bootstrap.container import build_user_repository, resolve_settings
from app.domain.models.user import User
from app.infrastructure.security.auth_tokens import create_auth_token
from app.infrastructure.security.password_hasher import hash_password, verify_password


def register_user(email: str, password: str, nickname: str | None = None) -> tuple[User, str]:
    settings = resolve_settings()
    repository = build_user_repository(settings)
    existing = repository.find_password_record_by_email(email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = repository.create_user(email=email, password_hash=hash_password(password), nickname=nickname)
    token = create_auth_token(user_id=user.id, secret_key=settings.auth_secret_key, expires_in_seconds=settings.auth_token_expire_hours * 3600)
    return user, token


def login_user(email: str, password: str) -> tuple[User, str]:
    settings = resolve_settings()
    repository = build_user_repository(settings)
    record = repository.find_password_record_by_email(email)
    if not record or not verify_password(password, str(record.get("password_hash") or "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = repository.find_by_id(int(record["id"]))
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="User not available")
    token = create_auth_token(user_id=user.id, secret_key=settings.auth_secret_key, expires_in_seconds=settings.auth_token_expire_hours * 3600)
    return user, token
