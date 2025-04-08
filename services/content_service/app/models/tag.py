import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

problem_tags = Table(
    "problem_tags",
    Base.metadata,
    Column(
        "problem_id", UUID(as_uuid=True), ForeignKey("problems.id"), primary_key=True
    ),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True),
)

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", UUID(as_uuid=True), ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    problems = relationship("Problem", secondary=problem_tags, back_populates="tags")
    posts = relationship("Post", secondary=post_tags, back_populates="tags")
