# Exact decision probe

**Constructed examples only. No real-user accuracy or novelty claim.**

Loss = worst-case recommendation regret (or specified abstention loss) + information-action costs. Values are hypothetical normalized units.

| Fixture | 0 actions: decision / loss | ≤1 action: decision / loss | ≤2 actions: decision / loss |
|---|---|---|---|
| both_known | recommend / 0.00 | recommend / 0.00 | recommend / 0.00 |
| preference_unknown | abstain / 0.45 | ask_user / 0.04 | ask_user / 0.04 |
| item_fact_unknown | abstain / 0.45 | inspect_evidence / 0.02 | inspect_evidence / 0.02 |
| both_unknown | abstain / 0.45 | abstain / 0.45 | ask_user / 0.06 |
| uncertain_but_ranking_stable | recommend / 0.00 | recommend / 0.00 | recommend / 0.00 |
| item_evidence_unavailable | abstain / 0.45 | abstain / 0.45 | abstain / 0.45 |
| information_too_costly | abstain / 0.45 | abstain / 0.45 | abstain / 0.45 |

The joint-uncertainty fixture is constructed so that either observation alone leaves the two opposing item rankings possible. Two observations identify the best item. This illustrates complementary information and a limitation of one-step planning; it is not a newly discovered theorem.

Every branch was replayed against every compatible fixture world. The reported worst-case losses match those exhaustive replays. The guarantee does not apply if a real preference or evidence state was omitted.

Run: `PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.decision_probe`
