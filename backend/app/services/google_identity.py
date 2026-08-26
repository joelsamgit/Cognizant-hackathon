from collections.abc import Mapping
from typing import Any

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token


class GoogleIdentityError(RuntimeError):
    pass


def verify_google_user_token(token: str, *, audience: str) -> Mapping[str, Any]:
    if not token or not audience:
        raise GoogleIdentityError("Google sign-in is not configured")
    try:
        claims = id_token.verify_oauth2_token(token, Request(), audience=audience)
    except (GoogleAuthError, ValueError) as exc:
        raise GoogleIdentityError("Invalid Google sign-in token") from exc
    if not claims.get("email") or claims.get("email_verified") is not True:
        raise GoogleIdentityError("Google account email is not verified")
    return claims


def verify_google_oidc_token(
    token: str,
    *,
    audience: str,
    expected_email: str,
) -> Mapping[str, Any]:
    if not token or not audience or not expected_email:
        raise GoogleIdentityError("Google OIDC authentication is not configured")

    try:
        claims = id_token.verify_oauth2_token(token, Request(), audience=audience)
    except (GoogleAuthError, ValueError) as exc:
        raise GoogleIdentityError("Invalid Google OIDC token") from exc

    if claims.get("email") != expected_email or claims.get("email_verified") is not True:
        raise GoogleIdentityError("Google OIDC service account does not match")

    return claims
