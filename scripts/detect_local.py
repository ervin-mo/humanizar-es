#!/usr/bin/env python3
"""Instrumento local: perplejidad y burstiness con un modelo de lenguaje pequeno.

Son las senales clasicas de los detectores tipo GPTZero:
  - perplejidad global: que tan predecible es el texto para un modelo de lenguaje
    (baja = previsible, tipico de texto generado)
  - burstiness: cuanto varia la perplejidad de una oracion a otra
    (baja = todas las oraciones igual de previsibles)

Tambien reporta la variacion de longitud de oracion. Para eso no hace falta este
script: scripts/estilo.py lo mide sin dependencias.

Opcional (--clasificador): un clasificador XLM-R de texto IA/humano. Esta afinado en
ingles, chino y vietnamita, NO en espanol. En el benchmark dio 99.97% a todas las
variantes, humanizadas o no. Se conserva solo para quien quiera reproducirlo.

Requisitos: pip install -r scripts/requirements.txt (torch + transformers). La primera
corrida descarga Qwen2.5-0.5B (~1 GB) a ~/.cache/huggingface. Funciona sin GPU.

Uso:
  .venv/bin/python scripts/detect_local.py texto.txt [otro.txt ...]
  .venv/bin/python scripts/detect_local.py texto.txt --clasificador
"""
import argparse
import math
import os
import statistics
import sys

# mismo corte de oraciones que estilo.py, para que los numeros cuadren
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estilo import oraciones  # noqa: E402

try:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoModelForSequenceClassification,
        AutoTokenizer,
    )
except ImportError:
    sys.exit(
        "ERROR: faltan torch y transformers. Instala con:\n"
        "  python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt"
    )

LM = "Qwen/Qwen2.5-0.5B"
CLASIFICADOR = "bibbbu/multilingual-ai-human-detector_xlm-roberta-base"
MIN_PALABRAS_PPL = 5  # por debajo, la perplejidad de una oracion es puro ruido

_cache = {}


def cargar_lm():
    if "lm" not in _cache:
        tok = AutoTokenizer.from_pretrained(LM)
        mdl = AutoModelForCausalLM.from_pretrained(LM, dtype=torch.float32)
        mdl.eval()
        _cache["lm"] = (tok, mdl)
    return _cache["lm"]


def perplejidad(texto):
    tok, mdl = cargar_lm()
    enc = tok(texto, return_tensors="pt", truncation=True, max_length=1024)
    ids = enc["input_ids"]
    if ids.shape[1] < 3:
        return float("nan")
    with torch.no_grad():
        out = mdl(**enc, labels=ids)
    return float(math.exp(out.loss))


def prob_ia(texto):
    """P(IA) del clasificador. LABEL_0 = humano, LABEL_1 = IA: el mapeo se valido
    con un control humano (el Quijote cae en LABEL_0 con 0.998)."""
    if "cls" not in _cache:
        tok = AutoTokenizer.from_pretrained(CLASIFICADOR)
        mdl = AutoModelForSequenceClassification.from_pretrained(CLASIFICADOR)
        mdl.eval()
        _cache["cls"] = (tok, mdl)
    tok, mdl = _cache["cls"]
    enc = tok(texto, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        probs = torch.softmax(mdl(**enc).logits[0], dim=-1)
    return float(probs[1])


def medir(texto):
    ors = oraciones(texto)
    longs = [len(o.split()) for o in ors]
    ppls = [perplejidad(o) for o in ors if len(o.split()) >= MIN_PALABRAS_PPL]
    ppls = [p for p in ppls if not math.isnan(p)]
    return {
        "palabras": len(texto.split()),
        "oraciones": len(ors),
        "media_palabras": statistics.mean(longs) if longs else float("nan"),
        "sd_longitud": statistics.pstdev(longs) if len(longs) > 1 else float("nan"),
        "perplejidad": perplejidad(texto),
        "burstiness": statistics.pstdev(ppls) if len(ppls) >= 3 else float("nan"),
        "oraciones_ppl": len(ppls),
    }


def main():
    ap = argparse.ArgumentParser(description="Perplejidad y burstiness de uno o varios textos.")
    ap.add_argument("archivos", nargs="+")
    ap.add_argument(
        "--clasificador",
        action="store_true",
        help="agrega P(IA) del clasificador XLM-R (no entrenado en espanol: no fiable)",
    )
    args = ap.parse_args()

    for ruta in args.archivos:
        try:
            with open(ruta, encoding="utf-8") as fh:
                texto = fh.read().strip()
        except OSError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        m = medir(texto)
        print(f"\n=== {ruta}")
        print(
            f"  palabras: {m['palabras']} | oraciones: {m['oraciones']} | "
            f"media palabras/oracion: {m['media_palabras']:.1f} (sd {m['sd_longitud']:.1f})"
        )
        print(f"  perplejidad global:                  {m['perplejidad']:.2f}")
        print(
            f"  burstiness (sd perplejidad/oracion): {m['burstiness']:.2f}"
            f"   [{m['oraciones_ppl']} oraciones de >={MIN_PALABRAS_PPL} palabras]"
        )
        if args.clasificador:
            print(f"  P(IA) clasificador XLM-R:            {prob_ia(texto):.4f}   (no fiable en espanol)")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
