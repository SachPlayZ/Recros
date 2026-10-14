import math

import numpy as np
import pytest

from recros_api.discovery import Candidate, discounted_utility, rerank
from recros_ml.research.metrics import ranking_metrics


def test_ap_penalizes_missing_relevant_items():
    result = ranking_metrics([1, 5, 6], {1, 2, 3}, 3)
    assert result['map'] == pytest.approx(1 / 3)
    assert result['recall'] == pytest.approx(1 / 3)
    assert ranking_metrics([1, 2, 3], {1, 2, 3}, 3)['ndcg'] == 1


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError):
        ranking_metrics([1, 1], {1}, 2)
    with pytest.raises(ValueError):
        rerank([Candidate('a', 1), Candidate('a', 2)], 2)


def test_budget_invariant_randomized():
    rng = np.random.default_rng(19)
    for _ in range(80):
        candidates = [Candidate(str(i), float(rng.random()), float(rng.random()),
                                frozenset([str(i % 3)])) for i in range(20)]
        for budget in [0, .01, .05, .2, 1]:
            selected, certificate = rerank(candidates, 7, budget)
            assert len(selected) == len({c.key for c in selected}) == 7
            assert discounted_utility(selected) + 1e-10 >= (1 - budget) * certificate['baseline_utility']


def test_reranker_edge_cases():
    assert rerank([], 10)[0] == []
    assert len(rerank([Candidate('x', 0)], 20)[0]) == 1
    assert rerank([Candidate('x', 1)], 0)[0] == []
    for score in [-1, math.inf, math.nan]:
        with pytest.raises(ValueError):
            rerank([Candidate('x', score)], 1)


def test_zero_budget_and_score_rescaling():
    candidates = [Candidate('a', .9), Candidate('b', .89, 1), Candidate('c', .88, .8)]
    assert [c.key for c in rerank(candidates, 2, 0)[0]] == ['a', 'b']
    before = rerank(candidates, 2, .1)[0]
    after = rerank([Candidate(c.key, c.score * 10, c.novelty, c.facets) for c in candidates], 2, .1)[0]
    assert [c.key for c in before] == [c.key for c in after]
