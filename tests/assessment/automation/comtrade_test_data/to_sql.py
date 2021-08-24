import json
import os

from faker import Faker

fake = Faker()


mapping = {
    "pfCode": "classification",
    "yr": "year",
    "period": "period",
    "periodDesc": "period_desc",
    "aggrLevel": "aggregate_level",
    "IsLeaf": "is_leaf_code",
    "rgCode": "trade_flow_code",
    "rgDesc": "trade_flow",
    "rtCode": "reporter_code",
    "rtTitle": "reporter",
    "rt3ISO": "reporter_iso",
    "ptCode": "partner_code",
    "ptTitle": "partner",
    "pt3ISO": "partner_iso",
    "cmdCode": "commodity_code",
    "cmdDescE": "commodity",
    "qtCode": "quantity_unit_code",
    "qtDesc": "quantity_unit",
    "TradeQuantity": "quantity",
    "NetWeight": "netweight_kg",
    "TradeValue": "trade_value_usd",
}

commodity_cache = {}


def get_commodity(val):
    if val not in commodity_cache:
        commodity_cache[val] = fake.sentence(nb_words=10)

    return commodity_cache[val]


trade_value_usd_cache = {}


def get_trade_value_usd(val):
    if val not in trade_value_usd_cache:
        trade_value_usd_cache[val] = fake.random_int()

    return trade_value_usd_cache[val]


cast_mapping = {
    "classification": lambda x: "H1",
    "aggregate_level": lambda x: 1,
    "is_leaf_code": lambda x: False,
    "commodity": get_commodity,
    "quantity_unit_code": lambda x: 1,
    "quantity_unit": lambda x: "No Quantity",
    "quantity": lambda x: 0,
    "netweight_kg": lambda x: 1,
    "trade_value_usd": get_trade_value_usd,
}


def create_insert_statement():
    columns = ", ".join(v for v in mapping.values())

    values = set()
    for path in get_paths():
        data = get_data(path)
        if not data:
            continue

        for item in data:
            item_data = api_names_to_column_names(item)
            tuple_data = dict_to_tuple(item_data)
            values.add(tuple_data)

    for chunk in chunks(list(values), 500):
        print(f"INSERT INTO comtrade__goods ({columns})")
        print("VALUES")
        for idx, c in enumerate(chunk):
            value_statement = ", ".join(to_sql(v) for v in c)
            terminator = "," if idx != len(chunk) - 1 else ";"
            print(f"({value_statement}){terminator}")
        print()


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def get_paths():
    return os.listdir(os.getcwd())


def get_data(path):
    with open(path) as f:
        try:
            data = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            return None

        try:
            return data["dataset"]
        except KeyError:
            return None


def cast_map(key, val):
    try:
        return cast_mapping[key](val)
    except KeyError:
        return val


def api_names_to_column_names(api_item):
    return {new: cast_map(new, api_item[original]) for original, new in mapping.items()}


def dict_to_tuple(item):
    return tuple(item.values())


def to_sql(value):
    if isinstance(value, bool):
        return f"{'TRUE' if value else 'FALSE'}"
    elif isinstance(value, str):
        value = value.replace("'", "''")
        return f"'{value}'"
    elif isinstance(value, int):
        return f"{value}"
    elif value is None:
        return "NULL"


if __name__ == "__main__":
    create_insert_statement()
