"""PACT demonstration calculation engine. All default records are SYNTHETIC."""
from __future__ import annotations
import copy
from typing import Any
import numpy as np
from scipy.optimize import minimize

CLASSES = ['US equity', 'International equity', 'Bonds', 'Cash']
# Illustrative annual nominal assumptions, NOT market forecasts.
MU = np.array([.075, .072, .038, .025])
VOL = np.array([.18, .20, .065, .008])
CORR = np.array([[1,.78,.12,0],[.78,1,.05,0],[.12,.05,1,.08],[0,0,.08,1.]])
COV = np.outer(VOL,VOL)*CORR
SEED = 26011
DEFAULT = {
 'family':'The Morgan Family', 'currency':'USD', 'kind':'SYNTHETIC DEMONSTRATION',
 'members':[
  {'id':'father','name':'Daniel','relation':'Father','age':63,'retire_age':67,'income':33700,'expenses':30400,'liabilities':4000,'liquid_cash':3000,'home_equity':79000,'target_vol':.085,'risk_tolerance':'Moderately conservative','risk_capacity':.095,'retirement_income':25200,'retirement_spending':28000,'accounts':[
   {'id':'f401k','name':'401(k)','tax':'Tax-deferred','balance':49000,'allocation':[.37,.10,.47,.06]},
   {'id':'fbroker','name':'Brokerage','tax':'Taxable','balance':15000,'allocation':[.49,.11,.25,.15]}],
   'goals':[{'name':'Retirement','target':65000,'years':5}]},
  {'id':'mother','name':'Amira','relation':'Mother','age':58,'retire_age':67,'income':33760,'expenses':29500,'liabilities':3000,'liquid_cash':3000,'target_vol':.12,'risk_tolerance':'Balanced','risk_capacity':.14,'retirement_income':23500,'retirement_spending':26600,'accounts':[
   {'id':'mira','name':'Traditional IRA','tax':'Tax-deferred','balance':24000,'allocation':[.48,.17,.31,.04]},
   {'id':'mroth','name':'Roth IRA','tax':'Tax-free*','balance':7900,'allocation':[.62,.25,.10,.03]}],
   'goals':[{'name':'Retirement','target':55000,'years':10}]},
  {'id':'child','name':'Maya','relation':'Adult child','age':31,'retire_age':65,'income':20000,'expenses':17600,'liabilities':1000,'liquid_cash':2000,'target_vol':.17,'risk_tolerance':'Moderately aggressive','risk_capacity':.19,'retirement_income':0,'retirement_spending':65000,'accounts':[
   {'id':'cbroker','name':'Brokerage','tax':'Taxable','balance':12000,'allocation':[.68,.24,.06,.02]},
   {'id':'croth','name':'Roth IRA','tax':'Tax-free*','balance':6000,'allocation':[.73,.22,.03,.02]}],
   'goals':[{'name':'Property deposit','target':30000,'years':6}]}],
 'family_target_vol':.125,
 'family_goal':{'name':'Long-term capital','target':250000,'years':15}
}

def balance(m): return sum(a['balance'] for a in m['accounts'])
def holdings(m):
 b=balance(m)
 return np.sum([a['balance']*np.asarray(a['allocation'],float) for a in m['accounts']],axis=0)/b if b else np.zeros(4)
def portfolio_vol(w): return float(np.sqrt(np.asarray(w) @ COV @ np.asarray(w)))
def portfolio_return(w): return float(np.asarray(w)@MU)
def money(v): return round(float(v),2)

def snapshot(data:dict):
 members=[]; total=np.zeros(4); bal=0; assets=liabilities=income=expenses=0
 for m in data['members']:
  b=balance(m); w=holdings(m); total+=w*b; bal+=b
  a=b+m['liquid_cash']+m.get('home_equity',0); debt=m['liabilities']; inc=m['income']; exp=m['expenses']
  assets+=a; liabilities+=debt; income+=inc; expenses+=exp
  members.append({'id':m['id'],'name':m['name'],'relation':m['relation'],'age':m['age'],
    'assets':money(a),'home_equity':money(m.get('home_equity',0)),'investments':money(b),'liabilities':money(debt),'net_worth':money(a-debt),
    'income':money(inc),'expenses':money(exp),'surplus':money(inc-exp),'cash':money(m['liquid_cash']),
    'liquidity_months':money(m['liquid_cash']/(exp/12)) if exp else None,
    'allocation':[round(float(x),6) for x in w], 'actual_volatility':round(portfolio_vol(w),6),
    'target_volatility':m['target_vol'],'risk_capacity':m['risk_capacity'],'risk_tolerance':m['risk_tolerance'],
    'accounts':m['accounts'],'goals':m['goals']})
 w=total/bal if bal else np.zeros(4)
 bytax={}
 for m in data['members']:
  for a in m['accounts']: bytax[a['tax']]=bytax.get(a['tax'],0)+a['balance']
 return {'family':data['family'],'kind':data['kind'],'currency':data['currency'],'members':members,
   'assets':money(assets),'liabilities':money(liabilities),'net_worth':money(assets-liabilities),
   'investments':money(bal),'annual_income':money(income),'annual_expenses':money(expenses),'surplus':money(income-expenses),
   'savings_rate':round((income-expenses)/income,6) if income else None,
   'allocation':[round(float(x),6) for x in w], 'actual_volatility':round(portfolio_vol(w),6),
   'expected_return_assumption':round(portfolio_return(w),6),'target_volatility':data['family_target_vol'],
   'tax_accounts':bytax,'asset_classes':CLASSES,'assumption_version':'illustrative-v1',
   'provenance':{'balances':'Synthetic accounts supplied with demonstration dataset',
      'volatility':'sqrt(wᵀΣw), with illustrative annual covariance matrix v1',
      'net_worth':'Sum member investment balances + member cash − liabilities',
      'returns':'Illustrative annual nominal return assumptions (not forecasts)',
      'ownership':'Demonstration accounts are individually owned; no joint accounts'}}

def simulate(data,years=20,paths=5000,seed=SEED,retire_father=False,market_crash=False):
 """Annual correlated multiasset shocks; explicit simple contributions/withdrawals. Tax NOT modelled."""
 years=int(years); paths=int(paths)
 if not 1<=years<=40 or not 100<=paths<=50000: raise ValueError('Simulation parameters out of range')
 rng=np.random.default_rng(seed)
 shocks=rng.multivariate_normal(MU,COV,size=(years,paths),check_valid='raise')
 if market_crash: shocks[0,:2]-=.30; shocks[0,2]-=.08
 results=[]; curves=[]; success=[]
 for m in data['members']:
  inv=balance(m); weights=holdings(m)
  balances=np.full(paths,inv,dtype=float)
  inc,exp=m['income'],m['expenses']
  all_years=[round(inv,2)]
  for year in range(1,years+1):
   # Simplified first retirement year: retire_father toggles retirement at year 1.
   retired=(m['id']=='father' and retire_father and year>=1) or m['age']+year>=m['retire_age']
   annual_net=(m['retirement_income']-m['retirement_spending']) if retired else (inc-exp)
   nominal_cashflow=annual_net*(1.025**(year-1))
   annual_return=np.maximum(-.99,shocks[year-1]@weights)
   balances=np.maximum(0,balances*(1+annual_return)+nominal_cashflow)
   all_years.append(round(float(np.median(balances)),2))
  goal=m['goals'][0]; target=goal['target']; psuccess=float(np.mean(balances>=target)); success.append(psuccess)
  results.append({'id':m['id'],'name':m['name'],'median':money(np.median(balances)),
     'p10':money(np.quantile(balances,.10)),'p90':money(np.quantile(balances,.90)),
     'goal_success':round(psuccess,4),'goal':goal['name'],'goal_target':target,
     'depletion_probability':round(float(np.mean(balances<=0)),4)})
  curves.append({'id':m['id'],'median_trajectory':all_years})
 # Independent simulated members share the same market paths, correctly retaining correlated family outcomes.
 # Recompute year-end family total via separate common-shock calculation.
 fam=np.zeros(paths)
 for m in data['members']:
  b=np.full(paths,balance(m),float); w=holdings(m)
  for year in range(1,years+1):
   retired=(m['id']=='father' and retire_father and year>=1) or m['age']+year>=m['retire_age']
   flow=(m['retirement_income']-m['retirement_spending']) if retired else (m['income']-m['expenses'])
   b=np.maximum(0,b*(1+np.maximum(-.99,shocks[year-1]@w))+flow*(1.025**(year-1)))
  fam+=b
 family_success=float(np.mean(fam>=data['family_goal']['target']))
 return {'kind':'SYNTHETIC PROJECTION — NOT A FORECAST','years':years,'paths':paths,'seed':seed,
    'method':'Annual correlated multivariate normal returns; nominal cashflows increasing 2.5% yearly; no explicit taxes',
    'family':{'median':money(np.median(fam)),'p10':money(np.quantile(fam,.10)),
      'p90':money(np.quantile(fam,.90)),'goal_success':round(family_success,4),
      'goal_target':data['family_goal']['target']},
    'members':results,'trajectories':curves,'crash':market_crash,'father_retires_now':retire_father,
    'limitations':['Illustrative parameter assumptions, not live market estimates','No exact account-level tax modelling',
                   'No stochastic salary, mortality, healthcare or regime switching','Goals evaluated using end-horizon balances, not date-specific goal funding']}

def optimize(data, retire_father=False):
 """Constrained global member allocation: family volatility + member limits + turnover penalty."""
 ms=data['members']; init=np.concatenate([holdings(m) for m in ms]); balances=np.array([balance(m) for m in ms],float)
 fractions=balances/balances.sum(); n=len(ms)
 limits=np.array([min(m['target_vol'],m['risk_capacity']) for m in ms],float)
 if retire_father: limits[0]=min(limits[0],.065)
 target=data['family_target_vol']
 def family_w(x):return np.sum(x.reshape(n,4)*fractions[:,None],axis=0)
 def objective(x):
  w=family_w(x)
  return -(w@MU-.55*(w@COV@w)) + .018*np.sum((x-init)**2)
 constraints=[{'type':'eq','fun':lambda x,i=i: np.sum(x.reshape(n,4)[i])-1} for i in range(n)]
 constraints += [{'type':'ineq','fun':lambda x,i=i: limits[i]-portfolio_vol(x.reshape(n,4)[i])} for i in range(n)]
 constraints += [{'type':'ineq','fun':lambda x: target-portfolio_vol(family_w(x))}]
 res=minimize(objective,init,method='SLSQP',bounds=[(0,1)]*(n*4),constraints=constraints,
              options={'maxiter':1200,'ftol':1e-11})
 result=[]
 x=res.x.reshape(n,4)
 for i,m in enumerate(ms):
  result.append({'id':m['id'],'name':m['name'],'current':[round(float(z),4) for z in holdings(m)],
    'proposed':[round(float(z),4) for z in x[i]],'current_volatility':round(portfolio_vol(holdings(m)),5),
    'proposed_volatility':round(portfolio_vol(x[i]),5),'limit':round(float(limits[i]),5)})
 fw=family_w(res.x)
 feasible=bool(res.success and max(abs(np.sum(x,axis=1)-1))<1e-5 and all(portfolio_vol(x[i])<=limits[i]+1e-5 for i in range(n)) and portfolio_vol(fw)<=target+1e-5)
 return {'status':'feasible' if feasible else 'infeasible_or_unconverged','solver_message':res.message,
   'members':result,'family_current_volatility':snapshot(data)['actual_volatility'],
   'family_proposed_volatility':round(portfolio_vol(fw),5),'family_target_volatility':target,
   'family_proposed_allocation':[round(float(z),4) for z in fw],
   'family_current_allocation':snapshot(data)['allocation'],
   'method':'SLSQP joint constrained mean-variance proxy with turnover penalty',
   'limitations':['Illustrative returns and covariance','This version optimises member asset-class weights, not tax-lot transactions or asset location',
                  'No tax-impact estimate can be computed from the demonstration holdings']}

def tax_insights(data):
 insights=[]
 for m in data['members']:
  for a in m['accounts']:
   if a['tax']=='Taxable' and a['allocation'][2]>=.20:
    insights.append({'member':m['name'],'account':a['name'],'category':'Asset location review',
     'message':'This taxable account holds a material bond allocation. Compare asset location across this member’s accounts after confirming tax rates, account restrictions and transaction consequences.',
     'status':'Review only — tax impact not calculated'})
 return {'accounts':snapshot(data)['tax_accounts'],'insights':insights,
    'coverage':'Account classification based on synthetic labels, not verified tax eligibility or current law',
    'tax_savings':None,'reason':'Cost basis, lots, jurisdiction and individual tax details are missing; no defensible tax-savings estimate'}
