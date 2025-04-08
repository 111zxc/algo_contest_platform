import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class TargetType(str, enum.Enum):
    post = "post"
    comment = "comment"


class ReactionType(str, enum.Enum):
    plus = "plus"
    minus = "minus"


class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(String, ForeignKey("users.keycloak_id"), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    target_type = Column(Enum(TargetType), nullable=False)
    reaction_type = Column(Enum(ReactionType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
