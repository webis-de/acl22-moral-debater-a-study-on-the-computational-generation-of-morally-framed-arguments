# (C) Copyright IBM Corp. 2020.
import datetime
import logging
from debater_python_api.api.clients.abstract_client import AbstractClient
from debater_python_api.api.clients.term_wikifier_client import TermWikifierClient

endpoint= '/api/scores/TermRelater/pairs'

placeholder = 'placeholder'
nan = float('nan')


class TermRelaterClient(AbstractClient):

    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://tr.debater.res.ibm.com'
        self.auto_wikification = False
        self.term_wikifier_client = TermWikifierClient(apikey)

    def set_auto_wikification(self, auto_wikification):
        self.auto_wikification = auto_wikification

    def run(self, term_pairs):
        time_stamp_start = datetime.datetime.now().timestamp()
        if self.auto_wikification:
            flatten = [item for sublist in term_pairs for item in sublist]
            wikified_flatten = self.term_wikifier_client.run(flatten)
            concepts_flatten = [mention[0]['concept']['title'] if len(mention)==1 else placeholder
                                for mention in wikified_flatten]
            term_pairs = [list(a) for a in zip(concepts_flatten[0::2], concepts_flatten[1::2])]
        pairs = [{'first': term_pair[0], 'second': term_pair[1]} for term_pair in term_pairs]
        scores = self.run_in_batch(list_name=None, list=pairs, other_payload=None, endpoint=endpoint)
        fixed_scores = [score if term_pairs[i][0] != placeholder and term_pairs[i][1] != placeholder
                        else nan for i, score in enumerate(scores)]
        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('term_relater_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))
        return fixed_scores
