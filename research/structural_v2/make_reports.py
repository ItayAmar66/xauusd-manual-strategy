#!/usr/bin/env python3
"""Produce all 21 per-family study cards and complete audit data from already computed files."""
from pathlib import Path
import numpy as np,pandas as pd,json,hashlib
ROOT=Path(__file__).resolve().parent
s=pd.read_csv(ROOT/'train_selected_family.csv')
a=pd.read_csv(ROOT/'all_structural_variants.csv')
ledger=pd.read_csv(ROOT/'portfolio_4_2025_selected_trade_log.csv')
cards=ROOT/'family_reports';cards.mkdir(exist_ok=True)
labels={'SWEEP':'First M1 candle trades beyond previous reference liquidity and closes back inside; initial stop beyond the sweep wick.','BOS':'A liquidity sweep is followed within 12 M1 bars by a close breaking previously available five-candle structure; stop beyond original sweep extreme.','PULLBACK':'M1 closes beyond preceding 15/30/60-minute price-range extreme; stop beyond signal/preceding ten-minute opposite swing.','FVG':'M1 wick retests still-active FVG on specified higher timeframe and closes through zone boundary; stop beyond rejection candle/FVG boundary.'}
for q in s.itertuples(index=False):
 name=q.family
 typ='SWEEP' if name.endswith('SWEEP') else 'PULLBACK' if 'PULLBACK' in name else 'FVG' if 'FVG' in name else 'BOS'
 vec=a[a.family==name]
 # itertuples converts invalid identifiers starting digits to _ positions, so use direct Series lookup for 2025 columns, not _asdict names
 record=s[s.family==name].iloc[0]
 # instead make stable text with Series fields
 lines=[f'# {name} — structural stop strategy family','', '**RESEARCH — NOT VALIDATED FOR LIVE TRADING.**','',labels[typ],'',f'**Filter:** `{record["filter"]}`; **Session:** `{record["session"]}`; **Entry mode:** `{int(record.entry_mode)}`; **TP:** {int(record.target_R)}R; **Management code:** {int(record.management)}; **SL:** structure / sweep wick / local swing / FVG boundary.','', 'Modes: 0=market next bar; 1=limit halfway through signal candle; 2=limit at broken structure; 3=limit one-third candle body. Stops never fixed ATR multiples. Limit order expires after 15 minutes. Assumed 0.35 XAUUSD price cost.', '', '| Period | Filled trades | Avg net R | Total R | Days with fills |','|---|---:|---:|---:|---:|']
 for period in ('2025_H1','2025_H2','2026_Q1','2026_Q2Q3_REUSED'):
  lines.append(f"| {period} | {int(record[period+'_n'])} | {record[period+'_meanR']:+.3f} | {record[period+'_totalR']:+.1f} | {int(record[period+'_days'])} |")
 lines+=['',f"**Parameter combinations evaluated in this family:** {len(vec)}",'', '**Caution:** Selection used 2025H1 only; however 2026 is not fully independent due to repeated historical studies. No performance estimate is a guarantee. See parent README for conservative bid-only OHLC simulation rules and costs.']
 (cards/f'{name}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
# Per-day no-trade detection using trusted study calendar from period_report
market=pd.read_csv(ROOT/'portfolio_4_period_report.csv')
# Family contribution by period, not used to change 2025-only configuration.
ledger['period']=pd.cut(pd.to_datetime(ledger.date_israel),bins=[pd.Timestamp('2024-12-31'),pd.Timestamp('2025-06-30'),pd.Timestamp('2025-12-31'),pd.Timestamp('2026-03-31'),pd.Timestamp('2026-09-26')],labels=['2025H1','2025H2','2026Q1','2026Q2Q3_REUSED'])
rows=[]
for (fam,per),g in ledger.groupby(['recipe','period'],observed=True):
 v=g.netR_fee035.to_numpy();eq=np.r_[0,np.cumsum(v)];losstreak=0;best=0
 for x in v:
  if x<=0:losstreak+=1;best=max(losstreak,best)
  else:losstreak=0
 rows.append(dict(family=fam,period=str(per),trades=len(g),avg_R=float(v.mean()),R_sum=float(v.sum()),winrate_pct=100*np.mean(v>0),median_structural_stop_distance=float(g.risk_distance.median()),avg_cost_drag_R=float((.35/g.risk_distance).mean()),maxDD_R=float(np.min(eq-np.maximum.accumulate(eq))),losing_streak=best,early_stop_pct=100*np.mean(g.exit_reason==-1)))
pd.DataFrame(rows).to_csv(ROOT/'portfolio_component_diagnostics.csv',index=False)
# Weekly-cluster uncertainty on every portfolio period, bootstrap no optimization.
rng=np.random.default_rng(20261015);out=[]
for p,g in ledger.groupby('period',observed=True):
 gw=[sub.netR_fee035.to_numpy() for _,sub in g.groupby(pd.to_datetime(g.date_israel).dt.to_period('W').astype(str))]
 sims=[]
 for _ in range(2000):
  ids=rng.integers(0,len(gw),size=len(gw));a=np.concatenate([gw[i] for i in ids]);sims.append(float(a.mean()))
 arr=np.percentile(sims,[2.5,97.5]);out.append(dict(period=str(p),mean_R=float(g.netR_fee035.mean()),bootstrap_week_95_low_R=float(arr[0]),bootstrap_week_95_high_R=float(arr[1]),week_count=len(gw),number_of_parameter_tests=36192,multiple_comparison_adjusted=False))
pd.DataFrame(out).to_csv(ROOT/'portfolio_week_bootstrap.csv',index=False)
q=dict(candles_m1=760337,expected_variants=36192,executed_variants=len(a),signal_candidates=220638,actual_signals_count=pd.read_csv(ROOT/'signal_inventory.csv',usecols=['family']).shape[0],portfolio_trades=len(ledger),family_reports=len(list(cards.glob('*.md'))),portfolio_trade_entry_range=[str(ledger.entry_utc.min()),str(ledger.entry_utc.max())],observed_no_overlap=bool((ledger.entry_m1_index.iloc[1:].to_numpy()>ledger.exit_m1_index.iloc[:-1].to_numpy()).all()),limits_no_more_than_120=bool((ledger.hold_minutes<=120).all()),entry_hours_eligible=bool(pd.to_datetime(ledger.entry_utc,utc=True).dt.tz_convert('Asia/Jerusalem').dt.hour.between(6,19).all()))
# prevent length miscount due variable 'a' shadowing: calculate actual
q['executed_variants']=len(pd.read_csv(ROOT/'all_structural_variants.csv',usecols=['family']))
(ROOT/'QA_reproducibility.json').write_text(json.dumps(q,indent=2),encoding='utf8')
assert q['observed_no_overlap'] and q['limits_no_more_than_120'] and q['entry_hours_eligible']
assert q['executed_variants']==q['expected_variants'] and q['family_reports']==21
print(json.dumps(q,indent=2))