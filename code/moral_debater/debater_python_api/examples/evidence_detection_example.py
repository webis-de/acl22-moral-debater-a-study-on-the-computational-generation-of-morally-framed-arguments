# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
evidence_detection_client = debater_api.get_evidence_detection_client()

topic = 'We should legalize cannabis'
sentences = ['A cross-party report found good evidence that cannabis treatments can help alleviate the symptoms of chronic pain, multiple sclerosis, nausea and vomiting, particularly in the context of chemotherapy, and anxiety.',
             'A recent federal study indicates that cannabis is dangerous',
             'cannabis is dangerous',
             'The air in Los Angeles is clear']

sentence_topic_dicts = [{'sentence':sentence, 'topic':topic} for sentence in sentences]

scores = evidence_detection_client.run(sentence_topic_dicts)

for j in range(len(sentence_topic_dicts)):
    print('topic: '+sentence_topic_dicts[j]['topic'])
    print('sentence: '+sentence_topic_dicts[j]['sentence'])
    print('score: '+"{:.4f}".format(scores[j]))
    print()
