# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.debater_api import DebaterApi

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
embedding_client = debater_api.get_embedding_client()

sentences = ["ai is providing breakthroughs in medical technology that can save a lot of lives and find new cures.",
             "ai is paving the way for major medical advancements to cure many medical disorders.",
             "due to precision medicine, ai will be able to better provide personalized medical care that can improve quality of life.",
             "ai will enable technology to advance and further medical research which will save lives.",
             "ai is helping create major breakthroughs in medical research."]

embeddings = embedding_client.run('tf', sentences, mask = "ai brings more harm than good")
for e in embeddings:
    print(e)
