from debater_python_api.api.debater_api import DebaterApi
from debater_python_api.api.clients.keypoints_client import KpAnalysisUtils

debater_api = DebaterApi('PUT_YOUR_API_KEY_HERE')
keypoints_client = debater_api.get_keypoints_client()

comments_texts = [
    'Cannabis has detrimental effects on cognition and memory, some of which are irreversible.',
    'Cannabis can severely impact memory and productivity in its consumers.',
    'Cannabis harms the memory and learning capabilities of its consumers.',
    'Frequent use can impair cognitive ability.',
    'Cannabis harms memory, which in the long term hurts progress and can hurt people',
    'Frequent marijuana use can seriously affect short-term memory.',
    'Marijuana is very addictive, and therefore very dangerous'
    'Cannabis is addictive and very dangerous for use.',
    'Cannabis can be very harmful and addictive, especially for young people',
    'Cannabis is dangerous and addictive.'
                  ]

KpAnalysisUtils.init_logger()
keypoint_matchings = keypoints_client.run(comments_texts)
KpAnalysisUtils.print_result(keypoint_matchings, print_matches=True)
