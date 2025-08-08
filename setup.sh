#!/bin/bash
set -e

echo "🚀 Setting up Make It Heavy"

# Ollama check (quiet)
if ! command -v ollama &> /dev/null; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.ai/install.sh | sh
fi

if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
  ollama serve >/dev/null 2>&1 &
  sleep 2
fi

# Ensure default model
if ! ollama list | grep -q "llama3.2:3b"; then
  ollama pull llama3.2:3b
fi

# Resolve Python interpreter (prefer venv)
if [ -x "./.venv/bin/python" ]; then
  PYTHON="./.venv/bin/python"
elif [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
  PYTHON="$VIRTUAL_ENV/bin/python"
else
  PYTHON="$(command -v python3 || command -v python)"
fi

# Repair broken venvs (encodings error)
if ! "$PYTHON" - <<'PY' >/dev/null 2>&1
import encodings
print('ok')
PY
then
  rm -rf .venv 2>/dev/null || true
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv
    PYTHON="./.venv/bin/python"
  else
    echo "python3 not found" >&2
    exit 1
  fi
fi

echo "Installing Python deps..."
"$PYTHON" -m pip install --upgrade pip -q || true
"$PYTHON" -m pip install -r requirements.txt -q

# Playwright browsers for Crawl4AI (chromium only)
echo "Installing Playwright browsers..."
if ! "$PYTHON" -c "import playwright" >/dev/null 2>&1; then
  "$PYTHON" -m pip install playwright -q
fi
"$PYTHON" -m playwright install chromium >/dev/null 2>&1 || true

echo "Done."