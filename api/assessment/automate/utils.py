from collections import Counter
from itertools import groupby
from operator import itemgetter


def trade_df(x, df_input, products):
    if len(x) == 2:
        direction, partner_input = x
        reporter_input = None
    elif len(x) == 3:
        direction, partner_input, reporter_input = x

    df_filt = [
        item
        for item in df_input
        if item["partner"] == partner_input
        and item["trade_flow"] == direction
        and (reporter_input is None or item["reporter"] == reporter_input)
    ]

    df_filt = group_and_sum(
        data=df_filt, sum_field="trade_value_gbp", group_by=("trade_flow", "year")
    )

    for item in df_filt:
        item["reporter"] = reporter_input or "World"
        item["partner"] = partner_input
        item["products"] = products

    return df_filt


def trade_df_ind(x, df_input):
    if len(x) == 2:
        direction, partner_input = x
        reporter_input = None
    elif len(x) == 3:
        direction, partner_input, reporter_input = x

    df_filt = [
        item
        for item in df_input
        if item["partner"] == partner_input
        and item["trade_flow"] == direction
        and (reporter_input is None or item["reporter"] == reporter_input)
    ]

    commodity_lookup = get_commodity_lookup(df_filt)

    df_filt = group_and_sum(
        data=df_filt,
        sum_field="trade_value_gbp",
        group_by=("trade_flow", "year", "commodity_code"),
    )

    for item in df_filt:
        item["reporter"] = reporter_input or "World"
        item["partner"] = partner_input
        item["products"] = commodity_lookup.get(item["commodity_code"])

    return df_filt


def avgtrade(df, partner_input, direction, reporter_input=None):
    if reporter_input:
        df_filt = [
            item
            for item in df
            if item["partner"] == partner_input
            and item["reporter"] == reporter_input
            and item["trade_flow"] == direction
        ]
    else:
        df_filt = [
            item
            for item in df
            if item["partner"] == partner_input and item["trade_flow"] == direction
        ]

    df_filt = group_and_sum(
        data=df_filt, sum_field="trade_value_gbp", group_by=("year",)
    )

    count = 0
    total = 0
    for item in df_filt:
        total += item["total"]
        count += 1

    if count == 0:
        return 0

    return total / count


def group_and_sum(data, sum_field, group_by):
    grouper = itemgetter(*group_by)

    output = []
    for key, grp in groupby(sorted(data, key=grouper), grouper):
        if isinstance(key, str) or isinstance(key, int):
            key = (key,)
        item = dict(zip(group_by, key))
        item["total"] = sum(x[sum_field] for x in grp)
        output.append(item)

    return output


def group_and_average(data, field, group_by, start_year, end_year):
    grouper = itemgetter(*group_by)
    output = []
    for key, grp in groupby(sorted(data, key=grouper), grouper):
        summary_row = {str(year): 0 for year in range(start_year, end_year + 1)}

        total = 0
        for index, row in enumerate(grp):
            if index == 0:
                summary_row = {field: row.get(field) for field in group_by}
            summary_row[str(row["year"])] = row[field]
            total += row[field]

        summary_row["average"] = total / (1 + end_year - start_year)
        output.append(summary_row)
    return output


def most_common(items):
    occurence_count = Counter(items)
    return occurence_count.most_common(1)[0][0]


def get_commodity_lookup(df_input):
    df_code_descriptions = {}
    for item in df_input:
        df_code_descriptions.setdefault(item["commodity_code"], [])
        df_code_descriptions[item["commodity_code"]].append(item["commodity"])

    return {
        code: most_common(descriptions)
        for code, descriptions in df_code_descriptions.items()
    }
