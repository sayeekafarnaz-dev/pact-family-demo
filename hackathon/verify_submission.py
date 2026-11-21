#!/usr/bin/env python3
"""Smoke-test the public Packd demo and Nicrron/PRISM route using synthetic data.

No secrets are printed or recorded. Run from a machine with HTTPS access:
  python hackathon/verify_submission.py
  PACKD_RUN_AI=1 python hackathon/verify_submission.py

AI mode sends one synthetic-only question and explicit consent. It does not
assert that a PRISM Test your AI before/after cycle has been completed.
"""
import json,os,urllib.request,urllib.error,sys
BASE=os.getenv("PACKD_BASE_URL","https://pact-family-demo.onrender.com").rstrip("/")
def call(path,payload=None):
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(BASE+path,data=data,headers={"Content-Type":"application/json"} if data is not None else {},method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req,timeout=40) as r:
            return r.status,json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code,{"detail":e.read().decode()[:250]}
def check(name, path, predicate):
    code,body=call(path)
    ok=code==200 and predicate(body)
    print(("PASS" if ok else "FAIL")+" "+name+" HTTP="+str(code))
    return ok
ok=check("health","/health",lambda d:d.get("status")=="ok")
ok=check("USD synthetic portfolio","/api/public/portfolio",lambda d:d.get("currency")=="USD" and d.get("data_kind")=="synthetic" and len(d.get("rows",[]))>0) and ok
code,flags=call("/api/public/integrations")
print("INFO configuration presence (not proof): "+json.dumps({k:v for k,v in flags.items() if k.endswith("_configured")}) if code==200 else "INFO integrations HTTP="+str(code))
if os.getenv("PACKD_RUN_AI")=="1":
    code,ans=call("/api/public/ask",{"question":"Is the Morgan family portfolio real customer data? Explain where the numbers came from.","member":"family","privacy_consent":True})
    ai_ok=code==200 and ans.get("provider")=="Nicrron" and bool(ans.get("answer"))
    print(("PASS" if ai_ok else "FAIL")+" Nicrron live model response HTTP="+str(code))
    if ai_ok:
        print("INFO model="+str(ans.get("model"))+" prism_trace_sent="+str(ans.get("prism_trace_sent"))+" session_id="+str(ans.get("session_id")))
        print("INFO trace flag means HTTP acceptance, NOT confirmed PRISM evaluation")
    else:print("INFO AI error="+str(ans.get("detail","unknown"))[:200])
    ok=ai_ok and ok
sys.exit(0 if ok else 1)
