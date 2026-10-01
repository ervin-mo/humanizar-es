# humanizar-es

[![pruebas](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml/badge.svg)](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml)
[![licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)

Herramientas para que un texto en español escrito con IA **deje de detectarse como IA
sin cambiar lo que dice**, con resultados medidos en detectores reales en lugar de
promesas. Corre en tu computadora, sin API y sin costo.

> *English summary at the end.*

---

## El resultado

Un ensayo completo de 1,150 palabras generado con IA, medido a mano en dos detectores:

| Versión | Grammarly | CleverHumanizer | Tiempo | Costo |
|---|---|---|---|---|
| Reescrito por un modelo de chat (el cubo) | 67% IA | 80% IA | 46 min | API |
| Reescrito por un modelo base local (`hip.py`) | 77% IA | 81% IA | 4 min | $0 |
| **`hip.py` + `ensuciar.py`** | **8% IA** | **95% humano**\* | **4 min** | **$0** |

\* El 95% de CleverHumanizer se midió con la variante que además tenía errores de
ortografía (12% en Grammarly). La receta de abajo **no mete errores de ortografía**:
solo imperfecciones de redacción, y en Grammarly le fue mejor.

Mismo contenido: los 38 conceptos del original siguen ahí.

**Los dos descubrimientos:**

1. **Los detectores reconocen la huella del entrenamiento de chat, no «la IA».** Cualquier
   modelo de chat que reescriba (DeepSeek, GPT, Claude, Kimi…) deja esa huella. El texto
   de un modelo **base**, sin entrenamiento de chat, les parece humano
   ([Xu et al. 2026](https://arxiv.org/abs/2605.19516)).
2. **Los detectores castigan el texto demasiado limpio.** Comas de manual, una oración por
   idea, ritmo parejo. Comerse algunas comas y pegar algunas oraciones con coma, como
   hace cualquiera que escribe rápido, bajó Grammarly de 77% a 8%, sin tocar la
   ortografía.

Lo que **no** funcionó, medido: quitar las frases típicas de IA (siguió en 100%), cambiar
de modelo de chat, reescribir palabra por palabra y reorganizar el ensayo a mano. Todo el
detalle en [`references/evidencia.md`](references/evidencia.md).

---

## Cómo funciona

```
 tu texto ──► hip.py, párrafo por párrafo ──► ensuciar.py ──► texto final
               │                                 │
               ├─ un modelo base local            ├─ se come algunas comas
               │  (Qwen3-4B + adaptador HIP)      ├─ pega algunas oraciones con coma
               │  reescribe cada párrafo          └─ nunca toca la ortografía
               └─ si un párrafo pierde un concepto,
                  se reintenta; si no hay forma,
                  queda el original
```

- **HIP** (*Humanization by Iterative Paraphrasing*) es un adaptador publicado por
  [Xu et al.](https://github.com/YixuanEvenXu/humanization-by-iterative-paraphrasing)
  (código MIT, adaptador Apache-2.0) que convierte a Qwen3-4B-Base en un parafraseador.
  Se entrenó en inglés; `hip.py` le da las dos primeras palabras de cada párrafo para que
  siga en español. Una sola pasada: con más, el texto se aleja del sentido.
- **`ensuciar.py`** no usa ningún modelo: es un script determinista. Misma semilla, mismo
  resultado.

---

## Receta paso a paso

### 0. Lo que necesitas

- Python 3.9 o más reciente, git y [llama.cpp](https://github.com/ggml-org/llama.cpp)
  (en Mac: `brew install llama.cpp`).
- ~9 GB de disco: ~3 GB de bibliotecas y ~5.5 GB del modelo.
- Una computadora con 16 GB de RAM. Corre en CPU; no hace falta GPU.

### 1. Instalar (una sola vez)

```bash
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
./scripts/instalar_hip.sh        # descarga el modelo a ~/.cache/humanizar-es/hip
```

### 2. Anotar lo que no se puede perder

Un archivo de texto con los conceptos, uno por línea; variantes separadas por `|`; con `*`
al final, cuenta cualquier palabra que empiece así:

```text
# conceptos.txt
Aristóteles | Estagirita
principio de no contradicción
derrumbe*
1781
```

Para arrancar puedes pedir una lista automática y completarla:
`python3 scripts/verificar_fidelidad.py mi-texto.txt --listar`

### 3. Reescribir con el modelo local

```bash
.venv/bin/python scripts/hip.py mi-texto.txt -o reescrito.txt --conceptos conceptos.txt
```

Unos 30 segundos por párrafo en una Mac M4. Guarda el avance tras cada párrafo y avisa
cuáles dejó como el original.

### 4. Ensuciar la redacción

```bash
python3 scripts/ensuciar.py reescrito.txt -o final.txt --conceptos conceptos.txt
```

Por defecto usa el nivel `extra`, el medido (8% en Grammarly), y **no toca la
ortografía**. Hay `ligero`, `medio` y `fuerte` si prefieres menos. `--semilla N` da otra
variante. `--ortografia` además quita acentos y mete erratas de dedo: baja más en algunos
detectores, pero son errores que se notan.

### 5. Verificar y releer (no te lo saltes)

```bash
python3 scripts/verificar_fidelidad.py mi-texto.txt final.txt --conceptos conceptos.txt
```

Y **lee el resultado contra el original.** El modelo local a veces cambia un detalle: en la
prueba puso «lavan los platos» donde decía «limpian», y «agencias extranjeras» donde decía
«foráneas». Corrige esos detalles a mano; no le pidas a otro modelo de chat que lo arregle,
porque le devuelve la huella al texto.

### 6. Medir en tu detector, con un control

Pega en el detector que te importa el resultado **y un texto que tú escribiste sin IA**,
del mismo tipo. Si tu texto humano también sale como IA, ese detector no está midiendo
y su número sobre el otro no significa nada.

---

## Alternativa: el cubo (con API)

Si no puedes correr el modelo local, `scripts/cubo.py` reescribe oración por oración con
cualquier API compatible con OpenAI y se queda con la variante que un detector local
(Binoculars + Fast-DetectGPT sobre Qwen2.5-0.5B) ve menos como IA. Un revisor veta las que
cambian el sentido. Es la idea de *Adversarial Paraphrasing*
([NeurIPS 2025](https://github.com/chengez/Adversarial-Paraphrasing)).

Con el ensayo completo sacó 67% en Grammarly solo y **4% seguido de `ensuciar.py`** (esa
medición fue con la variante con errores de ortografía). Pero tardó 46 minutos, contra 4 de
`hip.py`.

```bash
export HUMANIZAR_API_KEY=tu-clave
export HUMANIZAR_API_URL=https://api.deepseek.com/chat/completions
export HUMANIZAR_MODEL=deepseek-flash
.venv/bin/python scripts/cubo.py mi-texto.txt -o cubo.txt --conceptos conceptos.txt --registro academico
python3 scripts/ensuciar.py cubo.txt -o final.txt --conceptos conceptos.txt
```

Si usas el cubo a través de un agente como Codex, guarda la clave en un archivo privado en
lugar de exportarla: algunos agentes no les pasan a los comandos las variables con «KEY» en
el nombre.

```bash
mkdir -p ~/.config/humanizar-es && chmod 700 ~/.config/humanizar-es
printf '%s' 'tu-clave' > ~/.config/humanizar-es/api_key && chmod 600 ~/.config/humanizar-es/api_key
```

Los nombres de los modelos cambian con el tiempo (DeepSeek retiró `deepseek-chat` en julio
de 2026). Para ver los vigentes, sin gastar saldo:
`curl -s https://api.deepseek.com/models -H "Authorization: Bearer $HUMANIZAR_API_KEY"`

| Proveedor | `HUMANIZAR_API_URL` | Nota |
|---|---|---|
| DeepSeek | `https://api.deepseek.com/chat/completions` | barato y bueno en español |
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` | cualquier modelo; evita los `:free` con textos privados |
| Ollama (local) | `http://localhost:11434/v1/chat/completions` | sin costo ni red; clave cualquiera; **no probado aquí** |
| OpenCode Go | `https://opencode.ai/zen/go/v1/chat/completions` | exige `HUMANIZAR_API_HEADERS="x-opencode-session: {uuid}"` (el `{uuid}` se reemplaza solo) |

`HUMANIZAR_REVISOR` elige quién veta los cambios de sentido. `scripts/calibrar.py`
comprueba qué tan bien predice el detector local a tu detector, y `scripts/ruleta.py`
cambia solo palabras sueltas (no movió a Grammarly).

---

## Costos y tiempos (medidos, ensayo de 1,150 palabras)

| | `hip.py` + `ensuciar.py` | El cubo |
|---|---|---|
| Tiempo | ~4–7 min | ~46 min |
| Dinero | $0 | ~790 mil tokens de API |
| Red | solo para instalar | todo el tiempo |
| CPU | 4 hilos, prioridad baja | ligera |

**Todo corre en CPU.** En Mac, `HUMANIZAR_DISPOSITIVO=mps` hace que el detector local del
cubo use la GPU, pero traba la pantalla mientras corre.

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
texto» y el agente arma la lista de conceptos, corre `hip.py` y `ensuciar.py`, verifica
el contenido y relee el resultado contigo.

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

Instálala con **`--symlink`**: así la skill usa el `.venv` que creaste en el repo (paso 1
de la receta). Con una copia, el agente te propondrá crear otro `.venv` dentro de la
carpeta de la skill.

La guía de reescritura manual (12 palancas, por registro) está en
[`references/tecnicas.md`](references/tecnicas.md). Sirve para entender qué delata a un
texto, pero por sí sola llegó a 75% en Grammarly: para pasar el detector, usa la receta.

---

## Herramientas

| Script | Requiere | Para qué |
|---|---|---|
| `scripts/hip.py` | `.venv` + llama.cpp + `instalar_hip.sh` | **la reescritura con el modelo base local** |
| `scripts/ensuciar.py` | Python | **las imperfecciones de redacción** |
| `scripts/instalar_hip.sh` | llama.cpp, git | descarga y prepara el modelo local |
| `scripts/cubo.py` | `.venv` + una API de modelo | la reescritura guiada por detector (alternativa) |
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

1. **Un ensayo, una medición por versión.** La receta se midió con un ensayo de
   divulgación de 1,150 palabras; cada número es un escaneo a mano. No sabemos cuánto se
   generaliza a marketing, correos o textos técnicos.
2. **El 8% es de Grammarly.** La receta exacta (redacción `extra`, sin errores de
   ortografía) no se midió en CleverHumanizer; la variante con errores sacó 95% humano.
3. **El modelo local se entrenó en inglés.** Funciona en español con un truco (le damos
   las primeras palabras), pero a veces cambia un detalle o deja un párrafo sin tocar.
4. **Los detectores cambian.** Lo que hoy pasa puede no pasar mañana, y un detector puede
   cambiar de opinión sobre el mismo texto el mismo día (le pasó a GPTZero).
5. **Los detectores marcan texto humano.** Un artículo de Wikipedia de 2014 sacó 46.5% en
   ZeroGPT.
6. **La redacción queda menos pulida.** Es justo lo que la hace pasar: comas de menos y
   oraciones largas pegadas con coma. Si tu texto exige redacción impecable, este no es
   tu método.
7. **Analizar varios documentos del mismo autor** revela patrones que un documento suelto
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
├── scripts/              hip.py, ensuciar.py, el cubo, el detector local y los medidores
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

Lo que más falta es **evidencia**: la receta medida en más textos y otros registros
(marketing, técnico, correos), con un control humano cada uno, y en más detectores. Y un
adaptador HIP entrenado en español. Si mides algo, abre un PR con los textos y los números en `references/evidencia.md`.

```bash
python3 -m unittest discover -s tests -v    # antes de abrir un PR
```

## Licencia

Código y documentación: [MIT](LICENSE). `hip.py` usa Qwen3-4B-Base (Apache-2.0) y el
adaptador HIP de Xu et al. 2026 (Apache-2.0; su código, MIT), que se descargan aparte con
`instalar_hip.sh`. El control de Wikipedia
(`ejemplos/controles/control-wikipedia-metafisica-2014.txt`) es de sus autores bajo
CC BY-SA 3.0; detalle en [`ejemplos/controles/LEEME.md`](ejemplos/controles/LEEME.md).

---

## English summary

Tools to make AI-written Spanish text stop being flagged as AI **without changing what it
says**, running locally at no cost. The recipe: `scripts/hip.py` rewrites each paragraph
with a *base* model (Qwen3-4B-Base plus the HIP adapter from Xu et al. 2026, "Base Models
Look Human To AI Detectors"), seeded with the paragraph's first words so it stays in
Spanish; then `scripts/ensuciar.py` deterministically roughens the prose (drops some
commas, joins some sentences with commas) without touching spelling. On a 1,150-word
essay, Grammarly went from 77% AI (base-model rewrite alone) to 8%, in about 4 minutes on
CPU, with all 38 key concepts preserved. Swapping chat models, removing typical "AI
phrases", word-level synonym swaps and manual restructuring did not work. The evidence is
small (one essay, measured by hand); every number is in `references/evidencia.md`, and the
tool is not meant for passing off graded work.
