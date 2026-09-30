# humanizar-es

[![pruebas](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml/badge.svg)](https://github.com/ervin-mo/humanizar-es/actions/workflows/pruebas.yml)
[![licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)

Guía y herramientas para que un texto en español **deje de sonar a IA sin cambiar lo
que dice**, con mediciones reproducibles en lugar de promesas.

Sirve de dos formas:

- **Como skill para un agente** (Claude Code, Codex y otros que lean `SKILL.md`): le
  pides «humaniza este texto» y sigue el método, verifica que no se perdió contenido y
  te entrega el antes y el después.
- **A mano**: la guía de reescritura está en `references/tecnicas.md` y los medidores
  son scripts de Python sin dependencias.

> *English summary at the end.*

---

## Qué resultado da

Sobre un ensayo académico generado con IA (Grammarly: 100% IA):

| Versión | ZeroGPT | Conceptos conservados |
|---|---|---|
| Original | 98.5% IA | — |
| **Reescrito con esta guía** | **7.7% IA** | **27 de 27** |
| Pasado por una cadena de traducción (método popular) | 81.2% IA | 25 de 27 — invirtió «principio de *no* contradicción» |

Y la otra mitad de la historia, igual de importante: **un artículo de Wikipedia en
español escrito por personas en 2014 sacó 46.5% en ZeroGPT**, y GPTZero lo marcó como
IA. Los detectores se equivocan con texto humano; por eso este proyecto mide siempre
contra un control humano y nunca promete «pasar todos los detectores».

Y un resultado en contra, que también cuenta: en Grammarly, esa versión bajó solo a
**75%**, y una reescritura completa posterior, con **cero** frases típicas de IA y
mejores números en todas las métricas de este repo, sacó **100%**. Quitar las marcas no
basta cuando el texto entero lo vuelve a escribir un modelo; lo que más falta es voz
propia del autor.

Es un solo texto de prueba: una demostración bien controlada, no una estadística. El
detalle, con sus limitaciones, está en [`references/evidencia.md`](references/evidencia.md).

---

## Empieza en un minuto (sin instalar nada)

Solo necesitas Python 3.9 o más reciente.

```bash
git clone https://github.com/ervin-mo/humanizar-es.git
cd humanizar-es

# 1. ¿Qué delata a tu texto?
python3 scripts/estilo.py mi-texto.txt

# 2. Reescríbelo (guía: references/tecnicas.md) y guárdalo como mi-texto-v2.txt

# 3. ¿Mejoró? ¿Se perdió algo?
python3 scripts/estilo.py mi-texto.txt mi-texto-v2.txt
python3 scripts/verificar_fidelidad.py mi-texto.txt mi-texto-v2.txt
```

`estilo.py` te dice, entre otras cosas, qué tan pareja es la longitud de tus oraciones y
qué frases típicas de IA encontró, con ejemplos del propio texto:

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

`verificar_fidelidad.py` comprueba que los nombres, cifras y términos del original
sigan en la versión nueva, y avisa si desapareció una negación. Para trabajo serio,
dale tu propia lista de conceptos (ver [Verificar el contenido](#verificar-el-contenido)).

---

## Instalarlo como skill

```bash
./install.sh                    # Claude Code  → ~/.claude/skills/humanizar-es
./install.sh --agente agents    # ~/.agents/skills (Codex y otros)
./install.sh --destino RUTA     # otra carpeta de skills (crea RUTA/humanizar-es)
./install.sh --symlink          # enlaza en vez de copiar, para editar en vivo
./install.sh --desinstalar      # quitarla (combínalo con --agente o --destino)
```

Abre una sesión nueva y pide, en lenguaje normal:

> «humaniza este texto sin cambiar lo que dice», «quítale lo de ChatGPT a este correo»,
> «esto sacó 90% en un detector; déjalo más natural, es para el blog de la empresa»

El agente te preguntará el registro (académico, técnico, marketing, correo) si no lo
dijiste, porque cambia qué técnicas puede usar.

---

## El método en breve

Un texto suena a IA sobre todo por su **regularidad**: oraciones del mismo largo,
párrafos iguales, series de tres, remates al final de cada párrafo, las mismas
muletillas. Las palancas, con ejemplos antes/después en
[`references/tecnicas.md`](references/tecnicas.md):

1. Variar la longitud de oración: frases cortas entre las largas.
2. Fragmentos como oraciones, con moderación.
3. Guion largo para incisos.
4. Preguntas retóricas.
5. Apartes de quien escribe.
6. Romper las series de tres.
7. Marcadores del español hablado dentro de la oración (*eso sí, ahora bien*).
8. Bajar las perífrasis: «constituye» → «es», «cabe destacar que» → nada.
9. Quitar empalmes: «no solo X sino Y», «no es X, es Y», «lejos de reducirse a».
10. Variar la longitud de párrafo.
11. Vocabulario menos previsible, sin rebuscar.
12. Cerrar sin frase-resumen grandilocuente.

No todas valen en todo registro: en un texto técnico o académico se moderan varias. La
tabla está en `SKILL.md`.

**Lo que no funciona (medido):** cadenas de traducción a idiomas distantes (bajan poco
y corrompen contenido), cambiar palabras por sinónimos sin tocar la estructura, y
meter erratas a propósito.

---

## Verificar el contenido

Humanizar solo sirve si el texto sigue diciendo lo mismo. Haz una lista de lo que no se
puede perder, un concepto por línea (variantes separadas por `|`):

```text
# conceptos.txt
Aristóteles | Estagirita
principio de no contradicción
Crítica de la razón pura
1781
```

```bash
python3 scripts/verificar_fidelidad.py original.txt reescrito.txt --conceptos conceptos.txt
```

Ignora mayúsculas y acentos, sale con código `1` si falta algo (útil en scripts) y lista
las negaciones del original que ya no aparecen igual. Para arrancar la lista:
`python3 scripts/verificar_fidelidad.py original.txt --listar`.

El script verifica la lista, no el texto entero: relee también el resultado contra el
original.

---

## Medir con más instrumentos (opcional)

| Instrumento | Requiere | Para qué |
|---|---|---|
| `scripts/estilo.py` | Python | regularidad y delatores; compara versiones |
| `scripts/verificar_fidelidad.py` | Python | que no se pierda contenido |
| `scripts/detect_local.py` | `torch` y `transformers` (~2 GB) | perplejidad y burstiness con un modelo local |
| `scripts/score-zerogpt.sh`, `score-gptzero.sh` | [ego lite](https://lite.ego.app/) (macOS; su comando es `ego-browser`) | detectores web automatizados |
| `scripts/score-grammarly.sh` | ego lite + sesión de Grammarly | detector de Grammarly (se corre aparte) |
| `scripts/medir.sh` | Python | corre todo lo anterior que tengas instalado, salvo Grammarly |

```bash
# modelo local
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt

# todo lo disponible sobre dos versiones del mismo texto
scripts/medir.sh original.txt reescrito.txt --conceptos conceptos.txt
```

Sin ego lite puedes pegar el texto a mano en [ZeroGPT](https://www.zerogpt.com/) o en el
detector que uses. Lo importante es pegar también un texto humano tuyo del mismo tipo:
si el detector lo marca como IA, su número sobre tu texto no significa nada.

Trampas de cada detector (anuncios que bloquean el clic, porcentajes que no son el
score, límites de uso gratuito): [`references/detectores.md`](references/detectores.md).

---

## Límites

1. **Ningún texto pasa todos los detectores.** La misma versión sacó 6.7% en ZeroGPT y
   «AI generated» en GPTZero.
2. **Los detectores marcan texto humano**, sobre todo en registro formal.
3. **Un detector puede cambiar de opinión** sobre el mismo texto el mismo día (le pasó
   a GPTZero con el Quijote).
4. **Las métricas de este repo no predicen a los detectores comerciales.** La versión
   con mejores números sacó 100% en Grammarly. Perplejidad y burstiness tampoco miden
   «humanidad»: el texto humano comparable fue *más* previsible que el generado.
5. **Un solo texto de prueba**, académico. No sabemos cuánto se generaliza.
6. **Analizar varios documentos del mismo autor** revela patrones que uno solo no
   muestra; humanizar un texto no protege de eso.

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
├── SKILL.md              instrucciones para el agente
├── install.sh            instala la skill
├── references/
│   ├── tecnicas.md       las palancas con ejemplos y el catálogo de delatores
│   ├── checklist.md      control de calidad antes de entregar
│   ├── detectores.md     cómo medir con cada instrumento y sus trampas
│   └── evidencia.md      el benchmark completo y la literatura
├── scripts/              medidores (ver tabla de arriba) y el experimento descartado
├── ejemplos/             texto de prueba, sus 3 reescrituras y 2 controles humanos
└── tests/                pruebas de los scripts sin dependencias
```

## Contribuir

Lo que más falta es **evidencia**: más textos de prueba, de otros registros (marketing,
técnico, correos) y de otros países hispanohablantes, cada uno con un control humano
del mismo registro. También nuevos delatores para `estilo.py`, con un ejemplo real.

Antes de abrir un PR:

```bash
python3 -m unittest discover -s tests -v
```

Si agregas un delator, agrega su prueba. Si cambias un número del benchmark, cambia
también `references/evidencia.md`.

## Licencia

Código y documentación: [MIT](LICENSE). El control de Wikipedia
(`ejemplos/controles/control-wikipedia-metafisica-2014.txt`) es de sus autores bajo
CC BY-SA 3.0; detalle en [`ejemplos/controles/LEEME.md`](ejemplos/controles/LEEME.md).

---

## English summary

A guide and toolkit for making Spanish text that reads as AI-generated sound
human-written **without changing what it says**. It works as an agent skill
(`SKILL.md`, installable with `./install.sh`) or by hand. It ships two
dependency-free Python tools: `estilo.py` (sentence-length regularity and a catalog of
Spanish AI "tells") and `verificar_fidelidad.py` (checks that names, figures, terms and
negations survive the rewrite). On one academic test essay, the style rules took
ZeroGPT from 98.5% to 7.7% AI with all 27 key concepts preserved, while a popular
translation-chain method only reached 81.2% and inverted a concept. A human-written
2014 Wikipedia article scored 46.5% on the same detector: detectors misfire, so every
measurement here is paired with a human control. It does not promise to beat every
detector, and it is not meant for passing off graded work.
