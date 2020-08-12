from rest_framework.exceptions import APIException


class PublicBarrierPublishException(APIException):
    status_code = 400
    default_detail = 'Cannot publish barrier with pending changes.'
    default_code = 'error'
