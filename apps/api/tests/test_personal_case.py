import json

from fastapi.testclient import TestClient

from recros_api import db, personal_case
from recros_api.main import app
from recros_api.reason_guard import text_hash


def test_private_case_token_revision_and_explicit_identity_confirmation(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.db')
    monkeypatch.setattr(personal_case,'CASE_DIR',tmp_path)
    (tmp_path/'access-token.txt').write_text('test-token')
    profile={'items':[{'id':'music:test','title':'Test','domain':'music','description':'',
                       'identity_status':'pending','preference_label':'dislike'}],
             'reasons':{},'revision':0}
    (tmp_path/'profile.json').write_text(json.dumps(profile))
    (tmp_path/'items.annotated.json').write_text(json.dumps({'items':profile['items'],
        'annotation_run':{k:'test' for k in ('requested_model','prompt_sha256','source_sha256','verification_scope')}}))
    with TestClient(app) as c:
        assert c.get('/api/personal-case/wrong').status_code==404
        assert c.get('/api/personal-case/test-token').json()['audit']['pending_identity_ids']==['music:test']
        payload={'expected_revision':0,'reasons':{'horror_contrast':'Automated fixture, not a human answer'},
                 'confirm_identities':['music:test']}
        result=c.post('/api/personal-case/test-token/clarifications',json=payload)
        assert result.status_code==200
        assert result.json()['profile']['revision']==1
        assert result.json()['audit']['pending_identity_ids']==[]
        assert c.post('/api/personal-case/test-token/clarifications',json=payload).status_code==409
        assert c.post('/api/personal-case/test-token/clarifications',json={**payload,'expected_revision':1,'reasons':{'invented':'test'}}).status_code==422
        assert (tmp_path/'revisions/0.json').exists()


def test_rehearsal_checks_revision_but_does_not_save_intent_or_rating(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.db')
    monkeypatch.setattr(personal_case,'CASE_DIR',tmp_path)
    (tmp_path/'access-token.txt').write_text('test-token')
    reason='Synthetic fixture: I liked the pacing.'
    profile={'items':[
        {'id':'source','title':'Source','domain':'movie','identity_status':'matched'},
        {'id':'target','title':'Target','domain':'book','identity_status':'matched'}],
        'reasons':{'hail_mary':reason},'revision':2}
    path=tmp_path/'profile.json'; path.write_text(json.dumps(profile)); before=path.read_bytes()
    ledger={'observations':[{'id':'pacing','item_id':'source','reason_key':'hail_mary',
        'quote':'I liked the pacing','source_sha256':text_hash(reason),'criterion':'pacing',
        'experience':'positive','interpretation_status':'proposed','evidence_question':'Inspect pacing.'}]}
    (tmp_path/'reason-observations.json').write_text(json.dumps(ledger))
    payload={'expected_revision':2,'observation_id':'pacing','target_id':'target','intent_confirmed':True}
    with TestClient(app) as c:
        assert c.post('/api/personal-case/wrong/transfer-rehearsal',json=payload).status_code==404
        route='/api/personal-case/test-token/transfer-rehearsal'
        assert c.post(route,json={**payload,'expected_revision':1}).status_code==409
        result=c.post(route,json=payload)
        assert result.status_code==200
        assert result.json()['next_action']=='inspect_target'
        assert path.read_bytes()==before
        assert not (tmp_path/'revisions').exists()


def test_composite_annotation_runs_keep_item_membership(tmp_path,monkeypatch):
    monkeypatch.setattr(personal_case,'CASE_DIR',tmp_path)
    run={k:'test' for k in ('requested_model','prompt_sha256','source_sha256','verification_scope')}
    cache={'items':[], 'annotation_runs':[{**run,'retained_item_ids':['source']},
                                         {**run,'retained_item_ids':['corrected-target']}]}
    (tmp_path/'items.annotated.json').write_text(json.dumps(cache))
    v=personal_case.view({'items':[],'reasons':{}})
    assert [r['retained_item_ids'] for r in v['annotation_runs']]==[['source'],['corrected-target']]
