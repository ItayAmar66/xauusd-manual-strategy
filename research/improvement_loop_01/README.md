# Iteration 01 — Diagnose the XAUUSD M1 confirmation entry / repair exits

**Status:** Complete, exploratory. **No verified tradable +1R edge**. This is the first reproducible iteration of a process, not a promise of unlimited automated research.

## Research question

Why did the prior 30M sweep → M1 MICRO_BOS3 confirmation → next-minute open, H1/M15/H4-aligned, NY-open entry, M15 ATR14 1x stop and 3R target (120 minute max hold) weaken in April–September 2026? Can we improve its payoff without changing its entry signal, creating lookahead, or choosing the parameter based on the later period?

**Input:** the exact 253-trade file `../reaction_confirmation_lab/train_chosen_trade_log.csv`, generated from 760,337 XAUUSD M1 OHLC bid candles (2025-01-01–2026-09-25). The 30M sweep candidate and its parameters had themselves been selected post hoc from previous research. The 2026 set is **reused research data, not untouched OOS**.

## 1. Diagnosis of the original 3R rule

| Period | Trades | Avg net R | Stop rate | Full 3R TP rate | Reached +1R before exit |
|---|---:|---:|---:|---:|---:|
| 2025 | 133 | +0.358 | 51.9% | 24.8% | 57.9% |
| 2026Q1 | 41 | +0.344 | 48.8% | 24.4% | 61.0% |
| 2026Q2–Q3 | 79 | −0.022 | 64.6% | 17.7% | 46.8% |

The 2026Q2–Q3 deterioration is driven by **more stops and fewer full winners**, not simply worse fee conversion. Observation is not proof of what caused the price move. Values derived from the fixed chosen rule's original fill/exit log; the minute-by-minute path audit excludes the exit bar when measuring favorable excursion before exit to avoid uncertain within-minute high/low order.

## 2. Matched-entry controlled exit-management iteration

We varied **only** TP and trade manager on the **same 253 historically recorded entries and initial stops**. A replay of TP3 with fixed stop reproduced the original trade log at machine precision — asserted in code. This makes the management-only comparison particularly direct; it **does not** re-allow newly unblocked signals after an earlier exit, so it is not a complete standalone strategy backtest.

- TPs: 2R, 3R, 4R, 5R, 6R, 8R.
- Managers: fixed; BE after +1R; BE after +1.5R; BE after +2R; trailing step 0.5R starting after +1R.
- M1 replay: stop-first within uncertain candle; trailing stop changes take effect only next candle; open gaps and data gaps handled conservatively; max 120-minute hold.
- Assumed full-roundtrip transaction friction $0.35 in XAUUSD price units; extra cost $0.70 column for sensitivity.
- Parameter selection: rank using **2025 training only** (with sample penalty), not 2026.

| Management | 2025 avg net R | 2026Q1 avg net R | 2026Q2–Q3 avg net R |
|---|---:|---:|---:|
| 3R fixed (control) | +0.358 | +0.344 | −0.022 |
| 4R fixed | +0.382 | +0.363 | +0.070 |
| **6R fixed** — 2025 selected | **+0.389** | **+0.370** | **+0.118** |
| 6R BE at +1R | +0.210 | +0.190 | +0.255 |

**Key caution:** Although 6R fixed was selected by 2025 train ranking (slightly higher than 8R fixed), the change is not statistically supported as a robust improvement. A paired week-block bootstrap of the 6R-vs-3R difference in 2026Q2–Q3 gives roughly **+0.139R**, 95% exploratory interval **−0.038R to +0.358R**. The absolute 6R mean has a 95% exploratory interval **−0.294R to +0.588R**. Only 5/79 trades reached the full 6R in that period, exposing concentration in a few large moves. These bootstrap intervals do not correct for multiple comparisons or dependence caused by the originally selected rule.

This is **not** 50% win rate at 3R, and not +1R/trade. Do not trade live based on these findings.

## Why iteration beats random combinatorial search

Each iteration should have (1) a measurable failure, (2) one proposed change, (3) a frozen comparison to the baseline, (4) train-only selection, (5) separate chronology-based reviews and uncertainty tests, (6) an explicit rollback when the change does not hold. Otherwise unlimited looping over the same tape guarantees overfitting and misleading winners.

### Next iteration / hypothesis, not yet validated

The failed-setup pattern is a **reduced probability of moving even +1R** after confirmation (61.0% → 46.8%). Test *time until M1 structural confirmation*, relative distance of entry from the sweep extreme, and movement in R during the first 5–10 bars. These variables must be measurable **at entry**, not computed from future successful movement. Evaluate baseline vs one predeclared causal condition with an untouched later data slice, preferably **new tick/ask data with actual spread and slippage**. Avoid selecting new rules using the already consulted 2026Q2–Q3 window.

## Reproduction

The input file and the full M1 tape already live in this repository under `research/reaction_confirmation_lab/` and `research/15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip` respectively.

```bash
python -m pip install pandas numpy
python 'research/improvement_loop_01/audit.py'
python 'research/improvement_loop_01/management_ablation.py'
```

Files generated:
- `trade_path_metrics.csv` — conservative path diagnostics for all 253 original trades.
- `period_diagnostics.csv` — reason/magnitude-by-period summary.
- `matched_entry_management_30x3.csv` — all 30 TP/management configurations in three periods.
- `matched_entry_management_trades.csv` — all 7,590 counterfactual trade results.
- `management_selected_train_only.csv` — ranked using 2025 data only.
- `bootstrap_paired_weekly.csv` — paired and absolute block-bootstrap interval results.