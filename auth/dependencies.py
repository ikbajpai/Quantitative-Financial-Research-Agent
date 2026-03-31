from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.jwt_utils import verify_token
from config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def _get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[str]:
    # 1. Authorization: Bearer <token> header
    if credentials and credentials.credentials:
        return credentials.credentials
    # 2. Cookie fallback
    return request.cookies.get("access_token")


def get_current_user(
    token: Optional[str] = Depends(_get_token_from_request),
) -> dict:
    settings = get_settings()
    # If Google OAuth is not configured, skip auth (dev mode)
    if (not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET
            or settings.GOOGLE_CLIENT_ID.startswith("your_")):
        return {"sub": "dev", "email": "dev@localhost", "name": "Dev User", "dev_mode": True}

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_optional_user(
    token: Optional[str] = Depends(_get_token_from_request),
) -> Optional[dict]:
    if not token:
        return None
    return verify_token(token)
