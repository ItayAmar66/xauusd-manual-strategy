#!/usr/bin/env python3
"""Analyze next-day performance of a 2-completed-day 3R-win-rate gate."""
from pathlib import Path
import numpy as np,pandas as pd,json
P=Path(__file__).resolve().parent
tr=pd.read_csv(P/'all_ten_strategy_trades.csv')
g=pd.read_csv(P/'two_day_eligibility_by_strategy_date.csv')
met=pd.read_csv(P/'rotation_policy_metrics.csv')
# Check the gate is history-only and has at least one closed trade per prior day.
assert (g.loc[g.active_aggregate,['n_day1','n_day2']].min(axis=1)>=1).all()
assert (g.loc[g.active_aggregate,'two_day_winrate']>=.5).all()
assert (g.loc[g.active_aggregate,'two_day_mean_R']>0).all()
assert (g['date']>g['prev_day2']).all() and (g['prev_day2']>g['prev_day1']).all()
# Per strategy gate effects in each period
rows=[]
for sn,x in tr.groupby('strategy'):
 for p in ('2025_dev','2026Q1_reused','2026Q2Q3_reused'):
  xx=x[(x.entry_israel_date<'2026-01-01') if p=='2025_dev' else ((x.entry_israel_date>='2026-01-01')&(x.entry_israel_date<'2026-04-01') if p=='2026Q1_reused' else (x.entry_israel_date>='2026-04-01'))]
  base=xx
  gate=xx[xx.gate_agg]
  rows.append(dict(strategy=sn,period=p,n_all=len(base),n_after2day=len(gate),mean_R_all=base.net_R.mean(),mean_R_after2day=gate.net_R.mean(),lift_R=(gate.net_R.mean()-base.net_R.mean()) if len(gate) else np.nan,TP3_hit_all=(base.reason==1).mean(),TP3_hit_after2day=(gate.reason==1).mean() if len(gate) else np.nan,days_after2day=gate.entry_israel_date.nunique()))
result=pd.DataFrame(rows);result.to_csv(P/'per_strategy_gate_lift.csv',index=False)

# Nonparametric day bootstrap is descriptive (reused test interval, not a fresh holdout).
# Each sampled calendar day carries *all* filled trades with that day's origin.
rng=np.random.default_rng(20261022)
pairs=[]
for p in ['2025_dev','2026Q1_reused','2026Q2Q3_reused']:
 a=met[(met.strategy=='PORTFOLIO')&(met.period==p)]
 dates=g.loc[g.date.map(lambda s: '2025_dev' if s<'2026-01-01' else ('2026Q1_reused' if s<'2026-04-01' else '2026Q2Q3_reused'))==p,'date'].unique()
 nday=len(dates)
 for policy in ['all','gate_agg','gate_strict','gate_min4']:
  t=pd.read_csv(P/f'portfolio_{policy}_trades.csv')
  t=t[t.entry_israel_date.isin(dates)]
  # Calendar-day profitability; zero days remain explicitly represented.
  by=t.groupby('entry_israel_date').agg(daily_R=('net_R','sum'),trades=('net_R','size'),hits=('reason',lambda x:sum(x==1)))
  daily=np.array([by.loc[d,'daily_R'] if d in by.index else 0 for d in dates])
  ndraw=5000
  sample=rng.integers(0,len(daily),size=(ndraw,len(daily)))
  means=daily[sample].mean(axis=1)
  pairs.append(dict(period=p,policy=policy,days=len(daily),daily_mean_R=float(np.mean(daily)),boot95_low=float(np.quantile(means,.025)),boot95_hi=float(np.quantile(means,.975)),days_positive=int((daily>0).sum()),days_negative=int((daily<0).sum()),days_flat=int((daily==0).sum()),n_trades=len(t)))
pd.DataFrame(pairs).to_csv(P/'calendar_day_bootstrap.csv',index=False)

summary={
 'declaration':'Win for the 2-day activation gate means an actual 3R TP fill (reason==1), not just positive time exit',
 'decide_when':'Start of next eligible Israel market day, after outcomes of preceding two completed weekdays',
 'min_completed_trades_each_prev_day':1,
 'minimum_closed_history':2,
 'cross_market_positioning':'replay from all raw candidate signals; only one portfolio position; no overlapping fills',
 'next_day_negative_at_50pct':'checked in the saved metrics',
 'data_reuse_warning':'2026 data has been reviewed many times already, so no truly untouched holdout',
 'original_strategy_warning':'archive of historical signals only, causal entry model not reimplemented',
 'proxies_warning':'other nine are reduced experimental implementations and are not certified ICT strategy definitions',
 'FVG_warning':'the reference gap can persist without fully validated lifecycle/mitigation, especially H1/AMD',
 'same_bar_stop_first':True,
 'slippage_spread':'0.35 XAUUSD price units approximate roundtrip, not broker confirmed',
 'max_holding_minutes':120,
 'number_of_strategy_rules':int(tr.strategy.nunique()),
 'filled_paper_trades':int(len(tr)),
 'trade_period_rows':int(len(met)),
 'days_eligibility_rows':int(len(g)),
 'seed_bootstrap':20261022,
}
(P/'QA_summary.json').write_text(json.dumps(summary,indent=2))
print(result.to_string(index=False));print(pd.DataFrame(pairs).to_string(index=False));print(summary)