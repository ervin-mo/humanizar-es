# Examples

Two essays generated with AI, each taken through the full recipe, with every hand fix
listed:

- [`en/`](en/): remote work, in English.
- [`es/`](es/): metaphysics, in Spanish.

Each folder has `original.txt` → `1-rewritten.txt` (the model's rewrite, fixed by hand) →
`2-final.txt` (after `join.py`), plus its `concepts.txt`.

`2-final.txt` uses the full join (every sentence of a paragraph in one). To see the
recommended version, with two or three periods per paragraph:

```bash
python3 scripts/join.py examples/es/1-rewritten.txt -o /tmp/final.txt --concepts examples/es/concepts.txt --pauses 2
```
