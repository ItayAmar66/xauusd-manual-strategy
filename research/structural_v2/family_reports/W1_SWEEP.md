# W1_SWEEP — structural stop strategy family

**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**

First M1 candle trades beyond previous reference liquidity and closes back inside; initial stop beyond the sweep wick.

**Filter:** `m15_opposed`; **Session:** `ny_14_19`; **Entry mode:** `3`; **TP:** 3R; **Management code:** 1; **SL:** structure / sweep wick / local swing / FVG boundary.

Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.

| Period | Filled trades | Avg net R | Total R | Days with fills |
|---|---:|---:|---:|---:|
| 2025_H1 | 55 | +0.014 | +0.8 | 16 |
| 2025_H2 | 75 | +0.137 | +10.3 | 19 |
| 2026_Q1 | 50 | -0.333 | -16.7 | 11 |
| 2026_Q2Q3_REUSED | 103 | -0.232 | -23.9 | 24 |

**Parameter combinations evaluated in this family:** 1680

**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.
