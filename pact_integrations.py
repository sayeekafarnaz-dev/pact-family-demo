"""PACT hackathon integrations. Synthetic-only public analytics; never send live financial data to AI or PRISM."""
import os,time,logging,uuid,re,datetime
import httpx
from fastapi import APIRouter,HTTPException,Request
from pydantic import BaseModel,Field
from openai import OpenAI
from engine import DEFAULT, CLASSES, simulate, snapshot
from decision_lab import EVENTS, compare_decision
router=APIRouter(prefix="/api/public")
_CALLS={}
log=logging.getLogger(__name__)
class Question(BaseModel):
 question:str=Field(min_length=2,max_length=1200)
 member:str=Field(default="family",max_length=32)
 session_id:str|None=None
 privacy_consent:bool=False
def portfolio():
 rows=[]
 for m in DEFAULT["members"]:
  for a in m["accounts"]:
   for category,weight in zip(CLASSES,a["allocation"]):
    amount=round(a["balance"]*weight,2)
    rows.append({"member":m["name"],"member_id":m["id"],"account":a["name"],"account_id":a["id"],"asset_class":category,"value":amount,"source":"engine.DEFAULT.members[].accounts[].allocation","data_kind":"synthetic"})
 total=round(sum(r["value"] for r in rows),2)
 return {"data_kind":"synthetic","currency":DEFAULT["currency"],"family":DEFAULT["family"],"total":total,"rows":rows,"formula":"position_value = account.balance * allocation_weight; family_total = sum(position_value)","source":"engine.py DEFAULT","as_of":"Fixed synthetic benchmark, not live market data"}
@router.get("/portfolio")
def public_portfolio():
 return {**portfolio(), "summary": snapshot(DEFAULT)}

class FamilyDecision(BaseModel):
 event: str
 member_id: str
 amount: float = Field(default=0, ge=0, le=1000000)

@router.post("/decision")
def public_family_decision(selection: FamilyDecision):
 try:
  return compare_decision(DEFAULT, **selection.model_dump(), paths=1000)
 except ValueError as error:
  raise HTTPException(400, str(error)) from error

@router.get("/decision/options")
def public_family_decision_options():
 return {"events": EVENTS, "members": [
  {"id": member["id"], "name": member["name"]} for member in DEFAULT["members"]
 ]}
@router.get("/simulation")
def public_simulation(years:int=10,crash:bool=False):
 if years<1 or years>30:raise HTTPException(400,"Years must be 1-30")
 result=simulate(DEFAULT,years=years,paths=1000,seed=26011,market_crash=crash)
 return {"data_kind":"synthetic","source":"engine.simulate(DEFAULT, seed=26011, paths=1000)","scenario":{"years":years,"market_crash":crash},"result":result}
@router.get("/integrations")
def integrations():
 return {"nicrron_configured":bool(os.getenv("NICRRON_API_KEY")),"prism_configured":bool((os.getenv("PRISMTRACE_API_KEY") or os.getenv("PRISM_API_KEY")) and os.getenv("PRISMTRACE_PROJECT_ID")),"plaid_configured":bool(os.getenv("PLAID_CLIENT_ID") and os.getenv("PLAID_SECRET")),"plaid_environment":os.getenv("PLAID_ENV","sandbox"),"data_kind":"synthetic"}
@router.post("/ask")
def ask(p:Question,request:Request):
 if not p.privacy_consent:raise HTTPException(403,'Explicit privacy consent is required before sending questions to Nicrron.')
 ip=request.client.host if request.client else 'unknown'
 now=time.time()
 _CALLS[ip]=[t for t in _CALLS.get(ip,[]) if now-t<3600]
 if len(_CALLS[ip])>=5:raise HTTPException(429,'Demo limit: five AI questions per hour.')
 _CALLS[ip].append(now)
 key=os.getenv("NICRRON_API_KEY")
 if not key:raise HTTPException(503,"Nicrron is not configured; no other model provider will be used.")
 if p.member!="family" and p.member not in {m["id"] for m in DEFAULT["members"]}:raise HTTPException(400,"Unknown member")
 info=portfolio()
 rows=info["rows"] if p.member=="family" else [r for r in info["rows"] if r["member_id"]==p.member]
 total=round(sum(r["value"] for r in rows),2)
 by_class={c:round(sum(r["value"] for r in rows if r["asset_class"]==c),2) for c in CLASSES}
 evidence={"scope":p.member,"currency":info["currency"],"total":total,"asset_class_totals":by_class,"source":"engine.py DEFAULT","formula":info["formula"],"data_kind":"synthetic"}
 import json
 model=os.getenv("NICRRON_MODEL","anthropic/claude-opus-5-5")
 started=time.perf_counter()
 try:
  result=OpenAI(api_key=key,base_url="https://api.nicrron.ai/v1",timeout=25,max_retries=0).chat.completions.create(model=model,messages=[{"role":"system","content":"You are Aunt Mabel, PACT's clear, warm financial education guide. The following JSON is the ONLY evidence. Cite exact values, source and calculation. Do not invent holdings, live prices, personal data, returns or advice. Explicitly identify synthetic data and limitations. Explain family vs individual portfolio and risk clearly."},{"role":"user","content":"Question: "+p.question+"\nEvidence: "+json.dumps(evidence)}])
  answer=result.choices[0].message.content or ""
 except Exception:
  log.exception("Nicrron failed")
  raise HTTPException(502,"Nicrron failed. No fallback provider was used.") from None
 trace=False
 trace_key=os.getenv("PRISMTRACE_API_KEY") or os.getenv("PRISM_API_KEY")
 project=os.getenv("PRISMTRACE_PROJECT_ID")
 session=p.session_id or str(uuid.uuid4())
 if trace_key and project:
  try:
   # Synthetic-only trace: no bank tokens, real customer data or identifiable accounts.
   response=httpx.post("https://api.prism.blockconvey.com/api/traces",headers={"X-PRISMtrace-Key":trace_key},json={"project_id":project,"model":result.model,"input_messages":[{"role":"user","content":"[question redacted; synthetic benchmark]"}],"output_message":"[answer redacted; synthetic benchmark]","latency_ms":round((time.perf_counter()-started)*1000),"session_id":session,"agent_id":"pact-aunt-mabel","agent_name":"PACT Aunt Mabel","metadata":{"provider":"nicrron","data_kind":"synthetic","source":"engine.py DEFAULT"}},timeout=5)
   response.raise_for_status();trace=True
  except Exception:log.warning("PRISM trace not accepted",exc_info=True)
 return {"answer":answer,"model":result.model,"provider":"Nicrron","prism_trace_sent":trace,"session_id":session,"evidence":evidence}

# Public historical market series, not holdings or account balances.
# Yahoo's unauthenticated chart endpoint is best-effort and not a licensed Bloomberg feed.
@router.get("/market-history")
def market_history(symbol:str="SPY",range:str="1y",interval:str="1mo"):
 if not re.fullmatch(r"[A-Za-z0-9.^=-]{1,20}",symbol):
  raise HTTPException(400,"Invalid ticker")
 if range not in {"1mo","3mo","6mo","1y","2y","5y","10y"} or interval not in {"1d","1wk","1mo"}:
  raise HTTPException(400,"Unsupported date range or interval")
 try:
  with httpx.Client(timeout=9,follow_redirects=False,headers={"User-Agent":"Mozilla/5.0 (compatible; packd-demo/1.0)"}) as client:
   response=client.get("https://query1.finance.yahoo.com/v8/finance/chart/"+symbol.upper(),params={"range":range,"interval":interval})
   response.raise_for_status()
   payload=response.json()["chart"]["result"][0]
  times=payload.get("timestamp",[])
  closes=payload["indicators"]["quote"][0]["close"]
  rows=[{"date":datetime.datetime.fromtimestamp(t,datetime.timezone.utc).date().isoformat(),"close":round(float(v),4)} for t,v in zip(times,closes) if v is not None]
  if not rows:raise ValueError("No price observations")
  return {"symbol":symbol.upper(),"range":range,"interval":interval,"currency":payload.get("meta",{}).get("currency"),"observations":rows,"source":"Yahoo Finance chart endpoint","source_url":"https://finance.yahoo.com/quote/"+symbol.upper()+"/history/","as_of":rows[-1]["date"],"data_kind":"historical_market_prices","limitations":"Unadjusted closing prices; may exclude dividends, splits, FX and fees. Not evidence of family holdings or live account balances. Provider availability and licensing are not guaranteed."}
 except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError) as exc:
  log.warning("Historical price provider unavailable for %s: %s",symbol,exc)
  raise HTTPException(503,"Historical price provider unavailable. No synthetic prices were substituted.") from None
