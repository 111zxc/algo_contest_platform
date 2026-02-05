import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class SolutionStatus(str, enum.Enum):
    PENDING = "pending"
    TLE = "TLE"
    MLE = "MLE"
    WA = "WA"
    RE = "RE"
    AC = "AC"


class Solution(Base):
    __tablename__ = "solutions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(String, nullable=False)
    problem_id = Column(String, nullable=False)
    code = Column(String, nullable=False)
    language = Column(String, nullable=False)

    status = Column(Enum(SolutionStatus), default=SolutionStatus.PENDING)
    time_used = Column(Float, nullable=True)
    memory_used = Column(Integer, nullable=True)
    faster_than = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
