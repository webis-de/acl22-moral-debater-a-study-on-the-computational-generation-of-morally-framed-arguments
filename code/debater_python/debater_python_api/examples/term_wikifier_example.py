# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
term_wikifier_client = debater_api.get_term_wikifier_client()

sentences = [
    'Cars should only assist drivers since self driving cars are too dangerous.',
    'Self driving car technology will be in conflict with vehicles driven by human users']

annotation_arrays = term_wikifier_client.run(sentences)

for i, annotation_array in enumerate(annotation_arrays):
    print('For sentence: "{}", identified annotations are:'.format(sentences[i]))
    print('[')
    for annotation in annotation_array:
        print('    Text "{}", within span {}, is wikified to titled "{}", whose inlinks = {}.'
           .format(annotation['cleanText'], str(annotation['span']), annotation['concept']['title'], str(annotation['concept']['inlinks'])))
    print(']')
    print()
