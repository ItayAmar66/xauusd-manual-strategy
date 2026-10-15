#!/usr/bin/env python3
"""Replay four precommitted-from-2025 complementary structural strategy recipes as ONE position stream.
The four recipes and sorting may use 2025 only; results on 2026 are never consulted to choose.
"""
from pathlib import Path
from numba import njit
import numpy as np,pandas as pd,json
OUT=Path(__file__).resolve().parent
rawp=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if rawp.exists():raw=pd.read_csv(rawp)
else:
 from zipfile import ZipFile
 with ZipFile(OUT.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip') as z:
  f=next(q for q in z.namelist() if q.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  raw=pd.read_csv(z.open(f))
ix=pd.DatetimeIndex(pd.to_datetime(raw.timestamp,unit='ms',utc=True))
t=np.array(ix.asi8//(60*10**9),dtype=np.int64)
o=raw.open.to_numpy();h=raw.high.to_numpy();l=raw.low.to_numpy();c=raw.close.to_numpy()
loc=ix.tz_convert('Asia/Jerusalem');hours=loc.hour+loc.minute/60
allowed=(hours>=6)&(hours<20)&(loc.weekday<5)&np.r_[False,np.diff(t)==1]&(h>l)
sig=pd.read_csv(OUT/'signal_inventory.csv')
x=pd.read_csv(OUT/'all_structural_variants.csv')
# Family-type diversity chosen PRE-2026: daily liquidity reversal, London trend continuation,
# NY trend continuation, NY imbalance reaction. One recipe per planned entry mechanism.
families=['D1_SWEEP','BOS15_PULLBACK','BOS30_PULLBACK','FVG_M15']
recipes=[]
for fam in families:
 a=x[(x.family==fam)&(x['2025_H1_n']>=60)&(x['2025_H2_n']>=60)&(x['2025_H1_meanR']>0)&(x['2025_H2_meanR']>0)].copy()
 a['strength']=a[['2025_H1_meanR','2025_H2_meanR']].min(axis=1)+.07*np.log1p(a['2025_H1_n']+a['2025_H2_n'])
 if not len(a):raise Exception('No 2025-stable configuration for '+fam)
 recipes.append(a.sort_values('strength',ascending=False).iloc[0].to_dict())
(OUT/'portfolio_4_2025_selected.json').write_text(json.dumps([dict(family=q['family'],filter=q['filter'],session=q['session'],entry_mode=int(q['entry_mode']),target_R=int(q['target_R']),management=int(q['management']),h1_n=int(q['2025_H1_n']),h1_R=float(q['2025_H1_meanR']),h2_n=int(q['2025_H2_n']),h2_R=float(q['2025_H2_meanR'])) for q in recipes],indent=2),encoding='utf8')
from collections import defaultdict
F={'none':lambda v:np.ones(len(v),dtype=bool),'h1_aligned':lambda v:v.H1_aligned,'h1_opposed':lambda v:v.H1_opposed,'m15_aligned':lambda v:v.M15_aligned,'m15_opposed':lambda v:v.M15_opposed,'h1_m15_aligned':lambda v:v.H1_aligned&v.M15_aligned,'h4_aligned':lambda v:v.H4_aligned,'weekly_value':lambda v:v.weekly_discount_premium,'h1_weekly':lambda v:v.H1_aligned&v.weekly_discount_premium}
W={'all':(6,20),'london_08_13':(8,13),'ny_14_19':(14,19),'ny_15_18':(15,18)}
sub=[]
for order,r in enumerate(recipes):
 v=sig[sig.family==r['family']];v=v[F[r['filter']](v).astype(bool)];a,b=W[r['session']];v=v[(v.hour_il>=a)&(v.hour_il<b)].copy()
 v['recipe']=r['family'];v['priority']=order;v['mode']=int(r['entry_mode']);v['rr']=int(r['target_R']);v['mgmt']=int(r['management']);sub.append(v)
all_=pd.concat(sub).sort_values(['entry_m1','priority']).reset_index(drop=True)
@njit
def stream(jj,sg,side,stop,ref,modes,rrs,mgmts,priority,op,hi,lo,cl,ts,can):
 out=np.empty((len(jj),15),dtype=np.float64);n=0;locked=-1
 for z in range(len(jj)):
  j=int(jj[z]);si=int(sg[z]);d=int(side[z]);st=stop[z];r=ref[z];mode=int(modes[z]);rr=int(rrs[z]);mgmt=int(mgmts[z])
  if j<=locked:continue
  if mode==0:filled=j;p=op[j]
  else:
   if mode==1:limit=(op[si]+cl[si])/2
   elif mode==2:limit=r
   else:limit=(2*op[si]+cl[si])/3
   if d==1 and limit>=op[j]:limit=op[j]
   if d==-1 and limit<=op[j]:limit=op[j]
   filled=-1;p=0
   # Exclusivity: at most one open pending order. Block competing signals until cancel/expiry.
   for k in range(j,min(len(op),j+16)):
    if ts[k]-ts[j]>15 or (k>j and ts[k]-ts[k-1]>1) or not can[k]:break
    if (d==1 and lo[k]<=limit) or (d==-1 and hi[k]>=limit):
     filled=k;p=min(op[k],limit) if d==1 else max(op[k],limit);break
   if filled<0:
    locked=min(len(op)-1,j+15);continue
  risk=(p-st)*d
  if risk<.65 or risk>150:continue
  target=p+d*rr*risk;curst=st;xp=p;ex=filled;why=9;maxf=0
  for k in range(filled,len(op)):
   if ts[k]-ts[filled]>=120:xp=op[k];ex=k;why=0;break
   if k>filled and ts[k]-ts[k-1]>1:xp=op[k];ex=k;why=2;break
   if d==1:
    if op[k]<=curst:xp=op[k];ex=k;why=-1;break
    if op[k]>=target:xp=target;ex=k;why=1;break
    hitst=lo[k]<=curst;hittp=hi[k]>=target
   else:
    if op[k]>=curst:xp=op[k];ex=k;why=-1;break
    if op[k]<=target:xp=target;ex=k;why=1;break
    hitst=hi[k]>=curst;hittp=lo[k]<=target
   if hitst:xp=curst;ex=k;why=-1;break
   if hittp:xp=target;ex=k;why=1;break
   favor=(hi[k]-p) if d==1 else (p-lo[k]);maxf=max(maxf,favor/risk)
   if mgmt==1 and maxf>=1.5:canst=p
   elif mgmt==2 and maxf>=2:canst=p
   elif mgmt==3 and maxf>=1:canst=p+d*max(0,np.floor(maxf-.00001)-1)*risk
   elif mgmt==4 and maxf>=1:canst=(lo[max(filled,k-4):k+1].min()-.10) if d==1 else (hi[max(filled,k-4):k+1].max()+.10)
   else:canst=curst
   if d==1 and canst>curst:curst=canst
   if d==-1 and canst<curst:curst=canst
  out[n,:]=np.array([j,filled,ex,z,d,p,st,xp,risk,(xp-p)*d/risk-.35/risk,ts[ex]-ts[filled],why,rr,mode,mgmt]);n+=1;locked=ex
 return out[:n]
res=stream(all_.entry_m1.to_numpy(np.int64),all_.signal_m1.to_numpy(np.int64),all_.side.to_numpy(np.int8),all_.stop.to_numpy(float),all_.reference.to_numpy(float),all_['mode'].to_numpy(int),all_.rr.to_numpy(int),all_.mgmt.to_numpy(int),all_.priority.to_numpy(int),o,h,l,c,t,allowed)
rows=[]
for v in res:
 j,fi,ex,zz=[int(z) for z in v[:4]]
 rows.append({'recipe':all_.recipe.iloc[zz],'entry_local':str(loc[fi]),'date_israel':str(loc[fi].date()),'entry_utc':str(ix[fi]),'exit_utc':str(ix[ex]),'entry_m1_index':fi,'exit_m1_index':ex,'side':'LONG' if v[4]>0 else 'SHORT','entry_price':v[5],'structural_stop':v[6],'exit_price':v[7],'risk_distance':v[8],'netR_fee035':v[9],'netR_fee070':v[9]-.35/v[8],'hold_minutes':v[10],'exit_reason':v[11],'targetR':v[12],'mode':v[13],'management':v[14]})
log=pd.DataFrame(rows).sort_values('entry_m1_index')
log.to_csv(OUT/'portfolio_4_2025_selected_trade_log.csv',index=False)
market=raw.groupby(pd.Series(loc.date,index=raw.index)).agg(count=('close','size'),high=('high','max'),low=('low','min'))
market=market[(market['count']>=200)&(market.high>market.low)&(pd.to_datetime(market.index).dayofweek<5)]
periods=[('2025H1','2025-01-01','2025-07-01'),('2025H2','2025-07-01','2026-01-01'),('2026Q1','2026-01-01','2026-04-01'),('2026Q2Q3_REUSED','2026-04-01','2026-09-26')]
rr=[]
for label,lo_,hi_ in periods:
 y=log[(log.date_israel>=lo_)&(log.date_israel<hi_)].copy();days=sum((np.array(market.index,dtype='str')>=lo_)&(np.array(market.index,dtype='str')<hi_))
 v=y.netR_fee035.to_numpy();eq=np.r_[0,np.cumsum(v)]
 rr.append(dict(period=label,market_days=int(days),days_with_trade=int(y.date_israel.nunique()),day_coverage_pct=float(100*y.date_israel.nunique()/max(1,days)),trades=len(y),mean_R=float(v.mean()) if len(y) else None,win_rate_pct=float(np.mean(v>0)*100) if len(y) else None,total_R=float(v.sum()),max_drawdown_R=float(np.min(eq-np.maximum.accumulate(eq))),fee_070_R=float(y.netR_fee070.mean()) if len(y) else None,stop_count=int((y.exit_reason==-1).sum()),target_count=int((y.exit_reason==1).sum()),time_exit_count=int((y.exit_reason==0).sum()),gap_count=int((y.exit_reason==2).sum())))
report=pd.DataFrame(rr);report.to_csv(OUT/'portfolio_4_period_report.csv',index=False)
assert (log.entry_m1_index.iloc[1:].to_numpy()>log.exit_m1_index.iloc[:-1].to_numpy()).all()
assert ((pd.to_datetime(log.entry_utc,utc=True).dt.tz_convert('Asia/Jerusalem').dt.hour>=6)&(pd.to_datetime(log.entry_utc,utc=True).dt.tz_convert('Asia/Jerusalem').dt.hour<20)).all()
print(report.to_string(index=False));print('trades',len(log))