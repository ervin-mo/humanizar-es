# Changelog

## Unreleased

**Lists keep their bullets and lose their skeleton (11-nov).**

- **`lists.py split/restore`:** a list pasted with one «•» per line and no blank lines reached
  `rewrite.py`, `join.py` and `check.py` as one 221-word paragraph. Now every line is a block,
  the marks go out of the model's view and come back at the end (exit 2 if the block count changed).
- **`rewrite.py --vary-bullets`:** a bullet that starts with a bare infinitive starts from that
  verb conjugated in a rotating form, also from try to try; blocks of up to 25 words are held to
  runs of 4 (max. 50% copied). Copied words on «3. Realizar»: 72% → 34% with `--dry`.
- **Measuring:** with Grammarly's daily free limit reached, the score stays at «—%»; a script
  that looked for «N% of this text» found another «0%» on the page and reported 0% for
  everything, AI original included. Check for the limit notice before reading any number.

**Documents made of bullets.** A second test document (1,300 words of short bullets) scored
35-40% in Grammarly. Causes found and fixed or documented:

- **`docx_tools.py` left a third of the words untouched.** Anything of 12 words or fewer was
  treated as a heading, so short bullets stayed as the original AI text (34% of the words).
  Now only real headings (up to four words, a line ending in «:», «1. Ubicar», «Acción 2.»,
  «Anexo») stay; a bullet of five or more words is rewritten.
- **`rewrite.py` exits with code 3 also when every try copied the original** (it only warned).
- **New guard for broken characters** (`oraciÃ³n`, `oraci6n`, `presi&oacute;n`).
- **Up to four words is a title for `rewrite.py` too** («Objetivo.» came back as «Objetivo;
  the purpose of this study is»).
- **New, unvalidated: `--dry` and `--lead-words N`** to make short bullets move away from the
  original (47% of the words stayed in runs of five or more identical ones).
- Documented how to measure without highlights (score is ~additive by words; per-block
  measurement with a 0% anchor) in `SKILL.md`.

**A paragraph that stays as the original no longer slips through.** Humanizing a 1,469-word
.docx assignment, paragraph 4 came back **identical to the original** (every try lost a
concept or invented a quote), `rewrite.py` printed one WARNING line and exited 0, and the
unchanged text would have been joined and delivered. Found by reading the paragraphs against
the original; fixed so the tools do it:

- **`rewrite.py --rescue N` (2).** A paragraph with no usable try gets extra rounds, the
  temperature up 0.1 each, before giving up.
- **Exit code 3 and `ACTION REQUIRED`** with the exact `--only` command when a paragraph still
  ends as the original.
- **`check.py` and `join.py --original`.** `check.py` lists the paragraphs that are still the
  original (copy 60%+ of it) and exits 1; `join.py --original` refuses to join them
  (`--allow-original` overrides). `copied_share` moved to `check.py`, shared by all three.
- **Headings with a colon are titles.** «Introducción:» was not recognized, went to the model
  and came back as «Introducción: Abstract»; «A mis seres queridos:» was lost the same way.
- **Two new guards on every try:** Spain's *vosotros* («venid y dadme… en vuestra
  misericordia», «aunque no coincidáis») and an accent lost in a short name («Ruiz Pérez» →
  «Ruiz Perez»; `spelling_problem` only looked at words of 6+ letters).
- **`scripts/docx_tools.py`**: `extract` the body of a .docx and `build` it back with the
  same formatting, header, titles and bibliography untouched (indents kept, text escaped,
  a short lead-in sentence mergeable with its paragraph). Checked on the real assignment:
  same blocks as the hand-made extraction, byte-identical .docx.
- 65 tests (7 new, each fails with the previous code).

## Unreleased

Three fixes found humanizing a 1,372-word Spanish assignment with numbered headings:

- **`--take` repeated kept only the last one, silently.** Adopting 7 candidates in one
  command changed 1 paragraph. `--take` now repeats (`--take 6=a.txt --take 18=b.txt`), checks
  every pair before writing, and a bad pair or a paragraph given twice changes nothing.
- **`join.py` broke numbered headings**: «1. Dimensión individual» came out as «1 y dimensión
  individual», «2; dimensión intelectual». A list number opening a paragraph («1.», «2.3.»)
  is no longer a sentence; a number closing one («el capítulo 3. Luego…») still is.
- **`rewrite.py` rewrote numbered headings that end in a period** («1. Dimensión individual:
  conocerme y orientar mi vida.»). A short paragraph (12 words or fewer) that opens with a
  list number («1.», «2.3.», «2.-», «4)») and holds one sentence is now a heading.

## Unreleased

**`scripts/halves.py`: a score counts only when it is the final's.** A test essay was measured
wrong twice, and both looked like real results: the user pasted the original (53%, read as
«it failed»), then a copy made with plain `pbcopy` broke every accent («a√±os»; 0%, read as
«it passed»). The final, measured right, scored 0% and 0%. `halves.py` cuts the text in
halves before a heading near the middle, prints a check phrase per half that only the final
has (and warns when a half is all original), and `--copy N` puts a half on the clipboard in
UTF-8 and reads it back. The skill makes it step 8.

 — October 9, 2026

**Three new fidelity guards**, found on a 3,433-word Spanish text of 60 short paragraphs
(pastoral theology answers, lists and headings). Every concept survived the rewrite, yet the
reread found what the guards could not see:

- **Accents eaten** in 11 of 60 paragraphs: «comunio'n», «oraci n», «composicin»,
  «acompanar», «Espiritu». The concept check ignores accents by design, so it passed them.
  A try is now rejected when an accented word of the original (6+ letters) comes back
  without its accent or missing that letter, when an apostrophe splits a word, or when the
  accent density falls below 40% of the original's.
- **Switched to English** in 2 paragraphs («VER significa listening and understanding the
  situation…»), despite the original's opening words. Rejected by function-word counts.
- **Negation dropped**: «el criterio no sería solo el de la asistencia» came out as «el
  criterio sería el de la asistencia». A try is rejected when it loses a «no solo» with no
  negation left, or a third of two or more negations. A single reworded negation («no
  propiedades» → «en lugar de propiedades») still passes.
- **Invented quotations**: a candidate wrote «Mateo 9,36: "¿Cuántos pastores hay entre
  vosotros?"», a verse that does not exist. A quotation must now be words the original has
  (quoting the original's own phrase, «"siempre lo hemos hecho así"», still passes).
- **Runaway repetition**: a candidate appended «2.- La parroquia es el lugar privilegiado
  para hacer proselitismo» twice. A run of 8 words said more times than in the original is
  rejected.
- Calibrated with no false rejection on the Spanish and English examples.

Measured on that text, rewritten, reviewed, joined (`--pauses 2`) and with selection on three
paragraphs ZeroGPT flagged: **Grammarly 0%, 0% and 8%** (three thirds, ~1,100 words each),
**ZeroGPT 0%, 0%, 0%**, **GPTZero 0/17/27% AI** (verdict "entirely human" on all three),
20/20 concepts. Human control: ZeroGPT 0%, GPTZero 100% human. The AI original also read
low (ZeroGPT 0-10%, GPTZero 3% AI): it was not raw chat output, so it is a weak AI control.

## 3.1.1 — October 7, 2026

**English, measured.** Two AI-generated English essays went from 100% to **0% in ZeroGPT**
(one of them with selection of three paragraphs). **GPTZero in English is the next
milestone**: its newer English model (4.1o) scored 100% AI on every variant tested on the whole
document - one and two passes of Qwen3-4B + HIP, temperature 1.3, mixed paragraphs, and two
other base-model families (Llama 3.1 8B, Mistral 7B) - while a 2016 human control read 100%
human. Spanish keeps passing all three detectors. Evidence: references/evidence.md, 2d.

- Docs: English results, the GPTZero limitation in the README, the skill and the detectors
  guide; GPTZero percentages explained as confidence; famous classics as ZeroGPT false
  positives (Emerson, 64.5%).

## 3.1.0 — October 7, 2026

**ZeroGPT passes.** The same 1,990-word essay now scores **0% in ZeroGPT, 0% and 0% in
Grammarly and 0% AI / 98% human in GPTZero**, keeping 24 of 24 concepts and its two
quotations verbatim. A fourth stage, selection, was added after taking ZeroGPT apart:
it scores sentence by sentence and weighs by words, so rhythm alone made it worse
(34% → 52%), and the base model gives a different version of a paragraph each run.

- `rewrite.py --candidates N --only K`: N acceptable versions of each listed paragraph in
  `<output>.candidates/`, without touching the output; `--take K=FILE` adopts one.
- `rewrite.py --lead "Desde la"`: other opening words. The original's first two words
  («Uno de los problemas…») made the model rebuild the stock sentence detectors flag.
- `rewrite.py --temperature` (1.0 by default; 1.1 gives more varied candidates).
- Fidelity guard: a try that changes a quotation of the original or adds a reference in
  brackets the original never had is rejected (the model wrote «(De Anima, libro i,
  cap. vi)» on a test essay).
- `join.py --pauses`: a sentence that opens with «Pero» / "But" joins as «, pero»; it
  used to produce «y pero».
- Docs: the method in four stages, what each detector measures, the ZeroGPT experiments
  (references/evidence.md, section 2c), and the selection step in the skill. 48 tests.

## 3.0.0 — October 7, 2026

A pipeline for two audiences: Spanish and English, with docs in both. Same name and URL,
so existing installs keep working.

**Measured:** a 1,990-word essay reached **0% and 0% in Grammarly** (two halves) and
**0% AI / 99% human in GPTZero**, keeping 24 of 24 key concepts. ZeroGPT does not pass yet.

- **Rhythm in blocks:** `join.py --pauses 2` leaves two or three periods per paragraph, in
  blocks of uneven length of at least two sentences, cutting first where a sentence already
  opens with a discourse marker. It reads like a person instead of one endless sentence.
  (6% while a block could be a single sentence; 0% once not allowed.)
- **Copy guard:** `rewrite.py` retries a try that copies more than 60% of its words from the
  original in runs of 8+ words (`--max-copied`); if every try does, it keeps the least copied
  one and warns. HIP had left half a paragraph word for word.
- **Regenerate instead of rewriting by hand:** `rewrite.py --only 6,11` redoes just those
  paragraphs and keeps the rest with their fixes. A hand fix is one to three words; bigger
  hand fixes kept half an essay at 3%, regenerating them gave 0%.
- `--tries` defaults to 6 (only a failing paragraph uses them); the warning for an unchanged
  paragraph names the concept it kept losing.
- English: `join.py` detects the language and links with "and"/";"; `check.py` knows English
  negations; `rewrite.py` restores the `%` sign the HIP adapter drops.
- Scripts in English: `rewrite.py` (was `hip.py`), `join.py` (`unir.py`), `check.py`
  (`verificar_fidelidad.py`), `install_model.py` (`instalar_hip.py`). The old names, flags
  (`--conceptos`, `--pausas`…) and environment variables still work. The model stays in
  `~/.cache/humanizar-es/hip`: no re-download.
- Docs: `README.md` (English) and `README.es.md` (Spanish), with the method, the controlled
  measurements and how we measure (a human control and the AI original in every session).

---

*Earlier entries, in Spanish:*

## 2.1.1 — 2 de octubre de 2026

- README en español y en inglés (`README.en.md`), con preguntas frecuentes.
- Tabla de detectores: optimizado para Grammarly; GPTZero y ZeroGPT, próxima mejora.
- `CITATION.cff` para citar el repo. Licencia a nombre de ervin-mo.

## 2.1.0 — 1 de octubre de 2026

Funciona en **Windows** igual que en macOS y Linux, sin Git Bash ni WSL.

- `install.py` e `instalar_hip.py` reemplazan a los `.sh` (que quedan como atajos). La
  descarga del modelo ya no necesita curl ni shasum, y si se corta sigue donde se quedó.
- `hip.py` le pasa el prompt a llama.cpp en un archivo UTF-8 y lee su salida como UTF-8: en
  Windows los acentos se habrían roto. Baja la prioridad del proceso también en Windows.
- `hip.py` encuentra llama.cpp recién instalado con winget sin abrir otra terminal, y
  acepta la ruta en `HUMANIZAR_LLAMA`.
- Las pruebas corren en Ubuntu, macOS y Windows, con una prueba de punta a punta de
  `hip.py` con un llama.cpp falso.
- `.gitattributes`: los scripts conservan los saltos de línea de Unix al clonar en Windows.

## 2.0.1 — 1 de octubre de 2026

- Evidencia: un tercer ensayo (690 palabras) pasó a **0%** en Grammarly en la primera
  corrida de la skill hecha por un agente, con 9 correcciones a mano y 18 de 18 conceptos.

## 2.0.0 — 1 de octubre de 2026

La repo queda solo con la receta que funciona: **`hip.py` → corrección a mano →
`unir.py`**. Dos ensayos completos a 0% y 10% en Grammarly, sin errores.

- `instalar_hip.sh` ya no convierte nada: baja el adaptador HIP ya convertido a GGUF desde
  las descargas del repo y verifica los dos archivos con sha256. Sin paquetes de Python.
- Se quitaron el cubo, la ruleta, `ensuciar.py`, el detector local, la cadena de
  traducción, la guía de reescritura a mano y los ejemplos viejos. Lo que se probó y no
  funcionó queda resumido en `references/evidencia.md` §4.
- Ejemplo nuevo en `ejemplos/`: un ensayo, su reescritura corregida y el resultado.
- `SKILL.md` reescrita para que el agente siga la receta de punta a punta.

## 1.4.0 — 1 de octubre de 2026

- **`scripts/unir.py`** reemplaza a `ensuciar.py` en la receta: une las oraciones de cada
  párrafo con «y», sin meter errores de ortografía ni de puntuación. `hip.py` + `unir.py`
  llevó dos ensayos completos a 0% y 10% en Grammarly.
- La receta corrige a mano **antes** de unir: corregir después subía el número.
- `ensuciar.py` queda como alternativa; ya no se recomienda.
- Evidencia nueva en `references/evidencia.md` §4f: qué castiga Grammarly, un cambio a la vez.

## 1.3.0 — 1 de octubre de 2026

- **Receta nueva, local y sin costo:** `scripts/hip.py` reescribe cada párrafo con un
  modelo base (Qwen3-4B-Base + adaptador HIP de Xu et al. 2026) y `scripts/ensuciar.py`
  le quita la redacción demasiado limpia. Un ensayo completo de 1,150 palabras: 8% IA en
  Grammarly, en unos 4 minutos de CPU.
- `scripts/instalar_hip.sh`: descarga el modelo y convierte el adaptador (~5.5 GB).
- `ensuciar.py` no toca la ortografía por defecto; `--ortografia` es opcional.
- El cubo pasa a ser la alternativa con API.
- Corregido: si el revisor del cubo contestaba vacío, se vetaba el lote entero y el
  párrafo se quedaba sin tocar. Ahora reintenta y parte el lote.
- Corregido: el `*` de los conceptos por prefijo ya no se cuela al texto.
- Evidencia nueva en `references/evidencia.md` §4e.

## 1.2.0 — 30 de septiembre de 2026

- **El cubo** (`scripts/cubo.py`): reescritura oración por oración guiada por un detector
  local. Llevó un párrafo de 100% IA a 0% en Grammarly y 99% humano en CleverHumanizer.
  Trabaja párrafo por párrafo por defecto; `--texto-completo` gira todo a la vez.
- Detector local (`scripts/sustituto.py`): Binoculars + Fast-DetectGPT sobre Qwen2.5.
- Revisor de sentido: otro modelo veta los giros que cambian, inventan o no tienen lógica.
- Varias familias de generadores (`HUMANIZAR_MODEL="a,b"`) y aviso de palabras repetidas.
- `scripts/calibrar.py`: mide qué tan bien predice el detector local a tu detector.
- `scripts/ruleta.py`: sinónimos guiados por detector (opcional; no movió a Grammarly).
- La skill funciona en Claude Code, Codex, OpenCode, Antigravity y DeepSeek Harness;
  `install.sh` instala por defecto en `~/.claude/skills` y `~/.agents/skills`.
- CPU por defecto: en Mac, la GPU traba la pantalla.

## 1.1.0 — 30 de septiembre de 2026

- `scripts/estilo.py` (sin dependencias) y `verificar_fidelidad.py` configurable, con
  detección de negaciones perdidas.
- Benchmark revisado con dos rondas de refutación; resultados de Grammarly.

## 1.0.0

- Guía de reescritura, benchmark inicial y scripts de medición.
