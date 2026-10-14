from pathlib import Path
import tempfile

import pytest
from fastapi.testclient import TestClient

from recros_api import db
from recros_api.main import app
from recros_api.recommender import recommend_with_trace, update_profile


@pytest.fixture
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setattr(db, 'DB_PATH', Path(directory) / 'test.db')
        with TestClient(app) as instance:
            yield instance


def test_authenticated_comparison_and_single_domain_fills_list(client):
    with db.get_conn() as conn:
        conn.executemany('INSERT INTO items(id, domain, title, genres, popularity, rating) VALUES (?, ?, ?, ?, ?, ?)',
                         [(f'movie:{i}', 'movie', f'Film {i}', 'Adventure', i, 8) for i in range(10)])
    created = client.post('/api/users').json()
    user = created['user_id']
    headers = {'Authorization': f"Bearer {created['token']}"}
    assert client.get(f'/api/users/{user}/compare').status_code == 401
    response = client.get(f'/api/users/{user}/compare?limit=10&domain=movie', headers=headers)
    assert response.status_code == 200
    for policy in response.json().values():
        assert len(policy['items']) == 10
        assert policy['certificate']['predicted_loss_fraction'] <= policy['certificate']['budget'] + 1e-10


def test_disliked_terms_are_excluded(client):
    with db.get_conn() as conn:
        conn.execute("INSERT INTO items(id, domain, title, genres, popularity) VALUES ('movie:1', 'movie', 'The Giant', 'Horror', 100)")
    user, _ = db.create_user()
    update_profile(user, {'disliked_terms': ['horror']})
    assert recommend_with_trace(user)['items'] == []


def test_lab_invalid_requests(client):
    assert client.get('/api/lab/bridges?seed=x&target=invalid').status_code == 422
    assert client.get('/api/lab/bridges?seed=x&remove=unknown').status_code == 422


def test_cached_real_catalog_and_ablation(client):
    catalog = client.get('/api/lab/catalog').json()
    assert not catalog['synthetic']
    assert len(catalog['items']) == 12
    assert all(item['source_url'].startswith('https://') for item in catalog['items'])
    before = client.get('/api/lab/bridges?seed=movie:manchester&target=book').json()['items']
    assert before[0]['id'] == 'book:grief-observed'
    assert before[0]['bridge_score'] > 0
    after = client.get('/api/lab/bridges?seed=movie:manchester&target=book&remove=grief%20and%20loss').json()['items']
    assert all(item['bridge_score'] == 0 for item in after)


@pytest.mark.parametrize('seed,target,expected', [
    ('movie:manchester', 'book', 'book:grief-observed'),
    ('movie:manchester', 'music', 'music:tears-in-heaven'),
    ('book:grief-observed', 'movie', 'movie:manchester'),
    ('book:grief-observed', 'music', 'music:tears-in-heaven'),
    ('music:tears-in-heaven', 'movie', 'movie:manchester'),
    ('music:tears-in-heaven', 'book', 'book:grief-observed'),
])
def test_all_six_cross_domain_directions(client, seed, target, expected):
    response = client.get('/api/lab/bridges', params={'seed': seed, 'target': target})
    assert response.status_code == 200
    payload = response.json()
    assert payload['model'] == 'deepseek/deepseek-v4-flash'
    assert payload['items'][0]['id'] == expected
    assert payload['items'][0]['evidence']
    assert all(item['domain'] == target for item in payload['items'])
