import sqlite3

import pytest
from fastapi.testclient import TestClient

from recros_api import db, familiarity
from recros_api.main import app


@pytest.fixture
def client(tmp_path,monkeypatch):
    catalog=tmp_path/'catalog.db'
    with sqlite3.connect(catalog) as c:
        c.execute('CREATE TABLE works(id TEXT,domain TEXT,title TEXT,creators TEXT,year TEXT,description TEXT,genres TEXT)')
        c.execute("INSERT INTO works VALUES ('movie:test','movie','Known Example','A Creator','2000','A description.','Mystery')")
        c.execute('CREATE VIRTUAL TABLE search USING fts5(title,creators,content=works,content_rowid=rowid)')
        c.execute("INSERT INTO search(search) VALUES ('rebuild')")
    monkeypatch.setattr(familiarity,'CATALOG_DB',catalog)
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'profile.db')
    with TestClient(app) as c: yield c


def test_title_search_and_domain_filter(client):
    assert client.get('/api/familiar/search',params={'q':'Known','domain':'movie'}).json()['items'][0]['id']=='movie:test'
    assert client.get('/api/familiar/search',params={'q':'Known','domain':'book'}).json()['items']==[]
    assert client.get('/api/familiar/search',params={'q':'" OR *'}).status_code==200
    assert client.get('/familiar').status_code==200


def test_local_profile_uses_catalog_identity_and_marks_missing_titles(client):
    p={'works':[{'id':'movie:test','title':'Untrusted title','domain':'movie','familiarity':'consumed','liking':4},
                {'title':'Absent Song','domain':'music','familiarity':'consumed','liking':2}]}
    s=client.post('/api/familiar/profiles',json=p)
    assert s.status_code==200
    data=client.get('/api/familiar/profiles/'+s.json()['token']).json()
    assert data['works'][0]['title']=='Known Example'
    assert data['works'][1]['evidence_status']=='unresolved_title_needs_source'
    assert client.get('/api/familiar/profiles/invalid').status_code==404
    assert client.post('/api/familiar/profiles',json={'works':[p['works'][0],p['works'][0]]}).status_code==422
