#!/usr/bin/env python3
"""Causal OHLC backtest for 26 XAUUSD M5-entry strategy families and 9 trade managers.
Data source: 760337 original XAUUSD M1 bid candles. Historical labeled reversal legs are NOT used as entry signals.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from numba import njit

OUT=Path(__file__).resolve().parent
SRC=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')  # local direct path, GitHub Actions uses the archived fallback
HOLDOUT='2026-04-01'
FEE=0.35                 # USD of XAUUSD price per completed trade: assumed friction, not observed spread
STRESS_FEE=0.70
MAX_HOLD_MINUTES=120
MIN_TRAIN=70
STOP_OPTIONS=(0.75,1.0,1.5,2.0,2.5)
np.random.seed(42)

if SRC.exists():
    m1=pd.read_csv(SRC)
else:
    from zipfile import ZipFile
    zp=OUT.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
    with ZipFile(zp) as z:
        member=next(n for n in z.namelist() if n.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
        m1=pd.read_csv(z.open(member))
m1['ts']=pd.to_datetime(m1.timestamp,unit='ms',utc=True)
m1=m1.set_index('ts')
m1=m1[['open','high','low','close']].astype('float64')
df=m1.resample('5min',label='left',closed='left').agg({'open':'first','high':'max','low':'min','close':'last'})
df['bars']=m1.close.resample('5min').count()
df=df[df.bars>0].copy()
# Signals only on complete 5-min bars, with a complete contiguous M5 predecessor
full=(df.bars==5)&(df.index.to_series().diff()==pd.Timedelta(minutes=5))
valid=full & full.shift(fill_value=False)
# All indicators use closed data at the end of the current M5 candle; orders enter NEXT M1 candle.
c=df.close;h=df.high;l=df.low;o=df.open
prev=c.shift()
tr=pd.concat([h-l,(h-prev).abs(),(l-prev).abs()],axis=1).max(axis=1)
a=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
ema9=c.ewm(span=9,adjust=False).mean();ema20=c.ewm(span=20,adjust=False).mean();ema21=c.ewm(span=21,adjust=False).mean();ema50=c.ewm(span=50,adjust=False).mean()
diff=c.diff();gain=diff.clip(lower=0).ewm(alpha=1/14,adjust=False,min_periods=14).mean();loss=(-diff.clip(upper=0)).ewm(alpha=1/14,adjust=False,min_periods=14).mean()
rsi=100-100/(1+gain/(loss+1e-12))
macd=c.ewm(span=12,adjust=False).mean()-c.ewm(span=26,adjust=False).mean();macd_sig=macd.ewm(span=9,adjust=False).mean()
ma20=c.rolling(20).mean();sd20=c.rolling(20).std();upper=ma20+2*sd20;lower=ma20-2*sd20
hi12=h.shift(1).rolling(12).max();lo12=l.shift(1).rolling(12).min();hi36=h.shift(1).rolling(36).max();lo36=l.shift(1).rolling(36).min()
hi20=h.shift(1).rolling(20).max();lo20=l.shift(1).rolling(20).min()
# Real Asia/Jerusalem time, honoring DST, NOT fixed UTC+3
local=df.index.tz_convert('Asia/Jerusalem')
date=pd.Series(local.date,index=df.index)
hour=local.hour+local.minute/60
# Compute prior complete Israel calendar day/week high/low, excluding current day
aggr=df.groupby(date).agg(high=('high','max'),low=('low','min'))
prevday=aggr.shift(1)
pdh=date.map(prevday.high);pdl=date.map(prevday.low)
pdh=pd.Series(np.asarray(pdh,dtype='float64'),index=df.index);pdl=pd.Series(np.asarray(pdl,dtype='float64'),index=df.index)
# Asia range determined solely by completed 00:00-05:59 Israeli candles.
asia=df[(hour>=0)&(hour<6)].groupby(date).agg(high=('high','max'),low=('low','min'))
ah=pd.Series(np.asarray(date.map(asia.high),dtype='float64'),index=df.index);al=pd.Series(np.asarray(date.map(asia.low),dtype='float64'),index=df.index)
# Opening range 06:00-06:59 in Israeli local time; entries only >=07:00
orb=df[(hour>=6)&(hour<7)].groupby(date).agg(high=('high','max'),low=('low','min'))
oh=pd.Series(np.asarray(date.map(orb.high),dtype='float64'),index=df.index);ol=pd.Series(np.asarray(date.map(orb.low),dtype='float64'),index=df.index)

def dirs(buy,sell):
    b=buy.fillna(False).to_numpy(dtype=bool) if hasattr(buy,'fillna') else np.asarray(buy,dtype=bool)
    s=sell.fillna(False).to_numpy(dtype=bool) if hasattr(sell,'fillna') else np.asarray(sell,dtype=bool)
    return np.where(b&~s,1,np.where(s&~b,-1,0)).astype('int8')

strategies={}
def add(name,b,s,atrstop=1.5,coverage=None):
    strategies[name]=(dirs(b,s),atrstop,coverage)

add('01_EMA9_21_cross',(ema9>ema21)&(ema9.shift()<=ema21.shift()),(ema9<ema21)&(ema9.shift()>=ema21.shift()))
add('02_EMA20_50_cross',(ema20>ema50)&(ema20.shift()<=ema50.shift()),(ema20<ema50)&(ema20.shift()>=ema50.shift()))
add('03_EMA20_pullback',(ema20>ema50)&(l<=ema20)&(c>ema20)&(c>o)&(c.shift()<=ema20.shift()),(ema20<ema50)&(h>=ema20)&(c<ema20)&(c<o)&(c.shift()>=ema20.shift()))
add('04_EMA50_pullback',(ema20>ema50)&(l<=ema50)&(c>ema50)&(c>o),(ema20<ema50)&(h>=ema50)&(c<ema50)&(c<o))
add('05_Donchian12_breakout',(c>hi12)&(c.shift()<=hi12.shift()),(c<lo12)&(c.shift()>=lo12.shift()))
add('06_Donchian36_breakout',(c>hi36)&(c.shift()<=hi36.shift()),(c<lo36)&(c.shift()>=lo36.shift()))
add('07_Donchian12_sweep_fade',(l<lo12)&(c>lo12)&(c>o),(h>hi12)&(c<hi12)&(c<o))
add('08_Donchian36_sweep_fade',(l<lo36)&(c>lo36)&(c>o),(h>hi36)&(c<hi36)&(c<o))
add('09_Prior_day_breakout',(c>pdh)&(c.shift()<=pdh.shift()),(c<pdl)&(c.shift()>=pdl.shift()))
add('10_Prior_day_sweep_fade',(l<pdl)&(c>pdl)&(c>o),(h>pdh)&(c<pdh)&(c<o))
maskasia=pd.Series((hour>=6)&(hour<12),index=df.index)
add('11_Asia_range_breakout',maskasia&(c>ah)&(c.shift()<=ah.shift()),maskasia&(c<al)&(c.shift()>=al.shift()))
add('12_Asia_range_sweep_fade',maskasia&(l<al)&(c>al)&(c>o),maskasia&(h>ah)&(c<ah)&(c<o))
add('13_RSI30_70_reclaim',(rsi>30)&(rsi.shift()<=30),(rsi<70)&(rsi.shift()>=70))
add('14_RSI20_80_reclaim',(rsi>20)&(rsi.shift()<=20),(rsi<80)&(rsi.shift()>=80))
add('15_RSI50_EMA_trend',(rsi>50)&(rsi.shift()<=50)&(c>ema50),(rsi<50)&(rsi.shift()>=50)&(c<ema50))
add('16_Bollinger_reentry',(c>lower)&(c.shift()<=lower.shift()),(c<upper)&(c.shift()>=upper.shift()))
add('17_Bollinger_breakout',(c>upper)&(c.shift()<=upper.shift()),(c<lower)&(c.shift()>=lower.shift()))
add('18_ATR_displacement_trend',(c-o>1.5*a)&(c>ema20)&(ema20>ema50),(o-c>1.5*a)&(c<ema20)&(ema20<ema50))
inside=(h.shift(1)<h.shift(2))&(l.shift(1)>l.shift(2))
add('19_Inside_bar_breakout',inside&(c>h.shift(1)),inside&(c<l.shift(1)))
engulf_up=(c>o)&(c.shift()<o.shift())&(c>o.shift())&(o<c.shift())
engulf_dn=(c<o)&(c.shift()>o.shift())&(c<o.shift())&(o>c.shift())
add('20_Engulf_extreme20',engulf_up&(l<=lo20),engulf_dn&(h>=hi20))
add('21_MACD_signal_cross',(macd>macd_sig)&(macd.shift()<=macd_sig.shift())&(c>ema50),(macd<macd_sig)&(macd.shift()>=macd_sig.shift())&(c<ema50))
# M5 Fair-Value Gap: a 3-candle imbalance, LAST CLOSED gap bounds, revisit on subsequent bar
bullgap=l>h.shift(2);beargap=h<l.shift(2)
bot_bull=pd.Series(np.where(bullgap,h.shift(2),np.nan),index=df.index).ffill().shift(1)
top_bull=pd.Series(np.where(bullgap,l,np.nan),index=df.index).ffill().shift(1)
bot_bear=pd.Series(np.where(beargap,h,np.nan),index=df.index).ffill().shift(1)
top_bear=pd.Series(np.where(beargap,l.shift(2),np.nan),index=df.index).ffill().shift(1)
add('22_M5_FVG_revisit',(l<=top_bull)&(h>=bot_bull)&(c>top_bull)&(c>o)&(l.shift(1)>top_bull.shift(1)),(h>=bot_bear)&(l<=top_bear)&(c<bot_bear)&(c<o)&(h.shift(1)<bot_bear.shift(1)))
# 15m FVG from COMPLETED M15 candles; convert to an as-of timeline at M15 close
f15=m1.resample('15min').agg({'high':'max','low':'min','close':'last'})
f15['n']=m1.close.resample('15min').count();f15=f15[f15.n==15]
bg=f15.low>f15.high.shift(2);sg=f15.high<f15.low.shift(2)
f15['bt_bull']=pd.Series(np.where(bg,f15.high.shift(2),np.nan),index=f15.index).ffill();f15['tp_bull']=pd.Series(np.where(bg,f15.low,np.nan),index=f15.index).ffill()
f15['bt_bear']=pd.Series(np.where(sg,f15.high,np.nan),index=f15.index).ffill();f15['tp_bear']=pd.Series(np.where(sg,f15.low.shift(2),np.nan),index=f15.index).ffill()
f15.index=f15.index+pd.Timedelta(minutes=15)
aligned=f15[['bt_bull','tp_bull','bt_bear','tp_bear']].reindex(df.index,method='ffill').shift(1)
add('23_M15_FVG_revisit',(l<=aligned.tp_bull)&(h>=aligned.bt_bull)&(c>aligned.tp_bull)&(c>o)&(l.shift()>aligned.tp_bull.shift()),(h>=aligned.bt_bear)&(l<=aligned.tp_bear)&(c<aligned.bt_bear)&(c<o)&(h.shift()<aligned.bt_bear.shift()))
# Daily 06:05 deterministic entry, executed 06:10, with trend from previous 12 completed M5 bars.
first=(hour==6+5/60)
add('24_Daily_0610_trend',pd.Series(first,index=df.index)&(c>c.shift(12)),pd.Series(first,index=df.index)&(c<c.shift(12)))
# Local opening range 06-07, traded 07-12 only
morning=pd.Series((hour>=7)&(hour<12),index=df.index)
add('25_Opening_hour_breakout',morning&(c>oh)&(c.shift()<=oh.shift()),morning&(c<ol)&(c.shift()>=ol.shift()))
add('26_RSI_extreme_fade',(rsi.shift()<25)&(rsi>rsi.shift())&(c>o)&(l<=lo12),(rsi.shift()>75)&(rsi<rsi.shift())&(c<o)&(h>=hi12))

# Signal generated at close of valid completed M5 bar t; trade executes at open t+5m (raw M1 minute).
entry_ts=df.index+pd.Timedelta(minutes=5)
mi=m1.index.get_indexer(entry_ts)
# only one-minute-contiguous feed around the open, no lookahead in signal building
okay=(mi>=1)
mi2=np.maximum(mi,1)
okay &= m1.index.values[mi2]==entry_ts.values
okay &= (m1.index.values[mi2]-m1.index.values[mi2-1])==np.timedelta64(1,'m')
# M1 open bar has available OHLC; signal features must have M5 atr and full bar
trade_local=entry_ts.tz_convert('Asia/Jerusalem')
local_hours=trade_local.hour+trade_local.minute/60
okay &= (local_hours>=6)&(local_hours<20) & (trade_local.dayofweek<5)
okay &= np.isfinite(a.to_numpy())&(a.to_numpy()>0)&valid.to_numpy()
M1_OPEN=m1.open.to_numpy();M1_HIGH=m1.high.to_numpy();M1_LOW=m1.low.to_numpy();M1_CLOSE=m1.close.to_numpy()
M1_TIME=m1.index.asi8//(60*10**9)
entry_idx=np.where(okay,mi,-1).astype('int64')
# stop multipliers chosen train-only from five values; nine exit managers
managers=[('fixed3',3,0),('fixed4',4,0),('fixed5',5,0),('be1p5_tp4',4,1),('be2_tp5',5,2),('ladder1_tp5',5,3),('ladder0p5_tp4',4,4),('fixed8',8,0),('be2_tp8',8,2)]

@njit
def simulate(side,entries,atr,opens,highs,lows,closes,times,stopmult,rr,manager,cost):
    n=len(side); maxtrs=n+1
    signals=np.empty(maxtrs,np.int64);exits=np.empty(maxtrs,np.int64);result=np.empty(maxtrs,np.float64);raw_r=np.empty(maxtrs,np.float64);minutes=np.empty(maxtrs,np.float64);orders=np.empty(maxtrs,np.int8);reasons=np.empty(maxtrs,np.int8)
    count=0;lock=-1
    for i in range(n):
        j=entries[i];dir=side[i]
        if dir==0 or j<0 or j<=lock:continue
        risk=atr[i]*stopmult
        if risk<0.4 or not np.isfinite(risk):continue
        if count>=maxtrs:break
        price=opens[j];stop=price-dir*risk;target=price+dir*rr*risk
        exitidx=j;xp=price;done=False;reason=9
        maxf=0.0
        for k in range(j,len(opens)):
            if times[k]-times[j]>=MAX_HOLD_MINUTES:
                exitidx=k;xp=opens[k];done=True;reason=0;break
            if k>j and times[k]-times[k-1]>1:
                exitidx=k;xp=opens[k];done=True;reason=2;break
            # Start-of-candle gap through stop/target is handled conservatively.
            if dir==1:
                if opens[k]<=stop:xp=opens[k];exitidx=k;done=True;reason=-1;break
                if opens[k]>=target:xp=target;exitidx=k;done=True;reason=1;break
                hitstop=lows[k]<=stop;hittp=highs[k]>=target
            else:
                if opens[k]>=stop:xp=opens[k];exitidx=k;done=True;reason=-1;break
                if opens[k]<=target:xp=target;exitidx=k;done=True;reason=1;break
                hitstop=highs[k]>=stop;hittp=lows[k]<=target
            if hitstop:
                xp=stop;exitidx=k;done=True;reason=-1;break
            if hittp:
                xp=target;exitidx=k;done=True;reason=1;break
            # Trailing updates happen after candle for NEXT candle. Using favorable highs
            # can only tighten for next candle, no guessing whether high or low came first.
            favorable=(highs[k]-price)*dir if dir==1 else (price-lows[k])
            if favorable>maxf:maxf=favorable
            if manager==1 and maxf>=1.5*risk:
                candidate=price
            elif manager==2 and maxf>=2*risk:
                candidate=price
            elif manager==3 and maxf>=1*risk:
                candidate=price+dir*max(0.0,(np.floor(maxf/risk)-1)*risk)
            elif manager==4 and maxf>=1*risk:
                candidate=price+dir*max(0.0,(np.floor(maxf/(0.5*risk))-2)*0.5*risk)
            else:candidate=stop
            if dir==1 and candidate>stop:stop=candidate
            if dir==-1 and candidate<stop:stop=candidate
        if not done:exitidx=len(opens)-1;xp=closes[-1];reason=3
        gross=dir*(xp-price)/risk
        net=gross-cost/risk
        signals[count]=j;exits[count]=exitidx;result[count]=net;raw_r[count]=gross;minutes[count]=times[exitidx]-times[j];orders[count]=dir
        reasons[count]=reason;lock=exitidx;count+=1
    return signals[:count],exits[:count],result[:count],raw_r[:count],minutes[:count],orders[:count],reasons[:count]


def score(ks,ex,rs,raw,mins,dirs):
    if not len(rs):return dict(n=0,avg_R=np.nan,total_R=0,win_rate_pct=np.nan,profit_factor=np.nan,max_drawdown_R=np.nan,days_with_trade=0,coverage_pct=0,max_consecutive_no_trade_days=0,median_hold_minutes=np.nan,loss_streak=0)
    t=pd.DatetimeIndex(m1.index[ks]).tz_convert('Asia/Jerusalem')
    traded=pd.Index(t.date).unique()
    # Eligible weekdays with real price activity, based on original M1 data
    ds=pd.to_datetime(traded)
    eq=np.r_[0,np.cumsum(rs)]; maxdd=float(np.min(eq-np.maximum.accumulate(eq)))
    # win rate includes costs, flat loses as non-win
    neg=-rs[rs<0].sum(); pos=rs[rs>0].sum()
    streak=0;maxstreak=0
    for v in rs:
        if v<=0:streak+=1;maxstreak=max(maxstreak,streak)
        else:streak=0
    mask=np.isin(MARKET_DATES.astype(str),traded.astype(str))
    longest=0;cur=0
    for xx in mask:
        if not xx:cur+=1;longest=max(longest,cur)
        else:cur=0
    return dict(n=int(len(rs)),avg_R=float(np.mean(rs)),total_R=float(rs.sum()),win_rate_pct=float(np.mean(rs>0)*100),profit_factor=float(pos/neg) if neg>0 else np.inf,max_drawdown_R=maxdd,days_with_trade=len(traded),coverage_pct=100*int(mask.sum())/len(mask),max_consecutive_no_trade_days=int(longest),median_hold_minutes=float(np.median(mins)),loss_streak=maxstreak)

# Eligible market days use nonzero daily range and >=200 M1 bars (avoid partial 180 bar day)
mt=m1.index.tz_convert('Asia/Jerusalem');group=pd.Series(mt.date,index=m1.index)
market=m1.groupby(group).agg(n=('close','size'),hi=('high','max'),lo=('low','min'))
market=market[(market.n>=200)&(market.hi>market.lo)]
MARKET_DATES=np.array([str(v) for v in market.index if pd.Timestamp(v).weekday()<5])
IS_HOLDOUT=np.array(MARKET_DATES)>=HOLDOUT
MARKET_DATES_ALL=MARKET_DATES.copy()
MKT_DEV=MARKET_DATES[~IS_HOLDOUT];MKT_HO=MARKET_DATES[IS_HOLDOUT]
fullmarket=MARKET_DATES
split_ns=pd.Timestamp(HOLDOUT,tz='Asia/Jerusalem').tz_convert('UTC').value//(60*10**9)
outputs=[];selected=[];tradelog=[]
for name,(signal,stopmult,_) in strategies.items():
    signal=signal.copy()
    # No M5 entries except the ones satisfying strict data, time guards.
    for stopmult_test in STOP_OPTIONS:
      for manage,rr,mid in managers:
        ks,ex,rs,raw,mins,ds,why=simulate(signal,entry_idx,a.to_numpy(),M1_OPEN,M1_HIGH,M1_LOW,M1_CLOSE,M1_TIME,stopmult_test,rr,mid,FEE)
        tr=M1_TIME[ks]<split_ns
        te=~tr
        MARKET_DATES=MKT_DEV
        dev=score(ks[tr],ex[tr],rs[tr],raw[tr],mins[tr],ds[tr])
        MARKET_DATES=MKT_HO
        ho=score(ks[te],ex[te],rs[te],raw[te],mins[te],ds[te])
        # Train-only fit score, reward positive expectancy but penalize low sample and low calendar coverage.
        fit=(dev['avg_R'] if np.isfinite(dev['avg_R']) else -99) - (0.12*np.sqrt(100/max(dev['n'],1)))
        if dev['n']<MIN_TRAIN:fit=-10000+dev['n']
        rec=dict(strategy=name,manager=manage,stop_atr=stopmult_test,target_R=rr,training_score=fit)
        rec.update({f'train_{k}':v for k,v in dev.items()});rec.update({f'holdout_{k}':v for k,v in ho.items()})
        outputs.append(rec)
    # Select ONLY from TRAIN. Holdout not inspected for choice.
    chosen=max((x for x in outputs if x['strategy']==name),key=lambda x:x['training_score'])
    selected.append(chosen.copy())
    mid=next(k for n,rr,k in managers if n==chosen['manager']);rr=chosen['target_R'];stopmult=chosen['stop_atr']
    ks,ex,rs,raw,mins,ds,why=simulate(signal,entry_idx,a.to_numpy(),M1_OPEN,M1_HIGH,M1_LOW,M1_CLOSE,M1_TIME,stopmult,rr,mid,FEE)
    atr_by_m1=np.full(len(M1_TIME),np.nan)
    vmask=entry_idx>=0
    atr_by_m1[entry_idx[vmask]]=a.to_numpy()[vmask]
    for k,j in enumerate(ks):
        initial_risk=atr_by_m1[j]*stopmult
        tradelog.append(dict(strategy=name,entry_utc=str(m1.index[j]),entry_il=str(m1.index[j].tz_convert('Asia/Jerusalem')),exit_utc=str(m1.index[ex[k]]),direction='LONG' if ds[k]==1 else 'SHORT',entry_price=M1_OPEN[j],exit_price=M1_OPEN[j]+ds[k]*raw[k]*initial_risk,initial_risk_price=initial_risk,gross_R=raw[k],net_R=rs[k],net_R_stress_fee07=raw[k]-STRESS_FEE/initial_risk,duration_minutes=mins[k],exit_reason={-1:'stop',0:'time',1:'target',2:'feed_gap',3:'data_end',9:'unknown'}.get(int(why[k]),'unknown'),split='train' if M1_TIME[j]<split_ns else 'holdout',management=chosen['manager'],target_R=rr,stop_atr=stopmult))

allvar=pd.DataFrame(outputs);selt=pd.DataFrame(selected)
allvar.to_csv(OUT/'all_1170_variants.csv',index=False)
selt.to_csv(OUT/'selected_26_strategies.csv',index=False)
alltr=pd.DataFrame(tradelog);alltr.to_csv(OUT/'all_selected_trades.csv',index=False)
print('market days',len(MKT_DEV),len(MKT_HO),'total',len(MARKET_DATES_ALL),'signal strategies',len(strategies),'configs',len(allvar))
print(selt[['strategy','manager','train_n','train_avg_R','holdout_n','holdout_avg_R','holdout_win_rate_pct','holdout_coverage_pct']].to_string(index=False))
with (OUT/'summary.json').open('w') as f:
    json.dump(dict(split=HOLDOUT,train_market_days=len(MKT_DEV),holdout_market_days=len(MKT_HO),strategy_families=len(strategies),variants=len(allvar),assumed_cost_price=FEE,assumed_stress_cost_price=STRESS_FEE,max_holding_minutes=MAX_HOLD_MINUTES,selected_holdout_R_positive=int((selt.holdout_avg_R>0).sum()),selected_holdout_R_ge_1=int((selt.holdout_avg_R>=1).sum()),selected_holdout_coverage_ge_95=int((selt.holdout_coverage_pct>=95).sum())),f,indent=2)