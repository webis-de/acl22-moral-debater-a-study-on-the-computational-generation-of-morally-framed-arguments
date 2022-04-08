import datetime
import logging
import time
import traceback
from debater_python_api.api.clients.abstract_client import AbstractClient

class KpPairsInferClient(AbstractClient):
    def __init__(self, apikey, host):
        AbstractClient.__init__(self, apikey)
        self.host = host

    def _post(self, endpoint, body, use_cache=True, retries=10, timeout=60):
        logging.info('client calls service (post): ' + self.host+endpoint)
        updates_to_headers = {}
        if not use_cache:
            updates_to_headers['cache-control'] = 'no-cache'

        return self.do_run(endpoint=endpoint, payload=body, updates_to_headers=updates_to_headers, timeout=timeout, retries=retries)

    # argument_kp_pairs: list of lists with two strings, the first is an argument and the second is a kp. the returned scores are not symmetric
    def get_pairs_inference_scores(self, argument_kp_pairs, batch_size, use_cache=True, retries=10, timeout=60):
        try:
            start_time = datetime.datetime.now()
            scores = []
            batch_data_list = [argument_kp_pairs[x:x + batch_size] for x in range(0, len(argument_kp_pairs), batch_size)]
            for batch in batch_data_list:
                start_time_batch = datetime.datetime.now()
                scores.extend(self._post('/score/', {'pairs': batch}, use_cache,  retries=retries, timeout=timeout))
                logging.info("inferred %d out of %d pairs, batch took: %s" % (len(scores), len(argument_kp_pairs), str(datetime.datetime.now() - start_time_batch)))
            logging.info("inferred %d batches, num_scores: %d,  took: %s" % (len(batch_data_list), len(scores), str(datetime.datetime.now() - start_time)))
            return scores
        except Exception as e:
            track = traceback.format_exc()
            logging.info(track)
            raise Exception('failed to retrieve pairs scores', e)