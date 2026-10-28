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

## Kalshi public market discovery (V0.3)

Use `python kalshi_public.py --limit 30` for a **one-time** read of open markets. The script saves `kalshi_snapshot.json` locally and displays the number of markets fetched. `--event-ticker <TICKER>` narrows to a specific event. This is **not continuous monitoring**. The connector requires internet access in the environment where it runs. It does not require login or an API key, and it neither estimates cross-exchange profit nor sends Telegram messages. Results are a Kalshi exchange snapshot, not a verified Wealthsimple executable quote.

Kalshi order-book depth, pagination, ForecastEx real-time quotes, market-rule matching, settlement delay and manual broker deep links remain outstanding.

## Cross-venue matching review (V0.5)

`python matching_review.py --kalshi kalshi_snapshot.json --forecast forecast_snapshot.json` compares event titles **only** and creates a non-actionable manual review list. It never verifies outcome equivalence or provides trade signals. The ForecastEx snapshot must be supplied from an authorized source in the same JSON object format with `markets` records containing `contract_id` and `title`. No ForecastEx live connector or verified broker link is available yet. IBKR's authenticated event-contract discovery and price feed are the intended next integration after account access is confirmed.

## V0.6 — strict paper-only paired evaluation

`research_pair.py` provides `assess_pair(pair)` and `format_research_alert(pair, result)`. For a **manually verified** two-venue YES/NO pair it checks separate underlying venues, verified matching resolution criteria, USD denomination, permissions, two fresh timestamps, expected payout on both venues within two hours, prices, fees, depth and $100 combined cost. The two sides receive the same integer contract count. Missing or unverified data is blocked, not guessed. The formula is illustrative and assumes a $1 combined payout, both legs completely filled and fees fully known.

The formatter returns text only for research-review status, prominently labeled **NOT A TRADE SIGNAL**. It never calls Telegram and never places orders. Contract matching from titles alone is still unverified, and no validated live ForecastEx broker feed or Wealthsimple contract mapping exists. Current 25% portfolio cap and 30% per-venue reserves are policy requirements but are NOT YET enforced by this pair evaluator; do not treat the program as live-ready.

Run `python -m unittest discover -s tests -v` to check safeguards. API tokens and trading credentials must never be committed to GitHub.

## V0.7 — balance policy and Telegram safety

The legacy CSV runner no longer transmits Telegram messages even when handed sample data. `telegram_text()` and `format_research_alert()` produce local strings only; nothing sends them to Telegram. Research results are **not live trade recommendations**.

`capital_limits.capital_check()` accepts user-supplied USD available balances for the two venues, current portfolio value and outstanding committed capital. It rejects any modeled allocation breaching a 30% per-venue available-balance reserve or 25% concurrent exposure cap. These balances are not fetched from brokerage APIs and the policy checker is **not yet connected to live alerts**.

No live ForecastEx data, verified identical contracts, independent resolution rule comparisons, wealthsimple deep links, account balance integrations, or safe real-time opportunity alerts are available. Those remain blockers.

## V0.8 — Offline end-to-end safety review

`paper_review.py` connects the separate paired-contract evaluator with the per-venue balance checks. It requires **two manually supplied JSON files** (candidate contract data and balances). It outputs one of `BLOCKED` or `PAPER_REVIEW`. It **never transmits** a Telegram alert, places an order, or asserts that hypothetical input is real.

```bash
python -m unittest discover -s tests -v
python paper_review.py --candidate local_candidate.json --balances local_balances.json
```

Don't commit personal account information, API credentials, balances, or investment records to GitHub. Local JSON input files are ignored by `.gitignore` once named `local_*.json`.

Important limitation: the proof fields `settlement_verified` and `eligibility_verified` remain user-supplied booleans. They are **not** independently validated against exchange or broker rules. Any positive result is a *paper review only*, not a trade recommendation. Broker-level fillability, platform eligibility and Wealthsimple deep links remain unresolved.

## V0.9 — Actual timestamped Kalshi observations

A separate read-only GitHub Actions workflow, **Kalshi quote history (research only)**, has been added under `.github/workflows/kalshi_history.yml`. It is scheduled at minute 07 and 37 every hour (GitHub schedules can be delayed or skipped). You may trigger it manually using **Actions → Kalshi quote history (research only) → Run workflow**.

Each successful run downloads up to the first 100 currently open Kalshi markets from the public API, records a UTC timestamp, and uploads a JSON snapshot as a private GitHub Actions artifact. Artifacts expire after 14 days. The repository does not contain the recorded prices, and the workflow does not place orders, transmit Telegram messages, or make profitability claims.

Caveats: the first 100 markets are only a partial market sample, snapshots are intermittent and the feed lacks verified $100 execution depth. This is *real public Kalshi quote collection*, not a cross-platform backtest. We need contemporaneous, authorized ForecastEx ask prices, equivalent settlement conditions, brokerage fees, available depth, and eventual actual payouts to evaluate any historical matched trade. The offline paper journal is still assumption-based until such recordings are available.

To inspect a snapshot: GitHub → Actions → Kalshi quote history → successful run → **Artifacts** → download `kalshi-research-...`. Do not treat the market list as a tradable alert.

## V1.0 — Optional Telegram capture-status notification

The quote-history workflow still captures Kalshi public data every 30 minutes on its best-effort GitHub schedule, and uploads snapshots retained for 14 days. For now, Telegram sends **only when you manually click Run workflow**, to avoid dozens of messages a day.

To activate:
1. Create a separate Telegram bot in BotFather, if desired, or reuse your own bot. Start a private chat with that bot and send `/start`.
2. Obtain your own Telegram chat ID from the Telegram Bot API `getUpdates` endpoint, or a trusted chat-ID utility. Never paste the token or chat ID into GitHub source code or the conversation.
3. Go to GitHub repository **Settings → Secrets and variables → Actions → New repository secret**. Add two secrets: `CJ_ARB_TELEGRAM_BOT_TOKEN` and `CJ_ARB_TELEGRAM_CHAT_ID`.
4. Go to **Actions → Kalshi quote history (research only) → Run workflow**. After successful collection, the manually triggered run attempts one message labeled **research status**.

If either secret is missing, the workflow still succeeds and no Telegram message is sent. The script reports that Telegram is disabled in its log.

Do not enable trade opportunity alerts until the second authenticated feed, independently verified rules, account permissions, broker-level prices, and matched-depth checks are available.


## V1.1 — Evidence-gated historical audit (not a performance claim)

`historical_audit.py` accepts a JSON **array** of externally supplied historical paired observations, each with both synchronized quote timestamps, depth, fees, outcome verification, recorded settlement time, and actual payout per pair. Run locally with `python historical_audit.py --input local_historical_observations.json`. The output is `local_backtest_audit.json`.

The audit enforces the $100 total paired budget and a 2% *entry-projected* return threshold; then records both gains **and losses** from supplied observed settlement outcomes. It reports `actual_realized_profit_usd: null` because neither source data nor historical fills are authenticated. Boolean evidence fields are externally supplied and cannot independently verify matching rules, executable order-book prices, account permissions or payouts. Do not interpret conditional paper results as a statistically valid win rate, verified return or assured profitability. Missing evidence is blocked. The currently captured Gamma/Kalshi snapshots are **insufficient** to run this full historical audit. The code has unit tests; check GitHub Actions for their results.

The original `paper_journal.py` has also been corrected to use the evaluator's canonical `capital_usd` field when comparing expected payout, rather than a nonexistent `total_cost` field.


## V1.2 — Displayed-depth scenario research

`depth_pair_review.review()` accepts two **manually chosen** public orderbooks, their observation times, which side of Kalshi to buy, explicit per-contract fee assumptions, and a total budget no greater than $100. It walks multiple price levels, refuses stale paired observations (over 20 seconds apart), refuses insufficient depth and missing fee inputs, and lists *hypothetical* combinations meeting at least 2% modeled return. It **does not** validate that the Polymarket token is the opposing outcome or that settlement terms are equivalent. It never labels the results as verified opportunities, never sends Telegram alerts, never trades, and makes no claims of achievable profit. Public orderbooks are non-atomic observations, not historical fills. Trading restrictions still apply.
