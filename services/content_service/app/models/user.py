from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.solved_problems import solved_problems


class User(Base):
    __tablename__ = "users"

    keycloak_id = Column(
        String, primary_key=True, unique=True, index=True, nullable=False
    )
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    solved_problems = relationship(
        "Problem", secondary=solved_problems, back_populates="solved_by"
    )
