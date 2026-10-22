#!/usr/bin/env python3
"""Exploratory ten-playbook 2-day gating test for XAUUSD M1.

All candidate rules: signal on completed bar t, entry at t+1 next contiguous M1 open.
Decision at market day's beginning uses outcomes from last TWO completed market days.

WARNING: rulebook proxies for 10 concept playbooks, not fully faithful reproductions.
Original Baseline uses separate prior completed trade-signal archive; its causal derivation
must be audited before live deployment. The historical 2026 review set has been reused.
"""
import numpy as np, pandas as pd, json
from pathlib import Path
from numba import njit
P=Path(__file__).resolve().parent
DATAP=Path('/mnt/data/full_rerun/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if not DATAP.exists():
 from zipfile import ZipFile
 z=P.parent.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
 with ZipFile(z) as f: DAT=pd.read_csv(f.open(next(k for k in f.namelist() if k.endswith('xauusd-m1-bid-2025-01-01-2026-09-25.csv'))))
else: DAT=pd.read_csv(DATAP)
tm=pd.to_datetime(DAT.timestamp,unit='ms',utc=True); m=DAT.set_index(tm)[['open','high','low','close']].astype('float64')
N=len(m)
o=m.open.to_numpy();h=m.high.to_numpy();l=m.low.to_numpy();c=m.close.to_numpy(); ts=(m.index.asi8//60_000_000_000).astype('int64')
local=m.index.tz_convert('Asia/Jerusalem'); ds=np.array(local.date,dtype='str');weekday=local.dayofweek;hr=local.hour+local.minute/60
is_valid=(np.r_[False,np.diff(ts)==1]) & (hr>=6)&(hr<20)&(weekday<5)
# Ensure all signals are on completed, contiguous candles and execute the NEXT minute.
entry_valid=np.roll(is_valid,-1);entry_valid[-1]=False
entry_valid &= np.r_[np.diff(ts)==1,False]

# Wilder M1 ATR & M1 candle/body filters: all known at bar end
tr=pd.concat([(m.high-m.low),(m.high-m.close.shift()).abs(),(m.low-m.close.shift()).abs()],axis=1).max(axis=1)
atr1=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean().to_numpy()
body=pd.Series(abs(c-o),index=m.index); medbody=body.shift(1).rolling(20,min_periods=20).median().to_numpy();bigbody=abs(c-o)>1.5*medbody
prior3hi=m.high.shift(1).rolling(3).max().to_numpy();prior3lo=m.low.shift(1).rolling(3).min().to_numpy()
prior5hi=m.high.shift(1).rolling(5).max().to_numpy();prior5lo=m.low.shift(1).rolling(5).min().to_numpy()
prior10hi=m.high.shift(1).rolling(10).max().to_numpy();prior10lo=m.low.shift(1).rolling(10).min().to_numpy()
prior30hi=m.high.shift(1).rolling(30).max().to_numpy();prior30lo=m.low.shift(1).rolling(30).min().to_numpy()
# True M1 gaps, known only on close of third candle; use ffill for latest gap (not an active-gap lifecycle).
bfvg=l>np.r_[np.full(2,np.nan),h[:-2]]
sfvg=h<np.r_[np.full(2,np.nan),l[:-2]]
bfbot=pd.Series(np.where(bfvg,np.r_[np.full(2,np.nan),h[:-2]],np.nan),index=m.index).ffill().to_numpy()
bftop=pd.Series(np.where(bfvg,l,np.nan),index=m.index).ffill().to_numpy()
sfbot=pd.Series(np.where(sfvg,h,np.nan),index=m.index).ffill().to_numpy()
sftop=pd.Series(np.where(sfvg,np.r_[np.full(2,np.nan),l[:-2]],np.nan),index=m.index).ffill().to_numpy()

# Resampling: only last COMPLETED H1/M15/M5 candle is used in M1 rows.
def tf(step):
 f=m.resample(step).agg({'open':'first','high':'max','low':'min','close':'last'})
 f['n']=m.close.resample(step).count()
 minutes=int(pd.Timedelta(step)/pd.Timedelta(minutes=1))
 f=f.where(f.n==minutes)
 ema20=f.close.ewm(span=20,adjust=False).mean();ema50=f.close.ewm(span=50,adjust=False).mean()
 # f row at START of timebox; at next box open prior f is known.
 up=((ema20>ema50)&f.close.notna()).shift(1).fillna(False).reindex(m.index,method='ffill').to_numpy(dtype=bool)
 dn=((ema20<ema50)&f.close.notna()).shift(1).fillna(False).reindex(m.index,method='ffill').to_numpy(dtype=bool)
 # completed FVG 3-candle on that timeframe; static last-seen gap bounds
 bull=f.low>f.high.shift(2); bear=f.high<f.low.shift(2)
 lowb=pd.Series(np.where(bull,f.high.shift(2),np.nan),index=f.index).ffill().shift(1).reindex(m.index,method='ffill').to_numpy()
 highb=pd.Series(np.where(bull,f.low,np.nan),index=f.index).ffill().shift(1).reindex(m.index,method='ffill').to_numpy()
 lows=pd.Series(np.where(bear,f.high,np.nan),index=f.index).ffill().shift(1).reindex(m.index,method='ffill').to_numpy()
 highs=pd.Series(np.where(bear,f.low.shift(2),np.nan),index=f.index).ffill().shift(1).reindex(m.index,method='ffill').to_numpy()
 # last completed bar OHLC also
 last=f[['high','low','close']].shift(1).reindex(m.index,method='ffill')
 return dict(up=up,dn=dn,bull_lo=lowb,bull_hi=highb,bear_lo=lows,bear_hi=highs,hi=last.high.to_numpy(),lo=last.low.to_numpy(),close=last.close.to_numpy())
f5=tf('5min');f15=tf('15min');f60=tf('60min');f240=tf('240min')
# daylight-aware Israel day; previous completed Israeli day's levels
agg=m.groupby(ds).agg(high=('high','max'),low=('low','min'),n=('close','size'))
pdh=pd.Series(ds,index=m.index).map(agg.high.shift()).to_numpy();pdl=pd.Series(ds,index=m.index).map(agg.low.shift()).to_numpy()
# completed 00-05:59 range, only allow after 06:00
asiah=m[(hr<6)].groupby(np.array(ds)[hr<6]).high.max(); asial=m[(hr<6)].groupby(np.array(ds)[hr<6]).low.min()
ah=pd.Series(ds,index=m.index).map(asiah).to_numpy(); al=pd.Series(ds,index=m.index).map(asial).to_numpy()

# prior swing pairs: 2-right closed pivots become observable only two bars later
swlo=((m.low.shift(2)<m.low.shift(3))&(m.low.shift(2)<m.low.shift(4))&(m.low.shift(2)<=m.low.shift(1))&(m.low.shift(2)<=m.low)).to_numpy(dtype=bool)
swhi=((m.high.shift(2)>m.high.shift(3))&(m.high.shift(2)>m.high.shift(4))&(m.high.shift(2)>=m.high.shift(1))&(m.high.shift(2)>=m.high)).to_numpy(dtype=bool)
last_pivot_hi=pd.Series(np.where(swhi,m.high.shift(2),np.nan),index=m.index).ffill().shift(1).to_numpy()
last_pivot_lo=pd.Series(np.where(swlo,m.low.shift(2),np.nan),index=m.index).ffill().shift(1).to_numpy()

# signals collected as list of arrays; stop = structural location, risk from that to actual entry.
E={}
def add(name,bu,bd,stopL,stopS,notes):
 bu=np.asarray(bu,dtype=bool);bd=np.asarray(bd,dtype=bool)
 side=np.where(bu&~bd,1,np.where(bd&~bu,-1,0))
 # stop specific to direction; all features from closed signal bar
 sl=np.where(side==1,stopL,stopS)
 ix=np.flatnonzero((side!=0)&entry_valid&np.isfinite(sl))
 ix=ix[np.where(((o[ix+1]-sl[ix])*side[ix])>0.30)[0]]
 E[name]=pd.DataFrame({'strategy':name,'signal_idx':ix,'entry_idx':ix+1,'side':side[ix].astype('int8'),'stop':sl[ix]})
 print(name, len(E[name]),flush=True)

buffer=0.10
# 01: archive of original completed trade signals. This is distinct from causal per-bar generation.
if Path('/mnt/data/XAUUSD_CLEAN_BASELINE_TRADES.csv').exists():
 orig=pd.read_csv('/mnt/data/XAUUSD_CLEAN_BASELINE_TRADES.csv')
else:
 from zipfile import ZipFile
 with ZipFile(P.parent.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip') as z:
  member=next(n for n in z.namelist() if n.endswith('/XAUUSD_CLEAN_BASELINE_TRADES.csv'))
  orig=pd.read_csv(z.open(member))
if len(orig):
 ix=orig.entry_idx.to_numpy(int)
 ix=ix[(ix>=1)&(ix<N)]
 # preserve original archive stop/side by row and deduplicate signals per entry
 tmp=orig[(orig.entry_idx>=1)&(orig.entry_idx<N)].copy();tmp['side']=np.where(tmp.direction=='LONG',1,-1)
 tmp=tmp.sort_values('entry_idx').drop_duplicates(['entry_idx','side']);ix=tmp.entry_idx.to_numpy(int)
 good=is_valid[ix]&np.isfinite(tmp.stop.to_numpy())&(((o[ix]-tmp.stop.to_numpy())*tmp.side.to_numpy())>0.30)
 tmp=tmp.loc[good];ix=tmp.entry_idx.to_numpy(int)
 E['01_original_CHoCH_breaker_FVG_ARCHIVE']=pd.DataFrame({'strategy':'01_original_CHoCH_breaker_FVG_ARCHIVE','signal_idx':ix-1,'entry_idx':ix,'side':tmp.side.to_numpy(dtype='int8'),'stop':tmp.stop.to_numpy()})
 print('01_original_CHoCH_breaker_FVG_ARCHIVE',len(E['01_original_CHoCH_breaker_FVG_ARCHIVE']),flush=True)
else: E['01_original_CHoCH_breaker_FVG_ARCHIVE']=pd.DataFrame(columns=['strategy','signal_idx','entry_idx','side','stop'])

# 02 AMD+iFVG: past 30m box manipulation sweep and 3m reversal + recently inverted opposite gap.
# inverted gap check: price closes beyond previous opposite gap outer boundary AFTER liquidity raid.
# sweep within prior 8 m, inversion within prior 4; iFVG source must be prior candle.
sweepdn=(l<prior30lo)&(c>prior30lo);sweepup=(h>prior30hi)&(c<prior30hi)
for_l=pd.Series(np.where(sweepdn,l,np.nan),index=m.index).ffill(limit=8).to_numpy()
for_s=pd.Series(np.where(sweepup,h,np.nan),index=m.index).ffill(limit=8).to_numpy()
recent_sweepdn=pd.Series(sweepdn,index=m.index).shift(1).rolling(9).max().fillna(0).to_numpy()>0
recent_sweepup=pd.Series(sweepup,index=m.index).shift(1).rolling(9).max().fillna(0).to_numpy()>0
invbull=(c>np.r_[np.nan,sftop[:-1]])&(np.r_[np.nan,c[:-1]]<=np.r_[np.nan,sftop[:-1]])
invbear=(c<np.r_[np.nan,bfbot[:-1]])&(np.r_[np.nan,c[:-1]]>=np.r_[np.nan,bfbot[:-1]])
add('02_AMD_iFVG_proxy',recent_sweepdn&invbull&bigbody,recent_sweepup&invbear&bigbody,for_l-buffer,for_s+buffer,'recent manipulation, inverted earlier opposite M1 FVG')
# 03 ICT 2022: prior day sweep + micro MSS on completed candles + fresh FVG after sweep; confirm on third bar.
priorraidL=pd.Series((l<pdl)&(c>pdl),index=m.index).shift(1).rolling(12).max().fillna(0).to_numpy()>0
priorraidS=pd.Series((h>pdh)&(c<pdh),index=m.index).shift(1).rolling(12).max().fillna(0).to_numpy()>0
add('03_PDH_PDL_raid_MSS_FVG',priorraidL&(c>last_pivot_hi)&bigbody&bfvg,priorraidS&(c<last_pivot_lo)&bigbody&sfvg,prior10lo-buffer,prior10hi+buffer,'raid + confirmed-pivot break with displacement plus fresh gap')
# 04 Unicorn proxy: recent thirty-bar sweep, MSS and FVG, FVG overlaps reversed candle range / breaker candle
prevdown=(np.r_[False,c[:-1]<o[:-1]]);prevup=(np.r_[False,c[:-1]>o[:-1]])
overlapL=(np.maximum(bfbot,np.r_[np.nan,l[:-1]])<np.minimum(bftop,np.r_[np.nan,h[:-1]]))
overlapS=(np.maximum(sfbot,np.r_[np.nan,l[:-1]])<np.minimum(sftop,np.r_[np.nan,h[:-1]]))
add('04_Unicorn_overlap_proxy',recent_sweepdn&bfvg&(c>prior3hi)&prevdown&overlapL,recent_sweepup&sfvg&(c<prior3lo)&prevup&overlapS,prior5lo-buffer,prior5hi+buffer,'proxy overlap reversal candle with gap; not audited breaker lifecycle')
# 05 H1 FVG touch + M1 rejection and micro 3-bar break
h1touchL=(l<=f60['bull_hi'])&(h>=f60['bull_lo'])&(c>f60['bull_hi'])&(c>o)
h1touchS=(h>=f60['bear_lo'])&(l<=f60['bear_hi'])&(c<f60['bear_lo'])&(c<o)
# completed touch on preceding 1-3 candles, must cross micro high now
h1lb=pd.Series(h1touchL,index=m.index).shift(1).rolling(4).max().fillna(0).to_numpy()>0
h1sb=pd.Series(h1touchS,index=m.index).shift(1).rolling(4).max().fillna(0).to_numpy()>0
add('05_H1_FVG_rejection',h1lb&(c>prior3hi)&(c>o),h1sb&(c<prior3lo)&(c<o),prior5lo-buffer,prior5hi+buffer,'completed H1 gap with M1 touch then break')
# 06 OTE 61.8-78.6 of known prior H1 candle impulse proxy; only closed H1 data
impHigh=f60['hi'];impLow=f60['lo'];impRange=impHigh-impLow
fibLlo=impHigh-0.786*impRange;fibLhi=impHigh-0.618*impRange
fibSlo=impLow+0.618*impRange;fibShi=impLow+0.786*impRange
zoneL=(l<=fibLhi)&(h>=fibLlo)&f60['up'];zoneS=(h>=fibSlo)&(l<=fibShi)&f60['dn']
add('06_OTE_H1_bar_retrace_proxy',zoneL&(c>prior3hi)&(c>o),zoneS&(c<prior3lo)&(c<o),prior10lo-buffer,prior10hi+buffer,'OTE from completed H1 candle, NOT pivot-defined M5 leg')
# 07 frozen Asia box reclaim
asiaraidL=(l<al)&(c>al)&(hr>=6)&(hr<12);asiaraidS=(h>ah)&(c<ah)&(hr>=6)&(hr<12)
prev_asia_L=np.r_[False,asiaraidL[:-1]];prev_asia_S=np.r_[False,asiaraidS[:-1]]
add('07_Asia_raid_reclaim',prev_asia_L&(c>np.r_[np.nan,h[:-1]])&(c>o),prev_asia_S&(c<np.r_[np.nan,l[:-1]])&(c<o),np.minimum(l,np.r_[np.nan,l[:-1]])-buffer,np.maximum(h,np.r_[np.nan,h[:-1]])+buffer,'frozen Asia level + following candle break')
# 08 trend M1 FVG pullback; historical gap freshness require formation within 1-8 minutes
barsSinceBull=np.full(N,np.inf);barsSinceBear=np.full(N,np.inf);lb=-10**6;sb=-10**6
for i in range(N):
 if bfvg[i]:lb=i
 if sfvg[i]:sb=i
 barsSinceBull[i]=i-lb;barsSinceBear[i]=i-sb
trendL=f60['up']&f5['up'];trendS=f60['dn']&f5['dn']
add('08_Trend_M1_FVG_retest',trendL&(barsSinceBull>=1)&(barsSinceBull<=8)&(l<=bftop)&(c>bftop)&(c>o),trendS&(barsSinceBear>=1)&(barsSinceBear<=8)&(h>=sfbot)&(c<sfbot)&(c<o),prior5lo-buffer,prior5hi+buffer,'fresh gap retest with confirmed HTF trend')
# 09 30 minute compression breakout and retest; freeze breakout boundary on completed breakout candle.
range30=prior30hi-prior30lo; rangemed=pd.Series(range30,index=m.index).shift(1).rolling(360,min_periods=200).median().to_numpy()
brL=(c>prior30hi)&bigbody&(range30<rangemed*.70)
brS=(c<prior30lo)&bigbody&(range30<rangemed*.70)
brHi=np.full(N,np.nan);brLo=np.full(N,np.nan)
hi_src=np.where(brL,prior30hi,np.nan);lo_src=np.where(brS,prior30lo,np.nan)
recentHi=pd.Series(hi_src,index=m.index).ffill(limit=7).shift(1).to_numpy()
recentLo=pd.Series(lo_src,index=m.index).ffill(limit=7).shift(1).to_numpy()
prev_breakL=pd.Series(brL,index=m.index).shift(1).rolling(8).max().fillna(0).to_numpy()>0
prev_breakS=pd.Series(brS,index=m.index).shift(1).rolling(8).max().fillna(0).to_numpy()>0
add('09_Compression_break_retest',prev_breakL&(l<=recentHi)&(c>recentHi)&(c>o),prev_breakS&(h>=recentLo)&(c<recentLo)&(c<o),prior5lo-buffer,prior5hi+buffer,'M1 box breakout and retest')
# 10 BPR overlap: prior bearish gap with newly formed bullish gap, overlap positive, retest next 8 bars.
# capture bounds on moment of gap pair and ffill for <=8 only, rejection at overlap zone
oppBearLo=np.r_[np.nan,sfbot[:-1]];oppBearHi=np.r_[np.nan,sftop[:-1]]
oppBullLo=np.r_[np.nan,bfbot[:-1]];oppBullHi=np.r_[np.nan,bftop[:-1]]
overlapBull=bfvg&(np.maximum(np.r_[np.nan,np.nan,h[:-2]],oppBearLo)<np.minimum(l,oppBearHi))
overlapBear=sfvg&(np.maximum(h,oppBullLo)<np.minimum(np.r_[np.nan,np.nan,l[:-2]],oppBullHi))
bprLlo=pd.Series(np.where(overlapBull,np.maximum(np.r_[np.nan,np.nan,h[:-2]],oppBearLo),np.nan),index=m.index).ffill(limit=7).shift(1).to_numpy()
bprLhi=pd.Series(np.where(overlapBull,np.minimum(l,oppBearHi),np.nan),index=m.index).ffill(limit=7).shift(1).to_numpy()
bprSlo=pd.Series(np.where(overlapBear,np.maximum(h,oppBullLo),np.nan),index=m.index).ffill(limit=7).shift(1).to_numpy()
bprShi=pd.Series(np.where(overlapBear,np.minimum(np.r_[np.nan,np.nan,l[:-2]],oppBullHi),np.nan),index=m.index).ffill(limit=7).shift(1).to_numpy()
add('10_BPR_opposite_FVG_overlap_proxy',(l<=bprLhi)&(c>bprLhi)&(c>o),(h>=bprSlo)&(c<bprSlo)&(c<o),prior5lo-buffer,prior5hi+buffer,'opposing gap overlap and M1 rejection proxy')

# Create and consolidate trade signals. Conservative: one per STRATEGY at a time, trade exits stop-first.
allsig=pd.concat(E.values(),ignore_index=True).sort_values(['strategy','entry_idx','side']).drop_duplicates(['strategy','entry_idx'])
assert allsig.strategy.nunique()==10,(allsig.strategy.unique(),)
# no stop distance adjusted to ATR; reject impossible or overly large stops; skip if costs too large relative to stop
entry_idx=allsig.entry_idx.to_numpy('int64');side=allsig.side.to_numpy('int8');stops=allsig.stop.to_numpy('float64');strat=allsig.strategy.to_numpy();
risks=(o[entry_idx]-stops)*side
# avoid no-stop / tiny stop where approximate 0.35 spread eats whole RR; don't move the SL
keep=np.isfinite(risks)&(risks>=0.70)&(risks<=90.0)&np.isfinite(o[entry_idx]); alls=allsig.loc[keep].copy()
# keep >=0.7 price risk explicitly disclosure as trade viability screen; not moving stop
alls['stop_distance']=risks[keep]; alls['entry_price']=o[alls.entry_idx.to_numpy(int)]

@njit
def run(se,sd,stop,op,high,low,cl,tt):
 n=len(se)
 ex=np.empty(n,np.int64);gross=np.empty(n,np.float64);why=np.empty(n,np.int8)
 lastexit=-1
 for a in range(n):
  j=se[a];di=sd[a];r=(op[j]-stop[a])*di;target=op[j]+di*3*r
  # per-strategy nonoverlap, same-bar stop-first, next-bar break/data-gap exit
  if j<=lastexit:ex[a]=-1;gross[a]=np.nan;why[a]=9;continue
  k=j;price=cl[j];reason=0
  while k<len(op):
   if k>j and tt[k]-tt[k-1]>1:price=cl[k-1];k=k-1;reason=2;break
   if tt[k]-tt[j]>=120:price=op[k];reason=0;break
   if di==1:
    if op[k]<=stop[a]:price=op[k];reason=-1;break
    if op[k]>=target:price=target;reason=1;break
    if low[k]<=stop[a]:price=stop[a];reason=-1;break
    if high[k]>=target:price=target;reason=1;break
   else:
    if op[k]>=stop[a]:price=op[k];reason=-1;break
    if op[k]<=target:price=target;reason=1;break
    if high[k]>=stop[a]:price=stop[a];reason=-1;break
    if low[k]<=target:price=target;reason=1;break
   k+=1
  if k==len(op):k-=1;price=cl[k];reason=3
  ex[a]=k;gross[a]=di*(price-op[j])/r;why[a]=reason;lastexit=k
 return ex,gross,why

T=[]
for sn,part in alls.groupby('strategy',sort=True):
 part=part.sort_values('entry_idx').copy()
 ix=part.entry_idx.to_numpy(np.int64);s=part.side.to_numpy(np.int8);st=part.stop.to_numpy(float)
 ex,gross,why=run(ix,s,st,o,h,l,c,ts)
 good=ex>=0;part=part.iloc[good].copy()
 ii=part.entry_idx.to_numpy(int);part['exit_idx']=ex[good];part['gross_R']=gross[good]
 part['net_R']=gross[good]-0.35/part.stop_distance.to_numpy(float)
 part['reason']=why[good];part['entry_israel_date']=ds[ii];part['exit_israel_date']=ds[ex[good]]
 part['entry_israel']=local[ii].astype(str);part['exit_israel']=local[ex[good]].astype(str)
 part['duration_min']=ts[ex[good]]-ts[ii]
 T.append(part)
trades=pd.concat(T,ignore_index=True).sort_values(['entry_idx','strategy']).reset_index(drop=True)
# Market dates: tradeable weekdays with >=200 minute bars (avoid holidays/partial days)
validdays=agg.loc[(agg.n>=200)].index.to_numpy(dtype='str');validdays=np.array([d for d in validdays if pd.Timestamp(str(d)).dayofweek<5]);
# Filter which market date gets a gate for next day. Only trades CLOSED before decision day begin are historical.
# First two dates have no lookback and are inactive.
active={}
rows=[]
for sn,group in trades.groupby('strategy'):
 dct={d:g for d,g in group.groupby('entry_israel_date')}
 active[sn]={}
 for i in range(2,len(validdays)):
  current=validdays[i];day1=validdays[i-2];day2=validdays[i-1]
  # entry-day grouping and all exits must have completed before start of today's 06h decision
  done=[];hit=[];counts=[];wrs=[]
  for d in (day1,day2):
   g=dct.get(d,pd.DataFrame())
   if len(g):
    gg=g.loc[(g.exit_israel_date<=d)] # if exit after midnight do not prematurely count
    counts.append(len(gg));wrs.append(float((gg.reason==1).mean()) if len(gg) else np.nan)
    done.extend(gg.net_R.tolist())
    hit.extend((gg.reason==1).tolist())
   else:counts.append(0);wrs.append(np.nan)
  po=np.asarray(done)
  hit=np.asarray(hit,dtype=bool)
  aggregate=(min(counts)>=1) and (len(po)>=2) and (hit.mean()>=.5) and (np.mean(po)>0)
  strict=(min(counts)>=1) and min(wrs)>=.5 and np.mean(po)>0
  four=aggregate and len(po)>=4
  active[sn][current]=(aggregate,strict,four)
  rows.append(dict(strategy=sn,date=current,prev_day1=day1,prev_day2=day2,n_day1=counts[0],n_day2=counts[1],winrate1=wrs[0],winrate2=wrs[1],two_day_n=len(po),two_day_winrate=float(hit.mean()) if len(po) else np.nan,two_day_mean_R=float(np.mean(po)) if len(po) else np.nan,active_aggregate=aggregate,active_strict=strict,active_min4=four))
G=pd.DataFrame(rows)
for gate,k in [('gate_agg','active_aggregate'),('gate_strict','active_strict'),('gate_min4','active_min4')]:
 trades[gate]=[active.get(s,{}).get(d,(False,False,False))[{'gate_agg':0,'gate_strict':1,'gate_min4':2}[gate]] for s,d in zip(trades.strategy,trades.entry_israel_date)]

# Actual shared-position portfolio replay starts from EVERY executable signal (not only paper-filled
# trades). Eligibility is computed from per-strategy paper trades. For coincident signals use a
# precommitted lexicographic strategy priority (never outcomes). No accidental overlapping fills.
alls['entry_israel_date']=ds[alls.entry_idx.to_numpy(int)]
for gate,col in [('gate_agg',0),('gate_strict',1),('gate_min4',2)]:
 alls[gate]=[active.get(s,{}).get(d,(False,False,False))[col] for s,d in zip(alls.strategy,alls.entry_israel_date)]
def replay_global(gate):
 a=(alls if gate=='all' else alls[alls[gate]]).sort_values(['entry_idx','strategy']).drop_duplicates('entry_idx').copy()
 j=a.entry_idx.to_numpy('int64');side=a.side.to_numpy('int8');stop=a.stop.to_numpy(float)
 ex,gross,why=run(j,side,stop,o,h,l,c,ts)
 good=ex>=0
 a=a.iloc[good].copy(); jj=a.entry_idx.to_numpy(int);xx=ex[good]
 a['exit_idx']=xx;a['gross_R']=gross[good];a['net_R']=gross[good]-0.35/a.stop_distance.to_numpy(float)
 a['reason']=why[good];a['entry_israel_date']=ds[jj];a['exit_israel_date']=ds[xx]
 a['entry_israel']=local[jj].astype(str);a['exit_israel']=local[xx].astype(str)
 a['duration_min']=ts[xx]-ts[jj]
 return a
runs={mode:replay_global(mode) for mode in ['all','gate_agg','gate_strict','gate_min4']}

cut1='2026-01-01';cut2='2026-04-01'
def period(d):return '2025_dev' if d<cut1 else ('2026Q1_reused' if d<cut2 else '2026Q2Q3_reused')

metrics=[]
for sn,ss in list(trades.groupby('strategy'))+[('PORTFOLIO',None)]:
 for mode in (['all','gate_agg','gate_strict','gate_min4']):
  z=(ss if mode=='all' else ss[ss[mode]]) if sn!='PORTFOLIO' else runs[mode]
  for timep,sub in z.groupby(z.entry_israel_date.map(period)):
   dates=[d for d in validdays if period(d)==timep]
   metrics.append(dict(strategy=sn,policy=mode,period=timep,n=int(len(sub)),avg_R=float(sub.net_R.mean()) if len(sub) else np.nan,winrate_pct=float((sub.reason==1).mean()*100) if len(sub) else np.nan,positive_close_pct=float((sub.net_R>0).mean()*100) if len(sub) else np.nan,total_R=float(sub.net_R.sum()),days=int(sub.entry_israel_date.nunique()),market_days=len(dates),coverage_pct=float(100*sub.entry_israel_date.nunique()/len(dates)) if dates else 0,median_risk=float(sub.stop_distance.median()) if len(sub) else np.nan,max_duration=float(sub.duration_min.max()) if len(sub) else np.nan))
metric=pd.DataFrame(metrics)
# Fill portfolio p/week comparisons, week decision streak eligible but drop periods with zero trades
trades.to_csv(P/'all_ten_strategy_trades.csv',index=False)
G.to_csv(P/'two_day_eligibility_by_strategy_date.csv',index=False)
metric.to_csv(P/'rotation_policy_metrics.csv',index=False)
for mode in runs:runs[mode].to_csv(P/f'portfolio_{mode}_trades.csv',index=False)
print('\nPORTFOLIO SUMMARY\n',metric[(metric.strategy=='PORTFOLIO')].to_string(index=False),flush=True)
print('\nPER-STRATEGY 2026Q2Q3\n',metric[(metric.strategy!='PORTFOLIO')&(metric.period=='2026Q2Q3_reused')].to_string(index=False),flush=True)
summary=dict(candles=N,market_days=len(validdays),strategy_count=10,total_signals=len(allsig),total_completed_trades=len(trades),cost_price_units=0.35,target_R=3.0,allowed_hours='06:00-20:00 Asia/Jerusalem',decision='06:00 of next market day; last two full market days; no contemporaneous performance',lookback='2 completed market days',archive_strategy_warning='original baseline trades are prior-research archival outputs and have not been fully causal-audited',rule_proxy_warning='other 9 are simplified first executable implementations; not identical to full ICT user concepts',review_warning='2026 used repeatedly and is not fresh holdout')
(P/'summary.json').write_text(json.dumps(summary,indent=2))
print('SUMMARY',summary,flush=True)