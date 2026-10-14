#!/usr/bin/env python3
"""Count daily origins and cross-midnight leg overlaps, fixed UTC+3."""
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
legs=pd.read_csv(ROOT/"primary/XAUUSD_Phase1_Reversal_Legs_3ATR_M15.csv")
ticks=pd.read_csv(ROOT/"raw/xauusd-m1-bid-2025-01-01-2026-09-25.csv")
ticks["date_utc3"]=(pd.to_datetime(ticks.timestamp,unit="ms",utc=True)+pd.Timedelta(hours=3)).dt.date
daily=ticks.groupby("date_utc3").agg(bars=("timestamp","size"),day_high=("high","max"),day_low=("low","min"))
daily=daily[(pd.to_datetime(daily.index).dayofweek<5)&(daily.day_high>daily.day_low)].copy()
starts=pd.to_datetime(legs.origin_datetime_utc,utc=True)+pd.Timedelta(hours=3)
ends=pd.to_datetime(legs.end_datetime_utc,utc=True)+pd.Timedelta(hours=3)
start_dates=set(starts.dt.date)
intersecting=set()
for start,end in zip(starts,ends):
    day=start.normalize()
    while day<=end.normalize():
        if start<day+pd.Timedelta(days=1) and end>day:
            intersecting.add(day.date())
        day+=pd.Timedelta(days=1)
daily["has_new_origin"]=daily.index.isin(start_dates)
daily["overlaps_existing_leg"]=daily.index.isin(intersecting)
daily["range_usd"]=daily.day_high-daily.day_low
assert len(daily)==449
assert daily.has_new_origin.sum()==440
assert daily.overlaps_existing_leg.sum()==447
assert list(map(str,daily.index[~daily.has_new_origin]))==[
 "2025-01-28","2025-04-22","2025-06-27","2025-07-04",
 "2026-01-01","2026-01-02","2026-02-06","2026-06-26","2026-09-25"]
daily.reset_index().to_csv(Path(__file__).with_name("daily_coverage.csv"),index=False)
print("PASS",{"total":len(daily),"with_new_origin":int(daily.has_new_origin.sum()),
"without_new_origin":int((~daily.has_new_origin).sum()),
"with_existing_leg":int(daily.overlaps_existing_leg.sum()),
"without_any_leg":int((~daily.overlaps_existing_leg).sum())})
