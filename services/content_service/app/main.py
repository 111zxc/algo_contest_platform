import uvicorn
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.endpoints import (
    blog_posts,
    comments,
    contests,
    posts,
    problems,
    reactions,
    register,
    tags,
    users,
)
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

app.include_router(users.router)
app.include_router(problems.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(reactions.router)
app.include_router(tags.router)
app.include_router(register.router)
app.include_router(blog_posts.router)
app.include_router(contests.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
