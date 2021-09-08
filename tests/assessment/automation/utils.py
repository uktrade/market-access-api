import logging
import os

import simplejson as json
from django.utils.text import slugify

logger = logging.getLogger(__name__)


def patched_comtrade_fetch(self, url):
    slugified_url = slugify(url)

    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "comtrade_test_data", f"{slugified_url}.json")
    logger.info("Loading data from %s", filename)

    try:
        comtrade_test_data_file = open(filename, "r")
        return json.load(comtrade_test_data_file)
    except IOError:
        raise Exception(f"Missing mock datafile {filename}")
