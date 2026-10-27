# Crypto Junction — Prediction Arbitrage Scanner

Research-only project. **No live exchange execution and no verified real-time cross-venue feed yet.** Separate from the Kraken scanner.

## V0.2 scope

- Two venues, matching YES/NO contract research.
- $100 USD maximum *combined* spend per opportunity; 2% minimum modeled net ROI.
- Target estimated payout within two hours, not merely event end.
- Reject stale or missing quotes, unverified settlement equivalence and insufficient depth.
- Optional Telegram messages are labeled **research candidate — not a trade signal**.
- No credentials committed; never paste private trading keys or bot tokens into source code.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Run sample (intentionally rejected)

```bash
python scanner.py
```

The included CSV sample is stale and unmatched and must print `REJECT`.

## Current limitations

1. This version reads user-supplied sample CSV records, **not live market feeds**.
2. Kalshi's public API is not proof a quote is executable through Wealthsimple Predict.
3. ForecastEx public delayed datasets are not appropriate for time-sensitive alerts; eligible IBKR real-time access must be validated.
4. Event terms, resolution, currency, fees, contract increments and settlement delays must be verified independently.
5. Account-specific balance tracking and exposure/reserve enforcement are still to be built.
6. Never place real orders based solely on research messages; the two legs may fail to fill together.

Next: API connectors (read-only), explicit rule-match allowlist, synchronized depth, broker mapping, balance ledger and manual alert links.
