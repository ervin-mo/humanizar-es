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
| `conceptos-metafisica.txt` | Los 27 conceptos que no se podían perder |
| `controles/` | Dos textos humanos para calibrar los detectores (ver su `LEEME.md`) |

## Números clave

| Texto | ZeroGPT (% IA) | Fidelidad | Variación de oración (CV) |
|---|---|---|---|
| 00 original | 98.5% | — | 0.36 |
| **01 reglas de estilo** | **7.7%** | **27/27** | **0.53** |
| 02 cadena de traducción | 81.2% | 25/27 | 0.36 |
| 03 adversarial | 6.7% | 27/27 | 0.68 |
| Control humano: Wikipedia 2014 | 46.5% | — | 0.51 |
| Control humano: Quijote (1605) | 23.7% | — | 0.60 |

GPTZero marcó como IA las cuatro variantes y el control de Wikipedia, y no fue reproducible.
Grammarly solo se pudo medir en el original.

## Cómo reproducirlo

Ver [`references/evidencia.md` §9](../references/evidencia.md#9-reproducir).
