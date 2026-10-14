"""Private local evidence audit and user-authored clarification record."""
from __future__ import annotations

from datetime import datetime, timezone
import hmac
import json
from pathlib import Path
import threading

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .contrast_audit import audit
from .reason_guard import observations, assess

CASE_DIR = Path(__file__).resolve().parents[3] / 'apps/api/data/personal-case'
router = APIRouter(prefix='/api/personal-case')
LOCK = threading.Lock()
REASON_KEYS = {'hail_mary','horror_contrast','books','songs','transfer'}


def load(token):
    try:
        expected = (CASE_DIR/'access-token.txt').read_text().strip()
        if not hmac.compare_digest(token,expected):
            raise HTTPException(404,'Case not found')
        return json.loads((CASE_DIR/'profile.json').read_text())
    except OSError as exc:
        raise HTTPException(404,'Case not found') from exc


def view(profile):
    try:
        annotated = json.loads((CASE_DIR/'items.annotated.json').read_text())
    except OSError as exc:
        raise HTTPException(503,'The item annotation cache is not ready') from exc
    runs = annotated.get('annotation_runs') or [annotated['annotation_run']]
    provenance = [{k:run[k] for k in
                   ('requested_model','prompt_sha256','source_sha256','verification_scope')}
                  | {'retained_item_ids':run.get('retained_item_ids', [i['id'] for i in annotated['items']])}
                  for run in runs]
    return {'profile':profile,'audit':audit(profile,annotated),
            'reason_evidence':observations(profile, reason_ledger()),
            'annotation_provenance':provenance[0], 'annotation_runs':provenance}


def reason_ledger():
    path = CASE_DIR/'reason-observations.json'
    return json.loads(path.read_text()) if path.exists() else {'observations': []}


@router.get('/{token}')
def read_case(token: str):
    with LOCK:
        return view(load(token))


class TransferRehearsal(BaseModel):
    expected_revision: int = Field(ge=0)
    observation_id: str = Field(min_length=1, max_length=100)
    target_id: str = Field(min_length=1, max_length=200)
    intent_confirmed: bool = False


@router.post('/{token}/transfer-rehearsal')
def rehearse(token: str, payload: TransferRehearsal):
    with LOCK:
        profile = load(token)
        if profile['revision'] != payload.expected_revision:
            raise HTTPException(409,'The case changed. Reload before rehearsing.')
        try:
            return assess(profile, reason_ledger(), payload.observation_id,
                          payload.target_id, payload.intent_confirmed)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc


class Clarification(BaseModel):
    expected_revision: int = Field(ge=0)
    reasons: dict[str,str] = Field(default_factory=dict,max_length=5)
    confirm_identities: list[str] = Field(default_factory=list,max_length=10)


@router.post('/{token}/clarifications')
def clarify(token: str, payload: Clarification):
    with LOCK:
        profile = load(token)
        if profile['revision'] != payload.expected_revision:
            raise HTTPException(409,'The case changed. Reload before saving.')
        if set(payload.reasons)-REASON_KEYS or any(len(v)>1500 for v in payload.reasons.values()):
            raise HTTPException(422,'Unknown or oversized clarification field')
        ids = {i['id'] for i in profile['items']}
        if set(payload.confirm_identities)-ids:
            raise HTTPException(422,'Unknown work identity')
        profile['reasons'].update({k:v.strip() for k,v in payload.reasons.items()})
        for item in profile['items']:
            if item['id'] in payload.confirm_identities:
                item['identity_status']='matched'
                item['identity_confirmation']='user confirmed'
        old = load(token)
        archive = CASE_DIR/'revisions'
        archive.mkdir(exist_ok=True)
        (archive/f'{old["revision"]}.json').write_text(json.dumps(old,indent=2)+'\n')
        profile['revision']+=1
        profile['updated_at']=datetime.now(timezone.utc).isoformat()
        staging=CASE_DIR/'profile.next.json'
        staging.write_text(json.dumps(profile,indent=2)+'\n')
        staging.replace(CASE_DIR/'profile.json')
        return view(profile)
