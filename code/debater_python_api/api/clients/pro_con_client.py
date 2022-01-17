# (C) Copyright IBM Corp. 2020.
import datetime
import logging

from debater_python_api.api.clients.abstract_client import AbstractClient

endpoint='/score/'

class ProConClient(AbstractClient):

    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://pro-con.debater.res.ibm.com'

    def run(self, sentence_topic_dicts):
        time_stamp_start = datetime.datetime.now().timestamp()
        for i, dict_ in enumerate(sentence_topic_dicts):
            if len(dict_['sentence']) == 0:
                raise RuntimeError('empty input sentence among the inputs at index {}'.format(i))
            if len(dict_['topic']) == 0:
                raise RuntimeError('empty imput topic among the inputs at index {}'.format(i))
        pairs = [[dict_['sentence'], dict_['topic']] for dict_ in sentence_topic_dicts]

        scores = self.run_in_batch(list_name='sentence_topic_pairs', list=pairs, other_payload={}, endpoint=endpoint)

        scores = [dict['pro'] - dict['con'] for dict in scores]

        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('pro_con_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))

        return scores

