# (C) Copyright IBM Corp. 2020.

import json


class ElasticSentencesSearchRes:
    def __init__(self, results_json):
        # keys: c (concept, options), s(start), e(end), t (type)
        self.totalHits = int(results_json["totalHits"])
        self.elasticTimeInMilli = int(results_json["elasticTimeInMilli"])
        self.totalTimeInMilli = int(results_json["totalTimeInMilli"])
        self.numOfDuplicationsRemoved = int(results_json["numOfDuplicationsRemoved"])
        self.sentences = [ElasticSentenceRes(x) for x in results_json["result"]]


class ElasticSentenceRes:
    def __init__(self, sentence,article=None):
        # keys: c (concept, options), s(start), e(end), t (type)
        self.sentenceConcepts = json.loads(sentence["sentenceConceptsTypesAndSpans"])
        self.spanStart = int(sentence["spanStart"])
        self.spanEnd = int(sentence["spanEnd"])
        self.sentencePosition = int(sentence["sentencePosition"])

        if article is None:
            self.cleanSentenceText = sentence["cleanSentenceText"]
            self.parentArticleId = sentence["parentArticleId"]
        else:
            self.cleanSentenceText = article.fullText[self.spanStart:self.spanEnd]
            self.parentArticleId = article.articleId

    def __str__(self):
        return self.cleanSentenceText

