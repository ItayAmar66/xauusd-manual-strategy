# Final canonical leg catalog audit — 2,091 labeled moves

## Verdict

**PASS for internal consistency and M1 endpoint verification. NOT YET PROVEN as an exhaustive catalog of every valid 3×ATR move, nor as 2-hour tradable signals.**

The catalog is a **retrospectively segmented** set of successive price legs. A fully independent exhaustive sweep needs the original segmentation algorithm, precise M15 ATR construction and handling of potentially overlapping/embedded moves, applied to the whole M1 feed.

## Results (computed from original CSV + original M1 candles)

| Test | Result |
|---|---:|
| Catalog records | 2,091 |
| Unique event_id | 2,091 |
| Recorded movement / ATR threshold >= 3 | 2,091 / 2,091 |
| Lowest recorded ratio | 3.0061328290143305 |
| Absolute movement matches `abs(end-origin)` | 2,091 / 2,091 |
| Movement ratio matches `movement_usd / m15_atr14` | 2,091 / 2,091 |
| Correct LONG/SHORT direction versus price change | 2,091 / 2,091 |
| Duration matches UTC timestamps exactly | 2,091 / 2,091 |
| End timestamp strictly before start | 0 |
| Starting timestamps found in original 760,337 M1 candles | 2,091 / 2,091 |
| Ending timestamps found in original M1 candles | 2,091 / 2,091 |
| Start price is precisely M1 candle high or low | 2,091 / 2,091 |
| End price is precisely M1 candle high or low | 2,091 / 2,091 |
| Positive-duration overlap between consecutive legs | 0 |
| Consecutive legs with the exact same end/start UTC minute | 1,998 |
| Events with M1 intrabar-order ambiguity and 0-minute duration | 26 |
| Events lasting 1–120 minutes | 724 (34.62%) |
| Events lasting 0–120 minutes, including ambiguous | 750 (35.87%) |
| Events lasting **more than 120 minutes** | **1,341 (64.13%)** |
| Median duration | 191 minutes |
| Max duration | 2,474 minutes |

## Interpretation for a manual strategy

- **Keep the complete 2,091-event catalog** as the historical reference for studying where strong reactions started.
- When evaluating whether a *full 3ATR movement completed within 120 min of its historical start*, focus on **724 nonzero-duration** events; flag the 26 ambiguous events separately. Do not treat this filter as an entry backtest.
- The 1,341 longer legs can still contain a profitable 120-minute entry **after** an actual causal signal; they are not automatically worthless. Equally, they do not prove a full 3ATR move was capturable within two hours.
- Future outcome measurement MUST start the clock at the actual real-time entry, not the hindsight-identified leg origin.
- This study does not independently recalculate M15 ATR from raw M1, and does not prove that alternate overlapping or smaller embedded 3ATR moves were all captured.
- `qa_flag=INTRABAR_SEQUENCE_AMBIGUOUS`: 26 events, not suitable for intrabar ordering without tick data.

## Decision

**Use all 2,091 events for reaction-zone discovery**, preserving QA flags; use only *causally discoverable signals* and at most 120 minutes **from entry** for trading-strategy tests. No blanket claim that these are *all* possible qualifying movements.

See `audit_canonical_legs.py` for exact automated checks.
