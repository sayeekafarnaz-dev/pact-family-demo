"""PACT Decision Lab: synthetic, reproducible, event-conditioned family analysis.

The calculations use illustrative asset-class parameters. Nothing is investment advice.
"""
from __future__ import annotations
import copy
import numpy as np
from engine import COV, MU, balance, holdings, optimize, snapshot, portfolio_vol

EVENTS = {
    'retirement': 'Member retires next year',
    'education': 'Education cost next year',
    'job_loss': 'One-year income disruption',
    'major_purchase': 'One-time family purchase',
}


def _run_paths(data, years: int, paths: int, seed: int, event: str | None = None,
               member_id: str | None = None, amount: float = 0.0):
    rng = np.random.default_rng(seed)
    shocks = rng.multivariate_normal(MU, COV, size=(years, paths), check_valid='raise')
    member_results = {}
    family_wealth = np.zeros(paths)
    for member in data['members']:
        current = np.full(paths, balance(member), dtype=float)
        at_goal = None
        goal = member['goals'][0] if member['goals'] else None
        due = min(years, max(1, int(goal['years']))) if goal else years
        depleted = np.zeros(paths, dtype=bool)
        for year in range(1, years + 1):
            # Year 1 starts at present age; normal retirement at the beginning of the year the member reaches retirement age.
            age = member['age'] + year - 1
            retired = age >= member['retire_age'] or (
                event == 'retirement' and member['id'] == member_id and year >= 1
            )
            cashflow = (member['retirement_income'] - member['retirement_spending']) if retired else (member['income'] - member['expenses'])
            if member['id'] == member_id and year == 1:
                if event == 'job_loss' and not retired:
                    cashflow -= member['income']
                elif event in ('education', 'major_purchase'):
                    cashflow -= amount
            cashflow *= 1.025 ** (year-1)
            yearly_return = np.maximum(-0.99, shocks[year-1] @ holdings(member))
            raw = current * (1 + yearly_return) + cashflow
            depleted |= raw < 0
            current = np.maximum(0, raw)
            if year == due:
                at_goal = current.copy()
        family_wealth += current
        member_results[member['id']] = {
            'name': member['name'],
            'goal': goal['name'] if goal else None,
            'goal_due_year': int(goal['years']) if goal else None,
            'goal_evaluation_year': due,
            'goal_probability': round(float(np.mean(at_goal >= goal['target'])), 4) if goal else None,
            'terminal_median': round(float(np.median(current)), 2),
            'terminal_p10': round(float(np.quantile(current, 0.1)), 2),
            'terminal_p90': round(float(np.quantile(current, 0.9)), 2),
            'depletion_probability': round(float(np.mean(depleted)), 4),
        }
    return {'members': member_results,
            'family': {'terminal_median': round(float(np.median(family_wealth)), 2),
                       'terminal_p10': round(float(np.quantile(family_wealth, .1)), 2),
                       'terminal_p90': round(float(np.quantile(family_wealth, .9)), 2)},
            'seed': seed, 'paths': paths, 'years': years}


def compare_decision(data, event: str, member_id: str, amount: float = 0,
                     years: int = 20, paths: int = 5000, seed: int = 26011):
    if event not in EVENTS:
        raise ValueError('Unsupported event')
    if member_id not in {m['id'] for m in data['members']}:
        raise ValueError('Unknown family member')
    if not 1 <= years <= 40 or not 100 <= paths <= 50000:
        raise ValueError('Simulation parameters out of range')
    if not 0 <= amount <= 1e9:
        raise ValueError('Event cost must be between zero and 1 billion')
    if event in ('education', 'major_purchase') and amount == 0:
        raise ValueError('Enter a positive event cost')

    # Identical random seed and shocks are used for both sides (common random numbers).
    baseline = _run_paths(data, years, paths, seed)
    scenario = _run_paths(data, years, paths, seed, event, member_id, amount)
    adjusted = copy.deepcopy(data)
    impacted = next(m for m in adjusted['members'] if m['id'] == member_id)
    if event == 'retirement':
        # Illustrative capacity adjustment, not an assessed suitability rule.
        impacted['risk_capacity'] = min(impacted['risk_capacity'], .065)
        impacted['target_vol'] = min(impacted['target_vol'], .065)
    elif event == 'job_loss':
        impacted['risk_capacity'] = min(impacted['risk_capacity'], .08)
        impacted['target_vol'] = min(impacted['target_vol'], .08)

    before_opt = optimize(data)
    after_opt = optimize(adjusted)
    differences = []
    for member in data['members']:
        mid = member['id']
        a, b = baseline['members'][mid], scenario['members'][mid]
        differences.append({
            'id': mid, 'name': member['name'],
            'event_subject': mid == member_id,
            'before_terminal_median': a['terminal_median'],
            'after_terminal_median': b['terminal_median'],
            'terminal_change': round(b['terminal_median'] - a['terminal_median'], 2),
            'goal_before': a['goal_probability'], 'goal_after': b['goal_probability'],
            'goal_due_year': a['goal_due_year'],
            'depletion_before': a['depletion_probability'],
            'depletion_after': b['depletion_probability'],
            'before_risk_capacity': member['risk_capacity'],
            'scenario_risk_capacity': next(x['risk_capacity'] for x in adjusted['members'] if x['id'] == mid),
        })

    return {
        'kind': 'SYNTHETIC RESEARCH SCENARIO — NOT A FORECAST OR INVESTMENT ADVICE',
        'event': event, 'event_description': EVENTS[event], 'member_id': member_id,
        'amount': amount if event in ('education', 'major_purchase') else None,
        'before': baseline['family'], 'after': scenario['family'],
        'family_terminal_change': round(scenario['family']['terminal_median'] - baseline['family']['terminal_median'], 2),
        'members': differences,
        'optimisation': {
            'before_status': before_opt['status'], 'after_status': after_opt['status'],
            'before_family_volatility': before_opt['family_proposed_volatility'],
            'after_family_volatility': after_opt['family_proposed_volatility'],
            'before_allocations': {m['id']: m['proposed'] for m in before_opt['members']},
            'after_allocations': {m['id']: m['proposed'] for m in after_opt['members']},
        },
        'methodology': {
            'paths': paths, 'years': years, 'seed': seed,
            'return_model': 'Annual correlated multivariate normal asset-class shocks; illustrative MU and COV v1',
            'pairing': 'Identical Monte Carlo market paths on each side to reduce simulation noise',
            'account_aggregation': 'Account-balance-weighted member holdings; no cross-member transfers',
            'goal_evaluation': 'Each member goal evaluated at the earlier of its due date and the simulation horizon',
            'cashflows': 'Annual cash flow increases by illustrative 2.5%; event costs occur in year one',
            'retirement_capacity': 'For demonstration only, cap event member risk target/capacity at 6.5% annualised volatility',
            'solver': 'Joint constrained mean-variance SLSQP, no account-level tax-lot optimisation',
            'limits': ['No actual tax or transaction costs', 'No salary or mortality uncertainty',
                       'No market-data calibration', 'No authenticated family consent or account privacy',
                       'No security-level trades or real brokerage connectivity',
                       'Comparisons are analytical scenarios, not personalised investment recommendations'],
        }
    }
