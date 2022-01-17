# (C) Copyright IBM Corp. 2020.
import datetime
import logging

from debater_python_api.api.clients.abstract_client import AbstractClient

endpoint = '/api/public/clustering'

class ClusteringClient(AbstractClient):
    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://clustering.debater.res.ibm.com'
        self.text_preprocessing = 'stemming' # stemming, lemmatization, or wikifier, or stemming_over_lemmatization
        self.embedding_method = 'tf' #tf, ifidf, concepts, glove, or bert_ft_concat
        self.clustering_method = 'sib'  # kmeans, skmeans_euclidean, or sib
        self.clustering_configuration = {}

    def set_text_preprocessing(self, text_preprocessing):
        self.text_preprocessing = text_preprocessing

    def set_embedding_method(self, embedding_method):
        self.embedding_method = embedding_method

    def set_clustering_method(self, clustering_method):
        self.clustering_method = clustering_method

    def set_seed(self, seed):
        self.clustering_configuration["random_state"] = seed

    def run(self, sentences, num_of_clusters):
        time_stamp_start = datetime.datetime.now().timestamp()
        clusters_json = self.sentences_to_clusters_json(sentences, num_of_clusters)

        clusters_list = []
        for cluster_info in clusters_json:
            arguments_info_container = cluster_info['argumentInfoContainers']
            argument_list = [sentences[argument['argument_id']] for argument in arguments_info_container]
            clusters_list.append(argument_list)

        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('clustering_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))
        return clusters_list

    def sentences_to_clusters_json(self, sentences, num_of_clusters):
        if not self.is_configuration_correct():
            raise RuntimeError('Clustering error: configuration not set properly. When choosing Clustering method sib, embedding method must be tf.')

        if len(sentences) == 0:
            raise RuntimeError('empty set of input sentences')
        if (len(sentences) < num_of_clusters):
            raise RuntimeError('The number {} of input sentences is smaller than the number {} of requested clusters.'
                               .format(len(sentences), num_of_clusters))

        if self.text_preprocessing == 'stemming_over_lemmatization' :
            textPreprocessing = ['lemmatization' , 'stemming']
        else: textPreprocessing = [str(self.text_preprocessing)]
        payload = {'text_preprocessing': textPreprocessing,
                   'embedding_method': str(self.embedding_method),
                   'clustering_method': str(self.clustering_method),
                   'num_of_clusters': num_of_clusters,
                   'arguments': sorted(sentences),
                   'clustering_configuration': self.clustering_configuration}
        # just here, as we go to the service itself and get results
        # sort sentences before going to service, and on the returned result, translate the indexes into the sorted list of sentences
        # to indexes into the original, non-sorted list of sentences
        # so that these indeces will be userful to the user who only knows the original, non-sorted list of sentences.
        response_json = self.do_run(payload, endpoint=endpoint)
        sorted_sentences_with_distance = response_json['arguments_id_and_distance_per_cluster']
        index_translation = sorted(range(len(sentences)), key=lambda k: sentences[k])
        for per_cluster_sorted_sentences_with_distance in sorted_sentences_with_distance:
            for arg_index_and_distance in per_cluster_sorted_sentences_with_distance['argumentInfoContainers']:
                arg_index_and_distance['argument_id'] = index_translation[arg_index_and_distance['argument_id']]

        return sorted_sentences_with_distance  #where the sentence-indexes refer to the sentences reshuffeled back to original order.


    def run_with_distances (self, sentences, num_of_clusters):
        time_stamp_start = datetime.datetime.now().timestamp()
        clusters_json = self.sentences_to_clusters_json(sentences, num_of_clusters)
        clusters_with_distances_list = []
        for cluster_info in clusters_json:
            arguments_info_container = cluster_info['argumentInfoContainers']
            argument_and_distances_list = [[sentences[argument['argument_id']], argument["distance"]] for argument in arguments_info_container]
            sorted_argument_and_distances_list = sorted(argument_and_distances_list, key=lambda arg_and_dist: arg_and_dist[1])
            clusters_with_distances_list.append(sorted_argument_and_distances_list)
        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('clustering_client.run_with_distances = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))
        return clusters_with_distances_list

    def run_with_full_info (self, sentences, num_of_clusters):
        time_stamp_start = datetime.datetime.now().timestamp()
        clusters_json = self.sentences_to_clusters_json(sentences, num_of_clusters)
        cluster_list = []
        for cluster_info in clusters_json:
            arguments_info_container = cluster_info['argumentInfoContainers']
            argument_and_distances_list = [
                {'text': sentences[argument['argument_id']],
                 'id': argument['argument_id'],
                 'distance': argument['distance']}
                for argument in arguments_info_container
            ]
            sorted_argument_and_distances_list = sorted(argument_and_distances_list, key=lambda arg_and_dist: arg_and_dist['distance'])
            cluster_list.append(sorted_argument_and_distances_list)
        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('clustering_client.run_with_distances = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))
        return cluster_list

    def is_configuration_correct(self):
        if self.clustering_method != 'sib':
            return True

        return self.embedding_method == 'tf'
