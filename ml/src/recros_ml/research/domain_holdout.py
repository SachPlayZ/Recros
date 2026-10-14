"""Independent book-rating and recording-level listening tests of hierarchy regret.

Book splits are cross-sectional, not chronological. Music uses recording MBIDs,
timestamped plays, and source-provided AcousticBrainz genre/subgenre relations.
No unrelated user IDs are joined between domains. Original movie runs are intact.
"""
from __future__ import annotations

import argparse
import bz2
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import time

import networkx as nx
import numpy as np
import pandas as pd

from .hierarchy_experiment import ROOT, digest
from .hierarchy_holdout import (
    background, cases_for, evaluate_case, fit_ease, matrices,
    prepare_scores, ranking, sha, summary,
)
from .metrics import bootstrap_mean, ranking_metrics

RAW = ROOT/'ml/data/raw/domain-holdout'
BASE = ROOT/'docs/milestone2/hierarchy/domains'
CACHE = ROOT/'ml/data/processed/domain-holdout'
SEED = 271828

# Project-declared shelf normalization and genre taxonomy, frozen before scoring.
# Secondary themes, audience categories and language are separate facets.
BOOK_ALIASES = {
    'fiction':['fiction'], 'nonfiction':['non-fiction','nonfiction'],
    'speculative-fiction':['speculative-fiction'], 'fantasy':['fantasy'],
    'science-fiction':['science-fiction','sci-fi','scifi'],
    'urban-fantasy':['urban-fantasy'], 'high-fantasy':['high-fantasy','epic-fantasy'],
    'dark-fantasy':['dark-fantasy'], 'paranormal-fantasy':['paranormal','paranormal-fantasy'],
    'romance':['romance'], 'historical-romance':['historical-romance'],
    'contemporary-romance':['contemporary-romance'], 'paranormal-romance':['paranormal-romance'],
    'historical-fiction':['historical-fiction'], 'mystery':['mystery','mysteries'],
    'detective-fiction':['detective','detective-fiction'], 'cozy-mystery':['cozy-mystery','cozy-mysteries'],
    'thriller':['thriller','thrillers'], 'psychological-thriller':['psychological-thriller','psychological-thrillers'],
    'horror':['horror'], 'crime-fiction':['crime','crime-fiction'],
    'dystopian-fiction':['dystopia','dystopian'], 'space-opera':['space-opera'],
    'comics':['comics'], 'manga':['manga'], 'graphic-novels':['graphic-novels','graphic-novel'],
    'poetry':['poetry'], 'drama':['drama','plays'], 'short-stories':['short-stories'],
    'memoir':['memoir','memoirs'], 'autobiography':['autobiography','autobiographies'],
    'biography':['biography','biographies'], 'history':['history'],
    'science':['science'], 'psychology':['psychology'], 'philosophy':['philosophy'],
    'self-help':['self-help'], 'business':['business'], 'religion':['religion'],
    'young-adult':['young-adult','ya'], 'children':['children','childrens','children-s'],
    'middle-grade':['middle-grade'], 'picture-books':['picture-books'],
    'theme:magic':['magic'], 'theme:vampires':['vampires'], 'theme:witches':['witches'],
    'theme:time-travel':['time-travel'], 'theme:war':['war'], 'theme:family':['family'],
    'theme:friendship':['friendship'], 'theme:coming-of-age':['coming-of-age'],
    'theme:adventure':['adventure'], 'tone:humor':['humor','humour'],
    'tone:gothic':['gothic'], 'tone:dark':['dark'],
}
BOOK_EDGES = [
    ('fantasy','speculative-fiction'),('science-fiction','speculative-fiction'),
    ('speculative-fiction','fiction'),('urban-fantasy','fantasy'),('high-fantasy','fantasy'),
    ('dark-fantasy','fantasy'),('paranormal-fantasy','fantasy'),
    ('dystopian-fiction','speculative-fiction'),('space-opera','science-fiction'),
    ('romance','fiction'),('historical-fiction','fiction'),('mystery','fiction'),
    ('thriller','fiction'),('horror','fiction'),('crime-fiction','fiction'),
    ('historical-romance','romance'),('historical-romance','historical-fiction'),
    ('contemporary-romance','romance'),('paranormal-romance','romance'),
    ('detective-fiction','mystery'),('cozy-mystery','mystery'),
    ('psychological-thriller','thriller'),('manga','comics'),('graphic-novels','comics'),
    ('middle-grade','children'),('picture-books','children'),
    ('memoir','nonfiction'),('autobiography','biography'),('biography','nonfiction'),
    ('history','nonfiction'),('science','nonfiction'),('psychology','nonfiction'),
    ('philosophy','nonfiction'),('self-help','nonfiction'),('business','nonfiction'),
    ('religion','nonfiction'),
    ('published:before1900','published:before1950'),
    ('published:before1950','published:before2000'),
]


def closures_for(features, edges):
    graph=nx.DiGraph(); graph.add_nodes_from(features); graph.add_edges_from(edges)
    if not nx.is_directed_acyclic_graph(graph):raise ValueError('Taxonomy must be acyclic.')
    return {tag:sorted({tag}|nx.descendants(graph,tag)) for tag in graph.nodes}


def protocol_base(domain, corpus, input_audit, validation_users, test_users):
    return {
        'created_utc':datetime.now(timezone.utc).isoformat(),'domain':domain,'seed':SEED,
        'question':'Do hierarchy-aware regret decisions improve held-out relevance or reduce metadata acquisition for a fixed recommendation?',
        'corpus_sha256':digest(corpus),'source_audit':input_audit,
        'validation_users':validation_users,'test_users':test_users,
        'background_partition':'user_id % 5 in {3,4}; never include validation/test partition users',
        'validation_partition':'user_id % 5 == 0','test_partition':'user_id % 5 in {1,2}',
        'candidate_pool':16,'k':5,'alpha_grid':[0,.25,.5,.75,1],
        'ease_lambda_grid':[100,1000,10000], 'gamma_grid':[0,.25,.5,1],
        'fixed_nonzero_gamma':.5,'ridge_lambda':10,'profile_items':20,
        'weight_box':'Integer-normalized signed history regression coefficients +/-25%; fixed sensitivity assumption, not calibrated confidence intervals.',
        'facets':'Top 16 absolute learned coefficients and all ancestors; retain ancestor coefficients.',
        'missing_fractions':[.5,.75],'primary_missing_fraction':.5,
        'primary':'Paired test-profile NDCG@5 hierarchy-minus-propagated-flat at gamma=.5 and 50% masking.',
        'gamma_selection':'Validation NDCG averaged across coherent/propagated-flat at primary mask; common gamma; zero fallback allowed.',
        'retrieval':'Same 16 unseen candidates from validation-selected content/ItemKNN mixture, with popularity fallback; no held-out positives inserted.',
        'metadata_content':'Independent author identifiers for books and artist identifiers for songs. Baseline does not read hidden genre facets.',
        'labels':'Source positive tags plus declared ancestors=1; unlisted tags=0 only in the simulated closed-world reference. Observed facts propagated for both uncertainty methods.',
        'lookup':'Shared entropy/influence schedule; fixed historical first pick versus 15 challengers; gamma=.5, threshold .20, budget24, unchanged five-item list. Single-bit source-reference lookups, not human preference questions.',
        'statistics':'2000 paired profile bootstrap resamples; masks reported separately, not counted as independent users. One split per dataset.',
        'full_catalog_baselines':['popularity','genre_content','itemknn','hybrid','ease'],
        'no_cross_domain_user_alignment':True,
        'scope':'Two independent within-domain benchmark extensions. No evidence of shared-user movie/book/song transfer, prospective enjoyment, zero-history cold start, or SLM gain.',
    }


def save_prepared(domain, corpus, windows, audit, validation_users, test_users):
    out=BASE/domain;cache=CACHE/domain;out.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    if (out/'protocol.json').exists():raise RuntimeError('Protocol exists; do not overwrite it.')
    p=protocol_base(domain,corpus,audit,validation_users,test_users)
    p['windows']={}
    for name,frame in windows.items():
        path=cache/(name+'.parquet');frame.to_parquet(path,index=False)
        p['windows'][name]={'rows':len(frame),'sha256':sha(path)}
    p['implementation_sha256']=sha(Path(__file__))
    (out/'corpus.json').write_text(json.dumps(corpus,indent=2)+'\n')
    (out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
    print(json.dumps({'frozen':domain,'protocol_sha256':digest(p),'items':len(corpus['items']),
                      'features':len(corpus['features']),'edges':len(corpus['edges']),
                      'validation_profiles':len(validation_users),'test_profiles':len(test_users),
                      'windows':p['windows']}),flush=True)


def prepare_books():
    if (BASE/'book/protocol.json').exists():raise RuntimeError('Book protocol exists.')
    ratings=pd.read_csv(RAW/'goodbooks-ratings.csv').rename(columns={'user_id':'user','book_id':'source_item'})
    duplicates=int(ratings.duplicated(['user','source_item']).sum())
    ratings=ratings.groupby(['user','source_item'],as_index=False).rating.mean()
    bg=ratings[ratings.user%5>=3]
    counts=bg[bg.rating>=4].groupby('source_item').size()
    # Training-only popular-item subset bounds EASE memory/CPU on the free Mac.
    catalog=sorted(counts.index,key=lambda i:(-counts[i],int(i)))[:3000];catalog.sort()
    mapping={int(i):n for n,i in enumerate(catalog)}
    selected=ratings[ratings.source_item.isin(mapping)].copy();selected['item']=selected.source_item.map(mapping)
    metadata=pd.read_csv(RAW/'goodbooks-books.csv').set_index('book_id')
    tag_names=pd.read_csv(RAW/'goodbooks-tags.csv').set_index('tag_id').tag_name.to_dict()
    aliases={alias:canonical for canonical,values in BOOK_ALIASES.items() for alias in values}
    votes=pd.read_csv(RAW/'goodbooks-book_tags.csv')
    votes['canonical']=votes.tag_id.map(lambda j:aliases.get(tag_names.get(j)))
    votes=votes[(votes['count']>=5)&votes.canonical.notna()]
    direct={int(i):set(g.canonical) for i,g in votes.groupby('goodreads_book_id')}
    features=set(BOOK_ALIASES)|{'published:before1900','published:before1950','published:before2000'}
    languages={str(metadata.loc[i].language_code) for i in catalog if pd.notna(metadata.loc[i].language_code)}
    features|={'edition-language:'+language for language in languages}
    closures=closures_for(sorted(features),BOOK_EDGES);items=[]
    for source_item in catalog:
        meta=metadata.loc[source_item];tags=set(direct.get(int(meta.goodreads_book_id),set()))
        year=meta.original_publication_year
        for cutoff in [1900,1950,2000]:
            if pd.notna(year) and float(year)<cutoff:tags.add('published:before'+str(cutoff))
        if pd.notna(meta.language_code):tags.add('edition-language:'+str(meta.language_code))
        closure=set().union(*(set(closures[t]) for t in tags)) if tags else set()
        authors=['author:'+name.strip() for name in str(meta.authors).split(',') if name.strip()]
        items.append({'id':'goodbooks:'+str(source_item),'title':str(meta.title),'domain':'book',
                      'source_id':int(source_item),'tags':sorted(tags),'closure':sorted(closure),
                      'genres':authors,'goodreads_book_id':int(meta.goodreads_book_id),
                      'label_source':'Goodreads popular shelves, minimum five shelf assignments; language/publication year from catalog metadata'})
    corpus={'items':items,'features':sorted(features),'edges':BOOK_EDGES,'closures':closures}
    histories={};targets={};cohorts={}
    for partition,allowed,maximum in [('validation',{0},128),('test',{1,2},320)]:
        candidate_groups=[]
        for user,group in selected[selected.user.mod(5).isin(allowed)].groupby('user'):
            if len(group)<30:continue
            rng=np.random.default_rng(SEED+int(user));order=rng.permutation(len(group))
            past=group.iloc[order[:20]].copy();future=group.iloc[order[20:]].copy()
            if int((past.rating>=4).sum())<3:continue
            # Randomized split position is an internal sorting coordinate, not time.
            past['time']=np.arange(20);future['time']=np.arange(20,20+len(future))
            candidate_groups.append((int(user),past[['user','item','rating','time']],future[['user','item','rating','time']]))
        rng=np.random.default_rng(SEED+(0 if partition=='validation' else 1));rng.shuffle(candidate_groups)
        chosen=candidate_groups[:maximum];cohorts[partition]=sorted(row[0] for row in chosen)
        histories[partition]=pd.concat([row[1] for row in chosen],ignore_index=True)
        targets[partition]=pd.concat([row[2] for row in chosen],ignore_index=True)
    selected_bg=selected[selected.user.mod(5).isin({3,4})][['user','item','rating']].copy();selected_bg['time']=0
    windows={'background_validation':selected_bg,'background_test':selected_bg,
             'history_validation':histories['validation'],'target_validation':targets['validation'],
             'history_test':histories['test'],'target_test':targets['test']}
    audit={'dataset':'Goodbooks-10k','source':'https://github.com/zygmuntz/goodbooks-10k',
           'original_ratings':len(ratings),'duplicate_pairs_collapsed_by_mean':duplicates,
           'total_books':len(metadata),'catalog_books':len(items),'background_ratings':len(selected_bg),
           'shelf_threshold':5,'taxonomy':'Project-declared genre-subgenre map, separate theme/tone/edition-language/publication-period facets',
           'split':'Cross-sectional user-disjoint background/validation/test partitions; 20 random known ratings and remaining ratings as held-out outcomes. No timestamp/forward-prediction claim.',
           'relevance':'Held-out rating >=4; unobserved items nonrelevant offline. Catalog is top3000 by background positive counts, not the full standard 10k benchmark.',
           'label_limits':['Crowd shelves are noisy genre proxies, not independently verified exhaustive labels.',
                           'Edition language is not original language; publication period is not story setting era.',
                           'Catalog counts/average ratings are not used to score popularity; only background interactions are.'],
           'file_hashes':{f.name:sha(f) for f in RAW.glob('goodbooks-*')},'download_audit':json.loads((RAW/'download-audit.json').read_text())}
    save_prepared('book',corpus,windows,audit,cohorts['validation'],cohorts['test'])


class HashingReader(io.RawIOBase):
    """Hash uncompressed source bytes while pandas reads the listening log once."""
    def __init__(self,handle):self.handle=handle;self.md5=hashlib.md5();self.bytes=0
    def readable(self):return True
    def readinto(self,buffer):
        data=self.handle.read(len(buffer));self.md5.update(data);self.bytes+=len(data)
        buffer[:len(data)]=data;return len(data)


def load_song_labels(path):
    labels={};edges=set();features=set()
    with bz2.open(path,'rt',encoding='utf-8') as handle:
        next(handle)
        for line in handle:
            values=line.rstrip('\n').split('\t');mid=values[0].strip().lower()
            tags={value.strip() for value in values[2:] if value.strip()}
            if not tags:continue
            expanded=set(tags)
            for tag in tags:
                parts=tag.split('---')
                for n in range(1,len(parts)):
                    child='---'.join(parts[:n+1]);parent='---'.join(parts[:n])
                    expanded.update([child,parent]);edges.add((child,parent))
            features.update(expanded);labels.setdefault(mid,set()).update(expanded)
    return labels,sorted(edges),sorted(features)


def song_window(events,cutoff):
    # Aggregate repeated plays only inside this historical window.
    frame=events[events.time<=cutoff].groupby(['user','item'],as_index=False).agg(time=('time','max'),plays=('time','size'))
    frame['rating']=4+np.log1p(frame.plays)
    return frame[['user','item','rating','time','plays']]


def song_targets(events,start,end=None):
    part=events[events.time>start]
    if end is not None:part=part[part.time<=end]
    frame=part.groupby(['user','item'],as_index=False).agg(time=('time','min'),plays=('time','size'))
    frame['rating']=4+np.log1p(frame.plays)
    return frame[['user','item','rating','time','plays']]


def sample_song_users(history,future,available,partition,maximum):
    known={int(u):set(g.item) for u,g in history.groupby('user')}
    counts=history.groupby('user').size();allowed={0} if partition=='validation' else {1,2}
    users=[]
    for user,group in future.groupby('user'):
        if int(user)%5 not in allowed or counts.get(user,0)<20:continue
        new=set(group.item)&available-known.get(int(user),set())
        if len(new)>=5:users.append(int(user))
    rng=np.random.default_rng(SEED+(0 if partition=='validation' else 1));rng.shuffle(users)
    return sorted(users[:maximum])


def prepare_songs():
    if (BASE/'music/protocol.json').exists():raise RuntimeError('Music protocol exists.')
    labels,edges,features=load_song_labels(RAW/'acousticbrainz-lastfm-genres.tsv.bz2')
    mbids=sorted(labels);mapping={value:i for i,value in enumerate(mbids)};frames=[];names={};parsed=0
    with bz2.open(RAW/'lastfm-events.tsv.bz2','rb') as raw:
        reader=HashingReader(raw)
        handle=io.BufferedReader(reader)
        columns=['userid','timestamp','artist_mbid','artist_name','recording_mbid','track_name']
        for chunk in pd.read_csv(handle,sep='\t',names=columns,dtype=str,keep_default_na=False,
                                 quoting=3,on_bad_lines='skip',chunksize=500_000):
            parsed+=len(chunk);chunk.recording_mbid=chunk.recording_mbid.str.lower().str.strip()
            part=chunk[chunk.recording_mbid.isin(mapping)].copy()
            for mid,artist_id,artist_name,title in part[['recording_mbid','artist_mbid','artist_name','track_name']].itertuples(index=False,name=None):
                if mid not in names:names[mid]={'title':title,'artist_id':artist_id or 'name:'+artist_name.casefold(),'artist':artist_name}
            part['user']=part.userid.str.replace('user_','',regex=False).astype('int32')
            part['item']=part.recording_mbid.map(mapping).astype('int32')
            part['time']=pd.to_datetime(part.timestamp,utc=True,errors='raise').astype('int64')//10**9
            frames.append(part[['user','item','time']])
            print(json.dumps({'stage':'match_recording_ids','parsed_events':parsed,'matched_so_far':sum(len(f) for f in frames)}),flush=True)
        uncompressed_md5=reader.md5.hexdigest()
    if uncompressed_md5!='64747b21563e3d2aa95751e0ddc46b68':
        raise ValueError('Original Last.fm uncompressed checksum mismatch: '+uncompressed_md5)
    events=pd.concat(frames,ignore_index=True)
    train_end,val_end=np.quantile(events.time,[.6,.8]).astype(int)
    past=events[(events.time<=train_end)&events.user.mod(5).isin({3,4})]
    count=past[['user','item']].drop_duplicates().groupby('item').size()
    catalog=sorted(count.index,key=lambda i:(-count[i],int(i)))[:2000];catalog.sort()
    remap={int(value):n for n,value in enumerate(catalog)}
    selected=events[events.item.isin(remap)].copy();selected['item']=selected.item.map(remap).astype('int32')
    closures=closures_for(features,edges);items=[]
    for old_id in catalog:
        mid=mbids[int(old_id)];meta=names[mid]
        items.append({'id':'recording:'+mid,'title':meta['title'],'domain':'music','recording_mbid':mid,
                      'tags':sorted(labels[mid]),'closure':sorted(labels[mid]),'artist':meta['artist'],
                      'genres':['artist:'+meta['artist_id']],'label_source':'AcousticBrainz Lastfm recording-level genre/subgenre annotations'})
    corpus={'items':items,'features':features,'edges':edges,'closures':closures}
    histories={'validation':song_window(selected,train_end),'test':song_window(selected,val_end)}
    targets={'validation':song_targets(selected,train_end,val_end),'test':song_targets(selected,val_end)}
    bg={name:frame[frame.user.mod(5).isin({3,4})].copy() for name,frame in histories.items()}
    cohorts={}
    for partition,maximum in [('validation',128),('test',320)]:
        available=set(bg[partition].item)
        cohorts[partition]=sample_song_users(histories[partition],targets[partition],available,partition,maximum)
        if len(cohorts[partition])<40:raise ValueError('Too few eligible song profiles; preserve source audit and redesign separately.')
    windows={'background_validation':bg['validation'],'background_test':bg['test'],
             'history_validation':histories['validation'][histories['validation'].user.isin(cohorts['validation'])],
             'target_validation':targets['validation'][targets['validation'].user.isin(cohorts['validation'])],
             'history_test':histories['test'][histories['test'].user.isin(cohorts['test'])],
             'target_test':targets['test'][targets['test'].user.isin(cohorts['test'])]}
    audit={'dataset':'Last.fm 1K listening events + AcousticBrainz Lastfm genres',
           'sources':['https://github.com/jlieth/lastfm-dataset-1K-extended','https://mtg.github.io/acousticbrainz-genre-dataset/data/'],
           'parsed_events':parsed,'source_users':int(events.user.nunique()),'genre_source_recordings':len(labels),
           'matched_events':len(events),'matched_recordings':int(events.item.nunique()),'catalog_recordings':len(items),
           'catalog_events':len(selected),'original_uncompressed_md5_verified':uncompressed_md5,
           'match':'Exact recording MusicBrainz IDs only. No artist-level recommendation or fuzzy title matching.',
           'train_end':int(train_end),'validation_end':int(val_end),
           'catalog':'Top2000 recording IDs by distinct background training listeners, selected before validation/test; genre-annotated recording subset.',
           'relevance':'New recording played after cutoff and not previously played is relevant; counts are implicit feedback, not an enjoyment rating.',
           'profile':'Last20 distinct previously played recordings; centered log(1+pre-window plays) learns signed facet coefficients.',
           'internal_rating_field':'4+log(1+plays) is a numerical adapter making all observed plays positive in existing routines; it is NOT a star rating and is never presented as one.',
           'label_limits':['Source-provided recording-level crowd genre taxonomy was inferred by its authors, not verified by this project.',
                           'Genre labels are retrospective and unlisted subgenres are not exhaustive negatives.',
                           'Repeated listening and selective exposure do not establish enjoyment or dissatisfaction.'],
           'file_hashes':{f.name:sha(f) for f in [RAW/'lastfm-events.tsv.bz2',RAW/'acousticbrainz-lastfm-genres.tsv.bz2']},
           'genre_download_audit':json.loads((RAW/'acousticbrainz-download-audit.json').read_text())}
    save_prepared('music',corpus,windows,audit,cohorts['validation'],cohorts['test'])


def load_inputs(domain):
    out=BASE/domain;p=json.loads((out/'protocol.json').read_text());corpus=json.loads((out/'corpus.json').read_text())
    if digest(corpus)!=p['corpus_sha256']:raise ValueError('Corpus changed after freeze.')
    windows={}
    for name,spec in p['windows'].items():
        path=CACHE/domain/(name+'.parquet')
        if sha(path)!=spec['sha256']:raise ValueError('Frozen window changed: '+name)
        windows[name]=pd.read_parquet(path)
    return p,corpus,windows


def make_cases(p,corpus,windows,phase):
    x,metadata,index=matrices(corpus)
    bg=background(windows['background_'+phase],len(x),set())
    cases=cases_for(p[phase+'_users'],windows['history_'+phase],windows['target_'+phase],corpus,x,metadata,bg)
    return x,metadata,index,bg,cases


def validate(domain):
    out=BASE/domain
    if (out/'validation.json').exists():raise RuntimeError('Validation completed; preserve it.')
    p,corpus,windows=load_inputs(domain);x,metadata,index,bg,cases=make_cases(p,corpus,windows,'validation')
    alpha_trials=[]
    for alpha in p['alpha_grid']:
        values=[ranking_metrics(ranking(prepare_scores(c,alpha,bg)['hybrid'],c['available'],5),c['relevant'],5)['ndcg'] for c in cases]
        alpha_trials.append({'alpha':alpha,'ndcg':float(np.mean(values))})
    alpha=max(alpha_trials,key=lambda v:(v['ndcg'],-v['alpha']))['alpha'];ease_trials=[]
    for regularization in p['ease_lambda_grid']:
        bg['ease']=fit_ease(bg['gram'],regularization)
        values=[ranking_metrics(ranking(prepare_scores(c,alpha,bg)['ease'],c['available'],5),c['relevant'],5)['ndcg'] for c in cases]
        ease_trials.append({'lambda':regularization,'ndcg':float(np.mean(values))})
    chosen_lambda=max(ease_trials,key=lambda v:(v['ndcg'],-v['lambda']))['lambda'];bg['ease']=fit_ease(bg['gram'],chosen_lambda)
    rows=[]
    for n,case in enumerate(cases):
        rows.extend(evaluate_case(case,alpha,p['gamma_grid'],corpus,x,index,bg,[.5]))
        if (n+1)%16==0:print(json.dumps({'stage':'validation','domain':domain,'profiles':n+1,'total':len(cases)}),flush=True)
    trials=[]
    for gamma in p['gamma_grid']:
        subset=[r for r in rows if r['gamma']==gamma]
        means={name:float(np.mean([r['metrics'][name]['ndcg'] for r in subset])) for name in subset[0]['metrics']}
        trials.append({'gamma':gamma,'ndcg':means,'selection_mean':(means['flat_regret']+means['hierarchy_regret'])/2})
    gamma=max(trials,key=lambda v:(v['selection_mean'],-v['gamma']))['gamma']
    result={'protocol_sha256':digest(p),'chosen_alpha':alpha,'chosen_gamma':gamma,'chosen_ease_lambda':chosen_lambda,
            'alpha_trials':alpha_trials,'ease_trials':ease_trials,'gamma_trials':trials,'validation_profiles':len(cases),
            'selection':'Validation-only; common gamma and retrieval. Test outcomes not consulted.'}
    (out/'validation-per-profile.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


def run_test(domain):
    out=BASE/domain
    if (out/'results.json').exists():raise RuntimeError('Test complete; do not retune or overwrite.')
    started=time.perf_counter();p,corpus,windows=load_inputs(domain)
    selection=json.loads((out/'validation.json').read_text())
    if selection['protocol_sha256']!=digest(p):raise ValueError('Parameter selection does not match frozen protocol.')
    x,metadata,index,bg,cases=make_cases(p,corpus,windows,'test');bg['ease']=fit_ease(bg['gram'],selection['chosen_ease_lambda'])
    rows=[];full=[]
    gammas=sorted({p['fixed_nonzero_gamma'],selection['chosen_gamma']})
    for n,case in enumerate(cases):
        rows.extend(evaluate_case(case,selection['chosen_alpha'],gammas,corpus,x,index,bg,p['missing_fractions'],lookup=True))
        scores=prepare_scores(case,selection['chosen_alpha'],bg)
        tops={name:ranking(scores[name],case['available'],5) for name in p['full_catalog_baselines']}
        full.append({'user':case['user'],'metrics':{name:ranking_metrics(top,case['relevant'],5) for name,top in tops.items()},
                     'rankings':tops,'candidates':len(case['available']),'relevant_count':len(case['relevant'])})
        if (n+1)%16==0:print(json.dumps({'stage':'test','domain':domain,'profiles':n+1,'total':len(cases),'seconds':round(time.perf_counter()-started,1)}),flush=True)
    result={'domain':domain,'protocol_sha256':digest(p),'selection_sha256':digest(selection),
            'chosen_alpha':selection['chosen_alpha'],'chosen_gamma':selection['chosen_gamma'],'by_mask':{},'fixed_nonzero_by_mask':{},
            'full_catalog_baselines':{},'test_profiles':len(cases),'available_items':int(bg['available'].sum()),
            'candidate_range':[min(r['candidates'] for r in full),max(r['candidates'] for r in full)],
            'background_interactions':len(windows['background_test']),'seconds':time.perf_counter()-started,
            'environment':{'python':platform.python_version(),'numpy':np.__version__,'machine':platform.machine()},
            'scope':p['scope'],'integrity':{'input_hashes_verified':True,'identical_lookup_recommendations':True,'no_stop_order_failures':True}}
    for fraction in p['missing_fractions']:
        for target,gamma in [('by_mask',selection['chosen_gamma']),('fixed_nonzero_by_mask',p['fixed_nonzero_gamma'])]:
            subset=[r for r in rows if r['missing_fraction']==fraction and r['gamma']==gamma]
            for r in subset:
                assert r['lookup']['fixed_ranking']==r['rankings']['hybrid']
                assert r['lookup']['hierarchy_queries']<=r['lookup']['flat_queries']
            result[target][str(fraction)]=summary(subset,corpus,bg)
    for name in p['full_catalog_baselines']:
        result['full_catalog_baselines'][name]={metric:bootstrap_mean([r['metrics'][name][metric] for r in full]) for metric in ['ndcg','recall','precision','map']}
    result['no_history_strength_variation_profiles']=sum(float(np.ptp(c['profile']['weights']))<1e-10 for c in cases)
    (out/'test-per-profile.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'full-catalog-per-profile.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare','validate','test']);parser.add_argument('domain',choices=['book','music'])
    args=parser.parse_args()
    if args.command=='prepare':{'book':prepare_books,'music':prepare_songs}[args.domain]()
    elif args.command=='validate':validate(args.domain)
    else:run_test(args.domain)
