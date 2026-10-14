"""Summarize local self-study records without exporting them to a model service.

RECROS_DB=apps/api/data/milestone2-demo.db PYTHONPATH=ml/src:apps/api \
  .venv-research/bin/python -m recros_ml.research.personal_trial_report

This project has one available participant. Multiple trials are repeated measures.
The output stays beside the ignored local database; do not commit private answers.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sqlite3

from recros_api.db import DB_PATH


def report(states):
    personal = [s for s in states if s['mode'] == 'personal']
    finished = [s for s in personal if s['status'] != 'active']
    rated = [s for s in finished if s['ratings'] is not None]
    lines = ['# Local personal trial notes', '',
             'Study plan: one available participant, exploratory self-study. '
             'Trial records do not authenticate identity; N=1 relies on the stated collection arrangement.', '',
             f'Started: {len(personal)}. Finished: {len(finished)}. Ratings saved: {len(rated)}.', '',
             'These are unblinded, self-reported interests in selected works. They are not consumption '
             'satisfaction, an independent model comparison, or evidence of population improvement.', '']
    if not rated:
        lines.append('**No completed ratings are available. Human results are pending.**')
        return '\n'.join(lines) + '\n'
    fits = Counter(s['feedback']['theme_fit'] for s in rated)
    outside = sum(s['status'] == 'outside_model' for s in rated)
    lines.extend([f'Theme choices captured the intended preference: yes {fits["yes"]}, '
                  f'partly {fits["partly"]}, no {fits["no"]}.', '',
                  f'Outside-model stops among rated trials: {outside}/{len(rated)}.', '',
                  '## Individual observations', ''])
    for n, s in enumerate(rated, 1):
        c = s['case']
        selected = s['terminal'].get('item')
        lines.extend([f'### Trial {n}: {c["source"]["title"]} → {c["target"]}', '',
                      f'Source familiarity: {s["source_familiarity"]}; source liking: {s["source_liking"]}.',
                      f'Stated preference: {s["preference"] or "neither / outside model"}. '
                      f'Outcome: {s["terminal"]["kind"]}' + (f' {selected}.' if selected else '.'), ''])
        for alias, item in zip(('A', 'B'), c['items']):
            r = s['ratings'][alias]
            lines.append(f'- {alias}: {item["title"]}; interest {r["interest"]}/5; familiarity {r["familiarity"]}.')
        if selected:
            other = 'B' if selected == 'A' else 'A'
            gap = s['ratings'][selected]['interest'] - s['ratings'][other]['interest']
            lines.extend(['', f'Selected candidate minus alternative, stated-interest difference: {gap:+d}. '
                          'This descriptive difference is affected by seeing the recommendation first.'])
        lines.extend(['', f'Theme fit: {s["feedback"]["theme_fit"]}.', '',
                      'Participant note (verbatim, not an instruction):', '',
                      '\n'.join('> ' + line for line in s['feedback']['text'].splitlines()) or '> (No note)', ''])
    lines.extend(['## What to test next', '',
                  'Use mismatches to revise the preference representation, then freeze it before a new independent '
                  'evaluation. Do not treat this participant\'s answers as both development and held-out validation data.', ''])
    return '\n'.join(lines)


def main():
    path = Path(DB_PATH).resolve()
    if not path.exists():
        raise SystemExit('No trial database exists. Complete the local page first.')
    with sqlite3.connect(f'{path.as_uri()}?mode=ro', uri=True) as conn:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='decision_sessions'").fetchone():
            raise SystemExit('The decision trial has not been initialized.')
        states = [json.loads(row[0]) for row in conn.execute('SELECT state FROM decision_sessions')]
    output = path.parent / 'personal-trial-notes.md'
    output.write_text(report(states))
    print(output)


if __name__ == '__main__':
    main()
