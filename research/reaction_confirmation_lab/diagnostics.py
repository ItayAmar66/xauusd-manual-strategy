#!/usr/bin/env python3
"""Focused preselected-rule diagnostics and confirmation ablation. Imports deterministic research replay."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import research as R
P=Path(__file__).resolve().parent
chosen=pd.read_csv(P/'train_only_top12.csv').iloc[0]
base=pd.read_csv(P/'../structural_v2/signal_inventory.csv')
base=base[(base.family==chosen.family)&base.H1_aligned&base.M15_aligned&base.H4_aligned]
base=base[(base.hour_il>=15)&(base.hour_il<18)].sort_values('entry_m1').drop_duplicates(['entry_m1','side'])
bi=base.entry_m1.to_numpy(int);bf=base.signal_m1.to_numpy(int);bs=base.side.to_numpy(np.int8);bstr=base.stop.to_numpy(float)
# Run at immediate next open; identical session/trend, M15 ATR, 3R, no trailing.
baseout=R.backtest(bi,bf,bs,bstr,R.ATR[5][bi],R.ATR[15][bi],R.o,R.h,R.l,R.c,R.t,R.hours,R.weekdays,2,3.,0,0,.35)
trade=pd.read_csv(P/'train_chosen_trade_log.csv');trade['date']=trade.entry_local.str.slice(0,10)
# For comparable risk time and period, segment strictly by local day of ENTRY.
def block(df):
 x=[]
 for p,start,end in [('2025_H1','2025-01-01','2025-07-01'),('2025_H2','2025-07-01','2026-01-01'),('2026_Q1','2026-01-01','2026-04-01'),('2026_Q2Q3_REUSED','2026-04-01','2026-09-26')]:
  s=df[(df.date>=start)&(df.date<end)];a=s.net_R.to_numpy();stress=s.stress_R.to_numpy()
  eq=np.r_[0,np.cumsum(a)];dd=float(np.min(eq-np.maximum.accumulate(eq)))
  # weekly-block resampling to estimate dependence and variance; not multiple-testing corrected.
  weeks=pd.to_datetime(s.date).dt.to_period('W').astype(str).to_numpy()
  groups={wk:a[weeks==wk] for wk in np.unique(weeks)}
  arrs=list(groups.values());rng=np.random.default_rng(103);boot=[]
  if len(arrs)>=4:
   for _ in range(2000):
    k=rng.integers(0,len(arrs),len(arrs)); pool=np.concatenate([arrs[j] for j in k]);boot.append(float(pool.mean()))
  q=np.quantile(boot,[.025,.975]) if boot else [np.nan,np.nan]
  x.append(dict(period=p,n=len(s),days=s.date.nunique(),winrate_pct=round(float((a>0).mean()*100),3) if len(a) else None,mean_net_R=round(float(a.mean()),5) if len(a) else None,mean_net_R_cost070=round(float(stress.mean()),5) if len(a) else None,net_total_R=round(float(a.sum()),3),maxDD_R=round(dd,3),week_boot_CI_low=float(q[0]),week_boot_CI_high=float(q[1])))
 return x

im=pd.DataFrame(baseout,columns=['entry_m1','fill_m1','exit_m1','side','price','stop','tp','risk','net_R','gross_R','exit'])
im['date']=R.dates[im.fill_m1.astype(int)];im['stress_R']=im.gross_R-.70/im.risk
confirmed=trade.rename(columns={'net_R_fee070':'stress_R'}).copy()
pd.DataFrame(block(im)).assign(method='IMMEDIATE_AFTER_SWEEP').to_csv(P/'immediate_vs_confirmed_by_period.csv',index=False)
diag=pd.concat([pd.DataFrame(block(im)).assign(method='IMMEDIATE_AFTER_SWEEP'),pd.DataFrame(block(confirmed)).assign(method='M1_CONFIRM_MICRO_BOS3')]).reset_index(drop=True)
diag.to_csv(P/'immediate_vs_confirmed_by_period.csv',index=False)
# True coverage of market weekdays 6–20 with any legitimate M1 bars in 2025 / 2026 dates.
rawdate=R.dates[(R.weekdays<5)&(R.hours>=6)&(R.hours<20)]
counts=pd.Series(rawdate).value_counts()
eligible_days=sorted(counts[counts>=240].index)
for x in [confirmed,im]:
 pass
cov=[]
for name,df in [('after_confirm',confirmed),('immediate',im)]:
 for label,a,b in [('train_2025','2025-01-01','2026-01-01'),('reused_2026','2026-01-01','2026-09-26')]:
  days=[x for x in eligible_days if a<=x<b];vals=df[(df.date>=a)&(df.date<b)]
  cov.append(dict(rule=name,period=label,market_days=len(days),days_traded=vals.date.nunique(),day_coverage_pct=round(100*vals.date.nunique()/len(days),2),n=len(vals)))
pd.DataFrame(cov).to_csv(P/'daily_coverage_comparison.csv',index=False)
# Openly disclose selection in 2025 and reuse of 2026.
result={'baseline_n':len(im),'confirmed_n':len(confirmed),'full_days_eligible':len(eligible_days),'selected_rule':chosen[['family','trigger','filter','session','stop','TP_R','order','management']].to_dict(),'caveats':['2026 review was previously reused','week bootstrap post selection unadjusted for many trials','bid OHLC and approximate fees','no daily-coverage guarantee']}
(P/'diagnostic_summary.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf8')
print(json.dumps(result,indent=2,default=str));print(diag.to_string(index=False));print(pd.DataFrame(cov).to_string(index=False))