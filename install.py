#!/usr/bin/env python3
"""Instala la skill humanizar-es para tus agentes de programacion.
Funciona igual en macOS, Linux y Windows (sin paquetes extra).

Por defecto instala en las dos carpetas que cubren a todos:
  ~/.claude/skills   Claude Code (y OpenCode, que tambien la lee)
  ~/.agents/skills   Codex, OpenCode, Antigravity (agy) y DeepSeek Harness (dsh)

uso:
  python3 install.py                       # las dos carpetas de arriba
  python3 install.py --agente codex        # solo un agente: claude, codex, opencode,
                                           #   antigravity, dsh, gemini o agents
  python3 install.py --destino RUTA        # otra carpeta de skills (crea RUTA/humanizar-es)
  python3 install.py --symlink             # enlaza en vez de copiar (editas aqui, se refleja alla)
  python3 install.py --desinstalar         # la quita de los mismos destinos

En Windows usa `python` o `py` en lugar de `python3`. En macOS y Linux tambien sirve
./install.sh, que llama a este mismo archivo.
"""
import argparse
import os
import shutil
import stat
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
NOMBRE = "humanizar-es"
COPIAR = ("SKILL.md", "README.md", "LICENSE", "THIRD_PARTY.md", "references", "scripts", "ejemplos")


def casa():
    # HOME manda si existe (Git Bash y las pruebas lo fijan); si no, el perfil de Windows.
    return os.environ.get("HOME") or os.path.expanduser("~")


def carpeta_de(agente):
    h = casa()
    return {
        "claude": os.path.join(h, ".claude", "skills"),
        "codex": os.path.join(h, ".codex", "skills"),
        "opencode": os.path.join(h, ".config", "opencode", "skills"),
        "antigravity": os.path.join(h, ".gemini", "config", "skills"),
        "agy": os.path.join(h, ".gemini", "config", "skills"),
        "dsh": os.path.join(h, ".dsh", "skills"),
        "gemini": os.path.join(h, ".gemini", "skills"),
        "agents": os.path.join(h, ".agents", "skills"),
    }.get(agente)


def borrar(ruta):
    if os.path.islink(ruta) or os.path.isfile(ruta):
        os.remove(ruta)
    elif os.path.isdir(ruta):
        def forzar(func, p, _):  # en Windows, los archivos de solo lectura no se borran sin esto
            os.chmod(p, stat.S_IWRITE)
            func(p)
        shutil.rmtree(ruta, onerror=forzar)


def instalar_en(base, modo):
    base = os.path.abspath(os.path.expanduser(base))
    if os.path.basename(base) == NOMBRE:  # no anidar .../humanizar-es/humanizar-es
        base = os.path.dirname(base)
    destino = os.path.join(base, NOMBRE)

    if modo == "desinstalar":
        if os.path.lexists(destino):
            borrar(destino)
            print(f"desinstalada: {destino}")
        else:
            print(f"no estaba en {destino}")
        return

    if os.path.realpath(destino) == os.path.realpath(AQUI):
        sys.exit(f"ERROR: {destino} es este mismo repositorio")
    os.makedirs(base, exist_ok=True)
    if os.path.lexists(destino):
        borrar(destino)

    if modo == "symlink":
        try:
            os.symlink(AQUI, destino, target_is_directory=True)
            print(f"enlazada: {destino} -> {AQUI}")
            return
        except OSError:
            # Windows sin modo de desarrollador no deja crear enlaces: se copia.
            print("AVISO: no se pudo crear el enlace (en Windows hace falta el modo de "
                  "desarrollador); se copia en su lugar.")

    os.makedirs(destino)
    ignorar = shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc")
    for item in COPIAR:
        origen = os.path.join(AQUI, item)
        if os.path.isdir(origen):
            shutil.copytree(origen, os.path.join(destino, item), ignore=ignorar)
        elif os.path.isfile(origen):
            shutil.copy2(origen, destino)
    if os.name == "posix":
        for raiz, dirs, archivos in os.walk(destino):
            for d in dirs:
                os.chmod(os.path.join(raiz, d), 0o755)
            for f in archivos:
                ejecutable = f.endswith((".sh", ".py")) and os.path.basename(raiz) == "scripts"
                os.chmod(os.path.join(raiz, f), 0o755 if ejecutable else 0o644)
    print(f"copiada: {destino}")


def main():
    ap = argparse.ArgumentParser(description="Instala la skill humanizar-es.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("uso:")[1])
    ap.add_argument("--agente", help="claude, codex, opencode, antigravity, dsh, gemini o agents")
    ap.add_argument("--destino", help="otra carpeta de skills")
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--symlink", dest="modo", action="store_const", const="symlink")
    grupo.add_argument("--copiar", dest="modo", action="store_const", const="copiar")
    grupo.add_argument("--desinstalar", dest="modo", action="store_const", const="desinstalar")
    args = ap.parse_args()
    modo = args.modo or "copiar"

    if args.destino:
        destinos = [args.destino]
    elif args.agente:
        c = carpeta_de(args.agente)
        if not c:
            print(f"ERROR: agente desconocido: {args.agente} (ver --help)")
            return 2
        destinos = [c]
    else:
        destinos = [carpeta_de("claude"), carpeta_de("agents")]

    if modo != "desinstalar":
        try:
            with open(os.path.join(AQUI, "SKILL.md"), encoding="utf-8") as fh:
                cabecera = fh.read(400)
        except OSError:
            cabecera = ""
        if f"\nname: {NOMBRE}" not in cabecera:
            print(f"ERROR: {AQUI}/SKILL.md no existe o no declara 'name: {NOMBRE}'")
            return 1

    for base in destinos:
        instalar_en(base, modo)
    if modo == "desinstalar":
        return 0

    py = "python" if os.name == "nt" else "python3"
    print("\nListo. Abre una sesion nueva de tu agente y pidele, por ejemplo:")
    print("  «humaniza este texto sin cambiar lo que dice»")
    print("\nLa primera vez hace falta ademas el modelo local (~4.6 GB, una sola vez):")
    if os.name == "nt":
        print("  winget install llama.cpp")
    else:
        print("  brew install llama.cpp")
    print(f'  {py} "{os.path.join(AQUI, "scripts", "instalar_hip.py")}"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
