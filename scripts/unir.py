#!/usr/bin/env python3
"""Une las oraciones de cada parrafo, como escribe alguien de corrido. Sin modelos.

Grammarly reconoce el ritmo del texto de IA: oraciones de largo parejo, cada una con
su punto. Unirlas con «y» (o con «, pero» cuando la siguiente empieza con «Pero»)
borra ese ritmo sin meter un solo error de ortografia ni de puntuacion. Aplicado
despues de scripts/hip.py, llevo dos ensayos completos a 0% y 10% en Grammarly
(references/evidencia.md §4f). Sobre el texto original, sin hip.py, no basta (57%).

Respeta los nombres propios: no los pasa a minuscula si estan en --conceptos o si
aparecen con mayuscula a media oracion en el texto.

uso:
  python3 scripts/unir.py reescrito.txt -o final.txt --conceptos conceptos.txt
"""
import argparse
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_fidelidad as vf  # noqa: E402

# Palabras que pueden ir con mayuscula a media oracion («San Cristobal de Las Casas»)
# pero que al empezar una oracion son comunes.
COMUNES = set("""El La Los Las Lo Un Una Unos Unas De Del Al A En Y O Con Por Para Sin
Su Sus Mi Mis Este Esta Estos Estas Ese Esa Esos Esas Esto Eso No Si Que""".split())


def nombres_propios(texto, conceptos=()):
    medios = set(re.findall(r"(?<=[a-záéíóúñü,;:] )([A-ZÁÉÍÓÚÑ][\w-]+)", texto)) - COMUNES
    for _, variantes in conceptos:
        for v in variantes:
            for w in v.rstrip("*").split():
                if w[:1].isupper() and w not in COMUNES:
                    medios.add(w)
    return medios


def unir_parrafo(parrafo, propios, p=1.0, rnd=None, maximo=400, dudosas=None):
    rnd = rnd or random.Random(7)
    oraciones = re.split(r"(?<=\.) (?=[A-ZÁÉÍÓÚÑ¿¡])", parrafo.strip())
    out = [oraciones[0]]
    for o in oraciones[1:]:
        prev = out[-1]
        w = o.split()[0]
        base = w.strip(",;:")
        if (not prev.endswith(".") or prev.endswith("...") or rnd.random() >= p
                or len(prev.split()) + len(o.split()) > maximo):
            out.append(o)
            continue
        cuerpo = prev[:-1]
        if base == "Pero":
            out[-1] = cuerpo + ", pero " + o[len(w) + 1:]
        elif o.startswith("Sin embargo, "):
            out[-1] = cuerpo + ", pero " + o[len("Sin embargo, "):]
        elif base in ("Además", "Asimismo", "También"):
            out[-1] = cuerpo + " y " + ("también " if base == "También" else "además ") + o[len(w) + 1:]
        elif base == "Y":
            out[-1] = cuerpo + " y " + o[2:]
        else:
            sig = o if base in propios else o[0].lower() + o[1:]
            if dudosas is not None and base not in propios:
                dudosas.append(base)
            out[-1] = cuerpo + " y " + sig
    return " ".join(out)


def unir(texto, conceptos=(), p=1.0, semilla=7, maximo=400, dudosas=None):
    """dudosas: si es una lista, recibe las palabras que pasaron a minuscula sin
    aparecer asi en ningun otro lugar del texto (posibles nombres propios)."""
    rnd = random.Random(semilla)
    propios = nombres_propios(texto, conceptos)
    parrafos = [x for x in re.split(r"\n\s*\n", texto.strip()) if x.strip()]
    bajadas = []
    salida = "\n\n".join(unir_parrafo(x, propios, p, rnd, maximo, bajadas) for x in parrafos) + "\n"
    if dudosas is not None:
        palabras = set(re.findall(r"\w+", texto))
        comunes = COMUNES | set("""Antes Mientras Cuando Aunque Quizá Quizás Hoy Ahora Así
        Luego Entonces Incluso Tampoco Nunca Siempre Todo Toda Todos Todas Cada Otro Otra
        Más Menos Muy Desde Hasta Entre Sobre Tras Ante Según Durante Como Donde""".split())
        dudosas.extend(sorted({w for w in bajadas if w.lower() not in palabras and w not in comunes
                               and not re.search(r"(ar|er|ir|mente)$", w)}))
    return salida


def main():
    ap = argparse.ArgumentParser(description="Une las oraciones de cada parrafo con «y».")
    ap.add_argument("entrada")
    ap.add_argument("-o", "--salida", required=True)
    ap.add_argument("--conceptos", help="archivo de conceptos (sus nombres propios se respetan)")
    ap.add_argument("--proporcion", type=float, default=1.0,
                    help="fraccion de uniones a hacer (1.0, la medida; 0.6 dio 66%% en Grammarly)")
    ap.add_argument("--maximo", type=int, default=400, help="palabras maximas por oracion unida")
    args = ap.parse_args()

    texto = open(args.entrada, encoding="utf-8").read()
    conceptos = vf.cargar_conceptos(args.conceptos) if args.conceptos else []
    dudosas = []
    unido = unir(texto, conceptos, args.proporcion, maximo=args.maximo, dudosas=dudosas)
    with open(args.salida, "w", encoding="utf-8") as fh:
        fh.write(unido)
    contar = lambda t: len(re.findall(r"[.!?](?:\s|$)", t))
    print(f"Escrito: {args.salida} ({contar(texto)} oraciones -> {contar(unido)})")
    if dudosas:
        print("REVISA: pasaron a minuscula y no aparecen asi en el texto; si son nombres "
              f"propios, agregalos a --conceptos: {', '.join(dudosas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
