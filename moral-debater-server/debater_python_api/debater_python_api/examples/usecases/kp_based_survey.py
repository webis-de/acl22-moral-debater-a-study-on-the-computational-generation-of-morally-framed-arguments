# (C) Copyright IBM Corp. 2020.

import pandas as pd
import os
from debater_python_api.api.debater_api import DebaterApi
from spacy.lang.en import English
from prettytable import PrettyTable


api_key = os.environ['API_KEY']
debater_api = DebaterApi(api_key)

####start##part1
data_file = os.path.join("..", "resources", "dataset_austin.csv")
input_frame = pd.read_csv(data_file, encoding='utf8')
nlp = English()
nlp.add_pipe(nlp.create_pipe('sentencizer'))
input_frame['sentences'] = input_frame.apply(lambda x: [sent.string.strip() for sent in nlp(x['Comment']).sents],axis=1)
sentence_based_frame = pd.DataFrame(input_frame['sentences'].tolist(), index=input_frame['Comment']).stack()
sentence_based_frame = sentence_based_frame.reset_index([0, 'Comment']).rename(columns={0: 'sentences'})
input_frame = pd.merge(sentence_based_frame, input_frame[['Comment', 'Council District', 'Year']], on='Comment', how='left')
####end##part1

####start##part2
keypoints_client = debater_api.get_keypoints_client()
arg_quality_client = debater_api.get_argument_quality_client()

years = input_frame['Year'].unique().tolist()
sentences_per_year = {}
ids_per_year = {}
domain = 'kp_based_survey_example'
for year in years:
    year_frame = input_frame[input_frame['Year'] == year]
    sentences = year_frame['sentences'].tolist()
    # use argument quality service to select top 1000 sentences
    arg_quality_scores = arg_quality_client.run([{'sentence': sentence, 'topic': 'Austin'} for sentence in sentences])
    sentences = [sentence for _, sentence in sorted(zip(arg_quality_scores, sentences), reverse=True)]
    sentences_per_year[year] = sentences[:1000]
####end##part2

####start##part3
year = 2016
ids_per_year[year] = ['{}_{}'.format(year, i) for i in range(len(sentences_per_year[year]))]
keypoints_client.upload_comments(domain=domain, comments_ids=ids_per_year[year], comments_texts=sentences_per_year[year])
####end##part3

####start##part4

# run kp analysis for 2016
keypoints_client.wait_till_all_comments_are_processed(domain)
future = keypoints_client.start_kp_analysis_job(domain=domain, comments_ids=ids_per_year[2016])
keypoint_matchings = future.get_result(high_verbosity=True, polling_timout_secs=5)  # waits till result is available
####end##part4

####start##part5
# print results in a table
kp_2016_table = PrettyTable()
kp_2016_table.field_names = ['#', 'key point', 'size', 'example']
j = 0
for kp in keypoint_matchings['keypoint_matchings']:
    if kp['keypoint'] == 'none':    # skip cluster of all unmatched sentences
        continue
    j += 1
    kp_2016_table.add_row([j, kp['keypoint'], len(kp['matching']), ''])
    num_of_examples = 0
    for i, matching in enumerate(kp['matching']):  # print 3 matched (short enough for readability) sentences
        if i == 0:  # The first example it the kp itself.
            continue
        sentence = matching['sentence_text']
        if len(sentence) < 65:
            kp_2016_table.add_row(['', '', '', matching['sentence_text']])
            num_of_examples += 1
        if num_of_examples >= 2:  # show two examples at table
            break
print('2016 key points:')
print(kp_2016_table)
####end##part5

####start##part6
# run kp analysis for 2017, use the same key points from 2016
# In order to reuse the 2016 key points, we pass 2016 job id as key_points_by_job_id parameter in start_kp_analysis_job.
year = 2017
ids_per_year[year] = ['{}_{}'.format(year, i) for i in range(len(sentences_per_year[year]))]
keypoints_client.upload_comments(domain=domain,
                                 comments_ids=ids_per_year[year],
                                 comments_texts=sentences_per_year[year])
future = keypoints_client.start_kp_analysis_job(domain=domain, comments_ids=ids_per_year[year],
                                                key_points_by_job_id=future.get_job_id())
keypoint_matchings = future.get_result(high_verbosity=True, polling_timout_secs=5)  # waits until results are available

kp_2017_table = PrettyTable()
kp_2017_table.field_names = ['#', 'key point', 'size', 'example']
j = 0
for kp in keypoint_matchings['keypoint_matchings']:
    if kp['keypoint'] == 'none':    # skip cluster of all unmatched sentences
        continue
    j += 1
    kp_2017_table.add_row([j, kp['keypoint'], len(kp['matching']), ''])
    num_of_examples = 0
    for i, matching in enumerate(kp['matching']):  # print 3 matched (short enough for readability) sentences
        if i == 0:  # The first example it the kp itself.
            continue
        sentence = matching['sentence_text']
        if len(sentence) < 65:
            kp_2017_table.add_row(['', '', '', matching['sentence_text']])
            num_of_examples += 1
        if num_of_examples >= 2:  # show two examples at table
            break
print('2017 key points:')
print(kp_2017_table)
####end##part6

####start##part7
keypoints_client.delete_domain_cannot_be_undone(domain)
####end##part7

