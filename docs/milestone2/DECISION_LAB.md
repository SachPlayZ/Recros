# Decision lab: what to demonstrate and what to evaluate

Open [the local trial](http://127.0.0.1:8008/decision). Restart it with `bash scripts/run_milestone2.sh` if needed.

## The working mechanism

The app can ask for a target-domain preference, retrieve cached item evidence, recommend, or abstain.
It constructs a tiny decision table containing possible preferences and possible candidate-theme assignments.
An exact finite planner selects an action tree under a budget of at most two information actions.

This table is hand specified. DeepSeek supplied the cached item facets, not the utility function or a
complete theory of the person's taste. Binary theme match is only a model of usefulness. Candidate
identities are deliberately masked until evidence access to make the information intervention explicit.

## A two-minute demonstration

1. In **Explore the mechanism**, start with *Manchester by the Sea*, target **Song**, both kinds of information missing, and a two-action budget.
2. Select **friendship** when asked. This permits moving away from the source's grief theme; the starting work does not dictate target taste.
3. Inspect the evidence. Read the cached, attributed passage supporting *You've Got a Friend*.
4. Make the recommendation and expand the decision model to show the possible-world table and the conditional regret certificate.
5. Repeat with an action budget of one. The exact planner stops because neither one action alone resolves this constructed ambiguity.
6. Restore a budget of two and answer **Neither / another reason**. The model is invalid for that response and stops without a valid certificate.

The source catalog contains 12 selected works. There are four theme labels and one item per theme
per domain. Each trial restricts the choice to two adjacent theme labels; this restriction is deliberate
and may frequently fail for actual users. All six movie/book/song directions are supported.

## The experiment already runnable

[Results](results/policy/RESULTS.md) compare six deterministic policies and, when its cache is present,
DeepSeek on 24 scripted tasks. This is a controlled policy test. Repeated items and hand-coded
preferences do not become 24 independent users.

Each policy sees the same structured possible-world table and has the same ask/inspect actions.
The answer and candidate assignment are not provided before their corresponding information action,
except in the protocol's explicitly known-information conditions. The DeepSeek prompt, final outputs,
usage and protocol hashes are retained. No personal-trial answers enter that experiment.

```bash
# Replay deterministic baselines and recorded model responses; no inference required.
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.policy_benchmark
```

`--run-model` allows missing requests to use the existing Command Code login. It does not retry
failed requests, substitute another model or purchase credits. Existing responses are reused.
The script rejects source or prompt changes against the frozen protocol; use a separately versioned
experiment for any substantive revision.

## Your personal case study

Only you are available today, so the collection is a **single-person exploratory case study**. It is
useful for finding bad hypotheses and confusing interactions. It cannot establish a general improvement.

**Pilot correction:** the first two completed trials revealed unfamiliar-work problems. Do not use
them as recommendation-accuracy evidence. Start with [familiar-work selection](http://127.0.0.1:8008/familiar)
or the private audit prepared from the participant's stated examples. See [the representation audit](REPRESENTATION_AUDIT.md).

- Use the controlled page's **Personal trial** mode only if its starting works and summaries permit meaningful judgments. Otherwise use familiar-work selection first; the 12-work page remains a mechanism demonstration.
- Record familiarity and liking honestly. A source you do not know can test the interface, but provides little evidence of personal transfer.
- Choose the direction you actually want. Use **Neither / another reason** when appropriate.
- After the decision, rate both candidates' interest and familiarity. Note what the theme model missed.
- Save ratings locally. Repeat a few times across domains, then export each trial if you want a portable copy.

These ratings are not blinded: you see the recommendation before rating. Candidate assignment is
randomized, but that does not eliminate anchoring, selection bias or carryover from repeated works.
There is no participant-level statistical comparison with a sample of one.

Records are saved in the ignored local SQLite database, separately marked `personal` or `demo`.
Automated API tests use an isolated temporary database. The agent's browser checks use demo mode.
No automated entries should be counted as human ratings.

Generate a local descriptive report after rating:

```bash
RECROS_DB=apps/api/data/milestone2-demo.db PYTHONPATH=ml/src:apps/api \
  .venv-research/bin/python -m recros_ml.research.personal_trial_report
```

The output is `apps/api/data/personal-trial-notes.md`, beside the ignored database. Until actual
ratings exist, it explicitly says human results are pending. Trial links contain an access token;
keep exports and the database local unless you deliberately choose to share them.

## Defensible presentation wording

“We built an interactive prototype that separates missing preferences from missing item evidence,
and tested the decision policies under matched observations and budgets. We can reproduce its decisions
and show when its assumptions fail. Our current controlled results do not establish improved human
recommendation quality or an advantage for an SLM.”

The next difficult research problem is constructing useful hypotheses from natural language and
detecting missing ones. Solving a four-world decision table is cheap; getting the table right is not.
