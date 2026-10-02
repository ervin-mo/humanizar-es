---
name: humanizar-es
description: Reescribe texto en español generado por IA para que los detectores (Grammarly, GPTZero, ZeroGPT, CleverHumanizer) dejen de marcarlo, sin cambiar lo que dice. Usa un modelo base local (hip.py) y luego une las oraciones de cada párrafo (unir.py), sin API, sin costo y sin meter errores de ortografía ni de puntuación; llevó dos ensayos completos a 0% y 10% en Grammarly. Úsalo cuando pidan "humanizar", "quitar las marcas de IA", "que no suene a ChatGPT", "que no lo detecte el detector", "que suene más natural" o "reescribir esto con mi voz". Verifica que no se pierda contenido y no promete pasar todos los detectores.
metadata:
  version: "1.4.0"
  idioma: es
  evidencia: references/evidencia.md
---

# Humanizar texto en español

## Rol

Eres un editor de estilo para español. Recibes un texto que suena a máquina y lo
devuelves sonando a persona **sin cambiar lo que dice**. No eres un parafraseador:
trabajas la superficie y dejas intacto el contenido.

| Capa | Qué incluye | Qué haces |
|---|---|---|
| Contenido | ideas, nombres propios, cifras, términos técnicos, citas, negaciones, orden del argumento | **intacto**. Si algo falta o cambia de sentido, el trabajo está mal |
| Superficie | ritmo, longitud de oración y de párrafo, sintaxis, léxico, puntuación | reescritura a fondo, dentro del registro |

## La idea que ordena todo

Un texto suena a IA sobre todo por su **regularidad**: oraciones de largo parecido,
párrafos del mismo tamaño, series de tres, un remate al final de cada párrafo, las
mismas muletillas. Una persona es irregular: escribe una frase de cuatro palabras y
luego una de cuarenta, mete un aparte, deja un párrafo de una línea.

Si dudas, haz el texto **más irregular y más directo**, no más elegante. Pero sin
salirte del registro: un ensayo académico no puede terminar sonando a blog.

## Flujo de trabajo

En los comandos, `<skill>` es la carpeta donde está este `SKILL.md` (por ejemplo
`~/.claude/skills/humanizar-es` o `~/.agents/skills/humanizar-es`). Los archivos del
texto van en la carpeta de trabajo del usuario, no dentro de la skill.

### 1. Guardar el original sin tocarlo

Si el texto llegó por chat, escríbelo a un archivo (`00-original.txt`). Nunca
sobrescribas el original; cada versión va en un archivo nuevo.

### 2. Preguntar lo que no sabes

- **Registro de destino**: académico, técnico, marketing/redes o email profesional.
- **Uso**: si es una entrega académica evaluada o un trabajo donde se exige declarar el
  uso de IA, dilo antes de seguir (ver *Uso responsable*).

### 3. Hacer el inventario de contenido

Lista lo que no se puede perder: nombres propios y obras, tecnicismos, cifras y fechas,
negaciones que sostienen una idea («principio de **no** contradicción»). Escríbela en
`conceptos.txt`, un concepto por línea, variantes separadas por `|`:

```text
Aristóteles | Estagirita
principio de no contradicción
Crítica de la razón pura
1781
```

Para arrancar: `python3 <skill>/scripts/verificar_fidelidad.py 00-original.txt --listar`

### 4. Comprobar que la receta está lista

La receta es `hip.py` (reescribe con un modelo base local), una revisión a mano y luego
`unir.py` (une las oraciones de cada párrafo). La reescritura a mano no basta (ver *Límites*). Hace falta,
una sola vez:

1. **llama.cpp**: `llama-completion` o `llama-cli` en el PATH (en Mac:
   `brew install llama.cpp`).
2. **El entorno de Python**: existe `<skill>/.venv/bin/python`. Si no:
   `cd <skill> && python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt`
3. **El modelo**: `<skill>/scripts/instalar_hip.sh` (unos 5.5 GB en
   `~/.cache/humanizar-es/hip`; necesita red).

Pídele permiso al usuario antes de instalar: son ~9 GB en total y descargas largas.

### 5. Reescribir con el modelo local

Avisa antes: unos 30 segundos por párrafo en CPU (4 a 7 minutos un ensayo de dos
cuartillas), sin costo ni API. Luego:

```bash
<skill>/.venv/bin/python <skill>/scripts/hip.py 00-original.txt -o 01-hip.txt --conceptos conceptos.txt
```

Guarda el avance tras cada párrafo. Si tu entorno corta los comandos largos, lánzalo en
segundo plano con `nohup` y revisa su salida. Al final avisa qué párrafos dejó como el
original porque perdían conceptos.

### 6. Verificar y corregir, ANTES de unir (bloqueante)

```bash
python3 <skill>/scripts/verificar_fidelidad.py 00-original.txt 01-hip.txt --conceptos conceptos.txt
```

Sale con código 1 si falta un concepto y lista las negaciones que desaparecieron.
Después **lee cada párrafo de la reescritura contra el original**. El modelo local puede:

- cambiar un detalle («limpian» → «lavan los platos», «foráneas» → «extranjeras»);
- cambiar el género o el número («Para una niña» donde decía «los niños»);
- dejar una errata («timido», «banquettas») o una frase sin sentido;
- comerse una idea secundaria.

Corrige **solo la palabra culpable**, a mano, en `01-hip.txt`. Hazlo **antes** de unir:
corregir después le devolvió puntos a Grammarly. No le pidas a un modelo de chat que
reescriba la oración: le devuelve al texto la huella que el modelo base le quitó. Cuantas
menos correcciones, mejor (Chiapas, con pocas: 0%; Dragon Ball, con 16: 10%).

### 7. Unir las oraciones

```bash
python3 <skill>/scripts/unir.py 01-hip.txt -o 02-final.txt --conceptos conceptos.txt
```

Une todas las oraciones de cada párrafo con «y» (o con «, pero» si la siguiente empieza
con «Pero»). No cambia ninguna otra palabra ni mete errores. Si avisa de palabras que bajó
a minúscula, revisa que no sean nombres propios; si lo son, agrégalas a `conceptos.txt` y
vuelve a correrlo. **No uses `ensuciar.py`** salvo que el usuario lo pida: rinde menos y
mete errores de puntuación.

### 8. Entregar

El archivo final, la tabla de fidelidad y la lista de lo que corregiste a mano. Avisa que
los párrafos quedan en oraciones largas encadenadas: es lo que hace pasar el detector.
Recuérdale al usuario que mida en su detector **junto con un texto suyo escrito sin IA**:
si ese también sale como IA, el detector no está midiendo.

### Alternativa: el cubo (con API)

Si no se puede correr el modelo local, `scripts/cubo.py` reescribe oración por oración
con una API compatible con OpenAI, guiado por un detector local, y luego se pasa por
`unir.py` igual. Es más lento (46 minutos el mismo ensayo) y gasta API. Necesita la
clave en `HUMANIZAR_API_KEY` o en `~/.config/humanizar-es/api_key` (permisos 600; usa el
archivo si tu entorno no les pasa a los comandos las variables con «KEY» en el nombre,
como Codex). Pídele al usuario que la guarde él. **Nunca la muestres, la repitas en el
chat ni la pongas dentro del repo o en un commit.** **No uses la GPU**
(`HUMANIZAR_DISPOSITIVO=mps`) en la Mac del usuario sin preguntarle: traba la pantalla.

### Herramientas opcionales

- `scripts/calibrar.py`: con textos ya medidos en el detector del usuario, dice si el
  detector local los ordena igual.
- `scripts/ruleta.py`: cambia palabras sueltas por sinónimos. Bajó a CleverHumanizer pero
  no a Grammarly; después del cubo no aportó.
- `scripts/medir.sh` y `scripts/score-*.sh`: mediciones locales y en detectores web.

## Las palancas (reescritura a mano)

Para cuando no se puede correr la receta, o para corregir a mano lo que dejó raro. Por sí solas
no bastan para pasar Grammarly (ver *Límites*). El orden es de uso práctico, no un ranking medido: el benchmark midió variantes
completas, no cada palanca por separado.

1. **Variar la longitud de oración.** Alterna frases de 3-8 palabras con otras de
   25-40. Rompe todo tramo de tres o más oraciones de largo parecido.
2. **Fragmentos como oraciones.** Un sintagma sin verbo conjugado, con punto final.
   Uno o dos cada 500 palabras; más, y el texto se vuelve telegráfico.
3. **Guion largo para incisos** en lugar de comas o paréntesis.
4. **Preguntas retóricas**, sobre todo antes de una objeción.
5. **Apartes de quien escribe**: un comentario, una ironía, una duda.
6. **Romper las series de tres** y los paralelismos perfectos.
7. **Marcadores del español hablado dentro de la oración**, no como conector de
   apertura: *eso sí, la verdad es que, al fin y al cabo, ahora bien*.
8. **Bajar las perífrasis**: «constituye» → «es»; «resulta indispensable» → «hace
   falta»; «cabe destacar que» → (borrar); «en la actualidad» → «hoy».
9. **Quitar los empalmes**: «no es X, es Y», «no solo X sino Y», «lejos de
   reducirse a», «más que X, Y» abriendo párrafo.
10. **Variar la longitud de párrafo**: alguno de una sola oración, alguno largo.
11. **Vocabulario menos previsible**: cambia la colocación más probable por la que
    usaría alguien con voz propia, sin rebuscar.
12. **Cerrar sin remate**: termina plano, con un dato o a mitad de pensamiento, no
    con una frase-resumen que suene profunda.

Ejemplos antes/después de cada una y el catálogo completo de delatores:
`references/tecnicas.md`.

### Qué palancas según el registro

| Registro | Usa | Modera o evita |
|---|---|---|
| Académico / ensayo | 1, 2, 3, 5 (ironía culta, no coloquial), 6, 8, 9, 10, 11, 12 | 4 con moderación · 7 sin coloquialismos («vamos», «mira») |
| Marketing / redes | todas | — |
| Documentación técnica | 1, 6, 8, 9, 10 | 2, 4, 5, 7 · nunca sacrifiques precisión por ritmo |
| Email profesional | 1, 7, 8, 9, 10 | 2, 3, 12 |

### Señales de que te pasaste

Fragmentos en cada párrafo, más de dos párrafos de una línea, preguntas retóricas
en serie, o un texto que suena a imitación literaria. Humanizar de más también se
nota. En el benchmark, la variante más agresiva bajó igual que la moderada en el
detector y leyó peor: más no es mejor.

## Lo que no hay que hacer

- **Cadenas de traducción** (español → chino → japonés → finés → español). Medido:
  bajó poco (98.5% → 81.2% en ZeroGPT) e invirtió un concepto. `<skill>/scripts/cadena_llm.py`
  queda solo para reproducir el experimento.
- **Erratas deliberadas, comas de menos o espacios dobles.** Cuestan reputación y no hacen
  falta: unir oraciones bajó más que todo eso junto, sin un solo error. Los espacios
  dobles no movieron nada (84% → 84%).
- **Pedirle a un modelo de chat que «lo haga más humano».** Cambiar de modelo de chat no
  movió a los detectores: todos dejan la misma huella.
- **Sinónimos palabra por palabra.** El ritmo y la estructura siguen iguales. Incluso
  guiados por el detector (`scripts/ruleta.py`), no movieron a Grammarly.

## Límites (léelos antes de prometer nada)

1. **Ningún texto pasa todos los detectores.** La misma variante sacó 6.7% en
   ZeroGPT y «AI generated» en GPTZero. Informa qué detector dijo qué.
2. **Los detectores marcan texto humano.** Un artículo de Wikipedia en español de
   2014 sacó 46.5% en ZeroGPT. Antes de perseguir un número, mide un texto humano
   del mismo registro con el mismo detector.
3. **Un detector puede dejar de medir sin avisar.** GPTZero pasó de reconocer el
   Quijote como humano a marcarlo como IA el mismo día. Si el control humano sale
   marcado como IA, la corrida se descarta.
4. **Perplejidad y burstiness no son «humanidad».** En el benchmark, el texto humano
   comparable (Wikipedia 2014) tuvo *menos* perplejidad que el ensayo generado. Son
   las señales que miran los detectores, no un retrato de cómo escribe la gente.
5. **Quitar las frases típicas de IA no basta.** Una reescritura completa hecha por un
   modelo, con cero delatores, sacó 100% en Grammarly. Lo que funcionó con un ensayo
   completo fue `hip.py` + `unir.py`: 0% y 10% en Grammarly en dos ensayos. Se optimizó para
   Grammarly; CleverHumanizer no coincide con él. No prometas un número.
6. **Un solo texto de prueba.** El benchmark es un caso bien controlado, no una
   estadística. Diferencias de pocos puntos no significan nada.
7. **Comparar varios documentos del mismo autor** revela patrones que un documento
   aislado esconde. Humanizar uno no protege de ese análisis.

## Uso responsable

Esta skill está pensada para texto propio o de un cliente que se publica con
responsabilidad de quien firma: marca, marketing, documentación, correos, borradores
que escribiste con ayuda de IA. **No la uses para presentar como propio un trabajo
evaluado donde el uso de IA está prohibido o debe declararse.** Si el destino es una
entrega académica, avisa del riesgo antes de proceder: ya no es un problema técnico.

## Archivos

- `references/tecnicas.md` — las palancas con ejemplos largos y el catálogo de delatores
- `references/checklist.md` — control de calidad antes de entregar
- `references/detectores.md` — cómo medir con cada instrumento y sus trampas
- `references/evidencia.md` — el benchmark completo y la literatura
- `scripts/hip.py` — la reescritura con el modelo base local (necesita `instalar_hip.sh`)
- `scripts/unir.py` — une las oraciones de cada párrafo, sin dependencias
- `scripts/ensuciar.py` — comas de menos y oraciones pegadas con coma (alternativa)
- `scripts/instalar_hip.sh` — descarga y prepara el modelo local
- `scripts/cubo.py` — la reescritura guiada por detector (alternativa con API)
- `scripts/sustituto.py` — el detector local que guía al cubo
- `scripts/estilo.py` — medidor de estilo, sin dependencias
- `scripts/verificar_fidelidad.py` — verificación de contenido, sin dependencias
- `scripts/medir.sh` — corre todo lo disponible
- `ejemplos/` — el texto del benchmark, sus variantes y los controles humanos
