#!/usr/bin/env python3
"""Mete imperfecciones de persona que escribe rapido: sin ningun modelo, sin red.

Grammarly y CleverHumanizer castigan el texto demasiado limpio: comas de manual,
una oracion por idea, ritmo parejo. Aplicado despues de scripts/hip.py, el nivel
extra bajo un ensayo completo de 77% a 8% en Grammarly sin un solo error de
ortografia (references/evidencia.md §4e).

Que hace, siempre de forma reproducible (misma semilla, mismo resultado):
  - se come algunas comas
  - pega algunas oraciones con coma en vez de punto
  - deja algun espacio doble
Con --ortografia, ademas (apagado por defecto: son errores que se notan):
  - quita el acento a palabras comunes donde la gente suele omitirlo (mas, tambien, dia)
  - mete unas pocas erratas de dedo (dos letras volteadas)

Nunca toca nombres propios (palabras con mayuscula) ni los conceptos de --conceptos:
una errata en «Zinacantan» o «derrumbe» cambiaria el texto, no solo su apariencia.

uso:
  python3 scripts/ensuciar.py reescrito.txt -o final.txt --conceptos conceptos.txt
"""
import argparse
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verificar_fidelidad as vf  # noqa: E402

NIVELES = {"ligero": 0.5, "medio": 1.0, "fuerte": 2.0, "extra": 3.0}

# Palabras a las que se les suele caer el acento al teclear rapido.
SIN_ACENTO = {
    "más": "mas", "también": "tambien", "está": "esta", "están": "estan", "día": "dia",
    "días": "dias", "río": "rio", "ríos": "rios", "aún": "aun", "después": "despues",
    "así": "asi", "además": "ademas", "quizá": "quiza", "quizás": "quizas",
    "económica": "economica", "económico": "economico", "turísticos": "turisticos",
    "turística": "turistica", "teléfono": "telefono", "técnico": "tecnico",
    "técnica": "tecnica", "difícilmente": "dificilmente", "aquí": "aqui", "allí": "alli",
    "según": "segun", "rápido": "rapido", "tecnología": "tecnologia", "público": "publico",
    "último": "ultimo", "fácil": "facil", "difícil": "dificil", "práctico": "practico",
    "política": "politica", "energía": "energia", "música": "musica", "árbol": "arbol",
}


def palabras_protegidas(conceptos):
    """Raices normalizadas de los conceptos: una errata no puede caer en ellas."""
    raices = set()
    for _, variantes in conceptos:
        for v in variantes:
            for w in v.split():
                w = vf.norm(w.rstrip("*"))
                if len(w) >= 4:
                    raices.add(w)
    return raices


def protegida(palabra, raices):
    if palabra[:1].isupper():
        return True  # nombres propios y principio de oracion
    n = vf.norm(palabra)
    return any(n.startswith(r) or r.startswith(n) for r in raices)


def ensuciar(texto, nivel="medio", conceptos=(), semilla=7, ortografia=False):
    k = NIVELES[nivel] if isinstance(nivel, str) else float(nivel)
    rnd = random.Random(semilla)
    raices = palabras_protegidas(conceptos)

    def acento(m):
        w = m.group(0)
        sin = SIN_ACENTO.get(w.lower())
        if ortografia and sin and rnd.random() < min(0.95, 0.45 * k):
            return sin.capitalize() if w[0].isupper() else sin
        return w

    t = re.sub(r"\b\w+\b", acento, texto)
    # comas de menos: primero antes de conjunciones, luego cualquiera
    t = re.sub(r",(?= y | o | que | pero )",
               lambda m: "" if rnd.random() < min(0.95, 0.5 * k) else m.group(0), t)
    t = re.sub(r",", lambda m: "" if rnd.random() < 0.12 * k else ",", t)

    # oraciones pegadas con coma (nunca si la siguiente empieza con nombre propio protegido)
    def pegar(m):
        sig = m.group(1)
        if rnd.random() < 0.18 * k and not protegida(sig.lower(), raices) and len(sig) > 1:
            return ", " + sig[0].lower() + sig[1:]
        return m.group(0)
    t = re.sub(r"\. ([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b(?! [A-ZÁÉÍÓÚÑ])", pegar, t)

    # erratas de dedo: dos letras volteadas en palabras largas no protegidas
    candidatas = sorted({w for w in re.findall(r"\b[a-záéíóúñü]{8,}\b", t)
                         if not protegida(w, raices)})
    rnd.shuffle(candidatas)
    for w in candidatas[:int(4 * k) if ortografia else 0]:
        i = rnd.randrange(2, len(w) - 2)
        errata = w[:i] + w[i + 1] + w[i] + w[i + 2:]
        t = re.sub(rf"\b{re.escape(w)}\b", errata, t, count=1)

    # algun espacio doble
    t = re.sub(r" (?=\w)", lambda m: "  " if rnd.random() < 0.01 * k else " ", t)
    return t


def main():
    ap = argparse.ArgumentParser(description="Mete imperfecciones humanas en el texto, sin modelos.")
    ap.add_argument("entrada")
    ap.add_argument("-o", "--salida", required=True)
    ap.add_argument("--nivel", choices=NIVELES, default="extra",
                    help="cuanto ensuciar (extra: el medido con HIP, 8%% en Grammarly)")
    ap.add_argument("--conceptos", help="archivo de conceptos que no pueden llevar erratas")
    ap.add_argument("--semilla", type=int, default=7, help="otra semilla da otra variante")
    ap.add_argument("--ortografia", action="store_true",
                    help="tambien acentos caidos y erratas de dedo (se notan; apagado por defecto)")
    args = ap.parse_args()

    texto = open(args.entrada, encoding="utf-8").read()
    conceptos = vf.cargar_conceptos(args.conceptos) if args.conceptos else []
    sucio = ensuciar(texto, args.nivel, conceptos, args.semilla, args.ortografia)
    with open(args.salida, "w", encoding="utf-8") as fh:
        fh.write(sucio)

    antes, despues = texto.split(), sucio.split()
    cambios = sum(a != b for a, b in zip(antes, despues)) + abs(len(antes) - len(despues))
    print(f"Escrito: {args.salida} (nivel {args.nivel}, ~{cambios} palabras tocadas)")
    if conceptos:
        faltan = [c for c, _ in conceptos
                  if any(vf.patron(v).search(vf.norm(texto)) for v in dict(conceptos)[c])
                  and not any(vf.patron(v).search(vf.norm(sucio)) for v in dict(conceptos)[c])]
        if faltan:
            print(f"AVISO: se perdieron conceptos: {', '.join(faltan)}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
