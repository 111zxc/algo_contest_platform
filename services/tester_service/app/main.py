from fastapi import FastAPI

from app.api.endpoints import solutions
from app.core.config import settings
from app.core.logger import logger
from app.services.docker_runner import get_docker_client

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(solutions.router)


@app.on_event("startup")
def pull_required_images():
    client = get_docker_client()
    print("Got docker client on startup")

    images = [
        "python:3.12-slim",
        "openjdk:17-slim",
        "node:18-slim",
        "gcc:latest",
    ]
    for image in images:
        logger.info(f"Pulling image {image} ...")
        try:
            client.images.pull(image)
            logger.info(f"Image {image} pulled successfully.")
        except Exception as e:
            logger.error(f"Error pulling {image}: {e}")
    logger.info("Pulled all needed images!")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
