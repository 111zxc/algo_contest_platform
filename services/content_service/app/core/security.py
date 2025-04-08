from typing import Optional

import requests
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class KeycloakWellKnown(BaseModel):
    issuer: str
    jwks_uri: str


class Jwks(BaseModel):
    keys: list


class KeycloakService:
    def __init__(self):
        self.realm_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
        self._well_known: Optional[KeycloakWellKnown] = None
        self._jwks: Optional[Jwks] = None

    def load_config(self):
        """Загружает well-known openid-configuration и JWKS из Keycloak."""
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

    @property
    def issuer(self) -> str:
        if not self._well_known:
            self.load_config()
        return self._well_known.issuer

    @property
    def jwks(self) -> list:
        if not self._jwks:
            self.load_config()
        return self._jwks.keys

    def decode_token(self, token: str) -> dict:
        """
        Проверяет подпись и валидирует токен.
        Возвращает payload (claims) или кидает ошибку JWTError.
        """
        # 1) Найдём kid из заголовка токена
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        # 2) Найдём соответствующий публичный ключ в self.jwks
        public_key = None
        for jwk in self.jwks:
            if jwk["kid"] == kid:
                public_key = jwk
                break

        if not public_key:
            raise JWTError("Public key not found in JWKS")

        payload = jwt.decode(
            token=token,
            key=public_key,
            audience=settings.KEYCLOAK_CLIENT_ID,
            issuer=self.issuer,
            options={"verify_aud": False, "verify_iss": False},
            algorithms=["RS256"],
        )

        return payload


keycloak_service = KeycloakService()
