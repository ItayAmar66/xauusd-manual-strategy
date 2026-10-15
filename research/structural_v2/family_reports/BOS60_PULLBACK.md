# BOS60_PULLBACK — structural stop strategy family

**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**

M1 closes beyond preceding 15/30/60-minute price-range extreme; stop beyond signal/preceding ten-minute opposite swing.

**Filter:** `h1_weekly`; **Session:** `ny_14_19`; **Entry mode:** `3`; **TP:** 5R; **Management code:** 4; **SL:** structure / sweep wick / local swing / FVG boundary.

Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.

| Period | Filled trades | Avg net R | Total R | Days with fills |
|---|---:|---:|---:|---:|
| 2025_H1 | 73 | +0.246 | +17.9 | 34 |
| 2025_H2 | 53 | -0.081 | -4.3 | 26 |
| 2026_Q1 | 25 | -0.198 | -5.0 | 11 |
| 2026_Q2Q3_REUSED | 64 | -0.143 | -9.2 | 35 |

**Parameter combinations evaluated in this family:** 1728

**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.
