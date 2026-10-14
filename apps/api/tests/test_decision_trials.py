import pytest
from fastapi.testclient import TestClient

from recros_api import db
from recros_api.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'trials.db')
    with TestClient(app) as c:
        yield c


def test_trial_revision_privacy_export_and_local_ratings(client):
    response = client.post('/api/decision/sessions', json={'seed_id':'movie:manchester','target':'music','mode':'personal'})
    assert response.status_code == 200
    s = response.json()
    root = '/api/decision/sessions/' + s['token']
    assert s['candidates'] == [{'alias':'A'}, {'alias':'B'}]
    assert client.get(root+'/export').status_code == 409
    assert client.get('/api/decision/sessions/not-the-token').status_code == 404
    s = client.post(root+'/actions', json={'kind':'ask_user','answer':'friendship','expected_revision':0}).json()
    assert client.post(root+'/actions', json={'kind':'inspect_evidence','expected_revision':0}).status_code == 409
    assert client.post(root+'/actions', json={'kind':'ask_user','answer':'friendship','expected_revision':1}).status_code == 400
    s = client.post(root+'/actions', json={'kind':'inspect_evidence','expected_revision':1}).json()
    assert all(i['quote'] in i['description'] for i in s['candidates'])
    s = client.post(root+'/actions', json={'kind':'recommend','item':s['suggested']['item'],'expected_revision':2}).json()
    assert s['suggested']['loss'] == 0
    # Automated fixtures in an isolated temporary DB, never human-study records.
    payload = {'expected_revision':3,'A':{'interest':2,'familiarity':'unfamiliar'},
               'B':{'interest':4,'familiarity':'familiar'},'theme_fit':'partly','feedback':'automated test'}
    assert client.post(root+'/ratings', json=payload).status_code == 200
    assert client.post(root+'/ratings', json={**payload,'expected_revision':4}).status_code == 409
    export = client.get(root+'/export').json()
    assert export['participant_count_claim'] is None
    assert export['ratings']['B']['interest'] == 4
    assert 'token' not in export


def test_none_choice_and_invalid_personal_setup(client):
    base = {'seed_id':'movie:manchester','target':'book','mode':'personal'}
    assert client.post('/api/decision/sessions', json={**base,'budget':1}).status_code == 422
    s = client.post('/api/decision/sessions', json=base).json()
    root = '/api/decision/sessions/' + s['token']
    s = client.post(root+'/actions', json={'kind':'ask_user','answer':'none','expected_revision':0}).json()
    assert s['status'] == 'outside_model'
    assert s['suggested']['certificate_valid'] is False
    assert s['suggested']['loss'] is None


def test_demo_serves_and_rejects_same_domain_and_invalid_known_preference(client):
    assert client.get('/decision').status_code == 200
    assert len(client.get('/api/decision/catalog').json()['items']) == 12
    assert client.post('/api/decision/sessions', json={'seed_id':'movie:manchester','target':'movie'}).status_code == 400
    assert client.post('/api/decision/sessions', json={'seed_id':'movie:manchester','target':'book','condition':'both_known'}).status_code == 400
