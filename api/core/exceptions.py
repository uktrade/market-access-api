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

class AnonymiseProductionDataException(Exception):
    """Exception to be used when you try to anonymise production data using the data_anonymise management command"""

    pass