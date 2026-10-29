# 24-hour read-only observation: implementation plan

Status: development only. Do not dispatch until validated.

## Constraints
- Kalshi and Polymarket public market data only; no credentials, order placement, or trading.
- Six sequential four-hour windows, each persisting timestamped order books and a progress summary.
- GitHub-hosted jobs must stay below the six-hour job timeout; allow for setup and artifact upload.
- Each window must recover the preceding window's archive, verify timestamps and counts, and append rather than overwrite.
- Ensure checkpoint artifacts survive failures and that a missing checkpoint fails closed.
- Final aggregation must distinguish verified from potential arbitrage and retain settlement warnings.
- Capital modeling: $5,000 total; $2,500 per exchange; dynamic sizing; strictly positive modeled net profit after all modeled costs. Do not restore obsolete percentage reserves, exposure caps, or a 2% minimum.
- Report executable ask prices, depth, fees, quote timestamps, and non-atomic execution risk.
- No Kraken changes.

## Implementation checks before launch
1. Inspect collector CLI, output formats, and backtest inputs.
2. Build checkpointed execution without relying on a single >6-hour job.
3. Verify artifact handoff, retry/idempotency, and cancellation behavior.
4. Validate on a short dry run with multiple checkpoints and no trading.
5. Review GitHub Actions runtime/cost and ensure the full 24-hour observation is explicitly launched only after validation.
