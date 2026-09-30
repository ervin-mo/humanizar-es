# Catálogo de técnicas

Referencia detallada de `SKILL.md`. Aquí están las palancas con ejemplos largos y el
catálogo de delatores del español generado por IA.

Los ejemplos «antes» salen del texto del benchmark (`ejemplos/00-original.txt`) y los
«después», salvo que se diga otra cosa, de las variantes que bajaron en ZeroGPT
(`01-reglas-estilo.txt`, `03-adversarial.txt`), ambas con los 27 conceptos intactos.

Esas variantes no son perfectas: `scripts/estilo.py` todavía les encuentra delatores
(«Lejos de reducirse», «Resulta indispensable», «En última instancia»). Se dejaron
tal cual porque son los textos que se midieron. Cuando un ejemplo de aquí va más lejos
que la variante medida, se marca como *ilustrativo*.

El orden de las palancas es de uso práctico. El benchmark midió variantes completas,
no el efecto de cada palanca por separado.

---

## Parte A — Las 12 palancas, con ejemplos extendidos

### 1. Varianza de longitud de oración

El original del benchmark tenía 29 palabras por oración de media y una desviación de
10.6. Las variantes que bajaron en el detector acortaron la media (19.9 y 15.1) con
una desviación casi igual (10.5 y 10.3). Lo que subió fue la variación **relativa**
a la media (coeficiente de variación): de 0.36 a 0.53 y 0.68. La cadena de
traducción, que no bajó, se quedó en 0.36. El control humano comparable (Wikipedia
2014) tiene 0.51.

En la práctica: más oraciones cortas entre las largas, no oraciones más largas.

Cómo se hace en la práctica: localiza cualquier tramo donde haya tres o más oraciones
seguidas de longitud parecida y rómpelo. Mete una corta. Alarga la siguiente
subordinando lo que antes era una oración aparte.

> **Antes:**
> Su objeto de estudio no es un sector delimitado del universo, sino el horizonte
> sobre el cual cualquier cosa cobra sentido: el ser en cuanto ser, los principios
> primordiales, la causalidad, el tiempo y la estructura ontológica de cuanto hay.
>
> **Después:**
> Su objeto no es un sector delimitado: es el ser en cuanto ser, los principios
> primordiales, la causalidad, el tiempo, la estructura ontológica de cuanto hay.

### 2. Fragmentos como oraciones

Un sintagma nominal o adjetival con punto final. Rompe el molde sujeto-verbo-predicado
que el modelo repite sin excepción.

Ejemplos reales usados:
- «Andamios que casi nunca miramos. Precisamente porque sostienen.»
- «Solo el refinamiento constante de las preguntas esenciales que nos definen como
  seres conscientes.»
- «Capaz de manipular la naturaleza, incapaz de comprender su propio marco de
  sentido.»
- «Su diagnóstico era duro.»

Regla práctica: uno o dos por cada 500 palabras. Más de eso y el texto se vuelve
telegráfico.

### 3. Guion largo para incisos

Convierte incisos que estaban entre comas o paréntesis. Aporta una voz que comenta.

> **Antes:** A diferencia de la física, orientada a estudiar las entidades sujetas al
> cambio empírico, la filosofía primera debía descifrar aquello que permanece.
>
> **Después:** La física estudiaba las entidades sujetas al cambio empírico. La
> filosofía primera, en cambio, debía descifrar aquello que permanece.

Nótese que además se partió la oración en dos y se movió el conector al medio.

### 4. Preguntas retóricas

El modelo afirma. El humano se pregunta. Funcionan especialmente después de una
afirmación fuerte o para introducir una objeción.

- «¿Abstracciones etéreas? ¿Misticismo desencarnado? No.»
- «¿Cuál es la textura ontológica de la realidad a nivel subatómico?»
- «¿Qué define la identidad de una entidad en un entorno digitalizado?»

### 5. Apartes subjetivos

Un comentario del autor rompe la neutralidad. En registro académico funcionan los
apartes irónicos o de complicidad con el lector.

- «Y conviene decirlo pronto, porque el malentendido es viejo.»
- «que es lo último que se esperaría de una disciplina a la que llevan décadas
  firmando el acta de defunción»
- «Su diagnóstico era duro.»
- «Preguntas viejas, más o menos, con ropa nueva.»

### 6. Tricolon y paralelismo

El modelo construye series de tres elementos con estructura idéntica. Dos formas de
romperlas:

**a) Convertir la serie en prosa separada por guiones:**
> **Antes:** Mientras las ciencias particulares parcelan el cosmos para medir el
> movimiento, describir la materia o clasificar los organismos...
>
> **Después:** Mientras las ciencias particulares parcelan el cosmos —miden el
> movimiento, describen la materia, clasifican organismos—...

**b) Cortar el paralelismo:** deja dos elementos donde había tres, o cambia la forma
de uno.

### 7. Marcadores discursivos españoles

Colocados **dentro** de la oración, nunca como conector de apertura formal.

Inventario útil: *eso sí · la verdad es que · al fin y al cabo · ahora bien · dicho
esto · vamos · en cambio · sin embargo (a media oración) · más o menos · no del todo ·
precisamente · por lo demás*

> **Antes:** Sin embargo, este afán por clausurar la indagación ontológica resultó
> prematuro.
>
> **Después:** El afán por clausurar la indagación ontológica resultó prematuro, sin
> embargo.

### 8. Perífrasis elevadas

El modelo sube el registro para sonar serio. Es la marca más fácil de eliminar y la
que más mejora el texto.

| Perífrasis | Alternativa directa |
|---|---|
| X constituye Y | X es Y |
| X se erige como Y | X es Y |
| X representa un hito | X fue importante |
| resulta indispensable | hace falta |
| cabe destacar / cabe señalar | (borrar) |
| es fundamental señalar que | (borrar) |
| es importante tener en cuenta que | (borrar) |
| en la actualidad | hoy |
| asimismo | y / también |
| no obstante | pero |
| en última instancia | al final |
| de manera implícita | implícitos |
| de forma significativa | mucho |
| con el objetivo de | para |
| la implementación de | implementar |
| la realización de un análisis | analizar |
| el desarrollo vertiginoso de | el avance acelerado de |
| llevó a cabo una investigación | investigó |
| posee la capacidad de | puede |

### 9. Empalmes de IA

Construcciones con altísima precisión de delación en español:

| Empalme | Por qué delata | Cómo arreglarlo |
|---|---|---|
| «No es X, es Y» | estructura especular típica de copy generado | afirma Y directamente |
| «No solo X, sino Y» | calco de *not only... but also*, rarísimo en español natural | «X. Y también Y» o solo Y |
| «Lejos de reducirse a X» | perífrasis de relleno | empieza por el sujeto |
| «Más que X, Y» abriendo párrafo | muletilla de apertura | entra directo |
| «Todo esto nos lleva a pensar que» | cierre prefabricado | corta el cierre |

### 10. Longitud de párrafo

El modelo produce párrafos de extensión similar. Permite párrafos de una oración, y
párrafos largos de seis o siete.

Ejemplo del texto adversarial: «La metafísica.» como párrafo de apertura.

### 11. Perplejidad léxica

Sube la imprevisibilidad del vocabulario sin volverte rebuscado. La prueba: ¿esto lo
diría alguien con vocabulario propio, o es la colocación más probable?

Ilustrativo: ninguna variante medida cambió «desarrollo vertiginoso».

| Colocación previsible | Alternativa con voz |
|---|---|
| desarrollo vertiginoso | avance acelerado |
| aspecto fundamental | punto de fondo |
| plantea interrogantes | abre preguntas |
| de suma importancia | que importa |
| en el ámbito de | en |
| una amplia gama de | varios |

### 12. Sin remate final

El modelo cierra con una frase-resumen que suena profunda. Termina plano, o corta
antes de la conclusión.

> **Antes (cierre del original):** La metafísica permanece, en última instancia, como
> la manifestación más pura de la inquietud filosófica: una búsqueda inagotable que
> no promete respuestas definitivas, sino el refinamiento constante de las preguntas
> esenciales que nos definen como seres conscientes.
>
> **Variante 01 (medida):** En última instancia, la metafísica permanece como la
> manifestación más pura de la inquietud filosófica. Una búsqueda inagotable que no
> promete respuestas definitivas. Solo el refinamiento constante de las preguntas
> esenciales que nos definen como seres conscientes.
>
> **Mejor (ilustrativo):** La metafísica sigue ahí, como la forma más pura de la
> inquietud filosófica. No promete respuestas definitivas. Solo preguntas cada vez
> mejor hechas.

La variante medida partió la oración y cerró con un fragmento, pero conservó el
remate («que nos definen como seres conscientes») y «En última instancia», que es un
delator. La versión ilustrativa quita las dos cosas.

---

## Parte B — Catálogo de delatores en español

Lista de verificación. Pasa el texto buscando cada uno.

### Léxico y muletillas

- `en la actualidad`, `hoy en día`, `en la era digital`
- `cabe destacar`, `cabe mencionar`, `es importante señalar`
- `en última instancia`, `en definitiva`, `a fin de cuentas`
- `sin duda alguna`, `indudablemente`, `ciertamente`
- `un abanico de`, `una amplia gama de`, `un sinfín de`
- `desempeña un papel crucial`, `juega un papel fundamental`
- `resulta fascinante`, `resulta evidente`, `resulta imperativo`
- `en el mundo actual`, `en el contexto actual`
- `no es de extrañar que`
- `es fundamental comprender que`

### Sintaxis

- Todas las oraciones con la misma estructura: sujeto + verbo + complemento largo
- Abundancia de voz pasiva y pasiva refleja (`se lleva a cabo`, `fue realizado por`)
- Subordinadas de relativo encadenadas (`el cual`, `cuya finalidad es`)
- Gerundios de apertura (`Teniendo en cuenta lo anterior, ...`)
- Aposiciones explicativas en todas las frases
- Ausencia total de fragmentos

### Puntuación

- Cero guiones largos
- Dos puntos usados siempre igual, para introducir listas
- Punto y coma ausente
- Comas perfectamente balanceadas

### Estructura

- Introducción + tres puntos + conclusión, siempre
- Cada párrafo abre con una oración-tesis y cierra con un remate
- Todos los párrafos miden lo mismo
- Ningún párrafo de una sola oración
- Cierre que recapitula todo lo dicho

### Contenido

- Ejemplos genéricos en vez de concretos
- Ninguna opinión, ninguna duda, ningún «no estoy seguro»
- Cero digresiones
- Afirmaciones sin fuente presentadas como obvias

---

## Parte C — Ajustar por registro

La humanización no debe romper el registro. Guía rápida:

| Registro | Palancas que aplicar | Palancas a moderar |
|---|---|---|
| Académico / ensayo | 1, 2, 3, 5 (irónico), 6, 8, 9, 10, 12 | 4, 7 (evitar «vamos», «mira») |
| Marketing / redes | todas | ninguna |
| Documentación técnica | 1, 6, 8, 9, 10 | 2, 4, 5, 7 |
| Email profesional | 1, 7, 8, 9, 10 | 2, 3, 12 |

En académico, los apartes subjetivos funcionan mejor como ironía culta que como
coloquialismo. Ejemplo válido: «que es lo último que se esperaría de una disciplina a
la que llevan décadas firmando el acta de defunción». Ejemplo inválido en ese
registro: «mira, la metafísica es un rollo».

---

## Parte D — Cómo verificar que mejoró

Sin instalar nada:

```bash
python3 scripts/estilo.py 00-original.txt 01-reescrito.txt
```

Qué mirar, con los números del benchmark como referencia:

| Señal | Original (IA) | 01 reglas | 03 adversarial | Humano comparable (Wikipedia 2014) |
|---|---|---|---|---|
| Palabras por oración (media) | 29.0 | 19.9 | 15.1 | 28.9 |
| Variación de oración (CV) | 0.36 | 0.53 | 0.68 | 0.51 |
| % oraciones de ≤8 palabras | 0 | 13 | 31 | 4 |
| Delatores de la lista | 9 | 3 | 3 | 1 |

Lectura: la variante 01 quedó prácticamente en la variación del humano comparable;
la 03 se pasó.
Los delatores deben tender a cero.

Con el modelo local instalado (`scripts/detect_local.py`) también puedes ver
perplejidad y burstiness. Úsalas con cuidado: el texto humano comparable tuvo **menos**
perplejidad (10.35) que el ensayo generado (12.33), y una burstiness de 16 frente a 39
de la variante 01. Esas señales miden lo que premian los detectores, no cómo escribe
una persona. Sirven para comparar versiones del mismo texto, no como meta.

Y siempre: fidelidad al 100% con `scripts/verificar_fidelidad.py`.
