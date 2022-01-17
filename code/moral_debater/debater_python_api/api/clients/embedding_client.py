# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.clients.abstract_client import AbstractClient

endpoint = '/api/public/embedding'

class EmbeddingClient(AbstractClient):
    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://clustering.debater.res.ibm.com'
        self.text_preprocessing = [] # stemming, or lemmatization, or stemming_over_lemmatization, or wikifier

    def set_text_preprocessing(self, text_preprocessing):
        if text_preprocessing in {'stemming', 'lemmatization', 'wikifier'}:
            self.text_preprocessing = [str(text_preprocessing)]
        elif text_preprocessing == 'stemming_over_lemmatization':
            self.textPreprocessing = ['lemmatization' , 'stemming']
        else:
            self.text_preprocessing = []

    def set_embedding_method(self, embedding_method):
        self.embedding_method = embedding_method

    def run(self, embedding_method, sentences, mask=''):
        """
        :param embedding_method: one of 'tfidf', 'tf', 'glove'
                                'bert_ft_sent', 'bert_ft_title', 'bert_ft_concat' will be available shortly
        :param sentences: a list of strings to be embedded
        :param mask: a string to ignore
        :return: a list of embeddings

        Default text preprocessing:
        tf/idf: stemming, lemmatization, ignore punctuations, ignore stopwords, apply masking when available
        glove: ignore punctuations, ignore stopwords, apply masking when available
        bert: apply masking when available

        Similarity calculation:
        The BERT models were fine-tuned to capture thematic similarity using the squared Euclidean distance.
        When calculating similarity between BERT embeddings (e1, e2), use L22 distance as follows:
            import numpy as np
            dist = np.linalg.norm(e1 - e2, axis=1)
        When calculating similarity between tf/idf/glove embeddings, use cosine similarity.

        Masking:
        The 'mask' parameter specifies tokens to ignore. The 'tfidf', 'tf', 'glove' methods remove these tokens from
        each string before creating the embedding. BERT concatenates the mask to each string before applying the model.
        """
        if len(sentences) == 0:
            raise RuntimeError('empty set of input sentences')
        payload = {'text_preprocessing': self.text_preprocessing,
                   'embedding_method': str(embedding_method),
                   'embedding_configuration': {'max_df': 1.0, 'min_df': 1, 'motion_text': mask}}
        if embedding_method == 'tfidf':
            payload['arguments'] = sentences
            embeddings_list = self.do_run(payload, endpoint=endpoint)['arguments_embedding']
        else:
            embeddings_list = self.run_in_batch(list_name='arguments', list=sentences, other_payload=payload,
                                                list_from_json_getter=lambda x:x['arguments_embedding'], endpoint=endpoint)
        return embeddings_list
