# (C) Copyright IBM Corp. 2020.

import requests
import json
import logging
from debater_python_api.api.sentence_level_index.client.elastic_search_sentence_res import ElasticSentencesSearchRes
from debater_python_api.api.sentence_level_index.client.sentence_query_request import SentenceQueryRequest
from debater_python_api.api.sentence_level_index.client.sentence_query_base import ConceptNumberQuery, SimpleQuery, \
    SentenceQueryBase
from debater_python_api.api.sentence_level_index.client.article_retrieval_request import ArticleRetrievalRequest
from debater_python_api.api.sentence_level_index.client.elastic_search_article_res import ElasticArticleRetrievalRes


class IndexServiceClient:
    def __init__(self, url,index_name,service_version, apikey):
        self.url = url
        self.index_name = index_name
        self.service_version = service_version
        self.apikey=apikey

    def post(self,endpoint, body):
        headers = {'content-type': "application/json;charset=UTF-8",
                   'apikey': self.apikey}
        result = requests.post(endpoint,
                               headers=headers, data=body)
        if result.status_code != 200:
            msg = 'Failed sending POST to server (%d): %s' % (result.status_code, result.text)
            raise ConnectionError(msg)
        return result.content.decode('utf8')

    def run_sentence_level_query(self,query):
        request_endpoint = "{}/search/{}/ln_document/andOfOrs?version={}".format(self.url, self.index_name,
                                                                            self.service_version)

        # this ugly code is here because the one of the fiels the json object should contains is called "from",
        # however, this cannot be a name of a member in Python :(
        query_dict = vars(query)
        query_dict["from"] = query_dict["start"]
        query_dict.pop("start")
        query_json = json.dumps(query_dict)
        logging.info ("query:%s",query_json)
        res_str = self.post(request_endpoint,str(query_json))
        res = json.loads(res_str)
        results = ElasticSentencesSearchRes(res)
        return results

    def get_articles_by_ids(self,ids):
        endpoint = "{}/search/{}/ln_document/getArticlesByIds?version={}".format(self.url,self.index_name,self.service_version)
        # url = "http://ace11:3000/search/2_gas_pipeline_mexico_v1/ln_document/andOfOrs?version=2.0"
        query_request = ArticleRetrievalRequest(
            articleIds=ids)
        query_json = json.dumps(query_request.articleIds)
        client_service = IndexServiceClient()
        res_str = client_service.post(endpoint,str(query_json))
        res = json.loads(res_str)
        articles = [ElasticArticleRetrievalRes(article) for article in res['results']]
        return articles


def print_elastic_sentence_query_search(res):
    for sentence in res:
        print("sentence position:%d\n%s" % (sentence.sentencePosition,sentence.cleanSentenceText))
        print("_____________")



def print_article_retrieval_results(res):

    for article in res:
        print("date: %s articleId: %s\ntitle: %s\nfull text: %s" % (article.dateOfPublish, article.articleId, article.title,article.fullText))
        print("_____________")


def sentence_query_main():
    #url = "http://ace11:3000/search/2_gas_pipeline_mexico_v1/ln_document/andOfOrs?version=2.0"
    query = ConceptNumberQuery(False, window_size=50)
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), start=0, size=12000)
    client_service = IndexServiceClient()
    results = client_service.run_sentence_level_query(query_request)
    print_elastic_sentence_query_search(results.sentences)


def random_query_main():
    query = SimpleQuery(queryElements = [
        [SentenceQueryBase.get_normalized_element("expert"), SentenceQueryBase.get_normalized_element("experts")],
        [SentenceQueryBase.get_normalized_element("IBM"), SentenceQueryBase.get_normalized_element("I.B.M"), SentenceQueryBase.get_normalized_element("ibm"), SentenceQueryBase.get_normalized_element("i.b.m")]],
        is_ordered = True, window_size = 50)
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), start=0, size=12000)
    client_service = IndexServiceClient()
    results = client_service.run_sentence_level_query(query_request)
    #print(results)
    print("# of sentences: %d" % len(results.sentences))
    for sentence in results.sentences:
        print(sentence.cleanSentenceText)
        print("_____________")




def article_retrieval_main():
    client_service = IndexServiceClient()
    articles = client_service.get_articles_by_ids(["24553890812", "24494998693", "24388452499", "24431946188", "24431946236", "24553890969",
                        "24431946279",
                        "24329960924", "24431946376", "24553890888", "24431946411", "24553890765", "24431946398"])
    print_article_retrieval_results(articles)





if __name__ == "__main__":
    #article_retrieval_main()
    #random_query_main()
    sentence_query_main()