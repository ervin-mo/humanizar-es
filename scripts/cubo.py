#!/usr/bin/env python3
"""El cubo: reescritura guiada por un detector, oracion por oracion.

Como un cubo Rubik: se gira una cara (una oracion), se mira si el cubo quedo mejor y
solo entonces se conserva el giro. "Mejor" lo decide el detector sustituto local
(scripts/sustituto.py). Es la idea de Adversarial Paraphrasing (NeurIPS 2025) con dos
diferencias: la guia es un detector abierto que corre en tu maquina, y cada giro pasa
filtros de contenido antes de competir.

En cada ronda:
  1. Un modelo de lenguaje propone N variantes de cada oracion (en paralelo).
  2. Se descartan las que pierden un concepto, una negacion, o meten un delator.
  3. Se mide el parrafo con cada variante y se conserva la que mas baja el puntaje.
  4. Si ninguna mejora, la oracion se queda como estaba.

No hay garantia de pasar ningun detector comercial. Verifica siempre el resultado en el
detector que te importa y relee el texto: el sustituto no entiende el sentido.

El generador es cualquier API compatible con OpenAI (chat/completions):
  export HUMANIZAR_API_KEY=...       # o guardala en ~/.config/humanizar-es/api_key
  export HUMANIZAR_API_URL=https://api.deepseek.com/chat/completions   # por defecto
  export HUMANIZAR_MODEL=deepseek-flash         # por defecto; varios separados por coma
  export HUMANIZAR_REVISOR=deepseek-flash       # modelo que veta cambios de sentido
  # cabeceras extra, separadas por ';'  (OpenCode Go exige x-opencode-session)
  export HUMANIZAR_API_HEADERS="x-opencode-session: {uuid}"   # {uuid} se reemplaza solo

Por defecto trabaja parrafo por parrafo (3 rondas cada uno), que es como se midio el
resultado de 100% -> 0% en Grammarly. Con --texto-completo gira todo el texto a la vez.

Uso:
  .venv/bin/python scripts/cubo.py original.txt -o humanizado.txt \\
      --conceptos conceptos.txt --registro academico
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estilo  # noqa: E402
import verificar_fidelidad as vf  # noqa: E402

PESO_RITMO = 4.0  # cuanto pesa la variacion de longitud de oracion frente al sustituto


def objetivo(sust, texto):
    """Mas bajo = mejor. Suma lo que mide el sustituto (eleccion de palabras) y resta
    la variacion de longitud de oracion (ritmo): los detectores miran las dos cosas."""
    longs = [len(o.split()) for o in estilo.oraciones(texto)]
    cv = 0.0
    if len(longs) > 1:
        media = sum(longs) / len(longs)
        cv = (sum((x - media) ** 2 for x in longs) / len(longs)) ** 0.5 / media
    return sust.puntuar(texto)["total"] - PESO_RITMO * cv


NEGACION = re.compile(rf"(?<!\w)({vf.NEGACIONES})(?!\w)")
MEJORA_MINIMA = 0.02

REGISTROS = {
    "academico": "ensayo académico: prosa culta y precisa, sin coloquialismos",
    "tecnico": "documentación técnica: precisa, clara, sin adornos",
    "marketing": "marketing y redes: cercano, con ritmo, se permite el tono coloquial",
    "email": "correo profesional: directo, cordial, sin rodeos",
}

PROMPT = """Eres un editor de estilo para español. Reescribe UNA oración de un texto para que suene escrita por una persona y no por un modelo de lenguaje.

Registro: {registro}.

Párrafo donde está (solo contexto, no lo reescribas):
<<<{parrafo}>>>

Oración a reescribir:
<<<{oracion}>>>

Da {n} versiones MUY distintas entre sí. Varía de verdad: cambia el verbo principal, el sujeto gramatical, el orden de las cláusulas y el vocabulario. Elige palabras menos previsibles pero naturales, como las elegiría alguien con voz propia. Algunas versiones pueden ser más cortas o partir la oración en dos; otras pueden unir ideas con un guion largo o con punto y coma.

Reglas:
- Conserva exactamente el sentido y cada dato.{obligatorios}
- Conserva todas las negaciones (no, ni, nunca, sin...): no inviertas nada.
- No uses: constituye, cabe destacar, en la actualidad, hoy en día, en última instancia, resulta + adjetivo, no solo... sino, no es X, es Y, lejos de, asimismo, no obstante, juega un papel.
- Vocabulario común y actual, el de una persona culta de hoy: nada rebuscado, arcaico ni ornamental (nada de «merced a», «señaladamente», «designio», «pecó de»).
- No agregues ideas, ejemplos ni opiniones que no estén en la oración.{repetidas}

Responde SOLO con JSON: {{"v": ["versión 1", "versión 2", ...]}}"""

PROMPT_REVISOR = """Eres un revisor exigente de traducciones de estilo en español. Cada par tiene una oración ORIGINAL y una NUEVA que debería decir exactamente lo mismo con otras palabras.

Rechaza la NUEVA si ocurre cualquiera de estas cosas:
1. Cambia el sentido, la fuerza o el matiz de una afirmación (por ejemplo, «se detiene ante X» → «halla su límite en X»).
2. Agrega información, ejemplos u opiniones que no están en la ORIGINAL.
3. Omite una idea de la ORIGINAL.
4. Usa un conector sin lógica («pese a ello» donde no hay oposición) o es circular o redundante.
5. Es agramatical, confusa o usa una palabra que un hablante culto no usaría ahí.

No rechaces por cambios de orden, de vocabulario o de estructura si el sentido se conserva.

{pares}

Responde SOLO con JSON: {{"rechazar": [números de los pares rechazados]}}"""


# ---------------------------------------------------------------- generador

ARCHIVO_CLAVE = os.path.expanduser("~/.config/humanizar-es/api_key")


def leer_clave():
    """La clave de la API: de HUMANIZAR_API_KEY o, si no esta, del archivo
    ~/.config/humanizar-es/api_key. El archivo sirve cuando un agente (Codex, por
    ejemplo) no les pasa a los comandos las variables con KEY en el nombre."""
    clave = os.environ.get("HUMANIZAR_API_KEY", "").strip()
    if not clave and os.path.isfile(ARCHIVO_CLAVE):
        with open(ARCHIVO_CLAVE, encoding="utf-8") as fh:
            clave = fh.read().strip()
    return clave


class Generador:
    def __init__(self, url, modelo, clave, cabeceras, temperatura, revisor=None):
        # varios modelos separados por coma: cada oracion recibe giros de todos ellos,
        # asi el texto final no lleva la huella de una sola familia
        self.modelos = [m.strip() for m in modelo.split(",") if m.strip()]
        self.revisor = revisor or self.modelos[0]
        self.url, self.clave = url, clave
        self.espera = float(os.environ.get("HUMANIZAR_ESPERA", "150"))  # segundos por llamada
        self.cabeceras = cabeceras
        self.temperatura = temperatura
        self.tokens = 0
        self.llamadas = 0
        self.cortadas = 0
        self.revisor_fallos = 0

    def variantes(self, oracion, parrafo, n, registro, obligatorios, repetidas=()):
        oblig = ""
        if obligatorios:
            oblig = "\n- Cada versión DEBE contener, tal cual: " + "; ".join(f"«{c}»" for c in obligatorios) + "."
        rep_txt = ""
        if repetidas:
            rep_txt = ("\n- El texto repite demasiado: " + ", ".join(f"«{r}»" for r in repetidas)
                       + ". Si aparece aquí y no es obligatoria, puedes cambiarla por una referencia"
                       " natural (un pronombre, «la disciplina»...), sin perder claridad.")
        por_modelo = max(1, -(-n // len(self.modelos)))
        prompt = PROMPT.format(registro=registro, parrafo=parrafo, oracion=oracion,
                               n=por_modelo, obligatorios=oblig, repetidas=rep_txt)
        # todas las familias a la vez: el tiempo de la oracion es el del modelo mas lento
        with cf.ThreadPoolExecutor(max_workers=len(self.modelos)) as ex:
            respuestas = ex.map(lambda m: self._llamar(m, prompt, self.temperatura), self.modelos)
        return [v for r in respuestas for v in extraer_variantes(r)]

    def revisar(self, pares):
        """pares: [(original, nueva)]. Devuelve el conjunto de indices rechazados.
        Si el revisor falla, rechaza todo: mejor no cambiar que cambiar el sentido."""
        texto = "\n\n".join(f"Par {i}:\nORIGINAL: {o}\nNUEVA: {n}" for i, (o, n) in enumerate(pares))
        contenido = self._llamar(self.revisor, PROMPT_REVISOR.format(pares=texto), 0.0)
        m = re.search(r"\{[^{}]*\}", contenido or "")
        try:
            return {int(i) for i in json.loads(m.group(0))["rechazar"]}
        except Exception:
            self.revisor_fallos += 1
            print(f"   (el revisor no dio una respuesta legible; se rechaza el lote: "
                  f"{(contenido or '')[:120]!r})", flush=True)
            return set(range(len(pares)))

    def _llamar(self, modelo, prompt, temperatura):
        cuerpo = json.dumps({
            "model": modelo,
            "temperature": temperatura,
            "max_tokens": 16000,  # los modelos que razonan gastan miles de tokens antes de contestar
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        # User-Agent propio: algunos proveedores (Cloudflare) bloquean el de urllib
        cab = {"Authorization": f"Bearer {self.clave}", "Content-Type": "application/json",
               "User-Agent": "humanizar-es/1.2", **self.cabeceras}
        for intento in range(2):  # pocos reintentos: un modelo colgado no debe congelar el bucle
            try:
                req = urllib.request.Request(self.url, data=cuerpo, headers=cab)
                with urllib.request.urlopen(req, timeout=self.espera) as r:
                    d = json.loads(r.read().decode())
                self.llamadas += 1
                self.tokens += d.get("usage", {}).get("total_tokens", 0)
                eleccion = d["choices"][0]
                if eleccion.get("finish_reason") == "length":
                    self.cortadas += 1
                return eleccion["message"]["content"] or ""
            except Exception as e:  # red, 5xx o JSON roto: reintentar con espera creciente
                if intento == 1:
                    print(f"   ({modelo} no respondio: {e})", flush=True)
                    return ""
                time.sleep(3)


def extraer_variantes(contenido):
    """Lee {"v": [...]}. Si la respuesta llego cortada, rescata las cadenas completas."""
    m = re.search(r"\{.*\}", contenido, re.S)
    v = []
    if m:
        try:
            v = json.loads(m.group(0)).get("v", [])
        except json.JSONDecodeError:
            v = []
    if not v:
        inicio = contenido.find("[")
        cadenas = re.findall(r'"((?:[^"\\]|\\.)*)"', contenido[inicio + 1:]) if inicio >= 0 else []
        v = [json.loads(f'"{c}"') for c in cadenas]
    return [re.sub(r"\s+", " ", x).strip() for x in v if isinstance(x, str) and len(x.split()) > 1]


# ---------------------------------------------------------------- filtros

def conceptos_en(texto, conceptos):
    t = vf.norm(texto)
    return [nombre for nombre, variantes in conceptos
            if any(vf.patron(v).search(t) for v in variantes)]


def motivo_rechazo(original, candidata, conceptos):
    """None si la candidata es aceptable; si no, la razon."""
    n_o, n_c = len(original.split()), len(candidata.split())
    if n_c < 0.4 * n_o or n_c > 1.8 * n_o + 4:
        return "longitud"
    faltan = set(conceptos_en(original, conceptos)) - set(conceptos_en(candidata, conceptos))
    if faltan:
        return "concepto"
    neg_o = set(NEGACION.findall(vf.norm(original)))
    neg_c = set(NEGACION.findall(vf.norm(candidata)))
    if neg_o - neg_c:
        return "negacion"
    if estilo.medir(candidata)["delatores_total"] > estilo.medir(original)["delatores_total"]:
        return "delator"
    return None


VACIAS = set("""cual cuales sobre entre desde hasta hacia porque aunque mientras cuando donde
tambien solo toda todo todas todos cada misma mismo otras otros nuestra nuestro puede
pueden siglo siglos ante tanto""".split())


def palabras_repetidas(texto, conceptos, minimo=6, cuantas=3):
    """Las palabras de contenido que mas se repiten, sin contar los conceptos protegidos."""
    protegidas = {vf.norm(w) for _, vs in conceptos for v in vs for w in v.split()}
    cuenta = {}
    for w in re.findall(r"[a-záéíóúñü]{6,}", texto.lower()):
        if w not in VACIAS and vf.norm(w) not in protegidas:
            cuenta[w] = cuenta.get(w, 0) + 1
    top = sorted(cuenta.items(), key=lambda kv: -kv[1])[:cuantas]
    return [w for w, c in top if c >= minimo]


# ---------------------------------------------------------------- estructura

def partir(texto):
    """Lista de parrafos; cada parrafo es una lista de oraciones. Los titulos (una
    linea sin punto final) se marcan para no tocarlos."""
    parrafos = []
    for p in estilo.parrafos(texto):
        es_titulo = len(p.split()) <= 12 and not re.search(r"[.!?…:]$", p)
        parrafos.append({"titulo": es_titulo, "oraciones": [p] if es_titulo else estilo.oraciones(p)})
    return parrafos


def unir(parrafos):
    return "\n\n".join(" ".join(p["oraciones"]) for p in parrafos) + "\n"


# ---------------------------------------------------------------- bucle

def correr(texto, gen, sust, conceptos, registro, n, rondas, hilos, salida=None, top=3):
    parrafos = partir(texto)
    repetidas = palabras_repetidas(texto, conceptos)
    inicial = objetivo(sust, texto)
    print(f"Puntaje inicial (mas bajo = mas humano): {inicial:.2f}", flush=True)
    if repetidas:
        print(f"Palabras repetidas que se pediran variar: {', '.join(repetidas)}", flush=True)
    print(flush=True)
    stats = {"propuestas": 0, "rechazos": {}, "aceptadas": 0, "vetadas": 0}

    for ronda in range(1, rondas + 1):
        tareas = [(pi, oi) for pi, p in enumerate(parrafos) if not p["titulo"]
                  for oi in range(len(p["oraciones"]))]
        print(f"Ronda {ronda}: pidiendo {n} variantes para {len(tareas)} oraciones "
              f"({', '.join(gen.modelos)})...", flush=True)

        def pedir(t):
            pi, oi = t
            o = parrafos[pi]["oraciones"][oi]
            return t, o, gen.variantes(o, " ".join(parrafos[pi]["oraciones"]), n,
                                       REGISTROS[registro], conceptos_en(o, conceptos), repetidas)

        with cf.ThreadPoolExecutor(max_workers=hilos) as ex:
            propuestas = list(ex.map(pedir, tareas))

        # A. ordenar los giros de cada oracion por puntaje (aplicando el mejor de forma
        #    provisional, para que las oraciones siguientes se midan en contexto)
        ranking = []
        for (pi, oi), original, cands in propuestas:
            p = parrafos[pi]["oraciones"]
            base = objetivo(sust, " ".join(p))
            buenas = []
            for c in dict.fromkeys(cands):
                stats["propuestas"] += 1
                motivo = motivo_rechazo(original, c, conceptos)
                if motivo:
                    stats["rechazos"][motivo] = stats["rechazos"].get(motivo, 0) + 1
                    continue
                puntaje = objetivo(sust, " ".join(p[:oi] + [c] + p[oi + 1:]))
                if puntaje < base - MEJORA_MINIMA:
                    buenas.append((puntaje, c))
            buenas = [c for _, c in sorted(buenas)[:top]]
            if buenas:
                p[oi] = buenas[0]
            ranking.append(((pi, oi), original, buenas))

        # B. el revisor de sentido veta los giros que cambian, inventan o no tienen logica
        pares = [(original, c) for _, original, buenas in ranking for c in buenas]
        vetados = set()
        lotes = [list(range(k, min(k + 15, len(pares)))) for k in range(0, len(pares), 15)]

        def revisar(lote):
            return {lote[i] for i in gen.revisar([pares[k] for k in lote]) if i < len(lote)}

        with cf.ThreadPoolExecutor(max_workers=hilos) as ex:
            for r in ex.map(revisar, lotes):
                vetados |= r

        # C. quedarse con el mejor giro aprobado de cada oracion
        cambios, k = 0, 0
        for (pi, oi), original, buenas in ranking:
            elegido = original
            for c in buenas:
                if k not in vetados and elegido == original:
                    elegido = c
                elif k in vetados:
                    stats["vetadas"] += 1
                k += 1
            parrafos[pi]["oraciones"][oi] = elegido
            if elegido != original:
                cambios += 1
                stats["aceptadas"] += 1

        total = objetivo(sust, unir(parrafos))
        print(f"  {cambios} giros conservados, {len(vetados)} vetados por el revisor · "
              f"puntaje del texto: {total:.2f}", flush=True)
        if salida and cambios:
            # guardar tras cada ronda: si el proceso se corta, no se pierde lo avanzado
            with open(salida, "w", encoding="utf-8") as fh:
                fh.write(unir(parrafos))
            print(f"  (guardado en {salida})", flush=True)
        if cambios == 0:
            break

    final = objetivo(sust, unir(parrafos))
    return unir(parrafos), inicial, final, stats


def por_parrafo(texto, gen, sust, conceptos, registro, n, rondas, hilos, salida):
    """Gira cada parrafo por separado, como en la prueba que paso los dos detectores
    (references/evidencia.md §4d). Cada parrafo recibe todas sus rondas antes de pasar
    al siguiente, y el resultado se guarda al terminar cada uno."""
    bloques = estilo.parrafos(texto)
    inicial = objetivo(sust, texto)
    stats = {"propuestas": 0, "rechazos": {}, "aceptadas": 0, "vetadas": 0}
    for i, b in enumerate(bloques):
        if partir(b)[0]["titulo"]:
            continue
        print(f"\n=== Parrafo {i + 1} de {len(bloques)} ===", flush=True)
        nuevo, _, _, st = correr(b, gen, sust, conceptos, registro, n, rondas, hilos)
        bloques[i] = nuevo.strip()
        stats["propuestas"] += st["propuestas"]
        stats["aceptadas"] += st["aceptadas"]
        stats["vetadas"] += st["vetadas"]
        for k, v in st["rechazos"].items():
            stats["rechazos"][k] = stats["rechazos"].get(k, 0) + v
        with open(salida, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(bloques) + "\n")
    resultado = "\n\n".join(bloques) + "\n"
    return resultado, inicial, objetivo(sust, resultado), stats


def main():
    ap = argparse.ArgumentParser(description="Reescritura guiada por detector, oracion por oracion.")
    ap.add_argument("original")
    ap.add_argument("-o", "--salida", required=True)
    ap.add_argument("--conceptos", help="archivo de conceptos (ver verificar_fidelidad.py)")
    ap.add_argument("--registro", choices=sorted(REGISTROS), default="academico")
    ap.add_argument("--variantes", type=int, default=8, help="giros por oracion (8)")
    ap.add_argument("--rondas", type=int, default=3, help="pasadas por bloque (3)")
    ap.add_argument("--texto-completo", action="store_true",
                    help="girar todo el texto a la vez en vez de parrafo por parrafo")
    ap.add_argument("--hilos", type=int, default=6, help="llamadas simultaneas al generador (6)")
    ap.add_argument("--temperatura", type=float, default=1.0)
    args = ap.parse_args()

    clave = leer_clave()
    if not clave:
        print(f"ERROR: falta la clave de la API: define HUMANIZAR_API_KEY o guardala en "
              f"{ARCHIVO_CLAVE} (ver la ayuda con -h)", file=sys.stderr)
        return 2
    cabeceras = {}
    for par in filter(None, os.environ.get("HUMANIZAR_API_HEADERS", "").split(";")):
        k, _, v = par.partition(":")
        cabeceras[k.strip()] = v.strip().replace("{uuid}", str(uuid.uuid4()))
    gen = Generador(
        os.environ.get("HUMANIZAR_API_URL", "https://api.deepseek.com/chat/completions"),
        os.environ.get("HUMANIZAR_MODEL", "deepseek-flash"),
        clave, cabeceras, args.temperatura,
        revisor=os.environ.get("HUMANIZAR_REVISOR"),
    )

    with open(args.original, encoding="utf-8") as fh:
        texto = fh.read()
    conceptos = vf.cargar_conceptos(args.conceptos) if args.conceptos else vf.extraer_conceptos(texto)

    from sustituto import Sustituto
    print("Cargando el detector sustituto...", flush=True)
    sust = Sustituto()  # CPU salvo HUMANIZAR_DISPOSITIVO; ver sustituto.py

    inicio = time.time()
    if args.texto_completo:
        resultado, inicial, final, stats = correr(
            texto, gen, sust, conceptos, args.registro, args.variantes, args.rondas, args.hilos,
            salida=args.salida)
    else:
        resultado, inicial, final, stats = por_parrafo(
            texto, gen, sust, conceptos, args.registro, args.variantes, args.rondas, args.hilos,
            args.salida)
    if gen.llamadas == 0:
        print("\nERROR: el generador no respondio ninguna vez; no escribo nada.", file=sys.stderr)
        print("Revisa HUMANIZAR_API_URL, HUMANIZAR_MODEL, la clave y las cabeceras.", file=sys.stderr)
        return 1
    with open(args.salida, "w", encoding="utf-8") as fh:
        fh.write(resultado)

    print(f"\nEscrito: {args.salida}")
    print(f"Puntaje del sustituto: {inicial:.2f} -> {final:.2f}  (mas bajo = mas humano)")
    print(f"Giros: {stats['propuestas']} propuestos, {stats['aceptadas']} conservados, "
          f"rechazos {stats['rechazos']}, vetados por el revisor {stats['vetadas']}")
    print(f"Generador: {gen.llamadas} llamadas, {gen.tokens} tokens, {gen.cortadas} respuestas cortadas"
          f" · {time.time() - inicio:.0f} s")
    if gen.cortadas:
        print("AVISO: hubo respuestas cortadas por limite de tokens; se rescato lo que venia completo.")
    print("\nSiguiente paso: python3 scripts/verificar_fidelidad.py ORIGINAL SALIDA --conceptos ...")
    print("y relee el texto. El sustituto no entiende el sentido; tú sí.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
