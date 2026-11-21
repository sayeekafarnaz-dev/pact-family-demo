import copy
import numpy as np
from engine import DEFAULT,snapshot,simulate,optimize,holdings,portfolio_vol,tax_insights

def test_net_worth_and_cashflow():
 s=snapshot(DEFAULT)
 assert s['net_worth']==s['assets']-s['liabilities']
 assert s['surplus']==s['annual_income']-s['annual_expenses']
 assert abs(sum(s['allocation'])-1)<1e-5

def test_member_account_aggregation():
 for m in DEFAULT['members']:
  w=holdings(m)
  assert abs(sum(w)-1)<1e-10
  assert np.isclose(portfolio_vol(w)**2,w @ __import__('engine').COV @ w)

def test_simulation_reproducibility_and_sensitivity():
 a=simulate(DEFAULT,5,5000,seed=13)
 b=simulate(DEFAULT,5,5000,seed=13)
 assert a==b
 assert simulate(DEFAULT,5,5000,seed=13,market_crash=True)['family']['median'] < a['family']['median']

def test_optimization_constraints():
 r=optimize(DEFAULT)
 assert r['status']=='feasible',r['solver_message']
 assert r['family_proposed_volatility']<=r['family_target_volatility']+1e-4
 for m in r['members']:
  assert abs(sum(m['proposed'])-1)<1e-3
  assert m['proposed_volatility']<=m['limit']+1e-4

def test_tax_does_not_claim_savings_without_data():
 t=tax_insights(DEFAULT)
 assert t['tax_savings'] is None
 assert all('not calculated' in x['status'] for x in t['insights'])

def test_new_member_zero_accounts():
 d=copy.deepcopy(DEFAULT)
 d['members'].append({'id':'new','name':'New','relation':'Other','age':40,'retire_age':67,'income':0,'expenses':0,'liabilities':0,'liquid_cash':0,'target_vol':.1,'risk_capacity':.1,'risk_tolerance':'Unassessed','retirement_income':0,'retirement_spending':0,'accounts':[],'goals':[{'name':'General','target':0,'years':10}]})
 assert snapshot(d)['members'][-1]['investments']==0
