#!/usr/bin/env python3
"""Causal daily coverage-versus-expectancy frontier on existing 10 M1 proxy strategy trade logs.

Does not claim genuine implementation of all ICT models; excludes archival strategy 01.
One late conditional fallback is actually replayed against full M1 OHLC, with structural stop.
Before each day, ranks candidate strategies only on closed historical trades.
All prices available for hindsight-oracle comparison are labeled EX-POST ONLY.
"""
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd

BASE=Path(__file__).resolve().parent
DATA=Path('/mnt/data')
if not (DATA/'m1_rotation_two_day/all_ten_strategy_trades.csv').exists():
    # Repo-run location
    DATA=BASE.parent/'m1_rotating_strategies'/'two_day'
    SOURCE=DATA/'all_ten_strategy_trades.csv'
else:
    SOURCE=DATA/'m1_rotation_two_day/all_ten_strategy_trades.csv'
CANDLES=Path('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv')
if not CANDLES.exists():
    from zipfile import ZipFile
    z=BASE.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
    with ZipFile(z) as arc:
        mem=next(n for n in arc.namelist() if n.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
        raw=pd.read_csv(arc.open(mem))
else: raw=pd.read_csv(CANDLES)

T0=time.monotonic()
bar_ts=pd.to_datetime(raw.timestamp,unit='ms',utc=True).dt.tz_convert('Asia/Jerusalem')
market=pd.DataFrame({'day':bar_ts.dt.strftime('%Y-%m-%d'),'hour':bar_ts.dt.hour,'minute':bar_ts.dt.minute,'weekday':bar_ts.dt.weekday})
# Count a trading day only if this tape has complete scheduled signal/fallback availability
full=market[market.weekday<5].groupby('day').agg(bars=('hour','size'))
dayrange=raw.groupby(market.day).agg(hi=('high','max'),lo=('low','min'))
full['range']=dayrange.hi-dayrange.lo
full=full[(full.bars>=1000)&(full['range']>0)]
day_names=full.index.to_numpy()
nd=len(day_names)
day_lookup={d:i for i,d in enumerate(day_names)}
raw['day']=market.day.values
trade=pd.read_csv(SOURCE)
trade=trade[trade.strategy!='01_original_CHoCH_breaker_FVG_ARCHIVE'].copy()
trade['day']=trade.entry_israel_date.astype(str)
trade=trade[trade.day.isin(day_lookup)].copy()
trade['day_i']=trade.day.map(day_lookup).astype(int)
models=sorted(trade.strategy.unique().tolist())
model_lookup={m:i for i,m in enumerate(models)}
trade['sid']=trade.strategy.map(model_lookup).astype(int)
trade['min_of_day']=pd.to_datetime(trade.entry_israel,utc=True).dt.tz_convert('Asia/Jerusalem').dt.hour*60+pd.to_datetime(trade.entry_israel,utc=True).dt.tz_convert('Asia/Jerusalem').dt.minute
# PREVIOUS COMPLETED SHADOW TRADES ONLY. Existing model simulation already closes inside 120m, before midnight.
assert (trade.entry_israel_date==trade.exit_israel_date).all()
assert (trade.duration_min<=120).all()
# no Look-Ahead: all 9 model shadow fills are scored only after their exit; candidate order chronological.
trade=trade.sort_values(['day_i','entry_idx','sid']).reset_index(drop=True)
N=len(models)
counts=np.zeros((nd,N),dtype=int)
sums=np.zeros((nd,N),dtype=float)
hits=np.zeros((nd,N),dtype=int)
for row in trade.itertuples(index=False):
    d=row.day_i; m=row.sid
    counts[d,m]+=1;sums[d,m]+=row.net_R;hits[d,m]+=int(row.reason==1 and row.gross_R>=2.999999)
cum_n=np.vstack([np.zeros((1,N),dtype=int),np.cumsum(counts,axis=0)])
cum_r=np.vstack([np.zeros((1,N)),np.cumsum(sums,axis=0)])
cum_hit=np.vstack([np.zeros((1,N),dtype=int),np.cumsum(hits,axis=0)])
by_day=[]
for d in range(nd):
    df=trade[trade.day_i==d]
    by_day.append({
        'sid':df.sid.to_numpy(dtype=np.int16),
        'entry':df.entry_idx.to_numpy(dtype=np.int64),
        'exit':df.exit_idx.to_numpy(dtype=np.int64),
        'minute':df.min_of_day.to_numpy(dtype=np.int16),
        'net':df.net_R.to_numpy(dtype=float),
        'stop_dist':df.stop_distance.to_numpy(dtype=float),
        'reason':df.reason.to_numpy(dtype=int),
    })
print(f'SHADOW {len(trade)} fills, {N} nonarchival models, {nd} completed weekdays')

# 17:55 rescue trade is always available by design on the 446 eligible active-price trading days.
# The trade is precommitted in this experiment: direction from last 60 complete minutes,
# stop outside extrema of last 15 or 30 complete M1 bars, target 3R, stop first in ambiguous candles.
openh=raw.open.to_numpy(float); highh=raw.high.to_numpy(float); loww=raw.low.to_numpy(float); closeh=raw.close.to_numpy(float)
timestamps=(raw.timestamp.to_numpy(np.int64)//60000)
mask=(market.hour==17)&(market.minute==55)&(market.weekday<5)&market.day.isin(day_lookup)
idxs=np.flatnonzero(mask.to_numpy())
assert len(idxs)==nd, (len(idxs),nd)

fallback=[]
for j in idxs:
    dt=str(raw.day.iat[j]);di=day_lookup[dt]
    # require contiguous minute data; late starts/holes disqualify day in full domain.
    if j<61 or np.any(np.diff(timestamps[j-60:j+1])!=1):raise ValueError('gap before fallback '+dt)
    side=1 if closeh[j-1]-closeh[j-61]>=0 else -1
    base=openh[j]
    extreme=np.min(loww[j-15:j]) if side==1 else np.max(highh[j-15:j])
    sl=min(extreme,base)-0.10 if side==1 else max(extreme,base)+0.10
    risk=(base-sl)*side
    # Never change invalidation price to manufacture a favorable backtest.
    if risk<=0:
        raise ValueError('invalid structural risk '+dt)
    tp=base+3*side*risk
    exitprice=None;ex=None;why=0
    for k in range(j,len(openh)):
        if timestamps[k]-timestamps[j]>=120:
            ex=k;exitprice=openh[k];why=0;break
        if k>j and timestamps[k]-timestamps[k-1]>1:
            ex=k;exitprice=openh[k];why=2;break
        if side==1:
            if openh[k]<=sl: ex=k;exitprice=openh[k];why=-1;break
            if openh[k]>=tp: ex=k;exitprice=tp;why=1;break
            hs=loww[k]<=sl; ht=highh[k]>=tp
        else:
            if openh[k]>=sl: ex=k;exitprice=openh[k];why=-1;break
            if openh[k]<=tp: ex=k;exitprice=tp;why=1;break
            hs=highh[k]>=sl; ht=loww[k]<=tp
        if hs: ex=k;exitprice=sl;why=-1;break
        if ht: ex=k;exitprice=tp;why=1;break
    if ex is None:
        raise ValueError('missing fallback exit '+dt)
    gross=side*(exitprice-base)/risk
    net=gross-0.35/risk
    fallback.append((di,j,ex,risk,gross,net,why,dt,side,base,sl,tp,float(timestamps[ex]-timestamps[j])))
fb=pd.DataFrame(fallback,columns=['day_i','entry_idx','exit_idx','stop_distance','gross_R','net_R','exit_reason','day','side','entry_price','SL','TP','duration_min'])
assert fb.day_i.nunique()==nd and (fb.duration_min<=120).all()
fb=fb.sort_values('day_i').reset_index(drop=True)
fb.to_csv(BASE/'daily_1755_structural_fallback_trades.csv',index=False)

# Oracle is a hindsight *theoretical upper bound*, impossible to implement without future knowledge.
orow=[]
for d in range(nd):
    p=by_day[d]
    keep=(p['minute']<17*60+55)
    candidates=p['net'][keep]
    arg=np.argmax(candidates) if len(candidates) else -1
    best=max(float(candidates.max()) if len(candidates) else -1e9,float(fb.net_R.iloc[d]))
    orow.append({'date':day_names[d],'model_candidates':len(candidates),
                 'any_profitable_candidate':bool(np.any(candidates>0)),'any_3R_candidate':bool(np.any(p['reason'][keep]==1)),
                 'oracle_best_net_R':best,'fallback_R':fb.net_R.iloc[d]})
oracle=pd.DataFrame(orow)
oracle.to_csv(BASE/'hindsight_oracle_NOT_TRADABLE.csv',index=False)

# A policy is a *precommitment* to a method at 06:00, based on prior completed days only.
# It may choose up to K models. At each qualifying actual entry time it chooses the first signal,
# then a later signal only after prior trade exited (up to max/day).
WINDOWS={
    'full':lambda x:(x>=360)&(x<1075),
    'london_ny':lambda x:((x>=540)&(x<720))|((x>=930)&(x<1075)),
    'ny':lambda x:(x>=900)&(x<1075),
}

def active_models(day,lookback,topk,min_n,mode,only_positive,reverse=False):
    past=max(0,day-lookback)
    cnt=cum_n[day]-cum_n[past]
    total=cum_r[day]-cum_r[past]
    n_tp=cum_hit[day]-cum_hit[past]
    eligible=cnt>=min_n
    if mode=='netR': score=total/(cnt+12)
    elif mode=='win3':score=(n_tp-0.25*cnt)/(cnt+12)
    elif mode=='totalR':score=total/(cnt+12)**0.5
    else: raise ValueError(mode)
    if only_positive:eligible&=score>0
    if not eligible.any():return np.empty(0,dtype=int)
    indexes=np.flatnonzero(eligible)
    order=np.argsort(score[indexes],kind='stable')
    if not reverse:order=order[::-1]
    return indexes[order[:topk]]

def replay(lookback,topk,min_n,mode,positive,reverse,window,maxday,fallback_on,save=False):
    res=[]; logs=[];mask_window=WINDOWS[window]
    for d in range(nd):
        selected=active_models(d,lookback,topk,min_n,mode,positive,reverse)
        p=by_day[d]
        accepted=0;lock=-1
        if selected.size:
            allow=np.isin(p['sid'],selected)&mask_window(p['minute'])
            # All model entries are restricted to before 17:55, when the rescue order may be executed.
            indices=np.flatnonzero(allow)
            for i in indices:
                if p['entry'][i]<=lock:continue
                accepted+=1;lock=p['exit'][i]
                res.append((d,float(p['net'][i]),float(p['stop_dist'][i]),False,int(p['sid'][i])))
                if save:logs.append((day_names[d],int(p['entry'][i]),int(p['exit'][i]),models[int(p['sid'][i])],float(p['net'][i]),False))
                if accepted>=maxday:break
        if accepted==0 and fallback_on:
            res.append((d,float(fb.net_R.iloc[d]),float(fb.stop_distance.iloc[d]),True,-1))
            if save:logs.append((day_names[d],int(fb.entry_idx.iloc[d]),int(fb.exit_idx.iloc[d]),'FALLBACK_1755',float(fb.net_R.iloc[d]),True))
    arr=np.array(res,dtype=[('d','i4'),('r','f8'),('risk','f8'),('fallback','?'),('model','i2')])
    return arr, logs

def metrics(records,ds):
    a=records[np.isin(records['d'],ds)]
    days=len(ds);count=len(a)
    if count==0:return {'n':0,'coverage_pct':0,'mean_R':np.nan,'sum_R':0,'tp_equivalent_at3R_pct':np.nan,'max_dd_R':np.nan,'fallback_pct':np.nan,'meanR_fee070':np.nan}
    cum=np.cumsum(np.r_[0.,a['r']]);dd=(cum-np.maximum.accumulate(cum)).min()
    return dict(n=count,coverage_pct=100*len(set(a['d']))/days,mean_R=float(a['r'].mean()),sum_R=float(a['r'].sum()),
                positive_pct=float(np.mean(a['r']>0)*100),max_dd_R=float(dd),fallback_pct=float(np.mean(a['fallback'])*100),
                meanR_fee070=float(np.mean(a['r']-0.35/a['risk'])),days=days)

dates=pd.to_datetime(day_names)
period_masks={'2025H1':np.flatnonzero((dates<'2025-07-01')),
              '2025H2':np.flatnonzero((dates>='2025-07-01')&(dates<'2026-01-01')),
              '2026Q1':np.flatnonzero((dates>='2026-01-01')&(dates<'2026-04-01')),
              '2026Q2Q3_REUSED':np.flatnonzero(dates>='2026-04-01')}

# Target-driven feasible selection: rank on 2025H2 ONLY, second-stage 2026Q1 for validation; Q2Q3 kept for reporting.
configs=[]
for window in ('full','ny'):
  for lookback in (5,10,20,40,80):
    for topk in (1,2,5):
      for min_n in (0,8):
        for mode in ('netR','win3'):
          for positive in (True,False):
            for reverse in (False,):
              # Initially exactly one entry per day; alternate is max three total.
              for maxday in (1,3):
                configs.append((lookback,topk,min_n,mode,positive,reverse,window,maxday))

rows=[];best_val=None;best_h2=None
for ci,cfg in enumerate(configs):
    r,_=replay(*cfg,True)
    per={p:metrics(r,ds) for p,ds in period_masks.items()}
    row={'config_id':ci,'lookback_days':cfg[0],'top_k':cfg[1],'min_shadow_trades':cfg[2],
         'score':cfg[3],'positive_score_only':cfg[4],'hours':cfg[6],'max_trades_per_day':cfg[7],
         'num_models':N,'with_1755_fallback':True}
    for p,v in per.items():
        for k,q in v.items():row[f'{p}_{k}']=q
    rows.append(row)
trials=pd.DataFrame(rows)
trials.to_csv(BASE/'all_480_causal_policy_trials.csv',index=False)
# First filter coverage exactly 100; choose policy from 2025H2 by mean R and small penalty to n.
trials['train_score']=trials['2025H2_mean_R'] - 0.12*np.sqrt(130/trials['2025H2_n'].clip(lower=1))
sel2025=trials.sort_values('train_score',ascending=False).iloc[0]
# Research diagnostic: highest 2026Q1 hindsight choice violates train-before-test selection, label exploratory only.
selq1=trials.sort_values('2026Q1_mean_R',ascending=False).iloc[0]
trials.sort_values('train_score',ascending=False).head(20).to_csv(BASE/'top20_selected_from_2025H2.csv',index=False)
summary_rows=[]
for who,row in [('2025H2_ONLY_SELECTED',sel2025),('2026Q1_POSTHOC_NOT_VALID',selq1)]:
    cfg=configs[int(row.config_id)]
    rec,logs=replay(*cfg,True,save=True)
    pd.DataFrame(logs,columns=['date','entry_idx','exit_idx','model','net_R','fallback']).to_csv(BASE/(who+'_trades.csv'),index=False)
    for p,ds in period_masks.items():summary_rows.append({'policy':who,'period':p,**metrics(rec,ds),'config_id':int(row.config_id)})
# benchmark first signal any non-archival plus rescue
for who,cfg in [
  ('ALL_FIRST_SIGNAL_1_A_DAY',(10,9,0,'netR',False,False,'full',1)),
  ('ALL_FIRST_3_PER_DAY',(10,9,0,'netR',False,False,'full',3)),
  ('NY_FIRST_1_A_DAY',(10,9,0,'netR',False,False,'ny',1)),
]:
    rec,logs=replay(*cfg,True,save=True)
    pd.DataFrame(logs,columns=['date','entry_idx','exit_idx','model','net_R','fallback']).to_csv(BASE/(who+'_trades.csv'),index=False)
    for p,ds in period_masks.items():summary_rows.append({'policy':who,'period':p,**metrics(rec,ds),'config_id':-1})
# baseline fallback alone, no shadow entry, always one/day
all_fb=np.array([(int(r.day_i),float(r.net_R),float(r.stop_distance),True,-1) for r in fb.itertuples(index=False)],dtype=[('d','i4'),('r','f8'),('risk','f8'),('fallback','?'),('model','i2')])
for p,ds in period_masks.items():summary_rows.append({'policy':'FALLBACK_ONLY_1755','period':p,**metrics(all_fb,ds),'config_id':-1})
# Feasible projection of perfect foresight (NOT causal)
for p,ds in period_masks.items():summary_rows.append({'policy':'HINDSIGHT_ORACLE_NOT_TRADABLE','period':p,'n':len(ds),'coverage_pct':100,'mean_R':oracle.iloc[ds].oracle_best_net_R.mean(),'sum_R':oracle.iloc[ds].oracle_best_net_R.sum(),'days':len(ds),'config_id':-1})
pd.DataFrame(summary_rows).to_csv(BASE/'coverage_expectancy_frontier.csv',index=False)

# weekly-block bootstrap for the PRE-SELECTED policy on reused final-period; reflect serial correlation.
rec,_=replay(*configs[int(sel2025.config_id)],True)
darr=rec[np.isin(rec['d'],period_masks['2026Q2Q3_REUSED'])]
day_to_week=np.array([pd.Timestamp(d).to_period('W-SUN').start_time.strftime('%Y-%m-%d') for d in day_names])
weeks=np.unique(day_to_week[darr['d']]);rv=[darr['r'][day_to_week[darr['d']]==w] for w in weeks]
rng=np.random.default_rng(20261022);boots=[]
for i in range(5000):
    sample=rng.integers(0,len(rv),size=len(rv))
    all_vals=np.concatenate([rv[k] for k in sample]);boots.append(float(all_vals.mean()))
ci=np.quantile(boots,[.025,.5,.975])

# Opportunity frontier for 2026 data, how often hindsight chooses a 3R winner (NOT an implementable policy).
report={
  'method':'2025H2 model selection; 2026Q1 validation; Apr-Sep2026 reused review; no fresh holdout',
  'model_warning':'9 simplified, nonvalidated ICT strategy proxies; original archived baseline omitted',
  'source_shadow_trades':int(len(trade)),'eligible_days':nd,'policy_count':len(configs),
  'fall_back_rule':'At 17:55, only when no previous fill: trade direction of past 60m, SL beyond prior 15m candle extreme by 0.10, TP=3R, <=120min, cost .35 USD/oz bid approximation',
  'best_2025H2_policy_id':int(sel2025.config_id),
  'chosen_2025H2_parameters':{k:sel2025[k] for k in ('lookback_days','top_k','min_shadow_trades','score','positive_score_only','hours','max_trades_per_day')},
  'best_2025H2_avgR':float(sel2025['2025H2_mean_R']),
  'chosen_2026Q1_avgR':float(sel2025['2026Q1_mean_R']),
  'chosen_2026_reused_avgR':float(sel2025['2026Q2Q3_REUSED_mean_R']),
  'chosen_2026_reused_bootstrap_CI95_R':ci.tolist(),
  '2026_reused_oracle_mean_R':float(oracle.iloc[period_masks['2026Q2Q3_REUSED']].oracle_best_net_R.mean()),
  '2026_reused_any3R_candidate_day_pct':float(oracle.iloc[period_masks['2026Q2Q3_REUSED']].any_3R_candidate.mean()*100),
  '2026_reused_any_profitable_day_pct':float(oracle.iloc[period_masks['2026Q2Q3_REUSED']].any_profitable_candidate.mean()*100),
  'cost_price_units':0.35,
  'data_start':str(raw.timestamp.iloc[0]),'data_end':str(raw.timestamp.iloc[-1]),
  'performance_status':'NOT A VERIFIED +1R PER-TRADE STRATEGY; reused historical periods; no tick/spread'
}
with open(BASE/'summary.json','w') as f:json.dump(report,f,indent=2,default=str)
print('SUMMARY',json.dumps(report,default=str,indent=2))
print('FRONTIER\n',pd.DataFrame(summary_rows).round(3).to_string(index=False))
print('DONE sec',round(time.monotonic()-T0,2))