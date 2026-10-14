"""Exact, finite-world research probe; NOT an evaluated recommender.

Implements established minimax-regret planning, with separate user-question and
item-evidence actions. All fixtures, utilities, costs and truthful observations
are constructed. A certificate is conditional on the supplied world set, NOT a
guarantee about a human. See docs/milestone2/RESEARCH_BET.md for prior art.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path


from recros_api.decision import Action, Problem, World, compatible_worlds, plan, recommendation, replay


def fixtures() -> tuple[Problem, ...]:
    # p = desired theme; f = which of two items has that theme. These are
    # hypothetical binary attributes, not measured moods of real songs.
    def make(name, combinations):
        worlds = tuple(World(f'preference={p};item_assignment={f}',
                             (F(int(p == f)), F(int(p != f)), F(1, 2)))
                       for p, f in combinations)
        return Problem(name, ('item_A', 'item_B', 'neutral_item'), worlds, (
            Action('ask_preference', 'ask_user', F(1, 25),
                   tuple(f'prefer_theme_{p}' for p, _ in combinations)),
            Action('inspect_item_fact', 'inspect_evidence', F(1, 50),
                   tuple(f'assignment_{f}' for _, f in combinations)),
        ))

    both = make('both_unknown', ((0, 0), (0, 1), (1, 0), (1, 1)))
    preference = make('preference_unknown', ((0, 0), (1, 0)))
    evidence = make('item_fact_unknown', ((0, 0), (0, 1)))
    known = make('both_known', ((0, 0),))
    stable = replace(both, id='uncertain_but_ranking_stable',
                     worlds=tuple(replace(w, utilities=(F(1), F(3, 4), F(1, 2)))
                                  for w in both.worlds))
    unavailable = replace(both, id='item_evidence_unavailable', actions=(
        both.actions[0], replace(both.actions[1], observations=('unavailable',) * 4)))
    costly = replace(both, id='information_too_costly',
                     actions=tuple(replace(a, cost=F(3, 10)) for a in both.actions))
    return known, preference, evidence, both, stable, unavailable, costly


def serialize(value):
    if isinstance(value, F):
        return float(value)
    raise TypeError(type(value).__name__)


def run(out: Path):
    rows = []
    for problem in fixtures():
        decisions = {str(h): plan(problem, h) for h in range(3)}
        replays = {h: [replay(problem, p, i) for i in range(len(problem.worlds))]
                   for h, p in decisions.items()}
        for h, p in decisions.items():
            assert max(r['total_loss'] for r in replays[h]) == p['loss']
        rows.append({'case': problem.id, 'world_count': len(problem.worlds),
                     'plans': decisions, 'exhaustive_replays': replays})
    result = {'evidence_level': 'Constructed mechanism probe, NOT user evaluation',
              'assumptions': ['Complete finite world set', 'Truthful deterministic observations',
                              'Exact specified utilities', 'Deterministic item recommendations',
                              'Normalized hypothetical costs, NOT money or time'],
              'abstention_loss': float(F(9, 20)), 'cases': rows}
    out.mkdir(parents=True, exist_ok=True)
    (out / 'decision_probe.json').write_text(json.dumps(result, indent=2, default=serialize) + '\n')
    lines = ['# Exact decision probe', '',
             '**Constructed examples only. No real-user accuracy or novelty claim.**', '',
             'Loss = worst-case recommendation regret (or specified abstention loss) '
             '+ information-action costs. Values are hypothetical normalized units.', '',
             '| Fixture | 0 actions: decision / loss | ≤1 action: decision / loss '
             '| ≤2 actions: decision / loss |', '|---|---|---|---|']
    for row in rows:
        cells = [f"{row['plans'][str(h)]['kind']} / {float(row['plans'][str(h)]['loss']):.2f}"
                 for h in range(3)]
        lines.append('| ' + ' | '.join([row['case'], *cells]) + ' |')
    lines += ['', 'The joint-uncertainty fixture is constructed so that either observation '
              'alone leaves the two opposing item rankings possible. Two observations '
              'identify the best item. This illustrates complementary information and '
              'a limitation of one-step planning; it is not a newly discovered theorem.', '',
              'Every branch was replayed against every compatible fixture world. The '
              'reported worst-case losses match those exhaustive replays. The guarantee '
              'does not apply if a real preference or evidence state was omitted.', '',
              'Run: `PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m '
              'recros_ml.research.decision_probe`', '']
    (out / 'DECISION_PROBE.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('docs/milestone2/results'))
    run(parser.parse_args().out)
