# Example (English): an essay on remote work

| File | What it is |
|---|---|
| `original.txt` | ~600-word essay generated with AI |
| `concepts.txt` | The 13 concepts that must not be lost |
| `1-rewritten.txt` | The `rewrite.py` output, already fixed by hand |
| `2-final.txt` | `1-rewritten.txt` after `join.py`: the result |

Reproduce the last step (no model needed):

```bash
python3 scripts/join.py examples/en/1-rewritten.txt -o /tmp/final.txt --concepts examples/en/concepts.txt
diff /tmp/final.txt examples/en/2-final.txt     # identical
```

## What was fixed by hand in `1-rewritten.txt`

One fix. The model added a claim the original didn't make:

| The model wrote | Fixed to | Why |
|---|---|---|
| Millions of workers **have been forced to work** from home | Millions of workers **now work** from home | the original said they *split their time*, not that they were forced |

Things left as they were because they say the same thing in other words: "COVID-19
pandemic" for "global pandemic", "wellness" for "well-being", "sleeping" for "rest".

`check.py` kept 13 of 13 concepts. `join.py` turned 24 sentences into 7.
