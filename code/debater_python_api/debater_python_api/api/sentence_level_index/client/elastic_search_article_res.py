# (C) Copyright IBM Corp. 2020.

import datetime

from debater_python_api.api.sentence_level_index.client.elastic_search_sentence_res import ElasticSentenceRes


class ElasticArticleRetrievalRes:
    def __init__(self, article_retrieval_res):
        articleFields = article_retrieval_res["articleFields"];

        self.articleLength = articleFields["articleLength"]
        self.author = articleFields["author"]
        self.articleId = articleFields["articleId"]
        self.fullText = articleFields["fullText"]
        self.publisher = articleFields["publisher"]
        self.dateOfPublish = datetime.datetime.fromtimestamp(int(articleFields["dateOfPublish"])/1000)
        self.mediaType = articleFields["mediaType"]
        self.sourceName = articleFields["sourceName"]
        self.title = articleFields["title"]

        self.sentences = [ElasticSentenceRes(sentence,self) for  sentence in article_retrieval_res["sentencesFields"]]
        self.sentences.sort(key=lambda x:x.sentencePosition)