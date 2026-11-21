from __future__ import annotations
import copy, csv, io, os, hmac, hashlib, time, html
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Form
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from engine import DEFAULT, snapshot, simulate, optimize, tax_insights, CLASSES, COV, MU
from decision_lab import compare_decision, EVENTS

app=FastAPI(title='PACT — family portfolio intelligence (synthetic MVP)',version='0.1.0')
app.mount('/static',StaticFiles(directory='static'),name='static')
DATA=copy.deepcopy(DEFAULT) # Demo-only in-memory store. Never deploy with real financial records.

# --- Team-demo access control -------------------------------------------------
# Server-side shared-password gate. Every route except PUBLIC_PATHS requires a valid
# signed session cookie. Fails closed: if PACT_DEMO_PASSWORD is unset, nothing is served.
SESSION_COOKIE='pact_session'
SESSION_TTL=int(os.environ.get('PACT_SESSION_TTL_SECONDS','43200'))
PUBLIC_PATHS={'/health','/login','/logout','/try-family','/static/family-demo.html'}

def _password()->str:return os.environ.get('PACT_DEMO_PASSWORD','')
def _signing_key()->bytes:
 secret=os.environ.get('PACT_SESSION_SECRET') or ('pact-derived:'+_password())
 return hashlib.sha256(secret.encode()).digest()
def _sign(expiry:int)->str:
 # Binding the password fingerprint means rotating PACT_DEMO_PASSWORD invalidates sessions.
 fp=hashlib.sha256(_password().encode()).hexdigest()[:16]
 return hmac.new(_signing_key(),f'{expiry}.{fp}'.encode(),hashlib.sha256).hexdigest()
def make_session_token(now:float|None=None)->str:
 expiry=int((time.time() if now is None else now)+SESSION_TTL);return f'{expiry}.{_sign(expiry)}'
def valid_session(token:str|None)->bool:
 if not token or not _password():return False
 try:exp_s,sig=token.split('.',1);expiry=int(exp_s)
 except ValueError:return False
 return expiry>time.time() and hmac.compare_digest(sig,_sign(expiry))
def _secure_cookie(request:Request)->bool:
 return request.url.scheme=='https' or os.environ.get('RENDER','').lower()=='true'

LOGIN_PAGE='''<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PACT · Team demo sign-in</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f5f6f4;color:#162b31;font:14px/1.5 system-ui,sans-serif}form{background:#fff;border:1px solid #e4e9e6;border-radius:14px;padding:28px;width:min(360px,90vw)}h1{margin:0 0 4px;font-size:22px}input,button{width:100%;box-sizing:border-box;padding:10px;margin-top:10px;border-radius:8px;border:1px solid #cfd8d5;font:inherit}button{background:#142d36;color:#fff;border:0;cursor:pointer}.err{color:#a33;margin-top:10px}.muted{color:#67777b;font-size:12px}</style></head>
<body><form method="post" action="/login"><h1>pact.</h1><div class="muted">Team demonstration · synthetic data only</div>
<input type="password" name="password" placeholder="Demo password" autocomplete="current-password" required autofocus>
<button type="submit">Sign in</button>__ERROR__</form></body></html>'''
def _login_page(error:str='',status:int=200)->HTMLResponse:
 err=f'<div class="err">{html.escape(error)}</div>' if error else ''
 return HTMLResponse(LOGIN_PAGE.replace('__ERROR__',err),status_code=status,headers={'Cache-Control':'no-store'})

@app.middleware('http')
async def require_demo_password(request:Request,call_next):
 path=request.url.path
 if path in PUBLIC_PATHS or valid_session(request.cookies.get(SESSION_COOKIE)):
  return await call_next(request)
 if path.startswith('/api/'):
  return JSONResponse({'detail':'Authentication required'},status_code=401)
 return RedirectResponse('/login',status_code=303)

@app.get('/health')
def health():return {'status':'ok'}
@app.get('/login')
def login_form(request:Request):
 if valid_session(request.cookies.get(SESSION_COOKIE)):return RedirectResponse('/',status_code=303)
 if not _password():return _login_page('Server is not configured: PACT_DEMO_PASSWORD is not set.',503)
 return _login_page()
@app.post('/login')
def login(request:Request,password:str=Form('')):
 expected=_password()
 if not expected:return _login_page('Server is not configured: PACT_DEMO_PASSWORD is not set.',503)
 if not hmac.compare_digest(password.encode(),expected.encode()):
  time.sleep(0.5) # slow down guessing
  return _login_page('Incorrect password.',401)
 r=RedirectResponse('/',status_code=303)
 r.set_cookie(SESSION_COOKIE,make_session_token(),max_age=SESSION_TTL,httponly=True,samesite='strict',secure=_secure_cookie(request),path='/')
 return r
@app.post('/logout')
def logout():
 r=RedirectResponse('/login',status_code=303);r.delete_cookie(SESSION_COOKIE,path='/');return r
# -----------------------------------------------------------------------------

@app.get('/')
def home():return FileResponse('static/index.html')
@app.get('/api/snapshot')
def get_snapshot():return snapshot(DATA)
@app.get('/api/source')
def source():return {'data_kind':DATA['kind'],'market_parameters':'Illustrative annualized inputs, not live prices','expected_returns':dict(zip(CLASSES,MU.tolist())),'covariance':COV.tolist(),'sources':['Synthetic family dataset in engine.py','Mathematical calculations in engine.py'],'live_connections':False}
@app.get('/api/simulation')
def get_simulation(years:int=20,paths:int=5000,seed:int=26011,retire_father:bool=False,market_crash:bool=False):
 try:return simulate(DATA,years,paths,seed,retire_father,market_crash)
 except ValueError as e:raise HTTPException(400,str(e))
@app.get('/api/optimize')
def get_optimize(retire_father:bool=False):return optimize(DATA,retire_father)
@app.get('/api/tax')
def get_tax():return tax_insights(DATA)
class Targets(BaseModel):
 member_id:str
 target_volatility:float=Field(ge=.005,le=.6)
@app.post('/api/targets')
def set_target(v:Targets):
 for member in DATA['members']:
  if member['id']==v.member_id:
   member['target_vol']=v.target_volatility
   return {'status':'updated','member_id':v.member_id,'target_volatility':v.target_volatility,'capacity_warning':v.target_volatility>member['risk_capacity']}
 raise HTTPException(404,'Member not found')
class MemberInput(BaseModel):
 name:str=Field(min_length=1,max_length=80)
 relation:str='Other'
 age:int=Field(ge=18,le=110)
 income:float=Field(ge=0)
 expenses:float=Field(ge=0)
 liabilities:float=Field(ge=0)
 liquid_cash:float=Field(ge=0)
@app.post('/api/members')
def add_member(m:MemberInput):
 mid='new'+str(len(DATA['members'])+1)
 DATA['members'].append({'id':mid,'name':m.name,'relation':m.relation,'age':m.age,'retire_age':67,'income':m.income,'expenses':m.expenses,'liabilities':m.liabilities,'liquid_cash':m.liquid_cash,'target_vol':.12,'risk_tolerance':'Unassessed','risk_capacity':.12,'retirement_income':0,'retirement_spending':m.expenses,'accounts':[],'goals':[{'name':'General capital','target':0,'years':10}]})
 return {'id':mid,'status':'added','warning':'In-memory demonstration record; data not persisted'}
class AccountInput(BaseModel):
 member_id:str
 name:str=Field(min_length=1)
 tax:str
 balance:float=Field(ge=0)
 allocation:list[float]=Field(min_length=4,max_length=4)
@app.post('/api/accounts')
def add_account(a:AccountInput):
 if any(x<0 for x in a.allocation) or abs(sum(a.allocation)-1)>.00001:raise HTTPException(400,'Allocations must be nonnegative and sum to 1')
 for m in DATA['members']:
  if m['id']==a.member_id:
   m['accounts'].append({'id':f'user-{len(m["accounts"])+1}','name':a.name,'tax':a.tax,'balance':a.balance,'allocation':a.allocation})
   return {'status':'added'}
 raise HTTPException(404,'Member not found')
@app.post('/api/import/accounts')
async def import_accounts(file:UploadFile=File(...)):
 if not file.filename.lower().endswith('.csv'):raise HTTPException(400,'CSV only')
 content=await file.read()
 if len(content)>1_000_000:raise HTTPException(400,'CSV is too large')
 try:
  reader=csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
  items=[]
  for row in reader:
   vals=[float(row[k]) for k in ('us_equity','international_equity','bonds','cash')]
   a=AccountInput(member_id=row['member_id'],name=row['name'],tax=row['tax'],balance=float(row['balance']),allocation=vals)
   if abs(sum(vals)-1)>1e-5:raise ValueError('Account allocations must sum to 1')
   items.append(a)
 except Exception as e:raise HTTPException(400,f'Invalid CSV: {e}')
 if len(items)>1000:raise HTTPException(400,'Too many accounts')
 mids={m['id'] for m in DATA['members']}
 if any(a.member_id not in mids for a in items):raise HTTPException(400,'Unknown member_id')
 for a in items:add_account(a)
 return {'imported':len(items),'status':'synthetic demo updated in memory'}
@app.post('/api/reset')
def reset():
 DATA.clear();DATA.update(copy.deepcopy(DEFAULT));return {'status':'reset'}

class DecisionRequest(BaseModel):
 event:str
 member_id:str
 amount:float=Field(default=0,ge=0,le=1e9)
 years:int=Field(default=20,ge=1,le=40)
 paths:int=Field(default=5000,ge=100,le=50000)
 seed:int=26011

@app.get('/api/decisions/events')
def get_events():
 return {'events':EVENTS,'kind':'SYNTHETIC DEMONSTRATION'}

@app.post('/api/decisions/compare')
def compare(req:DecisionRequest):
 try:
  return compare_decision(DATA,**req.model_dump())
 except ValueError as e:
  raise HTTPException(400,str(e))


@app.get('/try-family', include_in_schema=False)
def try_family_demo():
    """Public synthetic-only onboarding prototype, isolated from protected research APIs."""
    return FileResponse('static/family-demo.html', headers={'Cache-Control': 'no-store'})
