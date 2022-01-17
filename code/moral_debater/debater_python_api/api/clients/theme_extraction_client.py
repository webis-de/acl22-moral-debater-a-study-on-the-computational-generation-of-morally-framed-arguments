# (C) Copyright IBM Corp. 2020.
import datetime
import logging
from debater_python_api.api.clients.abstract_client import AbstractClient

endpoint = '/api/v1/theme/extract/'

class ThemeExtractionClient(AbstractClient):
    def __init__(self, apikey):
        AbstractClient.__init__(self, apikey)
        self.host = 'https://theme-extraction.debater.res.ibm.com'

    def run(self, topic, dominant_concept, clusters, themes_to_exclude=[]):
        time_stamp_start = datetime.datetime.now().timestamp()
        if (len(topic) == 0 or len(dominant_concept) == 0):
            raise RuntimeError('empty input argument: topic "{}" or dominant_concept "{}".'.format(topic, dominant_concept))

        payload = {
            'elements': clusters,
            'dominantConcept': dominant_concept,
            'topic': topic,
            'themesToExclude': themes_to_exclude
        }
        json = self.do_run(payload, endpoint=endpoint)
        theme_extraction_result = []
        results = json['elements']
        for i in range(len(results)):
            cluster_themes = results[i]['themes']
            themes = [{'theme' : cluster_themes[j]['theme'], 'pValue' : cluster_themes[j]['p_value']}
                      for j in range(len(cluster_themes)) if cluster_themes[j]['is_valid'] is True]
            theme_extraction_result.append(themes)

        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('theme_extraction_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))

        return theme_extraction_result


    def run_and_get_all_themes_supporters(self, topic, dominant_concept, clusters, themes_to_exclude=[], p_value_th = None):
        time_stamp_start = datetime.datetime.now().timestamp()
        if (len(topic) == 0 or len(dominant_concept) == 0):
            raise RuntimeError('empty input argument: topic "{}" or dominant_concept "{}".'.format(topic, dominant_concept))

        payload = {
            'elements': clusters,
            'dominantConcept': dominant_concept,
            'topic': topic,
            'themesToExclude': themes_to_exclude
        }
        json = self.do_run(payload)
        theme_extraction_result = []
        results = json['elements']
        for i in range(len(results)):
            cluster_themes = results[i]['themes']
            filtered_cluster_themes = [theme for theme in cluster_themes if
                                       (p_value_th is not None and theme['p_value'] <= p_value_th)
                                       or
                                       (theme['is_valid'] is True)]

            themes = [{'theme' : cluster_themes[j]['theme'],
                       'p_value' : cluster_themes[j]['p_value'],
                       'num_apearances': cluster_themes[j]['term_frequency_in_cluster'],
                       'num_supporters' : cluster_themes[j]['num_of_supporters'],
                       'indices_of_supporters' : cluster_themes[j]['indices_of_supporters'][0:cluster_themes[j]['num_of_supporters']]
                       }
                      for j in range(len(filtered_cluster_themes))]
            theme_extraction_result.append(themes)

        time_stamp_end = datetime.datetime.now().timestamp()
        logging.info('theme_extraction_client.run = {}ms.'.format(1000*(time_stamp_end - time_stamp_start)))
        return theme_extraction_result

