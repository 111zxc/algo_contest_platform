import uvicorn
from fastapi import FastAPI

from app.api.endpoints import (
    comments,
    posts,
    problems,
    reactions,
    register,
    tags,
    users,
)
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(users.router)
app.include_router(problems.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(reactions.router)
app.include_router(tags.router)
app.include_router(register.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
