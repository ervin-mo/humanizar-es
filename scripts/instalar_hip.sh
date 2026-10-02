#!/usr/bin/env bash
# Atajo para macOS y Linux: la descarga la hace instalar_hip.py (que tambien corre en
# Windows, con: python scripts\instalar_hip.py).
set -euo pipefail
exec python3 "$(dirname "${BASH_SOURCE[0]}")/instalar_hip.py" "$@"
