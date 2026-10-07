# humanizar-es · Humanizador de texto IA, local y gratis, para español e inglés

[![pruebas](https://github.com/ervin-mo/humanizar-es/actions/workflows/tests.yml/badge.svg)](https://github.com/ervin-mo/humanizar-es/actions/workflows/tests.yml)
[![licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
[![macOS · Linux · Windows](https://img.shields.io/badge/macOS%20·%20Linux%20·%20Windows-sí-success.svg)](#instalación)
[![Español · English](https://img.shields.io/badge/Español%20·%20English-sí-success.svg)](#idiomas)

[English](README.md) · **Español**

![humanizar-es: humaniza texto de IA en tu computadora y gratis](assets/vista-previa.png)

**humanizar-es** recibe un texto escrito con ChatGPT, Claude, Gemini o DeepSeek y lo
devuelve **diciendo lo mismo**, en una prosa que los detectores de IA leen como humana:
**0% en Grammarly y 0% IA / 99% humano en GPTZero** en nuestro último ensayo de prueba.
Corre en tu computadora con un modelo abierto: sin API, sin claves, sin cobro por palabra,
y tu texto nunca sale de tu máquina. Úsalo a mano o como *skill* de tu agente (Claude
Code, Codex, OpenCode, Antigravity).

No es un cambiador de sinónimos ni siembra faltas de ortografía. Es un proceso de tres
etapas construido con experimentos controlados, cambiando una sola variable a la vez y
contrastando cada medición con un texto humano de control.

---

## Resultados

| Ensayo generado con IA (español) | Grammarly, antes | **Grammarly, después** | GPTZero, después |
|---|---|---|---|
| Aristóteles: acto y potencia · 1,990 palabras | 45% | **0% y 0%** (en dos mitades) | **0% IA · 99% humano** |
| Turismo e IA en Chiapas · 1,150 palabras | 77% | **0%** | sin medir |
| Un modelo de IA de clasificación · 690 palabras | sin medir | **0%** | sin medir |
| Dragon Ball y su generación · 910 palabras | 84% | **10%** | sin medir |

*Octubre de 2026. En cada reescritura se verificaron los nombres, términos y cifras clave
(24 de 24 en el primer ensayo). GPTZero leyó los primeros 10,000 caracteres. El ensayo de
Dragon Ball se corrió con una versión anterior del proceso.*

---

## El método

```
 original ─► 1. rewrite.py ──► 2. control de fidelidad ──► 3. join.py ──► texto final
             modelo base,       conceptos, negaciones,       ritmo: bloques de
             sin entrenamiento  freno de copia, arreglos     largo disparejo,
             de chat            a mano de ≤3 palabras        cortes donde la idea gira
```

### 1. Quitar la huella del entrenamiento de chat

Los detectores reconocen sobre todo la *huella del entrenamiento de chat* (ajuste por
instrucciones y RLHF), no «la IA» en general. Todo lo que escribe un modelo de chat la
trae, aunque le pidas «sonar humano». Xu et al. (2026),
[*Base Models Look Human To AI Detectors*](https://arxiv.org/abs/2605.19516), lo midieron:
en GPTZero y Pangram, el texto de un modelo **base** salió 97–99% humano y el mismo modelo
después del entrenamiento de chat, 17–30%. Nuestras pruebas coinciden: ninguna reescritura
con un modelo de chat bajó de 64% en Grammarly.

`rewrite.py` parafrasea con Qwen3-4B-Base más el adaptador HIP del artículo, con
llama.cpp, en tu CPU. Cada párrafo recibe una sola pasada (con más pasadas se aleja del
sentido) y el intento se descarta y se repite cuando:

- pierde un concepto de tu lista (nombres, términos, cifras, negaciones clave);
- sale truncado o se desboca;
- **copia el original**: más del 60% de sus palabras en tramos de 8 o más palabras
  idénticas. Un tramo copiado sigue siendo texto de IA, y los detectores lo marcan.

### 2. Conservar el sentido sin devolver la huella

`check.py` compara el original con la reescritura: cada concepto y cada negación. Luego
una persona relee cada párrafo y corrige **de una a tres palabras** como máximo. Lo que
necesite más (una oración enredada, una cita inventada, una idea perdida) lo regenera el
modelo con `rewrite.py --only N`; nunca se escribe a mano ni se pega de vuelta del
original. La regla sale de una medición: arreglos a mano de cuatro palabras o más dejaron
la mitad de un ensayo en 3%; al regenerar esos párrafos bajó a 0%.

### 3. Cambiar el ritmo

Grammarly reconoce el ritmo de la prosa de IA: oraciones de largo parejo, cada una con su
punto. Las personas escriben a ráfagas, unas largas y otras cortas. `join.py` reconstruye
ese ritmo sin tocar una sola palabra de contenido:

- `--pausas 2` (recomendado) deja dos o tres puntos por párrafo, en **bloques de largo
  disparejo**, y corta primero donde una oración ya abre con un marcador del discurso
  («Sin embargo», «Por ejemplo», «Segundo»). Dentro de cada bloque une con «y» o «;».
  Cada bloque conserva al menos dos oraciones, para que una casi copia del original nunca
  quede sola.
- Después puedes cambiar una unión por un conector lógico («sin embargo», «por eso», «es
  decir», «en cambio») donde la relación sea evidente: una o dos palabras por cambio.
- Sin `--pausas`, todas las oraciones del párrafo se unen en una sola: la primera
  versión, también en 0%, pero más difícil de leer.

### Cuánto aporta cada pieza (un cambio a la vez)

| Versión del mismo ensayo | Grammarly |
|---|---|
| Solo reescrito por el modelo base | 84% |
| … más espacios dobles al azar | 84% |
| … quitando ~35% de las comas | 60% |
| … uniendo ~60% de las oraciones | 40% |
| … uniendo todas las oraciones de cada párrafo | **8%** |
| El original, sin el modelo base, uniendo todas las oraciones | 57% |
| Reescribir con un modelo de chat (cuatro recetas distintas) | 64–100% |
| Modelo base + pausas, con una oración sola entre dos puntos | 6% |
| **Modelo base + pausas, bloques de dos o más oraciones + 12 conectores** | **0% y 0%** |

Hacen falta las dos etapas, y las faltas de ortografía no: el ruido de puntuación casi no
mueve el número, y el ritmo sí. Todas las mediciones:
[`references/evidence.md`](references/evidence.md).

### Cómo medimos

- **Dos controles en cada sesión**: un texto humano (un prólogo de Unamuno de 1914, y los
  mensajes de chat del autor, con todo y sus erratas) tiene que salir humano, y el original
  de IA tiene que salir IA. El detector que falla cualquiera de los dos no cuenta: QuillBot
  dio 100% humano al original de IA, y GPTZero, tras muchos escaneos desde el mismo
  navegador, dio 100% IA a Unamuno.
- **La referencia se vuelve a medir en la misma sesión**; nunca se compara con un número
  de horas antes: los detectores cambian y se saturan sin avisar.
- **Grammarly lee unas 1,400 palabras**, así que los textos largos se miden en mitades.

---

## Instalación

### Con tu agente (lo más fácil)

```bash
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es
python3 install.py          # en Windows: python install.py
```

Abre una sesión nueva y pide: **«humaniza este texto»**. La skill le dice al agente qué
hacer: instalar lo que falte (pregunta antes de bajar el modelo), armar contigo la lista
de lo que no se puede perder, reescribir, mostrarte cada cambio, unir y verificar.

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

**5. Mide** en tu detector, con un texto humano de control
([`references/detectors.md`](references/detectors.md)).

Hay ejemplos completos, con cada arreglo a mano anotado, en [`examples/`](examples/).

---

## Idiomas

| | Reescribe | Ritmo | Revisa | Medido |
|---|---|---|---|---|
| **Español** | ✅ | ✅ «y», «;», «sin embargo»… | ✅ | ✅ cuatro ensayos |
| **English** | ✅ (el adaptador HIP se entrenó en inglés) | ✅ "and", ";", "however"… | ✅ | todavía no |

Otros idiomas: la reescritura puede funcionar (el modelo base es multilingüe), pero
`join.py` solo conoce los conectores del español y del inglés. Agregar uno es un
diccionario pequeño en `scripts/join.py`; se aceptan pull requests.

## Detectores

| Detector | Estado |
|---|---|
| **Grammarly** | ✅ 0% en tres de cuatro ensayos; 10% en el otro |
| **GPTZero** | ✅ 0% IA · 99% humano en el ensayo que medimos |
| **ZeroGPT** | ❌ todavía no: 44.9% el original, 49.8% después. Pesa otra cosa |
| QuillBot | no sirve en español: dio 100% humano al original de IA |

Cada detector usa su propio modelo: una versión que pasa uno puede no pasar otro. Lo que
más necesitamos son mediciones en más detectores.

---

## Preguntas frecuentes

**¿Es gratis? ¿Necesito una clave de OpenAI o alguna cuenta?**
Gratis y sin claves. El modelo se baja una vez y corre en tu computadora.

**¿Cambia lo que dice mi texto?**
No debería: `rewrite.py` descarta los intentos que pierden un concepto, `check.py` revisa
conceptos y negaciones, y tú relees cada párrafo. En nuestras pruebas, los textos finales
conservaron todos los conceptos de la lista.

**¿Mete faltas de ortografía a propósito, como otros «humanizadores»?**
No. Cambia el ritmo, no la ortografía.

**¿Los resultados son consistentes?**
Tres de los cuatro ensayos llegaron a 0% en Grammarly (el cuarto, 10%, se corrió con una
versión anterior), y el más reciente también pasó GPTZero. El proceso es determinista
donde se puede (la unión usa una semilla fija), rechaza la salida copiada, y 43 pruebas
corren en cada cambio en Ubuntu, macOS y Windows. Los detectores no son estables en el
tiempo; por eso siempre medimos con controles.

**¿Necesito GPU?**
No. Corre en CPU, con prioridad baja, así que tu computadora sigue usable.

---

## Límites

1. **Medido en Grammarly y GPTZero, con ensayos en español.** ZeroGPT todavía no pasa; en
   inglés aún no se ha medido.
2. **Releer no es opcional.** El modelo base a veces cambia un detalle, inventa una cita o
   invierte una idea. El proceso atrapa los conceptos perdidos; lo demás lo atrapa una
   persona.
3. **Bloques largos.** Con `--pausas 2` los párrafos se leen con naturalidad, pero las
   oraciones siguen siendo más largas que en un ensayo pulido.
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
│   ├── rewrite.py           etapa 1: reescribe con el modelo base local
│   ├── check.py             etapa 2: conceptos y negaciones, original contra reescritura
│   └── join.py              etapa 3: reconstruye el ritmo de cada párrafo
├── examples/                ejemplos completos en español y en inglés
├── references/              todas las mediciones y cómo medir
└── tests/                   43 pruebas en Ubuntu, macOS y Windows (sin red ni modelo)
```

Los nombres viejos de los scripts (`hip.py`, `unir.py`, `verificar_fidelidad.py`,
`instalar_hip.py`) siguen funcionando.

## Contribuir

Lo que más falta es **evidencia**: el proceso medido en más textos, más idiomas y más
detectores, siempre con un control humano. Abre un issue o un PR con los números en
[`references/evidence.md`](references/evidence.md).

```bash
python3 -m unittest discover -s tests -v
```

## Créditos y licencia

Código y documentación: [MIT](LICENSE), © ervin-mo. El método y el adaptador HIP son de
Xu et al. (2026); el modelo base es Qwen3-4B-Base, de Alibaba. Ambos son Apache-2.0 y se
descargan por separado: ver [`THIRD_PARTY.md`](THIRD_PARTY.md). Si lo usas en tu trabajo,
cita el repo ([`CITATION.cff`](CITATION.cff)) y el artículo de HIP.
