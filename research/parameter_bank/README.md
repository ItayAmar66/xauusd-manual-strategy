# XAUUSD Adaptive Condition Bank — research v0.1

**Project goal:** Do not demand one fixed set of five confirmations. Maintain a *bank of real-time-observable parameters*, classify the market, assemble candidate LONG/SHORT playbooks and evaluate whether each additional condition raises **net expectancy**, not just retrospective winner frequency.

**Status: EXPLORATORY, NOT A VALIDATED TRADING SYSTEM.** This library does **not** establish ≥+1R/trade, and the Apr–Sep 2026 review segment was previously inspected in earlier research. New forward data are needed for confirmation.

## Market, hours and trading objective

- XAUUSD; 760,337 original M1 bid OHLC records; historical period 2025-01 through 2026-09.
- **New entry between 06:00 inclusive and 20:00 exclusive, `Asia/Jerusalem` DST-aware.** Exit may be later.
- **Max planned holding time: 120 minutes after entry.** Data gaps can make this unachievable; explicit exception counts retained. No ticks, actual spreads or live broker pricing available.
- Aspirational target: ≥1 new trade per trading day, mean **+1R net per trade**. The two goals must be evaluated jointly, not optimized separately by forced low-quality trades.
- Training 2025-01 to 2026-03; Apr–Sep 2026 reused **exploratory** review, NOT independent validation.

## Files

| File | Purpose |
|---|---|
| `build_bank.py` | Build real-time M5 signal-time parameter matrix from archived M1 prices + historic FVG lifecycle |
| `condition_bank_m5.csv` | **75,264 eligible completed M5 decisions × 43 boolean flags**, risk ATR, Fibonacci zone, timestamps |
| `condition_prevalence.json` | How often each flag appears in the *full tradable market* rather than successful 3/4ATR legs |
| `PARAMETER_DICTIONARY.md` | Every parameter, prevalence, exact methodological caveats |
| `test_playbooks.py` | 16 illustrative LONG/SHORT composite rule templates, three trade-management choices and two ATR stops |
| `composite_prototypes_96.csv` | Results of **96 rule/management/stop combinations** |
| `prototypes_fixed4R_comparison.csv` | Transparent *common* entry: 1.5×M5 ATR stop, fixed 4R TP; no favorable post-hoc manager selection |
| `prototype_trade_log.csv` | Entry/exit/time/price outcome in R for **all** exploratory trade simulations |
| `PLAYBOOKS.md` | All 16 rule definitions and summary rankings |
| `summary.json` | Programmatic research stage metadata |
| `make_docs.py` | Generate reports directly from computed outputs |

## 5 layers, but NOT 5 mandatory confirmations

1. **Daily/weekly context:** 4 fully completed Israeli weeks Premium/Discount, prior day/week high-low, actual sweep/reclaim.
2. **H1/H4 zone:** still-active fair value gaps and confirmed 2-right-bar H1 swing Fibonacci 0.618–0.786 (not a hypothetical untouched level).
3. **M15 context:** most recently closed M15 trend (EMA20/50) and completed-bar displacement.
4. **M5 entry trigger:** rejection, engulfing, prior 12-M5 bar breakout, reclaim, momentum and RSI. Future M1 entry signals (breaker/CHOCH) are **not implemented yet**.
5. **Exit:** fixed 4R, BE at 1.5R, or half-R ladder; ATR stop x1.5 or x2; 120min time expiry. **Structural stops and target liquidity are not implemented yet.**

Two styles: **REVERSAL** (liquidity grab / discount / FVG rejection) vs **CONTINUATION** (HTF trend / pullback FVG / momentum). Mixing opposite narratives merely to increase the count of confirmations is discouraged.

## What has been checked

Signals are computed on **fully closed** M5 data, with M15/H1/H4 inputs available only after their bar close. Price orders enter at the **next existing M1 open**. Sweep/reclaim is defined with the M5 wick and close and does not borrow retrospective origin labels. Historic successful 15M/5M reversal catalogs are not read by either signal generator.

The M1 backtest is conservative when target+stop hit within same M1 bar (STOP first), only tightens stop *after* the bar, and subtracts an **assumed** XAUUSD price friction of $0.35 per completed trade. It is not a broker-executable tick simulation. The unavoidable gap/market-closure exceptions are explicitly visible as `over_120min` in per-configuration results.

## Main prototype conclusion

**0/16 fixed-4R illustrative playbooks achieved +1R average on the REUSED review period.** The strongest observed positive reusable-period result was small and/or sparsely traded. The weekly H1/FVG trend templates often give large daily coverage but did not display reliable positive expectancy in the development period.

For example, a **C04_M15FVG_trend_engulf** configuration at 1.5 ATR / fixed 4R produced about **+0.138R** in the reused 2026 period, **-0.091R** in training and **88.1%** review-day coverage. This is NOT a validated edge.

## Research protocol — what to do next

- Add M1 real-time structure (confirmed swing, BOS/CHOCH, breaker retest and iFVG), confluence-distance (ATR units), liquidity targets, structural stop, and FVG zone age/first vs repeated touch.
- Evaluate conditional edge using *all market opportunities* (including non-events), and **compare each extra filter to the identical base trigger without it**. Require material uplift and sufficient count; penalize highly correlated confirmations.
- Use grouped/time-series walk-forward validation, embargo around adjacent events and bootstrap by market day. The April–September 2026 samples already influenced research, so do not rename them a virgin holdout.
- Compare every variant under both assumed frictions $0.35/$0.70 and realistic broker ticks. Test 120-minute time exits under gaps; distinguish a theoretical historical setup from a practical order.
- Find a portfolio of **complementary** playbooks maximizing daily coverage + expected R, with total risk constraints and no duplicate entries on the same market move. Do not artificially force a trade on days where expected edge is absent.
