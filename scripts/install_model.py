#!/usr/bin/env python3
"""Downloads the local model used by scripts/rewrite.py. Only once, ~4.6 GB.
Works the same on macOS, Linux and Windows (no extra packages).

  - Qwen3-4B-Base as GGUF Q8_0 (4.3 GB, Apache-2.0), from Hugging Face
  - the HIP adapter of Xu et al. 2026 already converted to GGUF (280 MB, Apache-2.0),
    from this repo's downloads (see THIRD_PARTY.md)

Needs llama.cpp:
  macOS and Linux:  brew install llama.cpp
  Windows:          winget install llama.cpp   (and open a new terminal afterwards)

Destination: $HUMANIZE_MODEL_DIR or ~/.cache/humanizar-es/hip. If the
files are already there, it only verifies them. If it gets cut off, run it again: it
resumes where it stopped.

usage:
  python3 scripts/install_model.py        (on Windows: python or py)
"""
import hashlib
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rewrite  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

BASE_URL = "https://huggingface.co/mradermacher/Qwen3-4B-Base-GGUF/resolve/main/Qwen3-4B-Base.Q8_0.gguf"
BASE_SHA = "4498bfc249d7597bef6e4bff1637c4cb9c6434974cada81b68a26974e23be977"
ADAPTER_URL = "https://github.com/ervin-mo/humanizar-es/releases/download/modelo-hip/hip-qwen3-4b-base-q8_0.gguf"
ADAPTER_SHA = "2f120a1f9e1f7d97e5a011a13c6dde127ce08c12edc96efba4bf97542ffdd99c"
CHUNK = 1 << 20


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for piece in iter(lambda: fh.read(CHUNK * 8), b""):
            h.update(piece)
    return h.hexdigest()


def download(name, url, sha, tries=3):
    final = os.path.join(rewrite.MODEL_DIR, name)
    if os.path.isfile(final):
        print(f"verifying {name} ...", flush=True)
        if sha256(final) == sha:
            print(f"already there: {name}")
            return
        os.remove(final)
    partial = final + ".part"
    for attempt in range(1, tries + 1):
        have = os.path.getsize(partial) if os.path.isfile(partial) else 0
        req = urllib.request.Request(url, headers={"User-Agent": "humanizar-es"})
        if have:
            req.add_header("Range", f"bytes={have}-")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if have and r.status != 206:  # the server does not resume: from scratch
                    have = 0
                total = have + int(r.headers.get("Content-Length") or 0)
                print(f"Downloading {name} ({total / 1e9:.2f} GB) ...", flush=True)
                with open(partial, "ab" if have else "wb") as fh:
                    done, t0, last = have, time.time(), 0.0
                    for piece in iter(lambda: r.read(CHUNK), b""):
                        fh.write(piece)
                        done += len(piece)
                        if time.time() - last > 2:
                            last = time.time()
                            speed = (done - have) / max(last - t0, 1e-3) / 1e6
                            pct = f"{100 * done / total:5.1f}%" if total else ""
                            print(f"\r  {pct} {done / 1e9:.2f} GB  {speed:.1f} MB/s   ",
                                  end="", flush=True)
            print()
            break
        except urllib.error.HTTPError as e:
            if e.code == 416 and have:  # it was already complete
                break
            print(f"\n  HTTP error {e.code}; retry {attempt} of {tries} ...", flush=True)
            time.sleep(3)
        except OSError as e:
            print(f"\n  connection dropped ({e}); retry {attempt} of {tries} ...", flush=True)
            time.sleep(3)
    else:
        sys.exit(f"ERROR: could not download {name}. Check the connection and run it again.")
    print(f"verifying {name} ...", flush=True)
    if sha256(partial) != sha:
        os.remove(partial)
        sys.exit(f"ERROR: {name} arrived corrupted (sha256 mismatch). Run it again.")
    os.replace(partial, final)


def main():
    if not rewrite.llama_binary():
        print("ERROR: llama.cpp is missing. " + rewrite.HOW_TO_INSTALL_LLAMA)
        return 1
    os.makedirs(rewrite.MODEL_DIR, exist_ok=True)
    download(rewrite.ADAPTER, ADAPTER_URL, ADAPTER_SHA)
    download(rewrite.BASE, BASE_URL, BASE_SHA)
    print(f"\nReady: {rewrite.MODEL_DIR}")
    for f in (rewrite.ADAPTER, rewrite.BASE):
        print(f"  {f}  {os.path.getsize(os.path.join(rewrite.MODEL_DIR, f)) / 1e9:.2f} GB")
    print(f"  llama.cpp: {rewrite.llama_binary()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
