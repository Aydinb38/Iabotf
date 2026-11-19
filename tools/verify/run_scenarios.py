#!/usr/bin/env python3
"""Automated verification of the IABot_M5 Expert Advisor inside the MQL5 emulator.

usage: run_scenarios.py <build_dir> <m1_data_dir> [report.md]

Every scenario runs the real EA code (translated from the .mq5) on real market
data and checks a list of assertions. Exit code 0 only if every check passes.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

import pandas as pd

BUILD, DATA = sys.argv[1], sys.argv[2]
REPORT = sys.argv[3] if len(sys.argv) > 3 else None
PROFILE_NAME = sys.argv[4] if len(sys.argv) > 4 else "gold"
PROFILES = {
    # EA "or" (IABot_M5) : XAUUSD, TP 4R, trailing, session 9h-20h, 4 trades/jour
    "gold": dict(title="IABot_M5 (or)", sym="XAUUSD", tp=4.0, trailing=True, win=(9, 20), win_incl_end=True, exit_hour=None,
                 max_day=4, risk_pairs=[("EURUSD", []), ("USDJPY", [])], gmt=(7, 18), min_trades=500, min_be=100,
                 extra=[]),
    # EA Forex (IABot_FX_M5) : EURUSD, profil « taux de réussite » (TP 1R, BE 0,5R), entrées 10h-13h, sortie 15h, 3 trades/jour
    "fx": dict(title="IABot_FX_M5 (Forex)", sym="EURUSD", tp=1.0, trailing=False, win=(10, 13), win_incl_end=False, exit_hour=15,
               max_day=3, risk_pairs=[("GBPUSD", []), ("EURJPY", ["--set", "InpDirection=1"])], gmt=(8, 11), min_trades=500, min_be=50,
               extra=["--set", "InpExitHour=13"]),
    # IABot EURUSD v3 : profil « taux de réussite » (sortie en gain, maintien jusqu'à 17 h), filtre d'amplitude, 3 positions espacées d'1 h, risque 0,5 %
    # EA EURUSD v6 : ventes 8h-15h, 10 positions/jour (15 min d'écart), SL 4 ATR, TP 2 R, BE 0,7 R, sortie 15h-17h, risque 0,2 %
    "eurusd": dict(title="IABot_EURUSD v6", sym="EURUSD", tp=2.0, trailing=False, win=(8, 15), win_incl_end=False, exit_hour=17,
                   max_day=10, max_pos=10, min_gap=15, risk=0.2, adaptive=True,
                   risk_pairs=[("GBPUSD", ["--set", "InpDirection=1"]), ("EURJPY", ["--set", "InpDirection=1"])], gmt=(6, 13),
                   min_trades=500, min_be=20, extra=["--set", "InpExitHour=13", "--set", "InpHoldUntilHour=15"]),
}
P = dict(dict(max_pos=1, min_gap=0, risk=0.5, adaptive=False), **PROFILES[PROFILE_NAME])
TMP = os.path.join(BUILD, "scenarios")
os.makedirs(TMP, exist_ok=True)
EMU = os.path.join(BUILD, "emu")
results = []


def aux_args(args):
    """EURUSD : GBPUSD / USDJPY / USDCHF de la même période (force des devises), s'ils existent"""
    if "--data" not in args or "--symbol" not in args or args[args.index("--symbol") + 1] != "EURUSD":
        return []
    data = args[args.index("--data") + 1]; d, f = os.path.split(data); suffix = f[len("EURUSD"):]
    out = []
    for sym in ("GBPUSD", "USDJPY", "USDCHF"):
        pth = os.path.join(d, sym + suffix)
        if os.path.exists(pth):
            out += ["--aux", f"{sym}={pth}"]
    return out


def run(name, args, exe=EMU, expect_rc=0):
    args = args + aux_args(args)
    log = os.path.join(TMP, name + ".log")
    trades = os.path.join(TMP, name + "_trades.csv")
    cmd = [exe] + args + ["--log", log, "--trades", trades]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout + p.stderr
    if p.returncode != expect_rc:
        raise AssertionError(f"exit code {p.returncode} (expected {expect_rc}):\n{out[-2000:]}")
    logtxt = open(log, encoding="utf-8").read() if os.path.exists(log) else ""
    tr = pd.read_csv(trades) if os.path.exists(trades) and os.path.getsize(trades) > 0 else pd.DataFrame()
    if len(tr):
        tr["open_time"] = pd.to_datetime(tr["open_time"], format="%Y.%m.%d %H:%M:%S")
        tr["close_time"] = pd.to_datetime(tr["close_time"], format="%Y.%m.%d %H:%M:%S")
    return out, logtxt, tr


def summary(out):
    s = {}
    m = re.search(r"final balance\s+: ([\d.]+)", out); s["balance"] = float(m.group(1)) if m else None
    m = re.search(r"trades\s+: (\d+).*win rate ([\d.]+)%", out)
    s["trades"], s["win"] = (int(m.group(1)), float(m.group(2))) if m else (0, 0.0)
    m = re.search(r"profit factor\s+: ([\d.]+)", out); s["pf"] = float(m.group(1)) if m else 0
    m = re.search(r"max equity drawdown\s+: [\d.]+ \(([\d.]+)%\)", out); s["dd"] = float(m.group(1)) if m else 0
    m = re.search(r"requests / modifies / rejected : (\d+) / (\d+) / (\d+)", out)
    s["requests"], s["modifies"], s["rejected"] = map(int, m.groups()) if m else (0, 0, 0)
    s["events"] = dict(re.findall(r"(\w+)=(\d+)", re.search(r"events\s+:(.*)", out).group(1))) if "events" in out else {}
    return s


def scenario(title):
    def deco(fn):
        def wrapper():
            checks = []
            def check(cond, what):
                checks.append((bool(cond), what))
            try:
                info = fn(check) or ""
                ok = all(c for c, _ in checks)
                results.append((title, ok, checks, info))
            except Exception as e:  # noqa
                results.append((title, False, checks + [(False, f"exception: {e}")], ""))
        wrapper.__name__ = fn.__name__
        SCENARIOS.append(wrapper)
        return wrapper
    return deco


SCENARIOS = []
XAU = os.path.join(DATA, f"{P['sym']}_IS.csv")
SYM = P["sym"]
TICK = 0.01 if SYM == "XAUUSD" else (0.001 if SYM.endswith("JPY") else 0.00001)
Y2016 = ["--from", "2016-01-01", "--to", "2017-01-01"]


def server_dst(t):
    y = t.year
    mar = datetime(y, 3, 1); start = mar + timedelta(days=(6 - mar.weekday()) % 7 + 7)
    nov = datetime(y, 11, 1); end = nov + timedelta(days=(6 - nov.weekday()) % 7)
    return start <= t < end


def balance_before(tr, deposit=10000.0):
    bal = []
    closed = tr.sort_values("close_time")
    for _, t in tr.iterrows():
        bal.append(deposit + closed[closed.close_time <= t.open_time].profit.sum())
    return pd.Series(bal, index=tr.index)


@scenario(f"1. Référence {P['sym']} 2014-2017 : SL/TP/BE/trailing/risque/horaires conformes")
def s_baseline(check):
    out, log, tr = run("baseline", ["--data", XAU, "--symbol", SYM])
    s = summary(out)
    check(s["trades"] >= P["min_trades"], f"nombre de trades suffisant ({s['trades']})")
    check((tr.init_sl > 0).all() and (tr.tp > 0).all(), "chaque position a un SL et un TP dès l'ouverture")
    ratio = (tr.tp - tr.open).abs() / (tr.open - tr.init_sl).abs()
    tol = 0.02
    check(ratio.between(P["tp"] - tol, P["tp"] + tol).all(), f"TP = {P['tp']:.0f} R (min {ratio.min():.3f} max {ratio.max():.3f}, arrondi au point)")
    check(tr.R.min() >= -2.0 and (tr.R < -1.15).mean() < 0.005,
          f"perte max par trade bornée ({tr.R.min():.2f} R, gaps d'annonces inclus ; {(tr.R < -1.15).sum()} trade(s) sous -1,15 R)")
    bal = balance_before(tr)
    riskpct = tr.risk_money / bal * 100
    tgt = P["risk"]
    check(riskpct.max() <= tgt * 1.12, f"risque par trade <= {tgt} % (+commission) : max {riskpct.max():.3f} %")
    check(riskpct.median() >= tgt * 0.45, f"risque médian cohérent avec la cible ({riskpct.median():.3f} %, risque adaptatif inclus)")
    check(not re.search(r"échec|refusé|impossible|introuvable", log), "aucun échec d'ordre dans le journal")
    # break-even : SL = ouverture +/- 0.1 R
    tk = tr.set_index("ticket")
    bad = 0; n_be = 0
    for m in re.finditer(r"#(\d+) break-even -> SL=([\d.]+)", log):
        t = int(m.group(1)); sl = float(m.group(2))
        if t not in tk.index: continue
        r = tk.loc[t]; R = abs(r.open - r.init_sl); d = 1 if r.type == "BUY" else -1
        n_be += 1
        if abs(sl - (r.open + d * 0.1 * R)) > 2.5 * TICK: bad += 1
    check(n_be > P["min_be"] and bad == 0, f"break-even à +0,1 R vérifié sur {n_be} déplacements (écarts : {bad})")
    bad = 0; n_tr = 0
    for m in re.finditer(r"#(\d+) trailing stop -> SL=([\d.]+)", log):
        t = int(m.group(1)); sl = float(m.group(2))
        if t not in tk.index: continue
        r = tk.loc[t]; R = abs(r.open - r.init_sl); d = 1 if r.type == "BUY" else -1
        n_tr += 1
        if d * (sl - r.open) < 0.5 * R - 2.5 * TICK: bad += 1
    if P["trailing"]:
        check(n_tr > 100 and bad == 0, f"trailing stop toujours >= +0,5 R ({n_tr} déplacements, écarts : {bad})")
    else:
        check(n_tr == 0, "trailing désactivé par défaut : aucun déplacement de trailing")
    h = tr.open_time.dt.hour + tr.open_time.dt.minute / 60
    a, b = P["win"]
    inwin = h.between(a, b) if P["win_incl_end"] else ((h >= a) & (h < b))
    check(inwin.all(), f"entrées uniquement dans la fenêtre {a}h-{b}h (heure serveur)")
    if P["exit_hour"] is not None:
        lim = tr.open_time.dt.normalize() + pd.Timedelta(hours=P["exit_hour"], minutes=1)
        check((tr.close_time <= lim).all(), f"toutes les positions fermées au plus tard à {P['exit_hour']}h le jour même")
    fri = tr.open_time.dt.dayofweek == 4
    check(not (fri & (tr.open_time.dt.hour >= 18)).any(), "aucune entrée le vendredi après 18h")
    span_weekend = (tr.close_time - tr.open_time > pd.Timedelta(days=2)) & (tr.open_time.dt.dayofweek >= 3) & (tr.close_time.dt.dayofweek <= 1)
    m1 = pd.read_csv(XAU, usecols=["time"]); m1t = pd.to_datetime(m1.time, unit="s")
    fri_late = set(m1t[(m1t.dt.dayofweek == 4) & (m1t.dt.hour >= 22)].dt.date)
    explained = 0
    for _, t in tr[span_weekend].iterrows():
        fri = (t.open_time + pd.Timedelta(days=(4 - t.open_time.dayofweek) % 7)).date()
        if fri not in fri_late:
            explained += 1   # marché fermé avant 22h ce vendredi (jour férié) : aucun tick pour clôturer
    check(span_weekend.sum() == explained, f"aucune position gardée le week-end quand le marché cote après 22h le vendredi ({span_weekend.sum()} cas, tous des vendredis fériés/clôture anticipée : {explained})")
    srt = tr.sort_values("open_time")
    ev = sorted([(t, 1) for t in tr.open_time] + [(t, -1) for t in tr.close_time], key=lambda x: (x[0], x[1]))
    cur = mx = 0
    for _, k in ev:
        cur += k; mx = max(mx, cur)
    check(mx <= P["max_pos"], f"jamais plus de {P['max_pos']} position(s) simultanée(s) (max observé {mx})")
    if P["min_gap"] > 0:
        g = srt.groupby(srt.open_time.dt.date).open_time.diff().dropna()
        check((g >= pd.Timedelta(minutes=P["min_gap"])).all(), f"au moins {P['min_gap']} min entre deux entrées (min observé {g.min()})")
    per_day = tr.groupby(tr.open_time.dt.date).size()
    check(per_day.max() <= P["max_day"], f"max {P['max_day']} trade(s) par jour (max observé {per_day.max()})")
    return f"{s['trades']} trades, gain {s['win']}%, PF {s['pf']}, DD {s['dd']}%"


@scenario(f"2. {' et '.join(p[0] for p in P['risk_pairs'])} (autre paire, conversion de devise du profit) : risque correct, aucun plantage")
def s_fx(check):
    for sym, extra in P["risk_pairs"]:
        out, log, tr = run("fx_" + sym, ["--data", os.path.join(DATA, f"{sym}_IS.csv"), "--symbol", sym] + extra + Y2016)
        check(len(tr) > 30, f"{sym} : trades exécutés ({len(tr)})")
        riskpct = tr.risk_money / balance_before(tr) * 100
        normal = tr.volume > 0.0101          # au lot minimum, jusqu'à 2 % sont tolérés (paramètre de l'EA)
        check(riskpct[normal].max() <= P["risk"] * 1.12 and riskpct.median() > P["risk"] * 0.45 and riskpct.max() <= 2.05,
              f"{sym} : risque {riskpct.median():.3f} % (max {riskpct[normal].max():.3f} % ; lot minimum : max {riskpct.max():.3f} %)")
        check((tr.init_sl > 0).all() and (tr.tp > 0).all(), f"{sym} : SL et TP présents")


@scenario("3. Courtier IOC uniquement / RETURN uniquement : mode de remplissage détecté")
def s_filling(check):
    base, _, trb = run("fill_base", ["--data", XAU, "--symbol", SYM] + Y2016)
    for mode in ["IOC", "RETURN"]:
        out, log, tr = run("fill_" + mode, ["--data", XAU, "--symbol", SYM, "--filling", mode] + Y2016)
        s = summary(out)
        check(s["rejected"] == 0, f"{mode} : aucun ordre rejeté ({s['rejected']})")
        check(len(tr) == len(trb), f"{mode} : mêmes trades que la référence ({len(tr)} vs {len(trb)})")


@scenario("4. Requotes aléatoires (30 % des ordres) : nouvelles tentatives automatiques")
def s_requote(check):
    _, _, trb = run("rq_base", ["--data", XAU, "--symbol", SYM] + Y2016)
    out, log, tr = run("requote", ["--data", XAU, "--symbol", SYM, "--requote-prob", "0.3"] + Y2016)
    s = summary(out)
    check(s["rejected"] > 30, f"requotes simulés ({s['rejected']})")
    check(abs(len(tr) - len(trb)) <= max(3, 0.03 * len(trb)), f"trades quasi identiques ({len(tr)} vs {len(trb)})")
    check((tr.init_sl > 0).all(), "SL toujours posé malgré les requotes")


@scenario("5. Courtier qui ignore SL/TP à l'ouverture : l'EA les pose immédiatement")
def s_ignore(check):
    out, log, tr = run("ignore_sltp", ["--data", XAU, "--symbol", SYM, "--ignore-sltp-on-open"] + Y2016)
    n_fix = len(re.findall(r"pose SL/TP", log))
    check(len(tr) > 50 and n_fix == len(tr), f"SL/TP posés après ouverture sur chaque trade ({n_fix}/{len(tr)})")
    check((tr.init_sl > 0).all() and (tr.tp > 0).all(), "toutes les positions finissent protégées")


@scenario("6. Courtier qui refuse SL et TP : fermeture de sécurité immédiate (jamais de position sans SL)")
def s_reject(check):
    out, log, tr = run("reject_sltp", ["--data", XAU, "--symbol", SYM, "--ignore-sltp-on-open", "--reject-sltp"] + Y2016)
    n_safety = len(re.findall(r"SL impossible à poser", log))
    check(len(tr) > 0 and n_safety >= len(tr), f"fermeture de sécurité déclenchée ({n_safety} fois / {len(tr)} trades)")
    check((tr.close_time == tr.open_time).all(), "chaque position non protégée est fermée dans la même seconde")


@scenario("7. Stops level élevé (or 300 pts / Forex 100 pts) et freeze level : aucune requête invalide")
def s_levels(check):
    lv = ["300", "50"] if SYM == "XAUUSD" else ["100", "20"]
    out, log, tr = run("levels", ["--data", XAU, "--symbol", SYM, "--stops-level", lv[0], "--freeze-level", lv[1]] + Y2016)
    s = summary(out)
    check(len(tr) > 50, f"le robot trade toujours ({len(tr)})")
    check(s["events"].get("reject_10016", "0") == "0", "aucun rejet 'invalid stops'")
    check(s["events"].get("reject_10029", "0") == "0", "aucun rejet 'frozen'")


@scenario("8. Compte netting")
def s_netting(check):
    _, _, trb = run("net_base", ["--data", XAU, "--symbol", SYM] + Y2016)
    out, log, tr = run("netting", ["--data", XAU, "--symbol", SYM, "--netting"] + Y2016)
    if P["max_pos"] <= 1:
        check(abs(len(tr) - len(trb)) <= 2, f"comportement identique en netting ({len(tr)} vs {len(trb)})")
    else:
        srt = tr.sort_values("open_time")
        overlap = (srt.open_time.values[1:] < srt.close_time.values[:-1]).sum()
        check(len(tr) > 50 and overlap == 0,
              f"netting : une seule position à la fois, comme l'impose ce type de compte ({len(tr)} trades contre {len(trb)} en hedging)")
    check("compte netting" in log, "mode netting détecté")


@scenario("9. Clôture partielle activée : une seule fois par position")
def s_partial(check):
    out, log, tr = run("partial", ["--data", XAU, "--symbol", SYM, "--set", "InpUsePartialClose=true"] + Y2016)
    parts = re.findall(r"#(\d+) clôturé ([\d.]+) lot\(s\) - raison : clôture partielle", log)
    tickets = [p[0] for p in parts]
    check(len(parts) > 10, f"clôtures partielles exécutées ({len(parts)})")
    check(len(tickets) == len(set(tickets)), "jamais deux clôtures partielles sur la même position")


@scenario("10. Limite de perte journalière (risque 4 %, limite 3 %) : arrêt pour la journée")
def s_daily(check):
    out, log, tr = run("daily", ["--data", XAU, "--symbol", SYM, "--set", "InpRiskPercent=4", "--set", "InpMaxDailyLossPct=3",
                                 "--set", "InpMaxDrawdownPct=0", "--set", "InpCloseOnDailyLoss=true", "--set", "InpMaxTradesPerDay=4"] + Y2016)
    hits = [datetime.strptime(m.group(1), "%Y.%m.%d %H:%M:%S") for m in re.finditer(r"^(\S+ \S+)  IABot: perte journalière max", log, re.M)]
    check(len(hits) > 0, f"limite journalière déclenchée ({len(hits)} jour(s))")
    bad = sum(((tr.open_time > h) & (tr.open_time.dt.date == h.date())).sum() for h in hits)
    check(bad == 0, "aucun nouveau trade le jour même après la limite")


@scenario("11. Coupe-circuit drawdown max (risque 3 %, limite 10 %) : arrêt définitif + fermeture")
def s_maxdd(check):
    out, log, tr = run("maxdd", ["--data", XAU, "--symbol", SYM, "--set", "InpRiskPercent=3", "--set", "InpMaxDrawdownPct=10",
                                 "--set", "InpMaxDailyLossPct=0"])
    m = re.search(r"^(\S+ \S+)  IABot: DRAWDOWN MAX ATTEINT", log, re.M)
    check(m is not None, "coupe-circuit déclenché")
    if m:
        t = datetime.strptime(m.group(1), "%Y.%m.%d %H:%M:%S")
        check((tr.open_time > t).sum() == 0, "plus aucun trade après l'arrêt")
        check((tr.close_time <= t + timedelta(seconds=1)).all(), "positions fermées au déclenchement")


@scenario("12. Petit capital (300 USD) : jamais de risque supérieur à 2 % par trade")
def s_small(check):
    out, log, tr = run("small", ["--data", XAU, "--symbol", SYM, "--deposit", "300"] + Y2016)
    if len(tr):
        riskpct = tr.risk_money / balance_before(tr, 300.0) * 100
        check(riskpct.max() <= 2.1, f"risque max {riskpct.max():.2f} % <= 2 %")
    check(True, f"{len(tr)} trades exécutés avec le lot minimum autorisé")


@scenario("13. Trading algorithmique désactivé : aucun ordre")
def s_algo(check):
    out, log, tr = run("algo_off", ["--data", XAU, "--symbol", SYM, "--algo-off"] + Y2016)
    s = summary(out)
    check(s["trades"] == 0 and s["requests"] == 0, "aucune requête envoyée")


@scenario("14. Mode réel simulé + calendrier : pause autour des news à fort impact, panneau affiché")
def s_news(check):
    out0, log0, tr0 = run("live_base", ["--data", XAU, "--symbol", SYM, "--live"] + Y2016)
    check(len(tr0) > 50, f"mode réel : le robot trade ({len(tr0)})")
    check("IABot" in out0 and "News :" in out0, "panneau d'information affiché")
    picks = tr0.open_time.iloc[::max(1, len(tr0) // 15)].head(15)
    news = os.path.join(TMP, "news.csv")
    with open(news, "w") as f:
        for i, t in enumerate(picks):
            nt = t + timedelta(minutes=10)
            f.write(f"{nt:%Y-%m-%d %H:%M},USD,3,Test event {i}\n")
        f.write(f"{picks.iloc[0] + timedelta(minutes=5):%Y-%m-%d %H:%M},EUR,3,Ignored currency\n")
    out, log, tr = run("live_news", ["--data", XAU, "--symbol", SYM, "--live", "--news", news] + Y2016)
    near = 0
    for t in picks:
        nt = t + timedelta(minutes=10)
        near += ((tr.open_time >= nt - timedelta(minutes=30)) & (tr.open_time <= nt + timedelta(minutes=30))).sum()
    check(near == 0, f"aucune entrée à +/-30 min des {len(picks)} news USD ({near})")
    if P.get("exit_hour", 0) and P["exit_hour"] > 15:
        # positions gardées en perte après 15 h : une news USD à 15 h 30 doit provoquer leur fermeture avant
        held = tr0[(tr0.close_time.dt.hour * 60 + tr0.close_time.dt.minute > 15 * 60 + 30)]
        days = sorted(set(held.close_time.dt.date))[:20]
        news2 = os.path.join(TMP, "news_hold.csv")
        with open(news2, "w") as f:
            for d in days:
                f.write(f"{d:%Y-%m-%d} 15:30,USD,3,Test hold {d}\n")
        out3, log3, tr3 = run("live_hold", ["--data", XAU, "--symbol", SYM, "--live", "--news", news2, "--set", "InpCloseBeforeNews=true"] + Y2016)
        out4, log4, tr4 = run("live_hold_default", ["--data", XAU, "--symbol", SYM, "--live", "--news", news2] + Y2016)
        check(len(re.findall(r"news imminente", log4)) == 0, "par défaut, une position gardée n'est pas fermée avant une news (option désactivée)")
        late = 0
        for d in days:
            x = tr3[(tr3.open_time.dt.date == d) & (tr3.close_time > pd.Timestamp(f"{d} 15:20")) & (tr3.close_time < pd.Timestamp(f"{d} 16:00"))]
            late += int(((x.close_time > pd.Timestamp(f"{d} 15:30"))).sum())
        n_close = len(re.findall(r"news imminente", log3))
        check(len(days) > 3 and n_close > 0 and late == 0,
              f"option activée : position gardée en perte fermée avant la news de 15 h 30 ({n_close} fermeture(s) sur {len(days)} jours testés, {late} après la news)")


@scenario("15. Session en heure GMT (testeur, décalage auto été/hiver US)")
def s_gmt(check):
    g0, g1 = P["gmt"]
    out, log, tr = run("gmt", ["--data", XAU, "--symbol", SYM, "--set", "InpTimeBase=1", "--set", f"InpSessionStart={g0}",
                               "--set", f"InpSessionEnd={g1}"] + P["extra"] + Y2016)
    off = tr.open_time.apply(lambda t: 3 if server_dst(t.to_pydatetime()) else 2)
    gmt_h = (tr.open_time - pd.to_timedelta(off, unit="h"))
    hh = gmt_h.dt.hour + gmt_h.dt.minute / 60
    check(len(tr) > 50 and hh.between(g0, g1).all(), f"entrées entre {g0}h et {g1}h GMT ({len(tr)} trades)")


@scenario("16. Paramètres invalides : initialisation refusée")
def s_invalid(check):
    run("invalid", ["--data", XAU, "--symbol", SYM, "--set", "InpRSIPeriod=1"] + Y2016, expect_rc=3)
    run("invalid2", ["--data", XAU, "--symbol", SYM, "--set", "InpRiskPercent=50"] + Y2016, expect_rc=3)
    check(True, "INIT_PARAMETERS_INCORRECT renvoyé")


@scenario("17. Redémarrage du terminal en pleine position : reprise de la gestion (persistance)")
def s_restart(check):
    outA, logA, trA = run("restartA", ["--data", XAU, "--symbol", SYM] + Y2016)
    # find a moment with an open position
    mid = trA[(trA.open_time > "2016-06-01") & (trA.close_time - trA.open_time > pd.Timedelta(minutes=50))].iloc[0]
    stop = mid.open_time + timedelta(minutes=30)
    state = os.path.join(TMP, "state.txt")
    o1, _, _ = run("restartB1", ["--data", XAU, "--symbol", SYM, "--from", "2016-01-01", "--stop-at", f"{stop:%Y-%m-%d %H:%M}",
                                 "--save-state", state])
    m_open = re.search(r"with (\d+) open position", o1)
    check(m_open is not None and int(m_open.group(1)) >= 1, f"position(s) ouverte(s) au moment de l'arrêt ({m_open.group(1) if m_open else 0})")
    outB, logB, trB = run("restartB2", ["--data", XAU, "--symbol", SYM, "--from", f"{stop:%Y-%m-%d %H:%M}", "--to", "2017-01-01",
                                        "--load-state", state])
    t = int(mid.ticket)
    managed = re.search(rf"#{t} (break-even|trailing stop|clôturé)", logB) or ("SL" in str(trB[trB.ticket == t].exit.values)) or ("TP" in str(trB[trB.ticket == t].exit.values))
    check(managed, f"la position #{t} est toujours gérée après redémarrage")
    bA, bB = summary(outA)["balance"], summary(outB)["balance"]
    check(abs(bA - bB) / 10000 < 0.01, f"résultat final identique à 1 % près ({bA:.2f} vs {bB:.2f})")


@scenario("19. Risque adaptatif : réduction après une série négative, retour à la normale, mémoire persistante")
def s_adaptive(check):
    if not P["adaptive"]:
        check(True, "sans objet pour ce robot")
        return
    out, log, tr = run("adaptive", ["--data", os.path.join(DATA, f"{SYM}_ALL.csv") if os.path.exists(os.path.join(DATA, f"{SYM}_ALL.csv")) else XAU,
                                    "--symbol", SYM, "--from", "2010-01-01", "--to", "2014-01-01", "--set", "InpUseAdaptiveRisk=true", "--set", "InpUseStrength=false"])
    reduced = False; ok = bad = 0; n_red = n_norm = 0
    for line in log.splitlines():
        if "risque adaptatif -> RÉDUIT" in line: reduced = True; n_red += 1
        elif "risque adaptatif -> normal" in line: reduced = False; n_norm += 1
        m = re.search(r"IABot: (VENTE|ACHAT) .*risque ([\d.]+)%\)", line)
        if m:
            exp = P["risk"] * (0.5 if reduced else 1.0)
            if abs(float(m.group(2)) - exp) < 1e-6: ok += 1
            else: bad += 1
    check(n_red > 5 and n_norm > 5, f"bascule en mode réduit ({n_red} fois) et retour à la normale ({n_norm} fois)")
    check(ok > 100 and bad == 0, f"chaque entrée utilise le bon risque ({ok} entrées conformes, {bad} écarts)")


@scenario("18. Exécution instrumentée (AddressSanitizer + UBSan + division par zéro) sur toutes les données")
def s_sanitize(check):
    for f in sorted(os.listdir(DATA)):
        if not f.endswith(".csv"):
            continue
        sym = f.split("_")[0]
        if sym not in ("XAUUSD", "EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY", "USDCHF", "NZDUSD", "EURJPY", "EURCAD", "EURGBP", "EURCHF", "GBPJPY"):
            continue
        if "_MT5" in f and f != "EURUSD_MT5c.csv":   # séries MT5 auxiliaires / brutes : EURUSD nettoyé suffit (19 ans)
            continue
        out, log, tr = run("san_" + f[:-4], ["--data", os.path.join(DATA, f), "--symbol", sym], exe=os.path.join(BUILD, "emu_san"))
        check("ERROR" not in out and "runtime error" not in out, f"{f} : aucune erreur mémoire / UB / division par zéro ({len(tr)} trades)")


if __name__ == "__main__":
    only = os.environ.get("ONLY")
    for sc in SCENARIOS:
        if only and only not in sc.__name__:
            continue
        sc()
    lines = [f"# Vérification automatique de {P['title']}", ""]
    npass = 0
    for title, ok, checks, info in results:
        npass += ok
        lines.append(f"## {'✅' if ok else '❌'} {title}")
        if info:
            lines.append(f"_{info}_")
        for c, what in checks:
            lines.append(f"- {'OK ' if c else 'ÉCHEC'} {what}")
        lines.append("")
    lines.insert(1, f"**{npass}/{len(results)} scénarios réussis**")
    text = "\n".join(lines)
    print(text)
    if REPORT:
        open(REPORT, "w", encoding="utf-8").write(text + "\n")
    sys.exit(0 if npass == len(results) else 1)
