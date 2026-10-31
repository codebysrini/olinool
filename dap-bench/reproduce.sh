#!/usr/bin/env bash
# One-command independent reproduction of the dabba scoped-views ANCHOR result.
# Fully local, keyless, free: runs qwen2.5:3b via ollama, no API keys, no signup.
# Writes to a throwaway outdir (never touches the committed reference), then
# checks your numbers against ours by EXIT CODE.
#
#   ./reproduce.sh
#
# Prereqs (the script checks and tells you): python3.12, ollama running with
# the qwen2.5:3b model pulled (`ollama pull qwen2.5:3b`).
set -euo pipefail
cd "$(dirname "$0")"

echo "==> dabba scoped-views — independent anchor reproduction"

# 1. env checks
command -v python3.12 >/dev/null || { echo "MISSING: python3.12 (needed for the pinned env)"; exit 2; }
command -v ollama >/dev/null || { echo "MISSING: ollama (https://ollama.com) — the anchor model runs locally"; exit 2; }
curl -sf http://localhost:11434/api/tags >/dev/null || { echo "ollama is not running — start it, then re-run"; exit 2; }
ollama list 2>/dev/null | grep -q "qwen2.5:3b" || { echo "MISSING model — run: ollama pull qwen2.5:3b"; exit 2; }

# 2. isolated venv (pinned deps live in ../ per package; this benchmark needs only stdlib + the local packages)
VENV=".venv-reproduce"
if [ ! -d "$VENV" ]; then
  echo "==> creating pinned venv"
  python3.12 -m venv "$VENV"
  "$VENV/bin/pip" -q install cryptography pytest >/dev/null
  # install the local packages the benchmark drives (editable, from this checkout)
  "$VENV/bin/pip" -q install -e ../moolam -e ../olinool -e ../dabba >/dev/null 2>&1 || true
fi
PY="$VENV/bin/python"

# 3. sanity: suites green before we trust any number
echo "==> running the benchmark's own test suite"
"$PY" -m pytest -q . >/dev/null && echo "    tests pass" || { echo "TESTS FAILED — environment problem, stop here"; exit 1; }

# 4. run the anchor A/B pilot into a throwaway dir (guarded: never overwrites the reference)
OUT="repro_out_$(date +%s)"
mkdir -p "$OUT"
echo "==> running the anchor pilot (qwen2.5:3b, n=12, real dabba runtime + seals)"
"$PY" run.py --backend ollama --model qwen2.5:3b --runtime dabba --n 12 --outdir "$OUT"

# 5. compare to the committed reference by exit code
echo "==> checking your numbers against the committed reference"
"$PY" reproduce_check.py "$OUT/raw_ollama.jsonl"
