# FVG_H1 — structural stop strategy family

**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**

M1 wick retests still-active FVG on specified higher timeframe and closes through zone boundary; stop beyond rejection candle/FVG boundary.

**Filter:** `weekly_value`; **Session:** `ny_14_19`; **Entry mode:** `3`; **TP:** 8R; **Management code:** 1; **SL:** structure / sweep wick / local swing / FVG boundary.

Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.

| Period | Filled trades | Avg net R | Total R | Days with fills |
|---|---:|---:|---:|---:|
| 2025_H1 | 58 | +0.148 | +8.6 | 45 |
| 2025_H2 | 64 | -0.329 | -21.1 | 47 |
| 2026_Q1 | 34 | -0.108 | -3.7 | 22 |
| 2026_Q2Q3_REUSED | 80 | -0.207 | -16.5 | 62 |

**Parameter combinations evaluated in this family:** 1728

**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.
