import logging

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.config import get_settings
from app.core.security import decode_jwt, get_platform_user_id_from_claims

logger = logging.getLogger(__name__)

settings = get_settings()
_bearer = HTTPBearer(auto_error=False)


def require_service_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if settings.DEBUG:
        logger.debug(
            "Auth debug: X-API-Key header=%r | configured SERVICE_API_KEY=%r | match=%s",
            x_api_key,
            settings.SERVICE_API_KEY,
            (x_api_key == settings.SERVICE_API_KEY) if x_api_key else False,
        )
    if not x_api_key or x_api_key != settings.SERVICE_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service API key")


def require_platform_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if settings.DEBUG:
        if credentials is None:
            logger.debug("Auth debug: no Bearer credentials")
        else:
            logger.debug(
                "Auth debug: Bearer token=%r | scheme=%s",
                credentials.credentials,
                credentials.scheme,
            )
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        claims = decode_jwt(credentials.credentials)
        return get_platform_user_id_from_claims(claims)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_auth(
    _api_key: None = Depends(require_service_api_key),
    platform_user_id: str = Depends(require_platform_user_id),
) -> str:
    return platform_user_id

