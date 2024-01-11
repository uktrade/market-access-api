class MarketAccessException(Exception):
    """General Market Access exception"""

    pass


class ArchivingException(Exception):
    """Exception to be raised when there's an issue during archiving"""

    pass


class S3UploadException(Exception):
    """Exception to be used when a file could not be uploaded to S3"""

    pass


class AtomicTransactionException(Exception):
    """Exception to be used when you want to roll back an atomic transaction"""

    pass


class IllegalManagementCommandException(Exception):
    """Exception to be used when you try to run a migrations command in an illegal environment"""

    pass
