# (C) Copyright IBM Corp. 2020.
'''
Example of using the pro-con clint, bout at old and new API.
Note that certain pro-con service supports the old API OR the new API, but not both.
In order to use the client for servers that support the old API, use the method 'run' with b2 parameters: topic and
arguments.
In order to use the client for servers that support the new API, use the method run with passing by name the parameter
sentence_topic_dicts, and with the optional parameter single_score_format (default is True), which determine
whether the client output will be the old format (list of score in range [-1,1]), or the new format (list of dict, with
probabilities for pro, con, and neutral classes).
'''

from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
pro_con_client = debater_api.get_pro_con_client()

topic = 'Social media is harmful'
sentences = [
    'Social media disproportionally promotes fake news',
    'Social media is wonderful for human relationship',
    'The air in Los Angeles is clear']

sentence_topic_dicts = [{'sentence' : sentence, 'topic' : topic } for sentence in sentences]

scores = pro_con_client.run(sentence_topic_dicts)

print('With respect to topic: "'+topic+'", sentences and their scores are: \n')
for i in range(len(sentences)):
    print("Sentence : "+sentences[i])
    print("Score: "+"{:.4f}".format(scores[i]))
    print()
