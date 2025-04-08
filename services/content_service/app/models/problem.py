import enum
import uuid

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.tag import problem_tags


class DifficultyEnum(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class Problem(Base):
    __tablename__ = "problems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum(DifficultyEnum), nullable=False)
    created_by = Column(String, ForeignKey("users.keycloak_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    test_cases = Column(JSON, nullable=True)
    time_limit = Column(Integer, nullable=True)
    memory_limit = Column(Integer, nullable=True)

    tags = relationship("Tag", secondary=problem_tags, back_populates="problems")
