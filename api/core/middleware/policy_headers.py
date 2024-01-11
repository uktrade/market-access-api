from django.utils.cache import add_never_cache_headers


class DisableClientCachingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        return response


class SetPermittedCrossDomainPolicyHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        return response
