#!/usr/bin/env python3
"""XAUUSD reaction-zone -> later M1 trigger -> M1 next-open or resting-limit backtest.

The anchored zone catalog is produced using only pre-entry bars by
../structural_v2/research.py (21 families), not historical winning-leg pivots.
Simulated order execution pessimistically prioritizes stops within same M1 bar.
"""
from pathlib import Path
from time import perf_counter
import numpy as np, pandas as pd, json
from numba import njit
P=Path(__file__).resolve().parent
PROJECT=P.parent
src=Path('/mnt/data/rebuild/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if src.exists():m=pd.read_csv(src)
else:
 from zipfile import ZipFile
 with ZipFile(PROJECT/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip') as z:
  member=next(n for n in z.namelist() if n.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  m=pd.read_csv(z.open(member))
idx=pd.to_datetime(m.timestamp,unit='ms',utc=True)
m=m.set_index(idx)[['open','high','low','close']];n=len(m)
o=m.open.to_numpy();h=m.high.to_numpy();l=m.low.to_numpy();c=m.close.to_numpy()
t=np.array(m.index.asi8//(60*10**9),dtype=np.int64)
lcl=m.index.tz_convert('Asia/Jerusalem');hours=np.array(lcl.hour+lcl.minute/60.);weekdays=np.array(lcl.weekday)
dates=np.array(lcl.date,dtype='str')
validentry=(hours>=6)&(hours<20)&(weekdays<5)
# Determine M5/M15 ATR14 as-of the minute; no incomplete HTF candle.
ATR={}
for tf in (5,15):
 g=m.resample(f'{tf}min',label='left',closed='left').agg({'high':'max','low':'min','close':'last'})
 q=m.close.resample(f'{tf}min',label='left').count()
 g=g[q==tf]
 tr=pd.concat([g.high-g.low,(g.high-g.close.shift()).abs(),(g.low-g.close.shift()).abs()],axis=1).max(axis=1)
 a=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
 a.index=a.index+pd.Timedelta(minutes=tf)
 ATR[tf]=a.reindex(m.index,method='ffill').to_numpy()
# Only pre-existing structural-zone candidates from prior study, not successful-reversal labels.
sig=pd.read_csv(PROJECT/'structural_v2'/'signal_inventory.csv',usecols=['family','signal_m1','side','stop','reference','H1_aligned','M15_aligned','H4_aligned','weekly_discount_premium'])
keep=['D1_SWEEP','W1_SWEEP','ASIA_SWEEP','15M_SWEEP','30M_SWEEP','60M_SWEEP','120M_SWEEP','FVG_M5','FVG_M15','FVG_H1','FVG_H4','D1_BOS','30M_BOS']
sig=sig[sig.family.isin(keep)].copy().drop_duplicates(['family','signal_m1','side']).sort_values('signal_m1').reset_index(drop=True)
# Arrays to test M1 confirmations at k=anchor+1..+6; ensure zone's structural stop has not broken.
clen=len(sig);si=sig.signal_m1.to_numpy('int64');side=sig.side.to_numpy('int8');ss=sig.stop.to_numpy(float)
fh=np.empty((5,clen),np.int64);fh.fill(-1)
# PRE-registered 5 confirmation types. Future bar is never used to label a signal until it CLOSES.
for gap in range(1,7):
 k=si+gap;ok=(k+1<n)&(t[k]-t[si]==gap)&(t[k+1]-t[k]==1)&validentry[k+1]
 for q in range(1,gap+1):
  j=si+q;ok &= np.where(side==1,l[j]>ss,h[j]<ss)
 up=side==1;dn=~up
 # must close directionally and there is a further reaction AFTER initial zone touch.
 bullish=(c[k]>o[k]);bearish=(c[k]<o[k]);directional=np.where(up,bullish,bearish)
 prev_high=h[k-1];prev_low=l[k-1]
 prev_open=o[k-1];prev_close=c[k-1]
 checks=[
  directional & np.where(up,c[k]>h[si],c[k]<l[si]), # break reaction candle wick
  directional & np.where(up,(c[k]>np.maximum(prev_open,prev_close)) & (o[k]<=np.minimum(prev_open,prev_close)),(c[k]<np.minimum(prev_open,prev_close))&(o[k]>=np.maximum(prev_open,prev_close))),# body engulf
  directional & np.where(up,c[k]>np.maximum.reduce((h[si-1],h[si-2],h[si-3])),c[k]<np.minimum.reduce((l[si-1],l[si-2],l[si-3]))), # 3-min structure break formed pre-anchor
  directional & np.where(up,(c[k]>c[k-1])&(c[k-1]>c[k-2]),(c[k]<c[k-1])&(c[k-1]<c[k-2])), # 2 bullish closes
  directional & np.where(up,(l[k]>h[k-2])&(c[k]>prev_high),(h[k]<l[k-2])&(c[k]<prev_low)), # newly closed M1 directional FVG
 ]
 for typ,chk in enumerate(checks):
  ix=np.where(ok & chk & (fh[typ]<0))[0]
  fh[typ,ix]=k[ix]
# Set candidate stop levels, add confirmations to long-form inventory.
features=['H1_aligned','M15_aligned','H4_aligned','weekly_discount_premium']
coll=[]
for typ,label in enumerate(['RESPONSE_WICK_BREAK','BODY_ENGULF','MICRO_BOS3','TWO_CANDLE_PUSH','M1_FVG_DISPLACEMENT']):
 mask=fh[typ]>=0;ii=np.where(mask)[0];conf=fh[typ,ii]
 df=pd.DataFrame(dict(family=sig.family.iloc[ii].to_numpy(),trigger=label,anchor_m1=si[ii],confirm_m1=conf,entry_m1=conf+1,side=side[ii],stop_struct=ss[ii],reference=sig.reference.iloc[ii].to_numpy(),**{k:sig[k].iloc[ii].to_numpy() for k in features}))
 coll.append(df)
cand=pd.concat(coll,ignore_index=True).sort_values('entry_m1').drop_duplicates(['family','trigger','entry_m1','side']).reset_index(drop=True)
ce=cand.entry_m1.to_numpy('int64');cf=cand.confirm_m1.to_numpy('int64')
cand['atr5']=ATR[5][ce];cand['atr15']=ATR[15][ce];cand['hour_il']=hours[ce];cand['date_israel']=dates[ce]
cand.to_csv(P/'confirmed_entry_inventory.csv',index=False)
print('verified zone anchors',len(sig),'M1-confirmed candidates',len(cand),flush=True)
# Strict no-same-minute future knowledge: signal after candle cf closes; order may fill from next open (ce).
@njit
def backtest(entries,confirm,sides,struct_stops,atr5,atr15,op,hi,lo,cl,tm,hour,weekday,stopkind,rr,manage,order,fee):
  out=np.empty((len(entries),11),np.float64);num=0;locked=-1
  for ii in range(len(entries)):
   e=int(entries[ii]);k=int(confirm[ii]);d=int(sides[ii]);struct=struct_stops[ii]
   if e<=locked:continue
   if stopkind==0:sl=struct
   elif stopkind==1:sl=op[e]-d*atr5[ii]
   elif stopkind==2:sl=op[e]-d*atr15[ii]
   elif stopkind==3: # wider of structural and completed M5 ATR
    sl=min(struct,op[e]-atr5[ii]) if d==1 else max(struct,op[e]+atr5[ii])
   else:sl=struct
   if not np.isfinite(sl):continue
   fill_idx=e;price=op[e]
   if order==1:
    # Resting limit at candle body midpoint, for 5 minutes; never fill outside approved entry hours.
    lim=(op[k]+cl[k])/2
    if d==1 and lim>=op[e]:lim=op[e]
    if d==-1 and lim<=op[e]:lim=op[e]
    fill_idx=-1
    for z in range(e,min(e+6,len(op))):
     if tm[z]-tm[e]>5 or (z>e and tm[z]-tm[z-1]!=1):break
     if not (6<=hour[z]<20 and weekday[z]<5):break
     if (d==1 and lo[z]<=lim) or (d==-1 and hi[z]>=lim):
      fill_idx=z;price=min(op[z],lim) if d==1 else max(op[z],lim);break
    if fill_idx<0:continue
   risk=(price-sl)*d
   if risk<.65 or risk>70 or not np.isfinite(risk):continue
   target=price+d*rr*risk;curr=sl;xp=price;end=fill_idx;reason=9;peak=0.
   for z in range(fill_idx,len(op)):
    if tm[z]-tm[fill_idx]>=120:
     xp=op[z];end=z;reason=0;break
    if z>fill_idx and tm[z]-tm[z-1]!=1:
     xp=op[z];end=z;reason=2;break
    # Stop-first on ambiguous OHLC minute. BUY limit may fill and stop in same minute.
    if d==1:
     if op[z]<=curr:xp=op[z];end=z;reason=-1;break
     if op[z]>=target:xp=target;end=z;reason=1;break
     touched_sl=lo[z]<=curr;touched_tp=hi[z]>=target
    else:
     if op[z]>=curr:xp=op[z];end=z;reason=-1;break
     if op[z]<=target:xp=target;end=z;reason=1;break
     touched_sl=hi[z]>=curr;touched_tp=lo[z]<=target
    if touched_sl:xp=curr;end=z;reason=-1;break
    if touched_tp:xp=target;end=z;reason=1;break
    fav=(hi[z]-price)/risk if d==1 else (price-lo[z])/risk
    peak=max(peak,fav)
    # Protection only starts NEXT bar after favorable range has CLOSED.
    if manage==1 and peak>=1.0:proposed=price
    elif manage==2 and peak>=1.5:proposed=price
    elif manage==3 and peak>=1.0:proposed=price+d*np.floor(max(0,peak-0.5)/0.5)*.5*risk
    else:proposed=curr
    if d==1:curr=max(curr,proposed)
    else:curr=min(curr,proposed)
   if z==len(op)-1 and reason==9:end=z;xp=cl[z];reason=3
   gross=d*(xp-price)/risk;net=gross-fee/risk
   out[num]=np.array([e,fill_idx,end,d,price,sl,target,risk,net,gross,reason]);num+=1;locked=end
  return out[:num]
# score with period masks and no look-ahead selection, done after sim; lock across periods stays global.
arr=cand
num_sig=len(arr)
filter_defs={
 'any':np.ones(num_sig,dtype=bool),
 'H1':arr.H1_aligned.to_numpy(bool),
 'M15':arr.M15_aligned.to_numpy(bool),
 'H1_M15':(arr.H1_aligned&arr.M15_aligned).to_numpy(bool),
 'H1_M15_H4':(arr.H1_aligned&arr.M15_aligned&arr.H4_aligned).to_numpy(bool),
 'H1_WEEKLY':(arr.H1_aligned&arr.weekly_discount_premium).to_numpy(bool),
}
session_defs={'all':(6,20),'morning':(6,11),'midday':(11,15),'ny_open':(15,18),'late':(17,20)}
# Shortlist ~ 13 groups * 5 confirmation * 6 filters * 5 time sessions *4 stops*2 RR*2 orders*3 management huge.
# Phase 1 initial screen fixed Market, fixed 3R, STRUCT/ATR5/ATR15, mgmt fixed; no alternate management yet.
records=[];timer=perf_counter();rawc=arr
idx_by_group=arr.groupby(['family','trigger']).indices
chosen=[]
for (fam,trig),gidx in idx_by_group.items():
 gidx=np.asarray(gidx,np.int64)
 for filtr,fmask in filter_defs.items():
  sub=gidx[fmask[gidx]]
  for sname,(start,end) in session_defs.items():
   jj=sub[(arr.hour_il.to_numpy()[sub]>=start)&(arr.hour_il.to_numpy()[sub]<end)]
   if len(jj)<30:continue
   for sk,skname in ((0,'STRUCT'),(1,'M5_ATR1'),(2,'M15_ATR1')):
    for rr in (2.,3.):
     out=backtest(ce[jj],cf[jj],arr.side.to_numpy('int8')[jj],arr.stop_struct.to_numpy(float)[jj],arr.atr5.to_numpy(float)[jj],arr.atr15.to_numpy(float)[jj],o,h,l,c,t,hours,weekdays,sk,rr,0,0,.35)
     if len(out)==0:continue
     locdates=dates[out[:,1].astype(int)];tr=(locdates<'2026-01-01');test=(locdates>='2026-01-01')
     # Training data is 2025; 2026 is REUSED research window, not untouched holdout.
     a=out[tr,8];b=out[test,8]
     if len(a)<20:continue
     records.append(dict(family=fam,trigger=trig,filter=filtr,session=sname,stop=skname,TP_R=rr,train_n=len(a),train_avg_R=float(a.mean()),train_WR=float((a>0).mean()*100),review_n=len(b),review_avg_R=float(b.mean()) if len(b) else np.nan,review_WR=float((b>0).mean()*100) if len(b) else np.nan))
print('phase1 screening',len(records),'elapsed',round(perf_counter()-timer,2),flush=True)
res=pd.DataFrame(records)
res.to_csv(P/'phase1_all_strategies.csv',index=False)
# Rank train only with conservative optimism penalty, sample requirement >=100 and no subsequent phase bias.
res['rank_score']=res.train_avg_R-1.2/np.sqrt(res.train_n)
# avoid duplicated 20,000 variants by requiring reasonable frequency, predeclare selection from train only.
sel=res[(res.train_n>=100)].sort_values('rank_score',ascending=False).head(18)
sel.to_csv(P/'train_selected_18.csv',index=False)
# Phase 2: ONLY selected 18 combinations, add limit vs market and trailing vs fixed. Selection again using train.
second=[];logs=[]
for _,row in sel.iterrows():
 gm=np.asarray(idx_by_group[(row.family,row.trigger)],dtype=int)
 v=filter_defs[row['filter']];s,e=session_defs[row.session]
 jj=gm[v[gm] & (arr.hour_il.to_numpy()[gm]>=s)&(arr.hour_il.to_numpy()[gm]<e)]
 sk={'STRUCT':0,'M5_ATR1':1,'M15_ATR1':2}[row.stop]
 for order in (0,1):
  for manager in (0,1,2,3):
   data=backtest(ce[jj],cf[jj],arr.side.to_numpy('int8')[jj],arr.stop_struct.to_numpy(float)[jj],arr.atr5.to_numpy(float)[jj],arr.atr15.to_numpy(float)[jj],o,h,l,c,t,hours,weekdays,sk,float(row.TP_R),manager,order,.35)
   if len(data)==0:continue
   di=data[:,1].astype(int);dt=dates[di];isdev=dt<'2026-01-01';isq1=(dt>='2026-01-01')&(dt<'2026-04-01');isrev=dt>='2026-04-01'
   nm=lambda x:float(data[x,8].mean()) if np.any(x) else None
   record=dict(family=row.family,trigger=row.trigger,filter=row['filter'],session=row.session,stop=row.stop,TP_R=row.TP_R,order='NEXT_OPEN' if order==0 else 'LIMIT_BODY_MID_5M',management=['FIXED','BE_AT_1R','BE_AT_1P5R','TRAIL_EVERY_HALF_R'][manager],train_n=int(isdev.sum()),train_avg_R=nm(isdev),review_q1_n=int(isq1.sum()),review_q1_avg_R=nm(isq1),review_q2q3_n=int(isrev.sum()),review_q2q3_avg_R=nm(isrev),overall_n=len(data),overall_avg_R=nm(np.ones(len(data),bool)))
   second.append(record)
   logs.append((record,data))
phase2=pd.DataFrame(second)
phase2.to_csv(P/'phase2_selected_144_variants.csv',index=False)
# Train-only selection among 144 choices; minimize false certainty. No 2026 metrics used to choose.
winning=phase2[(phase2.train_n>=90)].assign(score=lambda d:d.train_avg_R-1.5/np.sqrt(d.train_n)).sort_values('score',ascending=False)
winning.head(12).to_csv(P/'train_only_top12.csv',index=False)
if len(winning):
 w=winning.iloc[0]
 for rec,dat in logs:
  if all(rec[k]==w[k] for k in ['family','trigger','filter','session','stop','TP_R','order','management']):
   detail=pd.DataFrame(dat,columns=['signal_next_open_m1','fill_m1','exit_m1','side','entry_price','SL_price','TP_price','risk_price','net_R','gross_R','exit_reason'])
   detail['entry_local']=lcl[detail.fill_m1.astype(int)].astype(str);detail['exit_utc']=idx[detail.exit_m1.astype(int)].astype(str);detail['period']=np.where(dates[detail.fill_m1.astype(int)]<'2026-01-01','TRAIN_2025',np.where(dates[detail.fill_m1.astype(int)]<'2026-04-01','REUSED_2026Q1','REUSED_2026Q2Q3'))
   detail['net_R_fee070']=detail.gross_R-0.70/detail.risk_price
   detail.to_csv(P/'train_chosen_trade_log.csv',index=False)
   break
stats=dict(candles_m1=n,zone_anchor_signals=len(sig),m1_confirmed_candidates=len(cand),phase1_variants=len(res),phase2_variants=len(phase2),review_2026_is_reused=True,train_selection_train_only=True,ranked_rule_candidates=len(winning),fee_in_xauusd_price_units=0.35,entry_hours='06:00-20:00 Asia/Jerusalem',max_hold_minutes=120)
(P/'summary.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
print('finished',stats,'elapsed',round(perf_counter()-timer,1),flush=True)