# XAUUSD Manual Strategy — Research Repository

This repository is dedicated to developing a **manual XAUUSD trading strategy** based on reproducible historical evidence.

## Research dataset

The canonical historical catalog contains **2,091** retrospectively labeled price movements of at least **3 × M15 ATR(14)**, with the turning-price extreme marked on M1:
- 1,047 LONG, 1,044 SHORT.
- 440 London, 514 New York, 470 Asia, 667 Outside.
- Original interval: January 2025 through September 2026.
- All 2,091 event IDs are unique. Minimum recorded movement/ATR: 3.006132829.

## Intended tree

`research/01_reaction_zones_3x_m15_atr14/`
- `primary/`: canonical reversal legs, master events, features, snapshots, event descriptions.
- `context/`: FVG lifecycle, FVG-at-origin and liquidity interactions.
- `raw/`: source M1 bid OHLC.
- `historical_backtest_not_validated/`: archived candidate backtests; **not** production performance claims.
- `FILE_MANIFEST.csv`: SHA-256/rows/byte sizes for every source.

## Project targets (not achieved claims)

- Entry only during London 09:00–12:00 fixed UTC+3 and New York 16:30–18:30 fixed UTC+3.
- Every position closed within **120 minutes**.
- At least one trade on **90% of eligible market days**.
- **Realized average net R/trade ≥ +1** on robust out-of-sample testing; entry mechanics, RR, and TP are flexible.

## Critical methodology

An observed reversal leg is labeled **after the subsequent movement**. Its origin is NOT an automatically tradable real-time signal. Never test a strategy by pretending that a hindsight-labeled origin was known at entry.

For future backtests: preserve causality of level availability and fills, trading costs, stop/TP chronology and ambiguous one-minute candles, 120-minute time exits, unique execution IDs, session-local clocks versus Israel DST, overlap restrictions, walk-forward holdout, and the exact data manifest SHA-256.

## Upload status

**Important:** This repository was initialized with documentation. Large historical datasets are contained in the locally prepared import archive `XAUUSD_Manual_Strategy_Research_Git_Import.zip`, which must be uploaded to this repository separately. Do not assume source files are present until they appear in the tree. The ZIP includes the full SHA-256 manifest and 14 data files.
