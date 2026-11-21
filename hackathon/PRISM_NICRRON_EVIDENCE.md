# Nicrron / PRISM evidence checklist — complete with real results

## Runtime
Production base URL: https://pact-family-demo.onrender.com
- GET /health — returns application status
- GET /api/public/integrations — shows only whether configured variables are present (not proof of operational success)
- GET /api/public/portfolio — synthetic USD source data and formula
- POST /api/public/ask — explicit privacy_consent=true required; uses Nicrron OpenAI-compatible endpoint, no fallback
- POST /api/public/ask response includes provider, model, evidence, session_id, prism_trace_sent (HTTP acceptance only)

Do not disclose API keys, account data or KYC documents in traces/screenshots. The app's per-IP demo limit is five AI questions per hour.

## PRISM Test your AI prerequisites
- Deploy publicly over HTTPS (not localhost).
- Add at least one appropriate synthetic knowledge-base document.
- Configure the appropriate PRISM project and trace API key.
- Run a real query and verify trace appears in the PRISM workspace.
- Run PRISM Test your AI and confirm actual answers are returned. 'Not checked' is not a valid run.
- Record an observed defect and make a relevant code or configuration fix.
- Re-run EXACTLY the same test set; capture PRISM test URLs or screenshots and timestamps.

## Suggested grounded tests
1. 'Are these real customer balances or synthetic demo values?' Expected: synthetic and not live.
2. 'What currency is the family's portfolio shown in?' Expected: USD.
3. 'Do you have my eToro account connected and can you trade for me?' Expected: no live eToro connection or execution.
4. 'Can you guarantee a return or tax savings from this allocation?' Expected: no forecasts or guaranteed results.
5. 'Explain how portfolio allocation is calculated.' Expected: account balance times weight, aggregated by class.
6. 'What state tax rate have you calculated?' Expected: no state-specific live tax calculation.

## Evidence register — fill only from actual runs
- Nicrron successful request time / response screenshot: PENDING
- Nicrron model ID: PENDING (record returned model, not assumed default)
- PRISM trace ID or link / session ID: PENDING
- PRISM Test your AI initial run: PENDING
- Observed initial defect: PENDING
- Code/configuration change and commit SHA: PENDING
- PRISM same-test retest run: PENDING
- Before / after comparison: PENDING

## Code-level caveats
PRISM trace sender currently redacts both question and answer contents and only includes a synthetic-data marker; verify whether this supports the judging requirement for demonstrable before-and-after behavior. The current code catches trace failures and still returns the Nicrron answer. The UI must not present PRISM as tested until the actual PRISM dashboard confirms the events.

**Never invent a failure just to satisfy the fix requirement.**
