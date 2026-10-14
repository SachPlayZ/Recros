"""Human reading judgments on supplied text; model predictions hidden until submit."""
from datetime import datetime,timezone
import hmac,json
from pathlib import Path
import threading

from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field

from .transfer_engine import FEATURES,ROOT

REVIEW_DIR=ROOT/'apps/api/data/source-review'
router=APIRouter(prefix='/api/source-review');LOCK=threading.Lock()


def load(token):
    try:
        if not hmac.compare_digest(token,(REVIEW_DIR/'token.txt').read_text().strip()):
            raise HTTPException(404,'Review not found.')
        return json.loads((REVIEW_DIR/'state.json').read_text())
    except OSError as exc:raise HTTPException(404,'Review not found.') from exc


@router.get('/{token}')
def read(token:str):
    with LOCK:
        s=load(token)
        return {'revision':s['revision'],'submitted':s.get('submitted',False),
                'items':s['items'],'features':FEATURES,
                'result':s.get('result'),
                'scope':'Judge only whether the supplied paragraph supports a feature. No knowledge of the complete work or liking judgment is requested.'}


class Judgment(BaseModel):
    item_id:str
    status:str
    features:list[str]=Field(default_factory=list,max_length=4)


class Submission(BaseModel):
    expected_revision:int=Field(ge=0)
    judgments:list[Judgment]=Field(min_length=6,max_length=6)


def compare(judgments,predictions):
    eligible=[j for j in judgments if j['status']=='judged']
    actual={(j['item_id'],f) for j in eligible for f in j['features']}
    ids={j['item_id'] for j in eligible}
    outputs={}
    for model,pairs in predictions.items():
        proposed={(i,f) for i,features in pairs.items() if i in ids for f in features}
        tp=len(actual&proposed);fp=len(proposed-actual);fn=len(actual-proposed)
        outputs[model]={'tp':tp,'fp':fp,'fn':fn,'precision':tp/(tp+fp) if tp+fp else None,
                        'recall':tp/(tp+fn) if tp+fn else None,
                        'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
    return {'participant_count':1,'judged_paragraphs':len(eligible),
            'unsure_paragraphs':len(judgments)-len(eligible),'models':outputs,
            'scope':'One participant’s reading judgments on supplied summaries, with model outputs hidden in the form. Not a satisfaction study, population accuracy estimate, or verification of complete works.'}


@router.post('/{token}')
def submit(token:str,payload:Submission):
    with LOCK:
        s=load(token)
        if s['revision']!=payload.expected_revision or s.get('submitted'):
            raise HTTPException(409,'This review changed or was already submitted.')
        ids=[j.item_id for j in payload.judgments]
        if len(set(ids))!=len(ids) or set(ids)!={i['id'] for i in s['items']}:
            raise HTTPException(422,'Judge each supplied paragraph exactly once.')
        if any(j.status not in ('judged','unsure') or len(j.features)!=len(set(j.features)) or
               any(f not in FEATURES for f in j.features) or (j.status=='unsure' and j.features)
               for j in payload.judgments):
            raise HTTPException(422,'Unknown or contradictory judgment.')
        judgments=[j.model_dump() for j in payload.judgments]
        s.update(judgments=judgments,result=compare(judgments,s['predictions']),submitted=True,
                 revision=s['revision']+1,submitted_at=datetime.now(timezone.utc).isoformat())
        staging=REVIEW_DIR/'state.next.json';staging.write_text(json.dumps(s,indent=2)+'\n');staging.replace(REVIEW_DIR/'state.json')
        (REVIEW_DIR/'RESULTS.json').write_text(json.dumps(s['result'],indent=2)+'\n')
        return s['result']
