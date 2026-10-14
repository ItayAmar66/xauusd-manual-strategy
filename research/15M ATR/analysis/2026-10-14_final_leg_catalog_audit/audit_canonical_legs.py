#!/usr/bin/env python3
"""Final internal-consistency and original M1 endpoint audit of canonical 3 ATR legs."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
legs=pd.read_csv(ROOT/"primary/XAUUSD_Phase1_Reversal_Legs_3ATR_M15.csv")
m1=pd.read_csv(ROOT/"raw/xauusd-m1-bid-2025-01-01-2026-09-25.csv")
assert len(legs)==2091 and legs.event_id.is_unique
assert m1.timestamp.is_monotonic_increasing and not m1.timestamp.duplicated().any()
assert (legs.movement_atr>=3).all()
assert np.allclose(abs(legs.end_price-legs.origin_price),legs.movement_usd,atol=1e-7)
assert np.allclose(legs.movement_usd/legs.m15_atr14,legs.movement_atr,atol=1e-7)
assert (((legs.end_price>legs.origin_price)==(legs.direction=="LONG"))).all()
st=pd.to_datetime(legs.origin_datetime_utc,utc=True)
en=pd.to_datetime(legs.end_datetime_utc,utc=True)
assert np.allclose((en-st).dt.total_seconds()/60,legs.duration_min)
assert (en>=st).all()
m1=m1.set_index("timestamp")
for ts,prices in [(st,legs.origin_price),(en,legs.end_price)]:
    idx=ts.astype("int64")//1_000_000
    found=m1.reindex(idx)
    assert found.high.notna().all()
    assert np.all(np.isclose(prices,found.high,atol=1e-4,rtol=0)|np.isclose(prices,found.low,atol=1e-4,rtol=0))
srt=legs.assign(st=st,en=en).sort_values("st")
assert (srt.st.iloc[1:].to_numpy()>=srt.en.iloc[:-1].to_numpy()).all()
assert (legs.duration_min==0).sum()==26
assert (legs.duration_min.between(1,120)).sum()==724
assert (legs.duration_min>120).sum()==1341
print("PASS: 2091 unique; 2091 ATR ratios; 4182 exact M1 candle extremes; zero positive-duration overlap; 26 zero-duration ambiguous.")
print("Duration 1-120:",724," >120:",1341)
