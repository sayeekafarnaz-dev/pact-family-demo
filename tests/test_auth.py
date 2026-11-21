import pytest
from fastapi.testclient import TestClient

import app as pact_app

PASSWORD = 'test-only-password'  # synthetic test value, not a real credential


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('PACT_DEMO_PASSWORD', PASSWORD)
    monkeypatch.delenv('PACT_SESSION_SECRET', raising=False)
    return TestClient(pact_app.app)


def login(client, password=PASSWORD):
    return client.post('/login', data={'password': password}, follow_redirects=False)


def test_health_is_public(client):
    r = client.get('/health')
    assert r.status_code == 200 and r.json() == {'status': 'ok'}


@pytest.mark.parametrize('path', ['/api/snapshot', '/api/tax', '/api/source', '/api/decisions/events'])
def test_api_requires_auth(client, path):
    assert client.get(path).status_code == 401


def test_post_api_requires_auth(client):
    r = client.post('/api/decisions/compare', json={'event': 'retirement', 'member_id': 'father', 'paths': 200, 'years': 3})
    assert r.status_code == 401
    assert client.post('/api/reset').status_code == 401


def test_dashboard_and_static_redirect_to_login(client):
    for path in ['/', '/static/index.html']:
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 303 and r.headers['location'] == '/login'


def test_wrong_password_rejected(client):
    r = login(client, 'wrong')
    assert r.status_code == 401
    assert 'pact_session' not in r.cookies
    assert client.get('/api/snapshot').status_code == 401


def test_login_grants_access_and_logout_revokes(client):
    r = login(client)
    assert r.status_code == 303
    cookie = r.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'samesite=strict' in cookie
    assert client.get('/').status_code == 200
    assert client.get('/api/snapshot').json()['kind'] == 'SYNTHETIC DEMONSTRATION'
    d = client.post('/api/decisions/compare', json={'event': 'retirement', 'member_id': 'father', 'paths': 200, 'years': 3})
    assert d.status_code == 200
    client.post('/logout', follow_redirects=False)
    assert client.get('/api/snapshot').status_code == 401


def test_forged_or_expired_token_rejected(client):
    assert not pact_app.valid_session('9999999999.deadbeef')
    assert not pact_app.valid_session('garbage')
    expired = pact_app.make_session_token(now=0)
    assert not pact_app.valid_session(expired)
    assert pact_app.valid_session(pact_app.make_session_token())


def test_password_rotation_invalidates_sessions(client, monkeypatch):
    token = pact_app.make_session_token()
    monkeypatch.setenv('PACT_DEMO_PASSWORD', 'rotated-test-password')
    assert not pact_app.valid_session(token)


def test_fails_closed_without_password(monkeypatch):
    monkeypatch.delenv('PACT_DEMO_PASSWORD', raising=False)
    c = TestClient(pact_app.app)
    assert c.get('/health').status_code == 200
    assert c.get('/api/snapshot').status_code == 401
    assert c.post('/login', data={'password': ''}, follow_redirects=False).status_code == 503
