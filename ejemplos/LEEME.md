# Ejemplo: un ensayo de metafísica

| Archivo | Qué es |
|---|---|
| `original.txt` | Ensayo de ~725 palabras generado con IA |
| `conceptos.txt` | Los 27 conceptos que no se pueden perder |
| `1-hip.txt` | La reescritura de `hip.py`, ya corregida a mano |
| `2-final.txt` | `1-hip.txt` pasado por `unir.py`: el resultado |

Reproducir el último paso (sin modelo):

```bash
python3 scripts/unir.py ejemplos/1-hip.txt -o /tmp/final.txt --conceptos ejemplos/conceptos.txt
diff /tmp/final.txt ejemplos/2-final.txt     # idénticos
```

## Lo que se corrigió a mano en `1-hip.txt`

13 correcciones, todas de la palabra o la frase mínima:

| El modelo puso | Se corrigió a | Por qué |
|---|---|---|
| Renunciar a la metafísica significa **renunciar al** pragmatismo ciego | **resignarse al** | invertía la idea |
| **Hacia el siglo X**, las tradiciones escolásticas | **Siglos más tarde** | fecha falsa (Tomás de Aquino es del XIII) |
| la línea de horizonte: **la esencia**, los principios | **el ser en cuanto ser** | cambiaba el concepto |
| no puede entender **la meta que lo guia** | **su propio marco de sentido** | cambiaba la idea |
| **Contra** la física | **A diferencia de** | sentido de oposición equivocado |
| para **hacerle una ley de** la totalidad | **legislar sobre** | frase sin sentido |
| **al impulsado** por la necesidad | **impulsada** | concordancia |
| como fenómenos **(el fenómeno)** | (se quitó) | redundante |
| **Aunque** esta tendencia **al** clausurar | **Pero** … **a** | gramática |
| **fenomenologismo** | **la fenomenología** | término equivocado |
| **no solo la metafísica no ha muerto** | **la metafísica no solo no ha muerto** | orden |
| **la avance** explosivo | **el avance** | género |
| metafisica, expresion, mas, preocupacion, filosofica | con acento | acentos perdidos |

Además, `unir.py` avisó que «René» había bajado a minúscula: se agregó «René Descartes» a
`conceptos.txt` y se volvió a unir.
