# (C) Copyright IBM Corp. 2020.
import json
import zipfile
from datetime import datetime
import time
import logging
import pickle
from enum import Enum

import requests

from debater_python_api.api.clients.abstract_client import AbstractClient
from debater_python_api.api.clients.response_data.speech_response import ArgumentResponse
from debater_python_api.api.clients.response_data.speech_response import ClusterElementResponse
from debater_python_api.api.clients.response_data.speech_response import ClusterResponse
from debater_python_api.api.clients.response_data.speech_response import SpeechElement
from debater_python_api.api.clients.response_data.speech_response import SpeechResult
from debater_python_api.utils import general_utils


class Polarity(Enum):
    PRO = 1
    CON = -1

end_point_speech_generation = '/api/v1/speech/generate/'
end_point_get_customization = '/api/v1/speech/customization/'
end_point_get_assessment    = '/api/v1/speech/assess/'
end_point_retrieve_zipped_assessment = '/api/v1/speech/assess/getzippedresult/'
end_point_get_status_of_speech_construction    = '/api/v1/speech/status/'
end_point_post_speech_assessment_with_KP_labeled_data = '/api/v1/speech/assess/kpLabeledData/'
end_point_post_filters_assessment = '/api/v1/speech/assess/filters/'

spleeping_time = 10 # seconds

class NarrativeGenerationClient(AbstractClient):
    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)

        self.host = 'https://speech-construction.debater.res.ibm.com'

    def wait_for_completion_of(self, json):
        headers = general_utils.get_default_request_header(self.apikey)
        now = datetime.now()
        starting_to_wait = now.strftime("%d/%m/%Y %H:%M:%S")
        responseId = json['responseId']

        while True:
            attempts = 0
            while True:
                try:
                    json = requests.get(url=self.host+end_point_get_status_of_speech_construction+responseId, headers=headers, timeout=60).json()
                    break
                except requests.exceptions.ReadTimeout as e:
                    print (e)
                    print ('Got timeout exception, trying again.')
                except Exception as t:  ## all other errors
                    attempts += 1
                    print (t)
                    print ('failed attempt {} to access SC re status of {}'.format(attempts, responseId))
                    if attempts >= 10:
                        raise RuntimeError ('Failed to connect to {} 10 times leaving.'.format(self.host+end_point_get_status_of_speech_construction))

            if json['status'] == 'DONE' or json['status'] == 'ERROR':
                return json

            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            logging.info((dt_string+', SpeechResultResponse={}, motionGenerationid={}, status={}, started to wait at '
                         +starting_to_wait).format(responseId, json['motionGenerationId'], json['status']))
            print((dt_string+', SpeechResultResponse={}, motionGenerationid={}, status={}, started to wait at '
                  +starting_to_wait).format(responseId, json['motionGenerationId'], json['status']))
            time.sleep(spleeping_time)

    def run(self, topic, dc, sentences, pro_con_scores, polarity, customizations=[], sbcFlow='USE_THEMES', motionid='0', approvedAsKeypoints = None, additional_headers={}):
        time_stamp_start = datetime.now().timestamp()
        if len(sentences) != len(pro_con_scores):
            raise RuntimeError('The arguments size ({}) should be equal to pro con scores size ({})'.
                               format(len(sentences), len(pro_con_scores)))
        index_translation = sorted(range(len(sentences)), key=lambda k: sentences[k]) # the order in which sentences show alphabetically sorted
        arguments_records = [{'userId': '',
                              'argumentText': sentences[i],
                              'argumentId': i,
                              'userPolarity': 'PRO',
                              'approvedAsKeypoint' : True if approvedAsKeypoints is None else approvedAsKeypoints[i],
                              'systemPolarity': pro_con_scores[i]} for i in index_translation]

        payload = {'motionGenerationId': motionid,
                   'motionText': topic,
                   'creationTime': '',
                   'arguments': arguments_records,
                   'polarity': polarity.name,
                   'dominantConcept': dc,
                   'eventId': "eventId-e2e",
                   'publish': "false",
                   'customizations': customizations,
                   'sbcFlow' : sbcFlow  # one of: USE_THEMES, USE_KEYPOINTS_CLUSTER_LEVEL, USE_KEYPOINTS_MOTION_LEVEL
                   }

        json = self.do_run(payload, endpoint=end_point_speech_generation, updates_to_headers=additional_headers, timeout=60)

        json = self.wait_for_completion_of(json)

        if json['status'] == 'ERROR':
            # error_message = json['errorMessage']
            # speech_generation_uniq_id=json['speechGenerationUniqId']
            return SpeechResult(arguments=None, clusters=None, paragraphs=None,
                                speech_generation_uniq_id=json['speechGenerationUniqId'],
                                status=json['status'], rows_for_kps_csv = None, rows_for_filtered_elements = None,
                                error_message=json['errorMessage'])
            # raise RuntimeError(f'Generation {speech_generation_uniq_id} of speech for topic {topic} and polarity {polarity.name} failed. Error message is: {error_message}')

        arguments_list = [ArgumentResponse(id=arg['argumentId'], text=arg['argumentText'],
                                                        in_speech=arg['inSpeech'],reason=arg['reason'],
                                                        user_id=arg['userId']) for arg in json['arguments']]
        arguments = {arg.id: arg for arg in arguments_list}
        clusters = [ClusterResponse(theme=cluster['theme'], in_speech=cluster['inSpeech'],
                                    elements=[ClusterElementResponse(representative=arguments[element['sbcArgument']['argumentId']],
                                                                     similar_arguments=[arguments[arg['argumentId']] for arg in
                                                                                        element['similarSbcArguments']
                                                                                        ]
                                                                     ) for element in cluster['representativeArguments']
                                              ])
                    for cluster in json['clusters']]
        paragraphs = []
        for paragraph in json['speechParagraphs']:
            paragraph = [SpeechElement(text=element['elementText'], text_with_tts=element['elementTextWithTts'],
                                         contributing_arguments=[arguments[arg['sbcArgument']['argumentId']]
                                                                 for arg in element['contributingArguments']])
                         for element in paragraph['speechElements']]
            paragraphs.append(paragraph)
        time_stamp_end = datetime.now().timestamp()
        logging.info('narrative_generation_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))
        speech_generation_uniq_id = json['speechGenerationUniqId']
        status = json['status']
        rows_for_kps_csv = json['rowsOfKPsCsv']
        rows_for_filtered_elements = json['rowsOfFilteredElementsCSV']

        return SpeechResult(arguments=arguments, clusters=clusters, paragraphs=paragraphs,
                            speech_generation_uniq_id=speech_generation_uniq_id, status=status,
                            rows_for_kps_csv = rows_for_kps_csv,
                            rows_for_filtered_elements = rows_for_filtered_elements)

    def get_customization(self):
        headers = general_utils.get_default_request_header(self.apikey)
        response = requests.get(url=self.host+end_point_get_customization, headers=headers, timeout=60)
        if response.status_code != 200:
            dump = {'url': self.host+end_point_get_customization, 'headers': headers}
            x = datetime.now()
            with open(self.__class__.__name__ + x.strftime("%Y-%m-%d-%H-%M-%S") + '.pkl', 'wb') as f:
                pickle.dump(dump, f, pickle.HIGHEST_PROTOCOL)
            raise ConnectionError(
                "Can't access server. Status code: {} - {}".format(response.status_code, response.reason))
        return response.text


    def get_assessments_for_speechGenerationUniqueIds(self, idlist, path_to_dir_where_zip_to_be_stored):
        headers = general_utils.get_default_request_header(self.apikey)
        num_of_attempts = 0
        while True:
            try:
                response = requests.get(url=self.host+end_point_get_assessment+idlist, headers=headers, timeout=60).json()
                if response['status'] == 'ERROR':
                    raise RuntimeError ('An error occurred while generating speech assessment. Error reads: '+response['errorMessage'])
                if response['status'] == 'DONE':
                    break
                print('assessment is not ready yet, trying again soon')
                time.sleep(10)

            except Exception as e:
                num_of_attempts = 1+num_of_attempts
                print('Fail try {} to get assessment.'.format(num_of_attempts))
                print('Whole Exception printout:')
                print(e)
                print('Endof whole Exception printout.')
                if num_of_attempts >= 3:
                    raise Exception('Failed to get assessment in three attempts, leaving.')
                print(f'Trying again to get assessment for speech {idlist}')

        timestamp = '_' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        assessment_zip = path_to_dir_where_zip_to_be_stored + '/assessment'+timestamp+'.zip'
        headers = general_utils.get_default_request_header(self.apikey)
        response = requests.post(url=self.host+end_point_retrieve_zipped_assessment, json=response, headers=headers, timeout=60)
        print('Downloading zip to '+assessment_zip)
        with open(assessment_zip, 'wb') as zip_file:
            zip_file.write(response.content)

        print('Extracting all files to a sibling directory')
        with zipfile.ZipFile(assessment_zip, 'r') as file:
            # extracting the files using 'extracall' method into a newly created directory, a sibling of the zip file, same name.
            file.extractall(assessment_zip[0:-4])
        print('Done!')

    def get_filters_assessmet (self, labeled_data_records, computed_pro_cons_scores, customizations, path_to_dir_where_zip_to_be_stored):
        headers = general_utils.get_default_request_header(self.apikey)
        request = {'pro_con_scores' : computed_pro_cons_scores,
                   'labeled_data_records' : labeled_data_records,
                   'customizations' : customizations}

        response = requests.post(url=self.host+end_point_post_filters_assessment, json=request, headers=headers, timeout=3600)
        timestamp = '_' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        assessment_zip = path_to_dir_where_zip_to_be_stored + '/filter_assessment'+timestamp+'.zip'
        print('saving zipped report into '+assessment_zip)
        with open(assessment_zip, 'wb') as zip_file:
            zip_file.write(response.content)

        with zipfile.ZipFile(assessment_zip, 'r') as file:
            # printing all the information of archive file contents using 'printdir' method
            # print(file.printdir())

            # extracting the files using 'extracall' method into a newly created directory, a sibling of the zip file, same name.
            print('Extracting all files...')
            file.extractall(assessment_zip[0:-4])
        print('Done!')


    def get_assessment_for_speech_with_KP_Labeled_Data (self, list_of_labeled_data_records, evaluation_threshold,
                                                        speech_generation_unique_id, path_to_dir_where_zip_to_be_stored):
        payload = {'speechGenerationUniqeId': speech_generation_unique_id,
                   'labeledDataRecords' :  list_of_labeled_data_records,
                   'evaluationThreshold' : evaluation_threshold
                   }

        # do not use the usual do_run, because we do not receive a usual json here, but rather - a binary string.
        headers = general_utils.get_default_request_header(self.apikey)
        response = requests.post(url=self.host+end_point_post_speech_assessment_with_KP_labeled_data, json=payload, headers=headers, timeout=3600)
        if response.status_code > 200:
            raise ConnectionError("Error generating report with data")
        print('Downloading zip')
        timestamp = '_' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        assessment_zip = path_to_dir_where_zip_to_be_stored + '/assessment_withLabeledData'+timestamp+'.zip'
        with open(assessment_zip, 'wb') as zip_file:
            zip_file.write(response.content)

        with zipfile.ZipFile(assessment_zip, 'r') as file:
            # printing all the information of archive file contents using 'printdir' method
            # print(file.printdir())

            # extracting the files using 'extracall' method into a newly created directory, a sibling of the zip file, same name.
            print('Extracting all files...')
            file.extractall(assessment_zip[0:-4])
            print('Done!')
