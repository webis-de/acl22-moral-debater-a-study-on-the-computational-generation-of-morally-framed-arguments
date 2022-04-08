# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
clustering_client = debater_api.get_clustering_client()

sentences = ['The cat (Felis catus) is a small carnivorous mammal',
             'The origin of the domestic dog includes the dogs evolutionary divergence from the wolf',
             'As of 2017, the domestic cat was the second-most popular pet in the U.S.',
             'Domestic dogs have been selectively bred for millennia for various behaviors, sensory capabilities, and physical attributes.',
             'Cats are similar in anatomy to the other felid species',
             'Dogs are highly variable in height and weight.']

clusters_list = clustering_client.run(sentences=sentences, num_of_clusters=2)
for cluster in clusters_list:
    print('[')
    for sentence in cluster:
        print("  "+sentence)
    print (']')
