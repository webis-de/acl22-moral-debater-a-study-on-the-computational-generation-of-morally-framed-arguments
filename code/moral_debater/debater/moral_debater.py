import os
import sys
import pickle

import json
import traceback
import time
import pandas as pd

from moral_debater.classifier import bert_moral_classification
from moral_debater.utils import moral_utils
from moral_debater.config import Config

from debater_python_api.api.debater_api import DebaterApi
from debater_python_api.api.sentence_level_index.client.sentence_query_base import SimpleQuery
from debater_python_api.api.sentence_level_index.client.sentence_query_request import SentenceQueryRequest
from debater_python_api.api.clients.narrative_generation_client import Polarity

ibm_api_key = Config.config().get(section='KEYS', option='ibm_api_key')
debater_api = DebaterApi(ibm_api_key)


def get_concepts(debater_api, topics):
    term_wikifier_client = debater_api.get_term_wikifier_client()
    annotation_arrays = term_wikifier_client.run(topics)
    return [[annotation['concept']['title'] for annotation in annotations] for annotations in annotation_arrays]


def retrieve_arguments_moral_concepts(debater_api, topic, moral_concepts, query_size=3000):
    searcher = debater_api.get_index_searcher_client()

    candidates = set()
    # Simple query
    query = SimpleQuery(is_ordered=True, window_size=12)
    if len(moral_concepts) > 0:
        query.add_concept_element(moral_concepts)
    query.add_normalized_element([x.lower() for x in topic.split()])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    result = searcher.run(query_request)
    candidates.update(result)

    # Concept causes something
    query = SimpleQuery(is_ordered=True, window_size=12)
    query.add_normalized_element([x.lower() for x in topic.split()])
    query.add_type_element(['Causality'])

    if len(moral_concepts) > 0:
        query.add_concept_element(moral_concepts)

    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))

    query = SimpleQuery(is_ordered=False, window_size=12)
    query.add_normalized_element([x.lower() for x in topic.split()])
    query.add_type_element(['Causality', 'Sentiment'])

    if len(moral_concepts) > 0:
        query.add_concept_element(moral_concepts)

    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))

    query = SimpleQuery(is_ordered=False, window_size=60)
    query.add_normalized_element(['surveys', 'analyses', 'researches', 'reports', 'research', 'survey'])
    query.add_normalized_element(['that'])
    query.add_normalized_element([x.lower() for x in topic.split()])

    if len(moral_concepts) > 0:
        query.add_concept_element(moral_concepts)

    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))

    return candidates


def retrieve_arguments(debater_api, topic, dc, query_size=3000):
    searcher = debater_api.get_index_searcher_client()

    candidates = set()
    # Simple query
    query = SimpleQuery(is_ordered=True, window_size=1)
    # query.add_concept_element(dc)
    query.add_normalized_element([x.lower() for x in topic.split()])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    result = searcher.run(query_request)
    candidates.update(result)

    # Concept causes something
    query = SimpleQuery(is_ordered=True, window_size=12)
    # query.add_concept_element(dc)
    query.add_normalized_element([x.lower() for x in topic.split()])
    query.add_type_element(['Causality'])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))

    query = SimpleQuery(is_ordered=False, window_size=12)
    # query.add_concept_element(dc)
    query.add_normalized_element([x.lower() for x in topic.split()])
    query.add_type_element(['Causality', 'Sentiment'])
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))

    query = SimpleQuery(is_ordered=False, window_size=60)
    query.add_normalized_element([x.lower() for x in topic.split()])
    query.add_normalized_element(['surveys', 'analyses', 'researches', 'reports', 'research', 'survey'])
    query.add_concept_element(dc)
    query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
    candidates.update(searcher.run(query_request))

    return candidates


def assign_morals(candidates):
    candidates_morals = bert_moral_classification.get_arg_morals(candidates)
          

    arguments_and_morals = [{'text': x[0], 'morals': x[1]} for x in zip(candidates, candidates_morals)]
    return arguments_and_morals


def extract_claims_and_evidences(debater_api, topic, sentences, evidence_threshold=0.6, claims_threshold=0.8,
                                 num_tries=1):
    tries = 0
    while True:
        try:
            # Find evidences from the candidate sentences
            print('finding evidences from candidate sentences')
            candidate_motion_pairs = [{'sentence': candidate, 'topic': topic} for candidate in sentences]
            
            start_time=time.time()
            evidence_scores = debater_api.get_evidence_detection_client().run(candidate_motion_pairs)
            
            print('time elapsed in run() of evidenceDetectionClient: ',time.time()-start_time)
            evidences = [sentences[i] for i in range(len(evidence_scores)) if evidence_scores[i] > evidence_threshold]
            print('Number of evidences: {}'.format(len(evidences)))

            # Find claims from the candidate sentences
            print('finding claims from candidate sentences')
            start_time=time.time()
            claim_scores = debater_api.get_claim_detection_client().run(candidate_motion_pairs)
            print('time elapsed in claim detection: ', time.time()-start_time)
            
            claim_sentences = [sentences[i] for i in range(len(claim_scores)) if claim_scores[i] > claims_threshold]
            print('Number of claims: {}'.format(len(claim_sentences)))

            # Extract claims from claims sentences
            start_time=time.time()
            claims = debater_api.get_claim_boundaries_client().run(sentences=claim_sentences)
            claims_text = [claim['claim'] for claim in claims]
            print('time elapsed in claim extraction: ', time.time()-start_time)

            return claims_text, evidences

        except ConnectionError as ce:
            print(ce)
            if tries >= num_tries:
                return None
            else:
                print('Re-trying.. {} out of {}'.format(tries, num_tries))
                tries += 1


def create_narrative(debater_api, topic, dc, polarity, claims, evidences, num_tries=1):
    tries = 0
    while True:
        try:
            # Combine claims and evidences together
            arguments = set()
            arguments.update(claims)
            arguments.update(evidences)

            arguments_list = [arg for arg in arguments if arg]

            # classify the arguments to pro arguments, and con arguments
            sentence_topic_dicts = [{'sentence': sentence, 'topic': topic} for sentence in arguments_list]
            pro_con_scores = debater_api.get_pro_con_client().run(sentence_topic_dicts)
            
            # and finally -- generate the speech
            narrative_generation_client = debater_api.get_narrative_generation_client()
            
            print(dc)
            print(topic)
            #             print(arguments_list)
            speech = narrative_generation_client.run(topic=topic, dc=dc, sentences=arguments_list,
                                                     pro_con_scores=pro_con_scores, polarity=polarity)
            if speech.paragraphs == None:
                print('Speech on {}  has no paragraphs...'.format(topic))
                speech.paragraphs = []

            return speech
        except ConnectionError as ce:
            print(ce)
            if tries >= num_tries:
                return None
            else:
                print('Re-trying.. {} out of {}'.format(tries, num_tries))
                tries += 1


def filter_argumentative_texts(argumentative_texts, moral_class, moral_dict):
    filtered_texts = []
    for arg in argumentative_texts:
        critiria = [len(moral_dict[key].intersection(arg['morals'])) > 0 for key in moral_dict.keys() if
                    key != moral_class]
        if len(arg['morals']) == 0 or any(critiria):
            continue
        filtered_texts.append(arg['text'])

    return filtered_texts


def collect_narratives_via_concepts(topics, moral_dict, query_size, use_cache=True):
    try:
        moral_concepts = moral_utils.get_moral_concepts(preprocess=False)
        moral_concepts = {key: [x.split('/')[-1] for x in item] for key, item in moral_concepts.items()}

        # 1. Get Wiki concepts from topics
        topic_concepts = get_concepts(debater_api, topics)
        print(topic_concepts)
        topic_narratives = {x: {'dc': topic_concepts[i]} for i, x in enumerate(topics)}

        for topic, topic_item in list(topic_narratives.items()):
            # 4. Generate moral narratives
            for moral_class_name, morals in moral_dict.items():
                print('Topic:{}, Moral:{}'.format(topic, moral_class_name))

                if '{}_arguments'.format(moral_class_name) not in topic_item or use_cache == False:
                    # 2. Collect arguments for topics
                    all_moral_concepts = []
                    for moral in morals:
                        all_moral_concepts += [x.split('/')[-1] for x in moral_concepts[moral]]

                    topic_item['{}_arguments'.format(moral_class_name)] = list(
                        retrieve_arguments_moral_concepts(debater_api, topic, all_moral_concepts,
                                                          query_size=query_size))

                moral_arguments = topic_item['{}_arguments'.format(moral_class_name)]
                # 5. Extract claims and evidences
                claims, evidences = extract_claims_and_evidences(debater_api, topic, moral_arguments,
                                                                 claims_threshold=0.8, evidence_threshold=0.6)

                for polarity in [Polarity.PRO, Polarity.CON]:
                    # 6. Create narrative
                    moral_narrative = create_narrative(debater_api, topic, topic_item['dc'][0], polarity, claims,
                                                       evidences)
                    if len(moral_narrative.paragraphs) < 3:
                        print('Narrative is empty...')
                    topic_item['{}_{}_narrative'.format(moral_class_name,
                                                        'pro' if polarity == Polarity.PRO else 'con')] = moral_narrative

            # 5. Generate general narrative
            if 'general_arguments' not in topic_item or use_cache == False:
                topic_item['general_arguments'] = list(
                    retrieve_arguments_moral_concepts(debater_api, topic, [], query_size=query_size))

            general_arguments = topic_item['general_arguments']
            # 5. Extract claims and evidences
            claims, evidences = extract_claims_and_evidences(debater_api, topic, general_arguments,
                                                             claims_threshold=0.8, evidence_threshold=0.6)
            for polarity in [Polarity.PRO, Polarity.CON]:
                # 6. Create narrative
                general_narrative = create_narrative(debater_api, topic, topic_item['dc'][0], polarity, claims,
                                                     evidences)
                if len(general_narrative.paragraphs) < 3:
                    print('General Narrative is empty...')
                topic_item['{}_{}_narrative'.format('general',
                                                    'pro' if polarity == Polarity.PRO else 'con')] = general_narrative



    except Exception as e:
        print(e)
    finally:
        return topic_narratives


# def collect_narratives_via_classifier(topics, moral_dict, query_size, old_narratives=None, use_cache=True):
#     try:

#         # 1. Get Wiki concepts from topics
#         topic_concepts = get_concepts(debater_api, topics)
#         topic_narratives = {}
#         for i, topic in enumerate(topics):
#             if topic in old_narratives:
#                 topic_narratives[topic] = old_narratives[topic]
#             else:
#                 topic_narratives[topic] = {'dc': topic_concepts[i]}

#         for topic, topic_item in list(topic_narratives.items()):

#             if 'arguments' not in topic_item or use_cache == False:
#                 # 2. Collect arguments for topics
#                 topic_item['arguments'] = retrieve_arguments(debater_api, topic, topic_item['dc'],
#                                                              query_size=query_size)
#                 # 3. Tag them with morals
#                 topic_item['arguments'] = assign_morals(topic_item['arguments'])

#             # 4. Generate moral narratives
#             for moral_class_name, morals in moral_dict.items():
#                 print('Topic:{}, Moral:{}'.format(topic, moral_class_name))
#                 moral_arguments = filter_argumentative_texts(topic_item['arguments'], moral_class_name, moral_dict)

#                 # 5. Extract claims and evidences
#                 claims, evidences = extract_claims_and_evidences(debater_api, topic, moral_arguments,
#                                                                  claims_threshold=0.8, evidence_threshold=0.6)

#                 for polarity in [Polarity.PRO, Polarity.CON]:
#                     narrative_key = '{}_{}_narrative'.format(moral_class_name,
#                                                              'pro' if polarity == Polarity.PRO else 'con')
#                     if narrative_key not in topic_item or use_cache == False:
#                         # 6. Create narrative
#                         moral_narrative = create_narrative(debater_api, topic, topic_item['dc'][0], polarity, claims,
#                                                            evidences)
#                         if len(moral_narrative.paragraphs) < 3:
#                             print('Narrative is empty...')
#                         topic_item[narrative_key] = moral_narrative

#             # 5. Generate general narrative
#             if 'general_pro_narrative' not in topic_item or 'general_con_narrative' not in topic_item or use_cache == False:
#                 all_arguments = [x['text'] for x in topic_item['arguments']]
#                 # 5. Extract claims and evidences
#                 claims, evidences = extract_claims_and_evidences(debater_api, topic, all_arguments,
#                                                                  claims_threshold=0.8, evidence_threshold=0.6)
#                 for polarity in [Polarity.PRO, Polarity.CON]:
#                     narrative_key = '{}_{}_narrative'.format('general', 'pro' if polarity == Polarity.PRO else 'con')
#                     if narrative_key not in topic_item or use_cache == False:
#                         # 6. Create narrative
#                         general_narrative = create_narrative(debater_api, topic, topic_item['dc'][0], polarity, claims,
#                                                              evidences)
#                         print('Topic:{}, Moral:{}'.format(topic, 'general'))
#                         if len(general_narrative.paragraphs) < 3:
#                             print('General Narrative is empty...')
#                         topic_item['{}_{}_narrative'.format('general',
#                                                             'pro' if polarity == Polarity.PRO else 'con')] = general_narrative


#     except Exception as e:
#         print(e)
#     finally:
#         return topic_narratives


def collect_narratives_via_classifier_stance(topics, moral_dict, query_size, polarity, claims_threshold=0.8, evidence_threshold=0.6, old_narratives={}):
    try:

        # 1. Get Wiki concepts from topics
        start_time=time.time()
        topic_concepts = get_concepts(debater_api, topics)
        
        print('time elapsed in get_concepts: ', time.time()-start_time)
        
        topic_narratives = {}
        for i, topic in enumerate(topics):
            if topic in old_narratives:
                topic_narratives[topic] = old_narratives[topic]
            else:
                topic_narratives[topic] = {'dc': topic_concepts[i]}

        for topic, topic_item in list(topic_narratives.items()):

            if 'arguments' not in topic_item:
                # 2. Collect arguments for topics
                start_time = time.time()
                topic_item['arguments'] = retrieve_arguments(debater_api, topic, topic_item['dc'],
                                                             query_size=query_size)
                
                print('time elapsed in retrieve_argument() is: ', time.time()-start_time)
                
                # 3. Tag them with morals
                start_time=time.time()
                topic_item['arguments'] = assign_morals(topic_item['arguments'])
                print('time elapsed in assigning of morals is: ', time.time()-start_time)
                
            # 4. Generate moral narratives
            for moral_class_name, morals in moral_dict.items():
                print('Topic:{}, Moral:{}'.format(topic, moral_class_name))
                
                start_time=time.time()
                moral_arguments = filter_argumentative_texts(topic_item['arguments'], moral_class_name, moral_dict)
                print('time elapsed in filtering of moral arguments: ',time.time()-start_time)
                
                # 5. Extract claims and evidences
                start_time=time.time()
                claims, evidences = extract_claims_and_evidences(debater_api, topic, moral_arguments,
                                                                 claims_threshold, evidence_threshold)
                print('time elapsed in claims and evidences extraction: ', time.time()-start_time)
                
                # for polarity is either con or pro
                narrative_key = '{}_{}_narrative'.format(moral_class_name,
                                                         polarity)
                
                
                
                if narrative_key not in topic_item:
                    # 6. Create narrative
                    polarity_enum = Polarity.PRO if polarity=='pro' else Polarity.CON
                    
                    start_time=time.time()
                    moral_narrative = create_narrative(debater_api, topic, topic_item['dc'][0], polarity_enum, claims,
                                                       evidences)
                    print('time elapsed in create_narrative(): ', time.time()-start_time)
                    if len(moral_narrative.paragraphs) < 3:
                        print('Narrative is empty...')
                    topic_item[narrative_key] = moral_narrative
                    
                
                

            # 5. Generate general narrative
#             if 'general_pro_narrative' not in topic_item or 'general_con_narrative' not in topic_item:
#                 all_arguments = [x['text'] for x in topic_item['arguments']]
#                 # 5. Extract claims and evidences
#                 claims, evidences = extract_claims_and_evidences(debater_api, topic, all_arguments,
#                                                                  claims_threshold=0.8, evidence_threshold=0.6)
#                 #for polarity in [Polarity.PRO, Polarity.CON]:
#                 narrative_key = '{}_{}_narrative'.format('general', polarity)
#                 if narrative_key not in topic_item:
#                     # 6. Create narrative
#                     general_narrative = create_narrative(debater_api, topic, topic_item['dc'][0], polarity, claims,
#                                                          evidences)
#                     print('Topic:{}, Moral:{}'.format(topic, 'general'))
#                     if len(general_narrative.paragraphs) < 3:
#                         print('General Narrative is empty...')
#                     topic_item['{}_{}_narrative'.format('general',polarity)] = general_narrative


    except Exception as e:
        print(e)
    finally:
        return topic_narratives


def analyse_speech(speech):
    if speech.error_message != None:
        print(speech.error_message)
        return None, None

    print('Number of Paragraphs:', len(speech.paragraphs))
    print('Number of arguments:', len(speech.arguments) if speech.arguments != None else 0)
    print('Number of filtered-out arguments:', len(speech.rows_for_filtered_elements) - 1)
    print('Number of key points:', len(speech.rows_for_kps_csv) - 1)
    print('Number of clusters:', len(speech.clusters))
    print('Clusters:', [x.theme for x in speech.clusters])
    print('====')
    kps_df = pd.DataFrame(speech.rows_for_kps_csv)
    filtered_elements_df = pd.DataFrame(speech.rows_for_filtered_elements)

    return kps_df, filtered_elements_df