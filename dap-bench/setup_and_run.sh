#!/bin/bash
# dap-bench one-shot for macOS — runs Option 1 (Ollama) and Option 2 (claude CLI).
# Usage:  bash setup_and_run.sh          # both options, n=12
#         N=4 bash setup_and_run.sh     # smaller run
#         SKIP_OLLAMA=1 bash setup_and_run.sh   # only claude-cli
#         SKIP_CLI=1    bash setup_and_run.sh   # only ollama
set -u
cd "$(dirname "$0")"
N="${N:-12}"

echo "==================== Option 1: Ollama (free, local) ===================="
if [ -z "${SKIP_OLLAMA:-}" ]; then
  if ! command -v ollama >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
      echo "Installing ollama via Homebrew..."
      brew install ollama
    else
      echo "!! Ollama not found and no Homebrew."
      echo "   Install the app from https://ollama.com/download then re-run this script."
      exit 1
    fi
  fi
  if ! curl -s --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Starting ollama server in background (log: /tmp/ollama.log)..."
    (ollama serve >/tmp/ollama.log 2>&1 &)
    sleep 4
  fi
  ollama pull qwen2.5:3b
  python3 run.py --backend ollama --n "$N"
else
  echo "skipped (SKIP_OLLAMA set)"
fi

echo
echo "==================== Option 2: claude CLI (subscription) ==============="
if [ -z "${SKIP_CLI:-}" ]; then
  if ! command -v claude >/dev/null 2>&1; then
    if command -v npm >/dev/null 2>&1; then
      echo "Installing Claude Code CLI..."
      npm install -g @anthropic-ai/claude-code
    else
      echo "!! npm not found. Install node first:  brew install node  — then re-run."
      exit 1
    fi
  fi
  # login probe — claude login is interactive and must be done once by a human
  if ! claude -p "Reply with exactly: OK" --max-turns 1 </dev/null 2>/dev/null | grep -q "OK"; then
    echo "!! claude CLI is not logged in. Run:  claude   (then /login), and re-run:"
    echo "   SKIP_OLLAMA=1 bash setup_and_run.sh"
    exit 1
  fi
  python3 run.py --backend claude-cli --n "$N"
else
  echo "skipped (SKIP_CLI set)"
fi

echo
echo "==================== Cross-backend comparison + decision gate =========="
python3 compare.py
echo
echo "Done. Paste results/comparison.md back into Cowork for review."
