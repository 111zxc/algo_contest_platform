from typing import Optional

import requests
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logger import logger
from app.schemas.security import Jwks, KeycloakWellKnown


class KeycloakService:
    def __init__(self):
        self.realm_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
        self._well_known: Optional[KeycloakWellKnown] = None
        self._jwks: Optional[Jwks] = None

    def load_config(self):
        """
        Загружает well-known OpenID-конфигурацию и JWKS из Keycloak.
        Выполняет запрос к URL конфигурации и получает публичные ключи для верификации токенов.
        """
        try:
            # 1) well-known
            well_known_url = f"{self.realm_url}/.well-known/openid-configuration"
            r = requests.get(well_known_url)
            r.raise_for_status()
            data = r.json()
            self._well_known = KeycloakWellKnown(
                issuer=data["issuer"], jwks_uri=data["jwks_uri"]
            )

            # 2) JWKS
            r = requests.get(self._well_known.jwks_uri)
            r.raise_for_status()
            self._jwks = Jwks(keys=r.json()["keys"])
        except Exception as e:
            logger.error(f"Error loading keycloak configuration: {str(e)}")

    @property
    def issuer(self) -> str:
        """
        Возвращает issuer из конфигурации Keycloak.
        Если конфигурация не загружена, выполняется загрузка.
        """
        if not self._well_known:
            self.load_config()
        return self._well_known.issuer

    @property
    def jwks(self) -> list:
        """
        Возвращает список JWKS (публичных ключей) Keycloak.
        Если набор ключей не загружен, выполняется загрузка конфигурации.
        """
        if not self._jwks:
            self.load_config()
        return self._jwks.keys

    def decode_token(self, token: str) -> dict:
        """
        Проверяет подпись и валидирует JWT-токен.

        1. Извлекает заголовок токена и получает идентификатор ключа (kid).
        2. Ищет соответствующий публичный ключ в JWKS.
        3. Декодирует токен, проверяя подпись с использованием найденного ключа.
        """
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            logger.error("Token header does not contain kid")
            raise JWTError("Token header 'kid' missing")

        public_key = None
        for jwk in self.jwks:
            if jwk["kid"] == kid:
                public_key = jwk
                break

        if not public_key:
            logger.error(f"Public key with kid {kid} not found in JWKS")
            raise JWTError("Public key not found in JWKS")

        try:
            payload = jwt.decode(
                token=token,
                key=public_key,
                audience=settings.KEYCLOAK_CLIENT_ID,
                issuer=self.issuer,
                options={"verify_aud": False, "verify_iss": False},
                algorithms=["RS256"],
            )
            return payload
        except JWTError as e:
            logger.error(f"Error decoking token: {str(e)}")
            raise


keycloak_service = KeycloakService()
