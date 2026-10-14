"""Synthetic source fixtures, not participant preferences."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import permutations

import pytest

from recros_api.transfer_engine import discover, select, text_hash, validate_evidence


def item(ident='a',domain='book',features=('inquiry',)):
    text='Synthetic fixture: researchers investigate a puzzle in an ominous setting.'
    return {'id':ident,'domain':domain,'title':ident,'source_url':'https://example.org/source',
            'evidence_text':text,'annotation':{'evidence_sha256':text_hash(text),
                'claims':[{'feature':f,'quote':text} for f in features]}}


def test_source_change_cannot_reuse_cached_claim_and_absence_stays_unknown():
    a=item(); b=item('b',features=())
    assert select({'items':[a,b]},'book',['inquiry'])['item_id']=='a'
    a['evidence_text']='Only author credits remain.'
    out=select({'items':[a,b]},'book',['inquiry'])
    assert out['kind']=='abstain'
    assert all(r['score_interval']==[0,1] for r in out['candidates'])


def test_quote_and_feature_injection_are_rejected():
    a=item(); a['annotation']['claims'][0]['quote']='Fabricated quotation.'
    assert not validate_evidence(a)[0]
    a=item(); a['annotation']['claims'][0]['feature']='guaranteed liking'
    assert not validate_evidence(a)[0]


def test_two_goals_need_both_supported_at_default_regret_bound():
    a=item(features=('inquiry',)); b=item('b',features=())
    out=select({'items':[a,b]},'book',['inquiry','unease'])
    assert out['kind']=='abstain'
    assert out['certificate']['modeled_regret']==.5
    assert out['candidates'][0]['score_interval']==[.5,1]
    a=item(features=('inquiry','unease'))
    out=select({'items':[a,b]},'book',['inquiry','unease'])
    assert out['kind']=='recommend' and out['certificate']['modeled_regret']==0


def test_single_candidate_without_evidence_is_not_trivially_certified():
    out=select({'items':[item(features=())]},'book',['inquiry'])
    assert out['kind']=='abstain' and out['item_id'] is None


def test_single_candidate_with_only_half_the_requested_evidence_still_abstains():
    out=select({'items':[item(features=('inquiry',))]},'book',['inquiry','unease'])
    assert out['kind']=='abstain'
    assert out['certificate']['modeled_regret']==0
    assert out['certificate']['minimum_source_support']==.75


def test_intent_and_inspection_precede_choice_without_exposing_hidden_text():
    c={'items':[item()]}
    assert select(c,'book',[])['kind']=='ask_user'
    out=select(c,'book',['inquiry'],inspected=False)
    assert out['kind']=='inspect_evidence'
    assert 'researchers investigate' not in str(out)
    assert not out['candidates'][0]['evidence']


def test_removal_can_switch_choice_and_cannot_change_original_cache():
    c={'items':[item('a'),item('b')]}; original=deepcopy(c)
    out=discover(c,'book',['inquiry'],removed={'item_id':'a','feature':'inquiry'})
    assert out['item_id']=='b'
    assert out['intervention']['before_item_id']=='a'
    assert out['intervention']['changed_choice']
    assert c==original


def test_target_labels_do_not_change_decision():
    c={'items':[item('a'),item('b',features=())]}
    before=select(c,'book',['inquiry'])
    c['items'][0]['preference_label']='dislike'
    c['items'][1]['preference_label']='immense love'
    assert select(c,'book',['inquiry'])==before


def test_explicit_exclusion_and_invalid_request():
    c={'items':[item('a'),item('b')]}
    assert select(c,'book',['inquiry'],excluded_ids=['a'])['item_id']=='b'
    with pytest.raises(ValueError): select(c,'book',['inquiry','inquiry'])
    with pytest.raises(ValueError): select(c,'book',['guaranteed enjoyment'])
    with pytest.raises(ValueError): select(c,'invalid',['inquiry'])
    with pytest.raises(ValueError): select(c,'book',['inquiry'],max_regret=F(-1))


@pytest.mark.parametrize('source,target',list(permutations(('movie','book','music'),2)))
def test_every_directed_pair_can_use_an_explicit_criterion(source,target):
    # Source domain affects context, not an invented preference translation.
    c={'items':[item('source',source),item('target',target)]}
    assert select(c,target,['inquiry'])['item_id']=='target'
