#!/usr/bin/env bash
# Instala la skill humanizar-es para tus agentes de programacion.
#
# Por defecto instala en las dos carpetas que cubren a todos:
#   ~/.claude/skills   Claude Code (y OpenCode, que tambien la lee)
#   ~/.agents/skills   Codex, OpenCode, Antigravity (agy) y DeepSeek Harness (dsh)
#
# uso:
#   ./install.sh                       # las dos carpetas de arriba
#   ./install.sh --agente codex        # solo un agente: claude, codex, opencode,
#                                      #   antigravity, dsh, gemini o agents
#   ./install.sh --destino RUTA        # otra carpeta de skills (crea RUTA/humanizar-es)
#   ./install.sh --symlink             # enlaza en vez de copiar (editas aqui, se refleja alla)
#   ./install.sh --desinstalar         # la quita de los mismos destinos
#
# Las opciones se combinan: ./install.sh --agente codex --symlink
# La skill sigue el formato abierto Agent Skills (SKILL.md con name y description).

set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOMBRE="humanizar-es"
DESTINOS=("$HOME/.claude/skills" "$HOME/.agents/skills")
MODO="copiar"

carpeta_de() {
  case "$1" in
    claude) echo "$HOME/.claude/skills" ;;
    codex) echo "$HOME/.codex/skills" ;;
    opencode) echo "$HOME/.config/opencode/skills" ;;
    antigravity|agy) echo "$HOME/.gemini/config/skills" ;;
    dsh) echo "$HOME/.dsh/skills" ;;
    gemini) echo "$HOME/.gemini/skills" ;;
    agents) echo "$HOME/.agents/skills" ;;
    *) return 1 ;;
  esac
}

while [ $# -gt 0 ]; do
  case "$1" in
    --agente)
      [ $# -ge 2 ] || { echo "ERROR: --agente necesita un nombre (ver --help)"; exit 2; }
      c="$(carpeta_de "$2")" || { echo "ERROR: agente desconocido: $2 (ver --help)"; exit 2; }
      DESTINOS=("$c"); shift ;;
    --destino)
      [ $# -ge 2 ] || { echo "ERROR: --destino necesita una ruta"; exit 2; }
      DESTINOS=("$2"); shift ;;
    --symlink) MODO="symlink" ;;
    --copiar) MODO="copiar" ;;
    --desinstalar) MODO="desinstalar" ;;
    -h|--help) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "opcion desconocida: $1 (ver --help)"; exit 2 ;;
  esac
  shift
done

if [ "$MODO" != "desinstalar" ] && ! head -5 "$AQUI/SKILL.md" 2>/dev/null | grep -q "^name: $NOMBRE"; then
  echo "ERROR: $AQUI/SKILL.md no existe o no declara 'name: $NOMBRE'"; exit 1
fi

instalar_en() {
  local base="$1" destino
  # Si la ruta ya termina en .../humanizar-es, no anidar otra carpeta igual.
  [ "$(basename "$base")" = "$NOMBRE" ] && base="$(dirname "$base")"
  destino="$base/$NOMBRE"

  if [ "$MODO" = "desinstalar" ]; then
    if [ -L "$destino" ] || [ -d "$destino" ]; then
      rm -rf "$destino"; echo "desinstalada: $destino"
    else
      echo "no estaba en $destino"
    fi
    return
  fi

  # Nunca instalar encima de la propia carpeta del repo.
  if [ "$(cd "$base" 2>/dev/null && pwd)/$NOMBRE" = "$AQUI" ]; then
    echo "ERROR: $destino es este mismo repositorio"; exit 1
  fi
  mkdir -p "$base"
  if [ -e "$destino" ] || [ -L "$destino" ]; then rm -rf "$destino"; fi

  if [ "$MODO" = "symlink" ]; then
    ln -s "$AQUI" "$destino"
    echo "enlazada: $destino -> $AQUI"
  else
    mkdir -p "$destino"
    # solo lo que la skill usa; sin entorno virtual, git ni pruebas
    for item in SKILL.md README.md LICENSE references scripts ejemplos; do
      if [ -e "$AQUI/$item" ]; then cp -R "$AQUI/$item" "$destino/"; fi
    done
    find "$destino" \( -name .DS_Store -o -name __pycache__ \) -prune -exec rm -rf {} + 2>/dev/null || true
    find "$destino" -type d -exec chmod 755 {} +
    find "$destino" -type f -exec chmod 644 {} +
    chmod 755 "$destino"/scripts/*.sh "$destino"/scripts/*.py
    echo "copiada: $destino"
  fi
}

for base in "${DESTINOS[@]}"; do
  instalar_en "$base"
done

[ "$MODO" = "desinstalar" ] && exit 0
echo
echo "Listo. Abre una sesion nueva de tu agente y pidele, por ejemplo:"
echo "  «humaniza este texto sin cambiar lo que dice»"
echo
echo "Para el cubo (la reescritura guiada por detector) hace falta ademas, una vez:"
echo "  cd \"$AQUI\" && python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt"
