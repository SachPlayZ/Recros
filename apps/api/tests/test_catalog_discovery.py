from datetime import date
import json
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from fastapi.testclient import TestClient
from recros_api.catalog_discovery import (features,text_for,identity,source_labels,matches_filters,effective_weights,weighted,recommend,WEIGHTS)
from recros_api import db,catalog_routes
from recros_api.main import app

def dataset():
 items=[]
 for domain in ('movie','book','music'):
  for n in range(8):
   item={'id':f'{domain}:{n}','domain':domain,'title':f'{domain} fixture {n}','description':'Science and space exploration with friendship and survival.',
         'genres':'Science Fiction','creators':f'Creator {n}','year':2026 if n==6 else 2010,'source_url':'https://example.org/fixture','metadata':{},'languages':['en'] if domain=='movie' else [],'production_countries':['India'] if n==1 and domain=='movie' else []}
   if n==6:item['release_date']='2026-05-05'
   item['labels']=source_labels(item);items.append(item)
 v=TfidfVectorizer();matrix=v.fit_transform([text_for(i) for i in items])
 return {'items':items,'by_id':{i['id']:n for n,i in enumerate(items)},'aliases':{},'vectorizer':v,'matrix':matrix,
         'facets':[features(i) for i in items],'novelty':np.array([.9 if i['id'].endswith(':7') else .2 for i in items]),
         'domain_ids':{d:np.array([n for n,i in enumerate(items) if i['domain']==d]) for d in ('movie','book','music')},
         'cf_by_id':{},'cf_ids':[],'cf_matrix':csr_matrix((0,0)),'cf_counts':np.array([]),'label_options':{},'label_coverage':{}}

def test_automatic_has_five_in_all_domains_and_recent_discovery_slots():
 data=dataset();seed=data['items'][0]
 r=recommend(data,seed,today=date(2026,10,14))
 assert r['mode']=='automatic'
 assert set(r['domains'])=={'movie','book','music'}
 for domain,items in r['domains'].items():
  assert len(items)==5 and len({identity(i) for i in items})==5
  assert items[3]['kind']=='recent' and items[4]['kind']=='discovery'
  assert all(i['signals']['similar_users'] is None for i in items)
 assert seed['id'] not in {i['id'] for i in r['domains']['movie']}
 assert abs(sum(WEIGHTS.values())-1)<1e-12

def test_missing_signals_renormalize_report_weights_without_fake_cf():
 signals={k:.5 for k in WEIGHTS};signals['similar_users']=None
 weights=effective_weights(signals)
 assert 'similar_users' not in weights
 assert weights['user_item']==.30/.80
 assert abs(sum(weights.values())-1)<1e-12
 assert abs(weighted(signals)-.5)<1e-12

def test_zero_interaction_seed_uses_content_fallback():
 data=dataset();data['cf_by_id']={'movie:0':0,'movie:1':1}
 data['cf_ids']=['movie:0','movie:1'];data['cf_counts']=np.array([0,2])
 data['cf_matrix']=csr_matrix([[0,1],[0,1]])
 r=recommend(data,data['items'][0],today=date(2026,10,14))
 assert 'content fallback' in r['collaborative_status']
 assert all(i['signals']['similar_users'] is None for i in r['domains']['movie'])

def test_source_metadata_filters_and_unknown_not_negative():
 i=dataset()['items'][1]
 assert matches_filters(i,{'scope':'movie','languages':'en','production_countries':'India','include_genres':['Science Fiction']})
 assert not matches_filters(i,{'include_genres':['Fantasy']})
 assert not matches_filters(i,{'exclude_genres':['Science Fiction']})
 assert not matches_filters(i,{'include_genres':['Science Fiction','Fantasy'],'genre_mode':'AND'})
 assert matches_filters(i,{'include_genres':['Science Fiction','Fantasy'],'genre_mode':'OR'})
 book=dataset()['items'][8]
 assert not matches_filters(book,{'languages':'en'})
 assert matches_filters(book,{'scope':'movie','languages':'en'})
 assert not matches_filters(i,{'setting_mentions':'India'}) # origin isn't story setting
 assert not source_labels({'title':'x','domain':'book','year':1890,'description':'An ordinary family story.'})['era_mentions']

def test_dislikes_and_seen_works_are_excluded_even_from_exploration():
 data=dataset();r=recommend(data,data['items'][0],feedback=[{'item_id':'book:6','action':'dislike'},{'item_id':'music:7','action':'seen'}],today=date(2026,10,14))
 assert 'book:6' not in {i['id'] for i in r['domains']['book']}
 assert 'music:7' not in {i['id'] for i in r['domains']['music']}

def test_refinement_can_filter_same_domain_and_admits_fewer_than_five():
 data=dataset();r=recommend(data,data['items'][0],filters={'scope':'movie','production_countries':'India'},today=date(2026,10,14))
 assert len(r['domains']['movie'])==1
 assert len(r['domains']['book'])==5 and len(r['domains']['music'])==5

def test_receipts_scope_impressions_and_feedback_to_own_session(tmp_path,monkeypatch):
 monkeypatch.setattr(db,'DB_PATH',tmp_path/'db.sqlite')
 monkeypatch.setattr(catalog_routes,'index',dataset)
 with TestClient(app) as c:
  user=c.post('/api/users').json();other=c.post('/api/users').json()
  headers={'Authorization':'Bearer '+user['token']};other_headers={'Authorization':'Bearer '+other['token']}
  r=c.post('/api/discovery/recommend',headers=headers,json={'source_id':'movie:0'}).json()
  assert all(len(items)==5 for items in r['domains'].values())
  receipt=r['receipt_id'];item=r['domains']['book'][0]['id']
  assert c.post('/api/discovery/impressions',headers=headers,json={'receipt_id':receipt}).json()['saved']
  assert not c.post('/api/discovery/impressions',headers=headers,json={'receipt_id':receipt}).json()['saved']
  assert c.post('/api/discovery/feedback',headers=other_headers,json={'receipt_id':receipt,'item_id':item,'action':'like'}).status_code==404
  assert c.post('/api/discovery/feedback',headers=headers,json={'receipt_id':receipt,'item_id':'invented','action':'like'}).status_code==404
  assert c.post('/api/discovery/feedback',headers=headers,json={'receipt_id':receipt,'item_id':item,'action':'dislike'}).status_code==200
  again=c.post('/api/discovery/recommend',headers=headers,json={'source_id':'movie:0'}).json()
  assert item not in {i['id'] for i in again['domains']['book']}
  assert c.post('/api/discovery/recommend',headers=headers,json={'source_id':'movie:0','criteria':['made_up']}).status_code==422
  with db.get_conn() as conn:assert conn.execute('SELECT count(*) FROM decision_sessions').fetchone()[0]==0
