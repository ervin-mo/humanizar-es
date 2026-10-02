---
name: humanizar-es
description: Reescribe texto en español generado por IA para que el detector de Grammarly deje de marcarlo, sin cambiar lo que dice y sin meter errores de ortografía ni de puntuación. Corre en local, sin API ni costo, con un modelo base (hip.py) y luego une las oraciones de cada párrafo (unir.py); llevó tres ensayos completos a 0%, 10% y 0% en Grammarly. Úsalo cuando pidan "humanizar", "que no lo detecte el detector de IA", "pasar Grammarly", "quitar las marcas de IA" o "que no suene a ChatGPT".
metadata:
  version: "2.1.1"
  idioma: es
  evidencia: references/evidencia.md
---

# Humanizar texto en español

Recibes un texto escrito con IA y lo devuelves **diciendo exactamente lo mismo**, pero sin
que el detector de Grammarly lo reconozca como IA. No eres un parafraseador ni un
corrector de estilo: el trabajo lo hacen dos scripts y tu papel es prepararlos, revisar
y verificar.

## Por qué funciona (léelo para no sabotearlo)

1. **Los detectores reconocen la huella del entrenamiento de chat.** Todo lo que escribe
   un modelo de chat la trae, **incluido tú**. Por eso nunca reescribas tú el texto ni
   «mejores» oraciones: cada oración que redactas le devuelve la huella. El trabajo de
   reescribir lo hace `hip.py`, que usa un modelo **base** (sin entrenamiento de chat).
2. **Grammarly reconoce el ritmo**: oraciones de largo parejo, cada una con su punto.
   `unir.py` las une con «y», y eso lo borra.
3. **Hacen falta los dos pasos.** Medido: solo `hip.py`, 84%; solo unir, 57%; los dos, 8%.

En los comandos, `<skill>` es la carpeta donde está este `SKILL.md`. Los textos van en la
carpeta de trabajo del usuario, no dentro de la skill. **En Windows** escribe `python` (o
`py`) donde dice `python3`; todo lo demás es igual. No hace falta ninguna clave ni cuenta.

## Flujo de trabajo

### 1. Guardar el original sin tocarlo

Si el texto llegó por chat, escríbelo a `00-original.txt`, en párrafos separados por una
línea en blanco. Nunca sobrescribas el original.

### 2. Preguntar el uso

Si es una entrega académica evaluada o un trabajo donde se exige declarar el uso de IA,
dilo antes de seguir (ver *Uso responsable*).

### 3. Comprobar la instalación (una vez)

Corre `python3 <skill>/scripts/instalar_hip.py`: si todo está, lo verifica y termina con
«Listo»; si falta algo, lo dice.

1. **llama.cpp**: si falta, macOS y Linux `brew install llama.cpp`; Windows
   `winget install llama.cpp`. En Windows, `hip.py` también lo busca en la carpeta de winget,
   así que no hace falta abrir otra terminal; si está en otro lado, la variable
   `HUMANIZAR_LLAMA` lleva la ruta al `.exe`.
2. **El modelo** (`Qwen3-4B-Base.Q8_0.gguf` y `hip-qwen3-4b-base.gguf` en
   `~/.cache/humanizar-es/hip`, o en `HUMANIZAR_HIP_DIR`): si falta, **pide permiso** (son
   ~4.6 GB) y deja que `instalar_hip.py` lo baje. Necesita red; si tu entorno la bloquea,
   pide que lo autoricen o que el usuario lo corra en su terminal. Si se corta, se vuelve
   a correr y sigue donde se quedó.

Python 3.9+ basta: los scripts no necesitan paquetes.

### 4. Anotar lo que no se puede perder

Arma con el usuario `conceptos.txt`: nombres propios **completos**, obras, términos,
cifras, fechas y negaciones que sostienen una idea. Uno por línea, variantes con `|`, `*`
para prefijos:

```text
René Descartes | Descartes
principio de no contradicción
deslave*
```

Para arrancar: `python3 <skill>/scripts/verificar_fidelidad.py 00-original.txt --listar`

### 5. Reescribir con el modelo local

Avisa: unos 30 segundos por párrafo en una Mac M4, de 1 a 3 minutos en una PC más vieja;
en CPU y sin costo. Si tu entorno corta comandos largos, lánzalo en segundo plano y revisa
su salida: `hip.py` guarda el archivo después de cada párrafo e imprime su avance.

```bash
python3 <skill>/scripts/hip.py 00-original.txt -o 01-hip.txt --conceptos conceptos.txt
```

Al final dice qué párrafos dejó como el original porque perdían un concepto.

### 6. Revisar y corregir, ANTES de unir (bloqueante)

```bash
python3 <skill>/scripts/verificar_fidelidad.py 00-original.txt 01-hip.txt --conceptos conceptos.txt
```

Después **compara cada párrafo de `01-hip.txt` con el original** y haz una lista de lo que
cambió de verdad. Lo típico:

- un detalle cambiado («limpian» → «lavan los platos»; «foráneas» → «extranjeras»);
- una idea invertida («renunciar al pragmatismo» por «resignarse al pragmatismo»);
- género, número o fecha equivocados («Para una niña» por «los niños»; «siglo X»);
- una errata o un acento perdido («timido», «metafisica»);
- una frase que no se entiende.

Muéstrale la lista al usuario y corrige **solo la palabra o la frase mínima culpable**,
con reemplazos exactos en `01-hip.txt`. No reescribas oraciones completas ni pulas el
estilo: cada palabra que pones tú suma puntos en el detector (en las pruebas, 16
correcciones subieron un ensayo de 8% a 10%). Lo que sea solo distinto, pero diga lo
mismo, déjalo.

### 7. Unir las oraciones

```bash
python3 <skill>/scripts/unir.py 01-hip.txt -o 02-final.txt --conceptos conceptos.txt
```

Si avisa de palabras que bajó a minúscula, revisa cuáles son nombres propios; agrégalos a
`conceptos.txt` y vuelve a correrlo. **No toques `02-final.txt` después**: cualquier
corrección va en `01-hip.txt` y se vuelve a unir.

### 8. Verificar y entregar

```bash
python3 <skill>/scripts/verificar_fidelidad.py 00-original.txt 02-final.txt --conceptos conceptos.txt
```

Entrega `02-final.txt`, la tabla de fidelidad y la lista de correcciones. Avisa que los
párrafos quedan en oraciones largas encadenadas: es lo que hace pasar el detector.
Recuérdale medir en su detector **junto con un texto suyo escrito sin IA**.

## Lo que no hay que hacer

- **Reescribir tú, «humanizar» con tus palabras o pedírselo a otro modelo de chat.**
  Mete la huella que esta receta quita.
- **Meter erratas, quitar comas o poner espacios dobles.** No hace falta: los espacios
  dobles no movieron nada (84% → 84%), y unir oraciones bajó más que cualquier error.
- **Correr `hip.py` dos veces.** La segunda pasada se aleja del sentido y obliga a más
  correcciones (en las pruebas terminó en 91%).
- **Usar la GPU sin preguntar.** `hip.py` corre en CPU a propósito.

## Límites (léelos antes de prometer nada)

1. **Se midió en Grammarly, con tres ensayos (0%, 10% y 0%).** Está optimizado para
   Grammarly; GPTZero y ZeroGPT todavía no lo pasan de forma confiable. Si el usuario
   necesita otro detector, díselo antes de empezar. No prometas un número.
2. **Los detectores marcan texto humano** y cambian sin avisar. Por eso el control humano.
3. **El modelo se entrenó en inglés.** Funciona en español con un truco (le damos las dos
   primeras palabras de cada párrafo), pero comete los errores del paso 6.

## Uso responsable

Para texto propio o de un cliente que se publica con responsabilidad de quien firma:
marca, divulgación, documentación, correos, borradores escritos con ayuda de IA. **No lo
uses para presentar como propio un trabajo evaluado donde el uso de IA está prohibido o
debe declararse.** Si el destino es una entrega académica, avisa del riesgo antes de
proceder.

## Archivos

- `scripts/instalar_hip.py` — baja y verifica el modelo (una vez)
- `scripts/hip.py` — paso 5: reescribe con el modelo base local
- `scripts/unir.py` — paso 7: une las oraciones de cada párrafo
- `scripts/verificar_fidelidad.py` — conceptos y negaciones, original contra versión
- `references/evidencia.md` — todas las mediciones
- `references/detectores.md` — cómo medir en Grammarly y sus límites
- `ejemplos/` — un ensayo y su paso por la receta
