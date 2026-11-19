#!/usr/bin/env python3
"""Converts a ForexFactory calendar export (DateTime with UTC offset, Currency, Impact, Event, Actual, Forecast, Previous)
into data/calendar.csv in MT5 server time (GMT+2 winter / GMT+3 summer, US DST rule = New York time + 7 h).
usage: convert_calendar.py <forex_factory_cache.csv> <out.csv>"""
import sys, pandas as pd
src, out = sys.argv[1], sys.argv[2]
d = pd.read_csv(src, usecols=["DateTime", "Currency", "Impact", "Event", "Actual", "Forecast", "Previous"])
utc = pd.to_datetime(d.DateTime, utc=True)
ny = utc.dt.tz_convert("America/New_York").dt.tz_localize(None)
# rows exported at local midnight have no time (tentative / missing): use the usual New York time of the same event
notime = d.DateTime.str[11:19] == "00:00:00"
key = d.Currency + "|" + d.Event
tod = (ny - ny.dt.normalize())
usual = tod[~notime].groupby(key[~notime]).agg(lambda s: s.mode().iloc[0])
day = pd.to_datetime(d.DateTime.str[:10])
fill = key.map(usual)
ny = ny.where(~notime | fill.isna(), day + fill)
d["timed"] = (~notime | fill.notna()).astype(int)
srv = ny + pd.Timedelta(hours=7)
d["time"] = (srv - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)
d["server"] = srv.dt.strftime("%Y.%m.%d %H:%M")
d["impact"] = d.Impact.map({"High Impact Expected": 3, "Medium Impact Expected": 2, "Low Impact Expected": 1}).fillna(0).astype(int)
d = d.sort_values("time")
d[["time", "server", "timed", "Currency", "impact", "Event", "Actual", "Forecast", "Previous"]].to_csv(out, index=False)
print(len(d), "events", d.server.iloc[0], "->", d.server.iloc[-1])
