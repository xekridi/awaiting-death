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
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self';"
        )
        return resp
