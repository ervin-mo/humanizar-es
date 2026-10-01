#!/usr/bin/env bash
# Descarga y prepara el modelo local de HIP para scripts/hip.py (una sola vez).
#
#   - Qwen3-4B-Base en GGUF Q8_0 (4.3 GB, Apache-2.0)
#   - el adaptador HIP de Xu et al. 2026 (1 GB, Apache-2.0), convertido a GGUF (280 MB)
#
# Necesita llama.cpp (en Mac: brew install llama.cpp), git y el entorno del repo
# (.venv con scripts/requirements.txt), que trae torch y transformers para convertir.
# Destino: $HUMANIZAR_HIP_DIR o ~/.cache/humanizar-es/hip
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="${HUMANIZAR_HIP_DIR:-$HOME/.cache/humanizar-es/hip}"
PY="$AQUI/.venv/bin/python"
[ -x "$PY" ] || PY="python3"
HF="https://huggingface.co"

command -v llama-completion >/dev/null || command -v llama-cli >/dev/null || {
  echo "ERROR: falta llama.cpp (en Mac: brew install llama.cpp)"; exit 1; }
mkdir -p "$DIR/adaptador"
cd "$DIR"

if [ ! -s Qwen3-4B-Base.Q8_0.gguf ]; then
  echo "Descargando el modelo base (4.3 GB)..."
  curl -fL --progress-bar -o Qwen3-4B-Base.Q8_0.gguf \
    "$HF/mradermacher/Qwen3-4B-Base-GGUF/resolve/main/Qwen3-4B-Base.Q8_0.gguf"
fi

if [ ! -s hip-qwen3-4b-base.gguf ]; then
  echo "Descargando el adaptador HIP (1 GB)..."
  for f in adapter_config.json adapter_model.safetensors; do
    curl -fL --progress-bar -o "adaptador/$f" \
      "$HF/YixuanEvenXu/Qwen3-4B-Base-HIP-adapter/resolve/main/$f"
  done
  [ -d llama.cpp ] || git clone -q --depth 1 https://github.com/ggml-org/llama.cpp llama.cpp
  echo "Convirtiendo el adaptador a GGUF..."
  PYTHONPATH=llama.cpp/gguf-py "$PY" llama.cpp/convert_lora_to_gguf.py adaptador \
    --base-model-id Qwen/Qwen3-4B-Base --outtype q8_0 --outfile hip-qwen3-4b-base.gguf
  rm -rf adaptador llama.cpp  # ya no hacen falta
fi

echo "Listo: $DIR"
ls -lh "$DIR"/*.gguf
