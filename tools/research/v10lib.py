"""v10 : sélection des trades avec contrôle de l'empilement (P&L latent des positions ouvertes au moment de l'entrée)."""
import numpy as np, pandas as pd
from numba import njit
import v6lib as v
from v9lib import *

@njit(cache=True)
def select_guard(st, xt, day, ep, rr, curp, maxpos, maxday, gap, guard_mode, guard_th):
    """st/xt : entrée/sortie ; ep : prix d'entrée (vente) ; rr : 1R en prix ; curp : prix (ask) au moment de l'entrée.
    guard_mode 0 : aucun ; 1 : moyenne des R latents des positions ouvertes >= th ; 2 : dernière position ouverte >= th ;
    3 : toutes les positions >= th."""
    n = len(st); acc = np.zeros(n, np.bool_); open_i = np.full(64, -1, np.int64); last = -10**12; cday = -1; cnt = 0
    for k in range(n):
        if day[k] != cday: cday = day[k]; cnt = 0
        if cnt >= maxday or st[k] - last < gap: continue
        nopen = 0; s = 0.0; mn = 1e9; lastR = 1e9; lastt = -1
        for q in range(64):
            j = open_i[q]
            if j >= 0 and xt[j] > st[k]:
                nopen += 1
                u = (ep[j] - curp[k]) / rr[j]
                s += u
                if u < mn: mn = u
                if st[j] > lastt: lastt = st[j]; lastR = u
        if nopen >= maxpos: continue
        if guard_mode > 0 and nopen > 0:
            if guard_mode == 1 and s / nopen < guard_th: continue
            if guard_mode == 2 and lastR < guard_th: continue
            if guard_mode == 3 and mn < guard_th: continue
        for q in range(64):
            j = open_i[q]
            if j < 0 or xt[j] <= st[k]:
                open_i[q] = k; break
        acc[k] = True; last = st[k]; cnt += 1
    return acc

def prepare(src, ex, **kw):
    X, m1 = v.build_features(src)
    T = broad(src, ex, **kw)
    e = X.m1_next.values[T.i]
    T["ep"] = m1["open"][e]                      # vente au bid
    T["rr"] = ex.get("slk", 3.0) * X.atr.values[T.i]
    T["curp"] = m1["open"][e] + m1["spread"][e] * 1e-5   # prix de rachat (ask) au moment d'une nouvelle entrée
    return T.sort_values("entry_t").reset_index(drop=True)

def portfolio_guard(T, maxpos=10, maxday=10, gap=900, mode=0, th=0.0):
    acc = select_guard(T.entry_t.values, T.exit_t.values, T.day.values, T.ep.values, T.rr.values, T.curp.values,
                       maxpos, maxday, gap, mode, th)
    return T[acc].reset_index(drop=True)

@njit(cache=True)
def trade_from(o, h, l, sp, tm, e, entry, R, tpR, be_t, be_l, t1, t2, minp, pt):
    """vente déjà exécutée au prix `entry` pendant la bougie M1 e (ordre limite) ; même gestion que v6lib.trade"""
    n = len(o); d = -1
    sl = entry + R; tp = entry - tpR * R; best = 0.0; j = e; late = False
    while j < n - 1:
        s = sp[j] * pt
        if j > e:
            if tm[j] - tm[j - 1] > 4 * 3600:
                return (entry - (o[j] + s)) / R, j
            tod = (tm[j] % 86400) // 60
            if tod >= t1: late = True
            if late:
                cur = (entry - (o[j] + s)) / R
                if cur >= minp or tod >= t2: return cur, j
            if h[j] + s >= sl: return (entry - max(sl, o[j] + s)) / R, j
            if l[j] + s <= tp: return (entry - tp) / R, j
            fav = (entry - (l[j] + s)) / R
            if late and fav >= minp: return minp, j
            if fav > best: best = fav
            if best >= be_t:
                nsl = entry - be_l * R
                if nsl < sl: sl = nsl
        j += 1
    return 0.0, j

@njit(cache=True)
def limit_fills(o, h, l, sp, tm, e0s, lim, valid_min, Rs, tpR, be_t, be_l, t1, t2, minp, pt):
    """ordre de vente limite au prix lim, valable valid_min minutes à partir de la bougie M1 e0 : (rempli?, indice, R, sortie)"""
    n = len(e0s); fill = np.zeros(n, np.bool_); fe = np.zeros(n, np.int64); rr = np.zeros(n); xe = np.zeros(n, np.int64); fp = np.zeros(n)
    for k in range(n):
        e = e0s[k]; tend = tm[e] + valid_min * 60
        while e < len(o) - 1 and tm[e] < tend:
            if h[e] >= lim[k]:
                px = o[e] if o[e] >= lim[k] else lim[k]
                r, x = trade_from(o, h, l, sp, tm, e, px, Rs[k], tpR, be_t, be_l, t1, t2, minp, pt)
                fill[k] = True; fe[k] = e; rr[k] = r; xe[k] = x; fp[k] = px
                break
            e += 1
    return fill, fe, rr, xe, fp

def limit_trades(src, ex, k_atr, valid, **kw):
    """signaux v9 exécutés par ordre limite à clôture du signal + k_atr x ATR"""
    X, m1 = v.build_features(src)
    T = broad(src, ex, **kw)
    e0 = X.m1_next.values[T.i]; atr = X.atr.values[T.i]; c = X.close.values[T.i]
    Rs = ex["slk"] * atr; lim = c + k_atr * atr
    t1 = 15 * 60; t2 = 17 * 60
    fill, fe, rr, xe, fp = limit_fills(m1["open"], m1["high"], m1["low"], m1["spread"], m1["time"], e0, lim, valid, Rs,
                                       ex["tpR"], ex["be_t"], ex["be_l"], t1, t2, ex["minp"], 1e-5)
    T = T[fill].copy(); T["entry_t"] = m1["time"][fe[fill]]; T["exit_t"] = m1["time"][xe[fill]]; T["R"] = rr[fill]
    T["ep"] = fp[fill]; T["rr"] = Rs[fill]; T["curp"] = m1["open"][fe[fill]]
    T["h"] = ((T.entry_t % 86400) // 3600).astype(int)
    return T.sort_values("entry_t").reset_index(drop=True)
