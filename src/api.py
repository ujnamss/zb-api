import os
import json
import sys
import fastjsonschema
import requests
from fastjsonschema.exceptions import JsonSchemaException
from flask import Flask
from flask import request
from flask import render_template
from flask import send_from_directory
from zb_common import Util
from auth import AuthKeyGenerator
from cache import ReverseAuthKeyCache, AuthKeyCache, TagCache
from pathlib import Path

util = Util("../config/test.cfg")
auth_key_gen = AuthKeyGenerator()
auth_key_cache = AuthKeyCache(util)
reverse_auth_key_cache = ReverseAuthKeyCache(util)
tag_cache = TagCache(util)
json_only_http_headers = {
    'Content-type': "application/json"
}
zb_core_API_url = util.get_env_value('zb_core_api_url', 'internal')

app = Flask(__name__, static_url_path='')

variations_request_schema = None

def test():
    print("hello")

@app.route('/static/<path:path>')
def send_schema(path):
    print("send_schema: path: {}".format(path))
    return send_from_directory('schemas', path)

@app.route("/authkey", methods=['POST'])
def generate_auth_key():
    print("generate_auth_key: invoked")
    request.get_data()
    user_id = request.json.get("user_id")
    auth_key = auth_key_gen.generate_auth_key()
    print("generate_auth_key: generated {} for {}".format(auth_key, user_id))
    auth_key_cache.cache(user_id, auth_key)
    reverse_auth_key_cache.cache(auth_key, user_id)
    print("generate_auth_key: caching complete")

    resp = {
        'user_id': user_id,
        'auth_key': auth_key
    }
    return json.dumps(resp), 200

@app.route("/tags", methods=['POST'])
def set_tags_for_request_id():
    print("set_tags_for_request_id: invoked")
    auth_key = request.headers.get('Authorization', None)
    if auth_key == None:
        resp = {
            "status": "failure",
            "message": "Please specify your auth_key in the Authorization header"
        }
        return json.dumps(resp), 401
    user_id = reverse_auth_key_cache.get_user_id(auth_key)
    print("set_tags_for_request_id api invoked with auth_key: {} for user_id: {}".format(auth_key, user_id))

    request.get_data()
    request_id = request.json.get("request_id")
    tags = request.json.get("tags")

    resp = {
        'status': "success",
        'result': "tags was set successfully"
    }
    http_status_code = 200

    file_path = "/data/{}".format(request_id)
    req_file = Path(file_path)
    if not req_file.exists():
        resp['status'] = "failure"
        resp["result"] = "invalid request_id"
        http_status_code = 404
    else:
        try:
            tag_cache.cache(request_id, tags)
        except Exception as e:
            print("Exception occured: {}".format(e))
            http_status_code = 500
            resp = {'status':'failure', 'result': "Setting tags failed"}

    return json.dumps(resp), http_status_code

@app.route("/expectedvalue", methods=['POST'])
def set_expected_value():
    print("set_expected_value: invoked")
    auth_key = request.headers.get('Authorization', None)
    if auth_key == None:
        resp = {
            "status": "failure",
            "message": "Please specify your auth_key in the Authorization header"
        }
        return json.dumps(resp), 401
    user_id = reverse_auth_key_cache.get_user_id(auth_key)
    print("set_expected_value api invoked with auth_key: {} for user_id: {}".format(auth_key, user_id))

    request.get_data()
    request_id = request.json.get("request_id")
    item_id = request.json.get("item_id")
    value = request.json.get("value")

    resp = {
        'status': "success",
        'result': "expectedvalue was set successfully"
    }
    http_status_code = 200

    file_path = "/data/{}".format(request_id)
    req_file = Path(file_path)
    if not req_file.exists():
        resp['status'] = "failure"
        resp["result"] = "invalid request_id"
        http_status_code = 404
    else:
        try:
            variations = None
            with open(file_path, "r") as f:
                variations = json.load(f)
            item = None
            for v in variations:
                if v.get("item_id") == item_id:
                    item = v
                    break
            if item == None:
                resp['status'] = "failure"
                resp["result"] = "invalid item_id"
                http_status_code = 404
            else:
                item["expected_value"] = value
                with open(file_path, "w+") as f:
                    f.write(json.dumps(variations))
                    f.write("\n")
        except Exception as e:
            print("Exception occured: {}".format(e))
            http_status_code = 500
            resp = {'status':'failure', 'result': "Setting expectedvalue failed"}

    return json.dumps(resp), http_status_code

@app.route("/variations", methods=['GET'])
def get_variations():
    print("------------------------------ new request: get_variations invoked -----------------------------")
    auth_key = request.headers.get('Authorization', None)
    if auth_key == None:
        resp = {
            "status": "failure",
            "message": "Please specify your auth_key in the Authorization header"
        }
        return json.dumps(resp), 401
    user_id = reverse_auth_key_cache.get_user_id(auth_key)
    print("get_variations api invoked with auth_key: {} for user_id: {}".format(auth_key, user_id))

    request_id = request.args.get("request_id", None)
    tag = request.args.get("tag", None)

    if request_id == None and tag == None:
        resp = {
            "status": "failure",
            "message": "Please specify either a request_id or tag as query parameter"
        }
        return json.dumps(resp), 400

    if request_id == None:
        print("Getting request_id from tag: {}".format(tag))
        request_id = tag_cache.get_request_id(tag)
        print("Got request_id: {} from tag cache".format(request_id))

    resp = {
        "status": "success",
        "message": "Fetched variations successfully"
    }
    http_status_code = 200
    try:
        file_path = "/data/{}".format(request_id)
        print("file_path: {}".format(file_path))
        req_file = Path(file_path)
        if not req_file.exists():
            resp['status'] = "failure"
            resp["result"] = "invalid request_id"
            http_status_code = 404
        else:
            variations = None
            with open(file_path, "r") as f:
                variations = json.load(f)
            resp['result'] = variations
            resp['request_id'] = request_id
        print("resp: {}".format(resp))
    except Exception as e:
        print("Exception occured: {}".format(e))
        http_status_code = 500
        resp = {'status':'failure', 'result': "Error fetching variations"}
    finally:
        return json.dumps(resp), http_status_code

@app.route("/testcases", methods=['POST'])
def testcases():
    print("------------------------------ new request: variations invoked -----------------------------")
    auth_key = request.headers.get('Authorization', None)
    if auth_key == None:
        resp = {
            "status": "failure",
            "message": "Please specify your auth_key in the Authorization header"
        }
        return json.dumps(resp), 401
    user_id = reverse_auth_key_cache.get_user_id(auth_key)
    print("testcases api invoked with auth_key: {} for user_id: {}".format(auth_key, user_id))

    global variations_request_schema
    if not variations_request_schema:
        variations_request_schema_str = ""
        with open('schemas/testcases-request.schema.json', 'r') as f:
            variations_request_schema_str = json.load(f)
        # print(variations_request_schema_str)
        # code = fastjsonschema.compile_to_code(variations_request_schema_str)
        # with open('jsonvalidator.py', 'w') as f:
        #     f.write(code)
        variations_request_schema = fastjsonschema.compile(variations_request_schema_str)

    resp = {}
    http_status_code = 200
    try:
        request.get_data()
        format = request.args.get("format", "json")
        high = int(request.args.get("count", "100"))
        payload = request.json
        print("fetched payload: {}".format(payload))
        variations_core_API_url = "{}/{}?format={}&count={}".format(zb_core_API_url, "variations", format, high)

        r1 = variations_request_schema(payload)
        print("validation succeeded")
        vc_resp = requests.post(variations_core_API_url, headers=json_only_http_headers, data=json.dumps(payload))
        vc_resp = vc_resp.json()
        request_id = util.get_random_id_32()
        items = []
        for idx, item in enumerate(vc_resp['result']):
            item['item_id'] = idx
            items.append(item)
        resp = {
            'status': vc_resp['status'],
            'result': items,
            'request_id': request_id
        }
        file_path = "/data/{}".format(request_id)
        with open(file_path, "w+") as f:
            f.write(json.dumps(items))
            f.write("\n")
        print("resp: {}".format(resp))
    except JsonSchemaException as e:
        print("Exception occured: {}".format(e))
        http_status_code = 500
        resp = {'status':'failure', 'result': str(e)}
    except Exception as e:
        print("Exception occured: {}".format(e))
        http_status_code = 500
        resp = {'status':'failure', 'result': "Data generation failed"}
    finally:
        return json.dumps(resp), http_status_code

@app.route("/variations", methods=['POST'])
def variations():
    print("------------------------------ new request: variations invoked -----------------------------")
    auth_key = request.headers.get('Authorization', None)
    if auth_key == None:
        resp = {
            "status": "failure",
            "message": "Please specify your auth_key in the Authorization header"
        }
        return json.dumps(resp), 401
    user_id = reverse_auth_key_cache.get_user_id(auth_key)
    print("variations api invoked with auth_key: {} for user_id: {}".format(auth_key, user_id))

    global variations_request_schema
    if not variations_request_schema:
        variations_request_schema_str = ""
        with open('schemas/variations-request.schema.json', 'r') as f:
            variations_request_schema_str = json.load(f)
        # print(variations_request_schema_str)
        # code = fastjsonschema.compile_to_code(variations_request_schema_str)
        # with open('jsonvalidator.py', 'w') as f:
        #     f.write(code)
        variations_request_schema = fastjsonschema.compile(variations_request_schema_str)

    resp = {}
    http_status_code = 200
    try:
        request.get_data()
        format = request.args.get("format", "json")
        high = int(request.args.get("count", "100"))
        payload = request.json
        print("fetched payload: {}".format(payload))
        variations_core_API_url = "{}/{}?format={}&count={}".format(zb_core_API_url, "variations", format, high)

        r1 = variations_request_schema(payload)
        print("validation succeeded")
        vc_resp = requests.post(variations_core_API_url, headers=json_only_http_headers, data=json.dumps(payload))
        vc_resp = vc_resp.json()
        request_id = util.get_random_id_32()
        items = []
        for idx, item in enumerate(vc_resp['result']):
            item['item_id'] = idx
            items.append(item)
        resp = {
            'status': vc_resp['status'],
            'result': items,
            'request_id': request_id
        }
        file_path = "/data/{}".format(request_id)
        with open(file_path, "w+") as f:
            f.write(json.dumps(items))
            f.write("\n")
        print("resp: {}".format(resp))
    except JsonSchemaException as e:
        print("Exception occured: {}".format(e))
        http_status_code = 500
        resp = {'status':'failure', 'result': str(e)}
    except Exception as e:
        print("Exception occured: {}".format(e))
        http_status_code = 500
        resp = {'status':'failure', 'result': "Data generation failed"}
    finally:
        return json.dumps(resp), http_status_code

if __name__ == '__main__':
    port = os.getenv("PORT")
    file_encoding = os.getenv("PYTHONIOENCODING")
    print("starting server on port: {}, python-io-encoding: {}".format(port, file_encoding))
    app.run(host= '0.0.0.0', debug=True, port=port)
    # app.run(debug=True, port=port)
