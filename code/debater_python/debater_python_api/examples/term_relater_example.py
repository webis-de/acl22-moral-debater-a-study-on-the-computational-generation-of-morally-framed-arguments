# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
term_relater_client = debater_api.get_term_relater_client()

term_pairs = [['Soldier', 'Army'],
              ['Pupil', 'Teacher'],
              ['Ball', 'Tree']]

scores = term_relater_client.run(term_pairs)

for i in range(len(term_pairs)):
    print('for pair: '+str(term_pairs[i])+', relatedness score: '+"{:.4f}".format(scores[i]))
