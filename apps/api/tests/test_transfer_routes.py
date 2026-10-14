from fastapi.testclient import TestClient

from recros_api import db, transfer_routes
from recros_api.main import app
from recros_api.transfer_engine import text_hash


def fixture_catalog(n=12):
    text='Synthetic fixture: an investigator searches for answers in an ominous setting.'
    return {'items':[{'id':f'book:{n:02}','domain':'book','title':f'Fixture {n}',
                      'source_url':'https://example.org/fixture','evidence_text':text,
                      'annotation':{'evidence_sha256':text_hash(text),
                                    'claims':[{'feature':'inquiry','quote':'an investigator searches for answers'}]}}
                     for n in range(n)],'annotation_run':{'requested_model':'synthetic fixture'},
            'selection':'Synthetic automated fixture, not a participant record.'}


def test_large_bank_has_fixed_shortlist_and_removal_preserves_it(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.db')
    monkeypatch.setattr(transfer_routes,'catalog',lambda:fixture_catalog())
    with TestClient(app) as c:
        payload={'source_id':'movie:stand-by-me','target_domain':'book','goals':['inquiry']}
        route='/api/transfer/discover'
        before=c.post(route,json=payload).json()
        assert before['kind']=='recommend'
        assert before['retrieval_counts']=={'evidence_bank_candidates':12,'shortlist':8}
        ids=[r['id'] for r in before['candidates']]
        after=c.post(route,json={**payload,'removed':{'item_id':before['item_id'],'feature':'inquiry'}}).json()
        assert after['intervention']['changed_choice']
        assert sorted(ids)==sorted(r['id'] for r in after['candidates'])
        assert c.post(route,json={**payload,'target_domain':'movie'}).status_code==200
        assert c.post(route,json={**payload,'goals':['invented']}).status_code==422


def test_credits_only_invalidates_claims_and_private_tokens_are_checked(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.db')
    monkeypatch.setattr(transfer_routes,'catalog',lambda:fixture_catalog())
    monkeypatch.setattr(transfer_routes.personal_case,'CASE_DIR',tmp_path)
    (tmp_path/'access-token.txt').write_text('correct')
    with TestClient(app) as c:
        payload={'source_id':'movie:stand-by-me','target_domain':'book','goals':['inquiry'],
                 'evidence_mode':'credits_only'}
        r=c.post('/api/transfer/discover',json=payload)
        assert r.status_code==200 and r.json()['kind']=='abstain'
        assert all(not i['evidence'] for i in r.json()['candidates'])
        assert c.post('/api/transfer/discover',json={**payload,'case_token':'wrong'}).status_code==404


def test_no_intent_causes_no_recommendation_or_rating_write(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.db')
    monkeypatch.setattr(transfer_routes,'catalog',lambda:fixture_catalog())
    with TestClient(app) as c:
        r=c.post('/api/transfer/discover',json={'source_id':'movie:stand-by-me','target_domain':'book','goals':[]})
        assert r.status_code==200 and r.json()['kind']=='ask_user'
        assert not r.json()['candidates']


def test_student_mode_is_explicit_and_declares_teacher_evidence_dependency(tmp_path,monkeypatch):
    import json
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.db')
    monkeypatch.setattr(transfer_routes,'ROOT',tmp_path)
    monkeypatch.setattr(transfer_routes,'catalog',lambda:fixture_catalog(2))
    monkeypatch.setattr(transfer_routes,'public_anchors',lambda:[{'id':'movie:fixture','title':'Fixture source','domain':'movie'}])
    path=tmp_path/'apps/api/data/scaled-transfer/student.annotated.json';path.parent.mkdir(parents=True)
    path.write_text(json.dumps(fixture_catalog(2)))
    monkeypatch.setattr(transfer_routes,'interpret_with_student',lambda items:(items,{'parameter_count':1,'device':'synthetic fixture'}))
    with TestClient(app) as c:
        payload={'source_id':'movie:fixture','target_domain':'book','goals':['inquiry'],'extractor':'student'}
        result=c.post('/api/transfer/discover',json=payload)
        assert result.status_code==200 and result.json()['extractor']=='student'
        assert 'cached teacher' in result.json()['student_scope']
        assert c.post('/api/transfer/discover',json={**payload,'extractor':'unknown'}).status_code==422
