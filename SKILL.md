---
name: humanizar-es
description: Edita texto en español que suena generado por IA para que suene escrito por una persona, sin cambiar lo que dice ni su registro, y mide el antes y el después con herramientas reproducibles. Úsalo cuando pidan "humanizar", "quitar las marcas de IA", "que no suene a ChatGPT", "que suene más natural", "reescribir esto con mi voz", o cuando un texto salió alto en un detector como Grammarly, GPTZero o ZeroGPT. Verifica que no se pierda contenido y no promete pasar todos los detectores.
metadata:
  version: "1.1.0"
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
`~/.claude/skills/humanizar-es`). Trabaja los archivos del texto en la carpeta del
usuario, no dentro de la skill.

### 1. Guardar el original sin tocarlo

Si el texto llegó por chat, escríbelo a un archivo (`00-original.txt`). Nunca
sobrescribas el original; cada versión va en un archivo nuevo.

### 2. Preguntar lo que no sabes

Antes de reescribir necesitas dos datos. Si no están claros, pregúntalos:

- **Registro de destino**: académico, técnico, marketing/redes, email profesional.
- **Uso**: si es una entrega académica evaluada o un trabajo donde la institución
  exige declarar el uso de IA, dilo antes de seguir (ver *Uso responsable*).

### 3. Medir el punto de partida

```bash
python3 <skill>/scripts/estilo.py 00-original.txt
```

No necesita instalar nada. Te da la variación de longitud de oración, los tramos de
oraciones parejas y los delatores concretos que hay que quitar, con ejemplos.
`<skill>/scripts/medir.sh` corre además los instrumentos opcionales que estén instalados.

### 4. Hacer el inventario de contenido

Lista lo que no se puede perder: nombres propios y obras, tecnicismos y términos en
otra lengua, cifras y fechas, negaciones que sostienen una idea («principio de **no**
contradicción»), relaciones lógicas (causa, contraste, concesión) y el orden del
argumento. Escríbela en `conceptos.txt`, un concepto por línea:

```text
Aristóteles | Estagirita
principio de no contradicción
Crítica de la razón pura
1781
```

Para arrancar puedes pedir una lista automática y depurarla:
`python3 <skill>/scripts/verificar_fidelidad.py 00-original.txt --listar`

### 5. Reescribir

Aplica las palancas de la sección siguiente **que permite el registro** (tabla de
registros más abajo). El efecto viene de acumularlas, no de una sola. Guarda el
resultado con un nombre que diga qué hiciste: `01-reglas-estilo.txt`, no `v2.txt`.

### 6. Verificar fidelidad (bloqueante)

```bash
python3 <skill>/scripts/verificar_fidelidad.py 00-original.txt 01-reglas-estilo.txt --conceptos conceptos.txt
```

Sale con código 1 si falta un concepto. Además lista las negaciones del original
que ya no aparecen igual: revísalas una por una. La mayoría son reformulaciones
válidas; la que importa es la que invierte el sentido. En el benchmark, un método
convirtió «principio de no contradicción» en «principio de contradicción» y ningún
corrector lo detectó.

El script solo comprueba lo que está en la lista. Relee además el texto completo
contra el original: títulos, subtítulos y matices no se verifican solos.

### 7. Medir el resultado y entregar

```bash
python3 <skill>/scripts/estilo.py 00-original.txt 01-reglas-estilo.txt
```

Entrega: el archivo reescrito, la tabla de fidelidad, la tabla de estilo antes y
después y, si se usaron detectores, cada score **con el nombre del detector** y el
resultado del control humano. Si un detector no se pudo usar, dilo.

## Las palancas

El orden es de uso práctico, no un ranking medido: el benchmark midió variantes
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
- **Erratas deliberadas.** Cuestan reputación en cualquier texto firmado y no
  resuelven la regularidad, que es lo que delata.
- **Sinónimos palabra por palabra.** El ritmo y la estructura siguen iguales; es el
  «parafraseo ciego» que la literatura documenta como inútil.

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
5. **Las métricas no predicen a Grammarly.** Una reescritura completa hecha por un
   modelo, con cero delatores y mejores números que otra versión, sacó 100% contra 75%.
   No prometas que bajar los delatores bajará el score. Lo que un modelo no puede
   aportar es la voz del autor: pídele un ejemplo, una opinión o una anécdota suya y
   déjalos en su forma de decirlo.
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
- `scripts/estilo.py` — medidor de estilo, sin dependencias
- `scripts/verificar_fidelidad.py` — verificación de contenido, sin dependencias
- `scripts/medir.sh` — corre todo lo disponible
- `ejemplos/` — el texto del benchmark, sus variantes y los controles humanos
