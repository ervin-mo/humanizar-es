#!/usr/bin/env python3
"""EXPERIMENTO DESCARTADO. Se conserva solo para reproducir el benchmark.

Cadena de traduccion a idiomas distantes, inspirada en lynote-ai/humanize-text:
  ES -(reescritura LLM, temp 1.3)-> ZH -(reescritura LLM, temp 1.3)-> JA
     -(traduccion LLM, temp 0.3)-> FI -(traduccion LLM, temp 0.3)-> ES

Diferencia con el original: lynote-ai usa motores de traduccion automatica en los
dos ultimos saltos y parte del ingles. Aqui todos los saltos son LLM y se parte
del espanol. En el benchmark este metodo apenas bajo el score (98.5% -> 81.2% en
ZeroGPT) e invirtio un concepto ("principio de no contradiccion" -> "principio de
contradiccion"). Ver references/evidencia.md.

Habla con cualquier API compatible con OpenAI (chat/completions). Cuesta dinero:
cuatro llamadas por parrafo.

  export HUMANIZAR_API_KEY=...                       # obligatoria
  export HUMANIZAR_API_URL=https://api.deepseek.com/chat/completions   # por defecto
  export HUMANIZAR_MODEL=deepseek-chat               # por defecto
  python3 scripts/cadena_llm.py entrada.txt salida.txt
"""
import json
import os
import sys
import time
import urllib.request

URL = os.environ.get("HUMANIZAR_API_URL", "https://api.deepseek.com/chat/completions")
MODEL = os.environ.get("HUMANIZAR_MODEL", "deepseek-chat")


def call(key, messages, temperature, max_tokens=4000):
    body = json.dumps(
        {"model": MODEL, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    ).encode()
    req = urllib.request.Request(
        URL,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode())["choices"][0]["message"]["content"].strip()
        except Exception as e:  # red, 5xx, JSON inesperado: reintentar con espera creciente
            if intento == 3:
                raise
            print(f"   reintento ({e})", flush=True)
            time.sleep(5 * (intento + 1))


def salto(key, texto, idioma, reescribir, historial=None):
    if reescribir:
        sistema = (
            f"Eres un escritor nativo de {idioma}. Recibes un texto y lo REESCRIBES "
            f"integramente en {idioma}, con tu propio estilo y sintaxis nativa. "
            "Conserva todas las ideas, nombres propios, conceptos y datos: "
            "no agregues ni omitas informacion. No expliques nada, no uses markdown, "
            "no comentes. Devuelve unicamente el texto reescrito."
        )
    else:
        sistema = (
            f"Traduce el texto a {idioma} con maxima fidelidad. Conserva el sentido "
            "exacto, los nombres propios y los terminos tecnicos. No agregues ni omitas "
            "nada, no expliques, no comentes. Devuelve unicamente la traduccion."
        )
    msgs = [{"role": "system", "content": sistema}, *(historial or []), {"role": "user", "content": texto}]
    return call(key, msgs, temperature=1.3 if reescribir else 0.3)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    key = os.environ.get("HUMANIZAR_API_KEY")
    if not key:
        print("ERROR: define HUMANIZAR_API_KEY (ver la ayuda con -h)", file=sys.stderr)
        return 2
    origen, destino = sys.argv[1], sys.argv[2]
    with open(origen, encoding="utf-8") as f:
        parrafos = [p.strip() for p in f.read().split("\n") if p.strip()]

    salida = []
    for i, p in enumerate(parrafos):
        zh = salto(key, p, "chino mandarin", reescribir=True)
        ja = salto(key, zh, "japones", reescribir=True,
                   historial=[{"role": "user", "content": p}, {"role": "assistant", "content": zh}])
        fi = salto(key, ja, "fines", reescribir=False)
        es = salto(key, fi, "espanol", reescribir=False)
        salida.append(es)
        print(f"[{i + 1}/{len(parrafos)}] {len(p)}c -> zh {len(zh)}c -> ja {len(ja)}c "
              f"-> fi {len(fi)}c -> es {len(es)}c", flush=True)

    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n\n".join(salida) + "\n")
    print("escrito:", destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
