import logging
import os
import time
import calendar
import traceback
from collections import defaultdict
from pathlib import Path

import requests
from debater_python_api.api.clients.abstract_client import AbstractClient
from debater_python_api.utils.general_utils import get_default_request_header
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from debater_python_api.utils.kp_analysis_utils import print_progress_bar

domains_endpoint = '/domains'
comments_endpoint = '/comments'
kp_extraction_endpoint = '/kp_extraction'
data_endpoint = '/data'
report_endpoint = '/report'
self_check_endpoint = '/self_check'


class KpAnalysisUtils:
    '''
    A class with static methods for utilities that assist with the key point analysis service.
    '''

    @staticmethod
    def print_result(result, print_matches=False):
        '''
        Prints the key point analysis result to console.
        :param result: the result, returned by method get_result in KpAnalysisTaskFuture.
        '''
        def print_kp(kp, n_matches, n_matches_subtree, depth, print_matches, keypoint_matching):
            spaces = '     ' * depth
            has_n_matches_subtree = n_matches_subtree is not None
            print('%s    %d%s - %s' % (spaces, n_matches_subtree if has_n_matches_subtree else n_matches,
                                       (' - %d' % n_matches) if has_n_matches_subtree else '', kp))
            if print_matches:
                for match in keypoint_matching['matching']:
                    print('%s    %s - %s' % (spaces + '    ', str(match['score']), match['sentence_text']))

        kp_to_n_matches_subtree = defaultdict(int)
        parents = list()
        parent_to_kids = defaultdict(list)
        for keypoint_matching in result['keypoint_matchings']:
            kp = keypoint_matching['keypoint']
            kp_to_n_matches_subtree[kp] += len(keypoint_matching['matching'])
            parent = keypoint_matching.get("parent", None)
            if parent is None or parent == 'root':
                parents.append(keypoint_matching)
            else:
                parent_to_kids[parent].append(keypoint_matching)
                kp_to_n_matches_subtree[parent] += len(keypoint_matching['matching'])

        parents.sort(key=lambda x: kp_to_n_matches_subtree[x['keypoint']], reverse=True)

        print('Result:')
        for parent in parents:
            kp = parent['keypoint']
            print_kp(kp, len(parent['matching']), None if len(parent_to_kids[kp]) == 0 else kp_to_n_matches_subtree[kp], 0, print_matches, parent)
            for kid in parent_to_kids[kp]:
                kid_kp = kid['keypoint']
                print_kp(kid_kp, len(kid['matching']), None, 1, print_matches, kid)

    @staticmethod
    def print_report(user_report):
        '''
        Prints the user_report to console.
        :param user_report: the user report, returned by method get_full_report in KpAnalysisClient.
        '''
        logging.info('User Report:')
        comments_statuses = user_report['comments_status']
        logging.info('  Comments status by domain (%d domains):' % len(comments_statuses))
        if len(comments_statuses) == 0:
            logging.info('    User has no domains')
        else:
            for domain in comments_statuses:
                logging.info('    Domain: %s, Status: %s ' % (domain, str(comments_statuses[domain])))
        kp_analysis_statuses = user_report['kp_analysis_status']
        logging.info('  Key point analysis - jobs status (%d jobs):' % len(kp_analysis_statuses))
        if len(kp_analysis_statuses) == 0:
            logging.info('    User has no key point analysis jobs history')
        else:
            for kp_analysis_status in kp_analysis_statuses:
                logging.info('    Job: ' + str(kp_analysis_status))

    @staticmethod
    def set_stance_to_result(result, stance):
        for keypoint_matching in result['keypoint_matchings']:
            keypoint_matching['stance'] = stance
        return result

    @staticmethod
    def merge_two_results(result1, result2):
        result = {'keypoint_matchings': result1['keypoint_matchings'] + result2['keypoint_matchings']}
        result['keypoint_matchings'].sort(key=lambda matchings: len(matchings['matching']), reverse=True)
        return result

    @staticmethod
    def write_result_to_csv(result, result_file):
        '''
        Writes the key point analysis result to file.
        Creates two files:
        * matches file: a file with all sentence-key point matches, saved in result_file path.
        * summary file: a summary file with all key points and their aggregated information, saved in result_file path with suffix: _kps_summary.csv.
        :param result: the result, returned by method get_result in KpAnalysisTaskFuture.
        :param result_file: a path to the file that will be created (should have a .csv suffix, otherwise it will be added).
        '''
        def _write_df_to_file(df, file):
            logging.info("Writing dataframe to: " + file)
            file_path = Path(file)
            if not os.path.exists(file_path.parent):
                logging.info('creating directory: %s' % str(file_path.parent))
                os.makedirs(file_path.parent)
            df.to_csv(file, index=False)

        if 'keypoint_matchings' not in result:
            logging.info("No keypoint matchings results")
            return

        if '.csv' not in result_file:
            result_file += '.csv'

        total_sentences = np.sum([len(keypoint_matching['matching']) for keypoint_matching in result['keypoint_matchings']])
        all_comment_ids = set([m["comment_id"] for keypoint_matching in result['keypoint_matchings'] for m in keypoint_matching['matching']])
        total_comments = len(all_comment_ids)

        summary_rows = []
        matchings_rows = []
        kp_to_parent = {}
        kps_have_stance = False
        sentences_have_stance = False
        for keypoint_matching in result['keypoint_matchings']:
            kp = keypoint_matching['keypoint']
            kp_stance = keypoint_matching.get('stance', None)
            n_sentences = len(keypoint_matching['matching'])
            sentence_coverage = n_sentences / total_sentences if total_sentences > 0 else 0.0
            n_comments = len(set([m["comment_id"] for m in keypoint_matching['matching']]))
            comments_coverage = n_comments / total_comments if total_comments > 0 else 0.0

            summary_row = [kp, n_sentences, sentence_coverage, n_comments, comments_coverage]
            if kp_stance is not None:
                summary_row.append(kp_stance)
                kps_have_stance = True

            summary_rows.append(summary_row)
            kp_to_parent[kp] = keypoint_matching.get("parent", None)
            for match in keypoint_matching['matching']:
                match_row = [kp, match["sentence_text"], match["score"], match["comment_id"], match["sentence_id"],
                             match["sents_in_comment"], match["span_start"], match["span_end"], match["num_tokens"],
                             match["argument_quality"]]

                if 'stance' in match:
                    match_row.append(match['stance'])
                    sentences_have_stance = True
                if kp_stance is not None:
                    match_row.append(kp_stance)
                matchings_rows.append(match_row)

        summary_rows = sorted(summary_rows, key=lambda x: x[4], reverse=True)
        summary_cols = ["kp", "#sentences", 'sentences_coverage', '#comments', 'comments_coverage']
        if kps_have_stance:
            summary_cols.append('stance')
        summary_df = pd.DataFrame(summary_rows, columns=summary_cols)

        if len(set(kp_to_parent.values())) > 1:
            summary_df.loc[:, "parent"] = summary_df.apply(lambda x: kp_to_parent[x["kp"]], axis=1)
            parent_to_kps = {p: list(filter(lambda x: kp_to_parent[x] == p, kp_to_parent.keys()))
                             for p in set(kp_to_parent.values())}
            parent_to_kps.update({p: [] for p in set(parent_to_kps["root"]).difference(parent_to_kps.keys())})
            kp_to_n_args = dict(zip(summary_df["kp"],summary_df["#sentences"]))
            kp_to_n_args_sub = {kp: np.sum([kp_to_n_args[c_kp] for c_kp in set(parent_to_kps.get(kp, []) + [kp])])
                                for kp in kp_to_parent}
            kp_to_n_args_sub["root"] = np.sum(list(summary_df["#sentences"]))
            summary_df.loc[:, "#sents_in_subtree"] = summary_df.apply(lambda x: kp_to_n_args_sub[x["kp"]], axis=1)

            hierarchy_data = [[p, len(parent_to_kps[p]), kp_to_n_args_sub[p], parent_to_kps[p]] for p in parent_to_kps]
            hierarchy_df = pd.DataFrame(hierarchy_data, columns=["top_kp", "#level_2_kps", "#sents_in_subtree", "level_2_kps"])
            hierarchy_df.sort_values(by=["#sents_in_subtree"], ascending=False)

            hierarchy_file = result_file.replace(".csv", "_kp_hierarchy.csv")
            _write_df_to_file(hierarchy_df, hierarchy_file)

        summary_file = result_file.replace(".csv", "_kps_summary.csv")
        _write_df_to_file(summary_df, summary_file)

        matchings_cols = ["kp", "sentence_text", "match_score", 'comment_id', 'sentence_id', 'sents_in_comment', 'span_start',
                'span_end', 'num_tokens', 'argument_quality']
        if sentences_have_stance:
            matchings_cols.append('stance_dict')
        if kps_have_stance:
            matchings_cols.append('kp_stance')
        match_df = pd.DataFrame(matchings_rows, columns=matchings_cols)
        _write_df_to_file(match_df, result_file)

    @staticmethod
    def init_logger():
        '''
        Inits the logger for more informative console prints.
        '''
        from logging import getLogger, getLevelName, Formatter, StreamHandler
        log = getLogger()
        log.setLevel(getLevelName('INFO'))
        log_formatter = Formatter("%(asctime)s [%(levelname)s] %(filename)s %(lineno)d: %(message)s")

        console_handler = StreamHandler()
        console_handler.setFormatter(log_formatter)
        log.handlers = []
        log.addHandler(console_handler)


class KpaIllegalInputException(Exception):
    '''
    This exception is thrown when the user passes an illegal input.
    '''
    pass


class KpAnalysisClient(AbstractClient):
    '''
    A client for the Key Point Analysis (KPA) service.
    '''
    def __init__(self, apikey: str, host: Optional[str]=None):
        '''
        :param apikey: user's api-key, should be retreived from the early-access-program site.
        :param host: optional, enable switching to alternative services.
        '''
        AbstractClient.__init__(self, apikey)
        self.host = host if host is not None else 'https://keypoint-matching-backend.debater.res.ibm.com'

    def _delete(self, url, params, use_cache=True, timeout=300, retries=10):
        return self._run_request_with_retry(requests.delete, url, params, use_cache, timeout, retries)

    def _get(self, url, params, use_cache=True, timeout=300, retries=10):
        return self._run_request_with_retry(requests.get, url, params, use_cache, timeout, retries)

    def _post(self, url, body, use_cache=True, timeout=300, retries=10):
        return self._run_request_with_retry(requests.post, url, body, use_cache, timeout, retries)

    def _run_request_with_retry(self, func, url, params, use_cache=True, timeout=20, retries=10):
        headers = get_default_request_header(self.apikey)
        logging.info('client calls service (%s): %s' % (func.__name__, url))
        if not use_cache:
            headers['cache-control'] = 'no-cache'

        while True:
            try:
                if func.__name__ == 'post':
                    resp = func(url, json=params, headers=headers, timeout=timeout)
                else:
                    resp = func(url, params=params, headers=headers, timeout=timeout)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 422:
                    msg = 'There is a problem with the request (%d): %s' % (resp.status_code, resp.reason)
                    logging.error(msg)
                    raise KpaIllegalInputException(msg)
                msg = 'Failed calling server at %s: (%d) %s' % (url, resp.status_code, resp.reason)
            except KpaIllegalInputException as e:
                raise e
            except Exception as e:
                track = traceback.format_exc()
                msg = "Can't access server at {}. Exception: {}".format(url, track)

            retries -= 1
            if retries < 0:
                raise ConnectionError(msg)
            else:
                logging.warning('%s, retries left: %d' % (msg, retries))
                time.sleep(10)

    def _is_list_of_strings(self, lst):
        return isinstance(lst, list) and len([a for a in lst if not isinstance(a, str)]) == 0

    def create_domain(self, domain, domain_params=None):
        '''
        Creates a new domain and enables users to set domain parameters.
        :param domain: the name of the new domain (must not exist already)
        :param domain_params: a dictionary with various parameters for the domain. Supported values:
        * dont_split: (Boolean, set to False by default), when set to True, the comments uploaded to the domain will not be cleaned and not be split into sentences.
        * dc: (String) a dominant-concept to use as a topic for the argument_quality service
        * motion: (String) a motion to use as a topic for the argument_quality service (either use motion or dc, not both)
        '''
        body = {'domain': domain}
        if domain_params is not None:
            body['domain_params'] = domain_params

        self._post(url=self.host + domains_endpoint, body=body)
        logging.info('created domain: %s with domain_params: %s' % (domain, str(domain_params)))


    def upload_comments(self, domain: str, comments_ids: List[str], comments_texts: List[str], dont_split=False, batch_size: int = 2000) -> None:
        '''
        Uploads comments into a domain. These comments are processed and splitted into sentences.
        It is not mandatory to create domain before uploading comments. If the domain doesn't exist, a domain with default parameters will be created.
        When we need to change domain params, we must create it first via create_domain method.
        Users can clean their comments and split them into sentences themselves, if they wish to do so.
        In this case, dont_split parameter should be set to True, and the uploaded comments will be kept as is.
        Re-uploading the same comments (same domain + comment_id, text is ignored) is not problematic (and relativly quick).
        Processing comments (cleaning + sentence splitting + calculating quality etc.) takes some time,
        please wait for it to finish before starting a key point analysis job (using method wait_till_all_comments_are_processed).
        :param domain: the name of the domain to upload the comments into. (usually one per data-set).
        :param comments_ids: a list of comment ids (strings), comment ids must be unique.
        :param comments_texts: a list of comments (strings), this list must be the same length as comments_ids and the comment_id and comment_text should match by position in the list.
        :param dont_split: when set to True, the comments uploaded to the domain will not be cleaned and not be split into sentences.
        :param batch_size: the number of comments that will be uploaded in every REST-API call.
        '''
        assert len(comments_ids) == len(comments_texts), 'comments_texts and comments_ids must be the same length'
        assert len(comments_ids) == len(set(comments_ids)), 'comment_ids must be unique'
        assert self._is_list_of_strings(comments_texts), 'comment_texts must be a list of strings'
        assert self._is_list_of_strings(comments_ids), 'comment_ids must be a list of strings'
        assert len([c for c in comments_texts if len(c) > 1000]) == 0, 'comment_texts must be shorter then 1000 characters'
        logging.info('uploading %d comments in batches' % len(comments_ids))

        ids_texts = list(zip(comments_ids, comments_texts))
        uploaded = 0
        batches = [ids_texts[i:i + batch_size] for i in range(0, len(ids_texts), batch_size)]
        for batch in batches:
            comments_ids = [t[0] for t in batch]
            comments_texts = [t[1] for t in batch]
            body = {'domain': domain,
                    'comments_ids': comments_ids,
                    'comments_texts': comments_texts}

            if dont_split:
                body['dont_split'] = True

            self._post(url=self.host + comments_endpoint, body=body, retries=10)
            uploaded += len(batch)
            logging.info('uploaded %d comments, out of %d' % (uploaded, len(ids_texts)))

    def get_comments_status(self, domain: str) -> Dict[str, int]:
        '''
        Get the status of the comments in a domain.
        :param domain: the name of the domain
        :return: a dictionary with the status:
        * processed_comments: number of comments that where already processed
        * pending_comments: number of comments that still need to be processed
        * processed_sentences: number of sentences after sentence-splitting the processed comments
        '''
        res = self._get(self.host + comments_endpoint, {'domain': domain})
        logging.info('domain: %s, comments status: %s' % (domain, str(res)))
        return res

    def wait_till_all_comments_are_processed(self, domain: str, polling_timout_secs: Optional[int] = None) -> None:
        '''
        Waits for all comments in a domain to be processed.
        :param domain: the name of the domain
        '''
        while True:
            res = self.get_comments_status(domain)
            if res['pending_comments'] == 0:
                break
            time.sleep(polling_timout_secs if polling_timout_secs is not None else 10)

    def start_kp_analysis_job(self, domain: str, comments_ids: Optional[List[str]]=None, key_points: Optional[List[str]]=None,
                              key_points_by_job_id: Optional[str]=None, run_params=None, description: Optional[str]=None, use_cache: bool = True) -> 'KpAnalysisTaskFuture':
        '''
        Starts a Key Point Analysis (KPA) job in an async manner. Please make sure all comments had already been uploaded into a domain and processed before starting a new job (using the wait_till_all_comments_are_processed method).
          * By default it runs over all comments in the domain. In order to run only on a subset of the comments in the domain, pass their ids in the comment_ids param.
          * key points are automatically extracted unless they are provided in the key_points parameter in which case the service matches the sentences to the given key points. This enables a human-in-the-loop scenario, where the automatically extracted key points are reviewed by the user, and the sentences are then remapped to the revised key points.
          * It is also possible to use key points from a previous job by suppling the job_id in the key_points_by_job_id param. Note that only one of the key_points and key_points_by_job_id params can be used, not both.
          * It is also possible to add a job description. This description will later be visible in the user-report.
          * Every domain has a cache. When running a new job, only the delta from previous jobs in the same domain is calculated.
          * Different parameters that affect the job and its result can be passed in the run_params parameter:
              * arg_min_len (Integer, set to 4 by default): Filter shorter sentences (by number of tokens).
              * arg_max_len (Integer, set to 36 by default): Filter longer sentences (by number of tokens).
              * arg_relative_aq_threshold (Float in [0.0,1.0], set to 1.0 by default): Filter sentences having a quality score below this precentile (useful to filter out low quality data in the data-set).
              * clustering_threshold (Float in [0.0,1.0], set to 0.99 by default): Used for key points selection: choose higher values for more fine-grained key points, and lower for more distinct key points.
              * mapping_threshold (Float in [0.0,1.0], set to 0.99 by default): The matching threshold, scores above are considered a match. A higher threshold leads to a higher precision and a lower coverage.
              * n_top_kps (Integer, default is set by an internal algorithm): Number of key points to generate. Lower value will make the job finish faster. All sentences are re-mapped to these key point.
              * kp_relative_aq_threshold (Float in [0.0,1.0], set to 0.65 by default): Sentences having AQ score below this precentile will not be selected as key point candidates.
              * invalid_kps_comment_ids (String list, empty by default): A list of comment_ids who’s sentences should not be selected as key point candidates.
        :param domain: the name of the domain
        :param comments_ids: when None is passed, it uses all comments in the domain (typical usage) otherwise it only uses the comments according to the provided list of comment_ids.
        :param key_points: when a list of key points is passed (as a list of strings) it will use the provided key points and matches all sentences to them. Otherwise, it extracts key points automatically.
        :param key_points_by_job_id: when job_id is passed, it will use the key points from the result of that job in the current run and matches all senteces to them.
        :param run_params: a dictionary with different parameters and their values (see description above). e.g. run_param={'arg_min_len': 5, 'arg_max_len': 40, 'mapping_threshold': 0.0}
        :param description: add a description to a job so it will be easy to detecte it in the user-report.
        :param use_cache: determines whether the cache is used (should be kept as True for faster more efficient runs).
        :return: KpAnalysisTaskFuture: an object that enables the retrieval of the results in an async manner.
        '''
        body = {'domain': domain}

        if comments_ids is not None:
            body['comments_ids'] = comments_ids

        if run_params is not None:
            body['run_params'] = run_params

        if key_points is not None and key_points_by_job_id is not None:
            raise Exception("please pass keypoints either by key_points param or key_points_by_job_id, not both")

        if key_points is not None:
            body['key_points'] = key_points

        if key_points_by_job_id is not None:
            body['key_points_by_job_id'] = key_points_by_job_id

        if description is not None:
            body['description'] = description

        res = self._post(url=self.host + kp_extraction_endpoint, body=body, use_cache=use_cache)
        logging.info('started a kp analysis job - domain: %s, job_id: %s' % (domain, res['job_id']))
        return KpAnalysisTaskFuture(self, res['job_id'])

    def get_kp_extraction_job_status(self, job_id: str, top_k_kps: Optional[int] = None,
                                     top_k_sentences_per_kp: Optional[int] = None):
        '''
        Checks for the status of a key point analysis job. It returns a json with a 'status' key that can have one of the following values: PENDING, PROCESSING, DONE, CANCELED, ERROR
        If the status is PROCESSING, it also have a 'progress' key that describes the calculation progress.
        If the status is DONE, it also have a 'result' key that has the result json.
        If the status is ERROR, it also have a 'error_msg' key that has the description of the error.
        The result json have the following structure:
            * 'keypoint_matchings': a list of keypoint_matching (key point and its matched sentences). Sorted descendingly according to number of matched sentences. each keypoint_matching have:
                * 'keypoint': the key point (string).
                * 'matching': a list of matches (sentences that match the key point). each match have the sentences details ('domain', 'comment_id', 'sentence_id', 'sents_in_comment', 'span_start', 'span_end', 'num_tokens', 'argument_quality', 'sentence_text') and a match score ('score') this is the match score between the sentence and the key point. The matchings are sorted descendingly according to their match score.
        :param job_id: the job_id (can be found in the future returned when the job was started or in the user-report)
        :param top_k_kps: use this parameter to truncate the result json to have only the top K key points.
        :param top_k_sentences_per_kp: use this parameter to truncate the result json to have only the top K matched sentences per key point.
        :return: see description above.
        '''
        params = {'job_id': job_id}

        if top_k_kps is not None:
            params['top_k_kps'] = top_k_kps

        if top_k_sentences_per_kp is not None:
            params['top_k_sentences_per_kp'] = top_k_sentences_per_kp

        return self._get(self.host + kp_extraction_endpoint, params, timeout=180)

    def run(self, comments_texts: List[str], comments_ids: Optional[List[str]]=None):
        '''
        This is the simplest way to use the Key Point Analysis system.
        This method uploads the comments into a temporary domain, waits for them to be processed, starts a Key Point Analysis job using all comments (auto key points extraction with default parameters), and waits for the results. Eventually, the domain is deleted.
        It is possible to use this method for up to 1000 comments. For longer jobs, please run the system in a stagged manner (upload the comments yourself, start a job etc').
        :param comments_texts: a list of comments (strings).
        :param comments_ids: (optional) a list of comment ids (a list of strings). When not provided, dummy comment_ids will be generated (1, 2, 3,...). When provided, comment_ids must be unique, must be the same length as comments_texts and the comment_id and comment_text should match by position in the list.
        :return: a json with the result
        '''
        if len(comments_texts) > 1000:
            raise Exception('Please use the stagged mode (upload_comments, start_kp_analysis_job) for jobs with more then 1000 comments')

        if comments_ids is None:
            comments_ids = [str(i) for i in range(len(comments_texts))]
        domain = 'run_temp_domain_' + str(calendar.timegm(time.gmtime()))
        logging.info('uploading comments')
        self.upload_comments(domain, comments_ids, comments_texts)
        logging.info('waiting for the comments to be processed')
        self.wait_till_all_comments_are_processed(domain)
        logging.info('starting the key point analysis job')
        future = self.start_kp_analysis_job(domain)
        logging.info('waiting for the key point analysis job to finish')
        keypoint_matching = future.get_result(high_verbosity=True)
        self.delete_domain_cannot_be_undone(domain)
        return keypoint_matching

    def cancel_kp_extraction_job(self, job_id: str):
        '''
        Stops a running key point analysis job.
        :param job_id: the job_id
        :return: the request's response
        '''
        return self._delete(self.host + kp_extraction_endpoint, {'job_id': job_id})

    def cancel_all_extraction_jobs_for_domain(self, domain: str, clear_kp_analysis_jobs_log: bool = False):
        '''
        Stops all running jobs and cancels all pending jobs in a domain.
        :param domain: the name of the domain.
        :param clear_kp_analysis_jobs_log: When set to True, clears all jobs in this domain from the jobs-history in the user-report (useful when the report becomes too long).
        :return: the request's response
        '''
        return self._delete(self.host + data_endpoint, {'domain': domain, 'clear_kp_analysis_jobs_log': clear_kp_analysis_jobs_log, 'clear_db': False})

    def cancel_all_extraction_jobs_all_domains(self, clear_kp_analysis_jobs_log: bool = False):
        '''
        Stops all running jobs and cancels all pending jobs in all domains.
        :param clear_kp_analysis_jobs_log: When set to True, also clears all jobs (in all domains) from the jobs-history in the user-report (useful when the repots becomes too long).
        :return: the request's response
        '''
        return self._delete(self.host + data_endpoint, {'clear_kp_analysis_jobs_log': clear_kp_analysis_jobs_log, 'clear_db': False})

    def delete_domain_cannot_be_undone(self, domain: str, clear_kp_analysis_jobs_log: bool = False):
        '''
        Deletes a domain. Stops all running jobs and cancels all pending jobs in a domain. Erases the data (comments and sentences) in a domain and clears the domain's cache.
        When uploaded comments in a domain need to be replaced, first delete the domain and then upload the updated comments.
        :param domain: the name of the domain
        :param clear_kp_analysis_jobs_log: When set to True, also clears all jobs in the domain from the jobs-history in the user-report (useful when the repots becomes too long).
        :return: the request's response
        '''
        return self._delete(self.host + data_endpoint, {'domain': domain, 'clear_kp_analysis_jobs_log': clear_kp_analysis_jobs_log, 'clear_db': True})

    def delete_all_domains_cannot_be_undone(self, clear_kp_analysis_jobs_log: bool = False):
        '''
        Deletes all user's domains. Stops all running jobs and cancels all pending jobs in all domains. Erases the data (comments and sentences) in all domains and clears all domains' caches.
        :param clear_kp_analysis_jobs_log: When set to True, also clears all jobs (in all domains) from the jobs-history in the user-report (useful when the repots becomes too long).
        :return: the request's response
        '''
        return self._delete(self.host + data_endpoint, {'clear_kp_analysis_jobs_log': clear_kp_analysis_jobs_log, 'clear_db': True})

    def get_full_report(self, days_ago=30):
        '''
        Retreives a json with the user's report.
        :param days_ago: key point analysis jobs older then this parameter will be filtered out
        returns: The report which consists:
          * 'comments_status': all the domains that the user have and the current status of each domain (number of processed comments, sentences and comments that still need to be processed, similar to get_comments_status method).
          * 'kp_analysis_status': a list of all key point analysis jobs that the user have/had with all the relevant details and parameters for each job.
        '''
        return self._get(self.host + report_endpoint, {'days_ago': days_ago}, timeout=180)

    def run_self_check(self):
        '''
        Checks the connection to the service and if the service is UP and running.
        :return: a json with 'status': that have the value UP if all is well and DOWN otherwise.
        '''
        return self._get(self.host + self_check_endpoint, None, timeout=180)

    def get_sentences_for_domain(self, domain: str, job_id: Optional[str] = None):
        '''
        Uploaded comments are cleaned and splitted into sentences. This method retrieves the sentences in a domain.
        :param domain: the name of the domain.
        :param job_id: when provided, it will only return the sentences used in a specific key point analysis job.
        :return: a dictionary with all the sentences' details.
        '''
        res = self._get(self.host + data_endpoint, {'domain': domain, 'get_sentences': True, 'job_id': job_id})
        logging.info(res['msg'])
        return res['sentences_results']


class KpAnalysisTaskFuture:
    '''
    A future for an async key point analysis job. Wraps the job_id and uses a provided client for retrieving the job's result.
    Usually created when starting a key point analysis job but can also be created by a user, by suppling the client and the job_id.
    The job_id can be retrieved from the console (it is printed to console when a job is started) or from the user-report.
    '''
    def __init__(self, client: KpAnalysisClient, job_id: str):
        '''
        Create a KpAnalysisTaskFuture over a job_id for results retrieval.
        :param client: a client for communicating with the service.
        :param job_id: the job_id. The job_id can be retrieved from the console (it is printed to console when a job is started) or from the user-report.
        '''
        self.client = client
        self.job_id = job_id
        self.polling_timout_secs = 60

    def get_job_id(self) -> str:
        '''
        :return: the job_id
        '''
        return self.job_id

    def get_result(self, top_k_kps: Optional[int] = None, top_k_sentences_per_kp: Optional[int] = None,
                   dont_wait: bool = False, wait_secs: Optional[int] = None, polling_timout_secs: Optional[int] = None,
                   high_verbosity: bool = True):
        '''
        Retreives the job's result. This method polls and waits till the job is done and the result is available.
        The result-json consists:
            * 'keypoint_matchings': a list of keypoint_matching (key point and its matched sentences). Sorted descendingly according to number of matched sentences. each keypoint_matching have:
                * 'keypoint': the key point string.
                * 'matching': a list of matched sentences. each match have the sentences details ('domain', 'comment_id', 'sentence_id', 'sents_in_comment', 'span_start', 'span_end', 'num_tokens', 'argument_quality', 'sentence_text') and a match score ('score') this is the match score between the sentence and the key point. The matchings are sorted descendingly according to their match score.
        :param top_k_kps: use this parameter to truncate the result json to have only the top K key points.
        :param top_k_sentences_per_kp: use this parameter to truncate the result json to have only the top K matched sentences per key point.
        :param dont_wait: when True, tries to get the result once and returns it if it's available, otherwise returns None.
        :param wait_secs: limit the waiting time (in seconds).
        :param polling_timout_secs: sets the time to wait before polling again (in seconds). The default is 60 seconds.
        :param high_verbosity: set to False to reduce the number of messages printed to the logger.
        :return: the key point analysis job result or throws an exception if an error occurs.
        '''
        start_time = time.time()

        do_again = True
        while do_again:
            result = self.client.get_kp_extraction_job_status(self.job_id, top_k_kps=top_k_kps, top_k_sentences_per_kp=top_k_sentences_per_kp)
            if result['status'] == 'PENDING':
                if high_verbosity:
                    logging.info('job_id %s is pending' % self.job_id)
            elif result['status'] == 'PROCESSING':
                if high_verbosity:
                    progress = result['progress']
                    logging.info('job_id %s is running, progress: %s' % (self.job_id, progress))
                    self._print_progress_bar(progress)
            elif result['status'] == 'DONE':
                logging.info('job_id %s is done, returning result' % self.job_id)
                return result['result']
            elif result['status'] == 'ERROR':
                error_msg = 'job_id %s has error, error_msg: %s' % (self.job_id, str(result['error_msg']))
                logging.error(error_msg)
                raise Exception(error_msg)
            elif result['status'] == 'CANCELED':
                logging.info('job_id %s was canceled!' % self.job_id)
                raise Exception('waiting for result on a job that was canceled')
            else:
                raise Exception('unsupported status: %s, result: %s' % (result['status'], str(result)))

            do_again = False if dont_wait else True if wait_secs is None else time.time() - start_time < wait_secs
            time.sleep(polling_timout_secs if polling_timout_secs is not None else self.polling_timout_secs)
        return None

    def cancel(self):
        '''
        Cancels (stops) the running job. Please stop unneeded jobs since they use a lot of resources.
        '''
        self.client.cancel_kp_extraction_job(self.job_id)

    def _print_progress_bar(self, progress):
        if 'total_stages' in progress:
            total_stages = progress['total_stages']
            for i in reversed(range(total_stages)):
                stage = str(i + 1)
                stage_i = 'stage_' + stage
                if stage_i in progress and 'inferred_batches' in progress[stage_i] and 'total_batches' in progress[stage_i]:
                    print_progress_bar(progress[stage_i]['inferred_batches'], progress[stage_i]['total_batches'], prefix='Stage %s/%s:' % (stage, str(total_stages)), suffix='Complete', length=50)
                    break
