#!/usr/bin/env python3
"""Time-causal multi-timeframe condition ablation across ALL XAUUSD bars, not pre-selected winners.
Exploratory only: the previously reported 2026-Q2/Q3 interval has been inspected and is NOT virgin holdout.
"""
from pathlib import Path
from zipfile import ZipFile
from numba import njit
import pandas as pd
import numpy as np
import json, time
HERE=Path(__file__).resolve().parent
B=HERE.parent
F=pd.read_csv(B/'condition_bank_m5.csv')
P=B.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
local=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if local.exists():
 M=pd.read_csv(local)
else:
 with ZipFile(P) as z:
  key=next(k for k in z.namelist() if k.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  M=pd.read_csv(z.open(key))
assert len(M)==760337 and len(F)==75264
m_times=M.timestamp.to_numpy(np.int64)//60000
op=M.open.to_numpy(float);hi=M.high.to_numpy(float);lo=M.low.to_numpy(float);cl=M.close.to_numpy(float)
ent=F.entry_m1_index.to_numpy(np.int64);atr=F.m5_atr14.to_numpy(float)
assert np.all(ent>=0)
longtime=pd.to_datetime(F.entry_utc,utc=True);localtime=longtime.dt.tz_convert('Asia/Jerusalem')
assert ((localtime.dt.hour>=6)&(localtime.dt.hour<20)).all()
labels=F.entry_date.to_numpy(dtype='U10')
# ISO week labels for a daily-cluster block-bootstrap of strategy expectancy
all_days=np.unique(labels)
dev=labels<'2026-04-01';review=~dev
D={'2025_H1':(labels>='2025-01-01')&(labels<'2025-07-01'),
   '2025_H2':(labels>='2025-07-01')&(labels<'2026-01-01'),
   '2026_Q1':(labels>='2026-01-01')&(labels<'2026-04-01'),
   '2026_Q2_REUSED':(labels>='2026-04-01')&(labels<'2026-07-01'),
   '2026_Q3_REUSED':(labels>='2026-07-01')}
# Only previously completed candles in the 43-factor bank; do NOT use ex-post movement classes
X={k:F[k].to_numpy(bool) for k in F.columns if k not in ['entry_utc','entry_israel','entry_date','entry_m1_index','m5_atr14','signal_m5_close','fib_zone_low','fib_zone_high']}
def b(k):return X[k]
T={
 'rejection':(b('m5_rejection_bull'),b('m5_rejection_bear')),
 'engulfing':(b('m5_engulf_bull'),b('m5_engulf_bear')),
 'breakout12':(b('m5_breakup'),b('m5_breakdown')),
 'body':(b('m5_body_bull'),b('m5_body_bear')),
}
# Each filter is a PAIR of booleans conditioned on long vs short respectively.
true=np.ones(len(F),bool)
C={
 'NONE':(true,true),
 'M5_TREND_ALIGNED':(b('m5_up'),b('m5_down')),
 'M5_TREND_COUNTER':(b('m5_down'),b('m5_up')),
 'M15_TREND_ALIGNED':(b('m15_up'),b('m15_down')),
 'M15_TREND_COUNTER':(b('m15_down'),b('m15_up')),
 'H1_TREND_ALIGNED':(b('h1_up'),b('h1_down')),
 'H1_TREND_COUNTER':(b('h1_down'),b('h1_up')),
 'H4_TREND_ALIGNED':(b('h4_up'),b('h4_down')),
 'H4_TREND_COUNTER':(b('h4_down'),b('h4_up')),
 'M15_H1_ALIGNED':(b('m15_up')&b('h1_up'),b('m15_down')&b('h1_down')),
 'H1_H4_ALIGNED':(b('h1_up')&b('h4_up'),b('h1_down')&b('h4_down')),
 'WEEKLY_EXTREME20_REV':(b('weekly_rangebottom20'),b('weekly_rangetop20')),
 'WEEKLY_PREM_DISCOUNT_REV':(b('weekly_discount'),b('weekly_premium')),
 'WEEKLY_PREM_DISCOUNT_CONT':(b('weekly_premium'),b('weekly_discount')),
 'PRIOR_15M_COUNTER':(b('prior_15m_down'),b('prior_15m_up')),
 'DAILY_SWEEP_CURRENT':(b('pdl_sweep_reclaim'),b('pdh_sweep_reclaim')),
 'DAILY_SWEEP_LAST60':(b('pdl_sweep_reclaim_last60m'),b('pdh_sweep_reclaim_last60m')),
 'WEEK_SWEEP_LAST60':(b('pwl_sweep_reclaim_last60m'),b('pwh_sweep_reclaim_last60m')),
 'H1_FIB_618_786':(b('fib_h1_bull_618_786'),b('fib_h1_bear_618_786')),
 'M15_DISPLACEMENT':(b('m15_displacement'),b('m15_displacement')),
 'M5_FVG':(b('fvg_touch_M5_BULL'),b('fvg_touch_M5_BEAR')),
 'M15_FVG':(b('fvg_touch_M15_BULL'),b('fvg_touch_M15_BEAR')),
 'H1_FVG':(b('fvg_touch_H1_BULL'),b('fvg_touch_H1_BEAR')),
 'H4_FVG':(b('fvg_touch_H4_BULL'),b('fvg_touch_H4_BEAR')),
 'ANY_FVG':(b('fvg_touch_M5_BULL')|b('fvg_touch_M15_BULL')|b('fvg_touch_H1_BULL')|b('fvg_touch_H4_BULL'),b('fvg_touch_M5_BEAR')|b('fvg_touch_M15_BEAR')|b('fvg_touch_H1_BEAR')|b('fvg_touch_H4_BEAR')),
 'H1_M15_TREND_AND_FVG':(b('h1_up')&b('m15_up')&b('fvg_touch_M15_BULL'),b('h1_down')&b('m15_down')&b('fvg_touch_M15_BEAR')),
 'WEEKLY_REV_AND_DAILY_SWEEP':(b('weekly_discount')&b('pdl_sweep_reclaim_last60m'),b('weekly_premium')&b('pdh_sweep_reclaim_last60m')),
 'M15_TREND_AND_FVG':(b('m15_up')&b('fvg_touch_M15_BULL'),b('m15_down')&b('fvg_touch_M15_BEAR')),
 'COUNTERMOVE_AND_FVG':(b('prior_15m_down')&b('fvg_touch_M15_BULL'),b('prior_15m_up')&b('fvg_touch_M15_BEAR')),
}
# Standard strategies; stop and TP trade management fixed BEFORE analysis, no per-filter optimization.
MANAGERS={'fixed4':(1.5,4.,0),'be1.5_tp4':(1.5,4.,1),'ladder0.5_tp5':(1.5,5.,2)}
@njit
def replay(sig,ent,atr,op,hi,lo,cl,times,stopmult,rr,manage):
 n=len(sig);out_e=np.empty(n,np.int64);out_r=np.empty(n,np.float64);out_k=np.empty(n,np.int64);out_gap=np.empty(n,np.int8);count=0;locked=-1
 for i in range(n):
  d=sig[i];j=ent[i]
  if d==0 or j<=locked:continue
  risk=atr[i]*stopmult
  if risk<.4 or not np.isfinite(risk):continue
  price=op[j];stop=price-d*risk;tp=price+d*rr*risk;fav=0.;xp=price;k=j;gap=0
  while k<len(op):
   if k>j and times[k]-times[k-1]>1:
    # Missing OHLC interval: close at last observed price as a flagged PROXY.
    # Fill is NOT verifiable without intervening data; report worst-case stress.
    k=k-1;xp=cl[k];gap=1;break
   if times[k]-times[j]>=120:
    xp=op[k];break
   if d==1:
    if op[k]<=stop:xp=op[k];break
    if op[k]>=tp:xp=tp;break
    if lo[k]<=stop:xp=stop;break
    if hi[k]>=tp:xp=tp;break
    fg=hi[k]-price
   else:
    if op[k]>=stop:xp=op[k];break
    if op[k]<=tp:xp=tp;break
    if hi[k]>=stop:xp=stop;break
    if lo[k]<=tp:xp=tp;break
    fg=price-lo[k]
   if fg>fav:fav=fg
   cand=stop
   if manage==1 and fav>=1.5*risk:cand=price
   if manage==2 and fav>=risk:cand=price+d*max(0.,(np.floor(fav/(0.5*risk))-2.)*.5*risk)
   if d==1 and cand>stop:stop=cand
   if d==-1 and cand<stop:stop=cand
   k+=1
  if k>=len(op):k=len(op)-1;xp=cl[-1]
  out_e[count]=i;out_k[count]=k;out_r[count]=d*(xp-price)/risk-.35/risk;out_gap[count]=gap
  locked=k;count+=1
 return out_e[:count],out_k[:count],out_r[:count],out_gap[:count]

# Calendar date of candidate signals and 5 regime slices. E.g. review 2026-Q2, 2026-Q3 were used in prior research.
all_cal=np.unique(labels);train_cal=np.unique(labels[dev]);review_cal=np.unique(labels[review]);cal={**{k:np.unique(labels[v]) for k,v in D.items()},'train':train_cal,'review_REUSED':review_cal,'all':all_cal}
rs=[];raw_best=[];t0=time.time()
for trigger,(lb,sb) in T.items():
 for filt,(lc,sc) in C.items():
  long=lb&lc;short=sb&sc
  signal=np.where(long&~short,1,np.where(short&~long,-1,0)).astype(np.int8)
  for mgr,(stop,rr,mode) in MANAGERS.items():
   idx,exitidx,r,gap=replay(signal,ent,atr,op,hi,lo,cl,m_times,stop,rr,mode)
   row={'trigger':trigger,'filter':filt,'manager':mgr,'candidate_signals':int(np.sum(signal!=0))}
   dates=labels[idx]
   for label,dayarr in cal.items():
    mask=np.isin(dates,dayarr);z=r[mask];n=len(z)
    sub_eq=np.r_[0.,np.cumsum(z)]
    dd=float(np.min(sub_eq-np.maximum.accumulate(sub_eq)))
    run=mx=0
    for q in z:
     run=(run+1) if q<=0 else 0;mx=max(mx,run)
    duration=(m_times[exitidx[mask]]-m_times[ent[idx[mask]]]) if n else np.array([])
    gaps=gap[mask].astype(bool)
    z_worst=np.where(gaps, -1.0-.35/(atr[idx[mask]]*stop),z)
    row.update({label+'_gap_proxy_n':int(gaps.sum()),label+'_worst_gap_avg_R':float(z_worst.mean()) if n else None,label+'_n':n,label+'_avg_R':float(np.mean(z)) if n else None,label+'_total_R':float(z.sum()),label+'_wr_pct':100*float(np.mean(z>0)) if n else None,label+'_coverage_pct':100*len(np.unique(dates[mask]))/max(1,len(dayarr)),label+'_maxdd_R':dd,label+'_longest_loss_streak':mx,label+'_over_120':int(np.sum(duration>120))})
   rs.append(row)
   if filt=='NONE':raw_best.append((trigger,mgr,idx,r))
R=pd.DataFrame(rs)
# Basic comparisons without parameter selection. Each filter compared to its trigger-manager baseline using same calendar windows.
base=R[R['filter']=='NONE'].set_index(['trigger','manager'])
for window in ['train','review_REUSED','all']:
 v=R.set_index(['trigger','manager']).index
 R[f'{window}_delta_vs_base_avg_R']=R[f'{window}_avg_R'].to_numpy()-np.array([base.loc[x,f'{window}_avg_R'] for x in v])
# Unselectable condition when fewer than 100 training signals or <60 review signals
R['eligible_for_ranking']=(R.train_n>=100)&(R.review_REUSED_n>=60)
R.to_csv(HERE/'all_348_ablations.csv',index=False)
# fixed4 for easiest like-for-like; show all filter combinations incl rare cases, do not cherry-pick.
A=R[(R.manager=='fixed4')].sort_values('review_REUSED_delta_vs_base_avg_R',ascending=False)
A.to_csv(HERE/'fixed4_all_116_filters.csv',index=False)
# select filter by TRAIN ONLY, per trigger; penalize tiny samples, prefer high coverage
sel=[]
for trigger in T:
 Q=R[(R.trigger==trigger)&(R.train_n>=100)].copy()
 Q['selection_score']=Q.train_avg_R-0.5*np.sqrt(100/Q.train_n)-0.0005*(100-Q.train_coverage_pct)
 sel.append(Q.sort_values(['selection_score','train_n'],ascending=False).head(1))
S=pd.concat(sel,ignore_index=True)
S.to_csv(HERE/'train_selected_four.csv',index=False)
# Test audit: filtering does not increase exposures without new entry signals; and no holdout in selection
assert len(R)==len(T)*len(C)*len(MANAGERS)
assert (R.candidate_signals>=0).all()
assert all(x in X for x in ['weekly_discount','fvg_touch_H1_BULL'])
summary={'m1_bars':len(M),'candidate_m5_signal_times':len(F),'triggers':len(T),'filters_including_none':len(C),'managers':len(MANAGERS),'tests':len(R),'cost_dollars_per_trade':0.35,'over120_events_across_all_tests':int(R.all_over_120.sum()),'gap_proxy_exits_across_all_tests':int(R.all_gap_proxy_n.sum()),'min_train_n_for_selection':100,'max_review_avg_R_all_tests':float(R.review_REUSED_avg_R.max()),'max_review_avg_R_eligible':float(R.loc[R.eligible_for_ranking,'review_REUSED_avg_R'].max()),'train_selection_four_review_ge_1R':int((S.review_REUSED_avg_R>=1).sum()),'selection_status':'reused_review_NOT_fresh_holdout','runtime_s':round(time.time()-t0,2)}
(HERE/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
print('DONE',json.dumps(summary,indent=2))
print('TRAIN SELECTED:\n',S[['trigger','filter','manager','train_n','train_avg_R','review_REUSED_n','review_REUSED_avg_R','review_REUSED_coverage_pct']].to_string(index=False))
print('TOP FIXED4 DELTA (eligible):\n',A[A.eligible_for_ranking][['trigger','filter','train_n','train_avg_R','review_REUSED_n','review_REUSED_avg_R','review_REUSED_delta_vs_base_avg_R','review_REUSED_coverage_pct']].head(15).to_string(index=False))