from functools import wraps

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import keycloak_service

bearer_scheme = HTTPBearer()


def get_current_user(
    creds: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> dict:
    """
    Валидирует токен и возвращает payload (claims)

    Args:
        creds: HTTPAuthorizationCredentials - данные авторизации.

    Returns:
        dict: словарь с payload токена.

    Raises:
        HTTPException: 401, если токен неверный.
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


def authorize(required_role: str, owner_param: str = None, owner_field: str = None):
    """
    Универсальный декоратор для авторизации

    1. Если у пользователя есть требуемая роль, выполнение разрешается.
    2. Если требуемой роли нет, но указан параметр владельца, проверяется, соответствует ли он текущему пользователю.

    Args:
        required_role: роль, необходимая для доступа (например, "admin").
        owner_param: имя параметра в функции (например, 'keycloak_id' или 'problem'), ..
            .. который содержит либо идентификатор, либо объект ресурса.
        owner_field: если owner_param – это объект, с помощью этого параметра извлекается ..
            .. идентификатор владельца (например, 'created_by'). Если None, owner_param считается идентификатором напрямую.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_claims = kwargs.get("user_claims")
            if not user_claims:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No user info",
                )
            current_user_id = user_claims.get("sub")
            roles = user_claims.get("realm_access", {}).get("roles", [])

            # Если у пользователя есть требуемая роль, разрешаем выполнение
            if required_role in roles:
                return func(*args, **kwargs)

            # Если не хватает роли и указан параметр владельца, проверяем его
            if owner_param:
                target = kwargs.get(owner_param)
                if target is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Variable '{owner_param}' was not given",
                    )

                if owner_field:
                    owner_value = getattr(target, owner_field, None)
                else:
                    owner_value = target

                if owner_value == current_user_id:
                    return func(*args, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough rights",
            )

        return wrapper

    return decorator
