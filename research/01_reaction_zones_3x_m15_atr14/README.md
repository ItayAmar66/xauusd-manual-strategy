# Reaction Zone Catalog — 3× M15 ATR(14)

This folder tracks the original XAUUSD M1 turning-point study using a movement threshold of 3 × M15 ATR(14).

**Current state:** the SHA-256 and row-count manifest is committed. **The raw/CSV data files listed in that manifest have not yet been committed.** The complete, byte-preserving archive is available separately as `XAUUSD_Manual_Strategy_Research_Git_Import.zip`; its contents need importing into this repository before downstream code relies on it.

## Canonical datasets
- `primary/XAUUSD_Phase1_Reversal_Legs_3ATR_M15.csv` — 2,091 unique movements, LONG/SHORT, origin/end, ATR, movement magnitude and duration.
- `primary/XAUUSD_Master_Events.csv` — richer event-level attributes.
- `primary/XAUUSD_Master_Feature_Instances.csv` — 62,242 feature instances.
- `primary/XAUUSD_Master_TF_Snapshots.csv` — 12,546 time-frame OHLC snapshots.
- `primary/XAUUSD_Master_Features_Expanded.csv` — 136,960 expanded feature instances.
- `primary/XAUUSD_ALL_2091_Event_Descriptions.csv` — event explanations.
- `primary/XAUUSD_Event_Situations_ALL_2091.csv` — wider event situations.
- `context/` — FVG and liquidity context.
- `raw/` — original 760,337 M1 bid candles.
- `historical_backtest_not_validated/` — historical candidate results; not audited live trading proof.

## Verification performed
- Every canonical event-level table contains 2,091 distinct event IDs.
- Base legs have 1,047 LONG and 1,044 SHORT events.
- All base legs have `movement_atr >= 3`; smallest recorded value is approximately 3.00613.
- Exact file SHA-256, row counts, and byte sizes are recorded in `FILE_MANIFEST.csv`.

## Important limitations
These are **retrospective outcomes**, not causal entry signals. Event origins cannot be used as if their future move were already known. Any entry setup must be rebuilt from features available at each simulated decision instant, including pivot-confirmation delays. Backtests need spread, slippage, next-bar execution, ambiguous intrabar ordering, actual trading-session timestamps, max 120-minute holding period, sample split and days-without-trades reporting.

This public repository contains research methodology and hashes; keep any sensitive data private if desired.
