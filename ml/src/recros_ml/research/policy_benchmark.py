"""Frozen, matched-observation policy comparison. Scripted preferences, not users.

PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.policy_benchmark
Add --run-model to use the existing Command Code subscription (max nine calls).
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from recros_api.deliberation import (
    METHODS, CONDITIONS, act, choose, new_state, public_view, scripted_cases,
)
from .commandcode import DEFAULT_MODEL, complete_json

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'docs' / 'milestone2' / 'results' / 'policy'
PROMPT = '''You are selecting the next action for independent, controlled recommendation tasks.
Use only each supplied public state. Do not use tools, browse, read files, or invent observations.
The possible_worlds table is the full declared model, not a probability distribution.
For a deterministic recommendation, terminal loss is its maximum regret over remaining worlds:
max_world(max_candidate utility - chosen_candidate utility). Abstaining costs abstention_loss.
Your objective is to minimize information-action costs plus worst-case terminal loss, over
the remaining information-action budget. You may plan ahead; recommend and abstain cost no
information action. Each information action can be used at most once. Stopping is always allowed.
ask_user obtains the actual preference from the environment; do not answer on the user's behalf.
inspect_evidence obtains the held-back cached item descriptions and source excerpts.
Every possible action observation is in the world table. A later state will contain the actual
observation. Never assume an unrevealed preference or candidate assignment. Different cases
have separate hidden states; do not transfer observations between them.
Return only JSON: {"decisions":[{"case_id":"ID", "kind":"ask_user|inspect_evidence|recommend|abstain", "item":"A|B"}]}.
Omit item unless recommending. Return exactly one decision for every supplied case_id.
Do not output answers, justifications, or intermediate reasoning.
TASKS:
'''


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def frozen_protocol():
    cases = scripted_cases()
    paths = ['apps/api/recros_api/decision.py', 'apps/api/recros_api/deliberation.py',
             'ml/src/recros_ml/research/policy_benchmark.py',
             'ml/src/recros_ml/research/commandcode.py', 'demo/catalog.real.deepseek.annotated.json']
    protocol = {
        'version': 1, 'seed': 20261014, 'cases': len(cases), 'batch_size': 8, 'max_model_calls': 9,
        'requested_model': DEFAULT_MODEL, 'prompt': PROMPT,
        'design': 'Six directed domain pairs × four known/unknown conditions; twelve reused curated works.',
        'preferences': 'Scripted theme choices. No participants, no held-out natural preference labels.',
        'primary_measure': 'Mean modeled worst-case terminal loss plus used action costs; report coverage too.',
        'costs': {'ask_user': .04, 'inspect_evidence': .02, 'abstain': .45},
        'baselines': list(METHODS) + ['deepseek'],
        'fairness': 'Same structured world table, action budget and observations. Candidate identities '
                    'masked until evidence access; actual preference supplied only when known or asked.',
        'failure_rule': 'No retry or substitute policy. Failed/invalid decisions reported separately, '
                        'excluded from completed-episode means; completion denominator always shown.',
        'limitations': ['Finite hypothesis set and binary utilities are supplied, not inferred from raw text.',
                       'Evidence action returns existing cached annotations; it is not a fresh model call.',
                       'Batched CLI latency is not per-recommendation latency.',
                       'Fixed small repeated cases support no population confidence intervals.',
                       'Model response is stochastic; cache reproduces this run only.',
                       'Local freeze before inference is not an externally preregistered study.'],
        'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        'case_sha256': digest(cases),
    }
    return protocol, cases


def initialize(cases, method):
    result = {}
    for index, (case, preference) in enumerate(cases):
        case_id = hashlib.sha256(f'recros-policy-v1-{index}'.encode()).hexdigest()[:10]
        known = case['condition'] in ('both_known', 'item_fact_unknown')
        result[case_id] = {'state': new_state(case, initial_preference=preference if known else None,
                                             method=method if method in METHODS else 'exact'),
                           'scripted_preference': preference, 'trace': [], 'error': None}
    return result


def parse_decisions(response, ids):
    rows = response.get('decisions') if isinstance(response, dict) else None
    if not isinstance(rows, list) or len(rows) != len(ids):
        raise ValueError('Expected exactly one decision per case')
    found = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) - {'case_id', 'kind', 'item'}:
            raise ValueError('Unexpected decision fields')
        cid, kind = row.get('case_id'), row.get('kind')
        if cid not in ids or cid in found:
            raise ValueError('Unknown or repeated case ID')
        if kind not in ('ask_user', 'inspect_evidence', 'recommend', 'abstain'):
            raise ValueError('Unknown action')
        if (kind == 'recommend' and row.get('item') not in ('A', 'B')) or (kind != 'recommend' and 'item' in row):
            raise ValueError('Only recommendations must specify A or B')
        found[cid] = row
    return found


def advance(episode, decision):
    before = public_view(episode['state'])
    kind = decision['kind']
    episode['trace'].append({'public_state': before, 'decision': decision})
    try:
        episode['state'] = act(episode['state'], kind,
                               answer=episode['scripted_preference'] if kind == 'ask_user' else None,
                               item=decision.get('item'))
    except ValueError as exc:
        episode['error'] = str(exc)


def measure(cid, episode):
    s, c = episode['state'], episode['state']['case']
    row = {'case_id': cid, 'source_domain': c['source']['domain'], 'target_domain': c['target'],
           'condition': c['condition'], 'source': c['source']['id'],
           'candidate_ids': [i['id'] for i in c['items']],
           'scripted_preference': episode['scripted_preference'],
           'trace': episode['trace'], 'error': episode['error']}
    counts = Counter(h['kind'] for h in s['history'])
    row.update(ask_count=counts['ask_user'], inspect_count=counts['inspect_evidence'])
    if episode['error'] or s['status'] == 'active':
        row['completed'] = False
        return row
    terminal = s['terminal']
    cost = counts['ask_user'] * .04 + counts['inspect_evidence'] * .02
    row.update(completed=True, terminal=terminal['kind'], action_cost=cost,
               worst_case_terminal_loss=terminal['loss'], total_modeled_loss=cost + terminal['loss'])
    if terminal['kind'] == 'recommend':
        selected = ('A', 'B').index(terminal['item'])
        match = c['themes'].index(episode['scripted_preference']) == (c['assignment'] if selected == 0 else 1-c['assignment'])
        row.update(selected=terminal['item'], scripted_theme_match=bool(match), actual_scripted_regret=int(not match))
    return row


def summarize(rows):
    complete = [r for r in rows if r['completed']]
    recommended = [r for r in complete if r['terminal'] == 'recommend']
    avg = lambda name: sum(r[name] for r in complete) / len(complete) if complete else None
    return {'scheduled': len(rows), 'completed': len(complete), 'failures': len(rows)-len(complete),
            'recommendations': len(recommended), 'coverage': len(recommended)/len(rows),
            'scripted_match_among_recommendations': sum(r['scripted_theme_match'] for r in recommended)/len(recommended) if recommended else None,
            'mean_modeled_loss': avg('total_modeled_loss'), 'mean_questions': avg('ask_count'),
            'mean_evidence_accesses': avg('inspect_count')}


def run_local(cases):
    rows = {}
    for method in METHODS:
        episodes = initialize(cases, method)
        start = time.perf_counter()
        for episode in episodes.values():
            for _ in range(3):
                if episode['state']['status'] != 'active' or episode['error']:
                    break
                choice = choose(episode['state'])
                advance(episode, {k: choice[k] for k in ('kind', 'item') if k in choice})
        rows[method] = {'episodes': [measure(cid, e) for cid, e in episodes.items()],
                        'local_total_seconds': time.perf_counter() - start}
    return rows


def run_model(cases, protocol_hash, out, allow_calls):
    episodes = initialize(cases, 'deepseek')
    batches, call_count = [], 0
    cache = out / 'model_calls'
    cache.mkdir(parents=True, exist_ok=True)
    for round_index in range(3):
        active = [(cid, e) for cid, e in episodes.items() if e['state']['status'] == 'active' and not e['error']]
        for offset in range(0, len(active), 8):
            batch = active[offset:offset+8]
            tasks = [{'case_id': cid, 'state': public_view(e['state'])} for cid, e in batch]
            prompt = PROMPT + canonical(tasks)
            key = digest({'protocol_hash': protocol_hash, 'prompt': prompt, 'model': DEFAULT_MODEL})
            path = cache / f'{key}.json'
            if path.exists():
                record = json.loads(path.read_text())
                if record['key'] != key or record['prompt'] != prompt or record['protocol_sha256'] != protocol_hash:
                    raise ValueError('Model cache does not match the frozen request')
            elif not allow_calls:
                return None
            else:
                if call_count >= 9:
                    raise RuntimeError('Nine-call limit reached')
                call_count += 1
                print(f'DeepSeek batch {call_count}: round {round_index+1}, {len(batch)} tasks', flush=True)
                record = {'key': key, 'protocol_sha256': protocol_hash, 'prompt': prompt,
                          'requested_model': DEFAULT_MODEL, 'requested_at': datetime.now(timezone.utc).isoformat()}
                start = time.perf_counter()
                try:
                    response, provenance = complete_json(prompt, model=DEFAULT_MODEL)
                    provenance.pop('session_id', None)
                    record.update(response=response, provenance=provenance, error=None)
                except Exception as exc:
                    record.update(response=None, error=f'{type(exc).__name__}: {exc}')
                record['wall_seconds'] = time.perf_counter()-start
                path.write_text(json.dumps(record, indent=2) + '\n')
            batches.append({k: record.get(k) for k in ('key', 'provenance', 'wall_seconds', 'error')})
            try:
                if record.get('error'):
                    raise ValueError(record['error'])
                choices = parse_decisions(record['response'], {cid for cid, _ in batch})
            except ValueError as exc:
                for _, e in batch:
                    e['error'] = str(exc)
                continue
            for cid, episode in batch:
                advance(episode, choices[cid])
    return {'episodes': [measure(cid, e) for cid, e in episodes.items()], 'batches': batches}


def write_report(results, out, protocol_hash):
    text = ['# Matched-observation policy comparison', '',
            '**Controlled mechanism experiment: 24 scripted tasks, 12 reused real works, zero participants.**', '',
            'Six movie/book/song directions × four information conditions. Utilities and costs are hypothetical; '
            'the full structured hypothesis table is supplied to every policy. This is not an end-to-end recommendation quality benchmark.', '',
            '| Policy | Completed | Recommendations | Scripted theme match among recommendations | Mean modeled loss ↓ | Questions | Evidence accesses |',
            '|---|---:|---:|---:|---:|---:|---:|']
    for method, data in results.items():
        s = data['summary']
        fmt = lambda v: '—' if v is None else f'{v:.3f}'
        text.append(f"| {method} | {s['completed']}/{s['scheduled']} | {s['recommendations']}/{s['scheduled']} | "
                    f"{fmt(s['scripted_match_among_recommendations'])} | {fmt(s['mean_modeled_loss'])} | "
                    f"{fmt(s['mean_questions'])} | {fmt(s['mean_evidence_accesses'])} |")
    text.extend(['', '## Condition breakdown', '',
                 '| Policy | Information condition | Completed | Recommendations | Mean modeled loss |',
                 '|---|---|---:|---:|---:|'])
    for method, data in results.items():
        for condition in CONDITIONS:
            s = data['conditions'][condition]
            loss = '—' if s['mean_modeled_loss'] is None else f"{s['mean_modeled_loss']:.3f}"
            text.append(f"| {method} | {condition} | {s['completed']}/{s['scheduled']} | {s['recommendations']} | {loss} |")
    text.extend(['', '## How to read this', '',
                 '- Mean modeled loss is action costs plus worst-case terminal regret within the supplied worlds; abstention costs 0.45.',
                 '- Match rate uses scripted theme choices, not human satisfaction. Always read it alongside coverage.',
                 '- Information gain is a strong cheap baseline. A tie means this suite does not establish an advantage for exact planning.',
                 '- Candidate identity masking and cached evidence access are controlled interventions, not a claim about realistic retrieval difficulty.',
                 '- Cases reuse items and share a hand-built structure. No significance test, population interval or novelty claim is justified.',
                 '- No SLM was trained or evaluated. DeepSeek is a hosted model accessed through the existing subscription.',
                 '- Failure counts are retained. Completed-episode means exclude failures; do not use those means alone to compare an incomplete policy.', '',
                 f'Frozen local protocol SHA-256: `{protocol_hash}`. See [protocol](protocol.json), '
                 '[full traces](results.json), and `model_calls/` for final outputs and usage. Prompts were fixed before inference, '
                 'not externally preregistered. Model calls batch up to eight cases; batch latency is not individual inference latency.', ''])
    (out / 'RESULTS.md').write_text('\n'.join(text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-model', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    protocol, cases = frozen_protocol()
    protocol_hash = digest(protocol)
    path = OUT / 'protocol.json'
    if path.exists() and digest(json.loads(path.read_text())) != protocol_hash:
        raise RuntimeError('Frozen protocol differs. Preserve the old run and choose a versioned output directory.')
    if not path.exists():
        path.write_text(json.dumps(protocol, indent=2) + '\n')
    results = run_local(cases)
    model = run_model(cases, protocol_hash, OUT, args.run_model)
    if model:
        results['deepseek'] = model
    for data in results.values():
        data['summary'] = summarize(data['episodes'])
        data['conditions'] = {c: summarize([r for r in data['episodes'] if r['condition'] == c]) for c in CONDITIONS}
    (OUT / 'results.json').write_text(json.dumps({'protocol_sha256': protocol_hash,
                                                'generated_at': datetime.now(timezone.utc).isoformat(),
                                                'policies': results}, indent=2) + '\n')
    write_report(results, OUT, protocol_hash)
    print(json.dumps({method: d['summary'] for method, d in results.items()}, indent=2))


if __name__ == '__main__':
    main()
