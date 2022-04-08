# (C) Copyright IBM Corp. 2020.

import requests
import debater_python_api.examples.example_of_sc_args as sc_example

base_server_url_prefix = 'https://'
base_server_url = '.ris2-debater-event.us-east.containers.appdomain.cloud/'

"""
This function provides an example to how to send a simple request to clustering service
The clustering service receives list of sentences and clustering configuration, and returns a list of clusters,
where each cluster contains a list with it arguments id and the argument distance from the cluster centroid. 

The configuration contains the following fields:
text preprocessing - lemmatization, staming, wikification
embedding method - tfidf, tf, concepts, glove (mean vector), bert
clustering method - the options are: kmeans, skmeans_euclidean (sequential k means with L2 norm), skmeans_cosine )sequential k means with cosine similarity, sib (sequential information bottleneck)
number of clusters - the number of the clusters

"""
def show_clustering_example():
    HEADERS = {'accept-encoding': 'gzip, deflate', 'content-type': 'application/json;charset=UTF-8'}
    uri = 'https://clustering-server.debater-event.us-south.containers.appdomain.cloud:443/api/public/clustering'
    arguments = ['The cat (Felis catus) is a small carnivorous mammal',
                 'The origin of the domestic dog includes the dogs evolutionary divergence from the wolf',
                 'As of 2017, the domestic cat was the second-most popular pet in the U.S.',
                'its domestication, and its development into dog types and dog breeds.',
                 'Cats are similar in anatomy to the other felid species',
                 'Dogs are highly variable in height and weight.']
    payload = {'text_preprocessing': ['stemming'],
               'embedding_method': 'tfidf',
               'clustering_method': 'kmeans',
               'num_of_clusters': 2,
               'arguments':arguments}

    response = requests.post(url=uri, json=payload, headers=HEADERS)

    print(response.json())


"""
This function provides an example to how to send a simple request to quality service
The quality service receives list of pairs where each pair contains an argument and a topic, and returns a list of scores in the range [0, 1],

"""
def show_quality_example():
    HEADERS = {'accept-encoding': 'gzip, deflate', 'content-type': 'application/json;charset=UTF-8'}
    uri = base_server_url_prefix + 'arg-quality' + base_server_url + 'score/'
    payload = {'pairs': [['Cars should only provide assisted driving, not a complete autonomy', 'we should further explore the development of autonomous vehicles'],
                         ['Self driving car technology will be in conflict with vehicles driven by human users', 'we should further explore the development of autonomous vehicles'],
                         ['Finally, regarding Job', 'we should further explore the development of autonomous vehicles']]}

    response = requests.post(url=uri, json=payload, headers=HEADERS)

    print(response.json())


    """
    This function provides an example to how to send a simple request to pro con service
    The pro con service receives list of arguments and a topic, and for each argument, it returns a score in the range [-1,1] 
    that represents the amount of the argument is supporting the topic.

    """
def show_pro_con_example():
    HEADERS = {'accept-encoding': 'gzip, deflate', 'content-type': 'application/json;charset=UTF-8'}
    uri = base_server_url_prefix + 'pro-con' + base_server_url + 'score/'
    discussion_topic = 'Social media is harmful'
    arguments = ['Social media is information power which can be abused if not used with judgement, and Cognitive capabilities can help qualify author, relevance to personal content to help build careers, communities and innovation.',
                 'Social media disproportionally promotes fake news, or at least a somewhat false version of the actual news. Trustworthy media gets less exposure, and people are affected by the lies they encounter through social media.',
                 'Social media promotes isolation and alienation by providing people an easier means to find only those whose opinions they admire or adhere to instead of broadening ones point of view.',
                 'It is',
                 'It is not',
                 '1 2 3 4 5 6 7']
    payload = {'discussion_topic': discussion_topic,
               'arguments': arguments}
    response = requests.post(url=uri, json=payload, headers=HEADERS)
    print(response.json())

    """
    This function provides an example to how to send a simple request to the evidence classifier
    The evidence classifier service receives list, where each element is a topic concatenated to "^^^", concatenated to 
    the sentence. For each element in the list it returns a score in the range [0, 1], which predicts the probability 
    of the sentence to be an evidence for or against the topic. 

    """


def show_evidence_classifier_example():
    HEADERS = {'content-type': 'application/json',
               'charset': 'UTF-8'}
    uri = base_server_url_prefix + 'wp234-motion-evidence-gpu' + base_server_url + 'score/'
    payload = {'pairs': [
        'We should legalize cannabis^^^A cross-party report found good evidence that cannabis treatments can help alleviate the symptoms of chronic pain, multiple sclerosis, nausea and vomiting, particularly in the context of chemotherapy, and anxiety.',
        'We should legalize cannabis^^^cannabis is dangerous']}
    response = requests.post(url=uri, json=payload, headers=HEADERS)
    print(response.json())



    """
     This function provides an example to how to send a simple request to the claim classifier
     The claim classifier service receives list, where each element is a topic concatenated to "^^^", concatenated to 
     the sentence. For each element in the list it returns a score in the range [0, 1], which predicts the probability 
     of the sentence to contains claim for or against the topic. 

     """


def show_claim_classifier_example():
    HEADERS = {'content-type': 'application/json',
               'charset': 'UTF-8'}
    uri = base_server_url_prefix + 'wp234-claim-sentence-motion' + base_server_url + 'score/'
    payload = {'pairs': [
        'We should legalize cannabis^^^A cross-party report found good evidence that cannabis treatments can help alleviate the symptoms of chronic pain, multiple sclerosis, nausea and vomiting, particularly in the context of chemotherapy, and anxiety.',
        'We should legalize cannabis^^^cannabis is dangerous']}
    response = requests.post(url=uri, json=payload, headers=HEADERS)
    print(response.json())


def show_term_wikifier_example():
    HEADERS = {'content-type': 'application/json',
               'charset': 'UTF-8'}
    uri = base_server_url_prefix + 'tw' + base_server_url + 'TermWikifier/v2/annotate'
    payload = {
        'config': '',
        'contextTitles': [],
        'contextText': '',
        'textsToAnnotate': [
            {'text': 'Cats are much better than dogs',
             'contextTitles': []},
            {'text': 'Give me a wiki to stand, and I shall move the world.',
             'contextTitles': []},
        ]
    }
    response = requests.post(url=uri, json=payload, headers=HEADERS)
    print(response.json())


"""
    """
def show_term_relater_example():
    HEADERS = {'content-type': 'application/json',
               'charset': 'UTF-8'}
    uri = base_server_url_prefix + 'term-relater-service' + base_server_url + 'score/'
    payload = {'pairs':
        [
            {'first': 'Soldier',
             'second': 'Loneliness'},
            {'first': 'Army',
             'second': 'Soldier'}
        ]
    }
    response = requests.post(url=uri, json=payload, headers=HEADERS)
    print(response.json())

    """
    """
def show_speech_construction_example():
    HEADERS = {
    'Accept-Encoding': 'gzip, deflate',
    'Content-Type': 'application/json',
    'charset': 'utf-8'}
    uri = base_server_url_prefix + 'speech-construction' + base_server_url + '/api/v1/speech/generate'
    motionGenerationId = '1187'
    motionText = "We should legalize cannabis"
    creationTime = "Sun Sep 29 09:38:48 IDT 2019"
    polarity = "pro"
    dominantConcept = "Cannabis"
    eventId = "eventId-e2e"
    publish = "false"
    assess = "false"
    customizations = []
    payload = {'motionGenerationId' : motionGenerationId,
               'motionText' : motionText,
               'creationTime' : creationTime,
               'arguments': sc_example.args,
               'polarity' : polarity,
               'dominantConcept' : dominantConcept,
               'eventId' : eventId,
               'publish' : publish,
               'assess' : assess,
               'customizations' : customizations

               }
    response = requests.post(url=uri, json=payload, headers=HEADERS)
    print(response.json())


if __name__ == '__main__':

    print('\nClustering example:')
    show_clustering_example()

    print('\nQuality example:')
    show_quality_example()

    print('\nProCon example:')
    show_pro_con_example()

    print('\nTerm wikifier example:')
    show_term_wikifier_example()

    print('\nEvidence classifier example:')
    show_evidence_classifier_example()

    print('\nClaim classifier example:')
    show_claim_classifier_example()

    print('\nTerm relater example:')
    show_term_relater_example()

    print('\nSpeech construction example:')
    show_speech_construction_example()


