# Evidencia: el benchmark detrás de esta skill

Todo lo que la skill recomienda está respaldado aquí por una medición propia o por
literatura. Lo que no tiene respaldo se marca como tal.

Mediciones web: 30 de septiembre de 2026. Mediciones locales: repetidas el mismo día
con la versión publicada de los scripts.

---

## 1. Diseño

**Texto de prueba:** ensayo «El enigma del ser: Fundamentos, crisis y vigencia de la
metafísica», generado con IA. ~725 palabras, registro académico. Grammarly le dio
«100% of this text appears to be AI-generated», resultado que se reprodujo antes de
empezar.

**Variantes:**

| # | Método | Qué se hizo |
|---|---|---|
| 00 | línea base | el texto sin tocar |
| 01 | reglas de estilo | las palancas de `tecnicas.md` aplicadas respetando el registro académico |
| 02 | cadena de traducción | ES →(LLM, temp 1.3)→ ZH →(LLM, temp 1.3)→ JA →(LLM)→ FI →(LLM)→ ES |
| 03 | adversarial | reescritura agresiva: fragmentos, párrafos de una línea, subjetividad, ritmo forzado |

Las variantes 01 y 03 las escribió un modelo siguiendo las reglas, en una sola pasada,
sin iterar contra el detector. La 02 la produjo `scripts/cadena_llm.py`.

**Controles humanos** (`ejemplos/controles/`, con su origen y licencia en el `LEEME.md`):

- Quijote, 1605 — solo para comprobar que un instrumento distingue algo
- Wikipedia «Metafísica», revisión de dic-2014 — académico moderno, mismo tema, anterior
  a los LLM actuales: **el control comparable**

**Instrumentos:** ZeroGPT, GPTZero y Grammarly (web); perplejidad, burstiness y un
clasificador (local); `estilo.py` (estadística de estilo); `verificar_fidelidad.py`.

---

## 2. Detectores web

### ZeroGPT

| Texto | Veredicto | % IA |
|---|---|---|
| Control Quijote | Most Likely Human written | 23.7% |
| Control Wikipedia 2014 | contains mixed signals | 46.5% |
| 00 original | AI/GPT Generated | 98.5% |
| **01 reglas de estilo** | **Human written** | **7.7%** |
| 02 cadena de traducción | AI/GPT Generated | 81.2% |
| **03 adversarial** | **Human written** | **6.7%** |

El Quijote dio 23.7% en dos corridas separadas: el instrumento fue estable.

### GPTZero

| Texto | Veredicto | % humano |
|---|---|---|
| Control Quijote | entirely human | 99% |
| Control Wikipedia 2014 | AI generated | 0% |
| 00, 01, 02 y 03 | AI generated | 0% |

Una sola corrida. Más tarde, el mismo día, GPTZero marcó el **mismo archivo** del
Quijote como IA (0% humano) en dos corridas, y también una anécdota personal breve
escrita a mano. El script comprueba que la página de resultados contenga una huella del
texto enviado, así que no fue un error de lectura: el detector cambió de opinión.
**Estos números no sirven como evidencia de mejora ni de fracaso.**

### Grammarly

En la corrida automatizada solo se pudo medir el original (100% IA): después del primer
escaneo dejó de arrancar nuevos escaneos (detalle en `detectores.md` §5). Después se
midió a mano, con sesión iniciada:

| Texto | Grammarly |
|---|---|
| 00 original | 100% IA |
| 01 reglas de estilo | **75% IA** |
| 04 reescritura completa | **100% IA** |

La variante 04 (`ejemplos/04-reescritura-completa.txt`) se escribió después, con la
guía corregida: un modelo reescribió el texto entero quitando todos los delatores. Ver §4b.
Cada número es un solo escaneo; no se ha comprobado si Grammarly los repite.

---

## 3. Instrumento local

| Texto | Perplejidad | Burstiness | P(IA) clasificador |
|---|---|---|---|
| 00 original | 12.33 | 10.19 | 99.97% |
| 01 reglas de estilo | 16.50 | 38.94 | 99.97% |
| 02 cadena de traducción | 11.79 | 12.45 | 99.97% |
| 03 adversarial | 17.54 | 68.53 | 99.97% |
| Control Quijote | 28.50 | 58.23 | 0.19% |
| **Control Wikipedia 2014** | **10.35** | **16.24** | **99.96%** |

Tres lecturas:

1. **Perplejidad y burstiness ordenan igual que ZeroGPT.** Las variantes que bajaron
   en el detector las subieron; la cadena de traducción bajó la perplejidad por debajo
   del original.
2. **No son una medida de «humanidad».** El texto humano comparable es más previsible
   que el ensayo generado y tiene menos de la mitad de burstiness que la variante 01. Reflejan lo
   que premian los detectores. La versión anterior de esta documentación comparaba
   contra el Quijote (58.23) como si fuera «el nivel humano»: eso medía arcaísmo.
3. **El clasificador no sirve en español.** Su ficha dice que se afinó en inglés, chino
   y vietnamita. Marca como IA el control humano moderno; solo separa el Quijote.

---

## 4. Estilo (`scripts/estilo.py`, sin dependencias)

| Texto | Palabras/oración | Variación (CV) | % oraciones ≤8 pal. | Delatores |
|---|---|---|---|---|
| 00 original | 29.0 | 0.36 | 0 | 9 |
| 01 reglas de estilo | 19.9 | 0.53 | 13 | 3 |
| 02 cadena de traducción | 24.6 | 0.36 | 0 | 4 |
| 03 adversarial | 15.1 | 0.68 | 31 | 3 |
| Control Wikipedia 2014 | 28.9 | 0.51 | 4 | 1 |
| Control Quijote | 86.4 | 0.60 | 0 | 0 |

La variación relativa de longitud de oración (CV) separa lo que bajó en el detector
(0.53, 0.68) de lo que no (0.36), y la variante 01 queda prácticamente en el valor
del humano comparable (0.51). La desviación absoluta, en cambio, casi no cambió (10.6 → 10.5 y
10.3): las variantes metieron oraciones cortas entre las largas, no oraciones más largas.

Las variantes medidas conservan delatores que la guía manda quitar («Lejos de
reducirse», «Resulta indispensable», «En última instancia», «no es X: es Y»). Bajaron en el detector
con ellos dentro; una edición más cuidadosa los quitaría.

### 4b. Lo que la variante 04 enseñó

Por todas las métricas de este repositorio, la 04 era «más humana» que la 01: cero
delatores (contra 3), variación de oración 0.58 (contra 0.53), perplejidad 17.13
(contra 16.50) y burstiness 54.82 (contra 38.94). Grammarly la marcó **100% IA**; a la
01, 75%.

Conclusión: **ni `estilo.py` ni el instrumento local predicen a Grammarly.** Sirven
para encontrar delatores concretos y comparar versiones, no para anticipar el veredicto
de un clasificador comercial.

Hipótesis, sin comprobar: Grammarly reconoce la prosa fluida de un modelo aunque no
tenga los delatores de la lista. La 04 es una reescritura completa hecha por un modelo;
la 01 conserva más giros ásperos («La metafísica. Ahí está…», «Preguntas viejas, más o
menos, con ropa nueva»). Si es así, lo que baja el score no es quitar marcas sino meter
lo que un modelo no escribe: voz, ejemplos y decisiones del autor.

### 4c. El cubo: reescritura guiada por un detector local

Después de 4b se construyó `scripts/cubo.py` (ver README). Primero se comprobó que el
detector local (`scripts/sustituto.py`, Binoculars + Fast-DetectGPT sobre Qwen2.5-0.5B)
ordenaba como Grammarly las versiones ya medidas: lo hizo en las tres (00, 01, 04),
incluida la 04 que `estilo.py` daba por buena.

Grammarly, medido a mano, un escaneo por texto:

| Texto | Grammarly | Sustituto 0.5B | Nota |
|---|---|---|---|
| Párrafo 1 original | 100% | −0.49 | control |
| **Párrafo 1 por el cubo** | **0%** | −4.89 | `ejemplos/parrafo/` |
| Ensayo, cubo con un error (solo giró 10 de 25 oraciones) | 80% | −4.63 | no incluido |
| **Ensayo, cubo completo desde el original** | **39%** | −10.45 | `05-cubo-desde-original.txt` |
| Ensayo, cubo desde la 01 con criterio de ritmo | 42% | −10.69 | `06-cubo-desde-01.txt` |

Calibración (`scripts/calibrar.py`) contra los seis ensayos medidos en Grammarly:
correlación de rangos **0.87** con el sustituto de 0.5B y **0.93** con el de 1.5B. El de
1.5B nunca participó en el bucle y aun así ve mucho más humanas las versiones del cubo:
la mejora no es solo un engaño al modelo chico.

**El techo.** De 05 a 06 el sustituto siguió bajando, pero Grammarly no (39% → 42%).
CleverHumanizer marcó 80% y 81%; en la 06 ya no señaló «longitud uniforme» ni «ritmos
similares», pero siguió con «falta de voz propia», «frases predecibles» y «uso
repetitivo de palabras clave».

**El costo en calidad.** Revisadas a mano contra el original, las versiones 05 y 06
tienen 3 y 4 oraciones con el sentido desviado; la 06 inventó un ejemplo («una piedra,
una promesa, un número»). El sustituto premia el orden invertido y las palabras poco
comunes. Por eso se agregó un revisor de sentido: en una prueba con esos 7 errores reales
y 3 giros correctos, `deepseek-v4.1-flash` vetó los 7 errores y uno de los correctos.
**El cubo con revisor no se ha medido en Grammarly todavía.**

### 4d. El párrafo que pasó los dos detectores, y la ruleta

El primer párrafo del ensayo, medido a mano en Grammarly y en CleverHumanizer
(`ejemplos/parrafo/`):

| Versión | Grammarly | CleverHumanizer |
|---|---|---|
| Original | 100% IA | — |
| Solo ruleta (`scripts/ruleta.py`) | 100% IA | 76% humano |
| **Solo cubo** | **0% IA** | **99% humano** |
| Cubo + ruleta | 0% IA | 92% humano |

Lecturas:

1. **El cubo solo pasó los dos detectores.** Reescribe la estructura de cada oración, que
   es lo que mira Grammarly.
2. **La ruleta** (sinónimos palabra por palabra guiados por el mismo detector local, la
   idea de Shi et al., TACL 2023) movió a CleverHumanizer pero **no a Grammarly**, y
   después del cubo no aportó.
3. **El detector local no anticipó esa diferencia:** le dio mejor puntaje a la ruleta
   (−7.65) que al cubo (−4.89). Con cambios de estructura ordena como Grammarly; con
   cambios de palabras sueltas se deja engañar por el vocabulario poco común.

**Por qué el párrafo pasó y el ensayo no (hipótesis, sin comprobar).** En el párrafo el
cubo giró todas las oraciones; en el ensayo, girado de una vez, varias quedaron sin cambio,
y Grammarly parece puntuar por tramos. Además, un texto largo le da más evidencia al
detector. Por eso `cubo.py` trabaja ahora párrafo por párrafo, como en esta prueba. **Ese
modo no se ha medido todavía con un ensayo completo.**

---

## 5. Fidelidad de contenido

27 conceptos del original (`ejemplos/conceptos-metafisica.txt`):

| Texto | Conceptos |
|---|---|
| 01 reglas de estilo | 27/27 |
| **02 cadena de traducción** | **25/27** |
| 03 adversarial | 27/27 |

Lo que perdió la cadena de traducción:

1. «principio de **no** contradicción» → «principio de contradicción». No es una
   omisión: invierte el sentido, y ningún corrector ortográfico lo detecta.
   `verificar_fidelidad.py` ahora además lista las negaciones desaparecidas; esta
   aparece.
2. «subatómico» desapareció.

**Qué no mide este número.** Solo cuenta los 27 conceptos de la lista. La variante 03,
con 27/27, eliminó el subtítulo del ensayo («Fundamentos, crisis y vigencia de la
metafísica»). Por eso la guía pide releer el texto completo además de correr el script.

---

## 6. Literatura

**Los ataques bajan el score pero no borran la huella.**
[*Attacks on Machine-Text Detectors Retain Stylistic Fingerprints*](https://arxiv.org/abs/2505.14608)
(arXiv, 2025): los ataques actuales, desde prompts hasta optimización guiada por el
detector, degradan a los detectores estándar pero dejan una huella estilística que los
detectores basados en estilo siguen viendo, sobre todo cuando se analizan varios
documentos del mismo autor.

**Los detectores comerciales fallan en los dos sentidos.**
[Prueba de Langara College sobre Turnitin](https://iweb.langara.ca/edtech/files/2026/02/Turnitin_AI_Detection_Accuracy-Sept2025.pdf)
(septiembre de 2025): obtener 0% con texto generado fue fácil (ediciones humanas
mínimas, un humanizador o un modelo de pago sin editar); la actualización
«anti-humanizer» de Turnitin no los detectó; y Turnitin reconoce que el texto de
personas no nativas en inglés se marca más como IA porque varía menos en estructura y
vocabulario.

**El método con mejor respaldo publicado.**
[chengez/Adversarial-Paraphrasing](https://github.com/chengez/Adversarial-Paraphrasing)
(NeurIPS 2025): parafraseo guiado por un detector, sin entrenamiento y transferible
entre detectores. La variante 03 es una aproximación manual de una sola pasada a esa
idea, sin el bucle de retroalimentación.

**El método que se descartó.**
[lynote-ai/humanize-text](https://github.com/lynote-ai/humanize-text) (~3k estrellas):
dos reescrituras con LLM a temperatura 1.3 y luego dos saltos con motores de
traducción automática, partiendo del inglés. La variante 02 lo adapta al español y usa
un LLM en todos los saltos, así que el resultado describe esta adaptación, no
necesariamente al repositorio original.

---

## 7. Conclusiones

Lo que el benchmark sostiene, con su tamaño de muestra en mente:

1. **Las reglas de estilo funcionaron en este texto**: ZeroGPT pasó de 98.5% a 7.7%
   conservando los 27 conceptos. Es una brecha grande en un instrumento estable, pero
   es un solo texto.
2. **La variante agresiva no aportó nada medible** (6.7% frente a 7.7% es ruido) y se
   aleja más del humano comparable. Se recomienda la moderada.
3. **La cadena de traducción se descarta**: bajó poco (81.2%), empeoró la perplejidad
   y corrompió contenido.
4. **Los detectores se contradicen** sobre el mismo texto: 6.7% en ZeroGPT, «AI
   generated» en GPTZero.
5. **Los detectores marcan texto humano** del mismo registro: 46.5% en ZeroGPT; IA en
   GPTZero y en el clasificador local. Antes de optimizar contra un detector hay que
   medir cómo trata a un texto humano parecido.
6. **Sin control humano en la misma corrida, un detector degradado se lee como «la
   humanización falló».** Por eso el control es obligatorio.

7. **Las métricas propias no predicen a Grammarly**: la variante con mejores números
   (04) sacó 100%, y la 01 sacó 75% (§4b).

Lo que **no** sostiene: que las palancas funcionen igual en otros textos o registros,
qué palanca pesa más, ni que una reescritura hecha solo por un modelo baje en
Grammarly (la evidencia apunta a lo contrario).

---

## 8. Limitaciones

1. **Un solo texto de prueba**, de un solo registro (académico).
2. **Grammarly se midió a mano, un escaneo por texto**, sin repetir y sin control humano.
3. **GPTZero no fue reproducible** en la misma sesión.
4. **Las variantes las escribió un modelo**, en una pasada. No se comparó contra
   reescrituras hechas por personas.
5. **La fidelidad se mide sobre una lista**, no sobre el texto completo.
6. **El clasificador local está fuera de dominio**; la validación cruzada se apoya en
   ZeroGPT, perplejidad/burstiness y `estilo.py`.

Contribuciones que harían esto más sólido: más textos y registros (marketing, técnico,
correos), controles humanos de cada registro, y mediciones en Grammarly con cuenta.

---

## 9. Reproducir

Desde la raíz del repositorio:

```bash
# sin dependencias
python3 scripts/estilo.py ejemplos/0*.txt ejemplos/controles/control-wikipedia-metafisica-2014.txt
python3 scripts/verificar_fidelidad.py ejemplos/00-original.txt ejemplos/01-reglas-estilo.txt \
        ejemplos/02-cadena-traduccion.txt ejemplos/03-adversarial.txt \
        --conceptos ejemplos/conceptos-metafisica.txt

# perplejidad y burstiness (requiere el .venv)
.venv/bin/python scripts/detect_local.py ejemplos/0*.txt ejemplos/controles/*.txt --clasificador

# detectores web (requiere ego lite; usan la red y tienen límites de uso)
scripts/score-zerogpt.sh ejemplos/0*.txt ejemplos/controles/*.txt
scripts/score-gptzero.sh ejemplos/0*.txt ejemplos/controles/*.txt
```

Los números locales y de estilo deben salir idénticos. Los web pueden variar: los
detectores cambian sin avisar. Si regeneras la variante 02, cambiará (temperatura 1.3).
