# Packd — Family decisions, made together

**Tagline:** Explainable family financial intelligence, built around shared decisions.

## Inspiration
Families do not make financial decisions in isolation. One person's retirement, another's education costs, and a period of lost income can change the options available to everyone. Existing account dashboards show balances, but rarely explain coordinated family trade-offs.

## What it does
Packd connects the idea of a shared household financial view to an explainable decision engine. Our working synthetic demonstration models a three-member U.S. household, individual accounts, financial goals, allocation, liabilities, risk capacity, and life-event scenarios. Users can compare a baseline with retirement, education expenses, income disruption, or a major purchase. A financial education guide, Aunt Mabel, can explain synthetic evidence through Nicrron, with an optional PRISM trace.

## How we built it
FastAPI backend; NumPy and SciPy for calculations; deterministic portfolio aggregation and risk measures; SLSQP constrained asset-class optimization; seeded, correlated Monte Carlo simulation; a responsive HTML/JavaScript frontend; Render hosting; Nicrron OpenAI-compatible API gateway for model calls; PRISM trace integration; ElevenLabs-generated demo narration.

## Portfolio methodology
Positions = account balance × allocation weight. Household assets, liabilities, net worth and cash flow are aggregated from synthetic household records. Portfolio annual volatility = sqrt(w-transpose × covariance × w), using an explicitly illustrative four-asset-class covariance matrix. The constrained optimizer considers member risk limits; Monte Carlo projects correlated annual portfolio outcomes using a fixed seed and scenario-specific cash flows. The Decision Lab compares alternatives on paired simulated market paths. These are exploratory calculations, not forecasts or individualized investment advice. Tax treatment is limited to qualitative account-location flags; no live tax calculation, trade execution or personalised tax advice.

## Nicrron and PRISM
`POST /api/public/ask` routes model inference through Nicrron (no direct-provider fallback) after explicit consent; only synthetic portfolio evidence is sent. Where configured, the application submits a redacted trace to PRISM and returns whether the trace endpoint accepted the request. **Judges: attach an actual PRISM trace link, an initial Test your AI result, the identified defect and code fix, and a retest using the same test set before claiming completion.**

## Challenges
Keeping AI responses grounded in deterministic calculations, preserving sensitive-data boundaries, understanding household-level constraints, and making advanced portfolio concepts accessible without implying guaranteed results.

## What we learned
Traceability is part of product quality. A portfolio explanation is more trustworthy when its numbers can be reconstructed from source holdings, assumptions and documented calculations.

## What's next
U.S.-first user jurisdiction and state selection; jurisdiction-specific sourced tax rules; consent-based read-only banking and brokerage connectivity; secure KYC only when required; proper account-level permissions and persistence; broader financial-goal modelling and independently validated risk metrics.

## Links
- Live demo: https://pact-family-demo.onrender.com/
- GitHub: https://github.com/sayeekafarnaz-dev/pact-family-demo/tree/pact-render-demo
- Video: [ADD FINAL TWO-MINUTE VIDEO URL]
- PRISM proof: [ADD TRACE / INITIAL TEST / FIX / RETEST LINKS]

## Important scope
All family data are synthetic; all monetary illustrations are denominated in USD. Historical public Yahoo Finance prices may be displayed separately and are not household holdings. No live Plaid, eToro trading, identity verification, or production tax integration is claimed. The app is a hackathon research demonstration, not investment advice.
