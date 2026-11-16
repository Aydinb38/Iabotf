#!/usr/bin/env bash
# Build the MQL5 emulator for an Expert Advisor.
#   build.sh path/to/EA.mq5 [outdir]
# Produces: <outdir>/ea_strict.cpp (compile-only check, inputs const),
#           <outdir>/emu       (optimised back-tester),
#           <outdir>/emu_san   (AddressSanitizer + UBSan, division-by-zero traps).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
EA="$(realpath "$1")"; OUT="$(realpath -m "${2:-$HERE/build}")"
mkdir -p "$OUT"
FLAGS="-std=c++17 -Wall -Wextra -Werror -I$HERE"
echo "[1/4] MQL5 lint + translation (strict: inputs read-only)"
python3 "$HERE/translate.py" "$EA" "$OUT/ea_strict.cpp" --strict
echo "[2/4] strict compile check (conversions, shadowing, signedness, formats...)"
g++ $FLAGS -fsyntax-only -DEA_SOURCE="\"$OUT/ea_strict.cpp\"" "$HERE/runner.cpp"
echo "[3/4] translation for execution + optimised build"
python3 "$HERE/translate.py" "$EA" "$OUT/ea_run.cpp"
g++ $FLAGS -O2 -DEA_SOURCE="\"$OUT/ea_run.cpp\"" "$HERE/runner.cpp" -o "$OUT/emu"
echo "[4/4] sanitized build (ASan + UBSan + float divide-by-zero)"
g++ $FLAGS -O1 -g -fsanitize=address,undefined,float-divide-by-zero -fno-sanitize-recover=all \
    -DEA_SOURCE="\"$OUT/ea_run.cpp\"" "$HERE/runner.cpp" -o "$OUT/emu_san"
echo "build OK -> $OUT"
