# D1_BOS — structural stop strategy family

**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**

A liquidity sweep is followed within 12 M1 bars by a close breaking previously available five-candle structure; stop beyond original sweep extreme.

**Filter:** `m15_opposed`; **Session:** `ny_15_18`; **Entry mode:** `2`; **TP:** 8R; **Management code:** 0; **SL:** structure / sweep wick / local swing / FVG boundary.

Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.

| Period | Filled trades | Avg net R | Total R | Days with fills |
|---|---:|---:|---:|---:|
| 2025_H1 | 61 | +0.643 | +39.2 | 31 |
| 2025_H2 | 67 | -0.029 | -2.0 | 40 |
| 2026_Q1 | 42 | +0.034 | +1.4 | 22 |
| 2026_Q2Q3_REUSED | 68 | -0.378 | -25.7 | 40 |

**Parameter combinations evaluated in this family:** 1728

**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.
