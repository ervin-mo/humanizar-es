#!/usr/bin/env python3
"""Old name of rewrite.py, kept so existing commands and agents keep working."""
import os
import runpy
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    print("note: hip.py is now rewrite.py", file=sys.stderr)
    sys.argv[0] = os.path.join(_HERE, "rewrite.py")
    runpy.run_path(sys.argv[0], run_name="__main__")
else:
    sys.path.insert(0, _HERE)
    from rewrite import *  # noqa: E402,F401,F403
