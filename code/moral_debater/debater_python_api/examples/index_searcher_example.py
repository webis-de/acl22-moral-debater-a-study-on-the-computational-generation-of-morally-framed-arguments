# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi
from debater_python_api.api.sentence_level_index.client.sentence_query_base import SimpleQuery
from debater_python_api.api.sentence_level_index.client.sentence_query_request import SentenceQueryRequest
from debater_python_api.api.sentence_level_index.client.article_retrieval_request import ArticleRetrievalRequest

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')

index_searcher_client = debater_api.get_index_searcher_client()

query = SimpleQuery(is_ordered=False, window_size=10)
query.add_concept_element(['Wind power', 'Wind farm'])
query_request = SentenceQueryRequest(query=query.get_sentence_query(), size=200, sentenceLength=(7, 60))

sentences = index_searcher_client.run(query_request, return_full_record=True)

for sentence in sentences:
    print(sentence)


print('\n\nprev sentences')
query_request = ArticleRetrievalRequest(articleIds=[sentence.parentArticleId for sentence in sentences])
articles = index_searcher_client.get_articles(query_request)
for article, sentence in zip(articles, sentences):
    prev_sentence_position = sentence.sentencePosition - 1
    if 0 <= prev_sentence_position < len(article['sentencesFields']):
        print(article['articleFields']['fullText'][int(article['sentencesFields'][prev_sentence_position]['spanStart']):
                                                   int(article['sentencesFields'][prev_sentence_position]['spanEnd'])])