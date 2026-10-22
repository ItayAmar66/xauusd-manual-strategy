#!/usr/bin/env python3
"""Strictly lagged M1 entry features on ten-playbook shadow signals; 3R hit classifier.
Read raw archived original M1 candles, and prior nine-proxy trade log; exclude unaudited custom archive.
Exploratory study, not a deployable or clinically statistically validated strategy.
"""
from pathlib import Path
import json
from zipfile import ZipFile
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1] if (HERE.parents[1]/'research').exists() else None
ZIPLOCAL=Path('/mnt/data/XAUUSD_Manual_Strategy_Research_Git_Import.zip')
if ZIPLOCAL.exists():
    source=ZIPLOCAL
elif REPO is not None:
    source=REPO/'research/15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip'
else:
    source=HERE.parent.parent/'15M ATR/XAUUSD_Manual_Strategy_Research_Git_Import.zip'
loglocal=Path('/mnt/data/m1_rotation_two_day/all_ten_strategy_trades.csv')
if loglocal.exists():
    trade_src=loglocal
elif REPO is not None:
    trade_src=REPO/'research/m1_rotating_strategies/two_day/all_ten_strategy_trades.csv'
else:
    trade_src=HERE.parent.parent/'m1_rotating_strategies/two_day/all_ten_strategy_trades.csv'
with ZipFile(source) as z:
    member=next(n for n in z.namelist() if n.endswith('xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
    prices=pd.read_csv(z.open(member))
trades=pd.read_csv(trade_src)
trades=trades[~trades.strategy.str.contains('ARCHIVE')].copy()
assert len(prices)==760337 and len(trades)>25000
trades['date']=trades.entry_israel_date.astype(str)
trades['hit_3R']=((trades.reason==1)&(trades.gross_R>=2.999)).astype(int)
trades['period']=np.select([trades.date<'2025-07-01',trades.date<'2026-01-01',trades.date<'2026-04-01'],['2025H1_TRAIN','2025H2_VALID','2026Q1_TEST'],default='2026Q2Q3_REUSED')
price=prices.close
prev=price.shift(1)
ret=prev.diff()
rg=(prices.high-prices.low).shift(1)
base=rg.rolling(20,min_periods=20).median().clip(lower=.001)
feat=pd.DataFrame(index=prices.index)
for k in [5,15,60]:
    feat[f'return_{k}_minutes']=((prev-prev.shift(k))/base).clip(-50,50)
feat['body_last']=((prices.close.shift(1)-prices.open.shift(1))/base).clip(-25,25)
feat['range_last']=(rg/base).clip(0,50)
feat['local_vol_20']=(rg.rolling(20,min_periods=20).mean()/base).clip(0,50)
feat['local_vol_60']=(rg.rolling(60,min_periods=60).mean()/base).clip(0,50)
feat['prior15_hi_dist']=((prices.high.shift(1).rolling(15,min_periods=15).max()-prev)/base).clip(-50,50)
feat['prior15_lo_dist']=((prev-prices.low.shift(1).rolling(15,min_periods=15).min())/base).clip(-50,50)
ema20=price.ewm(span=20,adjust=False).mean().shift(1)
ema50=price.ewm(span=50,adjust=False).mean().shift(1)
feat['ema20_minus_ema50']=((ema20-ema50)/base).clip(-50,50)
feat['ema20_slope_10']=((ema20-ema20.shift(10))/base).clip(-50,50)
idx=trades.entry_idx.to_numpy(dtype=int)
assert (idx>100).all() and (idx<len(prices)).all()
# Verify raw index and already published trade entry correspond.
assert np.mean(np.isclose(prices.open.to_numpy()[idx],trades.entry_price.to_numpy(),atol=.001))>0.999
F=feat.iloc[idx].reset_index(drop=True).copy()
F['side']=trades.side.to_numpy()
F['risk_relative_vol20']=(trades.stop_distance.to_numpy()/base.iloc[idx].to_numpy()).clip(0,60)
F['fee_relative_risk']=(.35/trades.stop_distance.to_numpy()).clip(0,4)
local=pd.to_datetime(trades.entry_israel,utc=True).dt.tz_convert('Asia/Jerusalem')
F['hour']=local.dt.hour.to_numpy()+local.dt.minute.to_numpy()/60
F['weekday']=local.dt.weekday.to_numpy()
for strategy in sorted(trades.strategy.unique()):F['S_'+strategy]=(trades.strategy==strategy).to_numpy().astype(float)
assert not F.isna().any().any()
Y=trades.hit_3R.to_numpy()
train=trades.date.lt('2025-07-01').to_numpy()
models={
 'logistic':make_pipeline(StandardScaler(),LogisticRegression(C=.2,max_iter=700,random_state=17)),
 'shallow_tree':HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=7,max_depth=3,min_samples_leaf=160,learning_rate=.05,l2_regularization=10,random_state=17)
}
for n,m in models.items():
    m.fit(F[train],Y[train])
    trades[n+'_p3']=m.predict_proba(F)[:,1]
periods=['2025H1_TRAIN','2025H2_VALID','2026Q1_TEST','2026Q2Q3_REUSED']
rows=[];diag=[]
for name in models:
    col=name+'_p3'
    for per in periods:
        d=trades[trades.period==per]
        pr=d[col].to_numpy();yy=d.hit_3R.to_numpy()
        diag.append(dict(model=name,period=per,candidates=len(d),base_hit3_pct=100*yy.mean(),top10pct_hit3_pct=100*yy[pr>=np.quantile(pr,.9)].mean(),top5pct_hit3_pct=100*yy[pr>=np.quantile(pr,.95)].mean(),auc=float(roc_auc_score(yy,pr)),average_precision=float(average_precision_score(yy,pr)),highest_predicted_p3=float(pr.max())))
    for th in [.20,.25,.30,.35,.40,.45,.50]:
        eligible=trades[trades[col]>=th].sort_values(['date','entry_idx',col],ascending=[True,True,False]).drop_duplicates('date',keep='first')
        for per in periods:
            selected=eligible[eligible.period==per]
            d=trades[trades.period==per]
            rows.append(dict(model=name,threshold=th,period=per,n=len(selected),possible_days=d.date.nunique(),days_covered=selected.date.nunique(),coverage_pct=100*selected.date.nunique()/d.date.nunique(),full_3R_hit_pct=100*selected.hit_3R.mean() if len(selected) else np.nan,mean_net_R=selected.net_R.mean() if len(selected) else np.nan,cost_R= (.35/selected.stop_distance).mean() if len(selected) else np.nan))
metrics=pd.DataFrame(rows);disc=pd.DataFrame(diag)
# Validation selects only rules with minimum 25% day coverage and >=25 trades, fixed before 2026.
pick=metrics[(metrics.period=='2025H2_VALID')&(metrics.coverage_pct>=25)&(metrics.n>=25)].sort_values(['full_3R_hit_pct','mean_net_R'],ascending=False).head(1)
chosen=pick.iloc[0].to_dict() if len(pick) else {}
if chosen:
    model=chosen['model']; th=chosen['threshold']; col=model+'_p3'
    selected=trades[trades[col]>=th].sort_values(['date','entry_idx',col],ascending=[True,True,False]).drop_duplicates('date',keep='first')
    selected.to_csv(HERE/'selected_online_trades.csv',index=False)
disc.to_csv(HERE/'discrimination_by_period.csv',index=False)
metrics.to_csv(HERE/'causal_online_gate_56_results.csv',index=False)
summary=dict(candles=len(prices),strategy_candidates=len(trades),strategies=trades.strategy.nunique(),targetR=3,train='2025-01-01 through 2025-06-30',validation='2025-07-01 through 2025-12-31',evaluations=['2026Q1','2026Q2Q3_REUSED'],chosen_by_validation=chosen,noncausal_oracle_warning='No best-of-day selection after observing results',data_warning='Nine simplified proxy playbooks, not final audited ICT/custom implementations; OHLC bid + synthetic .35 friction',full_3R_win_required='50% full TP3 per trade; 50% only achieves +1R gross when all other outcomes exactly -1R',review_not_fresh=True)
(HERE/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
print('SUMMARY',summary)
print('DISCRIMINATION\n',disc.to_string(index=False,float_format=lambda v:f'{v:.3f}'))
print('SELECTED ROWS\n',metrics[(metrics.model==chosen.get('model')) & (metrics.threshold==chosen.get('threshold'))].to_string(index=False,float_format=lambda v:f'{v:.3f}'))