# humanizar-es

[![pruebas](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml/badge.svg)](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml)
[![licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)

Herramientas para que un texto en español escrito con IA **deje de detectarse como IA
sin cambiar lo que dice**, con resultados medidos en detectores reales en lugar de
promesas. Corre en tu computadora, sin API y sin costo.

> *English summary at the end.*

---

## El resultado

Dos ensayos completos generados con IA, medidos a mano en Grammarly. La receta no mete
**ni un error de ortografía ni de puntuación**:

| Ensayo | Reescrito por el modelo local (`hip.py`) | **+ `unir.py`** |
|---|---|---|
| Turismo en Chiapas (1,150 palabras) | 77% IA | **0% IA** |
| Dragon Ball (930 palabras) | 84% IA | **10% IA**\* |

\* Con 16 correcciones de sentido hechas a mano antes de unir. Sin ellas, 8%.

Mismo contenido: los conceptos del original siguen ahí. Corre en tu computadora, en
unos 5 minutos, sin API y sin costo.

**Los dos descubrimientos:**

1. **Los detectores reconocen la huella del entrenamiento de chat, no «la IA».** Cualquier
   modelo de chat que reescriba (DeepSeek, GPT, Claude, Kimi…) deja esa huella. El texto
   de un modelo **base**, sin entrenamiento de chat, les parece humano
   ([Xu et al. 2026](https://arxiv.org/abs/2605.19516)).
2. **Grammarly reconoce el ritmo: oraciones de largo parejo, cada una con su punto.**
   Unir las oraciones de cada párrafo con «y», como escribe alguien de corrido, bajó el
   mismo texto de 84% a 8%. Medido cambio por cambio: los espacios dobles no movieron nada
   (84%), quitar comas bajó a 60%, pegar oraciones con coma a 54% y unir con «y» a 40%; unir
   todas, a 8%. Sobre el original sin reescribir, unir no basta (57%): hacen falta los dos
   pasos.

Lo que **no** funcionó, medido: quitar las frases típicas de IA (siguió en 100%), cambiar
de modelo de chat, reescribir palabra por palabra y reorganizar el ensayo a mano. Todo el
detalle en [`references/evidencia.md`](references/evidencia.md).

---

## Cómo funciona

```
 tu texto ──► hip.py ──► tú corriges detalles ──► unir.py ──► texto final
               │           (antes de unir)           │
               ├─ un modelo base local               └─ une las oraciones de cada
               │  (Qwen3-4B + adaptador HIP)            párrafo con «y» (o «, pero»);
               │  reescribe cada párrafo                no cambia ninguna otra palabra
               └─ si un párrafo pierde un concepto,
                  se reintenta; si no hay forma,
                  queda el original
```

- **HIP** (*Humanization by Iterative Paraphrasing*) es un adaptador publicado por
  [Xu et al.](https://github.com/YixuanEvenXu/humanization-by-iterative-paraphrasing)
  (código MIT, adaptador Apache-2.0) que convierte a Qwen3-4B-Base en un parafraseador.
  Se entrenó en inglés; `hip.py` le da las dos primeras palabras de cada párrafo para que
  siga en español. Una sola pasada: con más, el texto se aleja del sentido.
- **`unir.py`** no usa ningún modelo: es un script determinista. Respeta los nombres
  propios de tu lista de conceptos y avisa si bajó a minúscula alguna palabra dudosa.

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

### 4. Releer y corregir, ANTES de unir (no te lo saltes)

```bash
python3 scripts/verificar_fidelidad.py mi-texto.txt reescrito.txt --conceptos conceptos.txt
```

Y **lee la reescritura contra el original.** El modelo local a veces cambia un detalle
(«limpian» → «lavan los platos», «foráneas» → «extranjeras»), se equivoca de género
(«Para una niña» donde decía «los niños») o deja una errata («timido»). Corrige **solo la
palabra culpable**, a mano, y hazlo ahora: corregir después de unir le devolvió puntos a
Grammarly. No le pidas a un modelo de chat que lo arregle: le devuelve la huella.

### 5. Unir las oraciones

```bash
python3 scripts/unir.py reescrito.txt -o final.txt --conceptos conceptos.txt
```

Cada párrafo queda en una o dos oraciones largas encadenadas con «y». Si avisa de palabras
que bajó a minúscula, revisa que no sea un nombre propio y, si lo es, agrégalo a
`conceptos.txt`. Se lee como alguien que escribe de corrido: es justo lo que lo hace pasar.

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

Con el ensayo completo sacó 67% en Grammarly solo y 4% seguido de `ensuciar.py` con
errores de ortografía (no se ha medido con `unir.py`). Tardó 46 minutos, contra 4 de
`hip.py`. `scripts/ensuciar.py` (comas de menos y oraciones pegadas con coma) queda como
alternativa a `unir.py`: rinde menos y mete errores de puntuación.

```bash
export HUMANIZAR_API_KEY=tu-clave
export HUMANIZAR_API_URL=https://api.deepseek.com/chat/completions
export HUMANIZAR_MODEL=deepseek-flash
.venv/bin/python scripts/cubo.py mi-texto.txt -o cubo.txt --conceptos conceptos.txt --registro academico
python3 scripts/unir.py cubo.txt -o final.txt --conceptos conceptos.txt
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

| | `hip.py` + `unir.py` | El cubo |
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
texto» y el agente arma la lista de conceptos, corre `hip.py`, te ayuda a corregir y corre `unir.py`, verifica
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
| `scripts/unir.py` | Python | **une las oraciones de cada párrafo** |
| `scripts/ensuciar.py` | Python | comas de menos y oraciones pegadas con coma (alternativa) |
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

1. **Dos ensayos, una medición por versión.** La receta se midió con dos ensayos de
   divulgación; cada número es un escaneo a mano en Grammarly. No sabemos cuánto se
   generaliza a marketing, correos o textos técnicos.
2. **Se optimizó para Grammarly.** CleverHumanizer no coincide con Grammarly (al Dragon
   Ball con oraciones unidas le dio 5% de IA cuando Grammarly le dio 69%): mide en el
   detector que te importa.
3. **El modelo local se entrenó en inglés.** Funciona en español con un truco (le damos
   las primeras palabras), pero a veces cambia un detalle o deja un párrafo sin tocar.
4. **Los detectores cambian.** Lo que hoy pasa puede no pasar mañana, y un detector puede
   cambiar de opinión sobre el mismo texto el mismo día (le pasó a GPTZero).
5. **Los detectores marcan texto humano.** Un artículo de Wikipedia de 2014 sacó 46.5% en
   ZeroGPT.
6. **Los párrafos quedan en oraciones muy largas.** Es justo lo que los hace pasar. Si tu
   texto exige oraciones cortas y pulidas, este no es tu método.
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
├── scripts/              hip.py, unir.py, el cubo, el detector local y los medidores
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
Spanish; you fix the few meaning slips by hand; then `scripts/unir.py` joins the sentences
of each paragraph with "y" (and), the way people write in one go. No spelling or
punctuation errors are introduced. Two full essays went to 0% and 10% AI on Grammarly.
Tested one change at a time, double spaces did nothing, dropping commas helped a little,
and joining sentences helped most; joining alone on the original text was not enough
(57%). The evidence is small (two essays, measured by hand); every number is in
`references/evidencia.md`, and the tool is not meant for passing off graded work.
