# (C) Copyright IBM Corp. 2020.

import unittest

from debater_python_api.integration_tests.api.clients.DebaterApiWithAdjustedUrl import DebaterApiWithAdjustedUrl
from debater_python_api.integration_tests.api.clients.DebaterApiWithAdjustedUrl import Domains
from debater_python_api.api.sentence_level_index.client.sentence_query_request import SentenceQueryRequest
from debater_python_api.api.sentence_level_index.client.sentence_query_base import RandomQuery
from timeit import default_timer as timer


class ServicesIT(unittest.TestCase):

    def setUp(self):
        self.debater_api = DebaterApiWithAdjustedUrl('PUT_YOUR_API_KEY_HERE', Domains.production)
        self.num_of_sentences = 1000
        self.sentence_length = (10,30)

    def get_sentences(self):
        for i in range(5):
            try:
                searcher = self.debater_api.get_index_searcher_client()

                query = RandomQuery()
                query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=self.num_of_sentences,
                                                     sentenceLength=self.sentence_length)
                return searcher.run(query_request)
            except Exception as e:
                print("Exception in searcher", e)

    def run_service(self, service_runner):
        start_time = timer()
        service_runner()
        run_time = timer() - start_time
        return run_time

    def test_argument_quality_service(self):
        sentences = self.get_sentences()
        motion = 'we should subsidize public transportation'
        time = self.run_service(service_runner=lambda: self.debater_api.get_argument_quality_client().
             run([{'sentence': candidate, 'topic': motion} for candidate in sentences]))
        print('Run argument quality. time={}'.format(time))

    def test_procon_service(self):
        sentences = self.get_sentences()
        motion = 'we should subsidize public transportation'
        time = self.run_service(service_runner=lambda: self.debater_api.get_pro_con_client().
                                run([{'sentence': candidate, 'topic': motion} for candidate in sentences]))
        print('Run procon. time={}'.format(time))

    def test_evidence_service(self):
        sentences = self.get_sentences()
        motion = 'we should subsidize public transportation'
        time = self.run_service(service_runner=lambda: self.debater_api.get_evidence_detection_client().
                               run([{'sentence': candidate, 'topic': motion} for candidate in sentences]))
        print('Run evidence. time={}'.format(time))

    def test_claim_service(self):
        sentences = self.get_sentences()
        motion = 'we should subsidize public transportation'
        time = self.run_service(service_runner=lambda: self.debater_api.get_claim_detection_client().
                               run([{'sentence': candidate, 'topic': motion} for candidate in sentences]))
        print('Run claim. time={}'.format(time))

    def test_claim_boundaries_service(self):
        sentences = self.get_sentences()
        time = self.run_service(service_runner=lambda: self.debater_api.get_claim_boundaries_client().
                                run(sentences=sentences))
        print('Run claim boundaries. time={}'.format(time))

    def test_term_wikifier_service(self):
        sentences = self.get_sentences()
        time = self.run_service(service_runner=lambda: self.debater_api.get_term_wikifier_client().run(sentences))
        print('Run term wikifier. time={}'.format(time))

    def test_clustering_service(self):
        sentences = self.get_sentences()
        time = self.run_service(service_runner=lambda: self.debater_api.get_clustering_client().run(sentences,10))
        print('Run clustering(cluster {} sentences to {} clusters) . time={}'.format(len(sentences), 10, time))

    def test_term_relater(self):
        num_of_pairs_of_concepts = 100
        sentences = self.get_sentences()
        term_wikifier_client = self.debater_api.get_term_wikifier_client()
        mentions = term_wikifier_client.run(sentences)
        concepts = [val['concept']['title'] for sublist in mentions for val in sublist]
        concepts = list(set(concepts))[0:num_of_pairs_of_concepts*2]
        pairs = [[concepts[i], concepts[-i - 1]] for i in range(num_of_pairs_of_concepts)]
        time = self.run_service(service_runner=lambda: self.debater_api.get_term_relater_client().run(pairs))
        print('Run term relater on {} pairs. time={}'.format(num_of_pairs_of_concepts, time))

if __name__ == '__main__':
    unittest.main()
