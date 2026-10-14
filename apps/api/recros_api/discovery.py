"""Discovery with a per-list budget on *predicted* discounted utility loss.

The certificate is about the input scores, not ground-truth relevance or fairness.
At each position a candidate must leave a feasible best-score completion. The
greedy objective rewards novelty and avoids repeated facets; it is not optimal.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    key: str
    score: float
    novelty: float = 0.0  # [0, 1], measured within a domain
    facets: frozenset[str] = frozenset()


def discounted_utility(candidates: list[Candidate]) -> float:
    return sum(c.score / math.log2(rank + 2) for rank, c in enumerate(candidates))


def rerank(candidates: list[Candidate], k: int, budget: float = 0.05,
           novelty_weight: float = 0.25, diversity_weight: float = 0.15
           ) -> tuple[list[Candidate], dict[str, float]]:
    """Return unique candidates and a checkable utility certificate.

    Scores must be finite and nonnegative. The bound is invariant to positive
    rescaling but not to offsets, so callers must disclose score normalization.
    A zero budget returns the original order (including score ties).
    """
    if not 0 <= budget <= 1 or k < 0:
        raise ValueError("Require 0 <= budget <= 1 and k >= 0")
    if len({c.key for c in candidates}) != len(candidates):
        raise ValueError("Duplicate candidate IDs")
    if any(not math.isfinite(c.score) or c.score < 0 or
           not math.isfinite(c.novelty) or not 0 <= c.novelty <= 1 for c in candidates):
        raise ValueError("Scores must be finite/nonnegative and novelty in [0, 1]")
    remaining = sorted(candidates, key=lambda c: (-c.score, c.key))
    k = min(k, len(remaining))
    baseline = discounted_utility(remaining[:k])
    floor = (1 - budget) * baseline
    chosen: list[Candidate] = []
    utility = 0.0
    scale = remaining[0].score if remaining and remaining[0].score > 0 else 1.0
    if budget == 0:
        chosen = remaining[:k]
    else:
        for rank in range(k):
            best = None
            best_objective = -math.inf
            slots = k - rank - 1
            for candidate in remaining:
                gain = candidate.score / math.log2(rank + 2)
                completion = [c for c in remaining[:slots + 1] if c.key != candidate.key][:slots]
                upper = utility + gain + sum(c.score / math.log2(rank + j + 3)
                                            for j, c in enumerate(completion))
                if upper + 1e-12 < floor:
                    continue
                redundancy = max((len(candidate.facets & c.facets) / len(candidate.facets | c.facets)
                                  if candidate.facets | c.facets else 0.0 for c in chosen), default=0.0)
                objective = candidate.score / scale + novelty_weight * candidate.novelty - diversity_weight * redundancy
                if objective > best_objective:
                    best, best_objective = candidate, objective
            if best is None:
                raise RuntimeError("No feasible completion; utility invariant violated")
            chosen.append(best)
            utility += best.score / math.log2(rank + 2)
            remaining.remove(best)
    achieved = discounted_utility(chosen)
    return chosen, {"baseline_utility": baseline, "selected_utility": achieved,
                    "predicted_loss_fraction": max(0.0, 1 - achieved / baseline) if baseline else 0.0,
                    "budget": budget}
