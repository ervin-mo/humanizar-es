#!/usr/bin/env bash
# Shortcut for macOS and Linux: the installation is done by install.py (which also
# runs on Windows). Same options; see: python3 install.py --help
set -euo pipefail
exec python3 "$(dirname "${BASH_SOURCE[0]}")/install.py" "$@"
