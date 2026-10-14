#!/usr/bin/env python3
"""Produce strategy-specific Hebrew methodology and comprehensive results; based only on completed backtests."""
from pathlib import Path
import pandas as pd, numpy as np, json
P=Path(__file__).resolve().parent
s=pd.read_csv(P/'selected_26_strategies.csv');v=pd.read_csv(P/'all_1170_variants.csv');t=pd.read_csv(P/'all_selected_trades.csv')
meta=json.loads((P/'summary.json').read_text())
D=P/'strategies';D.mkdir(exist_ok=True)
DESC={
'01':('EMA 9/21 Cross','LONG כאשר EMA9 חוצה מלמטה למעלה את EMA21; SHORT כאשר היא חוצה מלמעלה למטה. נר M5 סגור בלבד.'),
'02':('EMA 20/50 Cross','LONG כאשר EMA20 חוצה כלפי מעלה EMA50; SHORT בחצייה מטה.'),
'03':('EMA20 Pullback','במגמת EMA20 מעל EMA50: נגיעה ב-EMA20 ונר שורי שסוגר חזרה מעליו; SELL סימטרי במגמה יורדת.'),
'04':('EMA50 Pullback','מגמת EMA20 מעל EMA50, חזרה ל-EMA50 וסגירה שורית מעליו; SHORT סימטרי. סגירת M5.'),
'05':('Donchian 12 Breakout','סגירת M5 מעל שיא 12 הנרות הקודמים (LONG), או מתחת לשפל שלהם (SHORT), לראשונה.'),
'06':('Donchian 36 Breakout','פריצת סגירה של טווח 36 נרות M5 קודמים, בכיוון הפריצה.'),
'07':('Donchian12 Sweep Fade','Sweep של שפל 12 נרות עם חזרה וסגירה שורית מעל השפל (LONG); Sweep של השיא עם חזרה וסגירה דובית (SHORT).'),
'08':('Donchian36 Sweep Fade','כמו Sweep Fade, מול טווח 36 הנרות הקודמים.'),
'09':('Previous Day Breakout','סגירת M5 מעל שיא יום ישראל קודם (LONG) או מתחת לשפל יום קודם (SHORT).'),
'10':('Previous Day Sweep Fade','חדירה לשפל יום קודם ואז סגירה מעליו ונר שורי (LONG); סימטרי לשיא יום קודם.'),
'11':('Asia Box Breakout','טווח 00:00–05:59 ישראל; אות 06:00–12:00 כאשר M5 סוגר בפריצה ראשונה מעבר לשיא/שפל האסייתי.'),
'12':('Asia Box Sweep Fade','בטווח 06:00–12:00: חדירה מעבר לגבול טווח 00–06 וחזרה בסגירת M5 פנימה.'),
'13':('RSI 30/70 Reclaim','LONG בחצייה של RSI14 בחזרה מעל 30; SHORT בחצייה חזרה מתחת 70.'),
'14':('RSI 20/80 Reclaim','LONG ב-RSI14 שעולה חזרה מעל 20; SHORT בירידה חזרה מתחת 80.'),
'15':('RSI50 + EMA Trend','RSI14 חוצה מעל 50 והסגירה מעל EMA50 (LONG); מתחת 50 ומתחת EMA50 (SHORT).'),
'16':('Bollinger Band Reentry','חזרה בסגירה לתוך Bollinger(20,2) לאחר סגירה מחוץ לרצועה התחתונה/עליונה.'),
'17':('Bollinger Band Breakout','סגירה ראשונה מחוץ לרצועת Bollinger(20,2) עליונה (LONG) או תחתונה (SHORT).'),
'18':('ATR Displacement + Trend','גוף נר M5 גדול מ-1.5×ATR14 בכיוון של EMA20 לעומת EMA50; כניסה עם תנועת הגוף.'),
'19':('Inside Bar Breakout','לאחר נר Inside ב-M5: נר הבא סוגר מעבר לגבולות נר ה-Inside.'),
'20':('Engulf at 20-Bar Extreme','נר Bullish/Bearish Engulfing אשר באותו נר חודר את הקיצון של 20 נרות קודמים.'),
'21':('MACD Signal Cross','MACD(12,26,9) חוצה Signal בכיוון הסגירה, ובנוסף המחיר בצד המתאים של EMA50.'),
'22':('M5 FVG Return','FVG של 3 נרות M5; מחיר נוגע בתחום ה-FVG האחרון הקודם וסוגר מעבר לשפתו בכיוון ה-FVG.'),
'23':('M15 FVG Return','FVG של 3 נרות M15 שכבר נסגרו; מחיר M5 חוזר לאזור ומבצע סגירה בכיוון ה-FVG.'),
'24':('Daily 06:10 Trend','איתות סגור ב-06:05 ישראל; LONG אם המחיר מעל סגירת M5 לפני 12 נרות, אחרת SHORT. כניסה ב-06:10.'),
'25':('06–07 Opening Range Break','טווח השעה 06:00–06:59 ישראל; אות בין 07:00 ל-12:00 בפריצה ראשונה בסגירת M5.'),
'26':('RSI Extreme Exhaustion','שינוי כיוון RSI14 לאחר ירידה מתחת 25 בשפל 12 נרות (LONG); הפוך לאחר מעל 75 בשיא 12 נרות (SHORT).')}
MGR={
'fixed3':'SL קבוע, TP=3R; ללא קידום סטופ.',
'fixed4':'SL קבוע, TP=4R; ללא קידום סטופ.',
'fixed5':'SL קבוע, TP=5R; ללא קידום סטופ.',
'fixed8':'SL קבוע, TP=8R; ללא קידום סטופ.',
'be1p5_tp4':'יעד 4R; כאשר במהלך נר M1 הושגה תנועה חיובית של 1.5R, מעבירים SL למחיר הכניסה החל מהנר הבא.',
'be2_tp5':'יעד 5R; כאשר הושגה תנועה חיובית 2R, SL לכניסה מהנר הבא.',
'be2_tp8':'יעד 8R; כאשר הושגה תנועה חיובית 2R, SL לכניסה מהנר הבא.',
'ladder1_tp5':'יעד 5R; מעל 1R תנועה חיובית מעדכנים סטופ פעם בכל 1R נוסף: ב-2R סטופ 1R, ב-3R סטופ 2R וכו׳, רק מהנר הבא.',
'ladder0p5_tp4':'יעד 4R; מעל 1R תנועה חיובית, כל עליה נוספת של 0.5R מקדמת סטופ 0.5R; מהנר הבא בלבד.'}

def fmt(x,precision=3):
 if pd.isna(x):return '—'
 if np.isinf(x):return '∞'
 return f'{x:,.{precision}f}'

def boot_ci(trades,days,seed):
 rng=np.random.default_rng(seed)
 if len(trades)==0:return (np.nan,np.nan)
 # bootstrap independent trading days including dates without trades
 tdate=pd.to_datetime(trades.entry_il,utc=True).dt.tz_convert('Asia/Jerusalem').dt.date.astype(str)
 sums=trades.assign(day=tdate).groupby('day').net_R.agg(['sum','count'])
 d=np.array(days,dtype=str)
 allsum=sums['sum'].reindex(d,fill_value=0).to_numpy();allcount=sums['count'].reindex(d,fill_value=0).to_numpy()
 samples=rng.integers(0,len(d),size=(1000,len(d)))
 num=allsum[samples].sum(axis=1);den=allcount[samples].sum(axis=1)
 means=np.divide(num,den,out=np.full(len(num),np.nan),where=den>0)
 return np.nanpercentile(means,[2.5,97.5])

xdates=pd.read_csv(P/'../5M ATR/daily_coverage.csv') if False else None
# Calendar dates from trade file cannot infer no-trade days; in the source script eligibility sets 446 weekdays.
# CI uses all calendar weekdays in holdout then discards missing market dates by referencing valid original M1 feed.
from zipfile import ZipFile
zipfile=P.parent/'15M ATR'/'XAUUSD_Manual_Strategy_Research_Git_Import.zip'
if zipfile.exists():
 with ZipFile(zipfile) as z:
  f=next(x for x in z.namelist() if x.endswith('/xauusd-m1-bid-2025-01-01-2026-09-25.csv'))
  candles=pd.read_csv(z.open(f),usecols=['timestamp','high','low'])
 tms=pd.to_datetime(candles.timestamp,unit='ms',utc=True).dt.tz_convert('Asia/Jerusalem')
 candles['date']=tms.dt.date
 da=candles.groupby('date').agg(n=('high','size'),hi=('high','max'),lo=('low','min'))
 days=[str(d) for d in da[(da.n>=200)&(da.hi>da.lo)].index if pd.Timestamp(d).weekday()<5]
else:
 candles=pd.read_csv('/mnt/data/xauusd-m1-bid-2025-01-01-2026-09-25.csv',usecols=['timestamp','high','low'])
 tms=pd.to_datetime(candles.timestamp,unit='ms',utc=True).dt.tz_convert('Asia/Jerusalem')
 candles['date']=tms.dt.date
 da=candles.groupby('date').agg(n=('high','size'),hi=('high','max'),lo=('low','min'))
 days=[str(d) for d in da[(da.n>=200)&(da.hi>da.lo)].index if pd.Timestamp(d).weekday()<5]
hodays=[d for d in days if d>='2026-04-01']
assert len(hodays)==126

ci=[]
for i,r in s.iterrows():
 name=r.strategy;sample=t[(t.strategy==name)&(t.split=='holdout')].copy()
 assert len(sample)==r.holdout_n
 ci_low,ci_high=boot_ci(sample,hodays,42+i)
 stress=float(sample.net_R_stress_fee07.mean())
 full=t[t.strategy==name]
 reasons=sample.exit_reason.value_counts().to_dict()
 exceptions=int((sample.duration_minutes>120).sum())
 extra={'strategy':name,'holdout_over120m_exceptions':exceptions, 'holdout_avg_R_excluding_over120m':float(sample.loc[sample.duration_minutes<=120,'net_R'].mean()),'holdout_boot_CI_low':ci_low,'holdout_boot_CI_high':ci_high,'holdout_avg_R_cost07':stress,'holdout_target_exit_pct':100*reasons.get('target',0)/len(sample),'holdout_stop_exit_pct':100*reasons.get('stop',0)/len(sample),'holdout_time_exit_pct':100*reasons.get('time',0)/len(sample),'holdout_gap_exit_pct':100*reasons.get('feed_gap',0)/len(sample),'holdout_median_risk_price':float(sample.initial_risk_price.median()),'holdout_max_risk_price':float(sample.initial_risk_price.max()),'holdout_days_no_trades':126-r.holdout_days_with_trade}
 ci.append(extra)
 title,definition=DESC[name[:2]]
 sample_file=name+'.md'
 md=f'''# {name}: {title}

## הגדרת כניסה — מוכרת בזמן אמת בלבד

{definition}

כל האינדיקטורים מחושבים על נרות **M5 סגורים**. הכניסה מתבצעת במחיר OPEN של דקת M1 הבאה. חלון הכניסות: **06:00–19:59 שעון Asia/Jerusalem (שעון קיץ/חורף אוטומטי)**. בדיקת אסטרטגיה היא על כלל השוק, **בלי לבחור רק מהלכים מנצחים של 4ATR**. אותות סותרים באותו נר מבוטלים.

## ניהול העסקה שנבחר בתקופת הפיתוח בלבד

- **SL התחלתי:** {fmt(r.stop_atr,2)} × ATR(14) מחושב מנרות M5. מחיר סטופ LONG = מחיר כניסה פחות המרחק; SHORT = מחיר כניסה ועוד המרחק.
- **TP:** {int(r.target_R)}R לפי מרחק הסטופ ההתחלתי.
- **ניהול שנבחר:** `{r.manager}` — {MGR[r.manager]}
- **הגבלת זמן:** 120 דקות מהכניסה. אם אין נגיעה ביעד או בסטופ, היציאה במחיר הפתיחה של דקת הסיום הראשונה.
- **בר עם SL וגם TP:** קודם SL, הנחה מחמירה. כל שינוי סטופ נכנס לתוקף רק *בדקה הבאה*.
- **מחיר וביצוע:** M1 OHLC bid היסטורי, ללא נתוני tick ועומק שוק. עלות בסיס קבועה של $0.35 במחיר XAUUSD לעסקה שלמה; בדיקת רגישות $0.70. שני המספרים הנחות, לא עלויות ברוקר מאומתות.

## תוצאות — פיתוח 2025-01 עד 2026-03 / בדיקה 2026-04 עד 2026-09

| מדד | פיתוח (Train) | בדיקה שלא שימשה לבחירה (Holdout) |
|---|---:|---:|
| עסקאות | {int(r.train_n):,} | {int(r.holdout_n):,} |
| ממוצע R נטו לעסקה | {fmt(r.train_avg_R)} | **{fmt(r.holdout_avg_R)}** |
| סכום R נטו | {fmt(r.train_total_R,2)} | {fmt(r.holdout_total_R,2)} |
| Win rate כולל עלויות | {fmt(r.train_win_rate_pct,2)}% | {fmt(r.holdout_win_rate_pct,2)}% |
| Profit factor | {fmt(r.train_profit_factor,3)} | {fmt(r.holdout_profit_factor,3)} |
| Maximum Drawdown ב-R | {fmt(r.train_max_drawdown_R,2)} | {fmt(r.holdout_max_drawdown_R,2)} |
| ימים עם לפחות עסקה אחת | {int(r.train_days_with_trade)}/320 | {int(r.holdout_days_with_trade)}/126 |
| כיסוי ימי מסחר | {fmt(r.train_coverage_pct,2)}% | {fmt(r.holdout_coverage_pct,2)}% |
| רצף ימי מסחר ללא כניסה | {int(r.train_max_consecutive_no_trade_days)} | {int(r.holdout_max_consecutive_no_trade_days)} |
| רצף הפסדים מקסימלי | {int(r.train_loss_streak)} | {int(r.holdout_loss_streak)} |
| חציון זמן החזקה (דק׳) | {fmt(r.train_median_hold_minutes,1)} | {fmt(r.holdout_median_hold_minutes,1)} |

**רווחיות בבדיקת Holdout אחרי עלות $0.70:** {fmt(stress)}R בממוצע לעסקה. **95% CI bootstrap לפי ימי מסחר:** [{fmt(ci_low)}, {fmt(ci_high)}] R (הנחת דגימת ימים בלתי תלויים; אינה מבטיחה רווח עתידי).

**סיבת יציאה ב-Holdout:** יעד {fmt(extra['holdout_target_exit_pct'],1)}%; סטופ {fmt(extra['holdout_stop_exit_pct'],1)}%; זמן {fmt(extra['holdout_time_exit_pct'],1)}%; פער בנתונים {fmt(extra['holdout_gap_exit_pct'],1)}%.

**מרחק SL חציוני:** ${fmt(extra['holdout_median_risk_price'],2)} במחיר XAUUSD, לפני עלויות; לא שקול לסיכון בדולרים בחשבון בלי גודל פוזיציה.

**חריגת פערי נתונים:** {exceptions} עסקאות Holdout נמשכו יותר מ-120 דקות, משום שלא היו נרות מסחר זמינים בזמן הפקודה. ממוצע R בחישוב רגישות לא-סיבתי שמשמיט רק אותן עסקאות: {fmt(extra['holdout_avg_R_excluding_over120m'])}R. אסור לראות בהשמטה תיקון לביצוע בפועל: אי אפשר להבטיח יציאה בעת סגירת מסחר.

## בדיקת עמידה ביעד המשתמש

- **לפחות עסקה בכל יום מסחר:** {'כן, במדגם Holdout' if extra['holdout_days_no_trades']==0 else 'לא — היו '+str(extra['holdout_days_no_trades'])+' ימי מסחר ללא כניסה'}.
- **לפחות +1R ממוצע לעסקה:** {'כן במספר נקודתי בלבד; עדיין דרושה מובהקות' if r.holdout_avg_R>=1 else 'לא'}.
- **אישור למסחר חי:** **לא**. התוצאות אינן מאשרות יתרון מדיד של +1R ומחייבות אימות נוסף עם spread, slippage ונתוני tick/ברוקר.

## הגדרות וקבצי שחזור

- פרמטרים מלאים ל-1,170 גרסאות: [all_1170_variants.csv](../all_1170_variants.csv).
- תוצאות העסקאות של 26 המועמדות: [all_selected_trades.csv](../all_selected_trades.csv) — סינון בעמודה `strategy`.
- קוד חישוב: [backtest.py](../backtest.py) והפקת דוחות: [reports.py](../reports.py).
- שיטת הבחירה: מבין 45 שילובי SL/ניהול, בחרנו מקסימום `train_avg_R - 0.12*sqrt(100/train_n)` תחת לפחות 70 עסקאות פיתוח. אסור לבחור מחדש לפי התוצאות ב-Holdout.
'''
 (D/sample_file).write_text(md,encoding='utf-8')

summary=pd.DataFrame(ci)
summary.to_csv(P/'selected_26_robustness.csv',index=False)
t[t.duration_minutes>120].to_csv(P/'QA_over120min_trades.csv',index=False)
merged=s.merge(summary,on='strategy')
merged['holdout_stable_positive']=(merged.holdout_boot_CI_low>0)
merged['holdout_ge_1R']=merged.holdout_avg_R>=1
merged['daily_100pct']=merged.holdout_coverage_pct>=100
cols=['strategy','manager','stop_atr','target_R','train_n','train_avg_R','holdout_n','holdout_avg_R','holdout_win_rate_pct','holdout_profit_factor','holdout_max_drawdown_R','holdout_coverage_pct','holdout_avg_R_cost07','holdout_boot_CI_low','holdout_boot_CI_high','holdout_stable_positive','holdout_ge_1R','daily_100pct']
merged[cols].sort_values('holdout_avg_R',ascending=False).to_csv(P/'LEADERBOARD_holdout.csv',index=False)
header='''# XAUUSD strategy discovery — 26 families × 45 implementations (1,170 tests)

**Status: RESEARCH ONLY — no validated +1R/trade strategy found.**

All signals are formed on completed M5 candles and executed no earlier than the following M1 open. Trading window uses **Asia/Jerusalem 06:00–20:00 (exclusive)**, including real daylight-saving changes. Max holding time 120 minutes from entry. Market data are XAUUSD BID candles, January 2025–September 2026. Market days with at least 200 active/available M1 bars and positive intraday range: **446** (320 train and 126 holdout).

**No selection on holdout:** each strategy family tests 5 stop distances × 9 management options = 45 candidates using training data only, then locks best family variant. Reports present the locked variant's once-only holdout results. Selecting or combining based on holdout after viewing it will invalidate its status as independent test and require a fresh later period.

## Method and execution assumptions

- Stop distances 0.75, 1.0, 1.5, 2.0, 2.5 × Wilder M5 ATR14 at completed signal bar, using exact M1 exits.
- **Execution time exception:** 25 trades across all 45,009 selected-variant trades (16 in holdout) exceeded 120 elapsed minutes because quote data stopped during exchange closures or gaps. The simulator filled them at the next available M1 open; these gaps make the nominal 120-minute holding cap **not fully executable**. Per-strategy audit is in selected_26_robustness.csv.
- Exit management: fixed 3R/4R/5R/8R, break-even after +1.5R or +2R, 1R ladders, 0.5R ladders. Stop only changes for the subsequent M1 bar.
- If both SL and TP in the same M1 candle, assume the SL hit first. Gap-through stops fill at gap open when worse. Trades may remain open after 20:00 but no new entries outside time window.
- Assumed fixed roundtrip execution friction: **$0.35 price per XAUUSD** base, **$0.70** stress. No true order book, commission tier, or broker tick data; live returns could differ.
- Hindsight 2,091 and 4,584 leg catalogs were **not** used to generate entry times, eliminating that source of direct future label leakage.
- Independent comparison period is **2026-04-01 to 2026-09-24**; training is 2025-01-01 to 2026-03-31.
- Bootstrap CI resamples holdout trading days 1000 times; it may understate regime and interday dependency risk.
- CAVEAT: strategy families were brainstormed after reviewing earlier market data, so multiple-testing / research-selection effects still exist. The holdout must be treated as spent after this report.

## Critical conclusion

**No strategy achieved ≥ +1.00R mean per trade in independent holdout.** The 120-minute cap could not actually be met in 25 trades with market-data gaps, so no model is yet operationally validated.

[QA: trades held beyond 120 minutes](QA_over120min_trades.csv) explicitly lists all such exceptions. Having a signal every trading day is possible with time-based daily entries, but that method did not achieve the required expectancy. Entries should NOT be deployed just because the signal has high historical coverage or the favorable return multiple is 4R/8R.

## Complete leaderboard — lock variants before holdout

| Strategy | Selected risk ×ATR | Manager | Train trades | Train avg R | Holdout trades | Holdout avg R | Holdout Win% | Holdout days with a trade |
|---|---:|---|---:|---:|---:|---:|---:|---:|
'''
for _,r in merged.sort_values('holdout_avg_R',ascending=False).iterrows():
 header+=f"| [{r.strategy}](strategies/{r.strategy}.md) | {r.stop_atr:.2f} | {r.manager} | {int(r.train_n)} | {r.train_avg_R:.3f} | {int(r.holdout_n)} | **{r.holdout_avg_R:.3f}** | {r.holdout_win_rate_pct:.1f}% | {int(r.holdout_days_with_trade)}/126 |\n"
header+='''
## Read the data

- [LEADERBOARD_holdout.csv](LEADERBOARD_holdout.csv) includes cost sensitivity and 95% CI.
- [all_1170_variants.csv](all_1170_variants.csv) includes ALL 1,170 trials with both train/holdout diagnostic columns; do not select variants by comparing holdout returns.
- [selected_26_strategies.csv](selected_26_strategies.csv) contains best train-only variant per family.
- [selected_26_robustness.csv](selected_26_robustness.csv) shows sampling uncertainty, time/stop/TP exits, and cost sensitivity.
- [all_selected_trades.csv](all_selected_trades.csv) contains each trade's entry/exit UTC and Israeli time, direction, R result, price stop distance, exit reason, and selected management.
- [backtest.py](backtest.py), [reports.py](reports.py): full reproducible test implementation, expected to run from original 15M ATR ZIP in the same GitHub repo.

**Next step:** fix strategy deficiencies using training only in a NEW dataset period; test live-paper forward data and broker-realistic spreads. Do not treat small +0.02R samples as statistical edge.
'''
(P/'README.md').write_text(header,encoding='utf-8')
print('generated',len(list(D.glob('*.md'))),'strategy docs; best 3:',merged.nlargest(3,'holdout_avg_R')[['strategy','holdout_avg_R','holdout_boot_CI_low','holdout_boot_CI_high','holdout_avg_R_cost07']].to_string(index=False))