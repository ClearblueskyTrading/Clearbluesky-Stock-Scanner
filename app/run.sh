#!/usr/bin/env bash
# Run ClearBlueSky on Linux or macOS (no Docker).
# Requires: Python 3.10+, pip, tkinter (e.g. python3-tk on Debian/Ubuntu).

set -e
cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null; then
  echo "Python 3 is required. Install it with your package manager (e.g. brew install python3, or apt install python3 python3-tk)."
  exit 1
fi

# Create venv if missing
if [ ! -d "venv" ]; then
  python3 -m venv venv
  ./venv/bin/pip install -r requirements.txt
fi

./venv/bin/python app.py
