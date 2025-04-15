from pydantic import BaseModel


class KeycloakWellKnown(BaseModel):
    issuer: str
    jwks_uri: str


class Jwks(BaseModel):
    keys: list
