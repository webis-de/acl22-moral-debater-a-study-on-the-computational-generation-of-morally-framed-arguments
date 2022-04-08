# (C) Copyright IBM Corp. 2020.

from enum import Enum


class QueryType(Enum):
    simpleQuery=1
    complexQuery=2
    randomQuery=3


class SentenceQueryBase:
    def __init__(self, is_ordered, window_size,query_type=QueryType.simpleQuery):
        self.is_ordered = is_ordered
        self.slop = self.adjust_slot(window_size)
        self.query_type=query_type

    def adjust_slot(self, slop):
        return int(slop)

    def get_query_elements(self):
        raise NotImplementedError("Please Implement this method")

    def get_sentence_query(self):
        return {"type":self.query_type.name, "slop":self.slop,"inOrder": self.is_ordered, "clauses" : self.get_query_elements()}

    @staticmethod
    def _get_element(value, field):
        return {"value": value, "sentenceSearchableField": ["sentenceSearchableField", field]}

    @staticmethod
    def get_concept_element(value):
        return SentenceQueryBase._get_element(value, "Concept")

    @staticmethod
    def get_normalized_element(value):
        return SentenceQueryBase._get_element(value, "Normalized")

    @staticmethod
    def get_type_element(value):

        return SentenceQueryBase._get_element(value, "Type")
#///////
#// one list of sets where each set is a dict with type and field
#    // concept
#    // normalize
#    // type
#    // surface


class SimpleQuery(SentenceQueryBase):
    def __init__(self, is_ordered = True, window_size = 50):
        SentenceQueryBase.__init__(self, is_ordered, window_size, QueryType.simpleQuery)
        self.and_elements = list()

    def add_concept_element(self, values):
        # make sure values are written as wikipedia titles, with underscores replacing spaces
        renamed_values = [value.replace(" ", "_") for value in values]
        self.and_elements.append([self.get_concept_element(value) for value in renamed_values])

    def add_normalized_element(self, values):
        self.and_elements.append([self.get_normalized_element(value) for value in values])

    def add_type_element(self, values):
        # replace Sentiment and Causality by full names:  Sentiment -> WP2_sentiment
        # and  Causality -> WP2_action_verb_phrase , (or) WP3_connectors_2
        renamed_values = list()
        for value in values:
            if value == 'Sentiment':
                renamed_values.append('WP2_sentiment')
            elif value == 'Causality':
                renamed_values.append('WP2_action_verb_phrase')
                renamed_values.append('WP3_connectors_2')
            else: renamed_values.append(value)
        self.and_elements.append([self.get_type_element(value) for value in renamed_values])

    def get_query_elements(self):
        return self.and_elements


class RandomQuery(SentenceQueryBase):

    def __init__(self):
        SentenceQueryBase.__init__(self, False,1,QueryType.randomQuery)

    def get_query_elements(self):
        return []


class ConceptNumberQuery(SentenceQueryBase):
    def __init__(self, is_ordered, window_size, concept="Video_game_controversies"):
        SentenceQueryBase.__init__(self, is_ordered, window_size)
        self.concept = concept

    def get_query_elements(self):
        and_elements = list()
        #and_elements.append([self.get_type_element("Year")])
        #and_elements.append([self.get_normalized_element(x) for x in ["bans", "ban", "banned", "banning"]])
        and_elements.append([self.get_concept_element(self.concept)])
        and_elements.append([self.get_type_element(x) for x in ["Number", "Percent", "Money"]])
        return and_elements
