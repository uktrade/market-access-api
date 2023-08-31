import datetime
from random import randrange

from django.conf import settings

CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def random_barrier_reference():
    """
    function to produce a random reference number for barriers
    format: B-YY-XXXX
    where YY is year and Xs are random alpha-numerics
    """
    dd = datetime.datetime.now()
    ref_code = f"B-{str(dd.year)[-2:]}-"
    for i in range(settings.REF_CODE_LENGTH):
        ref_code += CHARSET[randrange(0, len(CHARSET))]
    return ref_code


def string_attribute_lookup(holder, *args, raise_exception=False):
    """
    Function to return nested attribute from an object, either a dict or an instance of a class.

    e.g.
    holder = {"cities": {"london": {"population": "12"}}}
    *args = ["cities", "london", "population"]
    string_attribute_lookup(holder, *args) == "12"

    OR with a class instance:
    holder = Barrier.objects.get(id=1)
    *args = ["status", "id"]
    string_attribute_lookup(holder, *args) == "1" == holder.status.id

    args:
        holder: dict or class instance
        *args: list of strings to be used as attribute names
        raise_exception: bool, whether to raise an exception if the attribute is not found

    returns:
        the value of the attribute if found, else None
    """
    if isinstance(args, str):
        args = [
            args,
        ]

    for arg in args:
        if isinstance(holder, dict):
            holder = holder.get(arg, None)
        else:
            holder = getattr(holder, arg, None)
        if not holder:
            if raise_exception:
                raise AttributeError(f"Attribute {arg} not found in {holder}")
            break
    else:
        return holder

    return None
