#!/usr/bin/env bash
# Télécharge les données M1 publiques utilisées pour les tests et les convertit
# (heure serveur GMT+2/+3) dans data/m1/.   usage : tools/data/fetch_data.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RAW="$ROOT/data/raw"; OUT="$ROOT/data/m1"
mkdir -p "$RAW/2026" "$OUT"
# 1) HistData M1 2014-2018 (dépôt public riknv/fx-m1-data, clone partiel)
if [ ! -d "$RAW/fxm1" ]; then
  git clone --filter=blob:none --no-checkout --depth 1 https://github.com/riknv/fx-m1-data.git "$RAW/fxm1"
fi
paths=""
for p in eurusd gbpusd usdjpy xauusd audusd; do
  P=$(echo $p | tr a-z A-Z)
  for y in 2014 2015 2016 2017 201801 201802 201803 201804 201805 201806 201807 201808 201809 201810; do
    paths="$paths $p/DAT_ASCII_${P}_M1_${y}.zip"
  done
done
for y in 2005 2006 2007 2008 2009 2010 2011 2012 2013; do paths="$paths eurusd/DAT_ASCII_EURUSD_M1_${y}.zip"; done
(cd "$RAW/fxm1" && git checkout HEAD -- $paths)
# 2) échantillons M1 récents (getdata.finance, 2026-03 -> 2026-09)
for p in eurusd gbpusd usdjpy audusd usdcad; do
  curl -sSfL -o "$RAW/2026/${p^^}_1m.csv" "https://raw.githubusercontent.com/getdata-finance/${p}-1m-ohlcv-forex-historical-data/main/${p^^}_1m.csv"
done
curl -sSfL -o "$RAW/2026/XAUUSD_1m.csv" "https://raw.githubusercontent.com/getdata-finance/xauusd-1m-ohlcv-metals-historical-data/main/XAUUSD_1m.csv"
python3 "$ROOT/tools/data/prepare_data.py" "$RAW/fxm1" "$RAW/2026" "$OUT"
python3 "$ROOT/tools/data/build_eurusd_all.py" "$RAW/fxm1" "$OUT/EURUSD_ALL.csv"
