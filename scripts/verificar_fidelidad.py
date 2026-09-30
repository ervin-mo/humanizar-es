#!/usr/bin/env python3
"""Verifica que una reescritura conserva el contenido del original.

Humanizar cambia la superficie (ritmo, sintaxis, lexico). El contenido -nombres,
cifras, terminos tecnicos, negaciones- tiene que sobrevivir intacto. Este script
lo comprueba de dos formas:

  1. Conceptos: cada concepto del original debe aparecer en cada variante.
     Los conceptos salen de un archivo (--conceptos) o, si no se da ninguno, se
     extraen automaticamente del original (nombres propios, cifras, terminos
     entre parentesis o comillas).
  2. Negaciones: avisa si una construccion negativa del original ("no
     contradiccion", "nunca", "sin") desaparece en la variante. Es el error mas
     peligroso: invierte el sentido y ningun corrector lo detecta.

Solo usa la biblioteca estandar.

Uso:
  verificar_fidelidad.py original.txt variante.txt [variante2.txt ...]
  verificar_fidelidad.py original.txt variante.txt --conceptos conceptos.txt
  verificar_fidelidad.py original.txt --listar     # ver que conceptos extrae

Formato del archivo de conceptos (uno por linea, # para comentarios):
  Aristoteles | Estagirita        <- variantes separadas por |; basta con una
  principio de no contradiccion
  antinomia                       <- palabra completa; acepta el plural (antinomias)
  subatomic*                      <- con * compara por prefijo: subatomico, subatomica...
La comparacion ignora mayusculas y acentos.

Codigo de salida: 0 si todas las variantes conservan el 100% de los conceptos,
1 si alguna pierde alguno, 2 si hay un error de uso.
"""
import argparse
import re
import sys
import unicodedata

NEGACIONES = r"no|ni|nunca|jamas|tampoco|sin|nadie|nada|ningun|ninguna|ninguno"

# Palabras con mayuscula que no son nombres propios aunque no abran oracion.
NO_PROPIOS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o", "en",
    "a", "al", "por", "para", "con", "sin", "que", "se", "su", "sus", "lo", "es",
    "este", "esta", "estos", "estas", "ese", "esa", "como", "pero", "si", "no",
}


def norm(s):
    """minusculas y sin acentos, para comparar sin depender de la ortografia."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def patron(termino):
    """Palabra completa (con plural opcional), espacios flexibles. Con * al final,
    compara por prefijo. Asi "ser" no casa con "servicio"."""
    termino = norm(termino).strip()
    prefijo = termino.endswith("*")
    partes = [re.escape(p) for p in termino.rstrip("*").split()]
    fin = "" if prefijo else r"(?:e?s)?(?!\w)"
    return re.compile(r"(?<!\w)" + r"\s+".join(partes) + fin)


def cargar_conceptos(ruta):
    conceptos = []
    with open(ruta, encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.split("#", 1)[0].strip()
            if not linea:
                continue
            variantes = [v.strip() for v in linea.split("|") if v.strip()]
            conceptos.append((variantes[0], variantes))
    return conceptos


def extraer_conceptos(texto):
    """Extrae candidatos a contenido intocable. Es una heuristica: revisa la lista
    con --listar y, para trabajo serio, pasa un archivo con --conceptos."""
    encontrados = {}

    def agregar(t, alternativas=()):
        t = t.strip(" .,;:«»\"'()")
        palabras = t.split()
        while len(palabras) > 1 and norm(palabras[0]) in NO_PROPIOS:
            palabras = palabras[1:]  # "el noumeno" -> "noumeno"
        t = " ".join(palabras)
        if len(t) >= 3 and norm(t) not in encontrados:
            encontrados[norm(t)] = [t, *alternativas]

    # 1. nombres propios: palabras con mayuscula y sus uniones internas ("Tomas de
    #    Aquino"). La palabra que abre una oracion se descarta porque su mayuscula
    #    puede ser solo de posicion: un nombre que SOLO aparece al inicio de oracion
    #    no se detecta. Por eso la lista automatica es un punto de partida.
    mayus = r"[A-ZÁÉÍÓÚÑÜ][\wáéíóúñü]+"
    union = r"(?:\s+(?:de|del|la|las|los|y)\s+|\s+)"
    for m in re.finditer(rf"{mayus}(?:{union}{mayus})*", texto):
        inicio = m.start()
        previo = texto[:inicio].rstrip()
        abre_oracion = not previo or previo[-1] in ".!?¿¡:\n«\"—"
        palabras = m.group(0).split()
        if abre_oracion:
            palabras = palabras[1:]  # la primera lleva mayuscula por posicion
            while palabras and norm(palabras[0]) in NO_PROPIOS:
                palabras = palabras[1:]
        if palabras and norm(palabras[0]) not in NO_PROPIOS:
            # "Immanuel Kant" tambien vale como "Kant" en la variante
            alt = [palabras[-1]] if len(palabras) > 1 and palabras[-1][0].isupper() else []
            agregar(" ".join(palabras), alt)

    # 2. cifras, porcentajes y fechas
    for m in re.finditer(r"\d+(?:[.,]\d+)*\s*%?", texto):
        agregar(m.group(0))

    # 3. terminos entre parentesis o comillas angulares, si son cortos
    for m in re.finditer(r"\(([^()]{2,40})\)|«([^«»]{2,40})»", texto):
        agregar(m.group(1) or m.group(2))

    return [(v[0], v) for v in encontrados.values()]


def negaciones(texto):
    """Pares 'negacion + palabra siguiente' del texto, normalizados. Las comillas y
    parentesis se ignoran: 'no «contradiccion»' cuenta como 'no contradiccion'."""
    limpio = re.sub(r"[«»\"“”‘’()\[\]]", " ", norm(texto))
    return set(
        f"{a} {b}"
        for a, b in re.findall(rf"(?<!\w)({NEGACIONES})\s+(\w+)", limpio)
    )


def nombre_corto(ruta, ancho=18):
    base = ruta.replace("\\", "/").split("/")[-1]
    return base if len(base) <= ancho else base[: ancho - 1] + "…"


def main():
    ap = argparse.ArgumentParser(
        description="Verifica que una reescritura conserva el contenido del original."
    )
    ap.add_argument("original")
    ap.add_argument("variantes", nargs="*")
    ap.add_argument("--conceptos", help="archivo con un concepto por linea")
    ap.add_argument("--listar", action="store_true", help="muestra los conceptos y sale")
    args = ap.parse_args()

    try:
        textos = {}
        for f in [args.original] + args.variantes:
            with open(f, encoding="utf-8") as fh:
                textos[f] = fh.read()
        conceptos = (
            cargar_conceptos(args.conceptos)
            if args.conceptos
            else extraer_conceptos(textos[args.original])
        )
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    origen = "archivo " + args.conceptos if args.conceptos else "extraccion automatica"
    if args.listar or not args.variantes:
        print(f"{len(conceptos)} conceptos ({origen}):")
        if not args.conceptos:
            print("  Heuristica: no detecta nombres que solo aparecen al inicio de una oracion")
            print("  ni conceptos en minuscula. Copiala a un archivo, completala y usa --conceptos.")
        for nombre, variantes in conceptos:
            extra = f"   (o: {', '.join(variantes[1:])})" if len(variantes) > 1 else ""
            print(f"  - {nombre}{extra}")
        return 0

    if not conceptos:
        print("ERROR: no hay conceptos que verificar. Pasa --conceptos.", file=sys.stderr)
        return 2

    archivos = [args.original] + args.variantes
    normalizados = {f: norm(t) for f, t in textos.items()}
    print(f"Conceptos: {len(conceptos)} ({origen})\n")
    print(f"{'concepto':<30} " + " ".join(f"{nombre_corto(f):>18}" for f in archivos))

    totales = {f: 0 for f in archivos}
    perdidos = {f: [] for f in archivos}
    for nombre, variantes in conceptos:
        pats = [patron(v) for v in variantes]
        fila = []
        for f in archivos:
            hit = any(p.search(normalizados[f]) for p in pats)
            totales[f] += hit
            if not hit:
                perdidos[f].append(nombre)
            fila.append("ok" if hit else "PERDIDO")
        print(f"{nombre[:30]:<30} " + " ".join(f"{v:>18}" for v in fila))

    print("\nRESUMEN de fidelidad:")
    fallo = False
    for f in archivos:
        n = totales[f]
        pct = 100 * n / len(conceptos)
        marca = "" if n == len(conceptos) else "   <-- revisar"
        print(f"  {nombre_corto(f, 30):<30} {n}/{len(conceptos)} = {pct:.0f}%{marca}")
        if f != args.original and n < len(conceptos):
            fallo = True

    if totales[args.original] < len(conceptos):
        fallo = True
        print(
            "\nERROR: el ORIGINAL no contiene todos los conceptos. La lista no corresponde"
            " a este texto (o una variante esta mal escrita); corrigela."
        )

    neg_original = negaciones(textos[args.original])
    avisos = []
    for f in args.variantes:
        faltan = sorted(neg_original - negaciones(textos[f]))
        if faltan:
            avisos.append((f, faltan))
    if avisos:
        print("\nNEGACIONES del original que ya no aparecen igual (revisar a mano):")
        print("  Muchas son reformulaciones legitimas. Busca las que cambian el sentido,")
        print("  como 'principio de no contradiccion' -> 'principio de contradiccion'.")
        for f, faltan in avisos:
            print(f"  {nombre_corto(f, 30)}: " + ", ".join(f"«{x}»" for x in faltan))

    return 1 if fallo else 0


if __name__ == "__main__":
    sys.exit(main())
