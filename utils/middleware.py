import logging

from django.contrib.auth import get_user_model

UserModel = get_user_model()


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
        keys = "".join([f"|key|" for keys in request.session.__dict__.keys()])
        logging.warning(f"STUB: session KEYS {keys}")
        keys = "".join([f"|key|" for keys in request._stream.__dict__.keys()])
        logging.warning(f"STUB: _stream KEYS {keys}")
        keys = "".join([f"|key|" for keys in request._messages.__dict__.keys()])
        logging.warning(f"STUB: _messages KEYS {keys}")
        # keys = [
        #     "environ",
        #     "path_info",
        #     "path",
        #     "META",
        #     "method",
        #     "content_type",
        #     "content_params",
        #     "_stream",
        #     "_read_started",
        #     "resolver_match",
        #     "COOKIES",
        #     "session",
        #     "user",
        #     "_messages",
        #     "_cached_user",
        # ]
        # for key in keys:
        #     logging.warning(f"STUB: |{key}| |{getattr(request, key)}|")

        # token = request.environ["HTTP_AUTHORIZATION"].split(" ")[-1]
        # logging.warning(f"STUB:token {token}")
        # try:
        #     user = UserModel.objects.get(profile__sso_user_id=token)
        #     logging.warning(f"STUB:user {user}")
        # except Exception as exc:
        #     logging.warning(f"STUB ERROR {exc}")
        return self.get_response(request)
