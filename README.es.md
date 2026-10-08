# humanizar-es · Humanizador de texto IA, local y gratis, para español e inglés

[![pruebas](https://github.com/ervin-mo/humanizar-es/actions/workflows/tests.yml/badge.svg)](https://github.com/ervin-mo/humanizar-es/actions/workflows/tests.yml)
[![licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
[![macOS · Linux · Windows](https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-sí-success.svg)](#instalación)
[![Español · English](https://img.shields.io/badge/Español%20·%20English-sí-success.svg)](#idiomas)

[English](README.md) · **Español**

![humanizar-es: humaniza texto de IA en tu computadora y gratis](assets/vista-previa.png)

**humanizar-es** recibe un texto escrito con ChatGPT, Claude, Gemini o DeepSeek y lo
devuelve **diciendo lo mismo**, en una prosa que los tres detectores que medimos leen como
humana: **0% en Grammarly, 0% en ZeroGPT y 0% IA / 98% humano en GPTZero**, con el mismo
ensayo de 1,990 palabras que empezó en 45%. Corre en tu computadora con un modelo abierto:
sin API, sin claves, sin cobro por palabra, y tu texto nunca sale de tu máquina. Úsalo a
mano o como *skill* de tu agente (Claude Code, Codex, OpenCode, Antigravity).

No es un cambiador de sinónimos, ni un prompt de «reescríbelo con tono humano», ni un
generador de faltas de ortografía. Es un proceso de cuatro etapas, y cada etapa existe
porque un experimento controlado mostró qué mide de verdad un detector: una variable a la
vez, el mismo texto en cada condición, y un texto humano de control y el original de IA en
cada sesión.

---

## Resultados

| Ensayo generado con IA | Grammarly | ZeroGPT | GPTZero |
|---|---|---|---|
| **Aristóteles: acto y potencia** · 1,990 palabras · antes | 45% | 45.3% | 37% IA |
| **Aristóteles: acto y potencia** · **después** | **0% y 0%** | **0%** | **0% IA · 98% humano** |
| Turismo e IA en Chiapas · 1,150 palabras | 77% → **0%** | — | — |
| Un modelo de IA de clasificación · 690 palabras | → **0%** | — | — |
| Dragon Ball y su generación · 910 palabras | 84% → **10%** | — | — |
| 🇬🇧 Trabajo remoto (inglés) · 601 palabras | — | 100% → **0%** | — |
| 🇬🇧 Autos eléctricos (inglés) · 673 palabras | — | 100% → **0%** | — |

*Octubre de 2026. El primer ensayo conserva 24 de 24 nombres, términos y cifras clave, y
sus dos citas de Aristóteles palabra por palabra. Grammarly lee ~1,400 palabras, así que se
midió en mitades. El ensayo de Dragon Ball se corrió con una versión anterior del proceso.*

---

## El método

```
 original ─► 1. reescribe ─► 2. fidelidad ─► 3. ritmo ──► 4. selección ──► final
             modelo base     conceptos,       bloques de    candidatos,
             sin entrena-    citas, copia,    largo         medidos en el
             miento de chat  arreglos ≤3 pal. disparejo     documento completo
```

### Qué miden los detectores

Tres detectores, tres señales distintas. El proceso existe porque cada uno se desarmó con
experimentos:

| Detector | A qué reacciona | Qué **no** lo mueve |
|---|---|---|
| **GPTZero** | la huella del entrenamiento de chat; su modelo más nuevo en inglés (4.1o) también lee el texto de modelos base: nuestro siguiente objetivo | — |
| **Grammarly** | el ritmo: oraciones de largo parejo, cada una con su punto | los espacios dobles (las faltas sí, pero dejan errores visibles) |
| **ZeroGPT** | oraciones sueltas con estilo de libro de texto; califica **oración por oración y pesa por palabras** | unir oraciones de un texto humano (Unamuno unido: 0%) |

### 1. Quitar la huella del entrenamiento de chat

Xu et al. (2026), [*Base Models Look Human To AI Detectors*](https://arxiv.org/abs/2605.19516),
mostraron que el texto de un modelo **base** sale 97–99% humano en GPTZero y Pangram, y el
mismo modelo después del entrenamiento de chat, 17–30%. Nuestras pruebas coinciden: ninguna
reescritura con un modelo de chat bajó de 64% en Grammarly. `rewrite.py` parafrasea con
Qwen3-4B-Base más el adaptador HIP del artículo, con llama.cpp, en tu CPU.

### 2. Conservar el sentido sin devolver la huella

Cada párrafo recibe una pasada, y el intento se descarta y se repite cuando:

- pierde un concepto de tu lista (nombres, términos, cifras, negaciones clave);
- **altera una cita textual** del original o **agrega una referencia** que el original no
  tenía (en un ensayo de prueba el modelo escribió «(De Anima, libro i, cap. vi)», que no
  existe);
- **copia el original**: más del 60% de sus palabras en tramos de 8 o más palabras idénticas;
- sale truncado o se desboca.

Luego `check.py` compara conceptos y negaciones, y una persona corrige **de una a tres
palabras** como máximo. Lo que necesite más se regenera con el modelo (`--only`); nunca se
escribe a mano ni se pega de vuelta del original: arreglos a mano de cuatro palabras o más
dejaron la mitad de un ensayo en 3% en Grammarly; al regenerar esos párrafos bajó a 0%.

### 3. Reconstruir el ritmo

Las personas escriben a ráfagas, unas oraciones largas y otras cortas. `join.py --pausas 2`
deja dos o tres puntos por párrafo, en **bloques de largo disparejo** de al menos dos
oraciones, y corta primero donde una oración ya abre con un marcador del discurso («Sin
embargo», «Por ejemplo», «Segundo»). Dentro de cada bloque une con «y», «;» o «, pero». No
toca ninguna palabra de contenido.

### 4. Seleccionar midiendo

El modelo base muestrea: el mismo párrafo sale distinto cada vez, y un detector puede darle
0% a una versión y 100% a otra. Por eso los párrafos que un detector todavía marca se
regeneran varias veces (`--candidates`), cada candidato se une y **se mide dentro del
documento completo** (el contexto cambia el resultado), y se adopta el que pasa (`--take`).
Todos los candidatos salen del mismo modelo base, así que elegir no agrega huella de chat.
Dos hallazgos lo hicieron funcionar:

- **Las palabras de arranque importan.** Para que siga en español, el modelo arranca cada
  párrafo con las dos primeras palabras del original. Cuando son una apertura típica («Uno
  de los problemas más importantes…», «Aristóteles distingue…»), el modelo reconstruye la
  frase de manual y ZeroGPT la marca. Arrancar con otras palabras (`--lead "Desde la"`) lo
  resolvió: 22 candidatos de un párrafo con el arranque original salieron en 100%; con otro
  arranque, 0%.
- **Cada arreglo se vuelve a medir.** ZeroGPT es determinista pero frágil: un arreglo de una
  palabra subió un párrafo de 0% a 62%.

### Los experimentos detrás de cada etapa

El mismo ensayo, un cambio a la vez.

| Grammarly | |
|---|---|
| Solo reescrito por el modelo base | 84% |
| … más espacios dobles al azar | 84% |
| … quitando ~35% de las comas | 60% |
| … uniendo ~60% de las oraciones | 40% |
| … uniendo todas las oraciones de cada párrafo | **8%** |
| El original, sin el modelo base, uniendo todas las oraciones | 57% |
| Reescribir con un modelo de chat (cuatro recetas distintas) | 64–100% |
| Pausas, con una oración sola entre dos puntos | 6% |
| **Pausas, bloques de dos o más oraciones** | **0% y 0%** |

| ZeroGPT (determinista: el mismo texto siempre da el mismo número) | |
|---|---|
| El original de IA | 34.3% |
| Reescrito por el modelo base, oraciones sin unir | 33.9% |
| … todas las oraciones unidas | 44.0% |
| … con pausas | 52.4% |
| Un texto humano (Unamuno, 1914) unido igual | 0% |
| **Después de la selección: candidatos medidos en el documento completo** | **0%** |

La tensión es real: Grammarly quiere oraciones largas y ZeroGPT castiga una oración larga
que contenga una sola frase de manual. El ritmo solo no satisface a los dos; ritmo más
selección, sí. Todas las mediciones: [`references/evidence.md`](references/evidence.md).

### Cómo medimos

- **Dos controles en cada sesión**: un texto humano tiene que salir humano, y el original de
  IA tiene que salir IA. El detector que falla cualquiera de los dos no cuenta: QuillBot dio
  100% humano al original de IA, y GPTZero, tras muchos escaneos desde un mismo navegador,
  dio 100% IA a un texto de 1914.
- **La referencia se vuelve a medir en la misma sesión**; nunca se compara con un número de
  horas antes.
- **Se mide el formato final**: con títulos y bibliografía, ZeroGPT puede dar un número
  distinto que con el texto pelón.

---

## Instalación

### Con tu agente (lo más fácil)

```bash
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es
python3 install.py          # en Windows: python install.py
```

Abre una sesión nueva y pide: **«humaniza este texto»**. La skill guía al agente por cada
etapa: instalar lo que falte (pregunta antes de bajar el modelo), armar contigo la lista de
lo que no se puede perder, reescribir, mostrarte cada cambio, reconstruir el ritmo y
seleccionar candidatos de lo que tu detector todavía marque.

| Agente | Carpeta de skills | ¿La cubre `install.py`? |
|---|---|---|
| Claude Code | `~/.claude/skills` | sí |
| Codex | `~/.agents/skills` | sí |
| OpenCode | `~/.agents/skills`, `~/.claude/skills` | sí |
| Antigravity (`agy`) | `~/.agents/skills` | sí |
| DeepSeek Harness (`dsh`) | `~/.agents/skills` | sí |
| Gemini CLI | `~/.gemini/skills` | con `--agent gemini` |

### El modelo (una vez, ~4.6 GB)

Necesitas Python 3.9+ (sin paquetes extra) y [llama.cpp](https://github.com/ggml-org/llama.cpp):

| | macOS y Linux | Windows |
|---|---|---|
| llama.cpp | `brew install llama.cpp` | `winget install llama.cpp` |
| El modelo | `python3 scripts/install_model.py` | `python scripts\install_model.py` |

El instalador verifica cada archivo con su sha256 y continúa si la descarga se corta.
Corre en CPU: bastan 8 GB de RAM libre, sin GPU. En una Mac M4 tarda de 30 a 60 segundos
por párrafo; en una PC de hace unos años, de 1 a 3 minutos.

---

## Úsalo a mano

En Windows escribe `python` donde dice `python3`.

**1. Anota lo que no se puede perder** en `concepts.txt`: nombres propios completos,
cifras, términos. Uno por línea, variantes con `|`, `*` para prefijos.

```text
Aristóteles
acto y potencia
autorregula*
```

**2. Reescribe** con el modelo base:

```bash
python3 scripts/rewrite.py mi-texto.txt -o reescrito.txt --concepts concepts.txt
```

**3. Revisa y corrige de una a tres palabras como máximo.** Si hace falta más, regenera
ese párrafo:

```bash
python3 scripts/check.py mi-texto.txt reescrito.txt --concepts concepts.txt
python3 scripts/rewrite.py mi-texto.txt -o reescrito.txt --concepts concepts.txt --only 6,11
```

No le pidas a ChatGPT que lo corrija: le devuelve la huella que el modelo base quitó.

**4. Reconstruye el ritmo** (el idioma se detecta solo):

```bash
python3 scripts/join.py reescrito.txt -o final.txt --concepts concepts.txt --pausas 2
```

**5. Mide** el texto final en tu detector, en el formato que vas a entregar, con un texto
humano de control ([`references/detectors.md`](references/detectors.md)).

**6. Selecciona, para lo que siga marcado.** Genera candidatos de esos párrafos, con otras
palabras de arranque si el párrafo empieza con una frase de manual:

```bash
python3 scripts/rewrite.py mi-texto.txt -o reescrito.txt --concepts concepts.txt \
        --only 4 --candidates 6 --lead "Desde la" --temperature 1.1
```

Une cada candidato en el texto completo, mide, adopta el que pasa y vuelve a unir:

```bash
python3 scripts/rewrite.py mi-texto.txt -o reescrito.txt --take 4=reescrito.txt.candidates/p04-3.txt
python3 scripts/join.py reescrito.txt -o final.txt --concepts concepts.txt --pausas 2
```

Relee el párrafo adoptado contra el original: pasar un detector no vale nada si se perdió
una idea.

Hay ejemplos completos, con cada arreglo a mano anotado, en [`examples/`](examples/).

---

## Idiomas

| | Reescribe | Ritmo | Revisa | Medido |
|---|---|---|---|---|
| **Español** | ✅ | ✅ «y», «;», «pero»… | ✅ | ✅ cuatro ensayos, tres detectores |
| **English** | ✅ (el adaptador HIP se entrenó en inglés) | ✅ "and", ";", "but"… | ✅ | ✅ ZeroGPT, dos ensayos · GPTZero: siguiente objetivo |

Otros idiomas: la reescritura puede funcionar (el modelo base es multilingüe), pero
`join.py` solo conoce los conectores del español y del inglés. Agregar uno es un
diccionario pequeño en `scripts/join.py`; se aceptan pull requests.

## Detectores

| Detector | Estado |
|---|---|
| **Grammarly** | ✅ 0% en tres de cuatro ensayos (10% en una corrida con una versión anterior) |
| **GPTZero** | ✅ 0% IA · 98% humano (español) · Inglés: siguiente objetivo ([lo que probamos](references/evidence.md)) |
| **ZeroGPT** | ✅ 0% en español y en inglés, con la etapa 4 (selección) cuando hace falta |
| QuillBot | no sirve en español: dio 100% humano al original de IA |

Cada detector usa su propio modelo: una versión que pasa uno puede no pasar otro; el primer
ensayo pasa los tres a la vez. Lo que más necesitamos son mediciones en más detectores y en
más tipos de texto.

---

## Preguntas frecuentes

**¿Es gratis? ¿Necesito una clave de OpenAI o alguna cuenta?**
Gratis y sin claves. El modelo se baja una vez y corre en tu computadora.

**¿Cambia lo que dice mi texto?**
Está hecho para no hacerlo: descarta los intentos que pierden un concepto, alteran una cita
o inventan una referencia, `check.py` compara conceptos y negaciones, y tú relees cada
párrafo.

**¿Mete faltas de ortografía a propósito, como otros «humanizadores»?**
No. Cambia quién escribió las oraciones y su ritmo, no la ortografía.

**¿Los resultados son consistentes?**
Tres de los cuatro ensayos llegaron a 0% en Grammarly, y el más reciente pasa Grammarly,
GPTZero y ZeroGPT a la vez. Lo que puede ser determinista lo es (la unión usa una semilla
fija; ZeroGPT da el mismo número al mismo texto), la salida que copia el original se
rechaza, y 48 pruebas corren en cada cambio en Ubuntu, macOS y Windows. Los detectores
cambian con el tiempo; por eso cada sesión lleva controles.

**¿La selección manda mi texto a algún lado?**
La herramienta nunca lo hace. Medir es tu paso, en tu detector, como con cualquier texto que
revises.

**¿Necesito GPU?**
No. Corre en CPU, con prioridad baja, así que tu computadora sigue usable.

---

## Límites

1. **GPTZero en inglés es el siguiente objetivo.** Su modelo más nuevo en inglés (4.1o) lee el
   texto de modelos base desde ~250 palabras; probamos tres familias de modelos
   ([evidencia](references/evidence.md)). Correos, marketing y textos técnicos aún no se miden.
2. **Releer no es opcional.** El modelo base a veces cambia un detalle o invierte una idea.
   El proceso atrapa conceptos perdidos, citas alteradas y referencias inventadas; lo demás
   lo atrapa una persona.
3. **Seleccionar cuesta tiempo.** Cada candidato es una corrida del modelo (30–60 s por
   párrafo en una M4).
4. **Los detectores cambian.** Esto es una foto de octubre de 2026.

## Uso responsable

Hecho para textos que firmas y de los que respondes: contenido de marca, prospección,
documentación, correos, borradores escritos con ayuda de IA. **No lo uses para entregar
como propio un trabajo evaluado donde la IA está prohibida o debe declararse.** Ese
problema no es técnico: es de honestidad académica.

---

## Estructura

```
humanizar-es/
├── SKILL.md                 la skill para agentes
├── install.py               instala la skill (install.sh: atajo para macOS/Linux)
├── scripts/
│   ├── install_model.py     baja el modelo (una vez)
│   ├── rewrite.py           etapas 1, 2 y 4: reescribe, cuida la fidelidad, candidatos
│   ├── check.py             etapa 2: conceptos y negaciones, original contra reescritura
│   └── join.py              etapa 3: reconstruye el ritmo de cada párrafo
├── examples/                ejemplos completos en español y en inglés
├── references/              todas las mediciones y cómo medir
└── tests/                   48 pruebas en Ubuntu, macOS y Windows (sin red ni modelo)
```

Los nombres viejos de los scripts (`hip.py`, `unir.py`, `verificar_fidelidad.py`,
`instalar_hip.py`) siguen funcionando.

## Contribuir

Lo que más falta es **evidencia**: el proceso medido en más textos, más idiomas y más
detectores, siempre con un control humano y el original de IA. Abre un issue o un PR con
los números en [`references/evidence.md`](references/evidence.md).

```bash
python3 -m unittest discover -s tests -v
```

## Créditos y licencia

Código y documentación: [MIT](LICENSE), © ervin-mo. El método y el adaptador HIP son de
Xu et al. (2026); el modelo base es Qwen3-4B-Base, de Alibaba. Ambos son Apache-2.0 y se
descargan por separado: ver [`THIRD_PARTY.md`](THIRD_PARTY.md). Si lo usas en tu trabajo,
cita el repo ([`CITATION.cff`](CITATION.cff)) y el artículo de HIP.
