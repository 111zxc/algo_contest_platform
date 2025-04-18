import uuid
from sqlalchemy import Column, String, Table, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

contest_participants = Table(
    "contest_participants",
    Base.metadata,
    Column("contest_id", UUID(as_uuid=True), ForeignKey("contests.id", ondelete="CASCADE"), primary_key=True),
    Column("user_keycloak_id", String, ForeignKey("users.keycloak_id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
)


class Contest(Base):
    __tablename__ = "contests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, nullable=False, server_default="true")
    created_by = Column(String, ForeignKey("users.keycloak_id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="owned_contests")
    problems = relationship("Problem", back_populates="contest", cascade="all, delete-orphan")
    participants = relationship(
        "User",
        secondary=contest_participants,
        back_populates="contests_joined",
        lazy="joined",
    )