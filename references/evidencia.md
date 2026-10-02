# Evidencia

Todas las mediciones de la receta (`hip.py` → corrección a mano → `unir.py`), hechas a mano
en el [detector de IA de Grammarly](https://www.grammarly.com/ai-detector) el 1 de octubre
de 2026, un escaneo por versión, con el cuadro vacío antes de pegar. Los ensayos de
prueba no se publican (son de un usuario); se publican los números.

## 1. La receta completa

| Ensayo | Original + `hip.py` | `hip.py` + correcciones + **`unir.py`** |
|---|---|---|
| Turismo e IA en Chiapas, 1,150 palabras, 9 párrafos | 77% | **0%** |
| Dragon Ball y su generación, 910 palabras, 7 párrafos | 84% | **10%** |
| Un modelo de IA de clasificación, 690 palabras, 5 párrafos | sin medir | **0%** |

Las correcciones a mano fueron 21 en Chiapas y 16 en Dragon Ball. Se conservaron 37 de 38
conceptos en Chiapas («itinerarios» quedó como «rutas») y 24 de 24 en Dragon Ball.

El tercer ensayo fue la primera corrida de la skill v2.0.0 tal como está publicada, hecha
por un agente siguiendo `SKILL.md` paso a paso: 9 correcciones a mano (una de ellas
restituía una negación que `hip.py` había invertido), 18 de 18 conceptos y unos 4 minutos
en CPU.

## 2. Qué castiga Grammarly: un cambio a la vez

Base: la reescritura de `hip.py` del ensayo de Dragon Ball, **sin corregir**. A cada
versión se le aplicó un solo cambio.

| Versión (misma base) | Grammarly |
|---|---|
| Base, sin cambios | 84% |
| Espacios dobles al azar | 84% |
| Quitar ~35% de las comas | 60% |
| Pegar ~50% de las oraciones con coma | 54% |
| Unir ~60% de las oraciones con «y» | 40% |
| **Unir todas las oraciones de cada párrafo con «y»** | **8%** |
| Lo mismo, en 4 párrafos en vez de 7 | 8% |
| El original **sin** `hip.py`, unir ~60% | 66% |
| El original **sin** `hip.py`, unir todas | 57% |

Lo que enseña:

1. **Grammarly mira el ritmo de las oraciones**, no la tipografía: los espacios dobles no
   movieron nada, y cuantas más oraciones se unen, más baja.
2. **Unir con «y» rinde más que cualquier error de puntuación**, y no mete ninguno.
3. **Los dos pasos hacen falta.** Unir sin reescribir antes se quedó en 57%; reescribir sin
   unir, en 84%.
4. **El número de párrafos no importa** (8% con 7 y con 4).

## 3. Por qué un modelo base

Xu et al. (2026), *Base Models Look Human To AI Detectors*
([arXiv:2605.19516](https://arxiv.org/abs/2605.19516)): con GPTZero y Pangram, el texto de
Llama3-8B **base** salió 96.7% y 98.8% humano; el de su versión de chat, 30.3% y 17.1%. Los
detectores reconocen sobre todo la huella del entrenamiento de chat. Su método, HIP, ajusta
un modelo base para parafrasear; aquí se usa su adaptador para Qwen3-4B-Base.

Nuestras mediciones van en la misma dirección: reescribir con modelos de chat no bajó de
64% en ningún intento, y cada corrección hecha por un modelo de chat subió el número.

| Corrección | Grammarly |
|---|---|
| Dragon Ball, `hip.py` + unir, sin corregir | 8% |
| La misma con 16 correcciones antes de unir | 10% |
| Dos pasadas de `hip.py` + 19 correcciones, sin unir | 91% |

Por eso la receta corrige solo la palabra culpable, a mano, y antes de unir.

## 4. Lo que se probó y no funcionó

Para que nadie lo repita. Todo con ensayos completos, en Grammarly:

| Intento | Grammarly |
|---|---|
| Reescribir con un modelo de chat siguiendo reglas de estilo | 75% |
| Reescritura completa con un modelo de chat, sin frases típicas de IA | 100% |
| Reescribir oración por oración con un modelo de chat, guiado por un detector local | 67% |
| Reorganizar la estructura del ensayo con un modelo de chat | 92% |
| Una pasada de `hip.py`, sin unir | 77% y 84% |

Meter erratas y quitar acentos también bajaba el número (4% en el mejor caso), pero deja
errores visibles y unir oraciones lo consigue sin ellos.

## 5. Otros detectores

GPTZero y ZeroGPT están en pruebas para una próxima versión; sus mediciones se publicarán
cuando la receta esté ajustada para ellos.

- **CleverHumanizer** no coincide con Grammarly: correlación de rangos de 0.47 en 16 textos
  medidos en los dos. Al Dragon Ball con oraciones unidas le dio 5% de IA cuando Grammarly
  le dio 69%. Tiende a los extremos (o ~5% o ~78%).
- **El detector del editor de Grammarly**, con cuenta gratuita, muestra 20% a cualquier
  texto: es un número de muestra, no una medición.

## 6. Límites

- Tres ensayos de divulgación. No sabemos cuánto se generaliza a correos, marketing o textos
  técnicos.
- Un escaneo por versión. Diferencias de pocos puntos pueden ser ruido.
- Los detectores cambian; esto es una foto de octubre de 2026.
