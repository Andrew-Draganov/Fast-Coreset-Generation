from time import time
import numpy as np
from make_coreset import \
    fast_coreset, \
    sensitivity_coreset, \
    uniform_coreset, \
    evaluate_coreset, \
    semi_uniform_coreset, \
    lightweight_coreset, \
    bico_coreset

ALG_DICT = {
    'sens_sampling': sensitivity_coreset,
    'fast_coreset': fast_coreset,
    'uniform_sampling': uniform_coreset,
    'semi_uniform': semi_uniform_coreset,
    'lightweight': lightweight_coreset,
    'bico': bico_coreset
}

def get_algorithm(algorithm_type):
    return ALG_DICT[algorithm_type]

def get_results(
    points,
    coreset_alg,
    params,
):
    start = time()
    q_points, q_weights, _ = coreset_alg(
        points,
        k=params['k'],
        j_func=params['j_func'],
        m=params['m'],
        norm=params['norm'],
        hst_count_from_norm=params['hst_count_from_norm'],
        allotted_time=params['allotted_time'],
    )
    end = time()
    acc = evaluate_coreset(
        points,
        k=params['k'],
        coreset=q_points,
        weights=q_weights,
    )
    return acc, end - start, q_points, q_weights
