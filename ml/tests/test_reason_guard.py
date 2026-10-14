"""Synthetic fixtures only; none of these statements are participant data."""
from copy import deepcopy
from itertools import permutations

import pytest

from recros_api.reason_guard import assess, observations, text_hash


def inputs(source_domain='movie', target_domain='book'):
    text = 'Synthetic fixture: the story developed in an interesting way.'
    profile = {'items': [
        {'id':'source', 'title':'Source fixture', 'domain':source_domain,
         'identity_status':'matched', 'preference_label':'like'},
        {'id':'target', 'title':'Target fixture', 'domain':target_domain,
         'identity_status':'matched', 'preference_label':'dislike', 'description':'A friendship.'}],
        'reasons': {'fixture': text}}
    ledger = {'observations': [{'id':'development', 'item_id':'source', 'reason_key':'fixture',
        'quote':'developed in an interesting way', 'source_sha256':text_hash(text),
        'criterion':'interesting development', 'experience':'interesting for this fixture participant',
        'interpretation_status':'proposed', 'evidence_question':'Inspect development in the target.'}]}
    return profile, ledger


@pytest.mark.parametrize('source,target',list(permutations(('movie','book','music'),2)))
def test_all_directions_require_intent_then_target_evidence(source,target):
    p,l=inputs(source,target)
    r=assess(p,l,'development','target')
    assert r['cross_domain']
    assert r['next_action']=='ask_intent'
    r=assess(p,l,'development','target',intent_confirmed=True)
    assert r['next_action']=='inspect_target'
    assert r['target_experience']=='unknown'
    assert not r['recommendation_supported']


def test_target_like_dislike_cannot_fill_criterion_evidence_gap():
    p,l=inputs()
    before=assess(p,l,'development','target',True)
    p['items'][1]['preference_label']='immense love'
    p['items'][1]['reason']='Synthetic secret target answer'
    assert assess(p,l,'development','target',True)==before
    assert 'Synthetic secret target answer' not in str(before)


def test_editing_explanation_invalidates_proposed_meaning_even_when_quote_remains():
    p,l=inputs()
    assert len(observations(p,l)['observations'])==1
    p['reasons']['fixture']+=' Actually, this is not what I liked.'
    assert observations(p,l)['observations']==[]
    with pytest.raises(ValueError,match='stale'):
        assess(p,l,'development','target',True)


def test_ambiguous_referent_cannot_be_resolved_by_transfer_consent():
    p,l=inputs()
    l['observations'][0].update(interpretation_status='ambiguous',meaning_question='What do you mean?')
    assert assess(p,l,'development','target',True)['next_action']=='clarify_meaning'


def test_unresolved_identity_or_unsupported_quote_cannot_supply_observation():
    p,l=inputs()
    invalid=deepcopy(l)
    invalid['observations'][0]['quote']='Words the participant never said'
    assert observations(p,invalid)['observations']==[]
    p['items'][0]['identity_status']='pending'
    assert observations(p,l)['observations']==[]


def test_unknown_target_identity_is_first_obligation_and_source_is_not_a_test_target():
    p,l=inputs()
    p['items'][1]['identity_status']='pending'
    assert assess(p,l,'development','target',True)['next_action']=='resolve_identity'
    with pytest.raises(ValueError,match='different work'):
        assess(p,l,'development','source',True)
