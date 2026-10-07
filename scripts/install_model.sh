#!/usr/bin/env bash
# Shortcut for macOS and Linux: the download is done by install_model.py (which also
# runs on Windows, with: python scripts\install_model.py).
set -euo pipefail
exec python3 "$(dirname "${BASH_SOURCE[0]}")/install_model.py" "$@"
