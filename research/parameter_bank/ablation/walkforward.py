#!/usr/bin/env python3
"""Four predeclared sequential train-before-test window comparisons, without test-window optimizing.
All windows previously inspected by analysts. This is backtest research, NOT a untouched live holdout.
"""
from pathlib import Path
import pandas as pd,numpy as np,json
H=Path(__file__).resolve().parent
A=pd.read_csv(H/'all_348_ablations.csv')
windows=['2025_H1','2025_H2','2026_Q1','2026_Q2_REUSED','2026_Q3_REUSED']
results=[]
for t in A.trigger.unique():
 for j in range(1,len(windows)):
  prior=windows[:j];future=windows[j]
  Q=A[A.trigger==t].copy()
  Q['n_prior']=sum(Q[f'{w}_n'] for w in prior)
  Q['total_prior']=sum(Q[f'{w}_total_R'] for w in prior)
  Q['avg_prior']=Q.total_prior/Q.n_prior.clip(lower=1)
  Q['mean_prior_coverage']=sum(Q[f'{w}_coverage_pct'] for w in prior)/len(prior)
  Q=Q[Q.n_prior>=70].copy()
  Q['fit']=Q.avg_prior-.5*np.sqrt(100/Q.n_prior)-.0005*(100-Q.mean_prior_coverage)
  c=Q.sort_values(['fit','n_prior','trigger','filter'],ascending=[False,False,True,True]).iloc[0]
  base=A[(A.trigger==t)&(A['filter']=='NONE')&(A.manager==c.manager)].iloc[0]
  results.append({'trigger':t,'train_windows':'+'.join(prior),'review_window_PREVIOUSLY_SEEN':future,'selected_filter':c['filter'],'selected_manager':c.manager,'prior_trades':int(c.n_prior),'prior_avg_R':float(c.avg_prior),'prior_fit_penalized':float(c.fit),
                  'forward_trades':int(c[f'{future}_n']),'forward_avg_R':float(c[f'{future}_avg_R']),'forward_total_R':float(c[f'{future}_total_R']),'forward_coverage_pct':float(c[f'{future}_coverage_pct']),
                  'baseline_no_filter_trades':int(base[f'{future}_n']),'baseline_avg_R':float(base[f'{future}_avg_R']),
                  'delta_per_trade_R_vs_baseline':float(c[f'{future}_avg_R']-base[f'{future}_avg_R'])})
B=pd.DataFrame(results)
B.to_csv(H/'rolling_16_train_before_test_folds.csv',index=False)
summary=B.groupby('trigger').agg(fold_count=('forward_avg_R','size'),test_total_trades=('forward_trades','sum'),test_total_R=('forward_total_R','sum'),mean_coverage_pct=('forward_coverage_pct','mean')).reset_index()
summary['weighted_avg_R']=summary.test_total_R/summary.test_total_trades
summary.to_csv(H/'rolling_trigger_summary.csv',index=False)
# Fixed, not-selected comparison: how often does same filter + manager remain >0 in FIVE market regimes
wincols=[f'{w}_avg_R' for w in windows]
A['regimes_positive']=A[wincols].gt(0).sum(axis=1)
A['both_train_review_positive']=(A.train_avg_R>0)&(A.review_REUSED_avg_R>0)
val=A[(A.train_n>=100)&(A.review_REUSED_n>=60)]
results={'tests':len(A),'both_train_and_reused_review_positive':int(val.both_train_review_positive.sum()),'all_five_regimes_positive':int((val.regimes_positive==5).sum()),'rolling_trigger_weighted_avg_R':dict(zip(summary.trigger,summary.weighted_avg_R)), 'rolling_all_total_R':float(summary.test_total_R.sum()),'rolling_all_n':int(summary.test_total_trades.sum()),'rolling_all_weighted_R':float(summary.test_total_R.sum()/summary.test_total_trades.sum())}
(H/'stability_summary.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print('STABILITY:',results)
print('ROLLING:\n',B[['trigger','review_window_PREVIOUSLY_SEEN','selected_filter','selected_manager','prior_avg_R','forward_trades','forward_avg_R','forward_coverage_pct']].to_string(index=False))