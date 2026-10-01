#!/usr/bin/env python3
"""La ruleta: cambia palabras sueltas por sinonimos, guiada por un detector.

Donde el cubo (scripts/cubo.py) reescribe oraciones enteras, la ruleta toca solo las
palabras que el detector ve como mas previsibles y las cambia por un sinonimo que encaje
en la oracion. La estructura queda igual, asi que el riesgo de cambiar el sentido es
mucho menor. Es la idea de Shi et al., "Red Teaming Language Model Detectors with
Language Models" (TACL 2023): sustituir palabras en contexto, guiandose por el detector.

Por parrafo:
  1. El detector local marca las palabras de contenido mas previsibles.
  2. Un modelo de lenguaje propone sinonimos para cada una, en su oracion.
  3. Se prueba cada sinonimo y se queda el que mas baja el puntaje del parrafo.
  4. Al final, un revisor compara cada oracion cambiada con la original y deshace las
     que cambiaron el sentido.

Usa la misma configuracion de API que cubo.py (HUMANIZAR_API_KEY, HUMANIZAR_API_URL,
HUMANIZAR_MODEL, HUMANIZAR_REVISOR, HUMANIZAR_API_HEADERS). Gasta pocas llamadas: una por
parrafo para los sinonimos y unas cuantas para el revisor. El trabajo pesado es local, en
CPU.

Uso:
  .venv/bin/python scripts/ruleta.py texto.txt -o salida.txt --conceptos conceptos.txt
"""
import argparse
import concurrent.futures as cf
import difflib
import json
import os
import re
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cubo  # noqa: E402
import estilo  # noqa: E402
import verificar_fidelidad as vf  # noqa: E402

MEJORA_MINIMA = 0.02

# Palabras funcionales: no tiene sentido buscarles sinonimo.
FUNCIONALES = set("""
aunque cuando donde mientras porque pues sino tambien tampoco todavia siempre nunca
entre hacia hasta desde sobre contra durante mediante segun ante bajo tras
este esta estos estas ese esa esos esas aquel aquella aquellos aquellas
cual cuales quien quienes cuyo cuya cuyos cuyas algo nada alguien nadie
todo toda todos todas otro otra otros otras mismo misma mismos mismas
tanto tanta tantos tantas mucho mucha muchos muchas poco poca pocos pocas
puede pueden podria debe deben debia habia hace hacer tiene tienen
como solo ademas entonces luego asi bien
""".split())

PROMPT_SINONIMOS = """Eres un editor de estilo para español. Para cada palabra marcada, propone sinónimos que puedan sustituirla EXACTAMENTE en su oración, sin cambiar el sentido.

Reglas:
- Misma categoría gramatical, mismo género, número, tiempo y persona: el sinónimo debe encajar tal cual, sin tocar nada más de la oración.
- Que conserve el sentido preciso en ESE contexto. Nada de antónimos ni de palabras más fuertes o más débiles.
- Prefiere palabras naturales y menos previsibles, como las elegiría alguien con voz propia. Nada rebuscado ni arcaico.
- Si no hay un buen sinónimo, deja la lista vacía.
- Registro: {registro}.

{lista}

Responde SOLO con JSON: {{"1": ["sinónimo", ...], "2": [...], ...}}"""


# ---------------------------------------------------------------- utilidades

def objetivo(sust, texto):
    return cubo.objetivo(sust, texto)


def palabras_protegidas(conceptos):
    return {vf.norm(w) for _, vs in conceptos for v in vs for w in v.rstrip("*").split()}


def con_mayuscula_como(original, nueva):
    return nueva[:1].upper() + nueva[1:] if original[:1].isupper() else nueva


def reemplazar(texto, inicio, fin, nueva):
    return texto[:inicio] + con_mayuscula_como(texto[inicio:fin], nueva) + texto[fin:]


def oracion_de(parrafo, pos):
    """La oracion del parrafo que contiene la posicion pos."""
    cursor = 0
    for o in estilo.oraciones(parrafo):
        i = parrafo.find(o, cursor)
        if i <= pos < i + len(o) + 1:
            return o
        cursor = i + len(o)
    return parrafo


def leer_sinonimos(contenido, n):
    m = re.search(r"\{.*\}", contenido or "", re.S)
    if not m:
        return {}
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    salida = {}
    for k, v in d.items():
        if str(k).isdigit() and 1 <= int(k) <= n and isinstance(v, list):
            salida[int(k)] = [s.strip() for s in v if isinstance(s, str) and s.strip()
                              and len(s.split()) <= 3]
    return salida


# ---------------------------------------------------------------- seleccion

def palabras_objetivo(sust, parrafo, protegidas, maximo):
    """Las palabras de contenido mas previsibles del parrafo: (inicio, fin, palabra)."""
    tokens = sust.previsibilidad(parrafo)
    candidatas = []
    for m in re.finditer(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", parrafo):
        w = m.group(0)
        if (len(w) < 5 or w[:1].isupper() or vf.norm(w) in FUNCIONALES
                or vf.norm(w) in protegidas):
            continue
        lps = [lp for a, b, lp in tokens if a < m.end() and b > m.start()]
        if lps:
            candidatas.append((sum(lps) / len(lps), m.start(), m.end(), w))
    candidatas.sort(reverse=True)  # logprob mas alto = mas previsible
    elegidas, vistas = [], set()
    for _, i, f, w in candidatas:
        if w.lower() not in vistas:
            vistas.add(w.lower())
            elegidas.append((i, f, w))
        if len(elegidas) >= maximo:
            break
    return elegidas


# ---------------------------------------------------------------- bucle

def girar_parrafo(sust, gen, parrafo, conceptos, protegidas, registro, maximo, stats):
    objetivos = palabras_objetivo(sust, parrafo, protegidas, maximo)
    if not objetivos:
        return parrafo
    lista = "\n".join(
        f"{k}. «{w}» en: «{oracion_de(parrafo, i)}»" for k, (i, f, w) in enumerate(objetivos, 1))
    contenido = gen._llamar(gen.modelos[0], PROMPT_SINONIMOS.format(registro=registro, lista=lista),
                            gen.temperatura)
    sinonimos = leer_sinonimos(contenido, len(objetivos))

    actual = parrafo
    base = objetivo(sust, actual)
    # de derecha a izquierda: un cambio no mueve las posiciones de los que faltan
    for k, (i, f, w) in sorted(enumerate(objetivos, 1), key=lambda x: -x[1][0]):
        mejor, mejor_puntaje = None, base - MEJORA_MINIMA
        oracion = oracion_de(actual, i)
        for s in sinonimos.get(k, []):
            if vf.norm(s) == vf.norm(w):
                continue
            stats["probados"] += 1
            prueba = reemplazar(actual, i, f, s)
            nueva = oracion_de(prueba, i)
            if cubo.motivo_rechazo(oracion, nueva, conceptos):
                stats["filtrados"] += 1
                continue
            puntaje = objetivo(sust, prueba)
            if puntaje < mejor_puntaje:
                mejor, mejor_puntaje = prueba, puntaje
        if mejor:
            actual, base = mejor, mejor_puntaje
            stats["cambios"] += 1
    return actual


def revisar(gen, originales, nuevos, hilos):
    """Revisa cada palabra cambiada POR SEPARADO (la oracion original contra la misma
    oracion con solo ese cambio) y conserva unicamente los cambios aprobados. Asi un
    sinonimo dudoso no arrastra a los buenos de su misma oracion."""
    cambios = []  # (parrafo, opcode, oracion original, oracion con solo ese cambio)
    for pi, (po, pn) in enumerate(zip(originales, nuevos)):
        ow, nw = po.split(" "), pn.split(" ")
        for op in difflib.SequenceMatcher(a=ow, b=nw, autojunk=False).get_opcodes():
            if op[0] == "equal":
                continue
            tag, i1, i2, j1, j2 = op
            solo = " ".join(ow[:i1] + nw[j1:j2] + ow[i2:])
            pos = len(" ".join(ow[:i1]))
            cambios.append((pi, op, oracion_de(po, pos), oracion_de(solo, pos)))
    pares = [(a, b) for _, _, a, b in cambios]
    lotes = [list(range(k, min(k + 5, len(pares)))) for k in range(0, len(pares), 5)]

    def uno(lote):
        fallos = gen.revisor_fallos
        r = gen.revisar([pares[k] for k in lote])
        if gen.revisor_fallos > fallos:  # un reintento antes de rechazar el lote entero
            r = gen.revisar([pares[k] for k in lote])
        return {lote[i] for i in r if i < len(lote)}

    vetados = set()
    with cf.ThreadPoolExecutor(max_workers=hilos) as ex:
        for r in ex.map(uno, lotes):
            vetados |= r

    aprobados = {(pi, op) for k, (pi, op, _, _) in enumerate(cambios) if k not in vetados}
    resultado = []
    for pi, (po, pn) in enumerate(zip(originales, nuevos)):
        ow, nw = po.split(" "), pn.split(" ")
        salida = []
        for op in difflib.SequenceMatcher(a=ow, b=nw, autojunk=False).get_opcodes():
            tag, i1, i2, j1, j2 = op
            salida += nw[j1:j2] if tag != "equal" and (pi, op) in aprobados else ow[i1:i2]
        resultado.append(" ".join(salida))
    return resultado, len(pares), len(vetados)


def main():
    ap = argparse.ArgumentParser(description="Cambia palabras por sinonimos, guiada por un detector.")
    ap.add_argument("original")
    ap.add_argument("-o", "--salida", required=True)
    ap.add_argument("--conceptos", help="archivo de conceptos (ver verificar_fidelidad.py)")
    ap.add_argument("--registro", choices=sorted(cubo.REGISTROS), default="academico")
    ap.add_argument("--palabras", type=int, default=8, help="palabras a probar por parrafo (8)")
    ap.add_argument("--rondas", type=int, default=2, help="pasadas completas (2)")
    ap.add_argument("--hilos", type=int, default=4, help="llamadas simultaneas al revisor (4)")
    args = ap.parse_args()

    clave = cubo.leer_clave()
    if not clave:
        print(f"ERROR: falta la clave de la API: define HUMANIZAR_API_KEY o guardala en "
              f"{cubo.ARCHIVO_CLAVE}", file=sys.stderr)
        return 2
    cabeceras = {}
    for par in filter(None, os.environ.get("HUMANIZAR_API_HEADERS", "").split(";")):
        k, _, v = par.partition(":")
        cabeceras[k.strip()] = v.strip().replace("{uuid}", str(uuid.uuid4()))
    gen = cubo.Generador(
        os.environ.get("HUMANIZAR_API_URL", "https://api.deepseek.com/chat/completions"),
        os.environ.get("HUMANIZAR_MODEL", "deepseek-flash"), clave, cabeceras, 0.8,
        revisor=os.environ.get("HUMANIZAR_REVISOR"))

    with open(args.original, encoding="utf-8") as fh:
        texto = fh.read()
    conceptos = vf.cargar_conceptos(args.conceptos) if args.conceptos else vf.extraer_conceptos(texto)
    protegidas = palabras_protegidas(conceptos)

    from sustituto import Sustituto
    print("Cargando el detector sustituto...", flush=True)
    sust = Sustituto()
    inicio = time.time()

    bloques = estilo.parrafos(texto)
    originales = list(bloques)
    inicial = objetivo(sust, "\n\n".join(bloques))
    print(f"Puntaje inicial (mas bajo = mas humano): {inicial:.2f}\n", flush=True)
    stats = {"probados": 0, "filtrados": 0, "cambios": 0}
    registro = cubo.REGISTROS[args.registro]

    for ronda in range(1, args.rondas + 1):
        antes = stats["cambios"]
        for pi, p in enumerate(bloques):
            es_titulo = len(p.split()) <= 12 and not re.search(r"[.!?…:]$", p)
            if not es_titulo:
                bloques[pi] = girar_parrafo(sust, gen, p, conceptos, protegidas, registro,
                                            args.palabras, stats)
        puntaje = objetivo(sust, "\n\n".join(bloques))
        print(f"Ronda {ronda}: {stats['cambios'] - antes} palabras cambiadas · puntaje: "
              f"{puntaje:.2f}", flush=True)
        if stats["cambios"] == antes:
            break

    with open(args.salida + ".sin-revisar.txt", "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(bloques) + "\n")  # para auditar lo que el revisor deshizo
    bloques, revisadas, vetadas = revisar(gen, originales, bloques, args.hilos)
    resultado = "\n\n".join(bloques) + "\n"
    final = objetivo(sust, resultado)
    if gen.llamadas == 0:
        print("\nERROR: el modelo de lenguaje no respondio; no escribo nada.", file=sys.stderr)
        return 1
    with open(args.salida, "w", encoding="utf-8") as fh:
        fh.write(resultado)

    print(f"\nEscrito: {args.salida}")
    print(f"Puntaje: {inicial:.2f} -> {final:.2f}  (mas bajo = mas humano)")
    print(f"Sinonimos probados {stats['probados']}, filtrados {stats['filtrados']}, "
          f"palabras cambiadas {stats['cambios']}")
    print(f"Revisor: {revisadas} cambios revisados uno por uno, {vetadas} deshechos"
          + (f" ({gen.revisor_fallos} lotes fallidos)" if gen.revisor_fallos else ""))
    print(f"Llamadas al modelo: {gen.llamadas} · {time.time() - inicio:.0f} s")
    print("\nRelee el resultado: un sinonimo puede ser correcto y aun asi sonar raro.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
