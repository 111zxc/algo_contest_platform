from typing import Callable, Generator

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.database import SessionLocal
from app.core.security import keycloak_service

bearer_scheme = HTTPBearer()


def get_db() -> Generator:
    """
    Возвращает сессию БД
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> dict:
    """
    Валидирует токен, возвращает payload (claims).
    """
    token = creds.credentials
    try:
        payload = keycloak_service.decode_token(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# TODO: redo это и @require_role_or_self
def require_role(required_role: str):
    def wrapper(func: Callable):
        async def inner(user_claims: dict = Depends(get_current_user), *args, **kwargs):
            # Проверка ролей после того, как user_claims получены через Depends
            roles = user_claims.get("realm_access", {}).get("roles", [])
            if required_role not in roles:
                raise HTTPException(status_code=403, detail="Not enough privileges")
            return await func(*args, **kwargs)  # вызываем оригинальную функцию

        return inner

    return wrapper
