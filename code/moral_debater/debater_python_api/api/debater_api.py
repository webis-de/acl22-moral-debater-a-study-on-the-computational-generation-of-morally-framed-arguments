# (C) Copyright IBM Corp. 2020.

from debater_python_api.api.clients import argument_quality_client
from debater_python_api.api.clients import claim_and_evidence_detection_client
from debater_python_api.api.clients import claim_boundaries_client
from debater_python_api.api.clients import index_searcher_client
from debater_python_api.api.clients import clustering_client
from debater_python_api.api.clients import embedding_client
from debater_python_api.api.clients import pro_con_client
from debater_python_api.api.clients import narrative_generation_client
from debater_python_api.api.clients import term_relater_client
from debater_python_api.api.clients import term_wikifier_client
from debater_python_api.api.clients import theme_extraction_client
from debater_python_api.api.sentence_level_index.client.elastic_client import IndexServiceClient
from debater_python_api.utils import general_utils
from debater_python_api.api.clients import keypoints_client
from debater_python_api.api.clients import keypoints_pairs_infer_client


class DebaterApi:
    def __init__(self, apikey):
        general_utils.validate_api_key_or_throw_exception(apikey)
        self._apikey = apikey

    def get_apikey(self):
        return self._apikey

    def get_pro_con_client(self):
        return pro_con_client.ProConClient(self.get_apikey())

    def get_term_wikifier_client(self):
        return term_wikifier_client.TermWikifierClient(self.get_apikey())

    def get_term_relater_client(self):
        return term_relater_client.TermRelaterClient(self.get_apikey())

    def get_evidence_detection_client(self):
        return claim_and_evidence_detection_client.EvidenceDetectionClient(self.get_apikey())

    def get_claim_detection_client(self):
        return claim_and_evidence_detection_client.ClaimDetectionClient(self.get_apikey())

    def get_claim_boundaries_client(self):
        return claim_boundaries_client.ClaimBoundariesClient(self.get_apikey())

    def get_argument_quality_client(self):
        return argument_quality_client.ArgumentQualityClient(self.get_apikey())

    def get_clustering_client(self):
        return clustering_client.ClusteringClient(self.get_apikey())

    def get_embedding_client(self):
        return embedding_client.EmbeddingClient(self.get_apikey())

    def get_theme_extraction_client(self):
        return theme_extraction_client.ThemeExtractionClient(self.get_apikey())

    # renainder from old code, does more services than we need for now
    # def get_searcher_client(self, url, index_name, version):
    #     return IndexServiceClient(url=url, index_name=index_name, service_version=version, apikey=self.get_apikey())

    def get_index_searcher_client(self):
        return index_searcher_client.IndexServiceClient(self.get_apikey())

    def get_narrative_generation_client(self):
        return narrative_generation_client.NarrativeGenerationClient(self.get_apikey())

    def get_keypoints_client(self):
        return keypoints_client.KpAnalysisClient(self.get_apikey(), 'https://keypoint-matching-backend.debater.res.ibm.com')

    def get_keypoints_pairs_infer_client(self):
        return keypoints_pairs_infer_client.KpPairsInferClient(self.get_apikey(), 'https://keypoint-matching.debater.res.ibm.com')


