import logging

from sentry_sdk import set_user

logger = logging.getLogger(__name__)


class SentryUserContextMiddleware:
    """
    Middleware to make a log record of each url request with logged in user
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            set_user({
                "id": str(request.user.id),
                "email": request.user.email,
            })
        else:
            set_user(None)
        return self.get_response(request)

