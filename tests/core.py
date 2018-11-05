import unittest
import os
import sys
import requests
import time
import json
from zb_common import Util

import logging
logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('SDG Core Tests')

util = Util("../config/test.cfg")

srcPath = util.get_env_value("src_path", "src")
p = os.path.abspath(srcPath)
sys.path.insert(0, p)

serverBaseUrl = util.get_env_value("base_url", "server")
variationsAPIUrl = "{}/variations".format(serverBaseUrl)
authkeyAPIUrl = "{}/authkey".format(serverBaseUrl)
headers = {
    'Content-type': "application/json"
}
os.environ["ZB_SERVER_BASE_URL"] = serverBaseUrl

from parameterized import parameterized
from zerobugz import load_test_cases, set_expected_value

payload = {
    'user_id': 'ujnamss'
}
resp = requests.post(authkeyAPIUrl, headers=headers, data=json.dumps(payload))
assert(resp.status_code == 200)
os.environ["ZB_API_KEY"] = resp.json().get('auth_key')

class SDGCoreTests(unittest.TestCase):

    @parameterized.expand(load_test_cases('custom_entity_float_val.json', count=5))
    def test_getFloatCustomValVariations(self, variation):
        # request_id = zb.get_request_id()
        # item_id = zb.get_item_id()
        print(variation)
        print(os.environ["ZB_API_KEY"])
        col1 = float(variation.get("col1", "0.1"))
        assert(col1 >= 0.1 and col1 <= 1.0)
        # set_expected_value(request_id, item_id, col1 * col1)
        set_expected_value("0674db953f2146b2acbcf8e6cd3e8157", 0, col1 * col1)

    # @parameterized.expand(load_test_cases('custom_entity_float_seq.json', count=50))
    # def test_getFloatCustomSeqVariations(self, variation):
    #     print(variation)
    #
    # @parameterized.expand(load_test_cases('custom_entity_integer_seq_invalid.json', count=50))
    # def test_getIntegerCustomSeqVariations(self, variation):
    #     print(variation)
    #
    # @parameterized.expand(load_test_cases('custom_entity_integer_seq.json', count=20))
    # def test_getIntegerCustomSeqVariations(self, variation):
    #     print(variation)
    #
    # @parameterized.expand(load_test_cases('custom_entity.json', count=100))
    # def test_getVariations(self, variation):
    #     print(variation)
    #
    # @parameterized.expand(load_test_cases('custom_entity_val_seq.json', count=10))
    # def test_getCustomSeqVariations(self, variation):
    #     print(variation)
    #
    # @parameterized.expand(load_test_cases('custom_entity_val_seq_invalid.json', count=100))
    # def test_getInvalidCustomSeqAndValueVariations(self, variation):
    #     print(variation)
    #
    # def test_invalidSchemaVariationsStrs(self):
    #     headers = {
    #         'Content-type': "application/json"
    #     }
    #     variationsPayload = {
    #         "count": 100,
    #         "entities": [
    #             ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'a10'],
    #             ['a', 'b', 'c', 'd', 'e']
    #         ]
    #     }
    #     print("variationsAPIUrl: {}".format(variationsAPIUrl))
    #     variationsResponse = requests.post(variationsAPIUrl, headers=headers, data=json.dumps(variationsPayload))
    #     assert(variationsResponse.status_code == 500)
    #     print(json.loads(variationsResponse.text)['status'])
    #     assert(json.loads(variationsResponse.text)['status'] == "failure")
