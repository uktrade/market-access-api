from django.utils.text import slugify
import os
import json


def patched_comtrade_fetch(url):
    slugified_url = slugify(url)

    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, f"{slugified_url}.json")

    try:
        comtrade_test_data_file = open(filename, "r")
        return json.load(comtrade_test_data_file)
    except RuntimeError:
        return
