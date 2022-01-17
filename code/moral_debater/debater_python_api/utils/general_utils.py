# (C) Copyright IBM Corp. 2020.

import os
import configparser
import re
import pandas as pd

def get_config(module_name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    properties_file = os.path.join(dir_path, '../api/clients/config', module_name+'.properties')
    config = configparser.RawConfigParser()
    config.read(properties_file)
    return config


def get_resource_file(file_name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    resource_file = os.path.join(dir_path, '../examples/resources', file_name)
    return resource_file


def get_default_request_header(apikey):
    return {'accept-encoding': 'gzip, deflate',
            'content-type': 'application/json',
            'charset': 'UTF-8',
            'apikey': apikey}


def validate_api_key_or_throw_exception(apikey):

    if len(apikey) != 35 or re.match('^[0-9a-zA-Z]+$', apikey) is None:
        raise ValueError("api key is not valid")
    return True

from logging import getLogger, getLevelName, Formatter, StreamHandler
def init_logger():
    log = getLogger()
    log.setLevel(getLevelName('INFO'))
    log_formatter = Formatter("%(asctime)s [%(levelname)s] %(filename)s %(lineno)d: %(message)s [%(threadName)s] ")

    console_handler = StreamHandler()
    console_handler.setFormatter(log_formatter)
    log.handlers = []
    log.addHandler(console_handler)

def read_tups_from_csv(filename, col1, col2, limit):
    df = pd.read_csv(filename)
    id_text = list(zip(df[col1], df[col2]))
    if limit > 0:
        id_text = id_text[:limit]
    return id_text
