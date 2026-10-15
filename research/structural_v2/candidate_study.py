#!/usr/bin/env python3
"""Exploratory post-hoc mechanical structural breakout candidate, fully reproducible trade log.
IMPORTANT: chosen after inspecting historical 2026 results (in sample research) and NOT validated.
"""
from pathlib import Path
import portfolio_test as p
import pandas as pd,numpy as np,json
OUT=Path(__file__).resolve().parent
rules=[('BOS30_PULLBACK','h1_m15_aligned','ny_15_18',3,8,0),('BOS30_PULLBACK','h1_m15_aligned','ny_15_18',1,5,0)]
allout=[];summary=[]
rng=np.random.default_rng(20261015)
for family,filt,sess,mode,tp,manager in rules:
 a=p.sig[p.sig.family==family]
 a=a[(a.H1_aligned&a.M15_aligned)&(a.hour_il>=15)&(a.hour_il<18)].sort_values('entry_m1')
 x=p.stream(a.entry_m1.to_numpy(np.int64),a.signal_m1.to_numpy(np.int64),a.side.to_numpy(np.int8),a.stop.to_numpy(float),a.reference.to_numpy(float),np.full(len(a),mode),np.full(len(a),tp),np.full(len(a),manager),np.zeros(len(a),dtype=int),p.o,p.h,p.l,p.c,p.t,p.allowed,.65,150)
 cname=f'{family}|{filt}|{sess}|limit{mode}|tp{tp}|manager{manager}'
 d=[]
 for row in x:
  fi=int(row[1]);ex=int(row[2]);risk=row[8]
  d.append(dict(strategy=cname,entry_local=str(p.loc[fi]),date_il=str(p.loc[fi].date()),direction='LONG' if row[4]==1 else 'SHORT',entry_price=row[5],initial_stop=row[6],exit_price=row[7],initial_risk=risk,net_R_fee035=row[9],net_R_fee070=row[9]-.35/risk,exit_m1_index=ex,entry_m1_index=fi,exit_reason=row[11],duration_minutes=row[10]))
 df=pd.DataFrame(d)
 allout.append(df)
 for period,lo,hi in p.periods:
  sub=df[(df.date_il>=lo)&(df.date_il<hi)];v=sub.net_R_fee035.to_numpy();n=len(v)
  eq=np.r_[0,np.cumsum(v)];maxdd=float(np.min(eq-np.maximum.accumulate(eq)))
  # Block bootstrap at WEEK granularity, exploratory only; this is NOT a multiple-testing-adjusted CI.
  ci=[np.nan,np.nan]
  if n>10:
   wk=pd.to_datetime(sub.date_il).dt.to_period('W').astype(str)
   groups=[g.net_R_fee035.to_numpy() for _,g in sub.groupby(wk)]
   bs=[]
   for j in range(1200):
    choices=rng.integers(len(groups),size=len(groups));pool=np.concatenate([groups[k] for k in choices]);bs.append(float(pool.mean()))
   ci=np.percentile(bs,[2.5,97.5]).tolist()
  summary.append(dict(strategy=cname,period=period,entries=n,days=sub.date_il.nunique(),mean_R=float(v.mean()) if n else None,mean_R_stress_070=float(sub.net_R_fee070.mean()) if n else None,win_rate_pct=float(np.mean(v>0)*100) if n else None,max_drawdown_R=maxdd,bootstrap_week_ci_95_low=ci[0],bootstrap_week_ci_95_high=ci[1],stop_exits=int((sub.exit_reason==-1).sum()),target_exits=int((sub.exit_reason==1).sum()),time_exits=int((sub.exit_reason==0).sum())))
trade=pd.concat(allout);trade.to_csv(OUT/'posthoc_BOS30_candidate_trade_log.csv',index=False)
results=pd.DataFrame(summary);results.to_csv(OUT/'posthoc_BOS30_candidate_periods.csv',index=False)
print(results[['strategy','period','entries','days','mean_R','mean_R_stress_070','bootstrap_week_ci_95_low','bootstrap_week_ci_95_high']].to_string(index=False))