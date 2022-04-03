import os
import sys
import pickle

import json
import traceback
import time
import pandas as pd

from moral_debater.utils import moral_utils
from moral_debater.config import Config

from debater_python_api.api.debater_api import DebaterApi
from debater_python_api.api.sentence_level_index.client.sentence_query_base import SimpleQuery
from debater_python_api.api.sentence_level_index.client.sentence_query_request import SentenceQueryRequest
from debater_python_api.api.clients.narrative_generation_client import Polarity

from transformers import BertTokenizer, BertForSequenceClassification
import numpy as np
from spacy.lang.en import English


class MoralDebater(object):

    def __init__(self):
        ibm_api_key = Config.config().get(section='KEYS', option='ibm_api_key')
        model_path = Config.config().get(section='DATAPATHS', option='moral_classifier_path')

        self.debater_api = DebaterApi(ibm_api_key)

        self.moral_tokenizer = BertTokenizer.from_pretrained(model_path)
        self.moral_model = BertForSequenceClassification.from_pretrained(model_path, return_dict=True)

        self.sentencizer = English()
        self.sentencizer.add_pipe(self.sentencizer.create_pipe('sentencizer'))
        
        self.cache = {}
        self.cache_path = './cache_path.json'
        
        if os.path.exists(self.cache_path):
            print('Loading cache...')
            self.cache = json.load(open(self.cache_path))

    def get_concepts(self, topic):
        term_wikifier_client = self.debater_api.get_term_wikifier_client()
        annotation_arrays = term_wikifier_client.run([topic])
        #return [[annotation['concept']['title'] for annotation in annotations] for annotations in annotation_arrays]
        return [annotation['concept']['title'] for annotation in annotation_arrays[0]]

    def retrieve_arguments(self, topic, dc, query_size=3000):

        searcher = self.debater_api.get_index_searcher_client()
        
        print('Running first query...')
        candidates = set()
        # Simple query
        query = SimpleQuery(is_ordered=True, window_size=1)
        # query.add_concept_element(dc)
        query.add_normalized_element([x.lower() for x in topic.split()])
        query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
        result = searcher.run(query_request)
        candidates.update(result)
        
        print('Running second query...')
        # Concept causes something
        query = SimpleQuery(is_ordered=True, window_size=12)
        # query.add_concept_element(dc)
        query.add_normalized_element([x.lower() for x in topic.split()])
        query.add_type_element(['Causality'])
        query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=query_size, sentenceLength=(7, 60))
        candidates.update(searcher.run(query_request))

        print('Running third query...')
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

        return list(candidates)


    def get_arg_morals(self, args):
        moral2id = {0: 'authority', 1: 'care', 2: 'fairness', 3: 'loyalty', 4: 'purity'}
        output_morals = []
        args_sents = [[sent.text for sent in self.sentencizer(arg).sents] for arg in args]
        
        for arg_sents in args_sents:
            if len(arg_sents) == 0:
                output_morals.append([])
                continue

            input_tokens = self.moral_tokenizer(arg_sents, max_length=512, return_tensors='pt', truncation=True, padding=True, add_special_tokens=True)
            
            outputs = self.moral_model(input_tokens['input_ids'])[0].detach().cpu().numpy()
            
            scores  = list(np.exp(outputs) / np.exp(outputs).sum(-1, keepdims=True))
            morals  = [moral2id[np.argmax(s)] for s in scores if np.max(s) > 0.5]
            output_morals.append(list(set(morals)))
            

        return output_morals

    def assign_morals(self, candidates):
        candidates_morals = self.get_arg_morals(candidates)
        arguments_and_morals = [{'text': x[0], 'morals': x[1]} for x in zip(candidates, candidates_morals)]
        return arguments_and_morals


    def extract_claims_and_evidences(self, topic, sentences, evidence_threshold=0.6, claims_threshold=0.8,
                                     num_tries=1):
        tries = 0
        while True:
            try:
                # Find evidences from the candidate sentences
                print('finding evidences from candidate sentences')
                candidate_motion_pairs = [{'sentence': candidate, 'topic': topic} for candidate in sentences]
                
                evidence_scores = self.debater_api.get_evidence_detection_client().run(candidate_motion_pairs)
                
                evidences = [sentences[i] for i in range(len(evidence_scores)) if evidence_scores[i] > evidence_threshold]
                print('Number of evidences: {}'.format(len(evidences)))

                # Find claims from the candidate sentences
                print('finding claims from candidate sentences')
                claim_scores = self.debater_api.get_claim_detection_client().run(candidate_motion_pairs)
                
                claim_sentences = [sentences[i] for i in range(len(claim_scores)) if claim_scores[i] > claims_threshold]
                print('Number of claims: {}'.format(len(claim_sentences)))

                # Extract claims from claims sentences
                claims = self.debater_api.get_claim_boundaries_client().run(sentences=claim_sentences)
                claims_text = [claim['claim'] for claim in claims]

                return claims_text, evidences

            except ConnectionError as ce:
                print(ce)
                if tries >= num_tries:
                    return None
                else:
                    print('Re-trying.. {} out of {}'.format(tries, num_tries))
                    tries += 1


    def create_narrative(self, topic, dc, polarity, claims, evidences, num_tries=1):
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
                pro_con_scores = self.debater_api.get_pro_con_client().run(sentence_topic_dicts)
                
                # and finally -- generate the speech
                narrative_generation_client = self.debater_api.get_narrative_generation_client()
                

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


    def filter_argumentative_texts(self, argumentative_texts, morals):
        filtered_texts = []
        for arg in argumentative_texts:
            if len(morals.intersection(arg['morals'])) > 0:
                filtered_texts.append(arg['text'])

        return filtered_texts


    def collect_narratives_via_classifier(self, topic, moral_dict, query_size, polarity, claims_threshold=0.8, evidence_threshold=0.6):
        #try:
            
        print('Topic:', topic, ' moral_dict: ', moral_dict, ' query_size:', query_size, ' claims_threshold:', claims_threshold, 'evidence_threshold:', evidence_threshold)

        topic_item = self.cache[topic] if topic in self.cache else None
        if topic_item == None or topic_item['query_size'] < query_size: #if we are requireing more arguments then we have to update the chat
            topic_item = {}
            # 1. Get Wiki concepts from topics
            topic_item['dc'] = self.get_concepts(topic)
            # 2. Collect arguments for topics
            topic_item['arguments'] = self.retrieve_arguments(topic, topic_item['dc'], query_size=query_size)
            topic_item['query_size'] = query_size
            print('Number of retrieved arguments:', len(topic_item['arguments']))
            self.cache[topic] = topic_item

        else:
            print('Load topic from the cache!!')
            topic_item = self.cache[topic]

        if 'claims_and_evidences' not in topic_item or topic_item['claims_and_evidences']['claims_threshold'] != claims_threshold or topic_item['claims_and_evidences']['evidence_threshold'] != evidence_threshold:

            arguments = topic_item['arguments']
            # 3. Extract claims and evidences
            claims, evidences = self.extract_claims_and_evidences(topic, arguments, claims_threshold, evidence_threshold)
            
            # 4. Tag claims and evidences with morals
            #topic_item['arguments'] = self.assign_morals(topic_item['arguments'])
            claims = self.assign_morals(claims)
            evidences = self.assign_morals(evidences)
            
            topic_item['claims_and_evidences'] = {
                'claims': claims,
                'evidences': evidences,
                'claims_threshold': claims_threshold,
                'evidence_threshold': evidence_threshold
            }

            print('Number of retrieved claims:', len(claims))
            print('Number of retrieved evidences:', len(evidences))

            self.cache[topic] = topic_item
        else:
            print('Load claims and evidences from the cache!!')

        # 5. Generate moral narratives
        for moral_class_name, morals in moral_dict.items():
            print('Topic:{}, Moral:{}'.format(topic, moral_class_name))

            
            moral_claims   = self.filter_argumentative_texts(topic_item['claims_and_evidences']['claims'], morals)
            moral_evidence = self.filter_argumentative_texts(topic_item['claims_and_evidences']['evidences'], morals)
            print('Number of claims after filtering:', len(moral_claims))
            print('Number of evidences after filtering:', len(moral_evidence))
            
            # for polarity is either con or pro
            narrative_key = '{}_{}_narrative'.format(moral_class_name, polarity)
            
            # 6. Create narrative
            polarity_enum = Polarity.PRO if polarity=='pro' else Polarity.CON
            
            moral_narrative = self.create_narrative(topic, topic_item['dc'][0], polarity_enum, moral_claims, moral_evidence)
            if len(moral_narrative.paragraphs) < 3:
                print('Narrative is empty...')
            topic_item[narrative_key] = str(moral_narrative)
            self.cache[topic] = topic_item
                
        

        #save the cache everytime to the desk
        with open(self.cache_path, 'w') as cf:
            json.dump(self.cache, cf)

        return topic_item
                        
        # except Exception as e:
        #     print(e)
        # finally:
        #     return topic_narratives