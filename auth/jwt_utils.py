from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from config import get_settings

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=TOKEN_EXPIRE_HOURS))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def verify_token(token: str) -> Optional[dict]:
    try:
        return decode_token(token)
    except JWTError:
        return None
