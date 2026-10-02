# humanizar-es · Humanizador de texto IA en español, local y gratis

[![pruebas](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml/badge.svg)](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml)
[![licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
[![macOS · Linux · Windows](https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-sí-success.svg)](#instalar)
[![sin API ni costo](https://img.shields.io/badge/API%20ni%20claves-no%20hacen%20falta-success.svg)](#cómo-funciona)

**Español** · [English](README.en.md)

**humanizar-es** reescribe un texto en español generado con ChatGPT, Claude, Gemini o
DeepSeek para que **el detector de IA de Grammarly deje de marcarlo**, sin cambiar lo que
dice y sin meter errores de ortografía ni de puntuación. Corre en tu computadora con un
modelo abierto: sin API, sin claves, sin pagar por palabra y sin mandar tu texto a nadie.
Funciona solo o como *skill* para tu agente (Claude Code, Codex, OpenCode, Antigravity).

| Ensayo generado con IA | Antes | **Después** |
|---|---|---|
| Turismo e IA en Chiapas · 1,150 palabras | 77% IA | **0% IA** |
| Dragon Ball y su generación · 910 palabras | 84% IA | **10% IA** |
| Un modelo de IA para clasificar · 690 palabras | sin medir | **0% IA** |

*Detector de IA de Grammarly, octubre de 2026. Se conservaron 79 de 80 conceptos clave.*

---

## Cómo funciona

Dos ideas, cada una medida por separado:

```
 tu texto ─► 1. hip.py ─► 2. tú corriges 2-3 palabras ─► 3. unir.py ─► texto final
             reescribe con un        (lo que el modelo           une las oraciones
             modelo BASE local        cambió de más)              de cada párrafo
```

**1. Reescribir con un modelo base, no con uno de chat.** Los detectores reconocen sobre
todo la *huella del entrenamiento de chat*: todo lo que escribe un ChatGPT o un Claude la
trae, aunque le pidas que «suene humano». Un modelo **base**, sin ese entrenamiento,
escribe como la gente. Lo demostraron Xu et al. (2026) en
[*Base Models Look Human To AI Detectors*](https://arxiv.org/abs/2605.19516): con GPTZero y
Pangram, el texto de un modelo base salió 97–99% humano y el de su versión de chat,
17–30%. `hip.py` usa Qwen3-4B-Base con el adaptador HIP de ese artículo.

**2. Romper el ritmo.** Grammarly reconoce el ritmo del texto de IA: oraciones de largo
parejo, cada una con su punto. `unir.py` une las oraciones de cada párrafo con «y», como
escribe alguien de corrido, sin tocar ninguna otra palabra.

Los dos pasos hacen falta. Sobre el mismo ensayo, un cambio a la vez:

| Versión | Grammarly |
|---|---|
| Reescrito por `hip.py` | 84% |
| … más espacios dobles | 84% |
| … quitando comas | 60% |
| … uniendo con «y» algunas oraciones | 40% |
| … **uniendo todas las oraciones de cada párrafo** | **8%** |
| El original, sin `hip.py`, uniendo todas | 57% |
| Reescribir con un modelo de chat (varias recetas) | 64–100% |

Todas las mediciones: [`references/evidencia.md`](references/evidencia.md).

---

## Instalar

### Con tu agente (lo más fácil)

```bash
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es
python3 install.py          # en Windows: python install.py
```

Abre una sesión nueva y pídele **«humaniza este texto»**. La skill le dice al agente qué
hacer: instalar lo que falte (te pide permiso antes de bajar el modelo), anotar contigo lo
que no se puede perder, reescribir, mostrarte cada cambio, unir y verificar.

| Agente | Carpeta de skills | ¿La cubre `install.py`? |
|---|---|---|
| Claude Code | `~/.claude/skills` | sí |
| Codex | `~/.agents/skills` | sí |
| OpenCode | `~/.agents/skills`, `~/.claude/skills` | sí |
| Antigravity (`agy`) | `~/.agents/skills` | sí |
| DeepSeek Harness (`dsh`) | `~/.agents/skills` | sí |
| Gemini CLI | `~/.gemini/skills` | con `--agente gemini` |

### El modelo (una vez, ~4.6 GB)

Necesitas Python 3.9 o más nuevo, sin paquetes extra, y
[llama.cpp](https://github.com/ggml-org/llama.cpp):

| | macOS y Linux | Windows |
|---|---|---|
| llama.cpp | `brew install llama.cpp` | `winget install llama.cpp` |
| El modelo | `python3 scripts/instalar_hip.py` | `python scripts\instalar_hip.py` |

El instalador verifica cada archivo con su sha256 y, si la descarga se corta, sigue donde
se quedó. Corre en CPU: con 8 GB de RAM libres alcanza, sin GPU. En una Mac M4 tarda unos
30 segundos por párrafo; en una PC de hace unos años, de 1 a 3 minutos.

---

## Úsalo a mano

En Windows escribe `python` donde dice `python3`.

**1. Anota lo que no se puede perder**, en `conceptos.txt`: nombres propios completos,
cifras, términos. Uno por línea, variantes con `|`, `*` para prefijos.

```text
René Descartes | Descartes
principio de no contradicción
deslave*
```

**2. Reescribe** (párrafo por párrafo; reintenta si un párrafo pierde un concepto):

```bash
python3 scripts/hip.py mi-texto.txt -o reescrito.txt --conceptos conceptos.txt
```

**3. Revisa y corrige a mano, antes de unir.** El modelo a veces cambia un detalle
(«limpian» → «lavan los platos»), invierte una idea, se equivoca de género o de fecha o se
come un acento:

```bash
python3 scripts/verificar_fidelidad.py mi-texto.txt reescrito.txt --conceptos conceptos.txt
```

Corrige **solo la palabra culpable**. No le pidas a ChatGPT que lo arregle: le devuelve la
huella que el modelo base le quitó.

**4. Une las oraciones:**

```bash
python3 scripts/unir.py reescrito.txt -o final.txt --conceptos conceptos.txt
```

**5. Mide** en el detector, junto con un texto que tú escribiste sin IA como control
([`references/detectores.md`](references/detectores.md)).

Un ejemplo completo, con lo que se corrigió a mano, está en [`ejemplos/`](ejemplos/).

---

## ¿Y en otros detectores?

Los detectores no están de acuerdo entre sí, y aquí se midió con cuidado solo Grammarly.
Lo que sabemos, con el mismo texto antes y después, y un texto humano de control
(*Nuestra América*, José Martí, 1891):

| Detector | Control humano | Ensayo A: antes → después | Ensayo B: antes → después |
|---|---|---|---|
| **Grammarly** | — | sin medir → **0%** | sin medir |
| **GPTZero** | 0% IA | 98% → **65%** | 100% → 100% |
| **ZeroGPT** | 0% IA | 0% → 0% | 98.5% → 97.5% |
| **CleverHumanizer** | — | Dragon Ball unido: 5% | — |

*Ensayo A: el de un modelo de IA para clasificar (690 palabras). Ensayo B: el de metafísica
de [`ejemplos/`](ejemplos/). Un escaneo por versión, 2 de octubre de 2026.*

Dicho sin rodeos: **la receta está hecha y probada para Grammarly**. GPTZero la detecta
menos que el original pero todavía la marca, y ZeroGPT no se mueve. Si tu texto tiene que
pasar otro detector, mídelo ahí antes de confiar. Contribuciones con mediciones en otros
detectores son lo que más falta (ver [Contribuir](#contribuir)).

---

## Preguntas frecuentes

**¿Es gratis? ¿Necesito una clave de OpenAI o de algún servicio?**
Gratis y sin claves. El modelo se descarga una vez y corre en tu computadora; tu texto no
sale de ella.

**¿Cambia lo que dice mi texto?**
No debería: `hip.py` reintenta si se pierde un concepto, `verificar_fidelidad.py` revisa
conceptos y negaciones, y tú revisas cada párrafo antes de unir. En las pruebas se
conservaron 79 de 80 conceptos.

**¿Mete errores a propósito, como otros «humanizadores»?**
No. Meter erratas también baja el número, pero deja errores visibles. Esta receta no toca
la ortografía ni la puntuación.

**¿Funciona en inglés?**
El adaptador HIP se entrenó en inglés, así que la reescritura sí; `unir.py` está hecho para
el español («y», «pero», «además»). Nadie lo ha medido en inglés todavía.

**¿Por qué el texto final tiene oraciones tan largas?**
Es justo lo que lo hace pasar: Grammarly reconoce oraciones de largo parejo. Si tu texto
exige oraciones cortas y pulidas, este no es tu método.

**¿Necesito GPU?**
No. Corre en CPU, con prioridad baja para que tu computadora siga usable.

---

## Límites

1. **Medido en Grammarly, con tres ensayos.** En otros detectores no está probado que
   funcione (ver arriba).
2. **Párrafos en oraciones largas encadenadas.** Es parte de cómo pasa.
3. **Releer no es opcional.** El modelo se entrenó en inglés y a veces cambia un detalle o
   invierte una idea; en un ensayo volteó el sentido de la conclusión.
4. **Cada corrección hecha por un modelo de chat le suma puntos.** Corrige poco y a mano.
5. **Los detectores cambian.** Esto es una foto de octubre de 2026.

## Uso responsable

Hecho para texto que firmas y del que respondes: contenido de marca, divulgación,
documentación, correos, borradores escritos con ayuda de IA. **No lo uses para entregar
como propio un trabajo evaluado donde el uso de IA está prohibido o debe declararse.** Ahí
el problema no es técnico: es de honestidad académica.

---

## Estructura

```
humanizar-es/
├── SKILL.md                     la skill para agentes
├── install.py                   instala la skill (install.sh: atajo para macOS y Linux)
├── scripts/
│   ├── instalar_hip.py          baja el modelo (una vez)
│   ├── hip.py                   paso 1: reescribe con el modelo base local
│   ├── unir.py                  paso 3: une las oraciones de cada párrafo
│   └── verificar_fidelidad.py   que no se pierda ningún concepto ni negación
├── ejemplos/                    un ensayo y su paso por la receta
├── references/                  todas las mediciones y cómo medir
└── tests/                       pruebas en Ubuntu, macOS y Windows (sin red ni modelos)
```

## Contribuir

Lo que más falta es **evidencia**: la receta medida en más textos (correos, marketing,
textos técnicos) y en más detectores, siempre con un control humano. Abre un *issue* o un
PR con los números en [`references/evidencia.md`](references/evidencia.md).

```bash
python3 -m unittest discover -s tests -v
```

## Créditos y licencia

Código y documentación: [MIT](LICENSE), © ervin-mo. El método HIP y su adaptador son de
Xu et al. (2026); el modelo base es Qwen3-4B-Base de Alibaba. Ambos son Apache-2.0 y se
descargan aparte: ver [`THIRD_PARTY.md`](THIRD_PARTY.md). Si lo usas en un trabajo, cita el
repo ([`CITATION.cff`](CITATION.cff)) y el artículo de HIP.
