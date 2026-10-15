# FVG_H4 — structural stop strategy family

**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**

M1 wick retests still-active FVG on specified higher timeframe and closes through zone boundary; stop beyond rejection candle/FVG boundary.

**Filter:** `h4_aligned`; **Session:** `all`; **Entry mode:** `3`; **TP:** 5R; **Management code:** 0; **SL:** structure / sweep wick / local swing / FVG boundary.

Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.

| Period | Filled trades | Avg net R | Total R | Days with fills |
|---|---:|---:|---:|---:|
| 2025_H1 | 91 | +0.393 | +35.8 | 55 |
| 2025_H2 | 102 | -0.151 | -15.4 | 58 |
| 2026_Q1 | 36 | +0.307 | +11.1 | 20 |
| 2026_Q2Q3_REUSED | 88 | -0.378 | -33.2 | 52 |

**Parameter combinations evaluated in this family:** 1728

**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.
