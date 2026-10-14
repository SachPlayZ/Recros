"""Exact finite-world decision planning; guarantees are conditional on the model.

Established minimax-regret planning, not a calibrated claim about human taste.
See docs/milestone2/RESEARCH_BET.md for assumptions and attribution.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache


@dataclass(frozen=True)
class World:
    id: str
    utilities: tuple[F, ...]


@dataclass(frozen=True)
class Action:
    id: str
    kind: str
    cost: F
    # One truthful, deterministic observation for each world, in world order.
    observations: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    id: str
    items: tuple[str, ...]
    worlds: tuple[World, ...]
    actions: tuple[Action, ...]
    abstention_loss: F = F(9, 20)

    def __post_init__(self):
        if not self.items or len(set(self.items)) != len(self.items):
            raise ValueError('Items must be nonempty and unique')
        if not self.worlds or len({w.id for w in self.worlds}) != len(self.worlds):
            raise ValueError('Worlds must be nonempty and uniquely named')
        for w in self.worlds:
            if len(w.utilities) != len(self.items) or any(
                not isinstance(v, F) or not 0 <= v <= 1 for v in w.utilities
            ):
                raise ValueError('Utilities must be exact fractions in [0, 1]')
        if not isinstance(self.abstention_loss, F) or not 0 <= self.abstention_loss <= 1:
            raise ValueError('Abstention loss must be an exact fraction in [0, 1]')
        if len({a.id for a in self.actions}) != len(self.actions):
            raise ValueError('Action IDs must be unique')
        for a in self.actions:
            if a.kind not in ('ask_user', 'inspect_evidence'):
                raise ValueError('Unknown action kind')
            if not isinstance(a.cost, F) or a.cost < 0:
                raise ValueError('Costs must be nonnegative exact fractions')
            if len(a.observations) != len(self.worlds) or any(
                not isinstance(o, str) or not o for o in a.observations
            ):
                raise ValueError('Each world needs a nonempty observation')


def compatible_worlds(problem: Problem, active: tuple[int, ...],
                      action: Action, observation: str) -> tuple[int, ...]:
    remaining = tuple(i for i in active if action.observations[i] == observation)
    if not remaining:
        raise ValueError('Observation outside the hypothesis set; no certificate is valid')
    return remaining


def recommendation(problem: Problem, active: tuple[int, ...]) -> dict:
    """Return a deterministic minimax-regret item and an attaining witness."""
    if not active or any(i < 0 or i >= len(problem.worlds) for i in active):
        raise ValueError('A nonempty valid world set is required')
    candidates = []
    for j, item in enumerate(problem.items):
        gaps = [(max(problem.worlds[i].utilities) - problem.worlds[i].utilities[j], i)
                for i in active]
        gap, i = max(gaps, key=lambda pair: pair[0])
        w = problem.worlds[i]
        alternative = max(range(len(problem.items)), key=lambda k: w.utilities[k])
        candidates.append({
            'kind': 'recommend', 'item': item, 'loss': gap,
            'witness': {'world': w.id, 'alternative': problem.items[alternative],
                        'regret': gap},
        })
    return min(candidates, key=lambda candidate: (candidate['loss'], candidate['item']))


def plan(problem: Problem, horizon: int) -> dict:
    """Minimize worst-case terminal loss + action costs; stop is always allowed.

    The action tree is exact only for this finite deterministic model. Horizon
    counts information actions, not LLM reasoning tokens. No probability prior,
    preference inference, noisy observations or real evidence fetching is hidden
    in this function. Items are chosen deterministically, not as mixed policies.
    """
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 0:
        raise ValueError('Horizon must be a nonnegative integer')

    @lru_cache(None)
    def solve(active: tuple[int, ...], remaining: tuple[int, ...], depth: int) -> dict:
        best = recommendation(problem, active)
        if problem.abstention_loss < best['loss']:
            best = {'kind': 'abstain', 'loss': problem.abstention_loss,
                    'best_recommendation': best}
        if depth:
            for ai in remaining:
                action = problem.actions[ai]
                observations = sorted({action.observations[i] for i in active})
                if len(observations) == 1:
                    continue  # Reveals nothing; a nonnegative cost cannot help.
                children = {
                    o: solve(compatible_worlds(problem, active, action, o),
                             tuple(a for a in remaining if a != ai), depth - 1)
                    for o in observations
                }
                value = action.cost + max(c['loss'] for c in children.values())
                # Preserve stopping on ties; action-order breaks other exact ties.
                if value < best['loss']:
                    best = {'kind': action.kind, 'action': action.id,
                            'cost': action.cost, 'loss': value, 'branches': children}
        return {**best, 'worlds': [problem.worlds[i].id for i in active]}

    return solve(tuple(range(len(problem.worlds))), tuple(range(len(problem.actions))),
                 min(horizon, len(problem.actions)))


def replay(problem: Problem, decision: dict, world_index: int) -> dict:
    """Evaluate a plan against one declared fixture world, without sampling."""
    if not 0 <= world_index < len(problem.worlds):
        raise ValueError('Invalid world index')
    current, cost, trace = decision, F(0), []
    actions = {a.id: a for a in problem.actions}
    while current['kind'] in ('ask_user', 'inspect_evidence'):
        action = actions[current['action']]
        answer = action.observations[world_index]
        trace.append({'action': action.id, 'observation': answer})
        cost += action.cost
        current = current['branches'][answer]
    if current['kind'] == 'abstain':
        loss = problem.abstention_loss
    else:
        utilities = problem.worlds[world_index].utilities
        loss = max(utilities) - utilities[problem.items.index(current['item'])]
    return {'world': problem.worlds[world_index].id, 'trace': trace,
            'terminal': current['kind'], 'item': current.get('item'),
            'terminal_loss': loss, 'action_cost': cost, 'total_loss': loss + cost}


