#!/usr/bin/env bash
# Compile les deux EA dans l'émulateur (contrôles stricts) puis exécute les 18 scénarios de chacun.
#   usage : tools/verify/verify_all.sh      (données dans data/m1, voir tools/data/fetch_data.sh)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
"$ROOT/tools/mql5emu/build.sh" "$ROOT/MQL5/Experts/IABot/IABot_FX_M5.mq5" "$ROOT/build/fx"
"$ROOT/tools/mql5emu/build.sh" "$ROOT/MQL5/Experts/IABot/IABot_M5.mq5" "$ROOT/build/gold"
rc=0
python3 "$ROOT/tools/verify/run_scenarios.py" "$ROOT/build/fx" "$ROOT/data/m1" "$ROOT/tools/verify/last_report_fx.md" fx || rc=1
python3 "$ROOT/tools/verify/run_scenarios.py" "$ROOT/build/gold" "$ROOT/data/m1" "$ROOT/tools/verify/last_report.md" gold || rc=1
exit $rc
