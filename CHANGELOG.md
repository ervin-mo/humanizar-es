# Changelog

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
