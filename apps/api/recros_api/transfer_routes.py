"""Local cached evidence discovery. No hosted model call or rating writes."""
from copy import deepcopy
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import personal_case
from .transfer_engine import FEATURES, ROOT, discover, load_catalog

router=APIRouter(prefix='/api/transfer')


def interpret_with_student(items):
    from .student_runtime import interpret
    return interpret(items)


def catalog():
    try:
        scaled=ROOT/'apps/api/data/scaled-transfer/annotated.json'
        return load_catalog(scaled if scaled.exists() else None)
    except (OSError,ValueError) as exc:
        raise HTTPException(503,'The evidence catalog is not ready. Build its cache first.') from exc


def public_anchors():
    return json.loads((ROOT/'demo/catalog.real.json').read_text())['items']


@router.get('/catalog')
def metadata():
    c=catalog()
    return {'features':FEATURES,'source_anchors':[{k:i[k] for k in ('id','domain','title','description')}
                                                 for i in public_anchors()],
            'counts':{d:sum(i['domain']==d for i in c['items']) for d in ('movie','book','music')},
            'annotation_model':c['annotation_run']['requested_model'],
            'pipeline_counts':c.get('pipeline_counts',{'evidence_bank':len(c['items'])}),
            'student_available':(ROOT/'apps/api/data/scaled-transfer/student.annotated.json').exists(),
            'scope':c['selection']}


class Removal(BaseModel):
    item_id:str=Field(min_length=1,max_length=150)
    feature:str=Field(min_length=1,max_length=40)


class DiscoveryRequest(BaseModel):
    source_id:str=Field(min_length=1,max_length=150)
    target_domain:str=Field(min_length=1,max_length=20)
    goals:list[str]=Field(default_factory=list,max_length=2)
    inspected:bool=True
    removed:Removal|None=None
    evidence_mode:str='complete'
    extractor:str='teacher'
    case_token:str|None=Field(default=None,max_length=100)
    expected_revision:int|None=Field(default=None,ge=0)


@router.post('/discover')
def run(payload:DiscoveryRequest):
    c=catalog(); anchors=public_anchors(); excluded=[]
    if payload.extractor not in ('teacher','student'):
        raise HTTPException(422,'Unknown extractor.')
    if payload.extractor=='student':
        student_path=ROOT/'apps/api/data/scaled-transfer/student.annotated.json'
        if not student_path.exists():raise HTTPException(503,'The local student experiment is not ready.')
    if payload.case_token:
        with personal_case.LOCK:
            profile=personal_case.load(payload.case_token)
            if payload.expected_revision!=profile['revision']:
                raise HTTPException(409,'Your case changed. Reload before discovering.')
            anchors=profile['items']
            excluded=[i['id'] for i in profile['items']]
    seed=next((i for i in anchors if i['id']==payload.source_id),None)
    if not seed or seed.get('identity_status','matched')!='matched':
        raise HTTPException(422,'Choose a resolved starting work.')
    if payload.evidence_mode not in ('complete','credits_only'):
        raise HTTPException(422,'Unknown evidence condition.')
    if payload.removed:
        if payload.removed.feature not in payload.goals or not any(i['id']==payload.removed.item_id and
                                                                  i['domain']==payload.target_domain for i in c['items']):
            raise HTTPException(422,'The removed evidence must belong to a selected criterion and target candidate.')
    if payload.evidence_mode=='credits_only':
        c=deepcopy(c)
        for i in c['items']:
            i['evidence_text']=f'{i["title"]} by {i.get("creators", "credited creator")}. Only title and creator credits are available.'
    # Candidate generation uses source text before inspecting model feature
    # claims. The same fixed shortlist is shown to the text baseline.
    from recros_ml.research.transfer_build import bm25, QUERIES
    if any(g not in FEATURES for g in payload.goals):
        raise HTTPException(422,'Unknown criterion.')
    candidates=[i for i in c['items'] if i['domain']==payload.target_domain and i['id'] not in excluded]
    query=' '.join(QUERIES[g] for g in payload.goals)
    ranked=bm25(candidates,query)
    shortlist={ident for _,ident in ranked[:8]}
    # Hold the shortlist fixed for a one-claim intervention, preventing the
    # intervention from secretly changing the retrieval stage.
    c={**c,'items':[i for i in c['items'] if i['domain']!=payload.target_domain or i['id'] in shortlist]}
    student_run=None
    if payload.extractor=='student' and payload.inspected and payload.goals:
        try:
            transformed,student_run=interpret_with_student([i for i in c['items'] if i['domain']==payload.target_domain])
        except (ImportError,OSError,RuntimeError) as exc:
            raise HTTPException(503,'The local tiny-model runtime is unavailable. Use cached DeepSeek mode.') from exc
        c={**c,'items':[i for i in c['items'] if i['domain']!=payload.target_domain]+transformed,
           'annotation_run':{'requested_model':'local-tiny-causal-lm-v2'}}
    try:
        result=discover(c,payload.target_domain,payload.goals,inspected=payload.inspected,
                        removed=payload.removed.model_dump() if payload.removed else None,excluded_ids=excluded)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    result['source_context']={'id':seed['id'],'title':seed['title'],'domain':seed['domain']}
    result['evidence_condition']=payload.evidence_mode
    result['annotation_model']=c['annotation_run']['requested_model']
    result['extractor']=payload.extractor
    if payload.extractor=='student':
        result['student_scope']='Tiny local language-model proposals filtered by cached teacher passages. This is not independent source verification, and the student remains weak in the development test.'
        result['student_run']=student_run
    result['retrieval_counts']={'evidence_bank_candidates':len(candidates),'shortlist':len(shortlist)}
    if payload.inspected and payload.goals:
        candidates=[i for i in c['items'] if i['domain']==payload.target_domain and i['id'] not in excluded]
        ranked=bm25(candidates,query)
        by_id={i['id']:i for i in candidates}
        result['text_baseline']=[{'id':ident,'title':by_id[ident]['title'],'score':round(score,5),
                                  'source_url':by_id[ident]['source_url']}
                                 for score,ident in ranked[:3]]
    return result
