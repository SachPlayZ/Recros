import json

import pytest

from recros_api.bridges import bridge_candidates, description_hash, validate_facets, verified_facets
from recros_ml.research.commandcode import parse_result
from recros_ml.evaluate import average_precision_at_k
from recros_ml.research.benchmark import split_global
import numpy as np
import pandas as pd


def test_legacy_ap_denominator_is_all_positives():
    assert average_precision_at_k(np.array([1, 0, 0, 1, 1]), 3) == pytest.approx(1 / 3)


def test_evidence_validation_and_stale_cache():
    description = 'A crew explores distant planets.'
    valid = {'concept': 'space exploration', 'quote': 'explores distant planets'}
    invented = {'concept': 'hope', 'quote': 'never loses hope'}
    accepted, rejected = validate_facets(description, [valid, invented])
    assert accepted == [valid] and len(rejected) == 1
    item = {'description': description, 'annotation': {'facets': [valid], 'description_sha256': description_hash(description)}}
    assert verified_facets(item) == [valid]
    item['description'] = 'A different description.'
    assert verified_facets(item) == []


def test_bridge_ablation_and_unknown_id():
    def item(key, domain):
        description = 'A crew explores distant planets.'
        return {'id': key, 'domain': domain, 'description': description,
                'annotation': {'description_sha256': description_hash(description),
                               'facets': [{'concept': 'space exploration', 'quote': description}]}}
    catalog = [item('a', 'movie'), item('b', 'book')]
    assert bridge_candidates(catalog, 'a', 'book')[0]['bridge_score'] == 1
    assert bridge_candidates(catalog, 'a', 'book', 'space exploration')[0]['bridge_score'] == 0
    with pytest.raises(ValueError):
        bridge_candidates(catalog, 'missing', 'book')


def test_cli_final_result_parsing():
    final = {'type': 'result', 'subtype': 'success', 'finalText': '{}'}
    assert parse_result('update banner\n{}\n' + json.dumps(final)) == final
    for response in ['', '{"type":"result","subtype":"error"}', '{"type":"event"}']:
        with pytest.raises(RuntimeError):
            parse_result(response)


def test_global_split_keeps_ties_on_one_side():
    ratings = pd.DataFrame({'time': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]})
    train, val, test, cutoff1, cutoff2 = split_global(ratings)
    assert train.time.max() < val.time.min()
    assert val.time.max() < test.time.min()
    assert len(train) + len(val) + len(test) == len(ratings)
