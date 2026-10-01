#!/usr/bin/env python3
"""Detector sustituto local: Binoculars + Fast-DetectGPT sobre modelos Qwen pequenos.

Sirve de brujula para scripts/cubo.py: dice si un cambio acerca o aleja un texto de lo
que marcan los detectores. No es un veredicto: con modelos de 0.5B los textos humanos
de control tambien salen "IA". Compara versiones DEL MISMO texto, nunca textos distintos.

  - Fast-DetectGPT (Bao et al., ICLR 2024), version analitica: cuanto mas alto, mas IA.
  - Binoculars (Hans et al., ICML 2024): cuanto mas bajo, mas IA.
  - total = fdg - 40 * (binoculars - 1): una sola cifra, cuanto mas BAJA, mas humana.
    El 40 solo iguala escalas (en el benchmark, fdg se mueve ~2 puntos y binoculars ~0.05).

En el benchmark ordeno las tres versiones medidas en Grammarly igual que Grammarly
(ver references/evidencia.md). Son tres puntos: evidencia inicial, no prueba.

Uso:
  .venv/bin/python scripts/sustituto.py texto.txt [otro.txt ...]
"""
import argparse
import sys

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:
    sys.exit(
        "ERROR: faltan torch y transformers. Instala con:\n"
        "  python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt"
    )

import os

# Tamano del sustituto: HUMANIZAR_SUSTITUTO=0.5B (por defecto), 1.5B o 3B
TAMANO = os.environ.get("HUMANIZAR_SUSTITUTO", "0.5B")
BASE = f"Qwen/Qwen2.5-{TAMANO}"
INSTRUCT = f"Qwen/Qwen2.5-{TAMANO}-Instruct"
ESCALA_BINO = 40.0


class Sustituto:
    def __init__(self, base=BASE, instruct=INSTRUCT, dispositivo=None):
        # CPU por defecto: en Mac, usar la GPU (mps) traba la pantalla mientras corre.
        # Para usarla: HUMANIZAR_DISPOSITIVO=mps (Mac) o cuda (Nvidia).
        if dispositivo is None:
            dispositivo = os.environ.get("HUMANIZAR_DISPOSITIVO") or "cpu"
        self.dev = dispositivo
        # media precision en GPU (la mitad de memoria); los calculos finales van en float32
        # en CPU, los modelos de mas de 0.5B van en bfloat16 para caber en memoria
        if self.dev in ("mps", "cuda"):
            tipo = torch.float16
        else:
            tipo = torch.float32 if "0.5B" in base else torch.bfloat16
        self.tok = AutoTokenizer.from_pretrained(base)
        self.base = AutoModelForCausalLM.from_pretrained(base, dtype=tipo).to(self.dev).eval()
        self.inst = AutoModelForCausalLM.from_pretrained(instruct, dtype=tipo).to(self.dev).eval()

    @torch.no_grad()
    def puntuar(self, texto):
        ids = self.tok(texto, return_tensors="pt", truncation=True, max_length=1024).input_ids.to(self.dev)
        if ids.shape[1] < 4:
            return {"fdg": 0.0, "binoculars": 1.0, "total": 0.0}
        y = ids[0, 1:]
        lb = self.base(ids).logits[0, :-1].float()
        li = self.inst(ids).logits[0, :-1].float()

        # Fast-DetectGPT analitico: el modelo base muestrea y puntua
        lp = torch.log_softmax(lb, -1)
        p = lp.exp()
        ll = lp.gather(-1, y[:, None]).squeeze(-1)
        media = (p * lp).sum(-1)
        var = (p * lp ** 2).sum(-1) - media ** 2
        fdg = ((ll.sum() - media.sum()) / var.sum().clamp_min(1e-6).sqrt()).item()

        # Binoculars: observador = instruct, ejecutor = base
        lpo = torch.log_softmax(li, -1)
        log_ppl = -lpo.gather(-1, y[:, None]).mean().item()
        x_ppl = -(torch.softmax(lb, -1) * lpo).sum(-1).mean().item()
        bino = log_ppl / x_ppl

        return {"fdg": fdg, "binoculars": bino, "total": fdg - ESCALA_BINO * (bino - 1)}


def main():
    ap = argparse.ArgumentParser(description="Puntua textos con el detector sustituto local.")
    ap.add_argument("archivos", nargs="+")
    args = ap.parse_args()
    s = Sustituto()
    print(f"{'archivo':<40} {'FastDetectGPT ↑IA':>18} {'Binoculars ↓IA':>15} {'total ↑IA':>10}")
    for ruta in args.archivos:
        with open(ruta, encoding="utf-8") as fh:
            r = s.puntuar(fh.read().strip())
        nombre = ruta.replace("\\", "/").split("/")[-1][:40]
        print(f"{nombre:<40} {r['fdg']:>18.2f} {r['binoculars']:>15.4f} {r['total']:>10.2f}")
    print("\nSolo compara versiones del mismo texto: con modelos tan chicos, un texto humano")
    print("de otro tema o de otra epoca puede salir 'IA'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
