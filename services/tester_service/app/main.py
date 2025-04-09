import time

import docker
from fastapi import FastAPI

from app.api.endpoints import solutions
from app.core.config import settings
from app.core.middleware import LogRequestMiddleware

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(LogRequestMiddleware)

app.include_router(solutions.router)


def get_docker_client(timeout=30, interval=2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            client = docker.DockerClient(base_url=settings.DOCKER_HOST)
            client.version()
            print("Got docker client")
            return client
        except Exception as e:
            print("Waiting for dind to be ready...", e)
            time.sleep(interval)
    raise Exception("Timed out waiting for Docker daemon")


@app.on_event("startup")
def pull_required_images():
    client = get_docker_client()
    print("Got docker client on startup")

    images = [
        "python:3.12-slim",
        "openjdk:17-slim",
        "node:18-slim",
        "golang:1.24.1-bookworm",
        "gcc:latest",
        "mcr.microsoft.com/dotnet/sdk:7.0",
    ]
    for image in images:
        print(f"Pulling image {image} ...")
        try:
            client.images.pull(image)
            print(f"Image {image} pulled successfully.")
        except Exception as e:
            print(f"Error pulling {image}: {e}")
    print("Pulled all needed images!")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
