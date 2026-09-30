#!/usr/bin/env python3
"""Medidor de estilo sin dependencias: las senales de regularidad que delatan a un
texto generado, en numeros reproducibles.

No dice si un texto "es de IA". Mide lo que la guia de reescritura intenta mover:

  - variacion de longitud de oracion (desviacion y coeficiente de variacion)
  - tramos de oraciones seguidas con longitud parecida
  - variacion de longitud de parrafo y parrafos de una sola oracion
  - recursos que rompen la regularidad (guion largo, preguntas, punto y coma)
  - delatores del espanol generado ("cabe destacar", "no solo... sino", ...)

Solo usa la biblioteca estandar. Mismo texto, mismos numeros, siempre.

Uso:
  estilo.py texto.txt                   # informe de un texto
  estilo.py original.txt reescrito.txt  # tabla comparativa + delatores de cada uno
  estilo.py texto.txt --json            # salida para otros programas
"""
import argparse
import json
import re
import statistics
import sys

# (etiqueta, regex). Busqueda sin distinguir mayusculas. Ver references/tecnicas.md.
DELATORES = [
    ("constituye / se erige como", r"\bconstitu(?:ye|yen|y[oó]|yeron|[ií]a|[ií]an)\b|\bse erig(?:e|en|i[oó]|ieron)\b"),
    ("representa un(a)", r"\brepresent(?:a|an|[oó]|aron|aba|aban) (?:un|una)\b"),
    ("cabe destacar / señalar / mencionar", r"\bcabe (?:destacar|señalar|mencionar|resaltar)"),
    ("es importante / fundamental señalar", r"\bes (?:importante|fundamental|crucial|esencial) (?:señalar|destacar|mencionar|comprender|tener en cuenta)"),
    ("en la actualidad / hoy en día", r"\ben la actualidad\b|\bhoy en d[ií]a\b|\ben el mundo actual\b|\ben la era digital\b"),
    ("en última instancia / en definitiva", r"\ben [uú]ltima instancia\b|\ben definitiva\b"),
    ("resulta + adjetivo", r"\bresulta(?:n|ba|ban)? (?:indispensable|fundamental|fascinante|evidente|imperativo|imperativa|crucial|esencial)(?:e?s)?\b"),
    ("de manera / de forma + adjetivo", r"\bde (?:manera|forma) (?:significativa|implícita|implicita|integral|efectiva|notable)\b"),
    ("juega / desempeña un papel", r"\b(?:juega|juegan|jug[oó]|jugaron|desempe[nñ](?:a|an|[oó]|aron)) un papel\b"),
    ("un abanico / amplia gama / sinfín", r"\bun abanico de\b|\buna amplia gama de\b|\bun sinf[ií]n de\b"),
    ("sin duda alguna / indudablemente", r"\bsin duda alguna\b|\bindudablemente\b"),
    ("asimismo / no obstante", r"\basimismo\b|\bno obstante\b"),
    ("no solo ... sino", r"\bno s[oó]lo\b[^.?!]{0,120}?\bsino\b"),
    ("no es X, es Y", r"\bno es [^.,;:?!—]{1,40}(?:,|:|;| —|—)\s*es\b"),
    ("lejos de (reducirse / ser)", r"\blejos de (?:reducirse|ser|limitarse)\b"),
    ("todo esto nos lleva a", r"\btodo esto nos lleva\b"),
    ("gerundio de apertura", r"(?:^|[.!?]\s+)(?:Teniendo en cuenta|Considerando|Tomando en cuenta)\b"),
]


# Abreviaturas que terminan en punto sin cerrar la oracion.
ABREVIATURAS = (
    "a. C.", "d. C.", "a.C.", "d.C.", "p. ej.", "Sr.", "Sra.", "Srta.", "Dr.", "Dra.",
    "Lic.", "Ing.", "Prof.", "pág.", "págs.", "art.", "núm.", "cap.", "vol.", "ed.",
    "etc.", "aprox.", "fig.", "Ud.", "Uds.", "EE. UU.", "S. A.",
)
_MARCA = "\u2024"  # punto sustituto mientras se parte en oraciones


def oraciones(texto):
    plano = re.sub(r"\s+", " ", texto).strip()
    for abr in ABREVIATURAS:
        plano = plano.replace(abr, abr.replace(".", _MARCA))
    partes = re.split(r"(?<=[.!?…])\s+(?=[¿¡«\"(\[—A-ZÁÉÍÓÚÑ0-9])", plano)
    return [p.replace(_MARCA, ".") for p in partes if re.search(r"\w", p)]


def parrafos(texto):
    """Con lineas en blanco, esas separan parrafos (y los saltos simples son cortes
    de linea dentro del parrafo). Sin lineas en blanco, cada linea es un parrafo."""
    if re.search(r"\n\s*\n", texto):
        bloques = re.split(r"\n\s*\n", texto)
    else:
        bloques = texto.split("\n")
    return [re.sub(r"\s+", " ", b).strip() for b in bloques if b.strip()]


def palabras(s):
    return re.findall(r"[\wáéíóúüñÁÉÍÓÚÜÑ]+(?:[-'][\wáéíóúüñ]+)*", s)


def tramo_uniforme(longs, tolerancia=0.25):
    """Tramo mas largo de oraciones seguidas cuya longitud no se aleja mas de un
    25% de la media del tramo. Tres o mas seguidas es la huella tipica de la IA."""
    mejor = 1 if longs else 0
    for inicio in range(len(longs)):
        for fin in range(inicio + mejor + 1, len(longs) + 1):
            tramo = longs[inicio:fin]
            media = sum(tramo) / len(tramo)
            if all(abs(x - media) <= tolerancia * media for x in tramo):
                mejor = len(tramo)
    return mejor


def medir(texto):
    ors = oraciones(texto)
    longs = [len(palabras(o)) for o in ors] or [0]
    pars = parrafos(texto)
    ors_por_par = [len(oraciones(p)) for p in pars] or [0]
    pal_por_par = [len(palabras(p)) for p in pars] or [0]
    n_pal = len(palabras(texto))
    por_mil = lambda n: round(1000 * n / n_pal, 1) if n_pal else 0.0

    media = statistics.mean(longs)
    sd = statistics.pstdev(longs)
    delatores = []
    for etiqueta, rx in DELATORES:
        hallados = [m.group(0) for m in re.finditer(rx, texto, re.I | re.M)]
        if hallados:
            delatores.append({"delator": etiqueta, "veces": len(hallados), "ejemplo": hallados[0].strip()})

    return {
        "palabras": n_pal,
        "oraciones": len(ors),
        "palabras_por_oracion": round(media, 1),
        "sd_longitud_oracion": round(sd, 1),
        "cv_longitud_oracion": round(sd / media, 2) if media else 0.0,
        "oracion_min": min(longs),
        "oracion_max": max(longs),
        "pct_oraciones_cortas": round(100 * sum(l <= 8 for l in longs) / len(longs)),
        "pct_oraciones_largas": round(100 * sum(l >= 30 for l in longs) / len(longs)),
        "tramo_uniforme_max": tramo_uniforme(longs),
        "parrafos": len(pars),
        "cv_longitud_parrafo": round(statistics.pstdev(pal_por_par) / statistics.mean(pal_por_par), 2)
        if statistics.mean(pal_por_par)
        else 0.0,
        "parrafos_de_una_oracion": sum(n == 1 for n in ors_por_par),
        "guiones_largos_x1000": por_mil(texto.count("—")),
        "preguntas_x1000": por_mil(texto.count("?")),
        "punto_y_coma_x1000": por_mil(texto.count(";")),
        "delatores_total": sum(d["veces"] for d in delatores),
        "delatores": delatores,
    }


FILAS = [
    ("palabras", "palabras"),
    ("oraciones", "oraciones"),
    ("palabras_por_oracion", "palabras por oración (media)"),
    ("sd_longitud_oracion", "desviación de longitud de oración"),
    ("cv_longitud_oracion", "variación de oración (CV)  ↑"),
    ("oracion_min", "oración más corta (palabras)"),
    ("oracion_max", "oración más larga (palabras)"),
    ("pct_oraciones_cortas", "% oraciones de ≤8 palabras  ↑"),
    ("pct_oraciones_largas", "% oraciones de ≥30 palabras"),
    ("tramo_uniforme_max", "tramo de oraciones parejas  ↓"),
    ("parrafos", "párrafos"),
    ("cv_longitud_parrafo", "variación de párrafo (CV)  ↑"),
    ("parrafos_de_una_oracion", "párrafos de una oración"),
    ("guiones_largos_x1000", "guiones largos por 1000 pal."),
    ("preguntas_x1000", "preguntas por 1000 pal."),
    ("punto_y_coma_x1000", "punto y coma por 1000 pal."),
    ("delatores_total", "delatores encontrados  ↓"),
]


def nombre_corto(ruta, ancho=16):
    base = ruta.replace("\\", "/").split("/")[-1]
    return base if len(base) <= ancho else base[: ancho - 1] + "…"


def main():
    ap = argparse.ArgumentParser(description="Medidor de estilo sin dependencias.")
    ap.add_argument("archivos", nargs="+")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    args = ap.parse_args()

    resultados = {}
    for f in args.archivos:
        try:
            with open(f, encoding="utf-8") as fh:
                resultados[f] = medir(fh.read())
        except OSError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2

    if args.json:
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
        return 0

    print(f"{'':<36}" + "".join(f"{nombre_corto(f):>17}" for f in args.archivos))
    for clave, etiqueta in FILAS:
        print(f"{etiqueta:<36}" + "".join(f"{resultados[f][clave]:>17}" for f in args.archivos))
    print("\n↑ más alto suele ser más humano · ↓ más bajo suele ser más humano.")
    print("Son señales relativas: compáralas contra el original y contra un texto humano")
    print("del mismo registro, no contra un umbral absoluto.")

    for f in args.archivos:
        d = resultados[f]["delatores"]
        print(f"\nDelatores en {nombre_corto(f, 40)}:" + (" ninguno" if not d else ""))
        for x in d:
            print(f"  {x['veces']:>2}× {x['delator']:<38} «{x['ejemplo'][:60]}»")
    return 0


if __name__ == "__main__":
    sys.exit(main())
