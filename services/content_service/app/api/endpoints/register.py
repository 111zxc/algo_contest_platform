import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.user import UserCreate, UserRead, UserRegistration
from app.services.user import create_user

router = APIRouter(prefix="/register", tags=["registration"])


def get_keycloak_admin_token() -> str:
    """
    Возвращает keycloak admin token для регистрации user'ов по api
    """
    url = f"{settings.KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": settings.KEYCLOAK_ADMIN,
        "password": settings.KEYCLOAK_ADMIN_PASSWORD,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=data, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to obtain admin token from Keycloak: {response.text}",
        )
    return response.json()["access_token"]


def register_user_in_keycloak(user_data: dict, admin_token: str) -> str:
    """
    Регистрирует пользователя в Keycloak и возвращает его keycloak_id.
    """
    url = f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=user_data, headers=headers)
    if response.status_code not in (201, 204):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Keycloak registration failed: {response.text}",
        )
    loc = response.headers.get("Location")
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Keycloak did not return a location header.",
        )
    keycloak_id = loc.rstrip("/").split("/")[-1]
    return keycloak_id


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegistration, db: Session = Depends(get_db)):
    """
    Регистрирует нового пользователя:
      1. Создает пользователя в Keycloak через Admin REST API (используя данные из модели UserRegistration).
      2. Создает локальный профиль пользователя с keycloak_id, полученным из Keycloak.
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
