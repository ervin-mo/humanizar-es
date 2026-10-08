---
name: humanizar-es
description: Rewrites AI-generated text (Spanish or English) so AI detectors read it as human - 0% in Grammarly, 0% in ZeroGPT and 0% AI / 98% human in GPTZero on the same test essay - without changing what it says and without adding typos. Runs locally with no API or cost, in four measured stages - a base model without chat training rewrites (rewrite.py), fidelity is guarded (concepts, quotes, invented references, copying; check.py), the rhythm is rebuilt in blocks of uneven length (join.py --pauses 2), and paragraphs a detector still flags are regenerated as candidates and selected (rewrite.py --candidates, --lead, --take). Use when asked to "humanize" text, "make it not detectable as AI", "pass Grammarly", "remove AI tells", "make it not sound like ChatGPT", or in Spanish "humaniza este texto", "que no lo detecte el detector de IA", "que no suene a ChatGPT".
metadata:
  version: "3.1.1"
  languages: en, es
  evidence: references/evidence.md
---

# Humanize AI text, locally

You receive a text written with AI and give it back **saying exactly the same thing**, but
without AI detectors (Grammarly, GPTZero, ZeroGPT) recognizing it as AI. You are not a
paraphraser or a copy editor: the scripts do the writing, and your job is to prepare them,
review, measure and select.
Talk to the user in their language.

## Why it works (read this so you don't sabotage it)

1. **Detectors recognize the fingerprint of chat training.** Everything a chat model
   writes carries it, **including you**. So never rewrite the text yourself or "improve"
   sentences: every sentence you write puts the fingerprint back. `rewrite.py` does the
   rewriting with a **base** model (no chat training).
2. **Grammarly recognizes rhythm**: sentences of even length, each with its own period.
   `join.py` rebuilds it in blocks of uneven length, the way people write.
3. **Both steps are needed.** Measured: `rewrite.py` alone 84%; joining alone 57%; both 8%.
4. **Copied stretches of the original are AI text.** Never paste a sentence of the
   original back, and never fix more than three words by hand: regenerate instead
   (`--only`). Measured: 3% with bigger hand fixes, 0% after regenerating.
5. **ZeroGPT scores sentence by sentence and weighs by words.** One textbook clause inside
   a long joined sentence flags the whole sentence, so rhythm alone can make ZeroGPT worse
   (34% → 52% on a test essay). What fixes it is **selection**: the base model gives a
   different version each run, so regenerate the flagged paragraphs as candidates and keep
   the one that passes, measured in the whole document (step 9). That essay ended at 0% in
   ZeroGPT, Grammarly and GPTZero at once.
6. **Stock openings come from the original.** The model starts each paragraph with the
   original's first two words; if they are «Uno de los problemas…» or «Aristóteles
   distingue…», it rebuilds the stock sentence. `--lead "Desde la"` gives it another start.

In the commands, `<skill>` is the folder containing this `SKILL.md`. Texts go in the
user's working folder, not inside the skill. **On Windows** type `python` (or `py`) where
it says `python3`; everything else is the same. No key or account is needed.

## Workflow

### 1. Save the original untouched

If the text came through chat, write it to `00-original.txt`, with paragraphs separated by
a blank line. Never overwrite the original.

### 2. Ask what it's for

If it's graded academic work, or work where AI use must be disclosed, say so before going
on (see *Responsible use*).

### 3. Check the installation (once)

Run `python3 <skill>/scripts/install_model.py`: if everything is there it verifies it and
ends with "Ready"; if something is missing, it says so.

1. **llama.cpp**: if missing, macOS and Linux `brew install llama.cpp`; Windows
   `winget install llama.cpp`. On Windows `rewrite.py` also looks in winget's folder, so no
   new terminal is needed; if it lives elsewhere, `HUMANIZE_LLAMA` holds the path to the
   `.exe`.
2. **The model** (`Qwen3-4B-Base.Q8_0.gguf` and `hip-qwen3-4b-base.gguf`): if missing,
   **ask permission** (~4.6 GB) and let `install_model.py` download it. It needs network
   access; if your environment blocks it, ask for approval or have the user run it in a
   terminal. If the download is cut, run it again: it resumes.

Python 3.9+ is enough: the scripts need no packages.

### 4. List what must not be lost

Build `concepts.txt` with the user: **full** proper names, titles, terms, figures, dates
and the negations an idea rests on. One per line, variants with `|`, `*` for prefixes:

```text
Microsoft Teams | Teams
two or three days | 2 or 3 days
commut*
```

To start: `python3 <skill>/scripts/check.py 00-original.txt --list`

### 5. Rewrite with the local model

Tell the user: about 30 seconds per paragraph on an M4 Mac, 1 to 3 minutes on an older PC;
CPU only, free. If your environment cuts long commands, run it in the background and read
its output: `rewrite.py` saves the file after every paragraph and prints its progress.

```bash
python3 <skill>/scripts/rewrite.py 00-original.txt -o 01-rewritten.txt --concepts concepts.txt
```

At the end it reports which paragraphs it left as the original and the concept they kept
losing (check its spelling in `concepts.txt`), and which ones copied long stretches of the
original in every try. Rerun only those paragraphs, with more `--tries`.

### 6. Review and fix, BEFORE joining (blocking)

```bash
python3 <skill>/scripts/check.py 00-original.txt 01-rewritten.txt --concepts concepts.txt
```

Then **compare every paragraph of `01-rewritten.txt` with the original** and list what
really changed. Typical slips:

- a changed detail ("many" → "the majority"; "physical office" → "fixed schedule");
- an inverted or overstated idea ("were forced to work from home" where it said "split
  their time"; «renunciar al pragmatismo» for «resignarse al pragmatismo»);
- wrong gender, number or date («siglo X»);
- a lost `%` written in words ("sixty percent" → "60"), a typo or a dropped accent;
- a sentence that doesn't make sense.

Show the list to the user and fix **only the minimal culprit word or phrase**, with exact
replacements in `01-rewritten.txt`. Don't rewrite whole sentences or polish style: every
word you add raises the detector score (in testing, 16 fixes moved an essay from 8% to
10%). If it's just different but says the same thing, leave it.

**A fix is one to three words.** If a paragraph needs more — a garbled or inverted
sentence, an invented quote, a lost sentence — **don't write it and don't paste the
original's sentence back** (that is AI text again): redo that paragraph from the original
with the model and review it again:

```bash
python3 <skill>/scripts/rewrite.py 00-original.txt -o 01-rewritten.txt --concepts concepts.txt --only 6,11
```

`--only` keeps the other paragraphs and their fixes. Measured on a 1,990-word essay in
Grammarly: its last half scored 3% twice while it carried hand fixes of four or more words
(a few of them the original's own words put back); after redoing those paragraphs with
`--only` and fixing only 1-2 words, 0%. The bibliography was not the cause.

### 7. Rebuild the rhythm

```bash
python3 <skill>/scripts/join.py 01-rewritten.txt -o 02-final.txt --concepts concepts.txt --pauses 2
```

It detects English or Spanish (force it with `--lang en|es`). If it warns about words it
lowercased, check which are proper names; add them to `concepts.txt` and run it again.
`--pauses 2` leaves two or three periods per paragraph, in blocks of
uneven length, cutting first where a sentence already opens with «Sin embargo», «Por
ejemplo», «Segundo»… and joining the rest with «y» or «;». Then you may swap the «y» or «;»
of a join for a logical connector («sin embargo», «por eso», «así», «es decir», «en
cambio») **only where the relation is plain**, one or two words per swap. Measured on a
1,990-word essay: **0% and 0% in Grammarly** with 12 such swaps. Every block keeps at least
two sentences: when a near-copy of the original was left alone between two periods, that
half went up to 6%. Without `--pauses`, every sentence of a paragraph is joined into one
(also measured at 0%, but it reads badly); use it only if the user asks for it.

**Don't touch `02-final.txt` afterwards** except for those connector swaps: any fix goes into `01-rewritten.txt` and you
join again.

### 8. Verify and deliver

```bash
python3 <skill>/scripts/check.py 00-original.txt 02-final.txt --concepts concepts.txt
```

Deliver `02-final.txt`, the fidelity table and the list of fixes, **in the format the
user will hand in** (headings, bibliography): the context changes ZeroGPT's score. Warn
that sentences stay longer than in a polished essay. If the text is over ~1,400 words, tell
the user to measure it in Grammarly in two halves; GPTZero's free scan reads 10,000
characters. Ask them to measure in their detector **together with a text of their own
written without AI**, and to tell you what is still flagged.

### 9. Select, for what a detector still flags

ZeroGPT and Grammarly highlight the sentences they flag. For each flagged paragraph:

```bash
python3 <skill>/scripts/rewrite.py 00-original.txt -o 01-rewritten.txt --concepts concepts.txt \
        --only 4 --candidates 6 --temperature 1.1
```

If the paragraph starts with a stock opening, add `--lead` with two other words that fit
the paragraph («Desde la», «La potencia», «Para Aristóteles»). Candidates land in
`01-rewritten.txt.candidates/`; tries that lose a concept, change a quote, invent a
reference or copy the original are already discarded.

1. **Read each candidate against the original** and drop any that loses an idea, even if
   no concept is missing (one dropped a whole sentence about the contradiction between two
   authors).
2. **Have the user measure the survivors joined, inside the whole text**, not alone: a
   paragraph that scores 0% alone can be flagged in context, and the other way round.
3. Adopt the one that passes and join again:

```bash
python3 <skill>/scripts/rewrite.py 00-original.txt -o 01-rewritten.txt --take 4=01-rewritten.txt.candidates/p04-2.txt
python3 <skill>/scripts/join.py 01-rewritten.txt -o 02-final.txt --concepts concepts.txt --pauses 2
```

4. **Any fix to an adopted paragraph gets measured again.** ZeroGPT is deterministic but
   brittle: a one-word fix took a paragraph from 0% to 62%. If a fix breaks it, try the
   next candidate instead of forcing the fix.

## Don't

- **Rewrite it yourself, "humanize" it in your own words, or ask another chat model.**
  That adds the fingerprint this recipe removes.
- **Add typos, remove commas or add double spaces.** Not needed: double spaces moved
  nothing (84% → 84%), and joining sentences lowered the score more than any error.
- **Feed `rewrite.py` its own output.** A second pass drifts from the meaning (in testing
  it ended at 91%). Candidates are different: each is a fresh first pass from the original.
- **Accept a candidate that changes a quotation or adds a source.** The guard catches the
  usual cases; read for the rest.
- **Use the GPU without asking.** `rewrite.py` runs on CPU on purpose.

## Limits (read before promising anything)

1. **Measured on Grammarly, GPTZero and ZeroGPT**, Spanish essays: Grammarly 0% on three of
   four (10% on an older run); one essay at 0% in all three at once, ZeroGPT only after
   selection (step 9). **English:** ZeroGPT 0% on two essays; **GPTZero in English is not
   passed yet** - its model 4.1o recognizes base-model text (Qwen, Llama and Mistral tested)
   from ~250 words on. If the text is English and the user needs GPTZero, say so **before
   starting**. Never promise a number.
2. **Detectors flag human text too** and change without notice. Hence the human control.
3. **Only English and Spanish** have joining rules. Other languages: the rewrite may work,
   joining won't.

## Responsible use

For text the user or their client signs and answers for: brand content, outreach,
documentation, emails, drafts written with AI help. **Don't use it to pass off graded work
as one's own where AI is banned or must be disclosed.** If that's the destination, flag the
risk before proceeding.

## Files

- `scripts/install_model.py` — downloads and verifies the model (once)
- `scripts/rewrite.py` — steps 5, 6 and 9: rewrite with the local base model, guard
  fidelity, `--only`, `--candidates`, `--lead`, `--take`
- `scripts/join.py` — step 7: rebuild the rhythm of each paragraph
- `scripts/check.py` — concepts and negations, original against version
- `references/evidence.md` — every measurement
- `references/detectors.md` — how to measure in Grammarly, GPTZero and ZeroGPT, with controls
- `examples/` — worked examples in English and Spanish
