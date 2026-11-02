# Fee formula reconciliation — research only

Primary references (checked November 2026):
- Kalshi: https://kalshi.com/fee-schedule
- Polymarket: https://help.polymarket.com/en/articles/13364478-trading-fees
- Polymarket market-category schedules: https://polymarket.com/fees

## What can be modeled

Kalshi's general taker curve is `0.07 × contracts × price × (1-price)`, multiplied by the applicable **series-specific** fee multiplier and rounded as prescribed by the effective schedule. Do not assume multiplier 1 for every ticker.

Polymarket's published standard taker formula is `contracts × feeRate × price × (1-price)`. The July 2026 help article lists sports at 0.05, but the live category schedule distinguishes sports versions and exceptions. Do not assume that every sports token is 0.05.

The CLOB `/fee-rate` response `base_fee: 1000` is **not** proof of a 10% taker fee or a 0.05 feeRate. Do not convert it without reconciling the endpoint's semantics, the applicable schedule version, and fee-on-buy accounting. A public py-clob-client issue #326 reports a discrepancy and is **not** an authoritative resolution: https://github.com/Polymarket/py-clob-client/issues/326

## Required before promoting estimates

1. Resolve Kalshi series fee multiplier and schedule effective at the observed timestamp.
2. Resolve Polymarket token category/version, fee rate, and fee-on-buy units.
3. Confirm both venue rounding, maker/taker assumptions, and fees for multi-level fills.
4. Review settlement differences and payout equivalence independently.
5. Preserve raw evidence, model version, and source timestamp per priced observation.

Until then all results remain illustrative, `trade_allowed=false`, `fee_inputs_verified=false`. A positive modeled return is not an executable arbitrage.
