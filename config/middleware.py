import logging
import traceback

logger = logging.getLogger("exception_logger")

class ExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            tb = traceback.format_exc()
            logger.error("Unhandled exception on %s %s:\n%s",
                         request.method,
                         request.path,
                         tb)
            raise

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resp = self.get_response(request)
        resp["X-Frame-Options"] = "DENY"
        resp["X-Content-Type-Options"] = "nosniff"
        resp["Referrer-Policy"] = "same-origin"
        resp["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https:; "
            "style-src  'self' 'unsafe-inline' https:; "
            "img-src    'self' data:; "
            "font-src   'self';"
        )
        return resp
