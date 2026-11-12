---
name: humanizar-es
description: Rewrites AI-generated text (Spanish or English) so AI detectors read it as human - 0% in Grammarly, 0% in ZeroGPT and 0% AI / 98% human in GPTZero on the same test essay - without changing what it says and without adding typos. Runs locally with no API or cost, in four measured stages - a base model without chat training rewrites (rewrite.py), fidelity is guarded (concepts, quotes, invented references, copying; check.py), the rhythm is rebuilt in blocks of uneven length (join.py --pauses 2), and paragraphs a detector still flags are regenerated as candidates and selected (rewrite.py --candidates, --lead, --take). Use when asked to "humanize" text, "make it not detectable as AI", "pass Grammarly", "remove AI tells", "make it not sound like ChatGPT", or in Spanish "humaniza este texto", "que no lo detecte el detector de IA", "que no suene a ChatGPT".
metadata:
  version: "3.2.0"
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

**If it lives in a `.docx`** (an assignment, a client's document), don't copy by hand and don't
retype the header: `docx_tools.py` takes out only the body and puts the result back with the
same formatting, header and bibliography untouched:

```bash
python3 <skill>/scripts/docx_tools.py extract doc.docx -o 00-original.txt --map mapa.json \
        --start "Introducción:" --stop "Bibliografía" --merge-short 25
# ... steps 4 to 8 on 00-original.txt ...
python3 <skill>/scripts/docx_tools.py build doc.docx --map mapa.json --text 02-final.txt -o doc-final.docx
```

`--start`/`--stop` are the first paragraph that begins with that text (a header line like
«Introducción a la Filosofía» also begins with «Introducción»: include the colon or more words).
Headings (up to four words, a line ending in «:», «1. Ubicar», «Acción 2.», «Anexo») stay one block each and are never replaced; **a short bullet of five or more words is rewritten like any paragraph** (a list-heavy test document kept a third of its words as original AI bullets and scored 40% in Grammarly). `--merge-short 25` joins a lone short
sentence with the paragraph after it. Open the `.docx` yourself before delivering it: this
script checks the XML, not how Word draws it.

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

A paragraph with no usable try gets **rescue rounds** (`--rescue`, 2 by default): the temperature
goes up 0.1 each round, so it ends up rewritten instead of staying as the original. If one
**still** ends as the original text, `rewrite.py` **exits with code 3** and prints
`ACTION REQUIRED` with the exact `--only` command: **a paragraph that stays as the original is
AI text, a detector flags it and joining it hides nothing**. Run that command (check the
spelling of the concept it names in `concepts.txt` first), then read again. It also lists the
paragraphs that copied long stretches of the original in every try (that **also exits with
code 3**: a paragraph that is still mostly the original is not done): redo those with `--only`
and more `--tries`. It never touches a title or a greeting (up to four words, or a short line
closing with «:»): they come back exactly as they were. A try with broken characters
(«oraciÃ³n», «oraci6n», «presi&oacute;n») is discarded.

**A document made of bullets is the hard case** (measured on a 1,300-word pastoral proposal:
35-40% in Grammarly, against 0% for an essay of long paragraphs). Each bullet is one short
sentence: the model keeps the original's two opening words and changes two or three more, so
**47% of the final words still sat in runs of five or more identical to the original**, and
`join.py` has nothing to join. For a Spanish list use **`--vary-bullets --dry`** (measured on
the «Realizar» section, 220 words: words in runs of 4+ identical to the original 72% by default
→ 54% with `--vary-bullets` → **34% with `--vary-bullets --dry`**): a bullet that starts with a
bare infinitive («Ofrecer…») starts from that verb conjugated in a rotating form («Ofrecemos»,
«Formaremos», «Vamos a establecer», «Queremos promover»), and blocks of up to 40 words must
not copy more than 40% of their words in runs of four (runs of eight missed a bullet that only
lost an «y»); `check.py` applies the same rule afterwards. `--dry` alone with `--lead-words 0` was worse (81%: most bullets kept as the
original). Expect small agreement slips («sostenible y coordinadas», «la liderazgo»): they
are the one-to-three-word fixes of step 6.

**A list pasted as text** (one «•» per line, no blank lines) reaches the scripts as ONE
paragraph. Split it first and put the marks back at the end:

```bash
python3 <skill>/scripts/lists.py split pasted.txt -o 00-original.txt --map lists.json
# ... steps 4 to 7 (rewrite.py --vary-bullets --dry) ...
python3 <skill>/scripts/lists.py restore 02-final.txt --map lists.json -o 03-deliver.txt
```

**If the person accepts prose instead of bullets**, `split --merge` turns each run of bullets into
one paragraph and an inline numbered list («Criterios: 1.- A; 2.- B.») into one enumeration;
headings stay. Then the essay recipe applies: `rewrite.py` (a `--lead` with a conjugated verb,
such as «El centro ofrecerá», keeps the paragraph from starting with the original's infinitive)
and `join.py --pauses 2`. Measured on the same pastoral plan, in Grammarly: bullets rewritten by
the model and left as bullets 34-36%; the same bullets with two lines «polished» by Grammarly's
own humanizer 52%; rewritten by a large chat model 84%. **Do not polish**: the base model's
small awkward turns are what keep the score low.

**A table** (rows like «Tema: X · Actividades: Y · Texto bíblico: Z · Resultado esperado: W»,
the usual annex of a plan) is the hardest case. Measured on the same plan (11-nov-2026), in
Grammarly: the 8-row calendar as prose that kept its labels («…Texto bíblico: Lucas 24,13-15.
Resultado esperado: un grupo…») **22%**; the same with a different lead on every row still
**22%** (rows 14% and 30%); **one sentence with a verb per row**, the fields inside it
(«El primer encuentro es de presentación y confianza, … basándonos en Lucas 24,13-15, con el fin
de construir un grupo…») **0%**. Put the content shared by every row (duration, what each session
always has) in the intro paragraph, not in a row. Give each row its own `--lead` («El primer
encuentro es de», «En el segundo hablamos de», «La tercera semana toca», «Cerramos con la»).
The whole 1,312-word plan, done this way, measured **0% in both halves**.

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

The model's guards already reject, in each try: lost concepts, changed quotes, invented sources,
lost accents (including names of 4-5 letters: «Pérez»→«Perez»), a switch of language and
Spain's *vosotros* («venid», «vuestra», «coincidáis», «os»). They don't catch a **changed gender**
(«lo suficientemente buena» for a male writer), a flipped verb («afrontar la muerte»→«luchar
contra la muerte»), a wrong word that still fits the grammar («el cuerpo que se *desangra*»
for «muere») or a lost idea: those are what you look for.

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

**`check.py` also prints a NOTE (not an error) for shapes Grammarly flagged in prose** on that
plan: the «no X, sino que Y» antithesis (a 213-word section went from ~16% to 0% by changing it to
the model's own «no puede reemplazar…, pero puede ser…»), a row that keeps 2+ labels, the same
field frame row after row («el tema es…» in 3+ paragraphs), and a closing label followed by a
verbless clause («Compromiso final: que…» → «Nuestro compromiso final es que…»). Fix those
sentences only (pick another candidate or give a conjugated lead); a single «Propósito: …» line is
fine. Spelling fixes after that did not move the score (five one-word fixes, still 0%).

### 7. Rebuild the rhythm

```bash
python3 <skill>/scripts/join.py 01-rewritten.txt -o 02-final.txt --concepts concepts.txt --pauses 2 \
        --original 00-original.txt
```

With `--original`, `join.py` **refuses to run** (exit 2, nothing written) if a paragraph of the input is
still the original; redo it with `--only` first. `check.py` reports the same in step 8 and exits 1.
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
that sentences stay longer than in a polished essay. GPTZero's free scan reads 10,000
characters. Ask them to measure in their detector **together with a text of their own
written without AI**, and to tell you what is still flagged.

**Prepare what they paste, never let them pick the file** (blocking):

```bash
python3 <skill>/scripts/halves.py 02-final.txt --original 00-original.txt --copy 1
```

It writes `02-final-MEASURE-1.txt` (and `-2` if the text is over 1,400 words, cut before a
heading near the middle) and prints, for each half, a **check phrase** that only the final
has. Give the user that phrase: **a score counts only if the detector shows it.** Measured on
a test essay: the user pasted the original (53%, read as «it failed»), and a copy made with
plain `pbcopy` broke every accent («a√±os»; 0%, read as «it passed»). `--copy N` puts half
N on the clipboard in UTF-8 and reads it back; never copy with a bare `pbcopy`. When the
user sends a score, check the phrase in their screenshot before reading the number.

### Measuring without highlights (Grammarly free detector)

It gives a percentage and **no highlighted sentences** (checked in the page's DOM). What was
measured on the pastoral proposal: the score is **roughly additive by words** (the sections'
word-weighted average, 39.0%, matched the whole document's 35-40%); pasting the same text
twice gives the same percentage, so a section of 100-275 words is not just noise; and with
two 0% sections around it, a section scored the same as alone (31 vs 32). That makes a
**per-block measurement** possible: paste a 0% anchor text (~160 words) plus ONE block, and
the percentage times the words is that block's flagged share. ~12 s per measurement. **Do not
measure only a text you have rewritten**: the same section scored 70% as the original and
85% rewritten, so always keep the original's number beside it.

### 9. Select, for what a detector still flags

ZeroGPT and Grammarly highlight the sentences they flag. For each flagged paragraph:

```bash
python3 <skill>/scripts/rewrite.py 00-original.txt -o 01-rewritten.txt --concepts concepts.txt \
        --only 4 --candidates 6 --temperature 1.1
```

If the paragraph starts with a stock opening, add `--lead` with two other words that fit
the paragraph («Desde la», «La potencia», «Para Aristóteles»). Candidates land in
`01-rewritten.txt.candidates/`; tries that lose a concept, change a quote, invent a
reference, copy the original, eat Spanish accents («oraci n», «comunicacion»), switch
language, drop the negations an idea rests on, invent a quotation or repeat a sentence
are already discarded.

1. **Read each candidate against the original** and drop any that loses an idea, even if
   no concept is missing (one dropped a whole sentence about the contradiction between two
   authors).
2. **Have the user measure the survivors joined, inside the whole text**, not alone: a
   paragraph that scores 0% alone can be flagged in context, and the other way round.
3. Adopt the one that passes and join again:

```bash
python3 <skill>/scripts/rewrite.py 00-original.txt -o 01-rewritten.txt --take 4=01-rewritten.txt.candidates/p04-2.txt \
        --take 7=01-rewritten.txt.candidates/p07-1.txt   # one --take per paragraph
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
- `scripts/docx_tools.py` — step 1 and the end: take the body out of a `.docx` and put the final text back with the same formatting
- `scripts/halves.py` — step 8: halves to measure, check phrases, clipboard in UTF-8
- `references/evidence.md` — every measurement
- `references/detectors.md` — how to measure in Grammarly, GPTZero and ZeroGPT, with controls
- `examples/` — worked examples in English and Spanish
