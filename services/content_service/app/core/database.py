from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import comment, post, problem, reaction, tag, user
from app.models.base import Base

engine = create_engine(settings.DATABASE_URL, future=True, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base.metadata.create_all(bind=engine)
