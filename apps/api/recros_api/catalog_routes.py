"""Automatic and optional refined discovery, plus separate product feedback."""
from __future__ import annotations
from datetime import date
import json,re,time,secrets
from fastapi import APIRouter,HTTPException,Query,Header
from pydantic import BaseModel,Field
from . import db,personal_case
from .catalog_discovery import load_index,recommend,WEIGHTS,CRITERIA,identity,ARTIFACT
from .familiarity import connect_catalog

router=APIRouter(prefix='/api/discovery')

def init_discovery():
 with db.get_conn() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS discovery_feedback (
  user_id INTEGER NOT NULL REFERENCES users(id),item_id TEXT NOT NULL,action TEXT NOT NULL,
  created_at TEXT NOT NULL,PRIMARY KEY(user_id,item_id));
  CREATE TABLE IF NOT EXISTS discovery_exposure (item_id TEXT PRIMARY KEY,served INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS discovery_receipts (id TEXT PRIMARY KEY,user_id INTEGER NOT NULL,
  item_ids TEXT NOT NULL,created_at TEXT NOT NULL,impressions_saved INTEGER NOT NULL DEFAULT 0);''')

def actor(authorization):
 if not authorization:return None
 if not authorization.startswith('Bearer '):raise HTTPException(401,'Invalid authorization.')
 user=db.authenticate_token(authorization[7:])
 if user is None:raise HTTPException(401,'Session expired. Refresh the page.')
 return user

def index():
 if not ARTIFACT.exists():raise HTTPException(503,'The catalogue index is being prepared. Try again shortly.')
 return load_index()

def known_profile(token,revision=None):
 if not token:return None
 with personal_case.LOCK:
  p=personal_case.load(token)
  if revision is not None and revision!=p['revision']:raise HTTPException(409,'Your saved case changed. Reload first.')
  return p

def starters(token=None):
 p=known_profile(token)
 if p:return p['items']
 data=index();ids=['movie:project-hail-mary-2026','movie:2001','book:martian','music:space-oddity']
 records=[]
 for ident in ids:
  canonical=data['aliases'].get(ident,ident)
  if canonical in data['by_id']:records.append(data['items'][data['by_id'][canonical]])
 return records or data['items'][:3]

@router.get('/catalog')
def metadata(case_token:str|None=None):
 data=index()
 return {'counts':{d:len(ids) for d,ids in data['domain_ids'].items()},'criteria':[{'id':k,'label':label,'group':group} for k,label,group,_ in CRITERIA],
         'starters':[{k:i.get(k) for k in ('id','title','domain','creators','description','preference_label')} for i in starters(case_token)],
         'base_weights':WEIGHTS,'label_options':data.get('label_options',{}),'label_coverage':data.get('label_coverage',{}),
         'scope':'Full-catalogue text/audio metadata retrieval; cached source evidence and movie-only historical audience affinity.'}

@router.get('/search')
def search(q:str=Query(min_length=2,max_length=120),domain:str='all',case_token:str|None=None):
 if domain not in ('all','movie','book','music'):raise HTTPException(422,'Unknown domain.')
 # Validate private-token access before returning any private anchor.
 anchors=starters(case_token);data=index();terms=re.findall(r'\w+',q,flags=re.UNICODE)
 if not terms:return {'items':[]}
 match=' AND '.join('"'+term+'"*' for term in terms)
 with connect_catalog() as c:
  rows=c.execute('SELECT w.id,w.domain,w.title,w.creators,w.year FROM search JOIN works w ON search.rowid=w.rowid WHERE search MATCH ? AND (?="all" OR w.domain=?) ORDER BY bm25(search),w.year DESC LIMIT 20',(match,domain,domain)).fetchall()
 results=[dict(r) for r in rows]
 extras=anchors+[i for i in data['items'] if i.get('fresh_catalog')]
 for item in reversed(extras):
  if all(term.casefold() in (item['title']+' '+str(item.get('creators',''))).casefold() for term in terms) and domain in ('all',item['domain']):
   if not any(r['id']==item['id'] for r in results):results.insert(0,{k:item.get(k) for k in ('id','title','domain','creators','year')})
 return {'items':results[:25]}

class LabelFilters(BaseModel):
 scope:str='all'
 include_genres:list[str]=Field(default_factory=list,max_length=30)
 exclude_genres:list[str]=Field(default_factory=list,max_length=30)
 genre_mode:str='OR'
 languages:str=Field(default='',max_length=80)
 production_countries:str=Field(default='',max_length=120)
 setting_mentions:str=Field(default='',max_length=120)
 era_mentions:str=Field(default='',max_length=120)

class Request(BaseModel):
 source_id:str=Field(min_length=1,max_length=150)
 case_token:str|None=Field(default=None,max_length=100)
 expected_revision:int|None=Field(default=None,ge=0)
 criteria:list[str]=Field(default_factory=list,max_length=12)
 query:str=Field(default='',max_length=500)
 avoid:str=Field(default='',max_length=300)
 new_count:int=Field(default=2,ge=0,le=2)
 filters:LabelFilters=Field(default_factory=LabelFilters)

@router.post('/recommend')
def discovery(payload:Request,authorization:str|None=Header(default=None)):
 started=time.perf_counter();user=actor(authorization);data=index();p=known_profile(payload.case_token,payload.expected_revision)
 if payload.case_token and payload.expected_revision is None:raise HTTPException(409,'Reload your case revision first.')
 criteria_ids={k for k,*_ in CRITERIA}
 if any(k not in criteria_ids for k in payload.criteria):raise HTTPException(422,'Unknown shortcut. Use free text for other preferences.')
 if payload.filters.scope not in ('all','movie','book','music') or payload.filters.genre_mode not in ('AND','OR'):raise HTTPException(422,'Unknown filter mode.')
 if set(payload.filters.include_genres)&set(payload.filters.exclude_genres):raise HTTPException(422,'A genre cannot be both included and excluded.')
 canonical=data['aliases'].get(payload.source_id,payload.source_id)
 seed=next((i for i in (p or {}).get('items',[]) if i['id']==payload.source_id),None)
 if seed is None and canonical in data['by_id']:seed=data['items'][data['by_id'][canonical]]
 if seed is None:raise HTTPException(404,'Select a catalogue work from search.')
 with db.get_conn() as c:
  feedback=[dict(r) for r in c.execute('SELECT item_id,action FROM discovery_feedback WHERE user_id=?',(user,))] if user else []
  exposure=dict(c.execute('SELECT item_id,served FROM discovery_exposure'))
 result=recommend(data,seed,known=(p or {}).get('items',[]),feedback=feedback,exposure=exposure,
                  criteria=payload.criteria,query=payload.query,avoid=payload.avoid,new_count=payload.new_count,today=date.today(),filters=payload.filters.model_dump())
 if user:
  receipt=secrets.token_urlsafe(20)
  ids=[i['id'] for domain in result['domains'].values() for i in domain]
  with db.get_conn() as c:c.execute('INSERT INTO discovery_receipts VALUES (?,?,?,?,0)',(receipt,user,json.dumps(ids),db.utc_now()))
  result['receipt_id']=receipt
 result['runtime_ms']=round((time.perf_counter()-started)*1000,2)
 result['feedback_scope']='Product suggestions and explicit feedback; not research-study judgments.'
 return result

class Impression(BaseModel):
 receipt_id:str=Field(min_length=1,max_length=100)

@router.post('/impressions')
def impressions(payload:Impression,authorization:str|None=Header(default=None)):
 user=actor(authorization)
 if user is None:raise HTTPException(401,'A local session is required.')
 with db.get_conn() as c:
  row=c.execute('SELECT * FROM discovery_receipts WHERE id=? AND user_id=?',(payload.receipt_id,user)).fetchone()
  if row is None:raise HTTPException(404,'Recommendation batch not found.')
  changed=c.execute('UPDATE discovery_receipts SET impressions_saved=1 WHERE id=? AND impressions_saved=0',(payload.receipt_id,)).rowcount
  if changed:
   c.executemany('INSERT INTO discovery_exposure VALUES (?,1) ON CONFLICT(item_id) DO UPDATE SET served=served+1',[(ident,) for ident in json.loads(row['item_ids'])])
 return {'saved':bool(changed),'meaning':'Rendered recommendation opportunities, not proof of consumption or satisfaction.'}

class Feedback(BaseModel):
 receipt_id:str=Field(min_length=1,max_length=100)
 item_id:str=Field(min_length=1,max_length=150)
 action:str

@router.post('/feedback')
def feedback(payload:Feedback,authorization:str|None=Header(default=None)):
 user=actor(authorization)
 if user is None:raise HTTPException(401,'A local session is required.')
 if payload.action not in ('like','dislike','seen','undo'):raise HTTPException(422,'Unknown feedback action.')
 with db.get_conn() as c:
  row=c.execute('SELECT item_ids FROM discovery_receipts WHERE id=? AND user_id=?',(payload.receipt_id,user)).fetchone()
  if row is None or payload.item_id not in json.loads(row['item_ids']):raise HTTPException(404,'This work was not in your recommendation batch.')
  if payload.action=='undo':c.execute('DELETE FROM discovery_feedback WHERE user_id=? AND item_id=?',(user,payload.item_id))
  else:c.execute('INSERT INTO discovery_feedback VALUES (?,?,?,?) ON CONFLICT(user_id,item_id) DO UPDATE SET action=excluded.action,created_at=excluded.created_at',(user,payload.item_id,payload.action,db.utc_now()))
 return {'saved':True,'scope':'Explicit product feedback; no synthetic human-study record.'}
