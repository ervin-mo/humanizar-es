# El párrafo que pasó los dos detectores

El primer párrafo del ensayo de ejemplo (`../00-original.txt`), procesado de tres
formas. Medido a mano el 30-sep-2026, un escaneo por texto.

| Archivo | Qué es | Grammarly | CleverHumanizer |
|---|---|---|---|
| `original.txt` | sin tocar | 100% IA | — |
| `ruleta.txt` | `scripts/ruleta.py` sobre el original | 100% IA | 76% humano |
| **`cubo.txt`** | **`scripts/cubo.py` sobre el original** | **0% IA** | **99% humano** |
| `cubo-ruleta.txt` | `cubo.txt` pasado además por la ruleta | 0% IA | 92% humano |

Lectura:

- **El cubo solo basta.** Reescribe la estructura de cada oración, que es lo que mira
  Grammarly, y con eso también convenció a CleverHumanizer.
- **La ruleta sola no basta para Grammarly.** Cambiar palabras sueltas movió a
  CleverHumanizer pero no a Grammarly.
- **La ruleta después del cubo no aporta** (99% → 92% humano es ruido, si acaso peor).

`cubo.txt` se hizo con la versión de `cubo.py` de esa tarde: un solo generador
(`deepseek-v4.1-flash`), detector sustituto Qwen2.5-0.5B en CPU y 3 rondas, todavía sin
el revisor de sentido ni el criterio de ritmo. Releído contra el original: conserva todo
el contenido; el orden invertido («A la interrogación… se la denomina metafísica») lo
vuelve un poco acartonado, y «se la denomina» dice algo menos que «constituye».

Es **un párrafo**. El ensayo completo, girado de una vez, se quedó en 39% en Grammarly
(ver `../../references/evidencia.md` §4c y §4d).
