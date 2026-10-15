# W1_BOS — structural stop strategy family

**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**

A liquidity sweep is followed within 12 M1 bars by a close breaking previously available five-candle structure; stop beyond original sweep extreme.

**Filter:** `none`; **Session:** `ny_14_19`; **Entry mode:** `0`; **TP:** 8R; **Management code:** 0; **SL:** structure / sweep wick / local swing / FVG boundary.

Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.

| Period | Filled trades | Avg net R | Total R | Days with fills |
|---|---:|---:|---:|---:|
| 2025_H1 | 65 | -0.186 | -12.1 | 27 |
| 2025_H2 | 55 | +0.180 | +9.9 | 27 |
| 2026_Q1 | 30 | +0.242 | +7.3 | 14 |
| 2026_Q2Q3_REUSED | 58 | +0.077 | +4.5 | 30 |

**Parameter combinations evaluated in this family:** 1680

**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.
