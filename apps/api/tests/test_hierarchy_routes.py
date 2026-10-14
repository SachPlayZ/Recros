from fastapi.testclient import TestClient
import re

from recros_api import db,hierarchy_routes
from recros_api.main import app


def test_public_hierarchy_probe_is_conditional_and_does_not_record_feedback(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'demo.db')
    sample={'selection':'Post hoc constructed test fixture.','state':{'id':'unit','source':{'id':'fixture','title':'Fixture','domain':'movie'},
            'target_domain':'book','request_pairs':[{'prefer':'Broad','avoid':'Subtype'}],
            'features':['Broad','Subtype'],'edges':[(1,0)],'lower':[1,-1],'upper':[1,-1],
            'observed':[[None,None],[0,0]],'candidates':[{'id':'a','title':'Unknown fixture','domain':'book'},{'id':'b','title':'Neutral fixture','domain':'book'}]}}
    monkeypatch.setattr(hierarchy_routes,'demos',lambda:[sample])
    with TestClient(app) as client:
        assert client.get('/api/hierarchy/toy').json()['coherent_gap']==0
        assert client.get('/api/hierarchy/toy?budget=1').json()['fault_bound']==1
        assert client.get('/api/hierarchy/toy?budget=3').status_code==422
        result=client.get('/api/hierarchy/case/unit').json()
        assert result['candidates'][0]['exact_regret']==0
        assert result['candidates'][0]['flat_bound']==1
        assert result['candidates'][0]['flat_witness']['broken_hierarchy_relations']
        assert result['candidates'][0]['fault_bound']==0
        assert client.get('/api/hierarchy/case/unit?budget=1').json()['candidates'][0]['fault_bound']==1
        assert client.get('/api/hierarchy/case/private-token').status_code==404
        page=client.get('/hierarchy');assert page.status_code==200
        for asset in re.findall(r'(?:src|href)="(/[^" ]+\.(?:js|css))"',page.text):
            assert client.get(asset).status_code==200
        with db.get_conn() as conn:
            assert conn.execute('SELECT count(*) FROM decision_sessions').fetchone()[0]==0
            assert conn.execute('SELECT count(*) FROM users').fetchone()[0]==0
