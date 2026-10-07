# Example (Spanish): an essay on metaphysics

| File | What it is |
|---|---|
| `original.txt` | ~725-word essay generated with AI |
| `concepts.txt` | The 27 concepts that must not be lost |
| `1-rewritten.txt` | The `rewrite.py` output, already fixed by hand |
| `2-final.txt` | `1-rewritten.txt` after `join.py`: the result |

Reproduce the last step (no model needed):

```bash
python3 scripts/join.py examples/es/1-rewritten.txt -o /tmp/final.txt --concepts examples/es/concepts.txt
diff /tmp/final.txt examples/es/2-final.txt     # identical
```

## What was fixed by hand in `1-rewritten.txt`

13 fixes, each one the minimal word or phrase:

| The model wrote | Fixed to | Why |
|---|---|---|
| Renunciar a la metafísica significa **renunciar al** pragmatismo ciego | **resignarse al** | inverted the idea |
| **Hacia el siglo X**, las tradiciones escolásticas | **Siglos más tarde** | false date (Aquinas is 13th century) |
| la línea de horizonte: **la esencia**, los principios | **el ser en cuanto ser** | changed the concept |
| no puede entender **la meta que lo guia** | **su propio marco de sentido** | changed the idea |
| **Contra** la física | **A diferencia de** | wrong sense of contrast |
| para **hacerle una ley de** la totalidad | **legislar sobre** | meaningless phrase |
| **al impulsado** por la necesidad | **impulsada** | agreement |
| como fenómenos **(el fenómeno)** | (removed) | redundant |
| **Aunque** esta tendencia **al** clausurar | **Pero** … **a** | grammar |
| **fenomenologismo** | **la fenomenología** | wrong term |
| **no solo la metafísica no ha muerto** | **la metafísica no solo no ha muerto** | word order |
| **la avance** explosivo | **el avance** | gender |
| metafisica, expresion, mas, preocupacion, filosofica | with accent | lost accents |


`join.py` also warned that «René» had been lowercased: «René Descartes» was added to
`concepts.txt` and the text was joined again.
