"""Trace proposed experience criteria to user text before transferring them.

This is a provenance and evidence-obligation guard, not a preference predictor.
The criterion interpretation is analyst-authored; matching a quotation does not
confirm that interpretation. Target preference labels are never consulted.
"""
from __future__ import annotations

import hashlib


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def observations(profile: dict, ledger: dict) -> dict:
    items = {i['id']: i for i in profile['items']}
    valid, invalid = [], []
    seen = set()
    for row in ledger.get('observations', []):
        source = profile.get('reasons', {}).get(row.get('reason_key'), '')
        item = items.get(row.get('item_id'))
        problem = None
        if not row.get('id') or row['id'] in seen:
            problem = 'Missing or duplicate observation ID.'
        elif not item or item.get('identity_status') != 'matched':
            problem = 'Source work identity is unresolved.'
        elif not source or row.get('source_sha256') != text_hash(source):
            problem = 'The explanation changed; review the proposed interpretation again.'
        elif not row.get('quote') or row['quote'] not in source:
            problem = 'The supporting words are missing from the explanation.'
        elif row.get('interpretation_status') not in ('proposed', 'ambiguous'):
            problem = 'Unsupported interpretation status.'
        seen.add(row.get('id'))
        if problem:
            invalid.append({'id': row.get('id'), 'reason': problem})
        else:
            valid.append({**row, 'source_title': item['title'], 'source_domain': item['domain'],
                          'provenance_status': 'current exact quotation',
                          'scope': 'This participant’s reported experience of this work.'})
    return {'observations': valid, 'invalidated': invalid,
            'scope': 'Criterion names are proposed interpretations, not additional user answers. '
                     'A quotation check establishes provenance, not semantic correctness or transferability.'}


def assess(profile: dict, ledger: dict, observation_id: str, target_id: str,
           intent_confirmed: bool = False) -> dict:
    checked = observations(profile, ledger)
    source = next((r for r in checked['observations'] if r['id'] == observation_id), None)
    target = next((i for i in profile['items'] if i['id'] == target_id), None)
    if source is None:
        raise ValueError('The selected reason is missing or stale. Review the explanation first.')
    if target is None:
        raise ValueError('Unknown target work.')
    if target_id == source['item_id']:
        raise ValueError('Choose a different work for a transfer rehearsal.')

    blockers = []
    if target.get('identity_status') != 'matched':
        blockers.append({'action': 'resolve_identity', 'message': 'Resolve the target work before judging a transfer.'})
    if source['interpretation_status'] == 'ambiguous':
        blockers.append({'action': 'clarify_meaning', 'message': source['meaning_question']})
    if not intent_confirmed:
        blockers.append({'action': 'ask_intent', 'message':
                         f'Do you want “{source["criterion"]}” in this {target["domain"]} request? '
                         'Liking or disliking the source does not answer this.'})
    # No target-specific criterion evidence has been collected by this protocol.
    # Synopsis tags and the target's known like/dislike label cannot fill this gap.
    blockers.append({'action': 'inspect_target', 'message': source['evidence_question']})
    return {'observation_id': observation_id, 'target_id': target_id,
            'source': {'title': source['source_title'], 'quote': source['quote'],
                       'criterion': source['criterion'], 'reported_experience': source['experience']},
            'target': {'title': target['title'], 'domain': target['domain'],
                       'description': target.get('description', ''), 'source_url': target.get('source_url', '')},
            'cross_domain': source['source_domain'] != target['domain'],
            'intent_confirmed_for_this_rehearsal': intent_confirmed,
            'next_action': blockers[0]['action'], 'obligations': blockers,
            'recommendation_supported': False,
            'target_experience': 'unknown',
            'conclusion': 'The available item description does not establish how you would experience this criterion. '
                          'Inspect suitable evidence before making a fit claim; if it remains unavailable, abstain from that claim.',
            'scope': 'Development rehearsal on known works. Target labels are excluded from this check. '
                     'No preference prediction, satisfaction guarantee, or held-out evaluation.'}
