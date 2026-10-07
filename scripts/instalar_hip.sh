#!/usr/bin/env bash
# Old name of install_model.sh, kept so existing commands keep working.
set -euo pipefail
echo "note: instalar_hip.sh is now install_model.sh" >&2
exec bash "$(dirname "${BASH_SOURCE[0]}")/install_model.sh" "$@"
