#!/usr/bin/env python3
"""Reescritura con un modelo BASE local (HIP), sin API y sin GPU.

Los detectores reconocen sobre todo la huella del entrenamiento de chat: el texto de
un modelo base (sin ese entrenamiento) les parece humano. HIP es Qwen3-4B-Base con un
adaptador LoRA entrenado para parafrasear de vuelta hacia prosa humana (Xu et al.,
2026, «Base Models Look Human To AI Detectors», arXiv:2605.19516; codigo MIT,
adaptador Apache-2.0).

Se entreno en ingles: sin ayuda traduce al ingles. Por eso cada parrafo arranca con
sus dos primeras palabras originales, y el modelo sigue en espanol.

Una sola pasada por parrafo: con mas pasadas el texto se aleja del sentido. Si un
parrafo pierde un concepto de --conceptos o sale truncado, se reintenta; si no hay
forma, se deja el original y se avisa.

Corre en CPU (-ngl 0) con prioridad baja. Unos 30 s por parrafo en una Mac M4.
Instalar antes: python3 scripts/instalar_hip.py  (unos 4.6 GB en ~/.cache/humanizar-es/hip)

uso:
  python3 scripts/hip.py original.txt -o reescrito.txt --conceptos conceptos.txt
  python3 scripts/unir.py reescrito.txt -o final.txt --conceptos conceptos.txt
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_fidelidad as vf  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):  # que una consola de Windows no truene con «» o ñ
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

DIR_MODELO = os.environ.get("HUMANIZAR_HIP_DIR",
                            os.path.expanduser("~/.cache/humanizar-es/hip"))
BASE = "Qwen3-4B-Base.Q8_0.gguf"
ADAPTADOR = "hip-qwen3-4b-base.gguf"


def construir_prompt(parrafo, arranque_palabras=2):
    """El formato con que se entreno HIP, mas las primeras palabras del parrafo
    para que el modelo siga en el idioma del original."""
    arranque = " ".join(parrafo.split()[:arranque_palabras])
    prompt = f"<source_text>\n{parrafo.strip()}\n</source_text>\n\n<target_text>\n{arranque}"
    return prompt, arranque


def limpiar_salida(arranque, generado):
    texto = (arranque + generado).split("</target_text>")[0]
    return " ".join(texto.split())


COMO_INSTALAR_LLAMA = ("En macOS o Linux: brew install llama.cpp. En Windows: winget install "
                       "llama.cpp y abre una terminal nueva. Si ya esta instalado en otra carpeta, "
                       "pon su ruta en la variable HUMANIZAR_LLAMA.")


def binario():
    """llama-completion (o llama-cli, en versiones viejas). Busca en HUMANIZAR_LLAMA, en el
    PATH y, en Windows, en la carpeta de winget, que no entra al PATH hasta abrir otra terminal."""
    propio = os.environ.get("HUMANIZAR_LLAMA")
    if propio:
        return propio if os.path.isfile(propio) else None
    rutas = [None]
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "")
        rutas.append(os.path.join(local, "Microsoft", "WinGet", "Links"))
    for ruta in rutas:
        for b in ("llama-completion", "llama-cli"):
            encontrado = shutil.which(b, path=ruta)
            if encontrado:
                return encontrado
    return None


def girar(parrafo, hilos=4, temperatura=1.0):
    prompt, arranque = construir_prompt(parrafo)
    # El prompt va en un archivo UTF-8 y no en la linea de comandos: en Windows los acentos
    # y las comillas se maltratan al pasar como argumento.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as fh:
        fh.write(prompt)
    try:
        return limpiar_salida(arranque, _correr_llama(fh.name, parrafo, hilos, temperatura))
    finally:
        os.remove(fh.name)


def _correr_llama(archivo_prompt, parrafo, hilos, temperatura):
    llama = binario()
    cmd = [llama, "-m", os.path.join(DIR_MODELO, BASE),
           "--lora", os.path.join(DIR_MODELO, ADAPTADOR),
           "-ngl", "0", "-dev", "none", "-t", str(hilos), "-c", "4096",
           "-n", str(int(len(parrafo.split()) * 3) + 100),
           "--temp", str(temperatura), "--top-p", "0.95",
           "-no-cnv", "--no-display-prompt", "-r", "</target_text>", "-f", archivo_prompt]
    if llama.endswith(".py"):  # un llama falso, para las pruebas
        cmd = [sys.executable] + cmd
    extra = {}
    if os.name == "nt":  # prioridad baja, como nice en macOS y Linux
        extra["creationflags"] = subprocess.BELOW_NORMAL_PRIORITY_CLASS
    elif shutil.which("nice"):
        cmd = ["nice", "-n", "15"] + cmd
    # llama.cpp escribe UTF-8; sin encoding, Windows lo leeria como cp1252.
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL, **extra)
    return r.stdout


def conceptos_en(texto, conceptos):
    t = vf.norm(texto)
    return {n for n, variantes in conceptos if any(vf.patron(v).search(t) for v in variantes)}


def es_titulo(p):
    return len(p.split()) <= 12 and not p.rstrip().endswith((".", "!", "?", "…", ":"))


def main():
    ap = argparse.ArgumentParser(description="Reescritura con modelo base local (HIP), parrafo por parrafo.")
    ap.add_argument("original")
    ap.add_argument("-o", "--salida", required=True)
    ap.add_argument("--conceptos", help="archivo de conceptos que no se pueden perder")
    ap.add_argument("--intentos", type=int, default=3, help="reintentos por parrafo (3)")
    ap.add_argument("--hilos", type=int, default=4, help="hilos de CPU (4)")
    args = ap.parse_args()

    if not binario():
        print("ERROR: falta llama.cpp. " + COMO_INSTALAR_LLAMA, file=sys.stderr)
        return 2
    for f in (BASE, ADAPTADOR):
        if not os.path.isfile(os.path.join(DIR_MODELO, f)):
            print(f"ERROR: falta {f} en {DIR_MODELO}; corre scripts/instalar_hip.py",
                  file=sys.stderr)
            return 2

    texto = open(args.original, encoding="utf-8").read()
    conceptos = vf.cargar_conceptos(args.conceptos) if args.conceptos else []
    parrafos = [x.strip() for x in re.split(r"\n\s*\n", texto) if x.strip()]
    salida, sin_tocar, t0 = [], [], time.time()
    for i, p in enumerate(parrafos, 1):
        if es_titulo(p):
            salida.append(p)
            continue
        pedidos = conceptos_en(p, conceptos)
        elegido = None
        for _ in range(args.intentos):
            r = girar(p, args.hilos)
            if len(r.split()) < 0.6 * len(p.split()) or len(r.split()) > 1.6 * len(p.split()) + 10:
                continue  # truncado o desbocado
            if pedidos - conceptos_en(r, conceptos):
                continue  # perdio un concepto
            elegido = r
            break
        if elegido is None:
            sin_tocar.append(i)
            elegido = p
        salida.append(elegido)
        with open(args.salida, "w", encoding="utf-8") as fh:  # guarda tras cada parrafo
            fh.write("\n\n".join(salida + parrafos[i:]) + "\n")
        print(f"Parrafo {i} de {len(parrafos)}: {'sin tocar' if elegido == p else 'listo'} "
              f"({time.time() - t0:.0f} s)", flush=True)

    print(f"\nEscrito: {args.salida}")
    if sin_tocar:
        print(f"AVISO: los parrafos {sin_tocar} quedaron como el original (perdian conceptos).")
    print("Siguiente paso: relee contra el original y corrige a mano lo que cambio (HIP a\n"
          "veces cambia un detalle, como «limpian» por «lavan los platos»); despues\n"
          "scripts/unir.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
