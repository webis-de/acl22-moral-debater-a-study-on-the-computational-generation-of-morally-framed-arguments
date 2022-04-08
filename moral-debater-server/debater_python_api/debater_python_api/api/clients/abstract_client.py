# (C) Copyright IBM Corp. 2020.

import datetime
import logging
import pickle
import time
import traceback

import requests
from tqdm import tqdm

from debater_python_api.utils.general_utils import validate_api_key_or_throw_exception, \
    get_default_request_header

batch_size = 500
empty_string_placeholder = '-------'


class AbstractClient:
    def __init__(self, apikey):
        validate_api_key_or_throw_exception(apikey)
        self.apikey = apikey
        self.host = ''
        self.show_process = True

    def set_show_process(self, show_process):
        self.show_process = show_process

    def set_host(self, host):
        self.host = host

    def replace_empty_string_by_spaces(self, st):
        if st:
            return st
        return empty_string_placeholder

    def run_in_batch(self, list_name, list, other_payload, list_from_json_getter=lambda x: x, endpoint='', timeout=60):
        result = []
        batches = [list[i:i + batch_size] for i in range(0, len(list), batch_size)]
        if self.show_process:
            progress = tqdm(total=len(list), desc=self.__class__.__name__)
        for batch in batches:
            batch = [self.replace_empty_string_by_spaces(sentence) for sentence in batch]
            if self.payload_is_a_dict(list_name, other_payload):
                payload = other_payload.copy()
                payload[list_name] = batch
                batch_result = self.do_run(payload, endpoint=endpoint, timeout=timeout)
            else:
                batch_result = self.do_run(batch, endpoint=endpoint, timeout=timeout)
            result.extend(list_from_json_getter(batch_result))
            if self.show_process:
                progress.update(len(batch))
        return result

    def payload_is_a_dict(self, list_name, other_payload):
        return list_name is not None and other_payload is not None

    def do_run(self, payload, endpoint='', updates_to_headers={}, files=None, retries=0, timeout=60):
        headers = get_default_request_header(self.apikey)
        headers.update(updates_to_headers)

        while True:
            try:
                if files is None:
                    response = requests.post(url=self.host+endpoint, json=payload, headers=headers, timeout=timeout)
                else:
                    response = requests.post(url=self.host+endpoint, json=payload, headers=headers, files=files, timeout=timeout)
                if response.status_code == 200:
                    return response.json()

                dump = {'url': self.host+endpoint, 'json': payload, 'headers': headers}
                x = datetime.datetime.now()
                with open(self.__class__.__name__ + x.strftime("%Y-%m-%d-%H-%M-%S") + '.pkl', 'wb') as f:
                    pickle.dump(dump, f, pickle.HIGHEST_PROTOCOL)

                error, message, status = self.get_status_error_msg(response)
                msg = "Can't access server at {}. Status code: {} - {}. Message: {}".format(self.host+endpoint, status, error, message)
            except Exception as e:
                track = traceback.format_exc()
                msg = "Can't access server at {}. Exception: {}".format(self.host+endpoint, track)

            retries -= 1
            if retries < 0:
                raise ConnectionError(msg)
            else:
                logging.warning('%s, retries left: %d' % (msg, retries))
                time.sleep(10)

    def get_status_error_msg(self, response):
        status = ''
        error = ''
        message = ''
        try:
            json = response.json()
            if 'status' in json:
                status = json['status']
            if 'error' in json:
                error = json['error']
            if 'message' in json:
                message = json['message']
        except ValueError:
            status = response.status_code
            error = response.reason
            message = response.text
        return error, message, status

    @staticmethod
    def run_client_from_dump(file):
        with open(file, 'rb') as f:
            dump = pickle.load(f)
            response = requests.post(url=dump['url'], json=dump['json'], headers=dump['headers'])
            if response.status_code != 200:
                raise ConnectionError(
                    "Can't access server. Status code: {} - {}".format(response.status_code, response.reason))

            return response.json
