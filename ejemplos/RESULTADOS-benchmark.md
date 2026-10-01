# Benchmark: resumen

El análisis completo, con la literatura y las limitaciones, está en
[`references/evidencia.md`](../references/evidencia.md). Este archivo solo explica
qué hay en esta carpeta y los números clave.

## Archivos

| Archivo | Qué es |
|---|---|
| `00-original.txt` | Ensayo de metafísica generado con IA (~725 palabras). Grammarly: 100% IA |
| `01-reglas-estilo.txt` | Reescrito con las palancas de la guía, respetando el registro académico |
| `02-cadena-traduccion.txt` | Pasado por ES → ZH → JA → FI → ES con `scripts/cadena_llm.py` |
| `03-adversarial.txt` | Reescritura agresiva |
| `04-reescritura-completa.txt` | Reescritura completa posterior, con la guía corregida y cero delatores |
| `05-cubo-desde-original.txt` | El original pasado por `scripts/cubo.py` (sin revisor de sentido) |
| `06-cubo-desde-01.txt` | La variante 01 pasada por el cubo, con criterio de ritmo |
| `parrafo/` | Un párrafo suelto: original y su versión del cubo |
| `conceptos-metafisica.txt` | Los 27 conceptos que no se podían perder |
| `controles/` | Dos textos humanos para calibrar los detectores (ver su `LEEME.md`) |

## Números clave

| Texto | ZeroGPT (% IA) | Grammarly (% IA) | Fidelidad | Variación de oración (CV) |
|---|---|---|---|---|
| 00 original | 98.5% | 100% | — | 0.36 |
| **01 reglas de estilo** | **7.7%** | **75%** | **27/27** | **0.53** |
| 02 cadena de traducción | 81.2% | — | 25/27 | 0.36 |
| 03 adversarial | 6.7% | — | 27/27 | 0.68 |
| 04 reescritura completa | — | 100% | 27/27 | 0.58 |
| **05 cubo desde el original** | — | **39%** | 27/27 | 0.36 |
| 06 cubo desde la 01 | — | 42% | 27/27 | 0.50 |
| Párrafo: original → cubo | — | **100% → 0%** | — | — |
| Control humano: Wikipedia 2014 | 46.5% | — | — | 0.51 |
| Control humano: Quijote (1605) | 23.7% | — | — | 0.60 |

En CleverHumanizer, el párrafo del cubo sacó **99% humano** (ver `parrafo/LEEME.md`).

GPTZero marcó como IA las cuatro variantes y el control de Wikipedia, y no fue reproducible.
Grammarly se midió a mano, un escaneo por texto. La 04, con cero delatores y mejores
métricas propias que la 01, sacó 100%: las métricas del repo no predicen a Grammarly
(ver `references/evidencia.md` §4b). Lo que sí bajó fue el cubo (§4c).
CleverHumanizer marcó 80% y 81% a las variantes 05 y 06; el original no se midió ahí.

## Cómo reproducirlo

Ver [`references/evidencia.md` §9](../references/evidencia.md#9-reproducir).
