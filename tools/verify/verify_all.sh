#!/usr/bin/env bash
# Compile l'EA dans l'émulateur (contrôles stricts) puis exécute les 18 scénarios de vérification.
#   usage : tools/verify/verify_all.sh      (les données doivent être dans data/m1, voir tools/data/fetch_data.sh)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
"$ROOT/tools/mql5emu/build.sh" "$ROOT/MQL5/Experts/IABot/IABot_M5.mq5" "$ROOT/build"
python3 "$ROOT/tools/verify/run_scenarios.py" "$ROOT/build" "$ROOT/data/m1" "$ROOT/tools/verify/last_report.md"
