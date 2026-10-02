#!/usr/bin/env python3
"""Descarga el modelo local que usa scripts/hip.py. Una sola vez, ~4.6 GB.
Funciona igual en macOS, Linux y Windows (sin paquetes extra).

  - Qwen3-4B-Base en GGUF Q8_0 (4.3 GB, Apache-2.0), de Hugging Face
  - el adaptador HIP de Xu et al. 2026 ya convertido a GGUF (280 MB, Apache-2.0),
    de las descargas de este repo (ver THIRD_PARTY.md)

Necesita llama.cpp:
  macOS y Linux:  brew install llama.cpp
  Windows:        winget install llama.cpp   (y abrir una terminal nueva despues)

Destino: $HUMANIZAR_HIP_DIR o ~/.cache/humanizar-es/hip. Si ya estan los archivos,
solo los verifica. Si se corta, vuelve a correrlo: sigue donde se quedo.

uso:
  python3 scripts/instalar_hip.py        (en Windows: python o py)
"""
import hashlib
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hip  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

BASE_URL = "https://huggingface.co/mradermacher/Qwen3-4B-Base-GGUF/resolve/main/Qwen3-4B-Base.Q8_0.gguf"
BASE_SHA = "4498bfc249d7597bef6e4bff1637c4cb9c6434974cada81b68a26974e23be977"
ADAP_URL = "https://github.com/ervin-mo/humanizar-es/releases/download/modelo-hip/hip-qwen3-4b-base-q8_0.gguf"
ADAP_SHA = "2f120a1f9e1f7d97e5a011a13c6dde127ce08c12edc96efba4bf97542ffdd99c"
BLOQUE = 1 << 20


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for trozo in iter(lambda: fh.read(BLOQUE * 8), b""):
            h.update(trozo)
    return h.hexdigest()


def bajar(nombre, url, sha, intentos=3):
    final = os.path.join(hip.DIR_MODELO, nombre)
    if os.path.isfile(final):
        print(f"verificando {nombre} ...", flush=True)
        if sha256(final) == sha:
            print(f"ya estaba: {nombre}")
            return
        os.remove(final)
    parcial = final + ".part"
    for intento in range(1, intentos + 1):
        ya = os.path.getsize(parcial) if os.path.isfile(parcial) else 0
        req = urllib.request.Request(url, headers={"User-Agent": "humanizar-es"})
        if ya:
            req.add_header("Range", f"bytes={ya}-")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if ya and r.status != 206:  # el servidor no reanuda: desde cero
                    ya = 0
                total = ya + int(r.headers.get("Content-Length") or 0)
                print(f"Descargando {nombre} ({total / 1e9:.2f} GB) ...", flush=True)
                with open(parcial, "ab" if ya else "wb") as fh:
                    hecho, t0, aviso = ya, time.time(), 0.0
                    for trozo in iter(lambda: r.read(BLOQUE), b""):
                        fh.write(trozo)
                        hecho += len(trozo)
                        if time.time() - aviso > 2:
                            aviso = time.time()
                            vel = (hecho - ya) / max(aviso - t0, 1e-3) / 1e6
                            pct = f"{100 * hecho / total:5.1f}%" if total else ""
                            print(f"\r  {pct} {hecho / 1e9:.2f} GB  {vel:.1f} MB/s   ",
                                  end="", flush=True)
            print()
            break
        except urllib.error.HTTPError as e:
            if e.code == 416 and ya:  # ya estaba completo
                break
            print(f"\n  error HTTP {e.code}; reintento {intento} de {intentos} ...", flush=True)
            time.sleep(3)
        except OSError as e:
            print(f"\n  se corto ({e}); reintento {intento} de {intentos} ...", flush=True)
            time.sleep(3)
    else:
        sys.exit(f"ERROR: no se pudo bajar {nombre}. Revisa la conexion y vuelve a correrlo.")
    print(f"verificando {nombre} ...", flush=True)
    if sha256(parcial) != sha:
        os.remove(parcial)
        sys.exit(f"ERROR: {nombre} llego corrupto (sha256 distinto). Vuelve a correrlo.")
    os.replace(parcial, final)


def main():
    if not hip.binario():
        print("ERROR: falta llama.cpp. " + hip.COMO_INSTALAR_LLAMA)
        return 1
    os.makedirs(hip.DIR_MODELO, exist_ok=True)
    bajar(hip.ADAPTADOR, ADAP_URL, ADAP_SHA)
    bajar(hip.BASE, BASE_URL, BASE_SHA)
    print(f"\nListo: {hip.DIR_MODELO}")
    for f in (hip.ADAPTADOR, hip.BASE):
        print(f"  {f}  {os.path.getsize(os.path.join(hip.DIR_MODELO, f)) / 1e9:.2f} GB")
    print(f"  llama.cpp: {hip.binario()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
