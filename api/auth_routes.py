"""
Google OAuth2 authentication routes.
  GET /auth/login    → redirect to Google consent screen
  GET /auth/callback → exchange code, issue JWT, redirect to app
  GET /auth/logout   → clear cookie, redirect to app
  GET /auth/me       → return current user info (JSON)
  GET /auth/status   → returns {configured: bool, authenticated: bool}
"""
import logging

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse

from auth.dependencies import get_optional_user
from auth.jwt_utils import create_access_token
from config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth = OAuth()
_oauth_configured = False


def _setup_oauth():
    global _oauth_configured
    if _oauth_configured:
        return
    settings = get_settings()
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        _oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        _oauth_configured = True


@router.get("/status")
async def auth_status(request: Request):
    settings = get_settings()
    configured = bool(
        settings.GOOGLE_CLIENT_ID
        and settings.GOOGLE_CLIENT_SECRET
        and not settings.GOOGLE_CLIENT_ID.startswith("your_")
        and not settings.GOOGLE_CLIENT_SECRET.startswith("your_")
    )
    user = get_optional_user(
        token=request.cookies.get("access_token")
        or (request.headers.get("Authorization", "").removeprefix("Bearer ") or None)
    )
    return {
        "configured": configured,
        "authenticated": user is not None,
        "user": {
            "email": user.get("email"),
            "name": user.get("name"),
            "picture": user.get("picture"),
        } if user else None,
    }


@router.get("/login")
async def login(request: Request):
    _setup_oauth()
    settings = get_settings()

    if (not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET
            or settings.GOOGLE_CLIENT_ID.startswith("your_")):
        return JSONResponse(
            status_code=501,
            content={"error": "Google OAuth not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env"},
        )

    redirect_uri = f"{settings.BASE_URL}/auth/callback"
    return await _oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(request: Request):
    _setup_oauth()
    settings = get_settings()

    try:
        token = await _oauth.google.authorize_access_token(request)
    except OAuthError as e:
        logger.error("OAuth callback error: %s", e)
        return RedirectResponse(url="/?auth_error=oauth_failed")

    user_info = token.get("userinfo") or {}
    if not user_info.get("email"):
        return RedirectResponse(url="/?auth_error=no_email")

    jwt_payload = {
        "sub": user_info.get("sub", user_info["email"]),
        "email": user_info["email"],
        "name": user_info.get("name", ""),
        "picture": user_info.get("picture", ""),
    }
    access_token = create_access_token(jwt_payload)

    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,          # set True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response


@router.get("/me")
async def me(request: Request, user: dict = Depends(get_optional_user)):
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    return {
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture"),
        "dev_mode": user.get("dev_mode", False),
    }
