# humanizar-es

[![pruebas](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml/badge.svg)](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml)
[![licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)

Herramientas para que un texto en español escrito con IA **deje de detectarse como IA
sin cambiar lo que dice**, con resultados medidos en detectores reales en lugar de
promesas.

> *English summary at the end.*

---

## El resultado

Un párrafo de un ensayo generado con IA, medido a mano en dos detectores:

| Versión | Grammarly | CleverHumanizer |
|---|---|---|
| Original | 100% IA | — |
| **Pasado por el cubo** (`scripts/cubo.py`) | **0% IA** | **99% humano** |

Mismo contenido, mismos conceptos. Los textos están en
[`ejemplos/parrafo/`](ejemplos/parrafo/).

El camino hasta ahí también está medido, con el ensayo completo en Grammarly:

| Qué se intentó | Grammarly |
|---|---|
| El ensayo original | 100% IA |
| Reescrito por un modelo siguiendo reglas de estilo | 75% IA |
| Reescrito por un modelo, pulido y sin ninguna frase típica de IA | **100% IA** |
| El cubo, girando todo el ensayo de una vez | 39% IA |

**El descubrimiento central:** quitar las frases típicas de IA no sirve. Un detector como
Grammarly reconoce la prosa de un modelo aunque esté pulida. Lo que funciona es
**reescribir cada oración probando muchas variantes y quedarse con la que un detector
local ve menos como IA**: elegir midiendo, no adivinar.

Sé consciente del tamaño de la evidencia: el 100% → 0% es un párrafo; el ensayo completo,
girado de una vez, se quedó en 39%. Por eso el cubo ahora trabaja **párrafo por párrafo**,
como en la prueba que funcionó, aunque esa forma todavía no se ha medido con un ensayo
completo. Todo el detalle, con sus límites, en
[`references/evidencia.md`](references/evidencia.md).

---

## Cómo funciona

```
 tu texto ──► el cubo, oración por oración ──────────────────────────► texto nuevo
                │
                ├─ 1. un modelo de lenguaje propone 8 versiones de la oración
                ├─ 2. se descartan las que pierden un concepto, una negación
                │     o meten una frase típica de IA
                ├─ 3. un detector local (en tu computadora) mide cada versión
                │     y se queda la que menos parece IA
                └─ 4. un revisor veta las que cambian el sentido o inventan
```

Como un cubo Rubik: se gira una cara, se mira si el cubo quedó mejor y solo entonces se
conserva el giro.

- **El detector local** (`scripts/sustituto.py`) combina dos métodos publicados,
  [Binoculars](https://github.com/ahans30/Binoculars) y
  [Fast-DetectGPT](https://github.com/baoguangsheng/fast-detect-gpt), sobre un modelo Qwen2.5
  pequeño. Contra Grammarly ordenó los textos del benchmark con una correlación de 0.87.
  Gracias a él puedes probar miles de variantes sin gastar escaneos del detector real.
- **El generador** es cualquier API compatible con OpenAI: DeepSeek, OpenRouter, un
  modelo local con Ollama… Puedes poner varios de distintas familias.
- **La idea** viene de *Adversarial Paraphrasing* ([NeurIPS 2025](https://github.com/chengez/Adversarial-Paraphrasing)):
  parafrasear guiándose por un detector. Aquí el detector corre en tu máquina y cada
  giro pasa filtros de contenido antes de competir.

---

## Receta paso a paso

### 0. Lo que necesitas

- Python 3.9 o más reciente.
- ~3 GB de disco (las bibliotecas y el modelo local).
- Acceso a un modelo de lenguaje con API compatible con OpenAI (ver paso 2).

### 1. Instalar

```bash
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
```

La primera corrida descarga el modelo local (Qwen2.5-0.5B, ~2 GB) a `~/.cache/huggingface`.

### 2. Configurar el generador

```bash
export HUMANIZAR_API_KEY=tu-clave
export HUMANIZAR_API_URL=https://api.deepseek.com/chat/completions
export HUMANIZAR_MODEL=deepseek-chat
```

Otros proveedores, mismo formato:

| Proveedor | `HUMANIZAR_API_URL` | Nota |
|---|---|---|
| DeepSeek | `https://api.deepseek.com/chat/completions` | barato y bueno en español |
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` | cualquier modelo; evita los `:free` con textos privados |
| Ollama (local) | `http://localhost:11434/v1/chat/completions` | sin costo ni red; clave cualquiera; **no probado aquí** |
| OpenCode Go | `https://opencode.ai/zen/go/v1/chat/completions` | exige `HUMANIZAR_API_HEADERS="x-opencode-session: {uuid}"` (el `{uuid}` se reemplaza solo) |

Opcionales:

```bash
export HUMANIZAR_MODEL="deepseek-chat,otro-modelo"   # varias familias, se reparten las variantes
export HUMANIZAR_REVISOR=deepseek-chat              # quién veta los cambios de sentido
```

### 3. Anotar lo que no se puede perder

Un archivo de texto con los conceptos, uno por línea; variantes separadas por `|`:

```text
# conceptos.txt
Aristóteles | Estagirita
principio de no contradicción
Crítica de la razón pura
1781
```

Para arrancar puedes pedir una lista automática y completarla:
`python3 scripts/verificar_fidelidad.py mi-texto.txt --listar`

### 4. Pasar el texto por el cubo

```bash
.venv/bin/python scripts/cubo.py mi-texto.txt -o mi-texto-cubo.txt \
    --conceptos conceptos.txt --registro academico
```

`--registro` puede ser `academico`, `tecnico`, `marketing` o `email`. El cubo trabaja
párrafo por párrafo, 3 rondas cada uno, y guarda el avance al terminar cada párrafo.

### 5. Verificar y releer (no te lo saltes)

```bash
python3 scripts/verificar_fidelidad.py mi-texto.txt mi-texto-cubo.txt --conceptos conceptos.txt
python3 scripts/estilo.py mi-texto.txt mi-texto-cubo.txt
```

Y **lee el resultado oración por oración contra el original.** El detector local premia el
orden invertido y las palabras poco comunes: el texto puede quedar acartonado. En el
benchmark, antes de existir el revisor, el cubo llegó a cambiar el sentido de algunas
oraciones y a inventar un ejemplo. El revisor atrapó esos errores en una prueba (7 de 7),
pero la última palabra es tuya.

### 6. Medir en tu detector, con un control

Pega en el detector que te importa el resultado **y un texto que tú escribiste sin IA**,
del mismo tipo. Si tu texto humano también sale como IA, ese detector no está midiendo
y su número sobre el otro no significa nada.

### Opcional: calibrar el detector local contra el tuyo

Si mides varios textos en tu detector, anótalos así y comprueba que el detector local los
ordena igual (1.0 es perfecto):

```bash
printf 'original.txt\t100\nversion-a.txt\t75\nversion-b.txt\t40\n' > etiquetas.tsv
.venv/bin/python scripts/calibrar.py etiquetas.tsv
```

### Opcional: la ruleta de palabras

`scripts/ruleta.py` cambia solo palabras sueltas por sinónimos, guiada por el mismo
detector (la idea de [Shi et al., TACL 2023](https://arxiv.org/abs/2305.19713)). Es más
conservadora con el sentido y mucho más barata (≈3 llamadas por texto). En el benchmark
convenció a CleverHumanizer (76% humano) pero **no a Grammarly** (siguió en 100%), y
después del cubo no aportó. Úsala si tu detector se parece al primero.

---

## Costos y tiempos (medidos)

| | Cubo, párrafo de 120 palabras | Cubo, ensayo de 725 palabras |
|---|---|---|
| Llamadas al generador | ~12 | ~75 |
| Tokens del generador | ~90 mil | ~500 mil |
| Tiempo | ~5 min | ~20–35 min |
| CPU | ligera | ligera |

El tiempo es casi todo espera al generador. Con un modelo que «razona» antes de contestar,
cada llamada gasta miles de tokens.

**Corre en CPU por defecto.** En Mac, `HUMANIZAR_DISPOSITIVO=mps` usa la GPU y es mucho
más rápido, pero traba la pantalla mientras corre: úsalo solo si no estás usando la
computadora.

---

## Sin instalar nada: medir y verificar

Dos herramientas usan solo la biblioteca estándar de Python:

```bash
python3 scripts/estilo.py mi-texto.txt              # qué delata a tu texto
python3 scripts/estilo.py original.txt reescrito.txt
python3 scripts/verificar_fidelidad.py original.txt reescrito.txt --conceptos conceptos.txt
```

`estilo.py` mide qué tan pareja es la longitud de las oraciones y encuentra frases típicas
de IA con ejemplos del texto:

```
                                      00-original.txt 01-reglas-estil…
variación de oración (CV)  ↑                     0.36             0.53
% oraciones de ≤8 palabras  ↑                       0               13
delatores encontrados  ↓                            9                3

Delatores en 00-original.txt:
   1× constituye / se erige como             «constituye»
   1× no solo ... sino                       «no solo sobrevive, sino»
   1× lejos de (reducirse / ser)             «Lejos de reducirse»
   ...
```

Útil para encontrar marcas concretas. **No predice a los detectores comerciales**: una
versión con cero frases típicas sacó 100% en Grammarly.

`verificar_fidelidad.py` comprueba que los conceptos del original sigan en la versión
nueva, sale con código `1` si falta alguno y lista las negaciones que desaparecieron (el
error más peligroso: «principio de *no* contradicción» → «principio de contradicción»).

---

## Como skill para tu agente

`SKILL.md` sigue el formato abierto de *Agent Skills* (un `SKILL.md` con `name` y
`description`), así que funciona en cualquier agente que lo lea. Le pides «humaniza este
texto» y el agente arma la lista de conceptos, corre el cubo, verifica el contenido y
relee el resultado contigo.

| Agente | Dónde busca skills | ¿Lo cubre `./install.sh`? |
|---|---|---|
| Claude Code | `~/.claude/skills` | sí |
| Codex | `~/.agents/skills`, `~/.codex/skills` | sí |
| OpenCode | `~/.agents/skills`, `~/.claude/skills`, `~/.config/opencode/skills` | sí |
| Antigravity (`agy`) | `~/.agents/skills`, `~/.gemini/config/skills` | sí |
| DeepSeek Harness (`dsh`) | `~/.agents/skills`, `~/.dsh/skills` | sí |
| Gemini CLI | `~/.gemini/skills` | con `--agente gemini` |

```bash
./install.sh                    # ~/.claude/skills y ~/.agents/skills: cubre a todos los de arriba
./install.sh --agente codex     # solo uno: claude, codex, opencode, antigravity, dsh, gemini, agents
./install.sh --destino RUTA     # otra carpeta de skills (crea RUTA/humanizar-es)
./install.sh --symlink          # enlaza en vez de copiar
./install.sh --desinstalar      # quitarla de los mismos destinos
```

Para usar el cubo desde la skill, instálala con **`--symlink`**: así la skill usa el
`.venv` que creaste en el repo (paso 1 de la receta). Con una copia, el agente te
propondrá crear otro `.venv` dentro de la carpeta de la skill.

La guía de reescritura manual (12 palancas, por registro) está en
[`references/tecnicas.md`](references/tecnicas.md). Sirve para entender qué delata a un
texto, pero por sí sola llegó a 75% en Grammarly: para pasar el detector, usa el cubo.

---

## Herramientas

| Script | Requiere | Para qué |
|---|---|---|
| `scripts/cubo.py` | `.venv` + una API de modelo | **la reescritura guiada por detector** |
| `scripts/ruleta.py` | `.venv` + una API de modelo | sinónimos guiados por detector (opcional) |
| `scripts/sustituto.py` | `.venv` | el detector local; también puntúa textos sueltos |
| `scripts/calibrar.py` | `.venv` | qué tan bien predice el detector local a TU detector |
| `scripts/verificar_fidelidad.py` | Python | que no se pierda contenido |
| `scripts/estilo.py` | Python | regularidad y frases típicas de IA |
| `scripts/detect_local.py` | `.venv` | perplejidad y burstiness |
| `scripts/medir.sh` | Python | corre los medidores disponibles |
| `scripts/score-*.sh` | [ego lite](https://lite.ego.app/) (macOS) | automatiza ZeroGPT, GPTZero y Grammarly |
| `scripts/cadena_llm.py` | una API de modelo | el método descartado (cadena de traducción), para reproducirlo |

Trampas de cada detector web (anuncios que bloquean el clic, porcentajes que no son el
score, límites de uso): [`references/detectores.md`](references/detectores.md).

---

## Límites

1. **Un párrafo pasó los dos detectores; el ensayo completo todavía no se ha medido con
   el modo párrafo por párrafo.** Girado de una vez, se quedó en 39% en Grammarly y ~80%
   IA en CleverHumanizer.
2. **Un solo texto de prueba**, académico. No sabemos cuánto se generaliza a marketing,
   correos o textos técnicos.
3. **Los detectores cambian.** Lo que hoy pasa puede no pasar mañana, y un detector puede
   cambiar de opinión sobre el mismo texto el mismo día (le pasó a GPTZero).
4. **Los detectores marcan texto humano.** Un artículo de Wikipedia de 2014 sacó 46.5% en
   ZeroGPT.
5. **El texto puede quedar acartonado.** El detector local premia lo poco común. Relee.
6. **Analizar varios documentos del mismo autor** revela patrones que un documento suelto
   no muestra; humanizar uno no protege de eso.

## Uso responsable

Pensado para texto que firmas y del que respondes: contenido de marca, marketing,
documentación, correos, borradores que escribiste con ayuda de IA. **No lo uses para
entregar como propio un trabajo evaluado donde el uso de IA está prohibido o debe
declararse.** Ahí el problema no es técnico, es de honestidad académica, y ninguna
reescritura lo resuelve.

---

## Estructura

```
humanizar-es/
├── scripts/              el cubo, la ruleta, el detector local y los medidores
├── ejemplos/             el ensayo de prueba, sus versiones medidas y 2 controles humanos
│   └── parrafo/          el párrafo que pasó los dos detectores
├── references/
│   ├── evidencia.md      todas las mediciones, la literatura y los límites
│   ├── detectores.md     cómo medir con cada detector y sus trampas
│   ├── tecnicas.md       la guía de reescritura manual
│   └── checklist.md      control de calidad antes de entregar
├── tests/                pruebas automáticas (sin red ni modelos)
├── SKILL.md              la skill para agentes
└── install.sh            instala la skill
```

## Contribuir

Lo que más falta es **evidencia**: el modo párrafo por párrafo medido en ensayos completos,
y más textos de otros registros (marketing, técnico, correos) con un control humano cada
uno. Si mides algo, abre un PR con los textos y los números en `references/evidencia.md`.

```bash
python3 -m unittest discover -s tests -v    # antes de abrir un PR
```

## Licencia

Código y documentación: [MIT](LICENSE). El control de Wikipedia
(`ejemplos/controles/control-wikipedia-metafisica-2014.txt`) es de sus autores bajo
CC BY-SA 3.0; detalle en [`ejemplos/controles/LEEME.md`](ejemplos/controles/LEEME.md).

---

## English summary

Tools to make AI-written Spanish text stop being flagged as AI **without changing what it
says**. The core is `scripts/cubo.py`: for every sentence, a language model proposes
variants, filters drop the ones that lose a key concept or a negation, a local detector
(Binoculars + Fast-DetectGPT on a small Qwen2.5 model) keeps the one that looks least
machine-written, and a reviewer model vetoes changes of meaning. On a paragraph from a
test essay it went from 100% AI to 0% on Grammarly and 99% human on CleverHumanizer, with
all content preserved. Removing typical "AI phrases" alone did not work (a polished
rewrite still scored 100%). The evidence is small (one essay, one paragraph measured by
hand), every number is in `references/evidencia.md`, and the tool is not meant for passing
off graded work.
