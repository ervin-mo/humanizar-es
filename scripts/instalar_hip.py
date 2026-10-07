#!/usr/bin/env python3
"""Old name of install_model.py, kept so existing commands and agents keep working."""
import os
import runpy
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    print("note: instalar_hip.py is now install_model.py", file=sys.stderr)
    sys.argv[0] = os.path.join(_HERE, "install_model.py")
    runpy.run_path(sys.argv[0], run_name="__main__")
else:
    sys.path.insert(0, _HERE)
    from install_model import *  # noqa: E402,F401,F403
