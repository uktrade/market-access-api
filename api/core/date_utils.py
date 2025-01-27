from datetime import datetime


def get_nth_day_of_month(year, month, nth, weekday):
    """
    Gets the day of the nth weekday of a month.
    """
    first_of_month_weekday = datetime(year, month, 1).weekday()
    day_offset = (weekday - first_of_month_weekday) + 1

    if day_offset < 1:
        day_offset += 7

    return 7 * (nth - 1) + day_offset
