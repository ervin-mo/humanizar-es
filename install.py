#!/usr/bin/env python3
"""Installs the humanizar-es skill for your coding agents.
Works the same on macOS, Linux and Windows (no extra packages).

By default it installs into the two folders that cover everyone:
  ~/.claude/skills   Claude Code (and OpenCode, which reads it too)
  ~/.agents/skills   Codex, OpenCode, Antigravity (agy) and DeepSeek Harness (dsh)

An old humanizar-es install found in the same folders is removed.

usage:
  python3 install.py                       # the two folders above
  python3 install.py --agent codex         # a single agent: claude, codex, opencode,
                                           #   antigravity, dsh, gemini or agents
  python3 install.py --dest PATH           # another skills folder (creates PATH/humanizar-es)
  python3 install.py --symlink             # link instead of copy (edit here, it shows there)
  python3 install.py --uninstall           # remove it from the same destinations

The old Spanish flags still work: --agente, --destino, --copiar, --desinstalar.
On Windows use `python` or `py` instead of `python3`. On macOS and Linux ./install.sh,
which calls this same file, also works.
"""
import argparse
import os
import shutil
import stat
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "humanizar-es"
LEGACY_NAMES = ("humanize-local",)  # a 3.0 test build that never shipped
COPY = ("SKILL.md", "README.md", "README.es.md", "LICENSE", "THIRD_PARTY.md", "references",
        "scripts", "examples")


def home():
    # HOME wins if set (Git Bash and the tests set it); otherwise the Windows profile.
    return os.environ.get("HOME") or os.path.expanduser("~")


def folder_for(agent):
    h = home()
    return {
        "claude": os.path.join(h, ".claude", "skills"),
        "codex": os.path.join(h, ".codex", "skills"),
        "opencode": os.path.join(h, ".config", "opencode", "skills"),
        "antigravity": os.path.join(h, ".gemini", "config", "skills"),
        "agy": os.path.join(h, ".gemini", "config", "skills"),
        "dsh": os.path.join(h, ".dsh", "skills"),
        "gemini": os.path.join(h, ".gemini", "skills"),
        "agents": os.path.join(h, ".agents", "skills"),
    }.get(agent)


def remove(path):
    if os.path.islink(path) or os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        def force(func, p, _):  # on Windows, read-only files are not deleted without this
            os.chmod(p, stat.S_IWRITE)
            func(p)
        shutil.rmtree(path, onerror=force)


def remove_legacy(base):
    """Removes an install under an old name (folder or symlink) from this skills folder,
    unless it is this very repository."""
    for legacy in LEGACY_NAMES:
        old = os.path.join(base, legacy)
        if os.path.lexists(old) and (os.path.islink(old)
                                     or os.path.realpath(old) != os.path.realpath(HERE)):
            remove(old)
            print(f"removed old version: {old}")


def install_into(base, mode):
    base = os.path.abspath(os.path.expanduser(base))
    if os.path.basename(base) in (NAME,) + LEGACY_NAMES:  # do not nest .../humanizar-es/humanizar-es
        base = os.path.dirname(base)
    dest = os.path.join(base, NAME)

    if mode == "uninstall":
        if os.path.lexists(dest):
            remove(dest)
            print(f"uninstalled: {dest}")
        else:
            print(f"was not in {dest}")
        remove_legacy(base)
        return

    if os.path.realpath(dest) == os.path.realpath(HERE):
        sys.exit(f"ERROR: {dest} is this same repository")
    os.makedirs(base, exist_ok=True)
    remove_legacy(base)
    if os.path.lexists(dest):
        remove(dest)

    if mode == "symlink":
        try:
            os.symlink(HERE, dest, target_is_directory=True)
            print(f"linked: {dest} -> {HERE}")
            return
        except OSError:
            # Windows without developer mode does not allow links: copy instead.
            print("WARNING: could not create the link (on Windows it needs developer "
                  "mode); copying instead.")

    os.makedirs(dest)
    ignore = shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc")
    for item in COPY:
        src = os.path.join(HERE, item)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(dest, item), ignore=ignore)
        elif os.path.isfile(src):
            shutil.copy2(src, dest)
    if os.name == "posix":
        for root, dirs, files in os.walk(dest):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o755)
            for f in files:
                executable = f.endswith((".sh", ".py")) and os.path.basename(root) == "scripts"
                os.chmod(os.path.join(root, f), 0o755 if executable else 0o644)
    print(f"copied: {dest}")


def main():
    ap = argparse.ArgumentParser(description="Installs the humanizar-es skill.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("usage:")[1])
    ap.add_argument("--agent", "--agente", dest="agent",
                    help="claude, codex, opencode, antigravity, dsh, gemini or agents")
    ap.add_argument("--dest", "--destino", dest="dest", help="another skills folder")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--symlink", dest="mode", action="store_const", const="symlink")
    group.add_argument("--copy", "--copiar", dest="mode", action="store_const", const="copy")
    group.add_argument("--uninstall", "--desinstalar", dest="mode", action="store_const",
                       const="uninstall")
    args = ap.parse_args()
    mode = args.mode or "copy"

    if args.dest:
        destinations = [args.dest]
    elif args.agent:
        c = folder_for(args.agent)
        if not c:
            print(f"ERROR: unknown agent: {args.agent} (see --help)")
            return 2
        destinations = [c]
    else:
        destinations = [folder_for("claude"), folder_for("agents")]

    if mode != "uninstall":
        try:
            with open(os.path.join(HERE, "SKILL.md"), encoding="utf-8") as fh:
                header = fh.read(400)
        except OSError:
            header = ""
        if f"\nname: {NAME}" not in header:
            print(f"ERROR: {HERE}/SKILL.md does not exist or does not declare 'name: {NAME}'")
            return 1

    for base in destinations:
        install_into(base, mode)
    if mode == "uninstall":
        return 0

    py = "python" if os.name == "nt" else "python3"
    print("\nDone. Open a new session of your agent and ask it, for example:")
    print("  «humanize this text without changing what it says»")
    print("\nThe first time you also need the local model (~4.6 GB, only once):")
    if os.name == "nt":
        print("  winget install llama.cpp")
    else:
        print("  brew install llama.cpp")
    print(f'  {py} "{os.path.join(HERE, "scripts", "install_model.py")}"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
