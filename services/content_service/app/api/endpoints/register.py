from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserRead, UserRegistration
from app.services.keycloak import get_keycloak_admin_token, register_user_in_keycloak
from app.services.user import create_user

router = APIRouter(prefix="/register", tags=["registration"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegistration, db: Session = Depends(get_db)):
    """
    Регистрирует нового пользователя:
      1. Создает пользователя в Keycloak через Admin REST API (используя данные из модели UserRegistration)
      2. Создает локальный профиль пользователя с keycloak_id, полученным из Keycloak

    Args:
        user_in (UserRegistration): регистрационные данные пользователя
        db (Session): объект сессии БД

    Returns:
        UserRead - созданный пользователь

    Raises:
        HTTPException 500 - если регистрация в Keycloak или создание пользователя не удались
    """
    keycloak_payload = {
        "username": user_in.username,
        "email": user_in.email,
        "firstName": user_in.first_name,
        "lastName": user_in.last_name,
        "enabled": True,
        "emailVerified": True,
        "requiredActions": [],
        "attributes": {
            "display_name": [user_in.display_name] if user_in.display_name else []
        },
        "credentials": [
            {"type": "password", "value": user_in.password, "temporary": False}
        ],
    }
    admin_token = get_keycloak_admin_token()
    keycloak_id = register_user_in_keycloak(keycloak_payload, admin_token)

    user_create = UserCreate(
        username=user_in.username,
        email=user_in.email,
        display_name=user_in.display_name,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        keycloak_id=keycloak_id,
    )

    local_user = create_user(db, user_create)

    return local_user
