# PACT — Family Portfolio Intelligence (working title)

A **runnable research MVP** based on the supplied Family Wealth 360 specification. Uses synthetic demonstration data only. This is not a production financial application.

## Run

```bash
python -m pip install -r requirements.txt
uvicorn app:app --reload
```
Open http://127.0.0.1:8000. Requires an internet connection for the optional Chart.js CDN charts; API and calculations work offline.

## Test

```bash
python -m pytest -q
```

## What works

- Synthetic three-member family snapshot with individual accounts and tax categories
- Consolidated balance-sheet and allocation calculations
- Portfolio volatility from a cross-asset covariance matrix
- Member-specific adjustable risk targets and capacity warnings
- Joint SLSQP asset-class optimization, including a father-retirement constraint
- Reproducible 5,000+ path correlated Monte Carlo projections, early-retirement and crash scenarios
- Account-level tax-location review flags **without invented tax-savings numbers**
- API for creating temporary members, CSV demo account import, data-source details
- Deterministic Q&A explanations; source/assumption inspector
- Automated tests for aggregation, optimization, simulation reproducibility and tax caution

## Explicitly not implemented / production blockers

1. **Persistence & authentication:** demo uses shared process memory, with **no user accounts or isolation**. Do not expose it on a public server or enter real financial information.
2. **Plaid:** no bank-link token flow, webhook verification or linked account support until secure infrastructure and credentials are configured.
3. **Tax:** no jurisdiction-specific live tax rule integration, verified eligibility, exact after-tax objective, tax lots or transaction optimization.
4. **Market:** illustrative static return / volatility assumptions, no historical time series or security-level factor / ETF overlap analysis.
5. **Health score:** reproducible simulation and goal-threshold measures exist, but a rigorous 0–100 score is intentionally withheld pending properly date-aligned goal, retirement, liquidity and liabilities modelling.
6. **Asset location:** optimizer currently operates on individual asset-class weights subject to family risk, not actual security trades or account-level tax location.
7. **Life events:** early retirement and crash prototype only.
8. **AI:** transparent deterministic responses only, no LLM keys and no uncited financial claims.
9. **Compliance:** no production security review, investment-advice regulatory determination or tax advice service.

## Engineering roadmap

- Move to PostgreSQL/Prisma, separate multi-tenant auth, consent and role-based permissions, encrypt credentials, add audit trails.
- Add market-data and Plaid adapters with sandbox staging, token encryption and user-controlled revocation.
- Add test-backed individual account ownership, shared-asset accounting and real asset / tax-lot schemas.
- Add tax-year/jurisdiction sourced rule engine and genuine constrained account-level asset-location optimization.
- Build calibrated multivariate financial-health Monte Carlo scores with goals at correct due dates, liability amortization, income uncertainty and retirement drawdowns.
- Add LLM tool orchestration strictly on top of deterministic analytics, per-response provenance and least-privilege data sharing.
- Add integration, authorization, property-based, statistical validation and end-to-end tests before production release.

## CSV import

Required fields: `member_id,name,tax,balance,us_equity,international_equity,bonds,cash`.

This proof-of-concept was created as a standalone repository because no existing source repository was provided to inspect.

## v0.2 — Decision Lab (family decision engine prototype)

A **Decision Lab** tab now demonstrates PACT's proposed differentiator: event-driven, multi-member financial decision analysis. For one selected member, compare retirement, education costs, a one-year income disruption, or a major purchase against the original family scenario. The engine:

- Runs **paired** Monte Carlo market paths with a shared random seed, so baseline/scenario differences are not dominated by random sampling noise.
- Reports the family's terminal investment distribution and individual median wealth, goal-funding probability at the relevant goal due date (or horizon if shorter), and depletion frequency.
- Adjusts the affected member's *illustrative* risk capacity for retirement or job loss and reruns joint constrained asset-class optimisation across members.
- Returns methodology, assumptions, solver feasibility and explicit limitations in an inspectable response.

**API:** `POST /api/decisions/compare` with `{"event":"retirement","member_id":"father","years":20,"paths":5000,"seed":26011}`. Other event identifiers: `education`, `job_loss`, `major_purchase`. The latter two cost events require positive `amount` for `education` / `major_purchase`. Available events: `GET /api/decisions/events`.

**Critical limitations:** This is still a single, globally shared, unauthenticated synthetic demonstration. It has **no real family registration, permissions, private holdings protection or brokerage integration**. The event-specific risk-capacity change (6.5% retirement limit / 8% job-loss limit) is a demonstration assumption, not a suitability assessment. No account-level asset-location optimisation or tax effects are simulated. Do not expose this prototype publicly or enter real financial information.

### Proposed defensibility / competitive hypothesis

PACT should compete on **auditable, privacy-preserving, multi-person, event-driven decision optimisation**, not aggregation, chat, generic Monte Carlo, or portfolio analytics individually. Tested differentiation requires evidence that users and competitors cannot get comparable coordinated decisions elsewhere. Technical defensibility should derive from validated constraints, robust model monitoring, permission-aware family computations, member-specific explainability, and tested longitudinal decision outcomes. The present demo establishes only an initial vertical slice of that product direction; it does not yet establish a proprietary moat.
