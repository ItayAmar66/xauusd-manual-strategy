#!/usr/bin/env python3
"""Non-lookahead, event-independent XAUUSD M5 multi-timeframe condition bank.
Only COMPLETED timeframe candles used at M5 bar-close time; invalidated FVGs excluded.
No 15M/5M retrospectively tagged winning legs are read or used in signals.
"""
from pathlib import Path
import json
import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
SRC=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if SRC.exists():
    m1=pd.read_csv(SRC)
else:
    from zipfile import ZipFile
    z=HERE.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
    with ZipFile(z) as f:
        name=next(x for x in f.namelist() if x.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
        m1=pd.read_csv(f.open(name))
m1.index=pd.to_datetime(m1.timestamp,unit='ms',utc=True)
m1=m1[['open','high','low','close']].astype(float)
assert len(m1)==760337 and m1.index.is_unique and m1.index.is_monotonic_increasing

m5=m1.resample('5min',closed='left',label='left').agg({'open':'first','high':'max','low':'min','close':'last'})
m5['count']=m1.close.resample('5min').count()
m5=m5[m5['count']>0].copy()
# All values at m5 row t become known at its close t+5min, never at its start.
signal_times=m5.index+pd.Timedelta(minutes=5)
valid_bar=(m5['count']==5)&(m5.index.to_series().diff()==pd.Timedelta(minutes=5))
valid_bar=valid_bar & valid_bar.shift(fill_value=False)
O,H,L,C=(m5[x] for x in ['open','high','low','close'])
def wilderatr(frame,n=14):
    h,l,c=frame['high'],frame['low'],frame['close']
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
atr5=wilderatr(m5)
ema20=C.ewm(span=20,adjust=False).mean();ema50=C.ewm(span=50,adjust=False).mean()
prev_close=C.shift(1)
change=C.diff();g=change.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean();l=(-change.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
rsi=100-100/(1+g/(l+1e-12))

# Israeli calendar (DST-aware); yesterday = last ACTUAL trading date, not a flat holiday date.
il=m5.index.tz_convert('Asia/Jerusalem'); day=pd.Index(il.date)
D=pd.DataFrame({'date':day,'hi':H.to_numpy(),'lo':L.to_numpy()}).groupby('date').agg({'hi':'max','lo':'min'})
prevday=D.shift(1)
pdh=pd.Series(day.map(prevday.hi),index=m5.index,dtype=float)
pdl=pd.Series(day.map(prevday.lo),index=m5.index,dtype=float)
# Weeks ending Sunday and previous 4 COMPLETED weeks; shifted to avoid knowledge of current week.
week=il.tz_localize(None).to_period('W-SUN')
W=pd.DataFrame({'week':week,'hi':H.to_numpy(),'lo':L.to_numpy()}).groupby('week').agg({'hi':'max','lo':'min'})
prevweek=W.shift(1)
pwh=pd.Series(week.map(prevweek.hi).to_numpy(dtype=float),index=m5.index)
pwl=pd.Series(week.map(prevweek.lo).to_numpy(dtype=float),index=m5.index)
week4_hi=W.hi.shift(1).rolling(4,min_periods=4).max()
week4_lo=W.lo.shift(1).rolling(4,min_periods=4).min()
w4h=pd.Series(week.map(week4_hi).to_numpy(dtype=float),index=m5.index)
w4l=pd.Series(week.map(week4_lo).to_numpy(dtype=float),index=m5.index)

# HTF as-of at close timestamp, using only fully-closed M15/H1/H4 bar.
def completed_tf(freq):
    agg=m1.resample(freq,closed='left',label='left').agg({'open':'first','high':'max','low':'min','close':'last'})
    agg['n']=m1.close.resample(freq).count()
    # For HTF gaps: require at least 80% occupancy; otherwise treat as unavailable.
    bar_mins=int(pd.Timedelta(freq).total_seconds()/60)
    agg=agg.loc[agg['n']>=int(bar_mins*.8)].copy()
    agg['ema20']=agg.close.ewm(span=20,adjust=False).mean()
    agg['ema50']=agg.close.ewm(span=50,adjust=False).mean()
    agg['atr14']=wilderatr(agg)
    agg['trend5']=np.sign(agg.close-agg.close.shift(5))
    agg['displacement']=abs(agg.close-agg.open)>1.2*agg.atr14
    agg.index=agg.index+pd.Timedelta(freq)  # becoming known AT BAR CLOSE
    return agg
f15=completed_tf('15min');f1=completed_tf('1h');f4=completed_tf('4h')
def align(col,frame):
    return frame[col].reindex(signal_times,method='ffill').to_numpy()
ctx={}
ctx['m15_up']=align('ema20',f15)>align('ema50',f15)
ctx['m15_down']=align('ema20',f15)<align('ema50',f15)
ctx['h1_up']=align('ema20',f1)>align('ema50',f1)
ctx['h1_down']=align('ema20',f1)<align('ema50',f1)
ctx['h4_up']=align('ema20',f4)>align('ema50',f4)
ctx['h4_down']=align('ema20',f4)<align('ema50',f4)
ctx['m15_displacement']=align('displacement',f15).astype(bool)
ctx['weekly_premium']=C.to_numpy()>(w4h.to_numpy()+w4l.to_numpy())/2
ctx['weekly_discount']=C.to_numpy()<(w4h.to_numpy()+w4l.to_numpy())/2
ctx['weekly_rangetop20']=C.to_numpy()>(w4l.to_numpy()+.8*(w4h-w4l).to_numpy())
ctx['weekly_rangebottom20']=C.to_numpy()<(w4l.to_numpy()+.2*(w4h-w4l).to_numpy())
ctx['m5_up']=ema20.to_numpy()>ema50.to_numpy()
ctx['m5_down']=ema20.to_numpy()<ema50.to_numpy()
ctx['m5_body_bull']=(C>O).to_numpy()
ctx['m5_body_bear']=(C<O).to_numpy()
ctx['m5_rejection_bull']=((C>O)&((C-L)>.65*(H-L))&((O-L)>.25*(H-L))).to_numpy()
ctx['m5_rejection_bear']=((C<O)&((H-C)>.65*(H-L))&((H-O)>.25*(H-L))).to_numpy()
ctx['m5_engulf_bull']=((C>O)&(C.shift(1)<O.shift(1))&(C>O.shift(1))&(O<C.shift(1))).to_numpy()
ctx['m5_engulf_bear']=((C<O)&(C.shift(1)>O.shift(1))&(C<O.shift(1))&(O>C.shift(1))).to_numpy()
ctx['m5_rsi_oversold']=(rsi<35).to_numpy();ctx['m5_rsi_overbought']=(rsi>65).to_numpy()
ctx['m5_breakup']=((C>H.shift(1).rolling(12).max())&(C.shift(1)<=H.shift(2).rolling(12).max())).fillna(False).to_numpy()
ctx['m5_breakdown']=((C<L.shift(1).rolling(12).min())&(C.shift(1)>=L.shift(2).rolling(12).min())).fillna(False).to_numpy()
ctx['pdl_sweep_reclaim']=((L<pdl)&(C>pdl)).fillna(False).to_numpy()
ctx['pdh_sweep_reclaim']=((H>pdh)&(C<pdh)).fillna(False).to_numpy()
ctx['pwl_sweep_reclaim']=((L<pwl)&(C>pwl)).fillna(False).to_numpy()
ctx['pwh_sweep_reclaim']=((H>pwh)&(C<pwh)).fillna(False).to_numpy()
for key in ['pdl_sweep_reclaim','pdh_sweep_reclaim','pwl_sweep_reclaim','pwh_sweep_reclaim']:
    ctx[key+'_last60m']=pd.Series(ctx[key],index=m5.index).rolling(12,min_periods=1).max().to_numpy(dtype=bool)
ctx['prior_15m_down']=(C.shift(1)-C.shift(4)<0).fillna(False).to_numpy()
ctx['prior_15m_up']=(C.shift(1)-C.shift(4)>0).fillna(False).to_numpy()

# Last CONFIRMED H1 swing high/low: 2 bars on each side, available after i+2 CLOSE.
# Fib retracement zone based on latest chronological pair of alternating confirmed pivots.
hourly=f1.reset_index();hourly=hourly.rename(columns={hourly.columns[0]:'known_time'})
valsH=hourly.high.to_numpy();valsL=hourly.low.to_numpy();timeH=hourly.known_time.astype('int64').to_numpy()
ph=[];pl=[];swing_events=[]
for i in range(2,len(hourly)-2):
    if valsH[i]>max(valsH[i-1],valsH[i-2],valsH[i+1],valsH[i+2]):swing_events.append((timeH[i+2],i,'HIGH',float(valsH[i])))
    if valsL[i]<min(valsL[i-1],valsL[i-2],valsL[i+1],valsL[i+2]):swing_events.append((timeH[i+2],i,'LOW',float(valsL[i])))
swing_events.sort()
times5=signal_times.asi8
fib_bull=np.zeros(len(m5),dtype=bool);fib_bear=np.zeros(len(m5),dtype=bool)
fib_low=np.full(len(m5),np.nan);fib_high=np.full(len(m5),np.nan)
lastH=None;lastL=None;j=0;anchor_time=None
for k,(t,price) in enumerate(zip(times5,C.to_numpy())):
    while j<len(swing_events) and swing_events[j][0]<=t:
        et,idx,typ,v=swing_events[j]
        if typ=='HIGH':lastH=(idx,v)
        else:lastL=(idx,v)
        j+=1
    if lastH is None or lastL is None:continue
    if lastH[0]>lastL[0]:
        delta=lastH[1]-lastL[1]
        if delta<=0:continue
        a0=lastH[1]-.786*delta;b0=lastH[1]-.618*delta
        fib_low[k]=a0;fib_high[k]=b0;fib_bull[k]=a0<=price<=b0
    elif lastL[0]>lastH[0]:
        delta=lastH[1]-lastL[1]
        if delta<=0:continue
        a0=lastL[1]+.618*delta;b0=lastL[1]+.786*delta
        fib_low[k]=a0;fib_high[k]=b0;fib_bear[k]=a0<=price<=b0
ctx['fib_h1_bull_618_786']=fib_bull
ctx['fib_h1_bear_618_786']=fib_bear

# Active FVG at M5 close and a price intersection during the completed M5 bar.
# Existing lifecycle uses available_at / invalidated_at, excluding invalidation close itself.
from zipfile import ZipFile
zpath=HERE.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
if Path('/mnt/data/XAUUSD_FVG_Lifecycle_CloseInvalidation.csv').exists():
    fvg=pd.read_csv('/mnt/data/XAUUSD_FVG_Lifecycle_CloseInvalidation.csv',usecols=['tf','direction','available_at','invalidated_at','level_low','level_high'])
else:
    with ZipFile(zpath) as z:
        name=next(x for x in z.namelist() if x.endswith('/XAUUSD_FVG_Lifecycle_CloseInvalidation.csv'))
        fvg=pd.read_csv(z.open(name),usecols=['tf','direction','available_at','invalidated_at','level_low','level_high'])
fvg=fvg[fvg.tf.isin(['M5','M15','H1','H4'])].copy()
fvg['start']=pd.to_datetime(fvg.available_at,utc=True).astype('int64')
fvg['stop']=pd.to_datetime(fvg.invalidated_at,utc=True,errors='coerce').astype('int64')
fvg.loc[fvg.invalidated_at.isna(),'stop']=np.iinfo('int64').max
low5=L.to_numpy();high5=H.to_numpy()
for (tf,side),grp in fvg.groupby(['tf','direction']):
    hit=np.zeros(len(m5),dtype=bool)
    for row in grp.itertuples():
        st=np.searchsorted(times5,row.start,side='right')  # zone formed exactly at close was NOT available during that candle
        en=np.searchsorted(times5,row.stop)
        if en<=st:continue
        hit[st:en]|=(low5[st:en]<=row.level_high)&(high5[st:en]>=row.level_low)
    ctx[f'fvg_touch_{tf}_{side}']=hit

# Persist only full M5 rows where the next M1 open exists, previous M1 minute is present.
mi=m1.index.get_indexer(signal_times)
valid_entry=(mi>=1);ix=np.maximum(mi,1)
valid_entry&=(m1.index.values[ix]==signal_times.values)&((m1.index.values[ix]-m1.index.values[ix-1])==np.timedelta64(1,'m'))
trade_t=signal_times.tz_convert('Asia/Jerusalem')
trade_hr=trade_t.hour+trade_t.minute/60
valid_entry&=(trade_hr>=6)&(trade_hr<20)&(trade_t.dayofweek<5)
valid_entry&=valid_bar.to_numpy()&np.isfinite(atr5.to_numpy())&(atr5.to_numpy()>0)
mask=np.where(valid_entry)[0]
# No historical successful-movement event catalog is used in signals.
feat=pd.DataFrame({k:np.asarray(v)[mask].astype(bool) for k,v in ctx.items()})
feat.insert(0,'entry_utc',signal_times[mask].astype(str))
feat.insert(1,'entry_israel',trade_t[mask].astype(str))
feat.insert(2,'entry_date',np.array(trade_t.date)[mask].astype(str))
feat.insert(3,'entry_m1_index',mi[mask])
feat.insert(4,'m5_atr14',atr5.to_numpy()[mask])
feat.insert(5,'signal_m5_close',C.to_numpy()[mask])
feat.insert(6,'fib_zone_low',fib_low[mask]);feat.insert(7,'fib_zone_high',fib_high[mask])
feat.to_csv(HERE/'condition_bank_m5.csv',index=False)
count={key:int(feat[key].sum()) for key in ctx}
(HERE/'condition_prevalence.json').write_text(json.dumps({'candidate_m5_closes':len(feat),'source_m1_bars':len(m1),'by_parameter':count},indent=2),encoding='utf8')
print('PASS candidate closed M5 signals:',len(feat),'parameters:',len(ctx),'FVG sections:',{k:v for k,v in count.items() if 'fvg' in k})