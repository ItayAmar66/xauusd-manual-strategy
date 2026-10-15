# BOS30_PULLBACK — structural stop strategy family

**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**

M1 closes beyond preceding 15/30/60-minute price-range extreme; stop beyond signal/preceding ten-minute opposite swing.

**Filter:** `h1_m15_aligned`; **Session:** `ny_15_18`; **Entry mode:** `2`; **TP:** 3R; **Management code:** 1; **SL:** structure / sweep wick / local swing / FVG boundary.

Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.

| Period | Filled trades | Avg net R | Total R | Days with fills |
|---|---:|---:|---:|---:|
| 2025_H1 | 187 | +0.171 | +31.9 | 95 |
| 2025_H2 | 189 | +0.012 | +2.3 | 100 |
| 2026_Q1 | 111 | -0.133 | -14.7 | 51 |
| 2026_Q2Q3_REUSED | 172 | +0.088 | +15.2 | 88 |

**Parameter combinations evaluated in this family:** 1728

**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.
