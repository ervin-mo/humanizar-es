#!/usr/bin/env bash
# Instala la skill humanizar-es para un agente de programacion.
#
# uso:
#   ./install.sh                      # Claude Code: ~/.claude/skills/humanizar-es
#   ./install.sh --agente agents      # ~/.agents/skills (Codex, DSH y otros)
#   ./install.sh --agente dsh         # ~/.dsh/skills
#   ./install.sh --destino RUTA       # otra carpeta de skills (crea RUTA/humanizar-es)
#   ./install.sh --symlink            # enlaza en vez de copiar (editas aqui, se refleja alla)
#   ./install.sh --desinstalar        # quita la instalacion del destino elegido
#
# Las opciones se combinan: ./install.sh --agente agents --symlink
#
# Los agentes descubren skills en <carpeta-de-skills>/<nombre>/SKILL.md. La skill no
# depende de rutas absolutas, asi que la copia funciona igual que el original.

set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOMBRE="humanizar-es"
BASE_SKILLS="$HOME/.claude/skills"
MODO="copiar"

while [ $# -gt 0 ]; do
  case "$1" in
    --agente)
      [ $# -ge 2 ] || { echo "ERROR: --agente necesita claude, agents o dsh"; exit 2; }
      case "$2" in
        claude) BASE_SKILLS="$HOME/.claude/skills" ;;
        agents|codex) BASE_SKILLS="$HOME/.agents/skills" ;;
        dsh) BASE_SKILLS="$HOME/.dsh/skills" ;;
        *) echo "ERROR: agente desconocido: $2 (usa claude, agents o dsh)"; exit 2 ;;
      esac
      shift ;;
    --destino)
      [ $# -ge 2 ] || { echo "ERROR: --destino necesita una ruta"; exit 2; }
      BASE_SKILLS="$2"; shift ;;
    --symlink) MODO="symlink" ;;
    --copiar) MODO="copiar" ;;
    --desinstalar) MODO="desinstalar" ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "opcion desconocida: $1 (ver --help)"; exit 2 ;;
  esac
  shift
done

# Si --destino ya apunta a .../humanizar-es, no anidar otra carpeta igual.
if [ "$(basename "$BASE_SKILLS")" = "$NOMBRE" ]; then
  BASE_SKILLS="$(dirname "$BASE_SKILLS")"
fi
DESTINO="$BASE_SKILLS/$NOMBRE"

if [ "$MODO" = "desinstalar" ]; then
  if [ -L "$DESTINO" ] || [ -d "$DESTINO" ]; then
    rm -rf "$DESTINO"
    echo "desinstalada: $DESTINO"
  else
    echo "no estaba instalada en $DESTINO"
  fi
  exit 0
fi

if ! head -5 "$AQUI/SKILL.md" 2>/dev/null | grep -q "^name: $NOMBRE"; then
  echo "ERROR: $AQUI/SKILL.md no existe o no declara 'name: $NOMBRE'"; exit 1
fi

# Nunca instalar encima de la propia carpeta del repo.
if [ "$(cd "$BASE_SKILLS" 2>/dev/null && pwd)/$NOMBRE" = "$AQUI" ]; then
  echo "ERROR: el destino es este mismo repositorio"; exit 1
fi

mkdir -p "$BASE_SKILLS"
if [ -e "$DESTINO" ] || [ -L "$DESTINO" ]; then
  echo "reemplazo la instalacion previa en $DESTINO"
  rm -rf "$DESTINO"
fi

if [ "$MODO" = "symlink" ]; then
  ln -s "$AQUI" "$DESTINO"
  echo "enlazada: $DESTINO -> $AQUI"
else
  mkdir -p "$DESTINO"
  # solo lo que la skill usa; sin entorno virtual, git ni pruebas
  for item in SKILL.md README.md LICENSE references scripts ejemplos; do
    [ -e "$AQUI/$item" ] && cp -R "$AQUI/$item" "$DESTINO/"
  done
  find "$DESTINO" \( -name .DS_Store -o -name __pycache__ \) -prune -exec rm -rf {} + 2>/dev/null || true
  find "$DESTINO" -type d -exec chmod 755 {} +
  find "$DESTINO" -type f -exec chmod 644 {} +
  chmod 755 "$DESTINO"/scripts/*.sh "$DESTINO"/scripts/*.py
  echo "copiada: $AQUI -> $DESTINO"
fi

echo
echo "Listo. Abre una sesion nueva de tu agente y pidele, por ejemplo:"
echo "  «humaniza este texto sin cambiar lo que dice»"
echo
echo "Opcional, para medir perplejidad y burstiness (~1 GB de descarga):"
echo "  cd \"$AQUI\" && python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt"
