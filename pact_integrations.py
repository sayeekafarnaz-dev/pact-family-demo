"""PACT hackathon integrations. Synthetic-only public analytics; never send live financial data to AI or PRISM."""
import os,time,logging,uuid
import httpx
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from openai import OpenAI
from engine import DEFAULT,CLASSES
router=APIRouter(prefix="/api/public")
log=logging.getLogger(__name__)
class Question(BaseModel):
 question:str=Field(min_length=2,max_length=1200)
 member:str=Field(default="family",max_length=32)
 session_id:str|None=None
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
def public_portfolio():return portfolio()
@router.get("/integrations")
def integrations():
 return {"nicrron_configured":bool(os.getenv("NICRRON_API_KEY")),"prism_configured":bool((os.getenv("PRISMTRACE_API_KEY") or os.getenv("PRISM_API_KEY")) and os.getenv("PRISMTRACE_PROJECT_ID")),"plaid_configured":bool(os.getenv("PLAID_CLIENT_ID") and os.getenv("PLAID_SECRET")),"plaid_environment":os.getenv("PLAID_ENV","sandbox"),"data_kind":"synthetic"}
@router.post("/ask")
def ask(p:Question):
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
   response=httpx.post("https://api.prism.blockconvey.com/api/traces",headers={"X-PRISMtrace-Key":trace_key},json={"project_id":project,"model":result.model,"input_messages":[{"role":"user","content":p.question+" [synthetic benchmark]"}],"output_message":answer,"latency_ms":round((time.perf_counter()-started)*1000),"session_id":session,"agent_id":"pact-aunt-mabel","agent_name":"PACT Aunt Mabel","metadata":{"provider":"nicrron","data_kind":"synthetic","source":"engine.py DEFAULT"}},timeout=5)
   response.raise_for_status();trace=True
  except Exception:log.warning("PRISM trace not accepted",exc_info=True)
 return {"answer":answer,"model":result.model,"provider":"Nicrron","prism_trace_sent":trace,"session_id":session,"evidence":evidence}
