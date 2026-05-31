from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def decode_jwt(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=settings.JWT_ALGORITHMS,
        options={"verify_aud": False},
    )


def get_platform_user_id_from_claims(claims: dict) -> str:
    seen: set[str] = set()
    for key in (settings.JWT_PLATFORM_USER_ID_CLAIM, "userId", "sub"):
        if key in seen:
            continue
        seen.add(key)
        value = claims.get(key)
        if isinstance(value, str) and value.strip():
            return value
    raise JWTError("Missing or invalid platform user id claim (need non-empty userId or sub)")

