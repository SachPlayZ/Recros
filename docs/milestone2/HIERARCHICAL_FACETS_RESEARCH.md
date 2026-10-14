# Hierarchical labels and independent facets: prior-art check

Checked October 14, 2026. The question is whether films and books have actually
been annotated together, rather than whether hierarchical recommendation exists
in an unrelated domain. The earlier shopping-taxonomy and music-ontology examples
did not establish that specific claim.

## What the sources establish

| Primary source | Actual representation and domains | Boundary |
|---|---|---|
| [Literary Theme Ontology, Sheridan et al., 2019](https://arxiv.org/html/1905.00522v2) and [official project tutorial](https://github.com/theme-ontology/theming/wiki) | Hierarchical, defined themes; multiple themes per story. The current project explicitly includes films and novels. | The original paper's main annotated corpus is science-fiction film/TV. It does not evaluate our exact genre + geography + era + language recommendation scheme. |
| [LTO 2026.04 release](https://zenodo.org/records/19367236) | Downloaded the 3.6 MB author release and checked its published MD5. Explicit prefixes identify 1,768 unique film records (1,765 with theme sections) and 23 novels with theme sections, plus short stories and plays. | These are local parser counts, not independent judgments of tag correctness. Books are a small, imbalanced subset. Other IDs/chapters are excluded from these counts. |
| [Ontology-based fiction recommender, Sheridan et al., 2019](https://arxiv.org/abs/1808.00103) | Hierarchical literary-theme similarity used with Item-KNN in an item cold-start study. | Evaluation concerns Star Trek episodes; do not present it as an evaluated movie-to-book recommender. |
| [CATN, Zhao et al., SIGIR 2020](https://arxiv.org/html/2005.10549v2) | Extracts multiple latent aspects from reviews and learns cross-domain correlations. Section 4 evaluates Book→Movie, Movie→Music and Book→Music, using Amazon reviews and genuinely overlapping users. | Learned review aspects are not an explicit Novel Updates tag taxonomy or our proposed manual facets. Our independent datasets cannot be joined as if their user IDs overlap. |

A concrete shared-vocabulary example in the downloaded release is **The Time
Machine (1895 novel)** and **The Time Machine (1960 film)**. Both have `time
machine`, `time travel` and `the future of human evolution` themes. The film also
has `life in Victorian Britain`, `World War I` and `World War II`. Thus this
precedent extends beyond a single broad genre, including historical context.
See [the local audit](LTO_DATA_AUDIT.json) for source paths and checksums. A
novel/film adaptation pair is an illustrative annotation example, not evidence
of recommendation performance between unrelated works.

## Novel Updates: what was actually obtained

Before the initial answer, only the first [tag-list page](https://www.novelupdates.com/list-tags/)
had been inspected. It was incorrect to imply the complete vocabulary had already
been acquired. In this follow-up, normal browser pagination traversed 16 pages.
The local collection contains **722 unique tag names and source links from 15
pages**. Page 10 encountered a website access check and remains missing; it was
not bypassed. `apps/api/data/literary-theme-ontology/novelupdates-vocabulary-partial.json`
records the incomplete status explicitly. Definitions were not bulk republished.

The list includes plot devices, character traits, relationships, settings,
periods, adaptation metadata and content descriptors. These are candidate
vocabulary entries, not annotations of Recros's 222,915 records. They also
require domain-specific applicability: a novel plot trope need not describe a
song. The current app has not imported this vocabulary or assigned its tags to
all works. Downloading it does not establish permission to redistribute arbitrary
site prose. LTO's current release uses MIT for most content, with a CC BY-SA 4.0
exception for story descriptions; preserve attribution if integrating it.

## Proposed representation and experiment

Use a genre/subgenre hierarchy alongside independent facets for story location,
story period, language, production origin, tone, themes and narrative devices.
Each work can have several labels. Geography and language are not children of a
genre. Audience labels such as shounen/seinen and maturity descriptors belong in
their own facets. Publication date is not story era, and production country is
not story location. Preserve known, unsupported and unknown states with provenance.

The testable extension is whether **request-specific, domain-direction-specific
facet weights under incomplete labels** improve usefulness and constraints over
flat tags. Compare flat tags, hierarchy, and hierarchy with conditioned facets
using the same works, tag evidence, candidate pool and question budget. Evaluate
constraint satisfaction, usefulness, new-item coverage and abstention together;
report label coverage and annotation agreement separately. Avoid adaptation-pair
leakage and splits that put a work's different editions in both train and test.

This is a proposed experimental contribution. Hierarchical multi-label annotation
is established, aspect transfer is established, and this search does not prove
that the exact proposed extension is novel. A defensible claim requires a closer
comparison and measured improvement, rather than absence of an identical keyword
match. A subsequent [structural experiment](hierarchy/RESULT.md) now derives and
tests joint uncertainty under hierarchy implications and a bounded structural
fault allowance. It does not establish human usefulness, full catalogue tagging
or global novelty of the complete proposed system.
