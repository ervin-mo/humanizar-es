# humanizar-es

[![pruebas](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml/badge.svg)](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml)
[![licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)

Hace que un texto en español escrito con IA **deje de detectarse como IA en Grammarly sin
cambiar lo que dice** y sin meter errores de ortografía ni de puntuación. Corre en tu
computadora, en macOS, Linux o Windows: sin API, sin claves, sin costo y sin GPU.

> *English summary at the end.*

---

## El resultado

Tres ensayos completos generados con IA, medidos a mano en el
[detector de IA de Grammarly](https://www.grammarly.com/ai-detector):

| Ensayo | Reescrito por el modelo local | **Con la receta completa** |
|---|---|---|
| Turismo en Chiapas (1,150 palabras) | 77% IA | **0% IA** |
| Dragon Ball (910 palabras) | 84% IA | **10% IA** |
| Un modelo de IA para clasificar (690 palabras) | sin medir | **0% IA** |

Se conservaron los conceptos clave (79 de 80 entre los tres), sin una sola errata, en unos 5
minutos por ensayo en una Mac M4.

---

## Cómo funciona

```
 tu texto ──► 1. hip.py ──► 2. tú corriges detalles ──► 3. unir.py ──► texto final
```

1. **`hip.py` reescribe con un modelo base, no con un modelo de chat.** Los detectores
   reconocen sobre todo la huella del entrenamiento de chat: todo lo que escribe un
   ChatGPT, Claude, DeepSeek o Gemini la trae, aunque le pidas que «suene humano». El texto
   de un modelo **base** les parece humano
   ([Xu et al. 2026](https://arxiv.org/abs/2605.19516)). `hip.py` usa Qwen3-4B-Base con el
   adaptador HIP de ese mismo artículo, párrafo por párrafo, y reintenta si un párrafo
   pierde un concepto.
2. **Tú corriges a mano lo poco que el modelo cambió**: un detalle, un género, una errata.
   Solo la palabra culpable, y antes del paso 3.
3. **`unir.py` une las oraciones de cada párrafo con «y»**, como escribe alguien de
   corrido. Grammarly reconoce el ritmo del texto de IA: oraciones de largo parejo, cada
   una con su punto. Unirlas borra ese ritmo sin cambiar ninguna otra palabra.

Medido cambio por cambio sobre el mismo texto (detalle en
[`references/evidencia.md`](references/evidencia.md)):

| Sobre la reescritura de `hip.py` | Grammarly |
|---|---|
| Sin cambios | 84% |
| Espacios dobles | 84% |
| Quitar comas | 60% |
| Pegar oraciones con coma | 54% |
| Unir con «y» algunas oraciones | 40% |
| **Unir con «y» todas las oraciones de cada párrafo** | **8%** |
| *Unir todas, pero sobre el original, sin `hip.py`* | *57%* |

Los dos pasos hacen falta: ninguno solo baja de 57%.

---

## Con tu agente (Claude Code, Codex, OpenCode, Antigravity, DeepSeek Harness)

```bash
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es
python3 install.py        # en Windows: python install.py
```

Abre una sesión nueva y pídele **«humaniza este texto»**. La skill le dice al agente qué
hacer: instalar lo que falte (te pide permiso antes de bajar el modelo), anotar contigo lo
que no se puede perder, correr `hip.py`, revisar contigo cada párrafo, correr `unir.py` y
verificar el resultado.

| Agente | Dónde busca skills | ¿Lo cubre `install.py`? |
|---|---|---|
| Claude Code | `~/.claude/skills` | sí |
| Codex | `~/.agents/skills`, `~/.codex/skills` | sí |
| OpenCode | `~/.agents/skills`, `~/.claude/skills` | sí |
| Antigravity (`agy`) | `~/.agents/skills` | sí |
| DeepSeek Harness (`dsh`) | `~/.agents/skills` | sí |
| Gemini CLI | `~/.gemini/skills` | con `--agente gemini` |

`python3 install.py --agente codex` instala para uno solo; `--desinstalar` la quita. En
macOS y Linux, `./install.sh` hace lo mismo.

---

## A mano, paso a paso

### 1. Instalar (una vez)

Necesitas Python 3.9 o más reciente (sin paquetes extra) y
[llama.cpp](https://github.com/ggml-org/llama.cpp).

**macOS y Linux:**

```bash
brew install llama.cpp
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es
python3 scripts/instalar_hip.py   # baja el modelo: ~4.6 GB a ~/.cache/humanizar-es/hip
```

**Windows** (PowerShell o la terminal de tu agente):

```powershell
winget install llama.cpp
winget install Python.Python.3.12   # si no tienes Python
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es
python scripts\instalar_hip.py      # baja el modelo a C:\Users\<tú>\.cache\humanizar-es\hip
```

En Windows, en los comandos de abajo escribe `python` donde dice `python3`. Si `winget`
acaba de instalar llama.cpp, `hip.py` lo encuentra aunque no hayas abierto otra terminal; si
lo tienes en otra carpeta, pon la ruta del `.exe` en la variable `HUMANIZAR_LLAMA`.

El instalador verifica cada archivo con su sha256 y, si la descarga se corta, sigue donde
se quedó. Corre en CPU; con 8 GB de RAM libres alcanza. En una Mac M4 son unos 30 segundos
por párrafo; en una PC con un procesador de hace unos años puede ser de 1 a 3 minutos.

### 2. Anotar lo que no se puede perder

Un archivo con los conceptos, uno por línea; variantes separadas por `|`; con `*` al final,
cualquier palabra que empiece así. **Pon los nombres propios completos**: `unir.py` los
respeta con mayúscula.

```text
# conceptos.txt
René Descartes | Descartes
principio de no contradicción
deslave*
```

Para arrancar: `python3 scripts/verificar_fidelidad.py mi-texto.txt --listar`

### 3. Reescribir con el modelo local

```bash
python3 scripts/hip.py mi-texto.txt -o reescrito.txt --conceptos conceptos.txt
```

Unos 30 segundos por párrafo. Avisa qué párrafos dejó como el original porque perdían un
concepto.

### 4. Releer y corregir, antes de unir

```bash
python3 scripts/verificar_fidelidad.py mi-texto.txt reescrito.txt --conceptos conceptos.txt
```

Y lee la reescritura contra el original. El modelo a veces:

- cambia un detalle («limpian» → «lavan los platos»; «foráneas» → «extranjeras»);
- invierte una idea («renunciar al pragmatismo» donde decía «resignarse al pragmatismo»);
- se equivoca de género, de número o de fecha («Para una niña» por «los niños»);
- deja una errata o se come un acento («timido», «metafisica»).

Corrige **solo la palabra culpable**, a mano, en `reescrito.txt`. No le pidas a un modelo
de chat que lo arregle: le devuelve al texto la huella que el modelo base le quitó. Y
hazlo **antes** de unir: corregir después subió el número en las pruebas.

### 5. Unir las oraciones

```bash
python3 scripts/unir.py reescrito.txt -o final.txt --conceptos conceptos.txt
```

Si avisa de palabras que bajó a minúscula, revisa que no sean nombres propios; si lo son,
agrégalas a `conceptos.txt` y vuelve a correrlo.

### 6. Medir, con un control

Pega `final.txt` en el detector y, aparte, **un texto que tú escribiste sin IA**. Si tu
texto también sale como IA, ese detector no está midiendo. Con una cuenta gratuita,
Grammarly permite pocos escaneos al día; ver
[`references/detectores.md`](references/detectores.md).

---

## Ejemplo

[`ejemplos/`](ejemplos/) tiene un ensayo de metafísica generado con IA y su paso por la
receta: `original.txt` → `1-hip.txt` (ya corregido a mano) → `2-final.txt`, con su
`conceptos.txt`. Lo que se corrigió a mano está en [`ejemplos/LEEME.md`](ejemplos/LEEME.md).

---

## Límites

1. **Se midió en Grammarly, con tres ensayos.** Otros detectores no coinciden con él:
   CleverHumanizer le dio 5% de IA a un texto que Grammarly marcó con 69%. Mide en el que te
   importa. No sabemos todavía qué tanto se generaliza a correos o a textos técnicos.
2. **Los párrafos quedan en oraciones largas encadenadas.** Es justo lo que lo hace pasar;
   si tu texto exige oraciones cortas y pulidas, este no es tu método.
3. **El modelo se entrenó en inglés.** Funciona en español porque `hip.py` le da las dos
   primeras palabras de cada párrafo, pero comete los errores del paso 4. Por eso releer no
   es opcional.
4. **Cada corrección hecha por un modelo de chat le suma puntos.** En las pruebas, 16
   correcciones subieron un ensayo de 8% a 10%. Corrige poco y a mano.
5. **Los detectores cambian.** Lo que hoy pasa puede no pasar mañana.

## Uso responsable

Pensado para texto que firmas y del que respondes: contenido de marca, divulgación,
documentación, correos, borradores que escribiste con ayuda de IA. **No lo uses para
entregar como propio un trabajo evaluado donde el uso de IA está prohibido o debe
declararse.** Ahí el problema no es técnico: es de honestidad académica.

---

## Estructura

```
humanizar-es/
├── SKILL.md                 la skill para agentes
├── install.py               instala la skill (install.sh: atajo para macOS y Linux)
├── scripts/
│   ├── instalar_hip.py      baja el modelo (una vez; instalar_hip.sh: atajo)
│   ├── hip.py               paso 1: reescribe con el modelo base local
│   ├── unir.py              paso 3: une las oraciones de cada párrafo
│   └── verificar_fidelidad.py   que no se pierda ningún concepto ni negación
├── ejemplos/                un ensayo y su paso por la receta
├── references/
│   ├── evidencia.md         todas las mediciones
│   └── detectores.md        cómo medir en Grammarly y sus límites
├── tests/                   pruebas (sin red ni modelos)
└── THIRD_PARTY.md           licencias del modelo y del adaptador
```

## Contribuir

Lo que más falta es **evidencia**: la receta medida en más textos (correos, marketing,
textos técnicos) y en más detectores, siempre con un control humano. Abre un PR con los
números en `references/evidencia.md`.

```bash
python3 -m unittest discover -s tests -v    # antes de abrir un PR
```

## Licencia

Código y documentación: [MIT](LICENSE). El modelo (Qwen3-4B-Base) y el adaptador HIP son
Apache-2.0 y se descargan aparte; ver [`THIRD_PARTY.md`](THIRD_PARTY.md).

---

## English summary

Makes AI-written Spanish text stop being flagged as AI by Grammarly **without changing
what it says** and without adding spelling or punctuation errors. Runs locally: no API,
no API keys, no cost, no GPU; macOS, Linux and Windows. Three steps: `scripts/hip.py` rewrites each paragraph with a *base* model
(Qwen3-4B-Base plus the HIP adapter from Xu et al. 2026, "Base Models Look Human To AI
Detectors"); you fix the few slips by hand; `scripts/unir.py` joins the sentences of each
paragraph with "y" (and), breaking the even sentence rhythm Grammarly keys on. Three full
essays went to 0%, 10% and 0% AI (two of them from 77% and 84%). Measured one change at a time: double
spaces did nothing, dropping commas helped a little, joining sentences helped most, and
joining alone on the original text was not enough (57%). Install with `python3 install.py` (`python` on Windows) and
ask your coding agent to "humaniza este texto". Not meant for passing off graded work.
