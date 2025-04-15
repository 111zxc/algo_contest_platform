from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

solved_problems = Table(
    "solved_problems",
    Base.metadata,
    Column(
        "user_keycloak_id", String, ForeignKey("users.keycloak_id"), primary_key=True
    ),
    Column(
        "problem_id", UUID(as_uuid=True), ForeignKey("problems.id"), primary_key=True
    ),
)
