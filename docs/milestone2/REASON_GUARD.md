# From an explanation to a defensible transfer

Implemented October 14, 2026. Extension of the [representation audit](REPRESENTATION_AUDIT.md).

## The problem

A concept collision identifies a distinction that the representation loses. A user's
explanation can suggest a missing criterion, but three statements must stay separate:

1. **Observed experience:** this person found a particular work engaging or ineffective.
2. **Current intent:** this person wants that aspect considered for the next request.
3. **Target evidence:** appropriate information supports a claim about that aspect in the target.

A genre, shared creator, or theme cannot fill all three roles. A known target like/dislike
label cannot establish the reason for that label.

## Working implementation

The private audit page includes quotation-backed reason cards and a transfer rehearsal.
Six assistant-proposed observations are traced to the participant's actual text. The
participant clarified that “relatable” referred to the character; one interpretation
of “mess” remains ambiguous. The musical preference reason remains unknown. Their criterion names are not additional participant answers.
All ten work identities are resolved, including a corrected song identity. The incorrect
item's annotation was discarded; historical files were archived locally. One additional
DeepSeek call annotated only the corrected song's public description.

The [guard](../../apps/api/recros_api/reason_guard.py) checks the source work, exact quotation
and explanation hash. Editing an explanation invalidates its structured interpretation
until reviewed again. It returns outstanding obligations in this order:

| Condition | Next action |
|---|---|
| Target identity unresolved | Resolve the work |
| Interpretation ambiguous | Clarify the meaning |
| No intent supplied for this rehearsal | Ask whether this criterion matters here |
| No criterion-specific target evidence | Inspect appropriate evidence; abstain from the fit claim if unavailable |

`POST /api/personal-case/{token}/transfer-rehearsal` checks the profile revision and returns
a receipt. It does not save intent, record a rating, or train on the target label. All six
directed domain pairs have synthetic contract tests. Selecting a target is not consent to
reuse every source preference.

**Rehearsal boundary:** this endpoint detects missing evidence and leaves subjective
experience unknown. The separate `/explore` loop now retrieves a fixed text shortlist,
validates cached criterion excerpts and applies conditional minimax choice or abstention.
The participant explicitly chooses the current request criteria; the interface does not
silently turn a past like into a universal preference. The criteria are source-feature
proxies, not guarantees of engagement, scariness or relatability. See [the handoff](FINAL_HANDOFF.md).
No independently measured recommendation improvement is established.

The original 24-task decision experiment and frozen sources are unchanged. Its three
strongest methods still tie. Guard tests establish software behavior, not human preference
accuracy, semantic entailment, or novelty.

## Personal evidence so far

On ten development labels from one participant, the identical-vector diagnostic reports:

| Restricted representation | Minimum errors reproducing these labels |
|---|---:|
| Domain | 3 |
| Domain and available genres | 2 |
| Domain and cached concepts | 2 |
| Domain, genres and cached concepts | 1 |

These are counts on the same development examples, not measured classifier performance.
Genre metadata separates the observed film collision. The remaining song collision partly
reflects missing descriptions or an inadequate vocabulary. A separate same-creator witness
has opposite labels; it does not explain the musical reason for the difference. Private
titles, labels and verbatim reasons remain in the ignored case directory.

## The empirical test still required

Freeze proposed criteria and evidence rules before gathering new target judgments. Ask
whether the criterion matters for the requested domain; independently collect appropriate
target evidence and a specified outcome. Interest after reading and satisfaction after
consumption are different outcomes. Compare a strong content/model baseline with the same
inputs and question budget. Report usefulness alongside abstention, unsupported claims,
and questions asked.

New judgments must not have selected the criteria. With one participant this remains an
exploratory case study. Fit on these ten anchors is not unseen accuracy.

## Verification and local files

- `ml/tests/test_reason_guard.py`: six directions; target-label invariance; changed
  explanation, unsupported quote, unresolved identity and ambiguous meaning.
- `apps/api/tests/test_personal_case.py`: token/revision checks, no-write rehearsal,
  and separate item membership for cached annotation runs.
- `apps/api/data/personal-case/reason-observations.json`: private, manually curated
  proposed interpretations. This is not an automatic language extractor.
- `apps/api/data/personal-case/revisions/`: archived profile and evidence versions.

Run locally with `bash scripts/run_milestone2.sh`. The case token is in the ignored
`access-token.txt`; do not put its URL in a public report.
