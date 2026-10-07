#!/usr/bin/env python3
"""Old name of check.py, kept so existing commands and agents keep working."""
import os
import runpy
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    print("note: verificar_fidelidad.py is now check.py", file=sys.stderr)
    sys.argv[0] = os.path.join(_HERE, "check.py")
    runpy.run_path(sys.argv[0], run_name="__main__")
else:
    sys.path.insert(0, _HERE)
    from check import *  # noqa: E402,F401,F403
