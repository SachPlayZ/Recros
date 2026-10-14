"""Full-catalog content ranking using the report's seven-signal weighting.

Production heuristic, separate from frozen research comparisons. No satisfaction
certificate. Missing collaborative data are excluded, never fabricated.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
from functools import lru_cache
from pathlib import Path
import math,re,json
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
ARTIFACT=ROOT/'apps/api/data/catalog-discovery/index.joblib'
WEIGHTS={'user_item':.30,'similar_users':.20,'genre':.15,'novelty':.10,'diversity':.10,'fairness':.10,'recency':.05}
# Expandable shortcuts, not an exhaustive taxonomy. Free text has no category restriction.
CRITERIA=[
 ('space','Space and exploration','Themes','space astronaut galaxy planetary cosmic interstellar'),
 ('science','Science and technology','Themes','science scientist scientific engineering invention technology'),
 ('survival','Survival and resilience','Themes','survival stranded rescue survive resilience'),
 ('mystery','Mysteries and puzzles','Themes','mystery investigation detective puzzle secrets clues'),
 ('fantasy','Fantasy and mythology','Themes','fantasy magic myth mythology gods wizard dragon'),
 ('adventure','Adventure and journeys','Themes','adventure journey quest expedition voyage'),
 ('friendship','Friendship and found family','Themes','friendship friend companion cooperation ally connection belonging'),
 ('family','Family relationships','Themes','family parents children sibling father mother'),
 ('romance','Romance and intimacy','Themes','romance romantic lovers love relationship'),
 ('grief','Grief and loss','Themes','grief bereavement mourning loss death'),
 ('identity','Identity and self-discovery','Themes','identity self discovery memories consciousness reflection'),
 ('rebellion','Rebellion and power','Themes','rebellion resistance revolution authority power oppression'),
 ('history','History and real lives','Themes','history historical biography memoir war'),
 ('nature','Nature and animals','Themes','nature wildlife wilderness animal forest ocean'),
 ('crime','Crime and justice','Themes','crime criminal justice murder prison trial'),
 ('horror','Horror and the supernatural','Themes','horror haunted supernatural ghost terrifying demon'),
 ('humor','Humor and wit','Tone','humor humour comedy funny hilarious witty'),
 ('hope','Hopeful and uplifting','Tone','hope hopeful optimism uplifting inspiring'),
 ('dark','Dark and unsettling','Tone','dark unsettling ominous threatening sinister eerie'),
 ('reflective','Reflective and intimate','Tone','reflective introspective intimate contemplative memory'),
 ('heartbreak','Melancholy and heartbreak','Tone','melancholy heartbreak sorrow sadness mournful'),
 ('suspense','Suspense and tension','Tone','suspense thriller tension suspenseful dangerous'),
 ('fast','Action and momentum','Style','action chase fast paced battle fight'),
 ('character','Character relationships','Style','character relationship friendship emotional personal'),
 ('coming_age','Coming of age','Style','coming of age adolescence teenager youth growing up'),
 ('worlds','Immersive worlds','Style','world building imaginary universe alternate worlds'),
 ('experimental','Unusual and experimental','Style','experimental surreal unconventional fragmented dream'),
 ('energetic','High energy','Sound','energetic energy upbeat powerful energetic'),
 ('dance','Danceable beats','Sound','dance dancing danceable rhythmic disco'),
 ('acoustic','Acoustic and gentle','Sound','acoustic unplugged gentle piano folk'),
 ('instrumental','Instrumental','Sound','instrumental'),
 ('cinematic','Cinematic and soundtrack','Sound','orchestral cinematic soundtrack'),
 ('vocals','Vocal-focused','Sound','vocal singer singing voice'),
 ('calm','Calm and quiet','Sound','calm quiet soft ambient peaceful'),
 ('short','Shorter works','Format','short novella concise brief'),
 ('epic','Epic and expansive','Format','epic saga sweeping expansive'),
 ('series','Series and continuing worlds','Format','series sequel trilogy continuing')]
WORDS={k:set(re.findall(r'[a-z]+',q)) for k,_,_,q in CRITERIA}
QUERIES={k:q for k,_,_,q in CRITERIA}
LABELS={k:label for k,label,_,_ in CRITERIA}
AUDIO_KEYS=('acousticness','danceability','energy','instrumentalness','valence')

def audio_values(item):
    value=item.get('metadata') or {}
    if isinstance(value,str):
        try:value=json.loads(value)
        except (ValueError,TypeError):value={}
    return np.array([float(value.get(k,np.nan)) for k in AUDIO_KEYS],dtype=np.float32)

def query_for(item):
    # A film's title is not a lyrical topic: Hail Mary must not retrieve songs
    # solely because they contain 'hail'. Titles remain searchable in the catalogue.
    return str(item.get('description') or '')+' '+str(item.get('genres') or '')+' '+' '.join(QUERIES[k] for k in sorted(features(item)))

def reliable(item,exploration=False):
    if 'quality_count' not in item:return True
    if item['domain']=='music':return item.get('description') or (item.get('popularity') or 0)>=(5 if exploration else 30)
    if item['domain']=='movie':
        count=max(item.get('historical_movie_rating_count',0),item.get('quality_count',0) or 0)
        return count>=(20 if exploration else 100) and (item.get('quality') is None or item['quality']>=.55)
    return True
SETTING_TERMS=['India','Japan','Korea','China','England','Scotland','Ireland','France','Germany','Russia','Africa','America','London','Paris','New York','Tokyo','Mumbai','Delhi','Mars','Earth','space']
ERA_TERMS=['ancient','medieval','Victorian','Renaissance','nineteenth century','twentieth century','World War I','World War II','Cold War','future','futuristic']

def source_labels(item):
    text=item.get('description') or ''
    mentioned=lambda term:bool(re.search(r'\b'+re.escape(term)+r'\b',text,re.I))
    return {'genres':[g.strip() for g in (item.get('genres') or '').split('|') if g.strip()],
            'languages':item.get('languages',[]),'production_countries':item.get('production_countries',[]),
            'setting_mentions':[term for term in SETTING_TERMS if mentioned(term)],
            'era_mentions':[term for term in ERA_TERMS if mentioned(term)],
            'provenance':{'genres':'dataset or attributed catalogue category',
                          'languages':'movie source metadata; unknown elsewhere unless explicitly supplied',
                          'production_countries':'movie source metadata, not narrative setting',
                          'setting_mentions':'literal summary mentions, not independently verified story location',
                          'era_mentions':'literal summary mentions, not publication or release year'}}

def matches_filters(item,filters):
    if not filters or filters.get('scope','all') not in ('all',item['domain']):return True
    labels=item.get('labels') or source_labels(item)
    genres={g.casefold() for g in labels['genres']}
    included={g.casefold() for g in filters.get('include_genres',[])}
    excluded={g.casefold() for g in filters.get('exclude_genres',[])}
    if genres&excluded:return False
    if included and not (included<=genres if filters.get('genre_mode','OR')=='AND' else bool(included&genres)):return False
    for key in ('languages','production_countries','setting_mentions','era_mentions'):
        wanted=filters.get(key)
        if wanted and wanted.casefold() not in {value.casefold() for value in labels.get(key,[])}:return False
    return True

def tokens(text):return set(re.findall(r'[a-z]{3,}',text.lower()))
def identity(item):
    title=re.sub(r'\s*\((film|series)\).*','',item['title'],flags=re.I)
    title=title.split('—')[0]
    return item['domain'],re.sub(r'[^a-z0-9]+',' ',title.casefold()).strip()

def features(item):
    text=' '.join(str(item.get(k) or '') for k in ('description','genres','tags'))
    words=tokens(text);found={k for k,terms in WORDS.items() if words&terms}
    # Audio features describe the record; they don't establish plot or a user's taste.
    audio=item.get('metadata') or {}
    if isinstance(audio,str):
        try:audio=json.loads(audio)
        except (ValueError,TypeError):audio={}
    if not isinstance(audio,dict):audio={}
    for key,criterion,threshold in [('energy','energetic',.7),('danceability','dance',.65),('acousticness','acoustic',.65),('instrumentalness','instrumental',.65)]:
        if float(audio.get(key,0) or 0)>=threshold:found.add(criterion)
    if 'energy' in audio and float(audio['energy'])<.25:found.add('calm')
    return found

def text_for(item):
    traits=features(item)
    return ' '.join(str(item.get(k) or '') for k in ('title','title','description','creators','genres','tags'))+' '+ ' '.join(QUERIES[k] for k in sorted(traits))

@lru_cache(maxsize=1)
def load_index():
    import joblib
    data=joblib.load(ARTIFACT)
    data['by_id']={i['id']:n for n,i in enumerate(data['items'])}
    data['domain_ids']={d:np.array([n for n,i in enumerate(data['items']) if i['domain']==d]) for d in ('movie','book','music')}
    data['cf_by_id']={ident:n for n,ident in enumerate(data['cf_ids'])}
    return data

def effective_weights(signals):
    available={k:w for k,w in WEIGHTS.items() if signals.get(k) is not None}
    total=sum(available.values())
    return {k:w/total for k,w in available.items()} if total else {}

def weighted(signals):return sum(w*signals[k] for k,w in effective_weights(signals).items())

def recent(item,today=None):
    today=today or date.today()
    try:released=date.fromisoformat(item.get('release_date') or '')
    except ValueError:return False
    return 0<=(today-released).days<=365

def recency(item,today):
    if item.get('release_date'):
        try:
            age=(today-date.fromisoformat(item['release_date'])).days
            return max(0,1-age/3650) if age>=0 else None
        except ValueError:pass
    if item.get('year'):
        year=int(item['year'])
        return math.exp(-max(today.year-year,0)/10) if year<=today.year else None
    return None

def choose(pool,items,facets,signals,exposure,*,today,new_count=2):
    """Three relevance choices, then a recent and a less-exposed exploration choice.

    Recent releases are explicit exploration, not a promise of close similarity.
    No claimed true-utility bound; report weights apply within each eligible pool.
    """
    selected=[];used_identity=set();creator_counts=Counter();rows=[]
    exploration_start=5-new_count
    tail_candidates=[n for n in pool if not recent(items[n],today) and reliable(items[n],True) and signals[n]['novelty']>=.5
                     and signals[n]['user_item']>=max(.03,max((signals[m]['user_item'] for m in pool),default=0)*.25)]
    reserved_tail=max(tail_candidates,key=lambda n:weighted(signals[n])) if tail_candidates and new_count==2 else None
    for slot in range(5):
        candidates=[n for n in pool if identity(items[n]) not in used_identity]
        if not candidates:break
        # Relax a creator cap only when necessary to complete the list.
        diverse=[n for n in candidates if not items[n].get('creators') or creator_counts[items[n]['creators'].casefold()]<2]
        if diverse:candidates=diverse
        kind='match';note=None
        if new_count and slot<exploration_start:
            regular=[n for n in candidates if not recent(items[n],today) and n!=reserved_tail and reliable(items[n])]
            if len(regular)>=exploration_start-slot:candidates=regular
        if new_count and slot==exploration_start:
            fresh=[n for n in candidates if recent(items[n],today)]
            if fresh:candidates=fresh;kind='recent';note='Released within the last 12 months; a discovery choice.'
        elif new_count and slot>=exploration_start:
            # Avoid selecting an irrelevant obscure item just to fill a quota.
            best=max(signals[n]['user_item'] for n in candidates)
            eligible=[n for n in candidates if reliable(items[n],True) and signals[n]['user_item']>=max(.03,best*.25) and signals[n]['novelty']>=.5]
            if eligible:candidates=eligible;kind='discovery';note='Less-popular within this domain and not in your known history.'
        scored=[]
        for n in candidates:
            s=dict(signals[n]);prior=[m for m in selected]
            similarity=max((len(facets[n]&facets[m])/len(facets[n]|facets[m]) if facets[n]|facets[m] else 0 for m in prior),default=0)
            s['diversity']=1-similarity
            s['fairness']=1/(1+exposure.get(items[n]['id'],0))
            scored.append((weighted(s),n,s))
        score,n,s=max(scored,key=lambda r:(r[0],-r[1]))
        selected.append(n);used_identity.add(identity(items[n]));creator_counts[items[n].get('creators','').casefold()]+=1
        rows.append({'n':n,'score':score,'signals':s,'effective_weights':effective_weights(s),'kind':kind,'slot_note':note})
    return rows

def recommend(data,seed,*,known=(),feedback=(),exposure=None,criteria=(),query='',avoid='',new_count=2,today=None,filters=None):
    from scipy.sparse import csr_matrix
    today=today or date.today();exposure=exposure or {};items=data['items'];v=data['vectorizer'];matrix=data['matrix'];facets=data['facets']
    canonical=data.get('aliases',{}).get(seed['id'],seed['id'])
    if canonical in data['by_id']:
        catalogue_seed=items[data['by_id'][canonical]]
        seed={**catalogue_seed,**seed,'genres':seed.get('genres') or catalogue_seed.get('genres','')}
    explicit=' '.join(QUERIES[k] for k in criteria)+' '+query
    q=v.transform([query_for(seed) if not explicit.strip() else explicit])
    if explicit.strip():q=.65*q+.35*v.transform([query_for(seed)])
    else:
        likes=[i for i in known if i.get('preference_label') in ('like','immense love') and i['domain']==seed['domain'] and identity(i)!=identity(seed)]
        likes += [items[data['by_id'][f['item_id']]] for f in feedback if f['action']=='like' and f['item_id'] in data['by_id']]
        if likes:q=.8*q+.2*v.transform([query_for(i) for i in likes[:20]]).mean(axis=0)
    q=csr_matrix(q)
    raw=np.asarray((matrix@q.T).toarray()).ravel()
    wanted=features(seed)|set(criteria)
    genre_keys=lambda text:{re.sub(r'[^a-z0-9]','',part.lower()) for part in (text or '').split('|') if part.strip()}
    seed_genres=genre_keys(seed.get('genres',''))
    excluded={seed['id']}|{i['id'] for i in known}|{f['item_id'] for f in feedback if f['action'] in ('dislike','seen')}
    excluded_identity={identity(seed)}|{identity(i) for i in known}
    avoid_words=tokens(avoid)
    # True historical MovieLens audience affinity is available only in movies.
    movie_seeds=[seed]+[i for i in known if i.get('preference_label') in ('like','immense love') and i['domain']=='movie']
    seed_columns=sorted({data['cf_by_id'][data.get('aliases',{}).get(i['id'],i['id'])] for i in movie_seeds if data.get('aliases',{}).get(i['id'],i['id']) in data['cf_by_id']})
    seed_columns=[n for n in seed_columns if data['cf_counts'][n]>0]
    cf=None
    if seed_columns and data['cf_matrix'].shape[0]:
        affinity=np.asarray(data['cf_matrix'][:,seed_columns].mean(axis=1)).ravel()
        cf_values=np.asarray(data['cf_matrix'].T@affinity).ravel()/(data['cf_counts']+20)
        cf_values/=max(float(cf_values.max()),1e-9)
        cf={ident:float(value) for ident,value,count in zip(data['cf_ids'],cf_values,data['cf_counts']) if count>0}
    output={};details={};all_signals={}
    music_likes=[i for i in known if i['domain']=='music' and i.get('preference_label') in ('like','immense love')]
    music_likes += [items[data['by_id'][f['item_id']]] for f in feedback if f['action']=='like' and f['item_id'] in data['by_id'] and items[data['by_id'][f['item_id']]]['domain']=='music']
    if seed['domain']=='music':music_likes=[seed]+music_likes
    measured=[audio_values(i) for i in music_likes if np.isfinite(audio_values(i)).any()]
    audio_similarity=None
    if measured and 'audio_matrix' in data:
        mean=np.nanmean(np.vstack(measured),axis=0);valid=np.isfinite(mean)
        differences=np.abs(data['audio_matrix'][:,valid]-mean[valid]);observed=np.isfinite(differences).sum(axis=1)
        audio_similarity=np.where(observed>0,1-np.nansum(differences,axis=1)/np.maximum(observed,1),np.nan)
    music_creators={str(i.get('creators','')).casefold() for i in music_likes if i.get('creators')}
    for domain in ('movie','book','music'):
        ids=data['domain_ids'][domain];max_sim=max(float(raw[ids].max()),1e-9)
        for n in ids:
            i=items[n];feature_match=len(wanted&facets[n])/max(len(wanted),1)
            item_genres=genre_keys(i.get('genres',''))
            genre=len(seed_genres&item_genres)/len(seed_genres|item_genres) if seed_genres and item_genres else None
            content=.70*float(raw[n]/max_sim)+.30*feature_match
            if domain=='music' and audio_similarity is not None and np.isfinite(audio_similarity[n]):
                artist_match=float(any(artist in str(i.get('creators','')).casefold() for artist in music_creators))
                content=(.65 if explicit.strip() else .45)*content+(.25 if explicit.strip() else .45)*float(audio_similarity[n])+.10*artist_match
            all_signals[n]={'user_item':min(content,1),'similar_users':cf.get(i['id'],0) if cf is not None and domain=='movie' and i['id'] in cf else None,
                            'genre':genre,'novelty':float(data['novelty'][n]),'diversity':1.,'fairness':1/(1+exposure.get(i['id'],0)),'recency':recency(i,today)}
        eligible=[int(n) for n in ids if items[n]['id'] not in excluded and identity(items[n]) not in excluded_identity
                  and matches_filters(items[n],filters)
                  and (not avoid_words or not avoid_words&tokens(text_for(items[n])))
                  and not (items[n].get('release_date') and items[n]['release_date']>today.isoformat())]
        # Candidate generation is based on relevance, before novelty/fairness scoring.
        eligible.sort(key=lambda n:(-all_signals[n]['user_item'],items[n]['id']))
        pool=eligible[:200]
        # Explicit exploration pool supports recently added items lacking interactions.
        pool=list(dict.fromkeys(pool+[n for n in eligible if recent(items[n],today)]))
        chosen=choose(pool,items,facets,all_signals,exposure,today=today,new_count=new_count)
        results=[]
        for row in chosen:
            n=row.pop('n');i=items[n];shared=sorted(wanted&facets[n])
            explanation=[]
            if shared:explanation.append('Related catalogue features: '+', '.join(LABELS[k].lower() for k in shared[:3])+'.')
            if row['signals']['similar_users'] is not None:explanation.append('Includes historical movie-audience affinity.')
            if not shared:explanation.append('A broader text or metadata connection; fit is uncertain.')
            if row['slot_note']:explanation.append(row['slot_note'])
            scope='Summary and metadata connection.' if i.get('description') else 'Title, artist and audio metadata only; no lyric or story claim.'
            results.append({**{k:i.get(k) for k in ('id','domain','title','creators','year','description','source_url','release_date')},**row,
                            'shared_features':[LABELS[k] for k in shared],'reason':' '.join(explanation),'evidence_scope':scope,
                            'history_status':'Not in your known or consumed records; you may still know it.',
                            'new_to_catalog':bool(i.get('fresh_catalog')),
                            'labels':i.get('labels') or source_labels(i),
                            'source_excerpt':(i.get('description') or '')[:160]})
        output[domain]=results
        details[domain]={'eligible_catalogue':len(eligible),'candidate_pool':len(pool),'returned':len(results),'recent_count':sum(i['kind']=='recent' for i in results),'discovery_count':sum(i['kind']=='discovery' for i in results)}
    return {'source':{k:seed.get(k) for k in ('id','domain','title','description','creators')},'domains':output,'counts':details,
            'base_weights':WEIGHTS,'mode':'refined' if criteria or query or avoid else 'automatic','criteria':list(criteria),'query':query,
            'limitations':['Unavailable similar-user evidence is omitted and the remaining report weights are normalized.',
                           'Fairness uses local item-exposure balancing; no demographic or provider fairness guarantee.',
                           'Content similarity and exploration are suggestions, not measured satisfaction or a utility certificate.',
                           'Recent releases come from a small manually verified addition to the historical catalogue.'],
            'collaborative_status':'Historical movie audience affinity available.' if cf is not None else 'No movie interaction evidence for the selected starting work; content fallback active.'}
