import datetime
from random import randrange

from django.conf import settings

CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def random_barrier_reference() -> str:

    """
    function to produce a random reference number for barriers
    format: B-YY-XXXX
    where YY is year and Xs are random alpha-numerics
    """
    dd = datetime.datetime.now()
    ref_code = f"B-{str(dd.year)[-2:]}-"
    for _ in range(settings.REF_CODE_LENGTH):
        ref_code += CHARSET[randrange(0, len(CHARSET))]
    return ref_code
