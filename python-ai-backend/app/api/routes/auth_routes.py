from fastapi import APIRouter, Depends, Response, status

from app.api.deps.auth import get_current_user
from app.api.schemas.auth import LoginRequest, RegisterRequest, UserProfileResponse
from app.application.use_cases.auth import login_user, register_user
from app.bootstrap.container import resolve_settings
from app.domain.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _write_auth_cookie(response: Response, token: str) -> None:
    settings = resolve_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.auth_token_expire_hours * 3600,
        path='/',
    )


@router.post('/register', response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def register_route(request: RegisterRequest, response: Response) -> UserProfileResponse:
    user, token = register_user(request.email, request.password, request.nickname)
    _write_auth_cookie(response, token)
    return UserProfileResponse(id=user.id, email=user.email, nickname=user.nickname, status=user.status)


@router.post('/login', response_model=UserProfileResponse)
def login_route(request: LoginRequest, response: Response) -> UserProfileResponse:
    user, token = login_user(request.email, request.password)
    _write_auth_cookie(response, token)
    return UserProfileResponse(id=user.id, email=user.email, nickname=user.nickname, status=user.status)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout_route(response: Response) -> Response:
    settings = resolve_settings()
    response.delete_cookie(key=settings.auth_cookie_name, path='/', samesite=settings.auth_cookie_samesite)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get('/me', response_model=UserProfileResponse)
def me_route(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse(id=current_user.id, email=current_user.email, nickname=current_user.nickname, status=current_user.status)
