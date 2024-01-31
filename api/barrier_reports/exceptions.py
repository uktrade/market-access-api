from rest_framework.exceptions import APIException


class BarrierReportStatusUpdateError(APIException):
    status_code = 400
    default_code = "error"


class BarrierReportDoesNotExist(APIException):
    status_code = 404
    default_code = "error"


class BarrierReportNotificationError(APIException):
    status_code = 400
    default_code = "error"


class BarrierReportPatchError(APIException):
    status_code = 400
    default_code = "error"
