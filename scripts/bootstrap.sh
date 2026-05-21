#!/usr/bin/env bash
python -m venv .env && source .env/bin/activate
pip install -r requirements.txt
python - <<'PY'
from pathlib import Path; Path("outputs").mkdir(exist_ok=True)
print("Bootstrap complete ✓")
PY
