# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi
from debater_python_api.examples.resources.arguments import arguments_list
from debater_python_api.examples.resources.pro_con_scores import pro_con_scores
from debater_python_api.api.clients.narrative_generation_client import Polarity

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
speech_construction_client = debater_api.get_narrative_generation_client()

topic = "We should legalize cannabis"
polarity = "pro"
dominant_concept = "Cannabis"

speech = speech_construction_client.run(topic=topic, dc=dominant_concept, sentences=arguments_list,
                                        pro_con_scores=pro_con_scores, polarity=Polarity.PRO)

print(speech)

print()
print()
json_string = speech_construction_client.get_customization()
print("customization string:\n"+json_string)