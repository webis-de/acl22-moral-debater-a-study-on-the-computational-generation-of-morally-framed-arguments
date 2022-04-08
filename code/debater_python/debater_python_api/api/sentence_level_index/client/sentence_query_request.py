# (C) Copyright IBM Corp. 2020.

import time


class SentenceQueryRequest():
    def __init__(self, query, start = 0, size = 12000, sentenceLength=(1,150), range = None):
        self.query = query
        self.sentenceMetaDataConstraint = self.get_length_constrains(sentenceLength[0],sentenceLength[1])
        self.duplicatesRemovalConfiguration = {"duplicatesFactor":1.1,"duplicatesRemovalOption":"NON_ALPHA_NUMERIC_DUPLICATES_REMOVAL"}
        self.scoringScope = "SentenceLevelScore"
        self.sentenceResponseFields = ["parentArticleId", "sentencePosition", "cleanSentenceText", "spanStart", "spanEnd", "sentenceConceptsTypesAndSpans","parentArticleId","sentencePosition"]
        if (range is not None):
            self.scoringScope = "ArticleLevelScore"
            self.articleMetaDataConstraint = {"type":"rangeFieldQuery",
                                              "condition1":{"first":"gt","second":int(time.mktime(range[0].timetuple()))*1000},
                                              "condition2":{"first":"lte","second":int(time.mktime(range[1].timetuple()))*1000},"field":["articleSearchableField","dateOfPublish"]}
        self.start = start
        self.size = size
        self.useProfile = False

    def get_length_constrains(self, min_len, max_len):
        return {"type": "rangeFieldQuery", "condition1": {"first": "gt", "second": min_len},
         "condition2": {"first": "lte", "second": max_len}, "field":
             ["sentenceMetadataSearchableFields", "sentenceLength"]}