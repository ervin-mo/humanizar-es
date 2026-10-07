# Evidence

Every measurement of the recipe (`rewrite.py` → hand fixes → `join.py`), taken by hand in
[Grammarly's AI detector](https://www.grammarly.com/ai-detector) in October 2026, one scan
per version, with the box cleared before pasting. The Spanish test essays belong to a user
and are not published; their numbers are. The English examples are in `examples/en/`.

## 1. The full recipe

| Essay | Original rewritten by `rewrite.py` | `rewrite.py` + fixes + **`join.py`** |
|---|---|---|
| 🇪🇸 Aristotle: act and potency, 1,990 words, 11 paragraphs | 45% (the original, first half) | **0% and 0%** (two halves, `--pauses 2`) |
| 🇪🇸 Tourism and AI in Chiapas, 1,150 words, 9 paragraphs | 77% | **0%** |
| 🇪🇸 Dragon Ball and its generation, 910 words, 7 paragraphs | 84% | **10%** |
| 🇪🇸 An AI classification model, 690 words, 5 paragraphs | not measured | **0%** |

Hand fixes: 21 in Chiapas and 16 in Dragon Ball. Concepts kept: 37 of 38 in Chiapas
("itinerarios" became "rutas") and 24 of 24 in Dragon Ball.

The third Spanish essay was the first run of the published skill (v2.0.0), done by an
agent following `SKILL.md` step by step: 9 hand fixes (one restored a negation the model
had inverted), 18 of 18 concepts, about 4 minutes on CPU.

The fourth essay (October 7) ran the 3.0.0 pipeline: copy guard, `--only` regeneration
of five paragraphs, 7 + 3 hand fixes of one to three words, `--pauses 2` and 12 logical
connectors; 24 of 24 concepts. Grammarly reads about 1,400 words, so it was measured in
halves (1,081 and 937 words, with headings).

## 2. What Grammarly punishes: one change at a time

Base: the `rewrite.py` output of the Dragon Ball essay, **without fixes**. Each version
applies a single change.

| Version (same base) | Grammarly |
|---|---|
| Base, unchanged | 84% |
| Random double spaces | 84% |
| Remove ~35% of commas | 60% |
| Splice ~50% of sentences with commas | 54% |
| Join ~60% of sentences with "y" | 40% |
| **Join every sentence of each paragraph with "y"** | **8%** |
| Same, in 4 paragraphs instead of 7 | 8% |
| The original **without** `rewrite.py`, join ~60% | 66% |
| The original **without** `rewrite.py`, join all | 57% |

What it shows:

1. **Grammarly looks at sentence rhythm**, not typography: double spaces moved nothing,
   and the more sentences are joined, the lower the score.
2. **Joining sentences beats any punctuation error**, and adds none.
3. **Both steps are needed.** Joining without rewriting first stopped at 57%; rewriting
   without joining, at 84%.
4. **The number of paragraphs doesn't matter** (8% with 7 and with 4).

## 2b. Hand fixes and pauses: one change at a time (fourth essay)

Same essay, same base-model rewrite; second half unless noted.

| Version | First half | Second half |
|---|---|---|
| All joined; 23 hand fixes, three of them sentence-sized (one pasted back from the original) | 0% | 3% |
| The sentence-sized fixes regenerated with `--only`; bibliography removed | not measured | 3% |
| The two paragraphs still carrying 4–5-word fixes regenerated too | not measured | **0%** |
| `--pauses 2` + 12 connectors, a block could be a single sentence | 6% | **0%** |
| `--pauses 2` + 12 connectors, every block two or more sentences | **0%** | **0%** (same text) |

What it shows:

1. **Hand fixes of four or more words are measurable.** The 3% survived removing the
   bibliography and went away only when the paragraphs with bigger fixes were regenerated.
2. **Pauses are compatible with the rhythm step**, as long as no sentence is left alone.
   The 6% came from near-copies of the original standing between two periods; the same
   sentences inside longer blocks scored 0%.
3. **Logical connectors** («sin embargo», «por eso», «es decir»…), one or two words per
   swap, did not raise the score.

## 2c. ZeroGPT: what it measures, and how selection got it to 0% (fourth essay)

ZeroGPT was measured through the same service its web page uses, which returns the score
and the list of flagged sentences. **It is deterministic**: the same text gave the same
score every time (100% and 100%, 52.4% and 52.4%). Controls in every session: Unamuno's
prologue (1,685 words) and the author's chat messages, both 0%.

**One change at a time, same essay:**

| Version | ZeroGPT |
|---|---|
| The AI original (whole) | 34.3% |
| Rewritten by the base model, sentences unjoined | 33.9% |
| … every sentence of each paragraph joined | 44.0% |
| … `--pauses 2` (the version at 0% in Grammarly) | 52.4% |
| … the same, with headings, as handed in | 45.3% |
| Unamuno, joined with `join.py` (full and with pauses) | 0% and 0% |

What it shows:

1. **ZeroGPT scores sentence by sentence and weighs by words** (`aiWords / textWords`).
   Joining does not make human text look like AI, but a long sentence that contains one
   textbook clause is flagged whole, so joining amplifies what is left of the original.
2. **The base-model rewrite alone does not move ZeroGPT** (34.3% → 33.9%). It flags
   fluent, definitional sentences («La potencia activa es la facultad de…»).
3. **The same paragraph sampled several times gives very different scores.** Paragraph
   «potencia activa y pasiva», 8 samples, unjoined: 29% to 96%; joined: 100% in all.
   «Conclusión», 8 samples, joined: 0% in three, 58–100% in the rest.
4. **The stock opening comes from our own prompt.** `rewrite.py` starts each paragraph with
   the original's first two words. With «Aristóteles distingue…», 22 candidates of that
   paragraph scored 100% joined; starting with «La potencia» instead, the chosen candidate
   scored 0% with three different pause layouts. The introduction, starting with «Uno de»,
   was flagged in context with every candidate; with «Desde la», 0%.
5. **Context changes the score.** A paragraph at 0% alone was flagged inside the document,
   and the other way round; adding the bibliography moved one version from 0% to 10.2%. So
   candidates were measured inside the whole document, with and without bibliography.
6. **It is brittle.** Replacing «actus» with «acto» four times took a paragraph from 0% to
   43%; a three-word grammar fix, from 0% to 62%. Every fix was measured again; when one
   broke a paragraph, another candidate or a smaller fix was used.
7. **Selection needs a person.** One candidate passed but dropped a whole sentence about
   the contradiction between Parmenides and Heraclitus; another changed the quotation of
   Aristotle and added «(De Anima, libro i, cap. vi)», a reference that does not exist.
   Both were discarded; `rewrite.py` now rejects changed quotes and invented references.

**Result:** 7 of 11 paragraphs replaced by selected candidates (two with another opening),
24 of 24 concepts, both quotations of Aristotle verbatim. Measured by the author on the
public sites: **ZeroGPT 0%** (whole text), **Grammarly 0% and 0%** (halves), **GPTZero 0% AI ·
2% mixed · 98% human** (whole text, and the second half alone). 92 candidates were
generated and more than 200 versions scored to get there.

## 3. Why a base model

Xu et al. (2026), *Base Models Look Human To AI Detectors*
([arXiv:2605.19516](https://arxiv.org/abs/2605.19516)): on GPTZero and Pangram, text from
Llama3-8B **base** scored 96.7% and 98.8% human; text from its chat version, 30.3% and
17.1%. Detectors mostly recognize the fingerprint of chat training. Their method, HIP,
fine-tunes a base model to paraphrase; this repo uses their adapter for Qwen3-4B-Base.

Our measurements point the same way: rewriting with chat models never went below 64%, and
every fix made by a chat model raised the score.

| Fixes | Grammarly |
|---|---|
| Dragon Ball, `rewrite.py` + join, no fixes | 8% |
| Same with 16 fixes before joining | 10% |
| Two passes of `rewrite.py` + 19 fixes, no joining | 91% |

That's why the recipe fixes only the culprit word, by hand, and before joining.

## 4. What was tried and didn't work

So nobody repeats it. All with full essays, in Grammarly:

| Attempt | Grammarly |
|---|---|
| Rewrite with a chat model following style rules | 75% |
| Full rewrite with a chat model, without typical AI phrases | 100% |
| Rewrite sentence by sentence with a chat model, guided by a local detector | 67% |
| Reorganize the essay structure with a chat model | 92% |
| One pass of `rewrite.py`, no joining | 77% and 84% |

Adding typos and dropping accents also lowered the score (4% at best), but it leaves
visible errors, and joining sentences gets there without them.

## 5. Other detectors

Fourth essay, the `--pauses 2` version, before selection (section 2c has the final one).
Every detector was checked in the same session with two controls: human texts (a 1914
prologue by Miguel de Unamuno, and the author's own chat messages, typos included) and the
AI original.

| Detector | Human controls | AI original | **Final** | Valid? |
|---|---|---|---|---|
| **GPTZero** (free account, first 10,000 characters) | — | 37% AI · 32% mixed · 31% human | **0% AI · 1% mixed · 99% human** | yes |
| **ZeroGPT** | 0% and 0% | 44.9% | **49.8%** | yes; 0% after selection (section 2c) |
| QuillBot | 0% | 0% | 0% | no: it does not flag the AI original |
| GPTZero, from a browser after ~6 scans | 100% AI (Unamuno and the author's messages) | 100% | 100% | no: throttled, it flags everything |

The last row is why every session needs controls: without them, a throttled detector
reads as "the new version is worse".

- **CleverHumanizer** disagrees with Grammarly: rank correlation of 0.47 across 16 texts
  measured on both. It gave 5% AI to a joined essay Grammarly scored at 69%, and tends to
  extremes (~5% or ~78%).
- **Grammarly's in-editor detector**, on a free account, shows 20% for any text: it's a
  sample number, not a measurement.

## 6. Limits

- Four essays, all in Spanish. We don't yet know how well it carries over to emails,
  marketing, technical writing or English.
- ZeroGPT passes only with selection (section 2c), which costs model runs and a person's reading.
- One scan per version. Differences of a few points may be noise.
- Detectors change; this is a snapshot of October 2026.
