import uvicorn
from fastapi import FastAPI

from app.api.endpoints import solutions, languages as languages_endpoint
from app.core.config import settings
from app.core.logger import logger
from app.core.languages import required_images
from app.services.docker_runner import get_docker_client

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(solutions.router)
app.include_router(languages_endpoint.router)


@app.on_event("startup")
def pull_required_images():
    client = get_docker_client()
    logger.info("Got docker client on startup")

    images = required_images()
    for image in images:
        logger.info(f"Pulling image {image} ...")
        try:
            client.images.pull(image)
            logger.info(f"Image {image} pulled successfully.")
        except Exception as e:
            logger.error(f"Error pulling {image}: {e}")

    logger.info("Pulled all needed images!")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
