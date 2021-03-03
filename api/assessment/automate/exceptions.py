class ComtradeError(Exception):
    pass


class CountryNotFound(ComtradeError):
    pass


class ExchangeRateNotFound(ComtradeError):
    pass


class CountryYearlyDataNotFound(ComtradeError):
    pass
