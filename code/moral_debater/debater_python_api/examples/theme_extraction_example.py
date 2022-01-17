# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')

theme_extraction_client = debater_api.get_theme_extraction_client()

dominant_concept = 'Animal'
topic = 'We should love animals'
clusters = [
    [
        'The cat (Felis catus) is a small carnivorous mammal',
        'As of 2017, the domestic cat was the second-most popular pet in the U.S.',
        'Cats are similar in anatomy to the other felid species'
    ],
    [
        'The origin of the domestic dog includes the dogs evolutionary divergence from the wolf',
        'Domestic dogs have been selectively bred for millennia for various behaviors, sensory capabilities, and physical attributes.',
        'Dogs are highly variable in height and weight'
    ]
]

theme_extraction_results = theme_extraction_client.run(topic, dominant_concept, clusters)
for result in theme_extraction_results:
    print ('Themes for cluster: \n[')
    for theme_dict in result:
        print('  Theme: {}, of pValue = {}'.format(theme_dict['theme'], "{:.4f}".format(theme_dict['pValue'])))
    print (']')
    print()
