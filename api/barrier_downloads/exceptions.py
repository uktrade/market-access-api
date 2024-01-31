from rest_framework.exceptions import APIException


class BarrierDownloadStatusUpdateError(APIException):
    status_code = 400
    default_code = "error"


class BarrierDownloadDoesNotExist(APIException):
    status_code = 404
    default_code = "error"


class BarrierDownloadNotificationError(APIException):
    status_code = 400
    default_code = "error"
