# Automatic discovery across all three domains

The product at `/explore` searches the full local catalogue and immediately shows
five movies, five books and five songs, including the starting domain. Optional
refinement follows the automatic lists. The separate bounded evidence experiment
has moved to `/evidence`; its four research criteria are not the product's total
vocabulary.

The current catalogue has 222,915 works: 45,437 movies, 6,821 books and 170,657
songs. Nineteen canonical sourced additions extend the earlier 222,896-record
catalogue. Seven explicitly verified current additions supply the Project Hail
Mary seed and six recent options; this is a small freshness supplement to
historical datasets, not comprehensive current-release coverage.

## Ranking and the May report

The PDF's page-10 weights are preserved: user–item 0.30, similar-users 0.20,
genre 0.15, novelty 0.10, diversity 0.10, fairness 0.10 and recency 0.05.
Unavailable signals are omitted and the remaining weights normalized. A missing
signal is not fabricated as positive evidence. Explanations expose the weights
actually used and each signal's availability.

The operational content signal combines summary/metadata TF-IDF and lexical
feature matches. Songs can additionally use measured acoustic similarity to
known liked tracks and a weak artist-affinity signal; metadata does not establish
lyrics, narrative themes or reasons for a person's preference. Movie audience
affinity uses 9,973,646 positive interactions from the actual 20,000,263 MovieLens
ratings. It is available only for historically rated movie seeds, not book/song
users or new movie seeds with zero interaction counts. The profile is a seed
affinity proxy, not a measured personal collaborative profile.

Candidate generation retains up to 200 content-related works per domain plus
eligible recent additions. Default selection reserves three regular connections,
one recent release within the last 365 days and one less-popular discovery per
domain. Regular movie/music slots use available source-support thresholds before
weighting; this is a practical support filter and may favor established works.
The dedicated recent slot admits verified new additions without interactions.
Creator repetition is limited when alternatives exist. Strict filters or a lack
of recent candidates can produce fewer picks or fallback discovery slots.

Known source titles, recorded known works, disliked works and seen works are
excluded. "Not in known history" means the system has no such record; it cannot
guarantee that a user has never encountered the work. Release date and version
identity are kept separate; a newer recording date does not establish a new song.

## Labels and intent

The UI offers unrestricted text, 37 optional theme/tone/style/audio/format
shortcuts and sourced genre/category filters with include/exclude and AND/OR.
Language, production country, setting mentions and period mentions are separate
facets. Setting/period extraction detects literal summary mentions and is not
verified semantic setting annotation. Positive hard filters require a known
matching label. Country of production never substitutes for story setting.

| Records with labels | Movies / 45,437 | Books / 6,821 | Songs / 170,657 |
|---|---:|---:|---:|
| Genre/category | 42,994 | 6,713 | 0 |
| Language | 45,433 | 0 | 0 |
| Production country | 39,151 | 0 | 0 |
| Literal setting mentions | 6,432 | 1,151 | 1 |
| Literal period mentions | 1,865 | 572 | 0 |

These counts appear in the app's label-coverage disclosure and
[index audit](CATALOG_DISCOVERY_AUDIT.json). A complete hierarchical genre taxonomy,
Novel Updates tag assignments and reliable facets on every record are **not
implemented**. The [hierarchical-facet study](HIERARCHICAL_FACETS_RESEARCH.md) is a
documented next experiment, not an achieved accuracy result.

## Which report problems this operationalizes

| Problem | Current mechanism | Remaining limitation |
|---|---|---|
| User/item/system cold start | One starting work; content fallback; dedicated recent slot | No guarantee of correct implicit intent or new-item relevance |
| Sparse interactions | Metadata and summaries; omit absent collaborative evidence | Missing labels and shared cross-domain users remain missing |
| Popularity bias | Within-domain novelty and a less-popular slot | Popularity measures and support filters differ by domain |
| Filter bubbles | List diversity, creator cap, discovery slots | No long-term diversity or user outcome study |
| Feedback loops | Local feedback plus exposure balancing | No causal longitudinal evaluation; impressions are not satisfaction |
| Explainability | Source excerpts, evidence scope and used signal weights | Lexical matches do not certify semantic interpretation |
| Domain isolation | All three domains returned, including same-domain works | No learned preference transfer from shared-user data |
| Exposure/fairness | Local item-serving exposure proxy | No demographic or provider fairness guarantee |

Product feedback/impressions are stored separately from frozen research sessions
and human reading judgments. Requests in `?preview=1` mode do not create guest
sessions, impressions or ratings. The tiny LM continues to run in `/evidence`;
it does not label or rank the entire product catalogue. Existing controlled
experiment scores are not measurements of this newly revised automatic product.
