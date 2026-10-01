# Control de calidad antes de entregar

Referencia de `SKILL.md`. Pasa esta lista completa antes de dar un texto por terminado.

---

## Filtro 1 — Contenido (bloqueante)

Nada sale si esto falla.

- [ ] Corrí `verificar_fidelidad.py original.txt reescrito.txt --conceptos conceptos.txt`
      y sale **100%** (código de salida 0)
- [ ] El archivo de conceptos es de **este** texto: lo revisé, no me quedé con la
      extracción automática sin mirarla
- [ ] Revisé una por una las negaciones que el script reporta como desaparecidas
- [ ] Releí el texto completo contra el original: títulos, subtítulos y matices no
      los verifica ningún script
- [ ] Verifiqué manualmente nombres propios y obras citadas
- [ ] Verifiqué términos en otro idioma (ousía, Dasein, res cogitans...)
- [ ] Verifiqué cifras, fechas y unidades
- [ ] **No se invirtió ningún sentido.** Revisar específicamente negaciones:
      «no contradicción» ≠ «contradicción»; «no siempre» ≠ «nunca»;
      «no concluyente» ≠ «concluyente»
- [ ] El orden del argumento se mantiene
- [ ] No inventé datos, ejemplos ni fuentes que no estaban

**Señal de alarma:** la cadena de traducción del benchmark perdió exactamente esto —
invirtió «principio de no contradicción». Un error así pasa todos los correctores
ortográficos y cambia el significado. Por eso este filtro va primero y es bloqueante.

---

## Filtro 2 — Registro (bloqueante)

Un texto humanizado que cambió de registro no sirve, aunque el detector diga que está
limpio.

- [ ] Identifiqué el registro de destino antes de reescribir (académico, marketing,
      técnico, email)
- [ ] El resultado sigue en ese registro
- [ ] En académico: **no** metí coloquialismos tipo «mira», «vamos», «un rollo»
- [ ] En técnico: **no** sacrifiqué precisión por ritmo
- [ ] En marketing: puedo permitirme todas las palancas
- [ ] La terminología técnica se mantiene consistente (no llamé a lo mismo de tres
      formas distintas)
- [ ] El tono de marca, si es contenido de un cliente, se respeta (su guía de estilo
      manda sobre estas palancas)

---

## Filtro 3 — Barrido de delatores

`python3 scripts/estilo.py texto.txt` encuentra la mayoría de estos automáticamente.
Repásalos igual: la lista del script no es exhaustiva.

**Muletillas y perífrasis:**
- [ ] `constituye` / `se erige como` / `representa un`
- [ ] `cabe destacar` / `cabe señalar` / `es importante señalar`
- [ ] `en la actualidad` / `hoy en día` / `en el mundo actual`
- [ ] `en última instancia` / `en definitiva` / `a fin de cuentas`
- [ ] `resulta indispensable` / `resulta fascinante` / `resulta evidente`
- [ ] `de manera implícita` / `de forma significativa`
- [ ] `desempeña un papel` / `juega un papel`

**Empalmes:**
- [ ] `no solo ... sino`
- [ ] `no es X, es Y`
- [ ] `lejos de reducirse a`
- [ ] `más que X, Y` abriendo párrafo

**Estructura:**
- [ ] No hay tres oraciones seguidas de longitud parecida
- [ ] Hay al menos un fragmento sin verbo conjugado
- [ ] Hay al menos un guion largo
- [ ] Al menos un párrafo es más corto que los demás
- [ ] El texto no cierra con un remate grandilocuente

**Puntuación:**
- [ ] No todas las comas están en la misma posición relativa
- [ ] No uso el mismo signo para introducir todas las listas

---

## Filtro 4 — Mediciones

- [ ] Medí el original y el resultado con **el mismo** instrumento
- [ ] Medí al menos un **control humano** de registro comparable
- [ ] **El control humano salió marcado como humano.** Si sale marcado como IA, la
      corrida se descarta entera: el detector dejó de medir y el número no significa
      nada
- [ ] El resultado leído corresponde al texto enviado (no a una página de resultados
      vieja)
- [ ] Reporto **qué** detector dijo qué (nunca un veredicto único agregado)
- [ ] Si un detector no se pudo usar, lo digo explícitamente
- [ ] Registro si hubo límite de uso gratuito, bloqueo o veredicto no reproducible

---

## Filtro 5 — Entrega

Lo que se reporta al usuario, siempre:

- [ ] El archivo reescrito (nunca sobrescribiendo el original)
- [ ] El original intacto
- [ ] Nivel de confianza de cada medición
- [ ] Tabla antes/después **con nombre de detector**
- [ ] El resultado del control humano, para contexto
- [ ] Qué método se aplicó, en una línea

Lo que **no** se promete nunca:

- [ ] ~~«Ya no lo detecta»~~ → decir «bajó de X a Y en tal detector»
- [ ] ~~«Pasa todos los detectores»~~ → es falso por construcción
- [ ] ~~«Es indetectable»~~ → no existe
- [ ] ~~«100% humano»~~ → ningún método lo garantiza

---

## Condiciones de parada

Detente y consulta al usuario si:

1. **El destino es una entrega académica evaluada.** El riesgo deja de ser técnico y
   pasa a ser institucional. Informarlo antes de continuar.
2. **El control humano también sale marcado como IA.** Significa que el detector tiene
   sesgo de registro; optimizar contra él es perseguir un blanco roto. Reportarlo.
3. **El texto contiene afirmaciones de hecho que podrían ser erróneas.** Humanizar no
   es verificar. No arreglo de fondo lo que es un problema de contenido.
4. **La fidelidad no llega al 100% y no encuentro el error.** Entregar el original sin
   tocar es mejor que entregar contenido corrupto.
5. **Es contenido firmado por una marca y el usuario pide introducir erratas.** No
   hacerlo.

---

## Señales de que te pasaste

Humanizar de más también se nota. Si el texto:

- tiene fragmentos en cada párrafo
- tiene más de dos párrafos de una sola línea
- tiene una variación de oración (CV en `estilo.py`) muy por encima de un texto
  humano del mismo registro
- suena a alguien imitando un estilo literario más que a prosa natural

...entonces hay sobre-optimización. La variante adversarial del benchmark llegó a un
CV de 0.68 con el humano comparable en 0.51, y bajó en el detector lo mismo que la
variante moderada (6.7% frente a 7.7%). Más agresivo no es mejor: es otra forma de
sonar raro.
