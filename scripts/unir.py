#!/usr/bin/env python3
"""Une las oraciones de cada parrafo, como escribe alguien de corrido. Sin modelos.
En espanol y en ingles (detecta el idioma).

Grammarly reconoce el ritmo del texto de IA: oraciones de largo parejo, cada una con
su punto. Unirlas con «y» / «and» (o con «, pero» / «, but» cuando corresponde)
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

if hasattr(sys.stdout, "reconfigure"):  # que una consola de Windows no truene con «» o ñ
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

# Por idioma: palabras que pueden ir con mayuscula a media oracion («San Cristobal de
# Las Casas», «The Hague») pero que al empezar una oracion son comunes; los conectores
# con que se une; y lo que no se avisa como posible nombre propio.
IDIOMAS = {
    "es": {
        "comunes": set("""El La Los Las Lo Un Una Unos Unas De Del Al A En Y O Con Por Para Sin
        Su Sus Mi Mis Este Esta Estos Estas Ese Esa Esos Esas Esto Eso No Si Que""".split()),
        "y": "y", "pero": ("Pero",), "contraste": ("Sin embargo, ",),
        "suma": {"Además": "además", "Asimismo": "además", "También": "también"},
        "siempre": set(),
        "no_avisar": set("""Antes Mientras Cuando Aunque Quizá Quizás Hoy Ahora Así Luego
        Entonces Incluso Tampoco Nunca Siempre Todo Toda Todos Todas Cada Otro Otra Más
        Menos Muy Desde Hasta Entre Sobre Tras Ante Según Durante Como Donde""".split()),
        "sufijos": r"(ar|er|ir|mente)$",
        "pistas": set("de la que el en y los las del se por un una con para es".split()),
    },
    "en": {
        "comunes": set("""The A An This That These Those It Its In On At For Of To With By From
        As If When While And Or But Not No Our Their His Her We They He She You What Which
        There Here Some Many Most Each Every Such""".split()),
        "y": "and", "pero": ("But", "Yet"), "contraste": ("However, ",),
        "suma": {"Also": "also", "Additionally,": "also", "Moreover,": "also",
                 "Furthermore,": "also"},
        "siempre": {"I", "I'm", "I've", "I'd", "I'll"},
        "no_avisar": set("""Before After Today Now Then Even Still Never Always Every Each
        Other Another More Less Very Since Until Between Over During How Where Why Once
        Instead Rather Despite Although Though Because Nevertheless Ultimately Finally
        Meanwhile Similarly Consequently Therefore Thus Yet So""".split()),
        "sufijos": r"(ly|ing|ed)$",
        "pistas": set("the and of to is that in it for with as on are this be".split()),
    },
}
COMUNES = IDIOMAS["es"]["comunes"]  # compatibilidad

# «Dr. Smith», «Sr. García», «e.g. Slack»: el punto no cierra la oracion.
ABREVIATURA = re.compile(r"(?:^|\s)(?:Mr|Mrs|Ms|Dr|Prof|St|Sr|Sra|Srta|Dra|Lic|Ing|vs|etc|"
                         r"approx|e\.g|i\.e|U\.S|p\.ej)\.$", re.I)


def detectar_idioma(texto):
    palabras = re.findall(r"[a-záéíóúñü]+", texto.lower())
    cuenta = {i: sum(w in c["pistas"] for w in palabras) for i, c in IDIOMAS.items()}
    return max(cuenta, key=cuenta.get)


def nombres_propios(texto, conceptos=(), idioma="es"):
    comunes = IDIOMAS[idioma]["comunes"]
    medios = set(re.findall(r"(?<=[a-záéíóúñü,;:] )([A-ZÁÉÍÓÚÑ][\w'-]+)", texto)) - comunes
    medios |= IDIOMAS[idioma]["siempre"]
    for _, variantes in conceptos:
        for v in variantes:
            for w in v.rstrip("*").split():
                if w[:1].isupper() and w not in comunes:
                    medios.add(w)
    return medios


def unir_parrafo(parrafo, propios, p=1.0, rnd=None, maximo=400, dudosas=None, idioma="es"):
    rnd = rnd or random.Random(7)
    c = IDIOMAS[idioma]
    oraciones = re.split(r"(?<=\.) (?=[A-ZÁÉÍÓÚÑ¿¡])", parrafo.strip())
    out = [oraciones[0]]
    for o in oraciones[1:]:
        prev = out[-1]
        w = o.split()[0]
        base = w.strip(",;:")
        if (not prev.endswith(".") or prev.endswith("...") or ABREVIATURA.search(prev)
                or rnd.random() >= p or len(prev.split()) + len(o.split()) > maximo):
            out.append(o)
            continue
        cuerpo = prev[:-1]
        contraste = next((x for x in c["contraste"] if o.startswith(x)), None)
        if base in c["pero"]:
            out[-1] = cuerpo + f", {base.lower()} " + o[len(w) + 1:]
        elif contraste:
            out[-1] = cuerpo + ", " + c["pero"][0].lower() + " " + o[len(contraste):]
        elif w in c["suma"] or base in c["suma"]:
            out[-1] = cuerpo + f" {c['y']} " + c["suma"].get(w, c["suma"].get(base)) + " " + o[len(w) + 1:]
        elif base.lower() == c["y"] and base[:1].isupper():
            out[-1] = cuerpo + f" {c['y']} " + o[len(w) + 1:]
        else:
            sig = o if base in propios else o[0].lower() + o[1:]
            if dudosas is not None and base not in propios:
                dudosas.append(base)
            out[-1] = cuerpo + f" {c['y']} " + sig
    return " ".join(out)


def unir(texto, conceptos=(), p=1.0, semilla=7, maximo=400, dudosas=None, idioma=None):
    """dudosas: si es una lista, recibe las palabras que pasaron a minuscula sin
    aparecer asi en ningun otro lugar del texto (posibles nombres propios).
    idioma: "es", "en" o None para detectarlo."""
    idioma = idioma or detectar_idioma(texto)
    c = IDIOMAS[idioma]
    rnd = random.Random(semilla)
    propios = nombres_propios(texto, conceptos, idioma)
    parrafos = [x for x in re.split(r"\n\s*\n", texto.strip()) if x.strip()]
    bajadas = []
    salida = "\n\n".join(unir_parrafo(x, propios, p, rnd, maximo, bajadas, idioma)
                         for x in parrafos) + "\n"
    if dudosas is not None:
        palabras = set(re.findall(r"\w+", texto))
        dudosas.extend(sorted({w for w in bajadas if w.lower() not in palabras
                               and w not in c["comunes"] | c["no_avisar"]
                               and not re.search(c["sufijos"], w)}))
    return salida


def main():
    ap = argparse.ArgumentParser(description="Une las oraciones de cada parrafo con «y».")
    ap.add_argument("entrada")
    ap.add_argument("-o", "--salida", required=True)
    ap.add_argument("--conceptos", help="archivo de conceptos (sus nombres propios se respetan)")
    ap.add_argument("--proporcion", type=float, default=1.0,
                    help="fraccion de uniones a hacer (1.0, la medida; 0.6 dio 66%% en Grammarly)")
    ap.add_argument("--maximo", type=int, default=400, help="palabras maximas por oracion unida")
    ap.add_argument("--idioma", choices=sorted(IDIOMAS), help="es o en (por defecto lo detecta)")
    args = ap.parse_args()

    texto = open(args.entrada, encoding="utf-8").read()
    conceptos = vf.cargar_conceptos(args.conceptos) if args.conceptos else []
    dudosas = []
    idioma = args.idioma or detectar_idioma(texto)
    unido = unir(texto, conceptos, args.proporcion, maximo=args.maximo, dudosas=dudosas, idioma=idioma)
    with open(args.salida, "w", encoding="utf-8") as fh:
        fh.write(unido)
    contar = lambda t: len(re.findall(r"[.!?](?:\s|$)", t))
    print(f"Escrito: {args.salida} ({contar(texto)} oraciones -> {contar(unido)}, idioma: {idioma})")
    if dudosas:
        print("REVISA: pasaron a minuscula y no aparecen asi en el texto; si son nombres "
              f"propios, agregalos a --conceptos: {', '.join(dudosas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
