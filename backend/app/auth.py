import hmac

from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {get_settings().api_key}"
    # constant-time comparison -- cheap to do right even for a
    # single-user app, and avoids a timing side-channel on the key.
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
