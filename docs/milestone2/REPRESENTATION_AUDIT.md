# Check the representation before trusting the planner

October 14, 2026. This extends the [decision experiment](results/policy/RESULTS.md).

## What the first personal trial changed

The only available participant completed two trials, then reported that the selected works were
unfamiliar and the study was not useful. These records remain local. They should not be presented
as evidence of cross-domain recommendation accuracy. In particular, a rating made after reading
a short unfamiliar-work description does not establish satisfaction with consuming that work.

The collection flow now supports searching the **222,896 recovered catalog records** at
`/familiar`, recording known works and explicitly entering missing titles. Some contemporary
works are outside the recovered catalog. Title identity must be resolved before evaluating a
preference; a similarly named old movie, a film adaptation and its book are not interchangeable.

The participant then supplied ten categorical preferences across movies, books and songs. These
are development inputs from one person. “Like,” “dislike” and “immense love” are preserved as
stated, without inventing numerical star ratings. Series-level feedback stays series-level.

## A concrete diagnostic

Suppose two works receive the same feature vector but opposite user labels. Any deterministic
binary classifier restricted to that vector must make the same prediction for both. It cannot
reproduce both labels, regardless of its size or how long it reasons.

For each identical-vector group g, with P(g) positive and N(g) negative labels, the minimum
possible number of errors on these observed labels is:

`sum_g min(P(g), N(g))`.

This is a counting identity, not a new theorem. It applies only to the declared input restriction,
not to a model also given titles, item IDs, richer text, acoustic features or extra user context.
It is a classification diagnostic on development examples, not a ranking bound or test-set accuracy.

[The audit implementation](../../apps/api/recros_api/contrast_audit.py) compares four representations:
domain alone, domain plus existing genres, domain plus verified model concepts, and their combination.
It emits the conflicting items as inspectable witnesses. Unconfirmed title matches are excluded.
Stale annotations or mismatched description versions cannot supply evidence.

The live familiar-work run found a pair of oppositely rated films that DeepSeek compressed to the
same concept representation. Existing genre metadata separates that pair. This establishes an
information-loss failure in the concept-only representation; it does not show a new algorithm beats
a competent baseline. The private audit page shows the exact works, labels, excerpts and alternatives.

Both pending song identities are now resolved; all ten preferences are included. The
domain/concept view has two unavoidable label errors; adding genres reduces the count
to one. A separate same-creator check finds opposite labels for two songs. These counts
describe the representation on development examples, not recommendation accuracy.

## Unknown features are not negative features

The recovered song records lack narrative descriptions. Official credits can establish identity,
performers and releases without establishing mood, narrative or why a particular person likes a song.
The annotator must return no supported concept when the available text does not support one.

If multiple untagged items collide, the diagnostic refers to the stored representation. It does
not establish that those songs are actually similar. The correct repair may be obtaining suitable
evidence, asking which musical property matters, or declining the proposed transfer.

The existing eight-concept vocabulary was retained for this diagnostic. We did not secretly change
it to fit the participant's labels. The hosted annotation calls received only public descriptions;
the personal labels and explanations remain in the ignored local case directory.

## The next empirical test

The [reason guard](REASON_GUARD.md) now preserves the supplied explanations, marks proposed
interpretations and ambiguity, and shows the missing intent/evidence for a transfer. It
is complemented by `/explore`, which retrieves source passages and makes a conditional
choice for explicitly selected criteria. Better personal recommendations have not been established.

Use the participant's explanation to propose an additional distinction, obtain item evidence for it,
and check whether the representation can express that distinction. Then freeze the new representation
and evaluate on independently obtained judgments. Splitting or memorizing the current examples is
not a generalization result.

The exact planner remains useful for choosing among specified information actions. This audit
addresses a prerequisite: whether its input can represent a preference distinction already observed.
It cannot certify that the hypothesis set is complete or that future preferences will be consistent.

## Implementation and privacy

- `/familiar`: local title search with manual entry for missing works.
- `/personal-case/{token}`: private local evidence audit and editable user-authored reasons.
- `scripts/build_familiar_catalog.py`: rebuilds the local search index from the recovered parquet and book CSV, without downloading anything.
- `apps/api/data/personal-case/`: ignored local preference records, item-only annotation input/output, and versioned clarification history.
- The frozen 24-task policy experiment is unchanged; its prompts and traces remain reproducible.

This diagnostic did not use model training or new target judgments. Subsequent work
trained a tiny local language model and completed a separate one-person supplied-text
review. Neither establishes preference improvement. No additional paid service or
pretrained model download was used.
