# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
argument_quality_client = debater_api.get_argument_quality_client()

topic = "We should further explore the development of autonomous vehicles"
sentences = [
    'Cars should only provide assisted driving, not complete autonomy.',
    'Cars cars cars cars who cares',
    'that he given sun roads sea']

sentence_topic_dicts = [{'sentence': sentence, 'topic': topic} for sentence in sentences]

scores = argument_quality_client.run(sentence_topic_dicts)

for i in range(len(scores)):
    print("sentence: " + sentence_topic_dicts[i]['sentence'])
    print("topic: "+sentence_topic_dicts[i]['topic'])
    print("score: "+"{:.4f}".format(scores[i]))
    print()

