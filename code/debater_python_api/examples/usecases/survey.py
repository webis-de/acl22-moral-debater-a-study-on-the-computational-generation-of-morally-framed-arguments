# (C) Copyright IBM Corp. 2020.

import os
import matplotlib.pyplot as plt, numpy as np, pandas as pd, os
from collections import namedtuple
from debater_python_api.api.debater_api import DebaterApi
from prettytable import PrettyTable, ALL
from sklearn.cluster import SpectralClustering
from spacy.lang.en import English

api_key = os.environ['API_KEY']
debater_api = DebaterApi(api_key)

def get_sentences_based_frame(comments_based_frame):
    nlp = English()
    nlp.add_pipe(nlp.create_pipe('sentencizer'))
    comments_based_frame['sentences'] = comments_based_frame.apply(lambda x: [sent.string.strip() for sent in nlp(x['Comment']).sents],axis=1)
    sentence_based_frame = pd.DataFrame(comments_based_frame['sentences'].tolist(), index=comments_based_frame['Comment']).stack()
    sentence_based_frame = sentence_based_frame.reset_index([0, 'Comment']).rename(columns={0: 'sentences'})
    return pd.merge(sentence_based_frame, comments_based_frame[['Comment', 'Council District', 'Year']], on='Comment', how='left')

def populate_similarity_matrix(num_themes,relation_scores):
    theme_similarity_matrix = np.zeros([num_themes, num_themes])
    index = 0
    for i in range(num_themes):
        theme_similarity_matrix[i, i] = 1
        for j in range(i + 1, num_themes):
            relation_score = relation_scores[index]
            theme_similarity_matrix[i, j] = relation_score
            theme_similarity_matrix[j, i] = relation_score
            index += 1
    return theme_similarity_matrix

def get_theme_clusters(theme_similarity_matrix, unique_themes):
    theme_clusters = []
    num_theme_clusters = round(num_themes/3)
    theme_clustering = SpectralClustering(num_theme_clusters,random_state=0).fit_predict(theme_similarity_matrix)
    for i in range(num_theme_clusters):
        themes_cluster = [unique_themes[j] for j in range(num_themes) if theme_clustering[j]== i]
        theme_clusters.append(themes_cluster)
    avg_cluster_size = sum([len(cluster) for cluster in theme_clusters]) / len(theme_clusters)
    theme_clusters_without_outliers = [cluster for cluster in theme_clusters if len(cluster) < (2 * avg_cluster_size)]
    outliers = [cluster for cluster in theme_clusters if cluster not in theme_clusters_without_outliers]
    flattened_outliers = [[theme] for cluster in outliers for theme in cluster]
    return theme_clusters_without_outliers + flattened_outliers

def get_representative_themes(theme_clusters, clusters_and_themes_frame):
    theme_represetative = namedtuple('theme_representative', ['representative_theme', 'clustered_themes', 'themes_count'])
    theme_clusters_print_table = PrettyTable(hrules=ALL)
    theme_clusters_print_table.field_names = ['Representing Theme', 'Clustered Themes']
    representative_themes = []
    for theme_cluster in theme_clusters:
        theme_cluster_counts = {theme: clusters_and_themes_frame['main_theme'].tolist().count(theme) for theme in theme_cluster}
        cluster_themes_sorted_by_frequency = sorted(theme_cluster_counts, key=theme_cluster_counts.get, reverse=True)
        representative_theme = cluster_themes_sorted_by_frequency[0]
        representative_themes.append(theme_represetative(representative_theme,theme_cluster,sum(theme_cluster_counts.values())))
    representative_themes.sort(key=lambda x: x.themes_count,reverse=True)
    [theme_clusters_print_table.add_row([theme.representative_theme,theme.clustered_themes]) for theme in representative_themes[:5]]
    print(theme_clusters_print_table)
    return [theme.representative_theme for theme in representative_themes]

def create_graph_and_get_top_themes(frame,series,is_stacked_graph,graph_title):
    supporters_per_rep_theme = frame[representative_themes].sum(axis=0, skipna=True).to_dict()
    top_themes = sorted(supporters_per_rep_theme,reverse=True, key=supporters_per_rep_theme.get)[:10]
    table = pd.pivot_table(data=frame[[series]+top_themes], index=[series], aggfunc=sum, margins=True)
    table = table.transpose().sort_values(by='All').drop('All',axis=1)
    table.plot.barh(stacked=is_stacked_graph)
    plt.title(graph_title)
    plt.legend(title='Districts')
    plt.xlabel('num_sentences')
    plt.tight_layout()
    plt.show()
    return top_themes

####start##part1
data_file = os.path.join("..","resources","dataset_austin.csv")
input_frame = pd.read_csv(data_file, encoding='utf8')
input_frame = get_sentences_based_frame(input_frame)
####end##part1


####start##part2
clustering_client = debater_api.get_clustering_client()
clustering_client.set_seed(0)
theme_extraction_client = debater_api.get_theme_extraction_client()
districts = input_frame['Council District'].unique().tolist()
years = input_frame['Year'].unique().tolist()
clusters_and_themes_info = []
for year in years:
    year_frame = input_frame[input_frame['Year'] == year]
    for district in districts:
        year_n_district_frame = year_frame[year_frame['Council District']==district]
        sentences = year_n_district_frame['sentences'].tolist()
        clusters = clustering_client.run(sentences=sentences, num_of_clusters=12)
        extracted_themes = theme_extraction_client.run(clusters=clusters, topic="We should support the City of Austin", dominant_concept='City of Austin')
        for cluster_index in range(len(clusters)):
            returned_themes = [theme['theme'] for theme in extracted_themes[cluster_index]]
            main_theme = returned_themes[0] if len(returned_themes) > 0 else 'No Theme'
            cluster_elements = clusters[cluster_index]
            cluster_size = len(cluster_elements)
            clusters_and_themes_info.append([year,district,main_theme,cluster_size,cluster_elements])
clusters_and_themes_frame = pd.DataFrame(data=clusters_and_themes_info,
                                         columns=['year','district','main_theme','cluster_size','cluster_elements'])

####end##part2

####start##part3
unique_themes = clusters_and_themes_frame['main_theme'].unique().tolist()
num_themes = len(unique_themes)
relation_pairs = []
for i in range(num_themes):
    theme_i = unique_themes[i]
    for j in range(i+1,num_themes):
        theme_j = unique_themes[j]
        relation_pairs.append([theme_i,theme_j])
term_relater_client = debater_api.get_term_relater_client()
relation_scores = term_relater_client.run(relation_pairs)
theme_similarity_matrix = populate_similarity_matrix(num_themes,relation_scores)
theme_clusters = get_theme_clusters(theme_similarity_matrix, unique_themes)
representative_themes = get_representative_themes(theme_clusters, clusters_and_themes_frame)
####end##part3

####start##part4
term_wikifier_client = debater_api.get_term_wikifier_client()
term_annotations_for_sentences = term_wikifier_client.run(input_frame['sentences'].tolist())
wiki_titles_for_sentences = [[annotation['concept']['title'] for annotation in annotation_array] for annotation_array in term_annotations_for_sentences]
sentences_to_wiki_titles = dict(zip(input_frame['sentences'].tolist(), wiki_titles_for_sentences))
input_frame['sentence_wiki_titles'] = input_frame['sentences'].map(sentences_to_wiki_titles)
####end##part4

####start##part5
def is_supporter(wiki_titles, theme_similarity_to_wiki_titles):
    sentence_similarity_scores = [theme_similarity_to_wiki_titles[title] for title in wiki_titles]
    if len(wiki_titles)>0 and max(sentence_similarity_scores)>0.95:
            return True
    return False
unique_wiki_titles = list(set([title for wiki_titles_for_sentence in wiki_titles_for_sentences for title in wiki_titles_for_sentence]))
for theme in representative_themes:
    relation_pairs_for_theme = [[theme, wiki_title] for wiki_title in unique_wiki_titles]
    theme_relation_scores = term_relater_client.run(relation_pairs_for_theme)
    similarity_of_theme_to_wiki_titles = {unique_wiki_titles[i]: theme_relation_scores[i]
                                          for i in range(len(unique_wiki_titles))}
    input_frame[theme] = input_frame.apply(
        lambda sentence: is_supporter(sentence['sentence_wiki_titles'],
                                      similarity_of_theme_to_wiki_titles),axis=1)
####end##part5

####start##part6
input_2016_frame = input_frame[input_frame['Year']==2016]
top_2016_themes = create_graph_and_get_top_themes(frame= input_2016_frame,
                                                  series='Council District',
                                                  is_stacked_graph= True,
                                                  graph_title='2016 top themes over districts')
####end##part6

####start##part7
argument_quality_client = debater_api.get_argument_quality_client()
claim_detection_client = debater_api.get_claim_detection_client()
scored_sentence = namedtuple('scored_sentence',['sentence','argumentative_score','quality_score'])
for theme in top_2016_themes[:3]:
    sample_texts_table = PrettyTable()
    sample_texts_table.field_names = [theme.upper() + ' sample texts']
    sub_frame = input_2016_frame[input_2016_frame[theme]]
    theme_sentences = sub_frame['sentences'].tolist()
    theme_sentences = [sentence for sentence in theme_sentences if len(sentence) in range(70, 150)]
    sentence_topic_dicts = [{'sentence': sentence, 'topic': 'We should support ' + theme} for sentence in theme_sentences]
    quality_scores = argument_quality_client.run(sentence_topic_dicts)
    argumentative_scores = claim_detection_client.run(sentence_topic_dicts)
    scored_sentences = [
        scored_sentence(sentence=theme_sentences[i],
                        argumentative_score=argumentative_scores[i],
                        quality_score=quality_scores[i])
        for i in range(len(theme_sentences))]
    sample_sentences = [sentence for sentence in scored_sentences if sentence.argumentative_score > 0.5]
    sample_sentences = sorted(sample_sentences, key=lambda x:x.quality_score, reverse=True)[:3]
    [sample_texts_table.add_row([sample_sentence.sentence]) for sample_sentence in sample_sentences]
    print(sample_texts_table)
    print()
####end##part7

####start##part8
create_graph_and_get_top_themes(frame=input_frame,series='Year', is_stacked_graph= False,graph_title='Yearly trends')
####end##part8