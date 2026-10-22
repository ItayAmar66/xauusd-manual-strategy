#!/usr/bin/env python3
"""Additional OOS experiment: Does a frozen pre-entry ML ranking select profitable M1 fills?

Models trained Jan-Jun 2025, thresholds selected Jul-Dec 2025. 2026 never fit.
Only causal features observable at trade open. Max one fill/day; 19:55 fallback.
Nine unvalidated proxy strategies, no ex-post zone labels.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
P=Path(__file__).resolve().parent
DATA=Path('/mnt/data')
if (DATA/'xauusd-m1-bid-2025-01-01-2026-09-25.csv').exists():
    raw=pd.read_csv(DATA/'xauusd-m1-bid-2025-01-01-2026-09-25.csv')
else:
    from zipfile import ZipFile
    archive=P.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
    with ZipFile(archive) as z:
        member=next(n for n in z.namelist() if n.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
        raw=pd.read_csv(z.open(member))
source=(DATA/'m1_rotation_two_day/all_ten_strategy_trades.csv') if (DATA/'m1_rotation_two_day/all_ten_strategy_trades.csv').exists() else P.parent/'m1_rotating_strategies'/'two_day'/'all_ten_strategy_trades.csv'
trade=pd.read_csv(source)
trade=trade[trade.strategy!='01_original_CHoCH_breaker_FVG_ARCHIVE'].copy()
ref=pd.read_csv(P/'daily_1755_structural_fallback_trades.csv')
days=list(ref.day);byday={d:i for i,d in enumerate(days)}
trade=trade[trade.entry_israel_date.isin(byday)].copy()
trade['day_i']=trade.entry_israel_date.map(byday).astype(int)
trade['minute']=(pd.to_datetime(trade.entry_israel,utc=True).dt.tz_convert('Asia/Jerusalem').dt.hour*60+pd.to_datetime(trade.entry_israel,utc=True).dt.tz_convert('Asia/Jerusalem').dt.minute)
trade=trade[trade.minute<1075].sort_values(['day_i','entry_idx','strategy']).reset_index(drop=True)
idx=trade.entry_idx.to_numpy(dtype=int)
# Features from FULLY CLOSED M1 candles only. Index j is next-bar open of an M1 signal.
c=raw.close;h=raw.high;l=raw.low;o=raw.open
tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
atr=tr.rolling(20,min_periods=20).mean().shift(1).to_numpy()
vol60=tr.rolling(60,min_periods=60).mean().shift(1).to_numpy()
prevhi=h.rolling(15,min_periods=15).max().shift(1).to_numpy()
prevlo=l.rolling(15,min_periods=15).min().shift(1).to_numpy()
cl1=c.shift(1).to_numpy();op1=o.shift(1).to_numpy();h1=h.shift(1).to_numpy();l1=l.shift(1).to_numpy()
feat=pd.DataFrame({
  'hour':trade.minute.to_numpy()/60,
  'weekday':pd.to_datetime(trade.entry_israel_date).dt.weekday.to_numpy(),
  'risk_usd':trade.stop_distance.to_numpy(dtype=float),
  'fee_R':0.35/trade.stop_distance.to_numpy(dtype=float),
  'risk_to_vol20':trade.stop_distance.to_numpy(dtype=float)/np.maximum(atr[idx],0.05),
  'vol20':atr[idx],
  'vol60':vol60[idx],
  'impulse_5_m1':(cl1[idx]-c.shift(6).to_numpy()[idx])/np.maximum(atr[idx],0.05),
  'impulse_15_m1':(cl1[idx]-c.shift(16).to_numpy()[idx])/np.maximum(atr[idx],0.05),
  'impulse_60_m1':(cl1[idx]-c.shift(61).to_numpy()[idx])/np.maximum(atr[idx],0.05),
  'prev_candle_body':(cl1[idx]-op1[idx])/np.maximum(atr[idx],0.05),
  'prev_candle_range':(h1[idx]-l1[idx])/np.maximum(atr[idx],0.05),
  'near_prev15_high':(prevhi[idx]-cl1[idx])/np.maximum(atr[idx],0.05),
  'near_prev15_low':(cl1[idx]-prevlo[idx])/np.maximum(atr[idx],0.05),
  'long_side':(trade.side.to_numpy()==1).astype(int),
})
feat=pd.concat([feat,pd.get_dummies(trade.strategy,prefix='S',dtype=float)],axis=1)
feat=feat.replace([np.inf,-np.inf],np.nan).fillna(0.)
# Save definitions for independent review.
feat.to_csv(P/'preentry_feature_matrix.csv',index=False)
y=trade.net_R.to_numpy(dtype=float)
train=(trade.entry_israel_date<'2025-07-01').to_numpy()
val=((trade.entry_israel_date>='2025-07-01')&(trade.entry_israel_date<'2026-01-01')).to_numpy()
hold=(trade.entry_israel_date>='2026-01-01').to_numpy()
models={
 'ridge':make_pipeline(StandardScaler(),Ridge(alpha=3000.)),
 'hgb_regression':HistGradientBoostingRegressor(max_iter=140,learning_rate=.04,max_leaf_nodes=7,min_samples_leaf=120,l2_regularization=50,random_state=20261022),
}
periods={
 '2025H1_FITTED':np.array([i for i,d in enumerate(days) if d<'2025-07-01']),
 '2025H2_THRESHOLD_TUNING':np.array([i for i,d in enumerate(days) if '2025-07-01'<=d<'2026-01-01']),
 '2026Q1_VALIDATION':np.array([i for i,d in enumerate(days) if '2026-01-01'<=d<'2026-04-01']),
 '2026Q2Q3_REUSED':np.array([i for i,d in enumerate(days) if d>='2026-04-01']),
}
fbR=ref.net_R.to_numpy();fbRisk=ref.stop_distance.to_numpy()

def first_threshold_policy(pred,threshold,session):
    # No future information in selection. We know score at candidate entry, never later candidate results.
    k0=trade.day_i.to_numpy(int)
    time=trade.minute.to_numpy(int)
    if session=='all': eligible=time>=360
    elif session=='ny':eligible=(time>=900)&(time<1075)
    elif session=='core':eligible=((time>=540)&(time<720))|((time>=930)&(time<1075))
    else:raise ValueError(session)
    fits=np.flatnonzero((pred>=threshold)&eligible)
    seen=np.full(len(days),False,dtype=bool)
    choose=np.full(len(days),-1,dtype=int)
    # Trade arrays sorted by day/entry index; selecting first eligible per day guarantees no overlap.
    for i in fits:
        d=k0[i]
        if not seen[d]:
            seen[d]=True; choose[d]=i
    result=fbR.copy()
    risk=fbRisk.copy()
    selected=choose>=0
    result[selected]=y[choose[selected]]
    risk[selected]=trade.stop_distance.to_numpy(float)[choose[selected]]
    return result,risk,choose

all_rows=[]
validation_grid=[]
for name,model in models.items():
    model.fit(feat.loc[train],y[train])
    pred=model.predict(feat)
    trade[name+'_predicted_R']=pred
    # Threshold from prior TRAIN prediction distribution alone. Tuning on 2025H2 only.
    thr=np.quantile(pred[train],[.05,.25,.5,.65,.8,.9,.95,.99])
    candidates=[]
    for k,cut in enumerate(thr):
      for session in ('all','ny','core'):
        r,stop,choose=first_threshold_policy(pred,float(cut),session)
        q=periods['2025H2_THRESHOLD_TUNING']
        v=r[q]
        candidates.append(dict(model=name,quantile=float([.05,.25,.5,.65,.8,.9,.95,.99][k]),cutoff=float(cut),session=session,
                               avg2025H2=float(v.mean()),n2025H2=len(v),n_signals2025H2=int(np.sum(choose[q]>=0)),
                               cost070avg2025H2=float(np.mean(v-0.35/stop[q]))))
    # Selection train-only 2025H2 average R; require >=20 chosen model fills to avoid fallback-only.
    cs=sorted((c for c in candidates if c['n_signals2025H2']>=20),key=lambda t:t['avg2025H2']-.12/np.sqrt(t['n_signals2025H2']),reverse=True)
    chosen=cs[0] if cs else sorted(candidates,key=lambda a:a['avg2025H2'],reverse=True)[0]
    validation_grid.extend(candidates)
    for typ,cho in [('2025H2_selected',chosen),('fallback_only',{'cutoff':float('inf'),'session':'all','quantile':1.})]:
        rr,risk,sel=first_threshold_policy(pred,cho['cutoff'],cho['session'])
        df=pd.DataFrame({'date':days,'R':rr,'risk_usd':risk,'from_model':(sel>=0),
                         'model':name,'selection':typ,'strategy':trade.strategy.to_numpy()[np.maximum(sel,0)]})
        df.loc[sel<0,'strategy']='LATE_FALLBACK'
        df.to_csv(P/f'ML_{name}_{typ}_daily_trades.csv',index=False)
        for per,q in periods.items():
            sub=rr[q]
            all_rows.append(dict(model=name,selection=typ,period=per,n=len(q),mean_R=float(sub.mean()),sum_R=float(sub.sum()),
                      picked_model=int((sel[q]>=0).sum()),fallback=int((sel[q]<0).sum()),
                      win_pct=float(np.mean(sub>0)*100),meanR_fee070=float(np.mean(sub-0.35/risk[q])),
                      cutoff=cho['cutoff'],session=cho['session']))
        print(name,typ,chosen,'period',[(k,round(rr[q].mean(),3)) for k,q in periods.items()])
pd.DataFrame(validation_grid).to_csv(P/'ml_threshold_grid.csv',index=False)
pd.DataFrame(all_rows).to_csv(P/'ml_period_results.csv',index=False)
trade[['strategy','entry_israel','entry_idx','net_R','ridge_predicted_R','hgb_regression_predicted_R']].to_csv(P/'ml_all_candidate_predictions.csv',index=False)
json.dump({'model_training':'January-June 2025 fixed; thresholds based only July-December 2025; no refit in 2026',
           'models':list(models),'features':list(feat.columns), 'n_training_trades':int(train.sum()),'n_validation_trades':int(val.sum()),'n_2026_shadow':int(hold.sum()),
           'limitations':'May have correlated/duplicated labels across simultaneous strategies; 2026 reused many times; no true tick or live execution'},
           open(P/'ml_summary.json','w'),indent=2)