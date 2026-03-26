import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Logs every request with method, path, status code, and response time."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        ms = round((time.monotonic() - start) * 1000)
        logger.info('%s %s → %d  (%dms)', request.method, request.path, response.status_code, ms)
        return response
