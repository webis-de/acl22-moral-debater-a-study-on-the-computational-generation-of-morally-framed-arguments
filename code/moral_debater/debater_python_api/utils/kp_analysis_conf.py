from debater_python_api.integration_tests.api.clients.DebaterApiWithAdjustedUrl import Domains

api_key1 = 'PUT_YOUR_API_KEY_HERE1'
second_api_key = 'PUT_YOUR_API_KEY_HERE2'

# must be located in debater_python_api/integration_tests/test_data_files
comments_csv_file = 'dataset_austin_open_ended_comments_3k_with_ids.csv'
comments_csv_file_ids_col = 'id'
comments_csv_file_text_col = 'comment'
default_env_in_test = Domains.test
default_use_cache_in_test = False

# Host String. If None - takes test_default_env
keypoint_analysis_local_host = None

results_dir = '<dir>'
keypoint_analysis_host = '<host>'