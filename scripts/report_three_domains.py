"""Compare preserved first-run domain experiments without tuning on test results."""
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/milestone2/hierarchy/domains'


def adjusted_bootstrap(values):
    """Descriptive Bonferroni 98.33% CI across three domain contrasts, 20k resamples."""
    x=np.asarray(values,dtype=float);rng=np.random.default_rng(20261014)
    estimates=np.concatenate([x[rng.integers(0,len(x),(1000,len(x)))].mean(axis=1) for _ in range(20)])
    alpha=.05/3
    return {'mean':float(x.mean()),'ci_bonferroni_98_33':np.quantile(estimates,[alpha/2,1-alpha/2]).tolist(),
            'profiles':len(x),'resamples':20000,'scope':'Supplemental descriptive correction across three domain contrasts; no models or primary outcomes changed.'}


def load(domain):
    folder=ROOT/'docs/milestone2/hierarchy/heldout' if domain=='movie' else BASE/domain
    return folder,json.loads((folder/'protocol.json').read_text()),json.loads((folder/'results.json').read_text())


def main():
    domains=['movie','book','music'];all_data={d:load(d) for d in domains};names={'movie':'Movies','book':'Books','music':'Songs'}
    corrections={};comparisons=[]
    for domain,(folder,p,r) in all_data.items():
        filename='test-per-user.json' if domain=='movie' else 'test-per-profile.json'
        rows=json.loads((folder/filename).read_text())
        selected=[row for row in rows if row['missing_fraction']==.5 and row['gamma']==.5]
        corrections[domain]={
            'hierarchy_minus_flat_ndcg':adjusted_bootstrap([row['metrics']['hierarchy_regret']['ndcg']-row['metrics']['flat_regret']['ndcg'] for row in selected]),
            'saved_annotation_lookups':adjusted_bootstrap([row['lookup']['flat_queries']-row['lookup']['hierarchy_queries'] for row in selected]),
        }
        s=r['fixed_nonzero_by_mask']['0.5'];q=s['lookup'];flat=q['flat_queries']['mean'];exact=q['hierarchy_queries']['mean']
        comparisons.append({'domain':domain,'test_profiles':s['users'],'flat_mean_lookups':flat,'hierarchy_mean_lookups':exact,
                            'relative_mean_reduction':1-exact/flat if flat else 0,'nominal_savings':q['paired_saved_queries'],
                            'profiles_saving':q['users_saving_queries'],'flat_certified':q['flat_certified'],'hierarchy_certified':q['hierarchy_certified'],
                            'hierarchy_ndcg':s['ranking']['hierarchy_regret']['ndcg']['mean'],'flat_ndcg':s['ranking']['flat_regret']['ndcg']['mean'],
                            'reference_ndcg':s['ranking']['hybrid']['ndcg']['mean'],'ease_ndcg_same_pool':s['ranking']['ease']['ndcg']['mean'],
                            'paired_ndcg':s['paired_ndcg_hierarchy_minus']['flat_regret']})
    combined={'created_utc':datetime.now(timezone.utc).isoformat(),'primary_condition':'50% artificially missing labels, fixed nonzero gamma=.5',
              'domains':comparisons,'adjusted_intervals':corrections,
              'interpretation':'Independent within-domain tests, not linked-user cross-domain transfer. Metadata acquisition remains conditional on the declared additive utility and annotation reference.',
              'ranking_policy':'Validation-selected gamma and fixed nonzero diagnostic kept separate. Per-item minimax-regret ordering is not a theorem of optimal five-item set relevance.'}
    (BASE/'comparison.json').write_text(json.dumps(combined,indent=2)+'\n')
    lines=['# Books and songs: held-out extension and three-domain comparison','',
           'October 14, 2026. All measurements below come from preserved first runs. The movie experiment was not retuned or overwritten.','',
           '## Finding','',
           'We now test the same uncertainty mechanism against real movie ratings, book ratings and recording-level song listening events. Metadata masking and label completion remain controlled simulations. These are independent datasets with independent users, not evidence of shared-user cross-domain preference transfer.','',
           '**No domain establishes a hierarchy ranking gain over propagated flat labels. All three validation runs select zero theme-reranking weight. Small mean annotation-bit savings appear in all three domains, with positive supplemental adjusted intervals, but benefit only a small minority of evaluated profiles.**','',
           'The acquisition ordering follows from the tighter conditional bound; the experiment measures its size and frequency. A hierarchy can rule out impossible annotation worlds while a learned matching utility still predicts enjoyment poorly.','',
           '## Primary acquisition comparison','',
           '50% missing metadata, fixed hybrid reference ranking, normalized first-pick regret threshold 0.20 and maximum 24 source-reference bit lookups. Both stopping rules see the same query sequence and sound propagation. The five recommendations remain exactly identical. Means include unsuccessful budget-limited runs.','',
           '| Domain | Test profiles | Flat mean lookups | Hierarchy mean lookups | Reduction | Saving, nominal 95% CI | Profiles benefiting | Certificates flat / hierarchy |',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in comparisons:
        v=row['nominal_savings'];lo,hi=v['ci95']
        lines.append(f"| {names[row['domain']]} | {row['test_profiles']} | {row['flat_mean_lookups']:.3f} | {row['hierarchy_mean_lookups']:.3f} | {row['relative_mean_reduction']:.1%} | {v['mean']:.3f} [{lo:.3f}, {hi:.3f}] | {row['profiles_saving']} | {row['flat_certified']} / {row['hierarchy_certified']} |")
    lines += ['', 'These are annotation-bit lookups, not measured LLM calls, human preference questions, tagging labor or API charges. Actual services may return several labels in one response. The certificate concerns the first pick among 16 retrieved candidates and assumes the declared preference intervals and ontology are adequate; it does not certify human enjoyment or the entire catalog.', '',
              'The lookup benchmark deliberately uses the nonzero gamma=.5 sensitivity model. When the selected ranking utility uses gamma=0, missing genre bits cannot affect that utility and no genre acquisition is needed for its ranking. The lookup saving therefore does not itself justify deploying the rejected nonzero model.', '',
              '## Real held-out relevance','',
              'Same 16-item candidate pools, NDCG@5 at gamma=.5 and 50% missing labels. EASE is an established additional comparator. Reference hybrid parameters and EASE regularization are selected on validation only. Scores from different datasets/splits are not directly comparable as measures of which entertainment domain is easier.','',
              '| Domain | Hybrid reference | EASE | Flat regret | Hierarchy regret | Hierarchy minus flat, nominal 95% CI |',
              '|---|---:|---:|---:|---:|---:|']
    for row in comparisons:
        v=row['paired_ndcg'];lo,hi=v['ci95']
        lines.append(f"| {names[row['domain']]} | {row['reference_ndcg']:.4f} | {row['ease_ndcg_same_pool']:.4f} | {row['flat_ndcg']:.4f} | {row['hierarchy_ndcg']:.4f} | {v['mean']:+.4f} [{lo:+.4f}, {hi:+.4f}] |")
    lines += ['', 'The historical movie and book validation studies selected zero theme weight. The song validation result is recorded independently below. Zero weight means that the paired deployment-policy family retains the reference list, rather than establishing a hierarchy accuracy gain. EASE is a separate comparator and is not automatically the reference retriever.','',
              '### Supplemental intervals across three domains','',
              'The original nominal intervals remain unchanged. The following supplemental bootstrap uses 20,000 profile resamples and Bonferroni-adjusted 98.33% intervals within each three-domain endpoint family. It is a descriptive correction, not a new parameter-selection procedure.','',
              '| Domain | Paired NDCG hierarchy minus flat | Adjusted interval | Mean saved lookups | Adjusted interval |',
              '|---|---:|---:|---:|---:|']
    for domain in domains:
        nd=corrections[domain]['hierarchy_minus_flat_ndcg'];sv=corrections[domain]['saved_annotation_lookups'];a,b=nd['ci_bonferroni_98_33'];c,d=sv['ci_bonferroni_98_33']
        lines.append(f"| {names[domain]} | {nd['mean']:+.4f} | [{a:+.4f}, {b:+.4f}] | {sv['mean']:.3f} | [{c:.3f}, {d:.3f}] |")
    lines += ['', '### 75% missing-label stress condition','',
              '| Domain | Flat / hierarchy mean lookups | Flat / hierarchy certified | Hierarchy minus hybrid NDCG, nominal 95% CI |',
              '|---|---:|---:|---:|']
    for domain,(_,p,r) in all_data.items():
        s=r['fixed_nonzero_by_mask']['0.75'];q=s['lookup'];v=s['paired_ndcg_hierarchy_minus']['hybrid'];lo,hi=v['ci95']
        lines.append(f"| {names[domain]} | {q['flat_queries']['mean']:.3f} / {q['hierarchy_queries']['mean']:.3f} | {q['flat_certified']} / {q['hierarchy_certified']} of {s['users']} | {v['mean']:+.4f} [{lo:+.4f}, {hi:+.4f}] |")
    lines += ['', 'High certification failure and negative relevance differences remain part of the result. Absence of a significant difference does not establish equivalence or noninferiority.','',
              '## Book dataset and split','']
    _,bp,br=all_data['book'];ba=bp['source_audit']
    lines += [f"- Source: Goodbooks-10k, **{ba['original_ratings']:,} real ratings and {ba['total_books']:,} books**. All six downloaded source files match their pinned GitHub commit blob hashes. Duplicate user/book pairs: {ba['duplicate_pairs_collapsed_by_mean']}.",
              f"- CPU-bounded catalog: **{ba['catalog_books']:,} books**, chosen by positive counts from disjoint background users, yielding **{ba['background_ratings']:,} background ratings**. This is not a reproduction of a full 10k benchmark score.",
              f"- **{len(bp['validation_users'])} validation and {len(bp['test_users'])} test profiles**. Background users have ID modulo5 in {{3,4}}, validation modulo5=0, test modulo5 in {{1,2}}. Numeric IDs are never joined to other domains.",
              '- Within each evaluated profile, 20 random ratings are supplied; remaining ratings are held out. No explicit timestamps exist, so this is a cross-sectional random split with no forward-prediction claim. Eligibility uses counts and known-history positivity, not future rating values.',
              f"- **{len(json.loads((BASE/'book/corpus.json').read_text())['features'])} facets and {len(json.loads((BASE/'book/corpus.json').read_text())['edges'])} implications**. Genre/subgenre mappings are project-declared and frozen before scoring. Source shelf assignments require at least five votes. Themes/tone, edition language and publication period are separate facets. Source data are not exhaustive semantic ground truth.",
              '- The content baseline uses author identifiers, not hidden genre labels. Aggregate average ratings and catalog-wide ratings counts never score popularity; only the disjoint background interaction matrix does.',
              '- Publication period is not story-setting era. Catalog edition language is not necessarily original language. Geographic setting is not inferred from author identity.',
              f"- Validation selects author/ItemKNN mixture alpha={br['chosen_alpha']} and theme gamma={br['chosen_gamma']}. EASE can outperform this mixture and is reported separately.",
              f"- Frozen protocol: `{br['protocol_sha256']}`.",'',
              '## Song dataset and split','']
    _,mp,mr=all_data['music'];ma=mp['source_audit']
    lines += [f"- Source log: **{ma['parsed_events']:,} actual song-play events** from Last.fm 1K. The decompressed original MD5 matches its published checksum. The AcousticBrainz genre archive also matches its published MD5.",
              f"- Genre source: **{ma['genre_source_recordings']:,} recordings**, with source-provided genre/subgenre paths. Joining **exact recording MusicBrainz IDs** yields **{ma['matched_events']:,} plays of {ma['matched_recordings']:,} recordings across {ma['source_users']} matched listeners**. No fuzzy title joins or artist-only proxy evaluation.",
              f"- CPU-bounded catalog: **{ma['catalog_recordings']:,} recordings**, selected by distinct background training listeners before validation/test. **{ma['catalog_events']:,} play events** belong to this selected catalog. This popular, annotated subset limits long-tail generalization.",
              f"- **{len(mp['validation_users'])} validation and {len(mp['test_users'])} test listeners** with disjoint background partitions. Global matched-event cutoffs: {datetime.fromtimestamp(ma['train_end'],timezone.utc).isoformat()} train and {datetime.fromtimestamp(ma['validation_end'],timezone.utc).isoformat()} validation. Test events occur later.",
              '- Repeat plays are aggregated only within each historical window. Profiles use the 20 most recent distinct previously played recordings. Signed genre coefficients learn centered log(1+past play count), not declared dislikes or invented enjoyment ratings.',
              '- A relevant test target is played after the cutoff and absent from the pre-cut logs. Previously played recordings are excluded. Unobserved recordings are treated as nonrelevant offline, not actual dislikes.',
              '- Internal adapter field `rating=4+log(1+plays)` lets existing binary-positive routines consume play events. It is not a star rating; centering removes the added constant for preference fitting.',
              f"- **{len(json.loads((BASE/'music/corpus.json').read_text())['features'])} genre facets and {len(json.loads((BASE/'music/corpus.json').read_text())['edges'])} source-provided implications**. Lastfm genres were inferred by the AcousticBrainz authors from collaborative recording tags. Retrospective annotations and missing subgenre negatives remain limitations.",
              '- The content baseline uses artist identifiers, not hidden genre labels. A song is identified and recommended by recording MBID, with title and artist retained as display metadata.',
              f"- Validation selects artist/ItemKNN mixture alpha={mr['chosen_alpha']} and theme gamma={mr['chosen_gamma']}.",
              f"- Frozen protocol: `{mr['protocol_sha256']}`.",'',
              '## Full-catalog baseline audit','',
              'Each baseline can rank every unseen item in its available catalog. Hierarchy is still tested as a 16-candidate decision layer. Consequently, the same-pool table cannot establish global superiority over these full-catalog baselines.','',
              '| Domain | Popularity | Metadata content | ItemKNN | Hybrid reference | EASE |',
              '|---|---:|---:|---:|---:|---:|']
    for domain,(folder,p,r) in all_data.items():
        full=json.loads((folder/'audit.json').read_text())['full_catalog_baselines'] if domain=='movie' else r['full_catalog_baselines']
        lines.append('| '+names[domain]+' | '+' | '.join(f"{full[name]['ndcg']['mean']:.4f}" for name in ['popularity','genre_content','itemknn','hybrid','ease'])+' |')
    lines += ['', '## Implementation, integrity and claim boundary','',
              '- `domain_holdout.py` prepares independent datasets, freezes corpus/windows/cohorts, selects parameters on validation, and refuses to overwrite completed scoring runs. The original movie protocols and predictions remain unchanged.',
              '- Genre tags and preference intervals are sensitivity-model inputs, not calibrated probabilities. Masking reveals both positive and unlisted-negative reference bits; actual annotation correctness and noisy extraction remain unmeasured.',
              '- Same-item gaps, shared preference cancellation, implication propagation, temporal isolation, source identity, future-count exclusion and constrained-ridge EASE equations have meaningful unit tests. The full API/ML suite has 116 passing tests.',
              '- Effective seeds: new-domain partition/profile sampling 271828; shared missing-label masks 314159 plus profile/condition offsets; original nominal bootstrap 42. Supplemental corrected intervals use 20261014. Only separate mask means are reported.',
              '- There is no linked-user evidence for movie-to-book, book-to-song or song-to-movie transfer. The three domains validate applicability of the decision mechanism independently.',
              '- The fixed five-item list stays unchanged in the acquisition experiment. Its conditional certificate concerns the first item; ranking by individual minimax-regret scores does not solve optimal five-item set recommendation.',
              '- Worldwide originality remains unverified. Hierarchical multi-label music genres are explicitly prior art in the AcousticBrainz source, not our invention. The candidate contribution is the specialized uncertainty formulation and structural-fault bound described in the existing derivation.',
              '- The label-proxy, limited-profile and popular-item subsets do not establish semantic intent understanding, causal satisfaction, universal cold-start performance, fairness, long-tail exposure or an SLM improvement.', '',
              '## Run commands','',
              '```bash',
              '# First download the public sources in a clean local environment.',
              '.venv-research/bin/python scripts/fetch_domain_holdout.py',
              'PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.domain_holdout prepare book',
              'PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.domain_holdout validate book',
              'PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.domain_holdout test book',
              '# Repeat prepare/validate/test with music. Completed runs refuse overwrite.',
              '.venv-research/bin/python scripts/report_three_domains.py',
              '```','',
              'Replication requires a clean separate checkout or saved output copy; preserve the existing frozen protocols and source windows. The source hashes, per-profile predictions, validation grid, query traces, full-catalog predictions and comparison report are saved. Runtime figures exclude fitting, source I/O and any real annotation service.', '',
              '## Primary sources and attribution','',
              '- [Goodbooks-10k, Zygmunt Zając](https://github.com/zygmuntz/goodbooks-10k)',
              '- [Last.fm 1K original README and permitted academic mirror](https://github.com/eifuentes/lastfm-dataset-1K)',
              '- [AcousticBrainz genre dataset, Bogdanov et al.](https://mtg.github.io/acousticbrainz-genre-dataset/data/)',
              '- [AcousticBrainz public label release](https://zenodo.org/records/2553414)',
              '- [EASE, Harald Steck](https://arxiv.org/abs/1905.03375)',
              '- [Original movie held-out result](../heldout/RESULT.md)',
              '- [Derivation and attribution](../DERIVATION.md)', '',
    ]
    (BASE/'RESULT.md').write_text('\n'.join(lines)+'\n')
    for domain in ['book','music']:
        (BASE/domain/'RESULT.md').write_text(f"# {names[domain]} held-out result\n\nSee the [complete three-domain comparison](../RESULT.md) for the measured results, split, sources and limitations.\n\nThis folder preserves this domain's frozen protocol, validation trials, per-profile predictions, query traces and full-catalog baseline outputs.\n")
    print(json.dumps({'report':str(BASE/'RESULT.md'),'domains':comparisons}),flush=True)


if __name__=='__main__':main()
