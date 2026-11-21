# Packd demo and live pitch

## Two-minute screen recording plan
**0:00–0:15** Show Packd landing page, lion-and-lioness family identity, Connect / Grow / Thrive, and synthetic-only label.

**0:15–0:35** Open the synthetic Morgan family dashboard. Show individual account ownership and USD balances. Do NOT describe banking accounts as connected live.

**0:35–1:00** Open portfolio allocation and Decision Lab. Show a life event, baseline/scenario comparison, portfolio risk, and methodology/source inspector. Use an actual working user interaction.

**1:00–1:20** Ask Aunt Mabel: 'How is the Morgan family's investment portfolio divided across asset classes?' Confirm consent and show the result is sourced to synthetic values. If Nicrron is unavailable, do not fake the result.

**1:20–1:40** Open the *actual* PRISM trace and before/after Test your AI runs. Do not manufacture screenshots or claim tests that have not run.

**1:40–2:00** Show longer-term family goals; close on 'Packd — Connect. Grow. Thrive.'

## ElevenLabs narration transcript
Meet Packd. Family finances are rarely managed as one decision. Savings, retirement accounts, education costs, and unexpected life events affect different family members in different ways.

Packd brings those decisions together in one explainable view.

Here is our demonstration household, the Morgan family. Every account and balance is synthetic, and every amount is shown in U.S. dollars.

In Connect, we bring household assets, liabilities, and account ownership into a shared picture. The current demonstration uses synthetic accounts; live banking and brokerage connections are future integrations.

In Grow, Packd analyses asset allocation, portfolio volatility, and risk capacity using a transparent numerical engine. We can compare a baseline with an early retirement, an education expense, or an income interruption. The engine uses reproducible Monte Carlo scenarios and constrained portfolio optimisation, and exposes the assumptions behind the results.

Now meet Aunt Mabel, our financial education guide. Her AI responses are routed through Nicrron, grounded in the same synthetic evidence, and designed not to invent holdings or imply financial advice.

PRISM records the model interaction for testing and traceability. We also run the same evaluation before and after a genuine fix, so judges can inspect what changed.

Thrive brings the family back to its long-term goals. Packd does not pretend to know the future. It helps people understand their options, risks, and trade-offs together.

Packd. Connect. Grow. Thrive.

**Editing rule:** Remove or adjust any claim about PRISM evaluation or Nicrron response if not visibly verified in the recording. Fit the spoken audio to 120 seconds by trimming pauses or text without accelerating excessively.

## Three-minute judge pitch
**Problem (0:00–0:35):** Family finances are connected, but financial decisions are fragmented. A retirement choice, education payment and income shock affect each other. Most dashboards show account totals, not the trade-offs.

**Product (0:35–1:05):** Packd introduces Connect, Grow and Thrive. It lets a family understand its consolidated picture, compare risk-aware scenarios and keep goals in view.

**Technical depth (1:05–1:55):** Show synthetic Morgan accounts and one actual event scenario. Explain portfolio aggregation, covariance risk, constrained optimization and reproducible, paired Monte Carlo. Open source/methodology controls.

**AI quality (1:55–2:35):** Show a verified Nicrron-model answer and the PRISM trace. Show an authentic PRISM Test your AI baseline, defect, fix and same-test retest.

**Vision (2:35–3:00):** U.S.-first, USD throughout, account consent and regulated integrations only after appropriate safeguards. 'Packd — family decisions, made together.'

## Q&A preparation
- **Is this investment advice?** No. Demonstration uses synthetic U.S. household inputs, illustrative returns and risk scenarios. No trades or personalised recommendations.
- **What is genuinely built?** FastAPI application, deterministic portfolio calculations, simulation, optimisation, Decision Lab, Nicrron model-call path and PRISM trace-posting code; live integration/test status must be separately verified.
- **Why not just a chatbot?** Numerical analytics are computed outside the LLM. Responses are grounded in a restricted evidence payload, and provenance is inspectable.
- **What is real market data?** Public historical Yahoo chart data, separate from synthetic family holdings; not a licensed Bloomberg integration.
- **What is unfinished?** Real account onboarding, state-specific taxation, KYC, production permissions, brokerage execution, PRISM evaluation proof until confirmed.
