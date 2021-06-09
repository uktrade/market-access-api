import logging


class SetAuthUserMiddleware:
    """
    The old setup of 2 of the 3 market-access project always used the anonymous user
    for the response.user object. This does not work for our new logging system, it
    needs to know which user is making each request. So this middleware is to set
    the request.user object based on the sso_token supplied in
    the request.session['sso_token']
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for key in request.__dict__:
            logging.warning(f"STUB:{key} {getattr(request, key)}")
        return self.get_response(request)
