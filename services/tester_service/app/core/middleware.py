from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logger import logger


class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        method = request.method
        url = str(request.url)

        response: Response = await call_next(request)
        status_code = response.status_code

        logger.debug(f"{method} {url} from {client_ip} | {status_code}")

        return response
