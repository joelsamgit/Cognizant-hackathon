from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserLogin, UserProfileUpdate, UserResponse, UserSignup
from app.schemas.user import GoogleAuthRequest
from app.services import auth as auth_service
from app.services.account_streaks import calculate_account_stats
from app.services import google_identity


router = APIRouter(tags=["account"])
DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: UserSignup,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> UserResponse:
    try:
        user, token = auth_service.register_user(db, payload, settings)
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    _set_session_cookie(response, token, settings)
    return _user_response(db, user)


@router.post("/auth/login", response_model=UserResponse)
def login(
    payload: UserLogin,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> UserResponse:
    user = auth_service.authenticate_user(db, str(payload.email), payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect",
        )
    token = auth_service.start_session(db, user, settings)
    _set_session_cookie(response, token, settings)
    return _user_response(db, user)


@router.post("/auth/google", response_model=UserResponse)
def google_auth(
    payload: GoogleAuthRequest,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> UserResponse:
    try:
        claims = google_identity.verify_google_user_token(payload.credential, audience=settings.google_client_id)
        user, token = auth_service.register_or_login_google(db, payload, dict(claims), settings)
    except google_identity.GoogleIdentityError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except auth_service.GoogleProfileRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    _set_session_cookie(response, token, settings)
    return _user_response(db, user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> Response:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        auth_service.end_session(db, token)
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/auth/me", response_model=UserResponse)
def me(user: CurrentUser, response: Response, db: DbSession) -> UserResponse:
    response.headers["Cache-Control"] = "no-store"
    return _user_response(db, user)


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    payload: UserProfileUpdate,
    user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    return _user_response(db, auth_service.update_profile(db, user, payload))


def _user_response(db: Session, user: User) -> UserResponse:
    stats = calculate_account_stats(db, user.id)
    return UserResponse.model_validate(
        {
            **UserResponse.model_validate(user).model_dump(),
            "account_current_streak": stats.current_streak,
            "account_longest_streak": stats.longest_streak,
            "account_xp": stats.xp,
            "account_growth_stage": stats.growth_stage,
            "account_mood": stats.mood,
            "account_total_waterings": stats.total_waterings,
        }
    )


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=int(timedelta(days=settings.session_lifetime_days).total_seconds()),
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
