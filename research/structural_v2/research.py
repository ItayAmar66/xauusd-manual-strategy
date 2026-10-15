#!/usr/bin/env python3
"""Structural-stop market and limit order strategy experiment on XAUUSD M1.
No retrospective winning-leg labels are used in signal generation.
"""
from pathlib import Path
import pandas as pd, numpy as np
from numba import njit
from time import time
import json
OUT=Path(__file__).resolve().parent
SRC=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if not SRC.exists():
 from zipfile import ZipFile
 with ZipFile(OUT.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip') as z:
  SRCNAME=next(x for x in z.namelist() if x.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  raw=pd.read_csv(z.open(SRCNAME))
else:raw=pd.read_csv(SRC)
idx=pd.to_datetime(raw.timestamp,unit='ms',utc=True)
raw=raw.set_index(idx)[['open','high','low','close']]
t=np.asarray(raw.index.asi8//(60*10**9),dtype=np.int64)
o=raw.open.to_numpy();h=raw.high.to_numpy();l=raw.low.to_numpy();c=raw.close.to_numpy();n=len(raw)
local=raw.index.tz_convert('Asia/Jerusalem');hour=local.hour+local.minute/60
localday=pd.Series(local.date,index=raw.index)
eligible=(hour>=6)&(hour<20)&(local.weekday<5)&np.r_[False,np.diff(t)==1]& (h>l)
base=pd.DataFrame(index=raw.index)
# Initial signal features only access preceding completed candles.
for window in (5,10,15,30,60,120):
 base[f'hi{window}']=pd.Series(h,index=raw.index).shift(1).rolling(window,min_periods=window).max()
 base[f'lo{window}']=pd.Series(l,index=raw.index).shift(1).rolling(window,min_periods=window).min()
# Calendar high/lows: previous COMPLETE local day/week, never today's future daily H/L.
keyweek=pd.Series(local.to_period('W-SUN').astype(str),index=raw.index)
for name,key in [('day',localday),('week',keyweek)]:
 g=raw.groupby(key).agg(hi=('high','max'),lo=('low','min'),count=('close','size'))
 g=g.shift(1)
 base[f'{name}hi']=key.map(g.hi).to_numpy()
 base[f'{name}lo']=key.map(g.lo).to_numpy()
# Asia range is fully known only once Israel clock passes 06:00.
a_mask=(hour>=0)&(hour<6)
a=raw[a_mask].groupby(localday[a_mask]).agg(hi=('high','max'),lo=('low','min'),count=('close','size'))
base['asiahi']=localday.map(a.hi).to_numpy();base['asialo']=localday.map(a.lo).to_numpy()
# Completed higher timeframe values stamped at candle end (no premature HTF bar use).
def complete_tf(freq, minutes):
 g=raw.resample(freq,label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last'})
 cnt=raw.close.resample(freq,label='left',closed='left').count()
 g=g[cnt==minutes].copy()
 g['ema20']=g.close.ewm(span=20,adjust=False).mean()
 g['ema50']=g.close.ewm(span=50,adjust=False).mean()
 g['trend']=np.sign(g.ema20-g.ema50)
 g['momentum']=np.sign(g.close-g.close.shift(3))
 g['rangelow']=g.low.shift(1).rolling(10,min_periods=10).min()
 g['rangehigh']=g.high.shift(1).rolling(10,min_periods=10).max()
 g.index=g.index+pd.Timedelta(minutes=minutes)
 return g[['trend','momentum','rangelow','rangehigh']].reindex(raw.index,method='ffill')
for tf,mi in [('m5',5),('m15',15),('h1',60),('h4',240)]:
 g=complete_tf(f'{mi}min',mi)
 for k in g:base[f'{tf}_{k}']=g[k]
# Trend and premium discount conditions are context; cannot use future pivots.
base['weekly_mid']=(base.weekhi+base.weeklo)/2
base['weekly_q25']=base.weeklo+.25*(base.weekhi-base.weeklo)
base['weekly_q75']=base.weeklo+.75*(base.weekhi-base.weeklo)
# FVG from archived lifecycle: as-of verified after bar close; value must be within an active gap.
# For first run use only last closed M5 or M15 3-candle FVG and check retest on M1, no future invalidation.
from collections import deque
fvgs={}
for tf,period in [('m5',5),('m15',15),('h1',60)]:
 candles=raw.resample(f'{period}min',label='left',closed='left').agg({'high':'max','low':'min','close':'last'})
 counts=raw.close.resample(f'{period}min',label='left',closed='left').count()
 candles=candles[counts==period].copy()
 # Historical gaps appear only at TF candle close. Precompute most recent zone as candidate, but check close invalidation during M1 iteration.
 bull=candles.low>candles.high.shift(2);bear=candles.high<candles.low.shift(2)
 candle_end=(candles.index+pd.Timedelta(minutes=period)).asi8//(60*10**9)
 events=[]
 for kk in np.where(bull.to_numpy())[0]:events.append((int(candle_end[kk]),1,float(candles.high.iloc[kk-2]),float(candles.low.iloc[kk])))
 for kk in np.where(bear.to_numpy())[0]:events.append((int(candle_end[kk]),-1,float(candles.high.iloc[kk]),float(candles.low.iloc[kk-2])))
 events.sort()
 fvgs[tf]=events
# Build causal stateful event candidates via completed M1 candle i (entry no earlier than i+1).
rows=[]
def emit(sig_i,typ,side,stop,ref,context, sweep_idx=-1):
 if sig_i>=n-1 or not eligible[sig_i+1]:return
 en=sig_i+1
 if not np.isfinite(stop) or not np.isfinite(ref):return
 entry=o[en]
 dist=(entry-stop)*side
 # This is a MINIMUM risk viability check, not a fixed SL distance.
 if not (0.65<=dist<=100):return
 rows.append((typ,sig_i,en,side,stop,ref,context,sweep_idx))
# Pattern A: wick sweep + close reclaim. Swing stop at signal wick (initial structural invalidation).
levels={
  'D1':(base.dayhi.to_numpy(),base.daylo.to_numpy()),
  'W1':(base.weekhi.to_numpy(),base.weeklo.to_numpy()),
  'ASIA':(base.asiahi.to_numpy(),base.asialo.to_numpy()),
  '15M':(base.hi15.to_numpy(),base.lo15.to_numpy()),
  '30M':(base.hi30.to_numpy(),base.lo30.to_numpy()),
  '60M':(base.hi60.to_numpy(),base.lo60.to_numpy()),
  '120M':(base.hi120.to_numpy(),base.lo120.to_numpy()),
}
trend_m15=base.m15_trend.to_numpy();trend_h1=base.h1_trend.to_numpy();trend_h4=base.h4_trend.to_numpy()
w_mid=base.weekly_mid.to_numpy();
# Track sweep->BOS without knowing reversal end; each family independent long/short state.
for lab,(levels_hi,levels_lo) in levels.items():
 for i in range(150,n-2):
  if not eligible[i] or not np.isfinite(levels_hi[i]):continue
  up=(l[i]<levels_lo[i]-0.001 and c[i]>levels_lo[i])
  dn=(h[i]>levels_hi[i]+0.001 and c[i]<levels_hi[i])
  if up!=dn:
   side=1 if up else -1
   stop=l[i]-.10 if up else h[i]+.10
   emit(i,lab+'_SWEEP',side,stop,levels_lo[i] if up else levels_hi[i],i, i)
# Pattern B: sequence sweep then BOS (break prior 5-bar micro structure), waiting max 12 M1 bars.
for lab,(levels_hi,levels_lo) in levels.items():
 arms={1:None,-1:None}
 hi5=base.hi5.to_numpy();lo5=base.lo5.to_numpy()
 for i in range(150,n-2):
  if not eligible[i] or not np.isfinite(levels_hi[i]):
   if not eligible[i]:arms={1:None,-1:None}
   continue
  for side in [1,-1]:
   ar=arms[side]
   if ar is None:continue
   si,ext,level,ref=ar
   if i-si>12 or (side==1 and l[i]<ext) or (side==-1 and h[i]>ext):
    arms[side]=None;continue
   # breakout of structure existing at time sweep (ref) and acceptance close
   if (side==1 and c[i]>ref and c[i]>o[i]) or (side==-1 and c[i]<ref and c[i]<o[i]):
    emit(i,lab+'_BOS',side,ext-.10 if side==1 else ext+.10,ref,i,si)
    arms[side]=None
  if l[i]<levels_lo[i] and c[i]>levels_lo[i] and np.isfinite(hi5[i]):
   arms[1]=(i,l[i],levels_lo[i],hi5[i])
  if h[i]>levels_hi[i] and c[i]<levels_hi[i] and np.isfinite(lo5[i]):
   arms[-1]=(i,h[i],levels_hi[i],lo5[i])
# Pattern C: structural breakout acceptance with pre-existing swing high/low and stop at opposite local swing (10 vs 30 M1 bars).
for span in (15,30,60):
 hi=base[f'hi{span}'].to_numpy();lo=base[f'lo{span}'].to_numpy()
 hl10=base.lo10.to_numpy();hh10=base.hi10.to_numpy();
 for i in range(150,n-2):
  if not eligible[i] or not np.isfinite(hi[i]):continue
  up=c[i]>hi[i] and c[i-1]<=hi[i-1] and c[i]>o[i]
  dn=c[i]<lo[i] and c[i-1]>=lo[i-1] and c[i]<o[i]
  if up!=dn:
   side=1 if up else -1
   stop=min(hl10[i],l[i])-.10 if up else max(hh10[i],h[i])+.10
   emit(i,f'BOS{span}_PULLBACK',side,stop,hi[i] if up else lo[i],i)
# Pattern D: M5/M15/H1 FVG touch followed by close back beyond zone boundary; need all prior bar close outside zone.
# Directly use archived M1-close invalidation lifecycle; evaluate only at candidate m1 price reaction.
fvg=pd.read_csv('/mnt/data/XAUUSD_FVG_Lifecycle_CloseInvalidation.csv') if Path('/mnt/data/XAUUSD_FVG_Lifecycle_CloseInvalidation.csv').exists() else None
if fvg is None:
 from zipfile import ZipFile
 with ZipFile(OUT.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip') as z:
  fn=next(n for n in z.namelist() if n.endswith('/XAUUSD_FVG_Lifecycle_CloseInvalidation.csv'))
  fvg=pd.read_csv(z.open(fn))
fvg=fvg[fvg.tf.isin(['M5','M15','H1','H4'])].copy()
fvg['st']=pd.to_datetime(fvg.available_at,utc=True).astype('int64')//(60*10**9)
fvg['ed']=pd.to_datetime(fvg.invalidated_at,utc=True,errors='coerce').astype('int64')//(60*10**9)
fvg.ed=fvg.ed.fillna(2**49)
fvg=fvg.sort_values('st')
# Iterate candidate rejections only on minute bars showing bullish/bearish rejection of prev 5m range;
# use interval index in current direction via deque of FVG ranges (pruned).
valid_idx=np.where(eligible & (c>o) & (l<np.r_[l[0],l[:-1]]) & (c>np.r_[c[0],c[:-1]]))[0]
valid_dn=np.where(eligible & (c<o) & (h>np.r_[h[0],h[:-1]]) & (c<np.r_[c[0],c[:-1]]))[0]
# Filter time active gap, price overlap and reclaim zone boundary, doing asof via group streaming.
for tf in ['M5','M15','H1','H4']:
 for d,bars in [('BULL',valid_idx),('BEAR',valid_dn)]:
  q=fvg[(fvg.tf==tf)&(fvg.direction==d)]
  arr=q[['st','ed','level_low','level_high']].to_numpy(dtype=float)
  arr=arr[np.argsort(arr[:,0])]
  j=0;active=[]
  for i in bars:
   now=t[i]
   while j<len(arr) and arr[j,0]<=now:
    active.append(arr[j]);j+=1
   if len(active)>300:active=[x for x in active if x[1]>now]
   # check most recent relevant active zones only, for each TF and side.
   for st,ed,bottom,top in reversed(active[-70:]):
    if not (st<=now<ed):continue
    if d=='BULL':
     if not (l[i]<=top and l[i]>=bottom-.05 and c[i]>top and c[i-1]>top):continue
     stop=min(l[i],bottom)-.10
     emit(i,'FVG_'+tf,1,stop,top,i);break
    else:
     if not (h[i]>=bottom and h[i]<=top+.05 and c[i]<bottom and c[i-1]<bottom):continue
     stop=max(h[i],top)+.10
     emit(i,'FVG_'+tf,-1,stop,bottom,i);break
print('raw eligible structural signals',len(rows),flush=True)
sig=pd.DataFrame(rows,columns=['family','signal_m1','entry_m1','side','stop','reference','context_index','sweep_index'])
if sig.empty:raise Exception('No signals')
sig['entry_ts_utc']=raw.index[sig.entry_m1.to_numpy()].astype(str)
sig['entry_local']=local[sig.entry_m1.to_numpy()].astype(str)
sig['risk_market_price']=np.abs(o[sig.entry_m1.to_numpy()]-sig.stop)
sig['H1_aligned']=sig.side.to_numpy()==trend_h1[sig.signal_m1.to_numpy()]
sig['H1_opposed']=sig.side.to_numpy()==-trend_h1[sig.signal_m1.to_numpy()]
sig['M15_aligned']=sig.side.to_numpy()==trend_m15[sig.signal_m1.to_numpy()]
sig['M15_opposed']=sig.side.to_numpy()==-trend_m15[sig.signal_m1.to_numpy()]
sig['H4_aligned']=sig.side.to_numpy()==trend_h4[sig.signal_m1.to_numpy()]
sig['weekly_discount_premium']=np.where(sig.side.eq(1),o[sig.entry_m1.to_numpy()]<=w_mid[sig.signal_m1.to_numpy()],o[sig.entry_m1.to_numpy()]>=w_mid[sig.signal_m1.to_numpy()])
sig['hour_il']=hour[sig.entry_m1.to_numpy()]
# dedupe to single family+minute+direction to avoid artificial repeated signals.
sig=sig.drop_duplicates(['family','entry_m1','side']).sort_values(['entry_m1','family']).reset_index(drop=True)
sig.to_csv(OUT/'signal_inventory.csv',index=False)
print('signals',len(sig),'families',sig.family.nunique(),flush=True)
# For structure retests: limit entry at fraction of signal candle body or originally breached level; stop always stays fixed at structural invalidation.
@njit
def run(entries,sides,stops,refs,signal_indices,open_,high_,low_,close_,tm,can_fill,mode,rr,mgmt,ttl,fee):
 out=np.empty((len(entries),13),dtype=np.float64);count=0;last_exit=-1
 for a in range(len(entries)):
  j=int(entries[a]);d=int(sides[a]);stop=stops[a];ref=refs[a];sig_idx=int(signal_indices[a]);
  if j<=last_exit:continue
  if mode==0:fillidx=j;fillprice=open_[j]
  else:
   # limit offset as a fraction of the previous signal candle, or structure reference
   if mode==1:targetentry=(open_[sig_idx]+close_[sig_idx])/2
   elif mode==2:targetentry=ref
   else:targetentry=(2*open_[sig_idx]+close_[sig_idx])/3
   if d==1 and targetentry>=open_[j]: targetentry=open_[j]
   if d==-1 and targetentry<=open_[j]:targetentry=open_[j]
   fillidx=-1;fillprice=0
   for k in range(j,min(j+ttl+1,len(open_))):
    if tm[k]-tm[j]>ttl or (k>j and tm[k]-tm[k-1]>1) or not can_fill[k]:break
    if (d==1 and low_[k]<=targetentry) or (d==-1 and high_[k]>=targetentry):
     fillidx=k;fillprice=min(open_[k],targetentry) if d==1 else max(open_[k],targetentry);break
   if fillidx<0:continue
  risk=(fillprice-stop)*d
  if risk<.65 or risk>150:continue
  target=fillprice+d*rr*risk;curstop=stop;xp=fillprice;end=fillidx;reason=9;maxf=0.;worst=0.
  for k in range(fillidx,len(open_)):
   if tm[k]-tm[fillidx]>=120:
    xp=open_[k];end=k;reason=0;break
   if k>fillidx and tm[k]-tm[k-1]>1:
    xp=open_[k];end=k;reason=2;break
   if d==1:
    if open_[k]<=curstop:xp=open_[k];end=k;reason=-1;break
    if open_[k]>=target:xp=target;end=k;reason=1;break
    hitstop=low_[k]<=curstop;hittarget=high_[k]>=target
   else:
    if open_[k]>=curstop:xp=open_[k];end=k;reason=-1;break
    if open_[k]<=target:xp=target;end=k;reason=1;break
    hitstop=high_[k]>=curstop;hittarget=low_[k]<=target
   # intra-M1 low/high order unavailable; prefer stop on both. Includes entry bar.
   if hitstop:xp=curstop;end=k;reason=-1;break
   if hittarget:xp=target;end=k;reason=1;break
   adverse=((fillprice-low_[k]) if d==1 else (high_[k]-fillprice))/risk
   if adverse>worst:worst=adverse
   favorable=(high_[k]-fillprice) if d==1 else (fillprice-low_[k]);maxf=max(maxf,favorable/risk)
   # management after candle close, only affects next bar.
   if mgmt==1 and maxf>=1.5:can=fillprice
   elif mgmt==2 and maxf>=2:can=fillprice
   elif mgmt==3 and maxf>=1:can=fillprice+d*max(0,np.floor(maxf-.00001)-1)*risk
   elif mgmt==4 and maxf>=1: # trail behind last 5 completed candles using a true structural low/high
    low5=low_[max(fillidx,k-4):k+1].min();high5=high_[max(fillidx,k-4):k+1].max()
    can=low5-.10 if d==1 else high5+.10
   elif mgmt==5 and maxf>=2:
    low10=low_[max(fillidx,k-9):k+1].min();high10=high_[max(fillidx,k-9):k+1].max()
    can=low10-.10 if d==1 else high10+.10
   else:can=curstop
   if d==1 and can>curstop:curstop=can
   elif d==-1 and can<curstop:curstop=can
  out[count,:]=np.array([j,fillidx,end,d,fillprice,stop,xp,risk,((xp-fillprice)*d-fee)/risk,(xp-fillprice)*d/risk,tm[end]-tm[fillidx],reason,worst]);count+=1;last_exit=end
 return out[:count]
# Split strictly chronological. Reused review 2026 Q2+ was inspected in earlier project attempts.
dateidx=np.array(local.date,dtype='str')
periods=[('2025_H1','2025-01-01','2025-07-01'),('2025_H2','2025-07-01','2026-01-01'),('2026_Q1','2026-01-01','2026-04-01'),('2026_Q2Q3_REUSED','2026-04-01','2026-09-26')]
filters={'none':np.ones(len(sig),dtype=bool),'h1_aligned':sig.H1_aligned.to_numpy(),'h1_opposed':sig.H1_opposed.to_numpy(),'m15_aligned':sig.M15_aligned.to_numpy(),'m15_opposed':sig.M15_opposed.to_numpy(),'h1_m15_aligned':(sig.H1_aligned&sig.M15_aligned).to_numpy(),'h4_aligned':sig.H4_aligned.to_numpy(),'weekly_value':sig.weekly_discount_premium.to_numpy(),'h1_weekly':(sig.H1_aligned&sig.weekly_discount_premium).to_numpy()}
win={'all':(6,20),'london_08_13':(8,13),'ny_14_19':(14,19),'ny_15_18':(15,18)}
rows=[];report=[];now=time()
# Evaluate every family with fixed structural invalidation, 4 entry modes, 3 RR, 3 management = ~thousands.
for family,ids in sig.groupby('family').indices.items():
 ids=np.asarray(ids,dtype=np.int64)
 for filt,ok in filters.items():
  for sess,(start,end) in win.items():
   ss=ids[ok[ids] & (sig.hour_il.to_numpy()[ids]>=start)&(sig.hour_il.to_numpy()[ids]<end)]
   if len(ss)<15:continue
   arr=sig.iloc[ss]
   en=arr.entry_m1.to_numpy(np.int64);directions=arr.side.to_numpy(np.int8)
   stops=arr.stop.to_numpy(np.float64);refs=arr.reference.to_numpy(np.float64);si=arr.signal_m1.to_numpy(np.int64)
   # min fill backtest mode market 0 and three limit models 1..3; 3 RR and 4 management
   for mode in (0,1,2,3):
    for rr in (3,5,8):
     for mgmt in (0,1,3,4):
      out=run(en,directions,stops,refs,si,o,h,l,c,t,eligible,mode,rr,mgmt,15,.35)
      if len(out)==0:continue
      dates=dateidx[out[:,1].astype(np.int64)]
      scores={}
      for label,begin,finish in periods:
       sel=(dates>=begin)&(dates<finish);v=out[sel,8]
       scores[label+'_n']=len(v);scores[label+'_meanR']=float(v.mean()) if len(v) else np.nan
       scores[label+'_totalR']=float(v.sum()) if len(v) else 0.
       scores[label+'_days']=int(len(np.unique(dates[sel])))
      rows.append(dict(family=family,filter=filt,session=sess,entry_mode=mode,target_R=rr,management=mgmt,raw_signals=len(ss),filled_n=len(out),max_hold=int(out[:,10].max()),max_gap=int(np.sum(out[:,11]==2)),**scores))
 print('done',family,'elapsed',int(time()-now),'s',flush=True)
results=pd.DataFrame(rows)
results.to_csv(OUT/'all_structural_variants.csv',index=False)
# Pessimism about optimization: use 2025 H1 train, 2025 H2 validation, 2026 as CHECK only; min 50 H1 and H2 trades, avoid OOS cherry-picking.
results['score_H1'] = np.where(results['2025_H1_n']>=50, results['2025_H1_meanR'] - .1*np.sqrt(100/results['2025_H1_n'].clip(lower=1)), -999)
results['eligible_both_2025']=(results['2025_H1_n']>=50)&(results['2025_H2_n']>=50)
selection=results[results.eligible_both_2025].sort_values(['family','score_H1'],ascending=[True,False]).groupby('family',as_index=False).head(1).copy()
selection.to_csv(OUT/'train_selected_family.csv',index=False)
# Also rank on combined 2025, explicitly exploratory because 2025H2 consulted.
rank=results[results.eligible_both_2025].copy()
rank['dev_2025_R']=(rank['2025_H1_totalR']+rank['2025_H2_totalR'])/(rank['2025_H1_n']+rank['2025_H2_n'])
rank=rank.sort_values('dev_2025_R',ascending=False)
rank.head(100).to_csv(OUT/'top100_exploratory_2025.csv',index=False)
# Five example final detailed ledgers selected by H1 for each family; yield verified execution statistics
trade_rows=[]
for z in selection.itertuples(index=False):
 arr=sig[(sig.family==z.family)&filters[z.filter]&(sig.hour_il>=win[z.session][0])&(sig.hour_il<win[z.session][1])]
 if len(arr)<1:continue
 out=run(arr.entry_m1.to_numpy(np.int64),arr.side.to_numpy(np.int8),arr.stop.to_numpy(float),arr.reference.to_numpy(float),arr.signal_m1.to_numpy(np.int64),o,h,l,c,t,eligible,z.entry_mode,z.target_R,z.management,15,.35)
 for row in out:
  j,fi,ex=[int(v) for v in row[:3]]
  trade_rows.append(dict(family=z.family,filter=z.filter,session=z.session,mode=z.entry_mode,manager=z.management,target_R=z.target_R,signal_utc=str(idx[j-1]),entry_utc=str(idx[fi]),entry_local=str(local[fi]),exit_utc=str(idx[ex]),date_israel=dateidx[fi],direction='LONG' if row[3]==1 else 'SHORT',entry_price=row[4],initial_stop=row[5],exit_price=row[6],initial_risk=row[7],net_R=row[8],gross_R=row[9],duration_min=row[10],exit_reason=row[11],adverse_R=row[12]))
ledger=pd.DataFrame(trade_rows).sort_values(['entry_utc','family'])
ledger.to_csv(OUT/'train_selected_trade_log.csv',index=False)
# For date coverage, eligible weekdays with ≥200 M1 bars and real intraday range
market=raw.groupby(localday).agg(bars=('close','size'),hi=('high','max'),lo=('low','min'))
market=market[(market.bars>=200)&(market.hi>market.lo)&(pd.to_datetime(market.index).dayofweek<5)]
D=np.array(market.index,dtype='str')
for label,begin,finish in periods:
 elig=D[(D>=begin)&(D<finish)]
 sub=ledger[(ledger.date_israel>=begin)&(ledger.date_israel<finish)]
 report.append({'period':label,'market_days':len(elig),'selected_family_trades':len(sub),'selected_family_unique_days':sub.date_israel.nunique(),'selected_family_union_coverage_pct':100*sub.date_israel.nunique()/max(1,len(elig))})
(OUT/'summary.json').write_text(json.dumps(dict(source_m1=n,signal_count=len(sig),family_count=int(sig.family.nunique()),tested_variants=len(results),eligible_selected_families=len(selection),base_cost=0.35,management='structural initial stops: origin wick/last swing/FVG boundary; no fixed ATR stop',period_coverage=report,runtime_sec=round(time()-now,2),caveats=['retrospective 15M and 5M winning legs are excluded from signals','this dataset used repeatedly in prior studies; no untouched 2026 holdout','bid-only data with assumed friction, execution uncertain','same-minute high/low order unknown, stop-first fill','no full trading session quote/spread history']),indent=2),encoding='utf8')
print('SUMMARY',json.dumps(json.loads((OUT/'summary.json').read_text()),indent=2),flush=True)