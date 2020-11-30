def rca(import_value, export_value):
    if import_value is None or export_value is None:
        return "NA"
    elif import_value > 0 and export_value > 0:
        return "Specialised"
    elif import_value < 0 and export_value < 0:
        return "Unspecialised"
    return "Inconclusive"


def rca_diff(import_value, export_value, country1, country2):
    if import_value is None or export_value is None:
        return "NA"
    elif import_value > 0 and export_value > 0:
        return f"{country2} more specialised globally than in {country1}"
    elif import_value < 0 and export_value < 0:
        return f"{country2} more specialised in {country1} than globally"
    return "Inconclusive"


def rca_diff_glob(import_value, export_value, country1, country2):
    if import_value is None or export_value is None:
        return "NA"
    elif import_value > 0 and export_value > 0:
        return f"{country2} more specialised globally than {country1}"
    elif import_value < 0 and export_value < 0:
        return f"{country1} more specialised globally than {country2}"
    return "Inconclusive"


def format_value(value):
    if value < 1000:
        return f"£{round(value, 0)}"
    elif value > 1000000000:
        return f"£{round(value, -8) / 1000000000}bn"
    elif value > 1000000:
        return f"£{round(value, -5) / 1000000}m"
    return f"£{round(value, -2) / 1000}k"


def value_range(import_value, export_value):
    if import_value < export_value:
        return f"{format_value(import_value)} - {format_value(export_value)}"
    return f"{format_value(export_value)} - {format_value(import_value)}"


def percent_range(import_value, export_value, decimal_places):
    import_value *= 100
    export_value *= 100
    if import_value == export_value:
        return f"{round(import_value, decimal_places)}%"
    elif import_value < export_value:
        return f"{round(import_value, decimal_places)}% - {round(export_value, decimal_places)}%"
    return f"{round(export_value, decimal_places)}% - {round(import_value, decimal_places)}%"
