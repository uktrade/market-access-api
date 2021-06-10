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
        sessions_keys = [
            "_SessionBase__session_key",
            "accessed",
            "modified",
            "serializer",
            "_session_cache",
        ]
        stream_keys = ["stream", "remaining", "buffer", "buf_size"]
        message_keys = [
            "request",
            "_queued_messages",
            "used",
            "added_new",
            "storages",
            "_used_storages",
        ]

        for key in sessions_keys:
            logging.warning(f"STUB:session: |{key}| |{getattr(request.session, key)}|")
        for key in stream_keys:
            logging.warning(f"STUB:stream: |{key}| |{getattr(request._stream, key)}|")
        for key in message_keys:
            logging.warning(
                f"STUB:message: |{key}| |{getattr(request._messages, key)}|"
            )
        # keys = "".join([f"|{key}|" for key in request.session.__dict__.keys()])  #
        # logging.warning(f"STUB: session KEYS {sessions_keys}")
        # keys = "".join([f"|{key}|" for key in request._stream.__dict__.keys()])
        # logging.warning(f"STUB: _stream KEYS {stream_keys}")
        # keys = "".join([f"|{key}|" for key in request._messages.__dict__.keys()])
        # logging.warning(f"STUB: _messages KEYS {message_keys}")
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
