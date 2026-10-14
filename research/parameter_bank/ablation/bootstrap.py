#!/usr/bin/env python3
"""Exploratory week-cluster bootstrap for three post-hoc identified positive-in-both-splits combinations.
CIs DO NOT correct for 348-way multiple selection. Never claim confirmed alpha.
"""
from pathlib import Path
from zipfile import ZipFile
from numba import njit
import numpy as np,pandas as pd,json
HERE=Path(__file__).resolve().parent; B=HERE.parent
F=pd.read_csv(B/'condition_bank_m5.csv');x={c:F[c].to_numpy(bool) for c in F.select_dtypes(include='bool').columns}
if not x:x={c:F[c].to_numpy(bool) for c in F if c not in ('entry_utc','entry_israel','entry_date','entry_m1_index','m5_atr14','signal_m5_close','fib_zone_low','fib_zone_high')}
Z=B.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
if not Z.exists():Z=Path('/mnt/data/XAUUSD_Manual_Strategy_Research_Git_Import.zip')
with ZipFile(Z) as z:
 n=next(k for k in z.namelist() if k.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
 M=pd.read_csv(z.open(n))
mins=M.timestamp.to_numpy(np.int64)//60000;op=M.open.to_numpy(float);hi=M.high.to_numpy(float);lo=M.low.to_numpy(float);cl=M.close.to_numpy(float)
entry=F.entry_m1_index.to_numpy(np.int64);atr=F.m5_atr14.to_numpy(float)
@njit
def replay(sig,ent,atr,op,hi,lo,cl,mins,mode):
 rr=4. if mode==1 else 5.;out=np.empty(len(sig),np.float64);ids=np.empty(len(sig),np.int64);gap=np.empty(len(sig),np.int8);cnt=0;locked=-1
 for i in range(len(sig)):
  d=sig[i];j=ent[i]
  if d==0 or j<=locked:continue
  risk=1.5*atr[i]
  if risk<.4 or not np.isfinite(risk):continue
  p=op[j];sl=p-d*risk;tp=p+d*rr*risk;maxf=0.;k=j;g=0
  while k<len(op):
   if k>j and mins[k]-mins[k-1]>1:k-=1;xp=cl[k];g=1;break
   if mins[k]-mins[j]>=120:xp=op[k];break
   if d==1:
    if op[k]<=sl:xp=op[k];break
    if op[k]>=tp:xp=tp;break
    if lo[k]<=sl:xp=sl;break
    if hi[k]>=tp:xp=tp;break
    fav=hi[k]-p
   else:
    if op[k]>=sl:xp=op[k];break
    if op[k]<=tp:xp=tp;break
    if hi[k]>=sl:xp=sl;break
    if lo[k]<=tp:xp=tp;break
    fav=p-lo[k]
   maxf=max(maxf,fav)
   if mode==1:
    can=p if maxf>=1.5*risk else sl
   else:
    can=p+d*max(0.,(np.floor(maxf/(.5*risk))-2)*.5*risk) if maxf>=risk else sl
   if d==1 and can>sl:sl=can
   if d==-1 and can<sl:sl=can
   k+=1
  if k>=len(op):k=len(op)-1;xp=cl[-1];g=1
  out[cnt]=d*(xp-p)/risk-.35/risk if not g else -1-.35/risk
  ids[cnt]=i;gap[cnt]=g;cnt+=1;locked=k
 return ids[:cnt],out[:cnt],gap[:cnt]
# Deliberately report only the 3 variants positive on both dev/reused windows (posthoc exploration).
configs=[('engulfing','M15_H1_ALIGNED','be1.5_tp4',1),('engulfing','M15_H1_ALIGNED','ladder0.5_tp5',2),('breakout12','M15_H1_ALIGNED','ladder0.5_tp5',2)]
np.random.seed(2142)
rows=[]
for trig,cond,manager,mode in configs:
 u=x['m15_up']&x['h1_up'];d=x['m15_down']&x['h1_down']
 if trig=='engulfing':u=u&x['m5_engulf_bull'];d=d&x['m5_engulf_bear']
 else:u=u&x['m5_breakup'];d=d&x['m5_breakdown']
 sig=np.where(u&~d,1,np.where(d&~u,-1,0)).astype(np.int8)
 ix,ret,gap=replay(sig,entry,atr,op,hi,lo,cl,mins,mode)
 e=F.entry_date.to_numpy(dtype='U10')[ix];mask=e>='2026-04-01';rv=ret[mask];dates=pd.to_datetime(e[mask]);w=dates.to_period('W-SUN')
 agg=pd.DataFrame({'week':w,'r':rv,'count':np.ones(len(rv),int)}).groupby('week').agg({'r':'sum','count':'sum'})
 rewards=agg.r.to_numpy();counts=agg['count'].to_numpy();L=len(rewards)
 # Sample weeks, preserving within-week correlations; this is an unadjusted interval.
 draws=np.random.randint(L,size=(3000,L));v=rewards[draws].sum(axis=1)/counts[draws].sum(axis=1)
 rows.append({'trigger':trig,'filter':cond,'manager':manager,'review_n':len(rv),'review_avg_R':float(rv.mean()),'review_boot95_lower_R':float(np.quantile(v,.025)),'review_boot95_upper_R':float(np.quantile(v,.975)),'review_bootstrap_prob_mean_positive':float(np.mean(v>0)),'review_gap_stress_n':int(gap[mask].sum()),'statistical_note':'posthoc selected; no familywise correction; cannot call confirmed edge'})
out=pd.DataFrame(rows)
out.to_csv(HERE/'three_positive_variants_bootstrap.csv',index=False)
print(out.to_string(index=False))