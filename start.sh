#!/usr/bin/env bash
# Load environment variables from web/plash.env using Python helper then run the app
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use Python to parse env file and export variables safely
if [[ -f "$script_dir/web/plash.env" ]]; then
  exports=$(python3 - "$script_dir/web/plash.env" <<'PY'
import shlex
import sys
from pathlib import Path

def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    with path.open() as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('export '):
                line = line[len('export '):].lstrip()
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if value and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            env[key] = value
    return env

env_path = Path(sys.argv[1])
values = load_env(env_path)
for key, value in values.items():
    print(f"export {key}={shlex.quote(value)}")
PY
)
  if [[ -n "$exports" ]]; then
    eval "$exports"
  fi
fi

python3 "$script_dir/web/main.py" "$@"
