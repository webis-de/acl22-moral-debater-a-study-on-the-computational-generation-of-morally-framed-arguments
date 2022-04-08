# (C) Copyright IBM Corp. 2020.


from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
claim_boundaries_client = debater_api.get_claim_boundaries_client()

sentences = ['A cross-party report found good evidence that cannabis treatments can help alleviate the symptoms of chronic pain, multiple sclerosis, nausea and vomiting, particularly in the context of chemotherapy, and anxiety.',
             'A recent federal study indicates that cannabis is dangerous']

boundaries_dicts = claim_boundaries_client.run(sentences)

for i in range(len(sentences)):
    print ('in sentence: '+sentences[i])
    print ('claim was detected in positions ['+str(boundaries_dicts[i]['span'][0])+', '+str(boundaries_dicts[i]['span'][1])+'], being the claim: '
           +boundaries_dicts[i]['claim'])
    print ()

