# (C) Copyright IBM Corp. 2020.
import datetime
import logging

from debater_python_api.api.clients.abstract_client import AbstractClient

endpoint = '/score/'

class ClaimBoundariesClient(AbstractClient):

    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://claim-boundaries.debater.res.ibm.com'

    def run(self, sentences):
        time_stamp_start = datetime.datetime.now().timestamp()
        boundaries = self.run_in_batch(list_name='sentences', list=sentences, other_payload={}, endpoint=endpoint,
                                       timeout=100)
        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('claim_boundaries_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))
        return [{'span':(boundaries[j][0], boundaries[j][1]), 'claim':sentences[j][boundaries[j][0]:boundaries[j][1]]} for j in range(len(sentences))]
