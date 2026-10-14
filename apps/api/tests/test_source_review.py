import json

from fastapi.testclient import TestClient
from recros_api import db,source_review
from recros_api.main import app


def prepare(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.db')
    monkeypatch.setattr(source_review,'REVIEW_DIR',tmp_path)
    (tmp_path/'token.txt').write_text('fixture-token')
    state={'revision':0,'submitted':False,
           'items':[{'id':str(i),'domain':'book','evidence_text':'Synthetic fixture, not a human label.'} for i in range(6)],
           'predictions':{'fixture_model':{str(i):['inquiry'] for i in range(6)}}}
    (tmp_path/'state.json').write_text(json.dumps(state))


def test_review_hides_predictions_and_does_not_accept_default_or_duplicate_answers(tmp_path,monkeypatch):
    prepare(tmp_path,monkeypatch)
    with TestClient(app) as c:
        route='/api/source-review/fixture-token'
        result=c.get(route)
        assert result.status_code==200 and 'predictions' not in result.json()
        assert c.get('/api/source-review/wrong').status_code==404
        payload={'expected_revision':0,'judgments':[{'item_id':str(i),'status':'','features':[]} for i in range(6)]}
        assert c.post(route,json=payload).status_code==422
        for r in payload['judgments']:r['status']='judged'
        payload['judgments'][-1]['item_id']='0'
        assert c.post(route,json=payload).status_code==422
        assert json.loads((tmp_path/'state.json').read_text())['revision']==0


def test_unsure_is_excluded_and_submitted_review_cannot_be_overwritten(tmp_path,monkeypatch):
    prepare(tmp_path,monkeypatch)
    with TestClient(app) as c:
        route='/api/source-review/fixture-token'
        payload={'expected_revision':0,'judgments':[{'item_id':str(i),'status':'judged','features':['inquiry']} for i in range(6)]}
        payload['judgments'][-1].update(status='unsure',features=[])
        r=c.post(route,json=payload)
        assert r.status_code==200
        assert r.json()['judged_paragraphs']==5 and r.json()['unsure_paragraphs']==1
        assert r.json()['models']['fixture_model']['tp']==5
        assert c.post(route,json=payload).status_code==409
