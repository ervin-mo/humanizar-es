#!/usr/bin/env bash
# Corre todos los instrumentos disponibles sobre uno o varios textos.
#
# uso:
#   scripts/medir.sh texto.txt                        # mide un archivo
#   scripts/medir.sh original.txt reescrito.txt       # mide y compara fidelidad
#   scripts/medir.sh original.txt reescrito.txt --conceptos conceptos.txt
#   scripts/medir.sh texto.txt control.txt --sin-fidelidad
#   scripts/medir.sh texto.txt --rapido               # sin detectores web ni modelo local
#
# Instrumentos, de menos a mas requisitos:
#   1. estilo.py               biblioteca estandar de Python   siempre
#   2. verificar_fidelidad.py  biblioteca estandar de Python   con 2+ archivos
#   3. detect_local.py         .venv con torch/transformers    si existe el .venv
#   4. ZeroGPT y GPTZero       ego-browser                     si esta en el PATH
#
# Con 2+ archivos, el PRIMERO es la referencia (el original).
# Codigo de salida: 1 si la fidelidad falla, 2 si hay error de uso, 0 en otro caso.

set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$(dirname "$AQUI")"
RAPIDO=0
SIN_FIDELIDAD=0
CONCEPTOS=()
ARCHIVOS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --rapido) RAPIDO=1 ;;
    --sin-fidelidad) SIN_FIDELIDAD=1 ;;
    --conceptos)
      [ $# -ge 2 ] || { echo "ERROR: --conceptos necesita un archivo"; exit 2; }
      CONCEPTOS=(--conceptos "$2"); shift ;;
    -h|--help) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "opcion desconocida: $1"; exit 2 ;;
    *) ARCHIVOS+=("$1") ;;
  esac
  shift
done

if [ ${#ARCHIVOS[@]} -eq 0 ]; then
  echo "uso: scripts/medir.sh archivo.txt [archivo2.txt ...] [--conceptos f] [--rapido] [--sin-fidelidad]"
  exit 2
fi

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "ERROR: hace falta python3 en el PATH"; exit 2
fi

for f in "${ARCHIVOS[@]}"; do
  [ -f "$f" ] || { echo "ERROR: no existe $f"; exit 2; }
done

echo "==================================================================="
echo " MEDICION: ${#ARCHIVOS[@]} archivo(s)"
echo "==================================================================="

# ---------- 1. estilo ----------
echo
echo "--- 1. ESTILO (sin dependencias) ---"
"$PY" "$AQUI/estilo.py" "${ARCHIVOS[@]}"

# ---------- 2. fidelidad ----------
ESTADO=0
if [ ${#ARCHIVOS[@]} -ge 2 ]; then
  echo
  if [ "$SIN_FIDELIDAD" -eq 1 ]; then
    echo "--- 2. FIDELIDAD: omitida (--sin-fidelidad) ---"
  else
    echo "--- 2. FIDELIDAD DE CONTENIDO (referencia: $(basename "${ARCHIVOS[0]}")) ---"
    echo "  Compara solo variantes del MISMO texto. Si mezclas un control humano, usa"
    echo "  --sin-fidelidad."
    if [ ${#CONCEPTOS[@]} -eq 0 ]; then
      echo "  Sin --conceptos: lista extraida automaticamente. Revisala con"
      echo "  scripts/verificar_fidelidad.py ORIGINAL --listar"
    fi
    echo
    "$PY" "$AQUI/verificar_fidelidad.py" "${ARCHIVOS[@]}" ${CONCEPTOS[@]+"${CONCEPTOS[@]}"} || ESTADO=1
  fi
fi

# ---------- 3. modelo local ----------
echo
if [ "$RAPIDO" -eq 1 ]; then
  echo "--- 3. MODELO LOCAL: omitido (--rapido) ---"
elif [ -x "$BASE/.venv/bin/python" ]; then
  echo "--- 3. MODELO LOCAL (perplejidad / burstiness) ---"
  "$BASE/.venv/bin/python" "$AQUI/detect_local.py" "${ARCHIVOS[@]}" 2>&1 | grep -v -i "warn"
else
  echo "--- 3. MODELO LOCAL: omitido (no hay .venv; ver README, seccion Instalacion) ---"
fi

# ---------- 4. detectores web ----------
echo
if [ "$RAPIDO" -eq 1 ]; then
  echo "--- 4. DETECTORES WEB: omitidos (--rapido) ---"
elif command -v ego-browser >/dev/null 2>&1; then
  echo "--- 4a. ZEROGPT ---"
  "$AQUI/score-zerogpt.sh" "${ARCHIVOS[@]}"
  echo
  echo "--- 4b. GPTZERO (no reproducible: mide un control humano en la misma corrida) ---"
  "$AQUI/score-gptzero.sh" "${ARCHIVOS[@]}"
else
  echo "--- 4. DETECTORES WEB: omitidos (ego-browser no esta en el PATH) ---"
fi

echo
echo "==================================================================="
cat <<'FIN'
 Recordatorios
  - Ningun detector es concluyente: miden distinto y se contradicen.
  - Mide un control humano del mismo registro. Si sale marcado como IA,
    descarta la corrida: el detector no esta midiendo.
  - La fidelidad es bloqueante: si baja del 100%, el texto no sirve.
  - Reporta que detector dijo que; nunca un veredicto agregado.
FIN
exit $ESTADO
