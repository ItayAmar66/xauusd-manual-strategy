# ASIA_SWEEP — structural stop strategy family

**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**

First M1 candle trades beyond previous reference liquidity and closes back inside; initial stop beyond the sweep wick.

**Filter:** `h1_weekly`; **Session:** `all`; **Entry mode:** `0`; **TP:** 8R; **Management code:** 0; **SL:** structure / sweep wick / local swing / FVG boundary.

Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.

| Period | Filled trades | Avg net R | Total R | Days with fills |
|---|---:|---:|---:|---:|
| 2025_H1 | 80 | -0.035 | -2.8 | 18 |
| 2025_H2 | 125 | -0.384 | -48.0 | 22 |
| 2026_Q1 | 27 | -0.707 | -19.1 | 5 |
| 2026_Q2Q3_REUSED | 115 | +0.107 | +12.3 | 25 |

**Parameter combinations evaluated in this family:** 1728

**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.
