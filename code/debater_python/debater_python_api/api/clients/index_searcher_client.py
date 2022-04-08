# (C) Copyright IBM Corp. 2020.

import json
import logging
import datetime

from debater_python_api.api.clients.abstract_client import AbstractClient
from debater_python_api.api.sentence_level_index.client.elastic_search_sentence_res import ElasticSentencesSearchRes


class IndexServiceClient(AbstractClient):

    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://wiki-index.debater.res.ibm.com'
        self.default_index_name = 'wiki18_v1'
        self.version = '3.0'

    def get_endpoint(self, endpoit_var):
        return '/search/'+ self.default_index_name + '/ln_document/' + endpoit_var + '?version=' + self.version

    def run(self, query, return_full_record=False):
        # this ugly code is here because one of the fields the json object should contain is called "from",
        # however, this cannot be a name of a member in Python :(
        time_stamp_start = datetime.datetime.now().timestamp()
        query_dict = vars(query)
        query_dict["from"] = query_dict["start"]
        query_dict.pop("start")
        logging.info ("customer of api_key {}, submitted a query: {}".format(self.apikey, json.dumps(query_dict)))
        res = self.do_run(query_dict, endpoint=self.get_endpoint('andOfOrs'))
        results = ElasticSentencesSearchRes(res)
        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('index_searcher_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))
        if return_full_record:
            return results.sentences
        return [sentence.cleanSentenceText.strip() for sentence in results.sentences]

    def get_articles(self, article_retrieval_request):
        result = self.run_in_batch(list_name=None, list=article_retrieval_request.articleIds,
                                other_payload=None, endpoint=self.get_endpoint('getArticlesByIds'),
                                list_from_json_getter=lambda x: x['results'])
        return result
