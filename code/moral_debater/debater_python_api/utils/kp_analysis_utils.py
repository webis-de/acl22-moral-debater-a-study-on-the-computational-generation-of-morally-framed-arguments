import logging
import pandas as pd
import numpy as np

def print_kps_summary(result):
    keypoint_matchings = result['keypoint_matchings']
    for keypoint_matching in keypoint_matchings:
        kp = keypoint_matching['keypoint']
        num_args = len(keypoint_matching['matching'])
        logging.info(kp + ' - ' + str(num_args))


def print_report(report):
    print('comments status:')
    comments_statuses = report['comments_status']
    for domain in comments_statuses:
        print('domain: %s, status: %s ' % (domain, str(comments_statuses[domain])))

    print('')
    print('kp_analysis jobs status:')
    kp_analysis_statuses = report['kp_analysis_status']
    for kp_analysis_status in kp_analysis_statuses:
        print(str(kp_analysis_status))


def write_results_to_csv(results, result_file):
    if 'keypoint_matchings' not in results:
        print("No keypoint matchings results")
        return

    keypoint_matchings = results['keypoint_matchings']
    summary_list = []
    match_list = []
    total_args = 0
    kp_to_parent = {}
    for keypoint_matching in keypoint_matchings:
        kp = keypoint_matching['keypoint']
        num_args = len(keypoint_matching['matching'])
        total_args += num_args
        summary_list.append([kp, num_args])
        kp_to_parent[kp] = keypoint_matching.get("parent", None)
        for match in keypoint_matching['matching']:
            match_list.append([kp, match["sentence_text"], match["score"]])
    summary_df = pd.DataFrame(summary_list, columns=["kp", "#args"])
    summary_df.loc[:, "coverage"] = summary_df.apply(lambda x: x["#args"] / total_args, axis=1)

    if len(set(kp_to_parent.values())) > 1:
        summary_df.loc[:, "parent"] = summary_df.apply(lambda x: kp_to_parent[x["kp"]], axis=1)
        parent_to_kps = {p: list(filter(lambda x: kp_to_parent[x] == p, kp_to_parent.keys()))
                         for p in set(kp_to_parent.values())}
        parent_to_kps.update({p: [] for p in set(parent_to_kps["root"]).difference(parent_to_kps.keys())})
        kp_to_n_args = dict(summary_list)
        kp_to_n_args_sub = {kp: np.sum([kp_to_n_args[c_kp] for c_kp in set(parent_to_kps.get(kp, []) +[kp])])
                            for kp in kp_to_parent}
        kp_to_n_args_sub["root"] = np.sum(list(summary_df["#args"]))
        summary_df.loc[:, "n_args_in_subtree"] = summary_df.apply(lambda x: kp_to_n_args_sub[x["kp"]], axis=1)

        hierarchy_data = [[p, len(parent_to_kps[p]), kp_to_n_args_sub[p], parent_to_kps[p]] for p in parent_to_kps]
        hierarchy_df = pd.DataFrame(hierarchy_data, columns=["top_kp", "n_level_2_kps", "n_args_subtree", "level_2_kps"])
        hierarchy_df.sort_values(by=["n_args_subtree"], ascending=False)

        h_result_file = result_file.replace(".csv", "_hierarchy.csv")
        logging.info("Writing hierarchy results to: " + h_result_file)
        hierarchy_df.to_csv(h_result_file)

    match_df = pd.DataFrame(match_list, columns=["kp", "comment", "match"])

    summary_file = result_file.replace(".csv", "_summary.csv")
    logging.info("Writing results to: " + summary_file)
    summary_df.to_csv(summary_file, index=False)

    logging.info("Writing results to: " + result_file)
    match_df.to_csv(result_file, index=False)


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'{prefix} |{bar}| {percent}% {suffix}\n')
    # Print New Line on Complete
    if iteration == total:
        print()
