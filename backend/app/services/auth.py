import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User, UserSession
from app.schemas.user import UserProfileUpdate, UserSignup
from app.schemas.user import GoogleAuthRequest


password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$"
    "CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc"
)


class EmailAlreadyRegisteredError(RuntimeError):
    pass


class GoogleProfileRequiredError(RuntimeError):
    pass


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def register_user(
    db: Session,
    payload: UserSignup,
    settings: Settings,
) -> tuple[User, str]:
    email = normalize_email(str(payload.email))
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise EmailAlreadyRegisteredError("An account with this email already exists")

    user = User(
        email=email,
        password_hash=password_hash.hash(payload.password),
        full_name=payload.full_name,
        place=payload.place,
        pets=[pet.value for pet in payload.pets],
        timezone=payload.timezone,
        is_active=True,
    )
    db.add(user)
    try:
        db.flush()
        token = _create_session(db, user.id, settings)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyRegisteredError("An account with this email already exists") from exc
    db.refresh(user)
    return user, token


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    candidate_hash = user.password_hash if user is not None and user.is_active else DUMMY_PASSWORD_HASH
    valid = password_hash.verify(password, candidate_hash)
    if user is None or not user.is_active or not valid:
        return None
    return user


def register_or_login_google(
    db: Session,
    payload: GoogleAuthRequest,
    claims: dict[str, object],
    settings: Settings,
) -> tuple[User, str]:
    email = normalize_email(str(claims["email"]))
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user, start_session(db, user, settings)

    full_name = (payload.full_name or str(claims.get("name") or "")).strip()
    if len(full_name) < 2 or not payload.place or not payload.pets:
        raise GoogleProfileRequiredError("Complete your name, place, and pets before continuing with Google")

    user = User(
        email=email,
        password_hash=password_hash.hash(secrets.token_urlsafe(32)),
        full_name=full_name,
        place=payload.place.strip(),
        pets=[pet.value for pet in payload.pets],
        timezone="UTC",
        is_active=True,
    )
    db.add(user)
    db.flush()
    token = _create_session(db, user.id, settings)
    db.commit()
    db.refresh(user)
    return user, token


def start_session(db: Session, user: User, settings: Settings) -> str:
    token = _create_session(db, user.id, settings)
    db.commit()
    return token


def resolve_session(
    db: Session,
    token: str,
    *,
    now: datetime | None = None,
) -> tuple[UserSession, User] | None:
    current = _as_utc(now or datetime.now(timezone.utc))
    session = db.scalar(
        select(UserSession).where(UserSession.token_hash == _token_hash(token))
    )
    if session is None:
        return None
    if _as_utc(session.expires_at) <= current:
        db.delete(session)
        db.commit()
        return None

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        db.delete(session)
        db.commit()
        return None

    if current - _as_utc(session.last_seen_at) >= timedelta(minutes=15):
        session.last_seen_at = current
        db.commit()
    return session, user


def end_session(db: Session, token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == _token_hash(token)))
    db.commit()


def update_profile(db: Session, user: User, payload: UserProfileUpdate) -> User:
    user.full_name = payload.full_name
    user.place = payload.place
    user.pets = [pet.value for pet in payload.pets]
    user.timezone = payload.timezone
    db.commit()
    db.refresh(user)
    return user


def _create_session(db: Session, user_id: int, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    db.execute(delete(UserSession).where(UserSession.expires_at <= now))
    token = secrets.token_urlsafe(32)
    db.add(
        UserSession(
            user_id=user_id,
            token_hash=_token_hash(token),
            expires_at=now + timedelta(days=settings.session_lifetime_days),
            created_at=now,
            last_seen_at=now,
        )
    )
    return token


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
