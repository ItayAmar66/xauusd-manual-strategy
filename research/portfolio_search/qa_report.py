"""QA and cost sensitivity for train-selected XAUUSD portfolio (not a live recommendation)."""
from pathlib import Path
import pandas as pd,numpy as np,json
P=Path(__file__).resolve().parent
ROOT=P.parent
B=pd.read_csv(ROOT/'parameter_bank'/'condition_bank_m5.csv',usecols=['entry_m1_index','m5_atr14'])
idx_to_atr=dict(zip(B.entry_m1_index,B.m5_atr14))
all_data=[];summary={}
for variant in ['portfolio_without_fallback','portfolio_with_daily_fallback']:
 df=pd.read_csv(P/f'{variant}_trade_log.csv')
 assert (df.exit_m1_index>=df.entry_m1_index).all()
 assert (df.entry_m1_index.iloc[1:].to_numpy()>df.exit_m1_index.iloc[:-1].to_numpy()).all(), 'overlap detected'
 assert (df.entry_israel.str[11:16]>='06:00').all() and (df.entry_israel.str[11:16]<'20:00').all()
 df['risk_price']=df.entry_m1_index.map(idx_to_atr)*df.risk_atr_multiple
 assert df.risk_price.min()>=0.7-1e-7
 for fee in [0.35,0.7,1.0]:df[f'netR_fee_{str(fee).replace(".","_")}']=df.net_R-(fee-.35)/df.risk_price
 df['period']=np.select([df.date_israel<'2026-01-01',df.date_israel<'2026-04-01',df.date_israel>='2026-04-01'],['2025_dev','2026Q1_validation','2026Q2Q3_reused'],default='unknown')
 df['iso_week']=pd.to_datetime(df.date_israel).dt.strftime('%G-W%V')
 df['month']=df.date_israel.str[:7]
 # deterministic block bootstrap by week of entry to handle trade clustering
 rng=np.random.default_rng(811)
 for era,d in df.groupby('period',sort=True):
  groups=[g.net_R.to_numpy() for _,g in d.groupby('iso_week')]
  total=np.array([a.sum() for a in groups]);counts=np.array([len(a) for a in groups]);arr=[]
  for i in range(5000):
   sampled=rng.integers(0,len(groups),size=len(groups));arr.append(total[sampled].sum()/counts[sampled].sum())
  outcomes=d.net_R.to_numpy();eq=np.r_[0,np.cumsum(outcomes)]
  last=0;longest=0
  for v in outcomes:
   last=last+1 if v<=0 else 0;longest=max(longest,last)
  info=dict(variant=variant,period=era,n=len(d),mean_R=float(outcomes.mean()),total_R=float(outcomes.sum()),winrate_pct=float(100*(outcomes>0).mean()),tp8_pct=float(100*(d.exit_reason_code==1).mean()),max_drawdown_R=float(np.min(eq-np.maximum.accumulate(eq))),longest_loss_streak=longest,min_stop_price=float(d.risk_price.min()),median_stop_price=float(d.risk_price.median()),mean_R_fee07=float(d.netR_fee_0_7.mean()),mean_R_fee10=float(d.netR_fee_1_0.mean()),bootstrap_week_95_low_R=float(np.quantile(arr,.025)),bootstrap_week_95_high_R=float(np.quantile(arr,.975)),weeks=len(groups),days_traded=d.date_israel.nunique())
  all_data.append(info)
 df[['strategy','entry_utc','entry_israel','date_israel','direction','entry_price','net_R','risk_price','netR_fee_0_7','netR_fee_1_0','exit_reason_code','entry_m1_index','exit_m1_index','period']].to_csv(P/f'{variant}_stressed_trade_log.csv',index=False)
 df.groupby(['period','month'],as_index=False).agg(n=('net_R','size'),net_R=('net_R','sum'),avg_R=('net_R','mean'),days=('date_israel','nunique')).to_csv(P/f'{variant}_monthly_results.csv',index=False)
 info=df.groupby(['period','strategy'],as_index=False).agg(n=('net_R','size'),net_R=('net_R','sum'),avg_R=('net_R','mean'),days=('date_israel','nunique'))
 info['variant']=variant
 info.to_csv(P/f'{variant}_components.csv',index=False)
qa=pd.DataFrame(all_data);qa.to_csv(P/'QA_cost_stress_bootstrap.csv',index=False)
(P/'QA_summary.json').write_text(json.dumps({'period_stress_qa':all_data},indent=2),encoding='utf8')
print(qa.to_string(index=False))