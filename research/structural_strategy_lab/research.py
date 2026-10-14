#!/usr/bin/env python3
"""Live-time reaction-zone / microstructure entries with structural stops.
Research script: exploratory, fully reproducible from original M1 CSV and bank CSV.
"""
from pathlib import Path
import numpy as np, pandas as pd, json, time
from numba import njit
P=Path(__file__).resolve().parent
SRC=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
BANK=Path('/mnt/data/parameter_bank/condition_bank_m5.csv')
if not BANK.exists(): BANK=P.parent/'parameter_bank'/'condition_bank_m5.csv'
if not BANK.exists():raise RuntimeError('First build the condition bank, missing '+str(BANK))
if SRC.exists():m=pd.read_csv(SRC)
else:
    from zipfile import ZipFile
    zpath=P.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
    with ZipFile(zpath) as z:
        member=next(x for x in z.namelist() if x.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
        m=pd.read_csv(z.open(member))
b=pd.read_csv(BANK)
N=len(m)
mt=pd.to_datetime(m.timestamp,unit='ms',utc=True); il=mt.dt.tz_convert('Asia/Jerusalem')
hour=il.dt.hour.to_numpy()+il.dt.minute.to_numpy()/60
O=m.open.to_numpy();H=m.high.to_numpy();L=m.low.to_numpy();C=m.close.to_numpy();TIME=m.timestamp.to_numpy()//60000
sC=pd.Series(C); sH=pd.Series(H); sL=pd.Series(L)
# Established daily/week extrema from completed local-calendar date groups, not current group.
D=il.dt.date.astype(str);W=(il.dt.tz_localize(None).dt.normalize()-pd.to_timedelta(il.dt.weekday,unit='D')).dt.date.astype(str)
prev={}
for name,labels in [('day',D),('week',W)]:
    t=pd.DataFrame({'group':labels.to_numpy(),'high':H,'low':L}).groupby('group',sort=True).agg({'high':'max','low':'min'}).shift(1)
    prev[name+'h']=t.high.reindex(labels.to_numpy()).to_numpy()
    prev[name+'l']=t.low.reindex(labels.to_numpy()).to_numpy()
PDH,PDL,PWH,PWL=(prev[x] for x in ('dayh','dayl','weekh','weekl'))
# Already-closed M1 candles only in the signal; all entries at NEXT minute open.
atr_indices=b.entry_m1_index.to_numpy(dtype=np.int64)
atr_vals=b.m5_atr14.to_numpy(dtype=np.float64)
# as-of bank feature at the next minute's open: never use features stamped after fill.
k=np.searchsorted(atr_indices,np.arange(N,dtype=np.int64)+1,side='right')-1
k=np.maximum(k,0)
ATR=atr_vals[k]
B={col:np.asarray(b[col].fillna(False).astype('bool'))[k] for col in b.columns if b[col].dtype.name=='bool'}
# Convert early NaN values from the roll to false, using previous completed M1.
roll={}
for z in (3,5,10,15,30,60):
    roll['lo'+str(z)]=sL.shift(1).rolling(z,min_periods=z).min().to_numpy()
    roll['hi'+str(z)]=sH.shift(1).rolling(z,min_periods=z).max().to_numpy()
# M1 candle patterns with no future labels.
prevO=np.r_[np.nan,O[:-1]];prevC=np.r_[np.nan,C[:-1]];prevH=np.r_[np.nan,H[:-1]];prevL=np.r_[np.nan,L[:-1]]
rng=np.maximum(H-L,1e-8); body=np.abs(C-O)
revbull=(C>O)&((C-L)/rng>=0.70)&((np.minimum(C,O)-L)/rng>=0.22)
revbear=(C<O)&((H-C)/rng>=0.70)&((H-np.maximum(C,O))/rng>=0.22)
engbull=(C>O)&(prevC<prevO)&(C>prevO)&(O<prevC)
engbear=(C<O)&(prevC>prevO)&(C<prevO)&(O>prevC)
strongbull=(C>O)&((C-O)/rng>0.65)
strongbear=(C<O)&((O-C)/rng>0.65)
breakbull=(C>roll['hi3'])&strongbull
breakbear=(C<roll['lo3'])&strongbear
# Sweeps must occur in current closed signal candle; wick crosses known prior extrema.
pdSbull=(L<PDL)&(C>PDL)&(prevC>=PDL)
pdSbear=(H>PDH)&(C<PDH)&(prevC<=PDH)
pwSbull=(L<PWL)&(C>PWL)&(prevC>=PWL)
pwSbear=(H>PWH)&(C<PWH)&(prevC<=PWH)
# Nearby, a recent liquidity grab then microstructure break close.
lastbars=10
breach_pdL=(L<PDL)&(C<PDL)
breach_pdH=(H>PDH)&(C>PDH)
pdBbull=(pd.Series(breach_pdL.astype('int8')).rolling(lastbars,min_periods=1).max().shift(1).fillna(0).to_numpy()>0)&(C>PDL)&breakbull
pdBbear=(pd.Series(breach_pdH.astype('int8')).rolling(lastbars,min_periods=1).max().shift(1).fillna(0).to_numpy()>0)&(C<PDH)&breakbear
# FVG and HTF conditions must have been available in source feature bank before next-open entry.
F15b=B['fvg_touch_M15_BULL'];F15s=B['fvg_touch_M15_BEAR']
F1hb=B['fvg_touch_H1_BULL'];F1hs=B['fvg_touch_H1_BEAR']
F4hb=B['fvg_touch_H4_BULL'];F4hs=B['fvg_touch_H4_BEAR']
H1up=B['h1_up'];H1dn=B['h1_down'];M15up=B['m15_up'];M15dn=B['m15_down']
WKdisc=B['weekly_discount'];WKprem=B['weekly_premium']
Fibbull=B['fib_h1_bull_618_786'];Fibbear=B['fib_h1_bear_618_786']
# Structuring entries; each strategy has BOTH long/short signals.
setups={
 '01_PD_sweep_reclaim':(pdSbull,pdSbear),
 '02_PW_sweep_reclaim':(pwSbull,pwSbear),
 '03_PD_delayed_break3':(pdBbull,pdBbear),
 '04_Local15_reject':((L<roll['lo15'])&revbull,(H>roll['hi15'])&revbear),
 '05_Local30_reject':((L<roll['lo30'])&revbull,(H>roll['hi30'])&revbear),
 '06_Local60_reject':((L<roll['lo60'])&revbull,(H>roll['hi60'])&revbear),
 '07_Local15_engulf':((L<roll['lo15'])&engbull,(H>roll['hi15'])&engbear),
 '08_Local30_break3':((sL.shift(1).rolling(5).min().to_numpy()<roll['lo30'])&breakbull,(sH.shift(1).rolling(5).max().to_numpy()>roll['hi30'])&breakbear),
 '09_FVG_H1_reject':(F1hb&revbull,F1hs&revbear),
 '10_FVG_M15_reject':(F15b&revbull,F15s&revbear),
 '11_FVG_H4_engulf':(F4hb&engbull,F4hs&engbear),
 '12_FiboH1_reject':(Fibbull&revbull,Fibbear&revbear),
 '13_M15_trend_microbreak':(M15up&breakbull,M15dn&breakbear),
 '14_PD_sweep_engulf':((pd.Series(pdSbull).rolling(5).max().shift(1).fillna(0).to_numpy()>0)&engbull,(pd.Series(pdSbear).rolling(5).max().shift(1).fillna(0).to_numpy()>0)&engbear),
 '15_FVG_M15_microbreak':(F15b&breakbull,F15s&breakbear),
 '16_Local5_reject':((L<roll['lo5'])&revbull,(H>roll['hi5'])&revbear),
 '17_Weekly_PD_local15_reject':(WKdisc&(L<roll['lo15'])&revbull,WKprem&(H>roll['hi15'])&revbear),
 '18_FVG_H1_local15_reject':(F1hb&(L<roll['lo15'])&revbull,F1hs&(H>roll['hi15'])&revbear)
}
filters={
 'none':(np.ones(N,dtype=bool),np.ones(N,dtype=bool)),
 'M15_align':(M15up,M15dn),
 'H1_align':(H1up,H1dn),
 'M15_H1_align':(M15up&H1up,M15dn&H1dn),
 'M15_counter':(M15dn,M15up),
 'weekly_PD':(WKdisc,WKprem),
 'FVG_M15':(F15b,F15s),
 'FVG_H1':(F1hb,F1hs),
 'M15_H1_FVG_M15':(M15up&H1up&F15b,M15dn&H1dn&F15s),
 'weekly_PD_H1_FVG':(WKdisc&F1hb,WKprem&F1hs)
}
# signal on completed minute i. Entry at next minute i+1, with no gaps.
next_j=np.arange(N)+1
candidate_ok=(next_j<N); next_clip=np.minimum(next_j,N-1)
candidate_ok &= (TIME[next_clip]-TIME==1)
entry_hour=np.r_[hour[1:],99.0]; entry_wkday=np.r_[il.dt.weekday.to_numpy()[1:],6]
candidate_ok &= (entry_hour>=6)&(entry_hour<20)&(entry_wkday<5)
candidate_ok &= (ATR>0.05)&np.isfinite(ATR)
# enforce a fully available M5 feature bank record at or before entry
candidate_ok &= np.arange(N)+1>=atr_indices[0]
# price level at signal close known, set SL beyond structural low/high with 0.10ATR buffer
# if stop would have been crossed by next-open gap, reject at time of fill.
FEE=0.35; time_start=time.time()
@njit
def sim(entries,side,stopdist,rr,manager,open_,high,low,close,times):
    count=0;hold_until=-1
    K=len(entries); totals=np.empty(K,np.float64); periods=np.empty(K,np.int64); durs=np.empty(K,np.int64);ers=np.empty(K,np.int64);exits=np.empty(K,np.int64);flags=np.empty(K,np.int8)
    for p in range(K):
        j=entries[p];di=side[p];risk=stopdist[p]
        if j<=hold_until:continue
        if risk<0.55 or not np.isfinite(risk):continue
        entry=open_[j];stop=entry-di*risk;target=entry+di*rr*risk
        peak=0.;exit_i=j;exit_px=entry;why=9
        for k in range(j,len(times)):
            if times[k]-times[j]>=120:
                exit_i=k;exit_px=open_[k];why=0;break
            if k>j and times[k]-times[k-1]!=1:
                exit_i=k-1;exit_px=close[k-1];why=2;break
            # stop-first and market gap-through handling
            if di==1:
                if open_[k]<=stop:exit_i=k;exit_px=open_[k];why=-1;break
                if open_[k]>=target:exit_i=k;exit_px=target;why=1;break
                hitstop=low[k]<=stop;hittp=high[k]>=target
            else:
                if open_[k]>=stop:exit_i=k;exit_px=open_[k];why=-1;break
                if open_[k]<=target:exit_i=k;exit_px=target;why=1;break
                hitstop=high[k]>=stop;hittp=low[k]<=target
            if hitstop:exit_i=k;exit_px=stop;why=-1;break
            if hittp:exit_i=k;exit_px=target;why=1;break
            fav=(high[k]-entry) if di==1 else (entry-low[k])
            if fav>peak:peak=fav
            if manager==1 and peak>=1.0*risk:
                be=entry
                if di==1 and be>stop:stop=be
                if di==-1 and be<stop:stop=be
            if manager==2 and peak>=1.5*risk:
                be=entry
                if di==1 and be>stop:stop=be
                if di==-1 and be<stop:stop=be
            if manager==3 and peak>=1.0*risk:
                locked=np.floor(peak/(0.5*risk))*0.5-1.0
                trail=entry+di*locked*risk
                if di==1 and trail>stop:stop=trail
                if di==-1 and trail<stop:stop=trail
        totals[count]=(di*(exit_px-entry)-0.35)/risk
        periods[count]=int(times[j]); durs[count]=int(times[exit_i]-times[j]);ers[count]=j;exits[count]=exit_i;flags[count]=why
        hold_until=exit_i;count+=1
    return totals[:count],periods[:count],durs[:count],ers[:count],exits[:count],flags[:count]

def score(r,periods,periodStart,periodEnd):
    mask=(periods>=periodStart)&(periods<periodEnd)
    rr=r[mask];tt=periods[mask]
    if not len(rr):return {'n':0,'avg_R':None,'win_pct':None,'dd_R':None,'total_R':0,'days':0,'coverage':0}
    eq=np.r_[0.,np.cumsum(rr)]
    idx2=np.searchsorted(TIME,tt)
    uniq=len(np.unique(D.to_numpy()[idx2])); possible_dates=MARKET_PERIOD_COUNTS[(periodStart,periodEnd)]
    return {'n':len(rr),'avg_R':float(np.mean(rr)),'win_pct':float(100*np.mean(rr>0)),'dd_R':float(np.min(eq-np.maximum.accumulate(eq))),'total_R':float(np.sum(rr)),'days':uniq,'coverage':100*uniq/max(1,possible_dates)}
# partitions boundaries local: 2025-01 through Dec 2025 DEVELOPMENT; 2026 Q1 validation, Apr-Sep reused review
start=lambda date: int(pd.Timestamp(date,tz='Asia/Jerusalem').tz_convert('UTC').value//(60*10**9))
periods=[('dev_2025',start('2025-01-01'),start('2026-01-01')),('validation_2026Q1',start('2026-01-01'),start('2026-04-01')),('review_reused_2026Q2Q3',start('2026-04-01'),start('2026-10-01'))]
market=pd.DataFrame({'date':D,'h':H,'l':L}).groupby('date').agg({'h':'max','l':'min'}); mdates=market.index[(market.h>market.l)&(pd.to_datetime(market.index).dayofweek<5)]
DAY_TS=[start(x) for x in mdates]
MARKET_PERIOD_COUNTS={(t0,t1):sum(t0<=t<t1 for t in DAY_TS) for _,t0,t1 in periods}
records=[];trades=[]
# fastest precompute structural stop distances from actual open at next minute.
M=np.maximum(ATR,0)
for stopmode in ['struct5','struct10','atr1']:
  pass
styles=['struct5','struct10','atr1']
for fname,(sb,ss) in setups.items():
  for filtername,(fb,fs) in filters.items():
    if filtername not in ('none','M15_align','H1_align','weekly_PD','FVG_H1'):continue
    buy=sb&fb&candidate_ok;sell=ss&fs&candidate_ok
    both=buy&sell;buy=buy&~both;sell=sell&~both
    idx=np.flatnonzero(buy|sell)
    if len(idx)<60:continue
    entries=(idx+1).astype('int64');direction=np.where(buy[idx],1,-1).astype('int8')
    nextopen=O[entries]
    for stopmode in styles:
      if stopmode.startswith('struct'):
        look=int(stopmode.removeprefix('struct'))
        lo=sL.rolling(look,min_periods=look).min().to_numpy()[idx]
        hi=sH.rolling(look,min_periods=look).max().to_numpy()[idx]
        pad=0.10*ATR[idx]
        sl=np.where(direction==1,lo-pad,hi+pad)
        risk=(nextopen-sl)*direction
      else:
        mul=1.0 if stopmode=='atr1' else 1.5
        risk=ATR[idx]*mul
      # guards against tiny spread-sensitive stops, huge stops, or already broken stop from opening gap.
      isok=np.isfinite(risk)&(risk>=0.65)&(risk<=6*ATR[idx])
      if np.count_nonzero(isok)<30:continue
      je=entries[isok];de=direction[isok];ri=risk[isok]
      for rr in (3.,4.,6.):
        for manage in (0,2):
          ret,ts,dur,kidx,ex,why=sim(je,de,ri,rr,manage,O,H,L,C,TIME)
          rec={'setup':fname,'filter':filtername,'stop':stopmode,'tp_R':rr,'manager':manage,'signals_eligible':len(je),'total_n':len(ret),'fee_price_units':FEE}
          for label,t0,t1 in periods:
            s=score(ret,ts,t0,t1)
            rec.update({label+'_'+n:v for n,v in s.items()})
          records.append(rec)
          if (fname,filtername,stopmode,rr,manage) in [('01_PD_sweep_reclaim','none','struct10',4.,0)]:pass
# Save full test universe incl unsuccessful and unavailable.
a=pd.DataFrame(records)
a.to_csv(P/'all_variants.csv',index=False)
# choose rules on Development only, threshold minimum 90 trades; from each setup choose highest conservative score.
chosen=[]
for name,grp in a.groupby('setup'):
   g=grp[(grp.dev_2025_n>=90)&(grp.validation_2026Q1_n>=30)].copy()
   if len(g)==0:continue
   g['score']=g.dev_2025_avg_R-0.3*np.sqrt(80/g.dev_2025_n)
   g=g.sort_values('score',ascending=False)
   chosen.append(g.iloc[0])
selected=pd.DataFrame(chosen).sort_values('dev_2025_avg_R',ascending=False)
selected.to_csv(P/'train_selected_by_family.csv',index=False)
# Re-run selected to get entry-by-entry genuine logs (not just aggregate) and identify best review but never choose it as valid.
for _,s in selected.iterrows():
    name,filtername,stopmode=s['setup'],s['filter'],s['stop']
    sb,ss=setups[name];fb,fs=filters[filtername];buy=sb&fb&candidate_ok;sell=ss&fs&candidate_ok
    both=buy&sell;buy=buy&~both;sell=sell&~both
    idx=np.flatnonzero(buy|sell)
    je=idx+1;dire=np.where(buy[idx],1,-1)
    if stopmode.startswith('struct'):
        look=int(stopmode.removeprefix('struct'));lo=sL.rolling(look,min_periods=look).min().to_numpy()[idx];hi=sH.rolling(look,min_periods=look).max().to_numpy()[idx];pad=0.10*ATR[idx];sl=np.where(dire==1,lo-pad,hi+pad);risk=(O[je]-sl)*dire
    else:risk=ATR[idx]*(1.0 if stopmode=='atr1' else 1.5)
    ok=np.isfinite(risk)&(risk>=0.65)&(risk<=6*ATR[idx]);je=je[ok];dire=dire[ok].astype(np.int8);risk=risk[ok]
    out,ts,dur,entries,ex,why=sim(je.astype(np.int64),dire,risk,float(s.tp_R),int(s.manager),O,H,L,C,TIME)
    direction_by_minute=np.zeros(N,dtype=np.int8);direction_by_minute[je]=dire
    for i in range(len(out)):
        j=entries[i];trades.append({'strategy':name,'filter':filtername,'stop':stopmode,'tp_R':s.tp_R,'manager':s.manager,'entry_israel':str(il.iloc[j]),'exit_israel':str(il.iloc[ex[i]]),'entry_price':O[j],'direction':'LONG' if direction_by_minute[j]==1 else 'SHORT','net_R':out[i],'duration_m':dur[i],'exit_reason':why[i]})
# print leaderboard top for each split, no false OOS claims
print('Variants:',len(a),'selected families:',len(selected),'seconds:',round(time.time()-time_start,2))
for label in ['dev_2025','validation_2026Q1','review_reused_2026Q2Q3']:
   top=a[(a[label+'_n']>=50)&a[label+'_avg_R'].notna()].sort_values(label+'_avg_R',ascending=False).head(10)
   print('\nTOP '+label+' (exploratory):')
   print(top[['setup','filter','stop','tp_R','manager',label+'_n',label+'_avg_R',label+'_coverage']].to_string(index=False))
print('\nTRAIN-SELECTED REVIEW:')
print(selected[['setup','filter','stop','tp_R','manager','dev_2025_n','dev_2025_avg_R','validation_2026Q1_avg_R','review_reused_2026Q2Q3_avg_R','review_reused_2026Q2Q3_coverage']].to_string(index=False))
pd.DataFrame(trades).to_csv(P/'train_selected_trade_logs.csv',index=False)
with open(P/'summary.json','w') as f:
 json.dump({'M1_candles':N,'variations':len(a),'selected_families':len(selected),'periods':[(x[0],x[1],x[2]) for x in periods],'assumed_cost_XAUUSD_price':FEE,'data_start':str(il.iloc[0]),'data_end':str(il.iloc[-1]),'caveats':['2026 reviewed repeatedly in prior research','bid OHLC only and artificial cost','same-bar stop-first','no fresh untouched holdout','ZigZag winners never used as signals'],'runtime_sec':round(time.time()-time_start,2)},f,indent=2)