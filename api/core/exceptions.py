class MarketAccessException(Exception):
    """General Market Access exception"""

    pass


class ArchivingException(Exception):
    """Exception to be raised when there's an issue during archiving"""

    pass


class S3UploadException(Exception):
    """Exception to be used when a file could not be uploaded to S3"""

    pass
