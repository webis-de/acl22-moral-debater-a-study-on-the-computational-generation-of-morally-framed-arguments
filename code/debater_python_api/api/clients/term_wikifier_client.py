# (C) Copyright IBM Corp. 2020.
import datetime
import logging
from debater_python_api.api.clients.abstract_client import AbstractClient

endpoint = '/TermWikifier/v2/annotate/'

class TermWikifierClient(AbstractClient):
    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://tw.debater.res.ibm.com'

    def run(self, texts):
        time_stamp_start = datetime.datetime.now().timestamp()
        texts_to_annotate = [{'text': text, 'contextTitles': []} for text in texts]
        payload = {
            'config': '',
            'contextTitles': [],
            'contextText': ''
        }
        sentences = self.run_in_batch(list_name='textsToAnnotate', list=texts_to_annotate, other_payload=payload,
                                 list_from_json_getter=lambda x:x['annotations'], endpoint=endpoint)
        term_wikifier_result = []
        for sentence in sentences:
            sentence_results = [{
                'span' : (annotation['spanStart'], annotation['spanEnd']),
                'cleanText' : annotation['cleanText'],
                'concept' : {'title' : annotation['title'] ,
                             'inlinks' : int(annotation['inlinks'])}
            } for annotation in sentence if annotation['title'] is not None]
            term_wikifier_result.append(sentence_results)

        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('term_wikifier_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))

        return term_wikifier_result
