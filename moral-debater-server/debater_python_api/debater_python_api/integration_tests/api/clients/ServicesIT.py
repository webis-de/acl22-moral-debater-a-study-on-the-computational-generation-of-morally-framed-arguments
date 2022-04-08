# (C) Copyright IBM Corp. 2020.
import math
import sys
import unittest

from hamcrest import assert_that

from debater_python_api.api.clients.keypoints_client import KpAnalysisUtils
from debater_python_api.api.clients.narrative_generation_client import Polarity
from debater_python_api.api.sentence_level_index.client.sentence_query_base import SimpleQuery
from debater_python_api.api.sentence_level_index.client.sentence_query_request import SentenceQueryRequest
from debater_python_api.examples.resources.arguments import arguments_list
from debater_python_api.examples.resources.pro_con_scores import pro_con_scores
from debater_python_api.integration_tests.api.clients.DebaterApiWithAdjustedUrl import DebaterApiWithAdjustedUrl
from debater_python_api.integration_tests.api.clients.DebaterApiWithAdjustedUrl import Domains
from debater_python_api.utils import clusters_refiner


class ServicesIT(unittest.TestCase):

    deployment_env = Domains.production
    # deployment_env = Domains.transformers
    # deployment_env = Domains.test

    def setUp(self):
        self.debater_api = DebaterApiWithAdjustedUrl('PUT_YOUR_API_KEY_HERE', ServicesIT.deployment_env)

    def test_argument_quality_service(self):

        argument_quality_client = self.debater_api.get_argument_quality_client()

        topic = "We should further explore the development of autonomous vehicles"
        sentences = [
            'Cars should only provide assisted driving, not a complete autonomy.',
            'Cars cars cars cars who cares',
            'that he given sun roads sea']

        sentence_topic_dicts = [{'sentence': sentence, 'topic': topic} for sentence in sentences]

        scores = argument_quality_client.run(sentence_topic_dicts)
        assert_that('wrong number of scores returned', len(sentence_topic_dicts) == len(scores))
        for score in scores:
            assert_that(0 <= score <= 1.0)

    def test_claim_detection_service(self):

        claim_detection_client = self.debater_api.get_claim_detection_client()

        topic = 'We should legalize cannabis'
        sentences = ['A cross-party report found good evidence that cannabis treatments can help alleviate the symptoms of chronic pain, multiple sclerosis, nausea and vomiting, particularly in the context of chemotherapy, and anxiety.',
                     'A recent federal study indicates that cannabis is dangerous',
                     'cannabis is dangerous',
                     'The apple tree is green']

        sentence_topic_dicts = [{'sentence' : sentence, 'topic' : topic } for sentence in sentences]

        scores = claim_detection_client.run(sentence_topic_dicts)
        assert_that('wrong number of scores returned', len(sentence_topic_dicts) == len(scores))
        for score in scores:
            assert_that(0 <= score <= 1.0)

    def test_evidence_detection_service(self):

        evidence_detection_client = self.debater_api.get_evidence_detection_client()

        topic = 'We should legalize cannabis'
        sentences = ['A cross-party report found good evidence that cannabis treatments can help alleviate the symptoms of chronic pain, multiple sclerosis, nausea and vomiting, particularly in the context of chemotherapy, and anxiety.',
             'A recent federal study indicates that cannabis is dangerous',
             'cannabis is dangerous',
             'The air in Los Angeles is clear']

        sentence_topic_dicts = [{'sentence' : sentence, 'topic' : topic } for sentence in sentences]

        scores = evidence_detection_client.run(sentence_topic_dicts)
        assert_that('wrong number of scores returned', len(sentence_topic_dicts) == len(scores))
        for score in scores:
            assert_that(0 <= score <= 1.0)

    def test_claim_boundaries_service(self):

        claim_boundaries_client = self.debater_api.get_claim_boundaries_client()

        sentences = ['A cross-party report found good evidence that cannabis treatments can help alleviate the symptoms of chronic pain, multiple sclerosis, nausea and vomiting, particularly in the context of chemotherapy, and anxiety.',
                     'A recent federal study indicates that cannabis is dangerous']

        boundaries_dicts = claim_boundaries_client.run(sentences)

        for i, boundary_dict in enumerate(boundaries_dicts):
            assert_that(boundary_dict['claim'] in sentences[i])

    def test_clustering_service(self):

        clustering_client = self.debater_api.get_clustering_client()

        sentences = ['The cat (Felis catus) is a small carnivorous mammal',
                     'The origin of the domestic dog includes the dogs evolutionary divergence from the wolf',
                     'As of 2017, the domestic cat was the second-most popular pet in the U.S.',
                     'its domestication, and its development into dog types and dog breeds.',
                     'Cats are similar in anatomy to the other felid species',
                     'Dogs are highly variable in height and weight.']

        clusters_list = clustering_client.run(sentences=sentences, num_of_clusters=2)
        assert_that(len(clusters_list) == 2)
        for cluster in clusters_list:
            assert_that(len(cluster) > 0)

        topP = 0.3333
        arguments_and_distances = clustering_client.run_with_distances(sentences, 2)
        assert_that(2 == len(arguments_and_distances))

        splitted_clusters = clusters_refiner.separate_close_from_distant_arguments(arguments_and_distances, topP)
        assert_that(2 == len(splitted_clusters))

        for i in range(0, 2):
            assert_that(math.ceil(len(arguments_and_distances[i]) * topP) == len(splitted_clusters[i][0]))


    def test_index_searcher_service(self):

        index_searcher_client = self.debater_api.get_index_searcher_client()

        query = SimpleQuery(is_ordered=False, window_size=10)
        query.add_concept_element(['Wind_power', 'Wind_farm'])
        query.add_normalized_element(['harnessing', 'batteries'])
        query.add_type_element(['Sentiment'])
        query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=8, sentenceLength=(7, 60))

        sentences = index_searcher_client.run(query_request)
        assert_that(len(sentences) == 8)

    def test_pro_con_service(self):

        pro_con_client = self.debater_api.get_pro_con_client()

        topic = 'Social media is harmful'
        sentences = [
            'Social media disproportionally promotes fake news',
            'Social media is wonderful for human relationship',
            'The air in Los Angeles is clear']

        sentence_topic_dicts = [{'sentence' : sentence, 'topic' : topic } for sentence in sentences]

        scores = pro_con_client.run(sentence_topic_dicts)
        assert_that('wrong number of scores returned', len(sentence_topic_dicts) == len(scores))
        for score in scores:
            assert_that(-1.0 <= score <= 1.0)

    def test_narrative_generation_client(self):

        narrative_generation_client = self.debater_api.get_narrative_generation_client()

        topic = "We should legalize cannabis"
        dominant_concept = "Cannabis"

        speech = narrative_generation_client.run(topic=topic, dc=dominant_concept, sentences=arguments_list,
                                                 pro_con_scores=pro_con_scores, polarity=Polarity.PRO)

        assert_that(len(speech.arguments) > 10)
        assert_that(len(speech.paragraphs) >= 4)
        assert_that(len(speech.clusters) >= 4)

    def test_term_relater_service(self):

        term_relater_client = self.debater_api.get_term_relater_client()

        term_pairs = [['Soldier', 'Army'],
                      ['Pupil', 'Teacher'],
                      ['Ball', 'Tree']]

        scores = term_relater_client.run(term_pairs)
        for score in scores:
            assert_that(0 <= score <= 1.0)


    def test_term_wikifier_service(self):

        term_wikifier_client = self.debater_api.get_term_wikifier_client()

        sentences = [
            'Cars should only provide assisted driving, not complete autonomy',
            'Self driving car technology will be in conflict with vehicles driven by human users']

        annotation_arrays = term_wikifier_client.run(sentences)

        titles = []

        for i, annotation_array in enumerate(annotation_arrays):
            for annotation in annotation_array:
                if annotation['concept']['title'] is not None:
                    titles.append(annotation['concept']['title'])

        assert_that(len(titles) > 0)

    def test_keypoints_service (self):
        comments_texts = [
            "Using cannabis can lead to more dangerous drug use",
            "Prolonged use of cannabis increases the risk of developing psychosis.",
            "Cannabis is a gateway drug to more dangerous drugs",
            "The use of cannabis can be addictive for some people",
            "Legalizing illicit drugs will kill the black market",
            "When cannabis is consumed over a long period of time it has impact on memory and decision making of people.",
            "Early studies suggested cognitive declines associated with marijuana ; these declines persisted long after the period of acute cannabis intoxication."
        ]
        KpAnalysisUtils.init_logger()
        keypoints_client = self.debater_api.get_keypoints_client()

        keypoint_matchings = keypoints_client.run(comments_texts)
        KpAnalysisUtils.print_result(keypoint_matchings)
        assert_that(len(keypoint_matchings['keypoint_matchings']) > 1)
        for keypoint_matching in keypoint_matchings['keypoint_matchings']:
            if keypoint_matching['keypoint'] != 'none':
                for matching in keypoint_matching['matching']:
                    assert_that(0.98 <= matching['score'] <= 1.0)


    def test_theme_extraction_service(self):

        theme_extraction_client = self.debater_api.get_theme_extraction_client()

        dominant_concept = 'Animal'
        topic = 'We should love animals'
        clusters = [
            [
                'The cat (Felis catus) is a small carnivorous mammal',
                'As of 2017, the domestic cat was the second-most popular pet in the U.S.',
                'Cats are similar in anatomy to the other felid species'
            ],
            [
                'The origin of the domestic dog includes the dogs evolutionary divergence from the wolf',
                'its domestication, and its development into dog types and dog breeds.',
                'Dogs are highly variable in height and weight'
            ]
        ]

        theme_extraction_results = theme_extraction_client.run(topic, dominant_concept, clusters)
        assert_that(len(theme_extraction_results[0]) == 1)  # single theme
        assert_that(len(theme_extraction_results[1]) == 0)  # no themes


if __name__ == '__main__':
    if len(sys.argv) > 1:
        deployment_env_str = sys.argv[1]
        if deployment_env_str == 'staging':
            ServicesIT.deployment_env = Domains.staging
        elif deployment_env_str == 'production':
            ServicesIT.deployment_env = Domains.production
        elif deployment_env_str == 'test':
            ServicesIT.deployment_env = Domains.test
        else:
            print('error specifying running environment parameter, options are: test/staging/production')
            exit(1)

    unittest.main(argv=['first-arg-is-ignored'], exit=True)
