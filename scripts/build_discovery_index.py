"""Local full-catalogue text index and real historical movie audience matrix.

No pretrained weights, model calls or downloads. Historical data are for product
retrieval; existing frozen evaluation artifacts remain unchanged.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,sqlite3,time,ast
import numpy as np
import pandas as pd
import joblib
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from recros_api.catalog_discovery import ROOT,ARTIFACT,text_for,features,identity,source_labels,audio_values

def finite(value,fallback=None):
 try:return float(value) if np.isfinite(float(value)) else fallback
 except (ValueError,TypeError):return fallback

def main():
 started=time.perf_counter();ARTIFACT.parent.mkdir(parents=True,exist_ok=True)
 frame=pd.read_parquet(ROOT/'ml/data/processed/items.parquet')
 with sqlite3.connect(ROOT/'apps/api/data/familiar-catalog.db') as c:
  clean_titles=dict(c.execute('SELECT id,title FROM works'))
 sources={'movie':'https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset','book':'https://www.kaggle.com/datasets/dylanjcastillo/7k-books-with-metadata','music':'https://www.kaggle.com/datasets/vatsalmavani/spotify-dataset'}
 items=[]
 raw_movies=pd.read_csv(ROOT/'movie_dataset/movies_metadata.csv',low_memory=False,on_bad_lines='skip')
 movie_metadata={}
 for r in raw_movies.to_dict('records'):
  if not finite(r.get('id')):continue
  def parsed(value):
   try:return ast.literal_eval(str(value)) if value else []
   except (ValueError,SyntaxError):return []
  spoken=parsed(r.get('spoken_languages'));countries=parsed(r.get('production_countries'))
  languages={str(r['original_language'])} if isinstance(r.get('original_language'),str) else set()
  languages.update(x['iso_639_1'] for x in spoken if isinstance(x,dict) and x.get('iso_639_1'))
  movie_metadata['movie:'+str(int(float(r['id']))) ]={'languages':sorted(languages),'production_countries':[x['name'] for x in countries if isinstance(x,dict) and x.get('name')],
    'quality_count':finite(r.get('vote_count'),0),
    'release_date':r['release_date'] if isinstance(r.get('release_date'),str) and len(r['release_date'])==10 else None}
 for row in frame.to_dict('records'):
  items.append({'id':row['item_key'],'domain':row['domain'],'title':clean_titles.get(row['item_key'],row['title']),
                'description':row['description'] if isinstance(row['description'],str) else '',
                'creators':row['creators'] if isinstance(row['creators'],str) else '',
                'genres':row['genres_str'] if isinstance(row['genres_str'],str) else '',
                'tags':row['tags_str'] if isinstance(row['tags_str'],str) else '',
                'year':int(row['year']) if finite(row['year']) else None,'popularity':finite(row['popularity']),
                'metadata':json.loads(row['extra_json']) if isinstance(row['extra_json'],str) else {},'source_url':sources[row['domain']],
                'quality':finite(row['avg_rating'])/(10 if row['domain']=='movie' else 5) if finite(row['avg_rating']) is not None else None,
                'quality_count':json.loads(row['extra_json']).get('ratings_count',0) if row['domain']=='book' else 0,
                **movie_metadata.get(row['item_key'],{})})
 by_identity={identity(i):i for i in items};by_id={i['id']:i for i in items};aliases={}
 # Reuse attributed sourced descriptions. Prefer canonical IDs, retaining aliases.
 for filename in ['demo/catalog.real.json','demo/transfer/sources.json','demo/catalog/recent.20261014.json']:
  for item in json.loads((ROOT/filename).read_text())['items']:
   key=identity(item);old=by_id.get(item['id']) or by_identity.get(key)
   if old and item.get('year') and old.get('year') and int(item['year'])!=int(old['year']):
    old=None  # A new adaptation/remake is a distinct work, never overwrite the old one.
   if old:
    aliases[item['id']]=old['id']
    for field in ('description','creators','source_url','genres','tags','release_date','fresh_catalog','evidence_kind'):
     value=item.get(field)
     if field=='description':value=item.get('evidence_text',value)
     if value:old[field]=value
   else:
    item={**item,'description':item.get('evidence_text',item.get('description','')),'metadata':item.get('metadata',{}),'popularity':None}
    items.append(item);by_identity[key]=item;by_id[item['id']]=item
 print(json.dumps({'stage':'catalogue','records':len(items)}),flush=True)
 for item in items:item['labels']=source_labels(item)
 vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=35000,min_df=2,stop_words='english',sublinear_tf=True,dtype=np.float32)
 matrix=vectorizer.fit_transform([text_for(i) for i in items])
 facets=[features(i) for i in items];novelty=np.full(len(items),.5,dtype=np.float32)
 for domain in ('movie','book','music'):
  rows=[n for n,i in enumerate(items) if i['domain']==domain and i.get('popularity') is not None]
  values=np.array([items[n]['popularity'] for n in rows]);ordered=np.sort(values)
  novelty[rows]=1-(np.searchsorted(ordered,values,'left')+np.searchsorted(ordered,values,'right'))/(2*len(values))
 print(json.dumps({'stage':'text','features':len(vectorizer.vocabulary_),'nonzero':matrix.nnz}),flush=True)
 links=pd.read_csv(ROOT/'movie_dataset/links.csv').dropna(subset=['movieId','tmdbId'])
 mapping={int(r.movieId):'movie:'+str(int(r.tmdbId)) for r in links.itertuples()}
 available={key:val for key,val in mapping.items() if val in by_id}
 movie_ids=sorted(available);columns={m:n for n,m in enumerate(movie_ids)}
 users=[];cols=[];counts=Counter();total=0
 for chunk in pd.read_csv(ROOT/'movie_dataset/rating.csv',usecols=['userId','movieId','rating'],dtype={'userId':'int32','movieId':'int32','rating':'float32'},chunksize=1000000):
  total+=len(chunk);counts.update(chunk.movieId.value_counts().to_dict())
  positive=chunk[(chunk.rating>=4)&chunk.movieId.isin(columns)]
  users.append(positive.userId.to_numpy()-1);cols.append(positive.movieId.map(columns).to_numpy(dtype=np.int32))
 users=np.concatenate(users);cols=np.concatenate(cols)
 cf_matrix=csr_matrix((np.ones(len(users),dtype=np.float32),(users,cols)),shape=(int(users.max())+1,len(columns)))
 cf_matrix.sum_duplicates();cf_matrix.data[:]=1
 cf_counts=np.asarray(cf_matrix.sum(axis=0)).ravel()
 for mid,key in available.items():by_id[key]['historical_movie_rating_count']=int(counts[mid])
 label_options={k:dict(Counter(value for i in items for value in i['labels'][k])) for k in ('genres','languages','production_countries','setting_mentions','era_mentions')}
 coverage={d:{k:sum(bool(i['labels'][k]) for i in items if i['domain']==d) for k in label_options} for d in ('movie','book','music')}
 data={'items':items,'vectorizer':vectorizer,'matrix':matrix,'facets':facets,'novelty':novelty,'aliases':aliases,'label_options':label_options,'label_coverage':coverage,
       'audio_matrix':np.vstack([audio_values(i) for i in items]),
       'cf_matrix':cf_matrix,'cf_ids':[available[m] for m in movie_ids],'cf_counts':cf_counts}
 staging=ARTIFACT.with_suffix('.building.joblib');joblib.dump(data,staging,compress=3);staging.replace(ARTIFACT)
 audit={'catalogue':len(items),'domains':dict(Counter(i['domain'] for i in items)),'text_features':len(vectorizer.vocabulary_),
        'movie_rating_rows_read':total,'positive_movie_interactions':int(cf_matrix.nnz),'historical_users_with_index_rows':cf_matrix.shape[0],
        'historical_movie_columns':cf_matrix.shape[1],'recent_source_additions':7,'built_seconds':round(time.perf_counter()-started,2),
        'scope':'Full catalogue content retrieval and movie-only historical audience affinity. No shared book/song users or independent preference evaluation.',
        'recent_sources':'demo/catalog/recent.20261014.json','label_coverage':coverage,
        'label_note':'Genre/category and movie language/country fields are source metadata. Setting/era fields are literal summary mentions, not verified setting. Missing values stay unknown.',
        'source_parquet_sha256':hashlib.sha256((ROOT/'ml/data/processed/items.parquet').read_bytes()).hexdigest()}
 (ROOT/'docs/milestone2/CATALOG_DISCOVERY_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit),flush=True)
if __name__=='__main__':main()
