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

app = FastAPI(title="Content Service")

app.include_router(users.router)
app.include_router(problems.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(reactions.router)
app.include_router(tags.router)
app.include_router(register.router)
