class ComtradeError(Exception):
    pass


class CountryNotFound(ComtradeError):
    pass


class ExchangeRateNotFound(ComtradeError):
    pass
