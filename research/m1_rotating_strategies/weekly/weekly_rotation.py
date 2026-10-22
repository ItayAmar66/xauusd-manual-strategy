#!/usr/bin/env python3
"""Weekly choose-next-week analysis on existing M1 playbook trade logs.
No look-ahead: a week W is chosen exclusively from completed previous ISO weeks.
Source: /mnt/data/m1_rotation_two_day/all_ten_strategy_trades.csv. GitHub Actions source path via relative fallback.
Use only complete ISO weeks (ignore partial data week at dataset beginning / end).
This is a shadow-signal hypothesis test, not validation of the 10 individual strategy concepts.
"""
from pathlib import Path
from itertools import product
import json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'m1_rotation_two_day'/'all_ten_strategy_trades.csv'
if not SOURCE.exists():
    SOURCE=HERE.parent/'two_day'/'all_ten_strategy_trades.csv'
if not SOURCE.exists():
    SOURCE=Path('/mnt/data/m1_rotation_two_day/all_ten_strategy_trades.csv')
assert SOURCE.exists(),SOURCE
out=HERE
raw=pd.read_csv(SOURCE)
assert {'strategy','net_R','reason','entry_idx','exit_idx','entry_israel_date','exit_israel_date','entry_israel'}.issubset(raw.columns)
raw['date']=pd.to_datetime(raw.entry_israel_date)
raw['week']=(raw['date']-pd.to_timedelta(raw['date'].dt.weekday,unit='D')).dt.strftime('%Y-%m-%d')
raw['hit3']=raw.reason.eq(1)&raw.gross_R.ge(2.9999)
raw['positive']=raw.net_R.gt(0)
raw=raw.sort_values(['entry_idx','strategy']).reset_index(drop=True)
assert not raw['net_R'].isna().any()
# each playbook was replayed with one position at a time; verify
for s,g in raw.groupby('strategy',sort=False):
    g=g.sort_values('entry_idx')
    if len(g)>1: assert (g.entry_idx.to_numpy()[1:]>g.exit_idx.to_numpy()[:-1]).all(),s

strategies=sorted(raw.strategy.unique())
assert len(strategies)==10,strategies
weeks=sorted(raw.week.unique())
# Last archived week is truncated at Thursday; first archived week begins midweek.
complete_weeks=[w for w in weeks if w >weeks[0] and w <weeks[-1]]
# For 8-week lookback common evaluation starts after first 8 full archived weeks.
evalweeks=complete_weeks[8:]
assert len(evalweeks)>70
market_dates=sorted(raw.entry_israel_date.unique()) # data has full-market signal coverage; market dates from baseline source
week_sets={w:raw[raw.week==w] for w in weeks}
by_week={w:{s:df for s,df in week_sets[w].groupby('strategy')} for w in weeks}

# Weekly signal outcome shadows: inactive models are still calculated from historical M1 tape.
weekly=raw.groupby(['week','strategy'],sort=False).agg(n=('net_R','size'),net_R=('net_R','sum'),avg_R=('net_R','mean'),TP3=('hit3','sum'),closed_positive=('positive','sum')).reset_index()
mi=pd.MultiIndex.from_product([weeks,strategies],names=['week','strategy'])
weekly=weekly.set_index(['week','strategy']).reindex(mi,fill_value=0).reset_index()
weekly['TP3_rate']=np.where(weekly.n>0,weekly.TP3/weekly.n,np.nan)
weekly.to_csv(out/'shadow_weekly_strategy_scoreboard.csv',index=False)

# A policy scores the last k FINISHED weeks, which must precede execution week.
allweeks=weeks
week_idx={w:i for i,w in enumerate(allweeks)}
week_stats=weekly.set_index(['week','strategy'])[['n','net_R','TP3','closed_positive']]
M=np.empty((len(allweeks),len(strategies),3),float)
for wi,w in enumerate(allweeks):
    for si,s in enumerate(strategies):
        x=week_stats.loc[(w,s)]
        M[wi,si]=[x.n,x.net_R,x.TP3]

# If a policy chooses no strategy, remain flat; no forced false-positive trades.
def ranks(w,k,metric,minn):
    end=week_idx[w]
    start=end-k
    if start<1: return []
    data=M[start:end,:,:]
    count=data[:,:,0].sum(axis=0)
    total=data[:,:,1].sum(axis=0)
    hits=data[:,:,2].sum(axis=0)
    if metric=='sum': score=total
    elif metric=='mean': score=total/np.maximum(count,1)
    elif metric=='shrink12': score=total/(count+12)
    elif metric=='tpshrink': score=(hits+1)/(count+2)
    elif metric=='recent':
        wts=(0.65**np.arange(k-1,-1,-1))[:,None]
        score=(data[:,:,1]*wts).sum(axis=0)/(12+(data[:,:,0]*wts).sum(axis=0))
    else: raise ValueError(metric)
    return sorted([(strategies[i],float(score[i]),int(count[i]),float(total[i])) for i in range(len(strategies)) if count[i]>=minn],key=lambda x:(-x[1],x[0]))

# trade-level replay chooses only previously selected model(s); trades compete for single position.
# Stop-first and fees already encoded in source results.
def replay_policy(selection):
    chunks=[]
    for w,picked in selection.items():
        if not picked: continue
        candidates=week_sets.get(w)
        if candidates is None or len(candidates)==0:continue
        z=candidates[candidates.strategy.isin(picked)].copy()
        if len(z)==0:continue
        z['rank']=z.strategy.map({s:i for i,s in enumerate(picked)})
        chunks.append(z)
    if not chunks:return raw.iloc[:0].copy()
    cand=pd.concat(chunks,ignore_index=True).sort_values(['entry_idx','rank','strategy'])
    # For top2, avoid double-fills: only one active trade; equal-timestamp priorities by ranking.
    chosen=[]; locked=-1
    # Use contiguous numpy arrays for millions of replay checks; iterrows is prohibitively slow.
    for ii,(ent,ext) in enumerate(zip(cand.entry_idx.to_numpy(),cand.exit_idx.to_numpy())):
        if ent<=locked:continue
        chosen.append(ii);locked=int(ext)
    return cand.iloc[chosen].drop(columns=['rank']).reset_index(drop=True)

# Generate choices, with optionally held incumbent if score difference <= inertia.
def choices(k,metric,minn,inertia,top):
    picked={};evidence=[];incumbent=None
    for w in evalweeks:
        rr=ranks(w,k,metric,minn)
        selected=[]
        if rr:
            selected=[x[0] for x in rr[:top]]
            if incumbent in [x[0] for x in rr] and incumbent!=selected[0]:
                # Keep incumbent if new leader doesn't outperform it by a meaningful margin in score units.
                sr={x[0]:x[1] for x in rr}
                if sr[selected[0]]-sr[incumbent]<=inertia:
                    selected=[incumbent]+[x[0] for x in selected if x[0]!=incumbent]
                    selected=selected[:top]
            incumbent=selected[0]
        else: incumbent=None
        picked[w]=selected
        evidence.append({'execution_week':w,'past_weeks':k,'metric':metric,'min_trades':minn,'inertia':inertia,'n_strategies':top,'selection':'+'.join(selected),'prior_week':allweeks[week_idx[w]-1],
                         'prior_window_start':allweeks[week_idx[w]-k],'leader_score':rr[0][1] if rr else np.nan,
                         'leader_trades':rr[0][2] if rr else 0,'leader_history_R':rr[0][3] if rr else 0,'incumbent_next':incumbent or ''})
    return picked,pd.DataFrame(evidence)

# Session metrics over identical weeks; evaluate coverage only on dates with qualifying original market data.
base_dates=[d for d in market_dates if (pd.Timestamp(d)-pd.Timedelta(days=pd.Timestamp(d).weekday())).strftime('%Y-%m-%d') in evalweeks]
def stats(z,mode):
    # Periods are cut by actual Israel-local entry date, not Monday ISO year.
    # Otherwise a year-boundary week leaks Jan 2026 results into 2025 fit.
    if mode=='2025': lo,hi='2025-01-01','2025-12-31'
    elif mode=='2026Q1': lo,hi='2026-01-01','2026-03-31'
    elif mode=='2026Q2Q3': lo,hi='2026-04-01','2026-09-20'
    elif mode=='all': lo,hi='1900-01-01','2100-01-01'
    else:raise ValueError(mode)
    z=z[(z.entry_israel_date>=lo)&(z.entry_israel_date<=hi)]
    eligible=[d for d in base_dates if lo<=d<=hi]
    ret=z.net_R.to_numpy(float)
    if len(ret):
        eq=np.r_[0,ret.cumsum()];dd=float(np.min(eq-np.maximum.accumulate(eq)))
        st=0;worst=0
        for x in ret:
            st=st+1 if x<=0 else 0;worst=max(st,worst)
        wr=float(z.hit3.mean()*100)
    else: dd=0.;worst=0;wr=np.nan
    return dict(n=len(z),total_R=float(ret.sum()),mean_R=float(ret.mean()) if len(ret) else np.nan,hit_3R_pct=wr,positive_pct=float(z.positive.mean()*100) if len(ret) else np.nan,days_with_trade=int(z.entry_israel_date.nunique()),eligible_days=len(eligible),coverage_pct=100*z.entry_israel_date.nunique()/max(len(eligible),1),max_DD_R=dd,losing_streak=worst)

# All chronological benchmark trades with no overlaps, and ten static models evaluated over same period.
baseline_raw=raw[raw.week.isin(evalweeks)].copy()
benchmarks={}
for s in strategies:
    z=baseline_raw[baseline_raw.strategy==s].copy()
    benchmarks['STATIC_'+s]=z
# 'ALL' enters whichever available strategy fired first, with deterministic tie-break; no model conditioning.
allcand=baseline_raw.sort_values(['entry_idx','strategy'])
selected=[];locked=-1
for i,row in allcand.iterrows():
    if row.entry_idx<=locked:continue
    selected.append(i);locked=row.exit_idx
benchmarks['ALL_10_FIRST_SIGNAL']=allcand.loc[selected].copy()

rows=[];best_train=None;bestscore=-np.inf;best_picks=None;best_evidence=None;best_trades=None
for name,z in benchmarks.items():
    for period in ['2025','2026Q1','2026Q2Q3','all']:
        rows.append(dict(policy=name,past_weeks=0,metric='static',min_trades=0,inertia=0,top=1,period=period,**stats(z,period)))

policies=list(product([1,2,3,4,8],['sum','mean','shrink12','tpshrink','recent'],[1,4,12],[0.0,0.15],[1,2]))
assert len(policies)==300
for k,metric,minn,inertia,top in policies:
    selections,ev=choices(k,metric,minn,inertia,top)
    trades=replay_policy(selections)
    recs={per:stats(trades,per) for per in ['2025','2026Q1','2026Q2Q3','all']}
    name=f'ROT_{k}W_{metric}_min{minn}_h{inertia}_top{top}'
    for period,v in recs.items():rows.append(dict(policy=name,past_weeks=k,metric=metric,min_trades=minn,inertia=inertia,top=top,period=period,**v))
    dev=recs['2025']
    # select only by 2025, with minimum transaction frequency; no use of outcomes from 2026
    fit=(dev['mean_R'] if np.isfinite(dev['mean_R']) else -99) - 0.2*np.sqrt(250/max(dev['n'],1))
    if dev['n']<120:fit=-1000
    if fit>bestscore:
        bestscore=fit;best_train=name;best_picks=selections;best_evidence=ev;best_trades=trades

results=pd.DataFrame(rows)
results.to_csv(out/'all_300_weekly_rotation_policy_scores.csv',index=False)
assert best_train
best_evidence.to_csv(out/'train_selected_weekly_switch_decisions.csv',index=False)
best_trades.to_csv(out/'train_selected_rotation_trade_log.csv',index=False)

# Explicit user proposal: previous full week with max net R, keep winner if same; switch when leader changes, top1.
exact_picks,exact_evidence=choices(1,'sum',1,0.0,1)
exact_evidence.to_csv(out/'exact_user_rule_weekly_switches.csv',index=False)
exact_trades=replay_policy(exact_picks)
exact_trades.to_csv(out/'exact_user_rule_trades.csv',index=False)

# Comparison controls: past week best 3R hit rate with enough trades and 4-week shrunk returns, and top2 rotation.
controls=[('EXACT_PREVIOUS_WEEK_WINNER',exact_picks,exact_trades),('TRAIN_SELECTED',best_picks,best_trades)]
for label,args in [('W1_HIT3', (1,'tpshrink',4,0,1)),('W4_SHRUNK', (4,'shrink12',4,0,1)),('W4_SHRUNK_TOP2',(4,'shrink12',4,0,2)),('W8_SHRUNK',(8,'shrink12',4,0,1))]:
    ch,ev=choices(*args);z=replay_policy(ch)
    ev.to_csv(out/(label+'_decisions.csv'),index=False)
    controls.append((label,ch,z))

summary_rows=[]
for label,ch,z in controls:
    switches=sum(int(ch[w][0]!=ch[evalweeks[i-1]][0]) for i,w in enumerate(evalweeks) if i and ch[w] and ch[evalweeks[i-1]])
    selected={w:(ch[w][0] if ch[w] else '') for w in evalweeks}
    switched_den=sum(int(bool(ch[w]) and bool(ch[evalweeks[i-1]])) for i,w in enumerate(evalweeks) if i)
    for p in ['2025','2026Q1','2026Q2Q3','all']:
        summary_rows.append(dict(policy=label,period=p,switches_total=switches,comparable_week_transitions=switched_den,**stats(z,p)))
for name in ['ALL_10_FIRST_SIGNAL']+['STATIC_'+x for x in strategies]:
    for p in ['2025','2026Q1','2026Q2Q3','all']:
        summary_rows.append(dict(policy=name,period=p,switches_total=0,comparable_week_transitions=0,**stats(benchmarks[name],p)))
pd.DataFrame(summary_rows).to_csv(out/'weekly_rotation_comparison.csv',index=False)

# Diagnostic ONLY, impossible forward strategy: chance past week's top winner is next week's winner.
diagnostic=[]
for i,w in enumerate(evalweeks):
    pre=ranks(w,1,'sum',1)
    future=M[week_idx[w],:,:]
    best_actual=strategies[int(np.argmax(future[:,1]))]
    past=pre[0][0] if pre else ''
    diagnostic.append(dict(week=w,past_winner=past,future_winner_NOT_TRADEABLE=best_actual,is_same=past==best_actual,pre_topR=pre[0][3] if pre else np.nan,next_R_of_past_winner=float(future[strategies.index(past),1]) if past else np.nan,actual_best_nextR=float(np.max(future[:,1]))))
pd.DataFrame(diagnostic).to_csv(out/'week_to_next_week_winner_persistence.csv',index=False)

# Weekly paired returns of selected and controls. Weeks resampling to estimate uncertainty.
all_w={}
for label,ch,z in controls:
    all_w[label]=z.groupby('week').net_R.sum().reindex(evalweeks,fill_value=0).to_numpy()
all_w['ALL_10_FIRST_SIGNAL']=benchmarks['ALL_10_FIRST_SIGNAL'].groupby('week').net_R.sum().reindex(evalweeks,fill_value=0).to_numpy()
# Fixed benchmark is best total R in 2025 among >=150 historical trades, chosen without 2026.
# It may pick the incompatible archived model. Interpret with caution, and use separate 8-model sensitivity.
staticdev={s:stats(benchmarks['STATIC_'+s],'2025')['total_R'] for s in strategies}
fixed_s=max((s for s in strategies if stats(benchmarks['STATIC_'+s],'2025')['n']>=150), key=lambda s:staticdev[s])
all_w['STATIC_TRAIN_BEST']=benchmarks['STATIC_'+fixed_s].groupby('week').net_R.sum().reindex(evalweeks,fill_value=0).to_numpy()
paired=[];rng=np.random.default_rng(20261022)
for label in ['EXACT_PREVIOUS_WEEK_WINNER','TRAIN_SELECTED','W4_SHRUNK','W4_SHRUNK_TOP2','W8_SHRUNK']:
  for segment,a,b in [('2025','2025-01-01','2025-12-31'),('2026Q1','2026-01-01','2026-04-05'),('2026Q2Q3','2026-04-06','2026-09-20')]:
    ix=np.array([a<=w<=b for w in evalweeks]); wk=np.array(evalweeks)[ix]; n=ix.sum()
    for benchmark in ['STATIC_TRAIN_BEST','ALL_10_FIRST_SIGNAL']:
        delta=(all_w[label]-all_w[benchmark])[ix]
        if n:
            samples=delta[rng.integers(0,n,size=(3000,n))].sum(axis=1)
            low,high=np.quantile(samples,[.025,.975])
        else:low=high=np.nan
        paired.append(dict(policy=label,period=segment,baseline=benchmark,n_weeks=int(n),sum_extra_R=float(delta.sum()),extra_R_per_week=float(delta.mean()) if n else np.nan,bootstrap95_extra_R_total_low=float(low),bootstrap95_extra_R_total_high=float(high)))
pd.DataFrame(paired).to_csv(out/'bootstrap_weekly_paired_comparison.csv',index=False)


# Robustness: independently exclude archival original payoff and the near-empty Unicorn implementation.
# This avoids mechanically preferring incomparable or four-trade weekly configurations.
excluded={s for s in strategies if s.startswith('01_') or s.startswith('04_')}
robust_names=[s for s in strategies if s not in excluded]
robust_rows=[]
for k,metric,minn,top in [(1,'sum',1,1),(1,'shrink12',4,1),(4,'shrink12',4,1),(8,'shrink12',4,1),(8,'shrink12',4,2)]:
    ch={}; ev=[]
    for w in evalweeks:
        r=[x for x in ranks(w,k,metric,minn) if x[0] in robust_names]
        ch[w]=[x[0] for x in r[:top]]
        ev.append({'execution_week':w,'selection':'+'.join(ch[w]),'last_observed_week':allweeks[week_idx[w]-1]})
    z=replay_policy(ch)
    name=f'EXCLUDE_ARCHIVE_UNICORN_{k}W_{metric}_min{minn}_top{top}'
    pd.DataFrame(ev).to_csv(out/(name+'_decisions.csv'),index=False)
    for period in ['2025','2026Q1','2026Q2Q3','all']:
        robust_rows.append(dict(policy=name,period=period,**stats(z,period)))
pd.DataFrame(robust_rows).to_csv(out/'exclude_archive_and_rare_sensitivity.csv',index=False)


# Previous user target is 50% full 3R TP hits over historical window.
# Check it as a separate gate, without assuming a positive day implies full TP.
strict_rows=[]
for k,minn,empty_rule in product([1,2,4,8],[1,4],['cash','keep']):
    history={};last=[];picked=None
    for w in evalweeks:
        widx=week_idx[w];hist=M[widx-k:widx,:,:]
        n=hist[:,:,0].sum(axis=0);total=hist[:,:,1].sum(axis=0);hit=hist[:,:,2].sum(axis=0)
        eligible=np.flatnonzero((n>=minn)&(total>0)&(hit/np.maximum(n,1)>=0.5))
        if len(eligible):
            rank=sorted(eligible,key=lambda i:(-total[i],strategies[i]))
            choice=[strategies[rank[0]]];picked=choice[0]
        elif empty_rule=='keep' and picked is not None: choice=[picked]
        else:choice=[];picked=None
        history[w]=choice
        last.append(dict(execution_week=w,observed_from=allweeks[widx-k],observed_until=allweeks[widx-1],selected=choice[0] if choice else '',eligible_count=len(eligible)))
    label=f'TP3_50PCT_GATE_{k}W_min{minn}_{empty_rule}'
    if k in [1,4] and minn==4:
        pd.DataFrame(last).to_csv(out/(label+'_decisions.csv'),index=False)
    z=replay_policy(history)
    for period in ['2025','2026Q1','2026Q2Q3','all']:
        strict_rows.append(dict(policy=label,period=period,**stats(z,period)))
pd.DataFrame(strict_rows).to_csv(out/'strict_50pct_3R_weekly_gate.csv',index=False)

# Inactive-model audit: compare past-vs-future winner only among the eight non-archival, non-sparse strategy proxies.
spec=[];robidx=[strategies.index(s) for s in robust_names]
for w in evalweeks:
    prev=ranks(w,1,'sum',1)
    best_past=next((x[0] for x in prev if x[0] in robust_names),'')
    f=M[week_idx[w],:,:]
    active=[i for i in robidx if f[i,0]>0]
    next_best=strategies[max(active,key=lambda i:f[i,1])] if active else ''
    spec.append(dict(week=w,past_8model_leader=best_past,next_week_8model_leader=next_best,repeat=best_past==next_best))
pd.DataFrame(spec).to_csv(out/'eight_model_winner_persistence.csv',index=False)

# Static ranking by full 2025 performance with no 2026 in selection, compare winner's fate later.
fix=pd.DataFrame([dict(strategy=s,train_2025_R=staticdev[s],train_trades=stats(benchmarks['STATIC_'+s],'2025')['n'],review_Q1_R=stats(benchmarks['STATIC_'+s],'2026Q1')['total_R'],review_Q2Q3_R=stats(benchmarks['STATIC_'+s],'2026Q2Q3')['total_R']) for s in strategies]).sort_values('train_2025_R',ascending=False)
fix.to_csv(out/'fixed_strategy_2025_rank.csv',index=False)

main=results[results.period=='2025'].sort_values('total_R',ascending=False)
summary=dict(source_rows=len(raw),models=len(strategies),source_warning='Original archive model and nine simplified proxies NOT independently validated against full discretionary ICT rules',full_data_first_week=weeks[0],full_data_last_week=weeks[-1],evaluation_week_count=len(evalweeks),evaluation_first=evalweeks[0],evaluation_last=evalweeks[-1],scanned_policies=len(policies),train_selected_policy=best_train,selection_criterion='2025 mean R minus 0.2 sqrt(250/n), n>=120; 2026 never used in selection',fixed_2025_total_R_winner=fixed_s,exact_switches=int(sum((exact_picks[evalweeks[i]]!=exact_picks[evalweeks[i-1]]) for i in range(1,len(evalweeks)))),no_model_reconstruction='Uses prior backtest trade logs as shadow trading; cannot validate actual execution/strategy correctness',caveats=['2026 reviewed repeatedly; no fresh OOS','per-trade bid OHLC approximated friction','source 01 is archival different payoff and requires correction','weekly selection assumes simulated outcome of all inactive strategies is observed','avoid live deployment from this experiment'])
(out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
print(json.dumps(summary,indent=2))
print(pd.read_csv(out/'weekly_rotation_comparison.csv').query('period=="2026Q2Q3"').to_string(index=False))
print('PERSISTENCE',pd.read_csv(out/'week_to_next_week_winner_persistence.csv').is_same.mean())