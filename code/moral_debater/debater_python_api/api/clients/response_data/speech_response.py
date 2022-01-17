# (C) Copyright IBM Corp. 2020.


class ArgumentResponse:
    def __init__(self, id, text, in_speech, reason, user_id):
        self.id = id
        self.text = text
        self.in_speech = in_speech
        self.reason = reason
        self.user_id = user_id


class ClusterResponse:
    def __init__(self, theme, in_speech, elements):
        self.theme = theme
        self.in_speech = in_speech
        self.elements = elements


class ClusterElementResponse:
    def __init__(self, representative, similar_arguments):
        self.representative = representative
        self.similar_arguments = similar_arguments


class SpeechElement:
    def __init__(self, text, text_with_tts, contributing_arguments):
        self.text = text
        self.text_with_tts = text_with_tts
        self.contributing_arguments = contributing_arguments


class SpeechResult:
    def __init__(self, arguments, clusters, paragraphs, status, rows_for_kps_csv, rows_for_filtered_elements,
                 speech_generation_uniq_id=None, error_message=None):
        self.clusters = clusters
        self.arguments = arguments
        self.paragraphs = paragraphs
        self.speech_generation_uniq_id = speech_generation_uniq_id
        self.status = status
        self.error_message = error_message
        self.rows_for_kps_csv = rows_for_kps_csv
        self.rows_for_filtered_elements = rows_for_filtered_elements

    def __str__(self):
        paragraphs = [' '.join([element.text for element in paragraph])
                      for paragraph in self.paragraphs]
        return '\n\n'.join(paragraphs)

