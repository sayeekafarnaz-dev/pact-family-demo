from fastapi.testclient import TestClient

from app import app


def test_family_benchmark_and_public_decision_use_same_synthetic_household():
    client = TestClient(app)
    portfolio = client.get('/api/public/portfolio').json()
    summary = portfolio['summary']
    assert portfolio['currency'] == 'USD'
    assert portfolio['total'] == summary['investments'] == 113_900
    assert summary['net_worth'] == 192_900
    assert summary['annual_income'] == 87_460

    options = client.get('/api/public/decision/options').json()
    assert {person['name'] for person in options['members']} == {'Daniel', 'Amira', 'Maya'}
    response = client.post('/api/public/decision', json={'event': 'retirement', 'member_id': 'father'})
    assert response.status_code == 200
    decision = response.json()
    assert decision['family_terminal_change'] < 0
    assert decision['methodology']['paths'] == 1000
    assert decision['members'][0]['scenario_risk_capacity'] == .065
    assert client.post('/api/public/decision', json={'event': 'education', 'member_id': 'father'}).status_code == 400
    assert client.get('/api/snapshot').status_code == 401
