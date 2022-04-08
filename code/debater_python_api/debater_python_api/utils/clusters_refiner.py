import math

# given a list of clusters, each cluster expressed as a list of ArgumentAndDistance sorted by increasing distance,
# and given p (expressed as a float 0..1)
# return the clusters expressed each as a pair of lists of arguments:
# those that are the top p close to the centroid of the cluster, and the rest of the arguments.

def separate_close_from_distant_arguments(clusters_of_arguments_with_distances, p):
    res = []
    for one_cluster in clusters_of_arguments_with_distances:
        num_of_close_arguments = int(math.ceil(p * len(one_cluster)))
        sorted_args_and_dists = sorted(one_cluster, key=lambda argAndDist: argAndDist[1])
        all_arguments_sorted_by_dists = [arg_and_dist[0] for arg_and_dist in sorted_args_and_dists]
        close_arguments = all_arguments_sorted_by_dists[:num_of_close_arguments]
        distant_arguments = all_arguments_sorted_by_dists[num_of_close_arguments:]
        res.append([close_arguments, distant_arguments])
    return res

