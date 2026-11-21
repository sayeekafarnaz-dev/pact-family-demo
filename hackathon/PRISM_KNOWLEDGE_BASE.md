# Packd synthetic portfolio knowledge base — PRISM Test your AI

Version: hackathon-demo-2026-11-21
Scope: United States, USD, demonstration only.

Packd is a family financial intelligence research prototype. It aggregates a synthetic three-member household, its accounts, goals, illustrative annual incomes and liabilities, and allows comparisons of alternative life-event scenarios.

All household values in this project are SYNTHETIC. They are not real customers, real brokerage balances, linked bank accounts or an authorised investment-advice service. A public historical market chart, where available, is a separate data source and does not verify household holdings.

The synthetic demonstration uses the U.S. dollar (USD), U.S. equity, international equity, bonds and cash as four analysis categories. Account types include 401(k), Roth IRA, Traditional IRA and taxable brokerage accounts. Account labels are illustrative, not confirmation of the household's tax eligibility or tax filing treatment.

Household position amount = account balance multiplied by the allocation weight for that asset class. Household portfolio totals aggregate the positions across members. Portfolio volatility is calculated as sqrt(w-transpose × covariance × w), based on a specified illustrative covariance matrix. Numerical simulation uses a fixed random seed for reproducibility and correlated annual return shocks using assumed means and covariances. The optimizer uses constrained SciPy SLSQP at the asset-class level. Results are scenarios, not guaranteed returns.

Decision Lab can compare retirement, education expense, job loss and major purchase scenarios against a baseline, using paired market paths to reduce noise in comparisons.

The demonstration does NOT provide: bank account connection, eToro brokerage trading, live tax data, exact U.S. federal or state income-tax calculations, identity verification, KYC/AML compliance for account creation, account-level tax-lot optimisation, risk suitability determinations, guaranteed returns, or personalised investment advice.

When asked about a particular jurisdiction, state tax treatment, current tax limits, security prices or real customer information that is absent from the provided evidence, the assistant must identify what is unknown and not invent a result.

When asked for a citation, cite the synthetic dataset and method name, not an invented third-party source. A language-model response must not override deterministic portfolio calculations.

Nicrron is the sole configured external model gateway for the deployed AI Q&A path. PRISM is the intended trace and evaluation service and requires separate proof of accepted traces and valid before/after test runs.
