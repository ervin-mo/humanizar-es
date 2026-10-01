#!/usr/bin/env python3
"""Calibra el detector sustituto contra un detector real.

Le das textos con el % de IA que les dio tu detector (Grammarly, GPTZero...) y te dice
si el sustituto los ordena igual. Si no los ordena igual, el cubo optimiza a ciegas.

Archivo de etiquetas, una linea por texto (# para comentarios):
  ruta/al/texto.txt <TAB> 100
  ruta/al/otro.txt  <TAB> 39

Compara solo textos de longitud parecida: el puntaje del sustituto depende del largo.

Uso:
  .venv/bin/python scripts/calibrar.py etiquetas.tsv
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def rangos(xs):
    orden = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and xs[orden[j + 1]] == xs[orden[i]]:
            j += 1
        for k in range(i, j + 1):
            r[orden[k]] = (i + j) / 2  # empates: rango promedio
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = rangos(a), rangos(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else float("nan")


def main():
    ap = argparse.ArgumentParser(
        description="Calibra el detector sustituto contra un detector real.",
        epilog="Formato del archivo: una linea por texto, 'ruta<TAB>porcentaje de IA'.")
    ap.add_argument("etiquetas", help="archivo con ruta y %% de IA de tu detector")
    args = ap.parse_args()
    filas = []
    with open(args.etiquetas, encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.split("#", 1)[0].strip()
            if linea:
                ruta, pct = linea.rsplit(None, 1)
                filas.append((ruta.strip(), float(pct)))
    from sustituto import TAMANO, Sustituto  # torch solo hace falta aqui

    s = Sustituto()
    puntajes = []
    print(f"Sustituto Qwen2.5-{TAMANO}\n")
    print(f"{'texto':<36} {'detector %IA':>12} {'sustituto':>10}")
    for ruta, pct in filas:
        with open(ruta, encoding="utf-8") as fh:
            p = s.puntuar(fh.read().strip())["total"]
        puntajes.append(p)
        print(f"{os.path.basename(ruta)[:36]:<36} {pct:>12.0f} {p:>10.2f}")
    rho = spearman([f[1] for f in filas], puntajes)
    print(f"\nCorrelacion de rangos (Spearman): {rho:.2f}")
    print("1.0 = ordena exactamente igual que tu detector · 0 = no tiene relacion")
    return 0


if __name__ == "__main__":
    sys.exit(main())
