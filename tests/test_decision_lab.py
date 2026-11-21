import copy
import pytest
from engine import DEFAULT
from decision_lab import compare_decision


def test_paired_scenarios_repeat_exactly():
    a = compare_decision(DEFAULT, 'retirement', 'father', years=8, paths=500, seed=42)
    b = compare_decision(DEFAULT, 'retirement', 'father', years=8, paths=500, seed=42)
    assert a == b
    assert a['optimisation']['after_status'] == 'feasible'
    assert a['members'][0]['scenario_risk_capacity'] < a['members'][0]['before_risk_capacity']


def test_education_cost_reduces_wealth_and_does_not_mutate_data():
    data = copy.deepcopy(DEFAULT)
    earlier = copy.deepcopy(data)
    result = compare_decision(data, 'education', 'mother', amount=60000, years=7, paths=800)
    assert result['family_terminal_change'] < 0
    mother = next(m for m in result['members'] if m['id']=='mother')
    assert mother['terminal_change'] < 0
    assert data == earlier
    assert result['methodology']['goal_evaluation'].startswith('Each member goal')


def test_income_disruption_is_explicitly_event_driven():
    r = compare_decision(DEFAULT, 'job_loss', 'child', years=5, paths=700)
    assert r['family_terminal_change'] < 0
    assert next(m for m in r['members'] if m['id']=='child')['scenario_risk_capacity'] <= .08


def test_rejects_invalid_event_and_negative_or_missing_cost():
    with pytest.raises(ValueError):
        compare_decision(DEFAULT, 'magic', 'father')
    with pytest.raises(ValueError):
        compare_decision(DEFAULT, 'education', 'father', amount=0)
    with pytest.raises(ValueError):
        compare_decision(DEFAULT, 'retirement', 'nobody')
