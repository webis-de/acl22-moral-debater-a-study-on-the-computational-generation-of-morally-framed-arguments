# (C) Copyright IBM Corp. 2020.
import os
from debater_python_api.api.clients.narrative_generation_client import Polarity
from debater_python_api.api.debater_api import DebaterApi
from debater_python_api.api.sentence_level_index.client.sentence_query_base import SimpleQuery
from debater_python_api.api.sentence_level_index.client.sentence_query_request import SentenceQueryRequest

query_size = 3000
topic = 'We should ban algorithmic trading'
dc = 'Algorithmic_trading'

if __name__ == "__main__":
    api_key = os.environ['API_KEY']
    debater_api = DebaterApi(api_key)

    # Search relevant sentences from corpus
    ####start##part1
    searcher = debater_api.get_index_searcher_client()
    candidates = set()

    query = SimpleQuery(is_ordered=True, window_size=1)
    query.add_concept_element([dc])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    result = searcher.run(query_request)
    candidates.update(result)
    ####end##part1

    ####start##part2
    query = SimpleQuery(is_ordered=True, window_size=12)
    query.add_normalized_element(['that'])
    query.add_concept_element([dc])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))
    ####end##part2

    ####start##part3
    query = SimpleQuery(is_ordered=True, window_size=12)
    query.add_concept_element([dc])
    query.add_type_element(['Causality'])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))
    ####end##part3

    ####start##part4
    query = SimpleQuery(is_ordered=False, window_size=7)
    query.add_concept_element([dc])
    query.add_type_element(['Causality', 'Sentiment'])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))
    ####end##part4

    ####start##part5
    query = SimpleQuery(is_ordered=False, window_size=60)
    query.add_normalized_element(['observation', 'researches', 'explorations', 'meta - analyses', 'observations',
                                  'documentation', 'exploration', 'studies', 'poll', 'polls', 'meta analyses',
                                  'surveys', 'analyses', 'reports', 'research', 'survey'])
    query.add_normalized_element(['that'])
    query.add_concept_element([dc])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))
    ####end##part5


    ####start##part6
    query = SimpleQuery(is_ordered=False, window_size=10)
    query.add_normalized_element(['observation', 'researches', 'explorations', 'meta - analyses', 'observations',
                                  'documentation', 'exploration', 'studies', 'poll', 'polls', 'meta analyses',
                                  'surveys', 'analyses', 'reports', 'research', 'survey'])
    query.add_type_element(['Person'])
    query.add_normalized_element(['that'])
    query.add_concept_element([dc])
    query.add_type_element(['Causality'])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))
    ####end##part6


    candidates_list = list(candidates)
    print('Number of candidates: {}'.format(len(candidates_list)))

    ####start##part7
    # Find evidences from the candidate sentences
    candidate_motion_pairs = [{'sentence' : candidate, 'topic' : topic} for candidate in candidates_list]
    evidence_scores = debater_api.get_evidence_detection_client().run(candidate_motion_pairs)
    evidence_threshold = 0.6

    evidences = [candidates_list[i] for i in range(len(evidence_scores)) if evidence_scores[i] > evidence_threshold]
    print('Number of evidences: {}'.format(len(evidences)))

    # Find claims from the candidate sentences
    claim_scores = debater_api.get_claim_detection_client().run(candidate_motion_pairs)
    claims_threshold = 0.8
    claim_sentences = [candidates_list[i] for i in range(len(claim_scores)) if claim_scores[i] > claims_threshold]
    print('Number of claims: {}'.format(len(claim_sentences)))

    # Extract claims from claims sentences
    claims = debater_api.get_claim_boundaries_client().run(sentences=claim_sentences)
    claims_text = [claim['claim'] for claim in claims]
    ####end##part7


    ####start##part8
    # Combine claims and evidences together
    arguments = set()
    arguments.update(claims_text)
    arguments.update(evidences)

    arguments_list = [arg for arg in arguments if arg]


    # classify the arguments to pro arguments, and con arguments
    print('Running pro con:')
    sentence_topic_dicts = [{'sentence' : sentence, 'topic' : topic } for sentence in arguments_list]
    pro_con_scores = debater_api.get_pro_con_client().run(sentence_topic_dicts)

    # customize opening statement
    opening_statement_customization_dict = {
        'type' : 'openingStatement',
        'items':
            [
                {
                    'key': 'Opening_statement',
                    'value': 'Greetings, Partners! The following speech is based on <NUM_SBC_ARGUMENTS_SUGGESTED> arguments mined from Wikipedia, contesting the notion that <MOTION>.',
                    'itemType' : 'single_string'
                }
            ]
    }

    # and finally -- generate the speech
    print('Generating speech:')
    narrative_generation_client = debater_api.get_narrative_generation_client()
    speech = narrative_generation_client.run(topic=topic, dc=dc, sentences=arguments_list,
                                             pro_con_scores=pro_con_scores, polarity=Polarity.CON, customizations=[opening_statement_customization_dict])
    print('\n\nSpeech: \n')
    print(speech)
    ####end##part8
