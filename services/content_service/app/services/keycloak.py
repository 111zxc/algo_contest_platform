import requests
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logger import logger


def get_keycloak_admin_token() -> str:
    """
    Возвращает keycloak admin token для регистрации пользователей через API

    Args:
        None

    Returns:
        str - admin access token из Keycloak

    Raises:
        HTTPException 500 - если не удалось получить токен от Keycloak
    """
    url = f"{settings.KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": settings.KEYCLOAK_ADMIN,
        "password": settings.KEYCLOAK_ADMIN_PASSWORD,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=data, headers=headers)
    except Exception as e:
        logger.error(f"Error getting keycloak admin token: {str(e)}")
        raise
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to obtain admin token from Keycloak: {response.text}",
        )
    logger.debug("Successfully got keycloak admin token")
    return response.json()["access_token"]


def register_user_in_keycloak(user_data: dict, admin_token: str) -> str:
    """
    Регистрирует пользователя в Keycloak и возвращает его keycloak_id

    Args:
        user_data (dict): регистрационные данные пользователя для Keycloak
        admin_token (str): токен доступа администратора Keycloak

    Returns:
        str - keycloak_id зарегистрированного пользователя

    Raises:
        HTTPException 500 - если регистрация в Keycloak не удалась или отсутствует заголовок Location
    """
    url = f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url, json=user_data, headers=headers)
    except Exception as e:
        logger.error(f"Error registering user in keycloak API: {str(e)}")
        raise
    if response.status_code not in (201, 204):
        logger.warning(f"Wrong status code from keycloak: {response.status_code}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Keycloak registration failed: {response.text}",
        )
    loc = response.headers.get("Location")
    if not loc:
        logger.warning("Keycloak did not return a location header.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Keycloak did not return a location header.",
        )
    keycloak_id = loc.rstrip("/").split("/")[-1]
    logger.info(f"Successfully registered keycloak user with keycloak_id {keycloak_id}")
    return keycloak_id
