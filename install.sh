#!/usr/bin/env bash
# Atajo para macOS y Linux: la instalacion la hace install.py (que tambien corre en
# Windows). Mismas opciones; ver: python3 install.py --help
set -euo pipefail
exec python3 "$(dirname "${BASH_SOURCE[0]}")/install.py" "$@"
