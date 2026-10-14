"""Evidence-linked semantic bridges; no online generative-model dependency.

Exact quotes establish provenance, not that the predicted concept is entailed.
The UI exposes the quoted evidence so a person can assess the model's judgment.
"""
from __future__ import annotations

import hashlib


CONCEPTS = ('space exploration', 'grief and loss', 'resistance to authority',
            'friendship', 'identity', 'mystery', 'nature', 'hope')


def description_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def validate_facets(description: str, facets: list[dict]) -> tuple[list[dict], list[dict]]:
    accepted, rejected, seen = [], [], set()
    for facet in facets:
        if not isinstance(facet, dict):
            rejected.append({'reason': 'facet is not an object'})
            continue
        concept, quote = facet.get('concept'), facet.get('quote')
        reason = None
        if concept not in CONCEPTS:
            reason = 'unknown concept'
        elif not isinstance(quote, str) or len(quote.strip()) < 8 or quote not in description:
            reason = 'evidence must be an exact nontrivial quote from the description'
        elif concept in seen:
            reason = 'duplicate concept'
        if reason:
            rejected.append({'facet': facet, 'reason': reason})
        else:
            accepted.append({'concept': concept, 'quote': quote})
            seen.add(concept)
    return accepted, rejected


def verified_facets(item: dict) -> list[dict]:
    annotation = item.get('annotation', {})
    if annotation.get('description_sha256') != description_hash(item.get('description', '')):
        return []
    return validate_facets(item['description'], annotation.get('facets', []))[0]


def bridge_candidates(catalog: list[dict], seed_id: str, target_domain: str,
                      removed_concept: str | None = None) -> list[dict]:
    seed = next((item for item in catalog if item['id'] == seed_id), None)
    if seed is None:
        raise ValueError('Unknown seed item')
    source = {f['concept']: f for f in verified_facets(seed) if f['concept'] != removed_concept}
    results = []
    for item in catalog:
        if item['domain'] != target_domain or item['id'] == seed_id:
            continue
        destination = {f['concept']: f for f in verified_facets(item)}
        shared = sorted(source.keys() & destination.keys())
        union = source.keys() | destination.keys()
        score = len(shared) / len(union) if union else 0.0
        results.append({**item, 'bridge_score': score,
                        'evidence': [{'concept': c, 'source_quote': source[c]['quote'],
                                      'target_quote': destination[c]['quote'],
                                      'score_without_concept': (len(shared) - 1) / len(union) if union else 0.0}
                                     for c in shared]})
    return sorted(results, key=lambda item: (-item['bridge_score'], item['id']))
