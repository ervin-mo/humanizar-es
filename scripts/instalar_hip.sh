#!/usr/bin/env bash
# Descarga el modelo local que usa scripts/hip.py. Una sola vez, ~4.6 GB.
#
#   - Qwen3-4B-Base en GGUF Q8_0 (4.3 GB, Apache-2.0), de Hugging Face
#   - el adaptador HIP de Xu et al. 2026 ya convertido a GGUF (280 MB, Apache-2.0),
#     de las descargas de este repo (ver THIRD_PARTY.md)
#
# Necesita curl y llama.cpp:
#   macOS:    brew install llama.cpp
#   Linux:    brew install llama.cpp  (o compilarlo: github.com/ggml-org/llama.cpp)
#   Windows:  winget install llama.cpp  (y correr esto desde Git Bash o WSL)
#
# Destino: $HUMANIZAR_HIP_DIR o ~/.cache/humanizar-es/hip. Si ya estan los archivos,
# solo los verifica.
set -euo pipefail

DIR="${HUMANIZAR_HIP_DIR:-$HOME/.cache/humanizar-es/hip}"
BASE="Qwen3-4B-Base.Q8_0.gguf"
BASE_URL="https://huggingface.co/mradermacher/Qwen3-4B-Base-GGUF/resolve/main/Qwen3-4B-Base.Q8_0.gguf"
BASE_SHA="4498bfc249d7597bef6e4bff1637c4cb9c6434974cada81b68a26974e23be977"
ADAP="hip-qwen3-4b-base.gguf"
ADAP_URL="https://github.com/ervin-mo/humanizar-es/releases/download/modelo-hip/hip-qwen3-4b-base-q8_0.gguf"
ADAP_SHA="2f120a1f9e1f7d97e5a011a13c6dde127ce08c12edc96efba4bf97542ffdd99c"

if ! command -v llama-completion >/dev/null && ! command -v llama-cli >/dev/null; then
  echo "ERROR: falta llama.cpp. En macOS o Linux: brew install llama.cpp"
  echo "       En Windows: winget install llama.cpp"
  exit 1
fi

sha256() {
  if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

bajar() {  # bajar archivo url sha
  local f="$1" url="$2" sha="$3"
  if [ -s "$f" ] && [ "$(sha256 "$f")" = "$sha" ]; then
    echo "ya estaba: $f"; return
  fi
  echo "Descargando $f ..."
  curl -fL --retry 3 -C - --progress-bar -o "$f.part" "$url"
  if [ "$(sha256 "$f.part")" != "$sha" ]; then
    rm -f "$f.part"; echo "ERROR: $f llego corrupto (sha256 distinto). Vuelve a correr el script."; exit 1
  fi
  mv "$f.part" "$f"
}

mkdir -p "$DIR"
cd "$DIR"
bajar "$ADAP" "$ADAP_URL" "$ADAP_SHA"
bajar "$BASE" "$BASE_URL" "$BASE_SHA"
echo
echo "Listo: $DIR"
ls -lh "$DIR"/*.gguf
