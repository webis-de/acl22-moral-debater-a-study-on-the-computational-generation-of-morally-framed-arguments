# (C) Copyright IBM Corp. 2020.
import datetime
import logging
from debater_python_api.api.clients.abstract_client import AbstractClient

endpoint = '/score/'

class ArgumentQualityClient(AbstractClient):
    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://arg-quality.debater.res.ibm.com'

    def run(self, sentence_topic_dicts, timeout=60):
        time_stamp_start = datetime.datetime.now().timestamp()
        for sentence_topic_dict in sentence_topic_dicts:
            if (len(sentence_topic_dict['sentence']) == 0 or len(sentence_topic_dict['topic']) == 0):
                raise RuntimeError('empty input argument in pair {}'.format(sentence_topic_dict))
        pairs = [[dict_item['sentence'], dict_item['topic']] for dict_item in sentence_topic_dicts]
        scores = self.run_in_batch(list_name='sentence_topic_pairs', list=pairs, other_payload={}, endpoint=endpoint, timeout=timeout)
        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('argument_quality_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))

        return scores
