#!/usr/bin/env python3
"""Rewrite with a local BASE model (HIP), no API and no GPU.

Detectors mostly recognize the fingerprint of chat training: text from a base model
(without that training) looks human to them. HIP is Qwen3-4B-Base with a LoRA
adapter trained to paraphrase back toward human prose (Xu et al., 2026, «Base
Models Look Human To AI Detectors», arXiv:2605.19516; MIT code, Apache-2.0 adapter).

It was trained in English: left alone it translates Spanish into English. That is
why each paragraph starts with its first two original words, so the model keeps
writing in the language of the original.

A single pass per paragraph: with more passes the text drifts from the meaning. If
a paragraph loses a concept from --concepts or comes out truncated, it is retried;
if nothing works, the original is kept and a warning names the concept it kept losing.
HIP sometimes copies long stretches of the original word for word; a try that copies
more than --max-copied of its words in runs of 8+ words is retried too, and if every
try copies that much, the least copied one is kept and a warning is printed.

Runs on CPU (-ngl 0) at low priority. About 30 s per paragraph on an M4 Mac.
Install first: python3 scripts/install_model.py  (about 4.6 GB in ~/.cache/humanizar-es/hip)

usage:
  python3 scripts/rewrite.py original.txt -o rewritten.txt --concepts concepts.txt
  python3 scripts/join.py rewritten.txt -o final.txt --concepts concepts.txt
"""
import argparse
import collections
import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):  # so a Windows console does not choke on «» or ñ
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

BASE = "Qwen3-4B-Base.Q8_0.gguf"
ADAPTER = "hip-qwen3-4b-base.gguf"
MODEL_FILES = (BASE, ADAPTER)


def _has_model(directory):
    return all(os.path.isfile(os.path.join(directory, f)) for f in MODEL_FILES)


def resolve_model_dir(environ=None, home=None):
    """Where the model lives: $HUMANIZE_MODEL_DIR (or the old $HUMANIZAR_HIP_DIR), else
    ~/.cache/humanizar-es/hip, the folder every version has used, so nobody downloads
    4.6 GB again."""
    environ = os.environ if environ is None else environ
    custom = environ.get("HUMANIZE_MODEL_DIR") or environ.get("HUMANIZAR_HIP_DIR")
    if custom:
        return custom
    return os.path.join(home or os.path.expanduser("~"), ".cache", "humanizar-es", "hip")


MODEL_DIR = resolve_model_dir()


LEAD_WORDS = 2     # how many of the original's first words open the rewrite (--lead-words)
SAMPLING_EXTRA = []  # extra llama.cpp sampler flags (--dry)
DRY_FLAGS = ["--min-p", "0.08", "--dry-multiplier", "0.8", "--dry-base", "1.75",
             "--dry-allowed-length", "2"]


# --vary-bullets: a list of «Ofrecer…», «Formar…», «Establecer…», «Promover…» keeps its
# skeleton after the model rewrites it, because it starts every bullet with the original's
# first two words and changes two or three more: on a pastoral plan 72% of the words still
# sat in runs of 4+ identical to the original and Grammarly scored the list 70-85%. The
# infinitive alone is not the tell (another list of infinitives in the same document scored
# 0%); the copying is. So the bullet starts from its own verb CONJUGATED in a form that
# rotates from bullet to bullet and from try to try («Ofrecemos», «Formaremos», «Vamos a
# establecer», «Queremos promover»), and a short block is held to a stricter copy check.
INFINITIVE = re.compile(r"[A-ZÁÉÍÓÚ][a-záéíóúñü]*(?:ar|er|ir)(?:se|nos|los|las|lo|la|le|les)?")
NOT_INFINITIVE = set("""lugar hogar mujer ayer placer poder deber ser taller altar
    nivel azar collar pilar militar familiar similar particular popular titular regular
    escolar celular solar dólar sur primer tercer cualquier líder carácter bienestar
    malestar porvenir auxiliar singular preliminar mayor menor par mar bar""".split())
BULLET_MAX_WORDS = 40
SHORT_BLOCK = 25          # words: up to this, copying is measured in runs of SHORT_RUN
SHORT_RUN = 4
SHORT_MAX_COPIED = 0.5
_FUTURE_STEM = {"decir": "dir", "poder": "podr", "saber": "sabr", "querer": "querr",
                "haber": "habr", "caber": "cabr"}
_FUTURE_SUFFIX = (("poner", "pondr"), ("tener", "tendr"), ("venir", "vendr"),
                  ("hacer", "har"), ("salir", "saldr"), ("valer", "valdr"))
_PRESENT = {"ser": "somos", "ir": "vamos", "haber": "hemos"}
BULLET_FORMS = ("present", "future", "vamos", "queremos")


def _nosotros(inf, form):
    """«ofrecer» → «ofrecemos» / «ofreceremos». None when it is not safe (accented or
    pronominal infinitives): the caller then uses «vamos a» + the infinitive."""
    if form == "present":
        if inf in _PRESENT:
            return _PRESENT[inf]
        return inf[:-2] + {"ar": "amos", "er": "emos", "ir": "imos"}[inf[-2:]]
    if inf in _FUTURE_STEM:
        return _FUTURE_STEM[inf] + "emos"
    for end, stem in _FUTURE_SUFFIX:
        if inf.endswith(end):
            return inf[:-len(end)] + stem + "emos"
    return inf + "emos"


def bullet_lead(paragraph, k):
    """The opening for a bullet that starts with a bare infinitive, or None. k counts the
    bullets (and, inside one, the tries), so the form rotates."""
    words = paragraph.split()
    if not words or len(words) > BULLET_MAX_WORDS:
        return None
    w = words[0].strip(",;:«¿¡\"")
    if not INFINITIVE.fullmatch(w) or w.lower() in NOT_INFINITIVE:
        return None
    inf = w.lower()
    form = BULLET_FORMS[k % len(BULLET_FORMS)]
    plain = re.fullmatch(r"[a-zñü]+(?:ar|er|ir)", inf)  # no accent, no enclitic pronoun
    if form in ("present", "future") and plain:
        verb = _nosotros(inf, form)
        return verb[0].upper() + verb[1:]
    if inf.endswith(("arse", "erse", "irse")):  # «Vamos a reunirnos», not «reunirse»
        inf = inf[:-2] + "nos"
    return ("Vamos a " if form != "queremos" else "Queremos ") + inf


def build_prompt(paragraph, lead_words=None, lead=None):
    """The format HIP was trained on, plus the first words of the paragraph so the
    model keeps writing in the language of the original. `lead` replaces those words:
    the original's own opening («Uno de los problemas más importantes…») ties the model
    to the stock sentence a detector flags; another opening («Desde la») frees it."""
    if lead_words is None:
        lead_words = LEAD_WORDS
    lead = lead or " ".join(paragraph.split()[:lead_words])
    prompt = f"<source_text>\n{paragraph.strip()}\n</source_text>\n\n<target_text>\n{lead}"
    return prompt, lead


def clean_output(lead, generated):
    text = (lead + generated).split("</target_text>")[0]
    return " ".join(text.split())


HOW_TO_INSTALL_LLAMA = ("On macOS or Linux: brew install llama.cpp. On Windows: winget install "
                        "llama.cpp and open a new terminal. If it is already installed in another "
                        "folder, put its path in the HUMANIZE_LLAMA variable.")


def llama_binary():
    """llama-completion (or llama-cli, in old versions). Looks in HUMANIZE_LLAMA (or the old
    HUMANIZAR_LLAMA), in the PATH and, on Windows, in the winget folder, which does not
    reach the PATH until another terminal is opened."""
    custom = os.environ.get("HUMANIZE_LLAMA") or os.environ.get("HUMANIZAR_LLAMA")
    if custom:
        return custom if os.path.isfile(custom) else None
    paths = [None]
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "")
        paths.append(os.path.join(local, "Microsoft", "WinGet", "Links"))
    for path in paths:
        for b in ("llama-completion", "llama-cli"):
            found = shutil.which(b, path=path)
            if found:
                return found
    return None


def rewrite_paragraph(paragraph, threads=4, temperature=1.0, lead=None):
    prompt, lead = build_prompt(paragraph, lead=lead)
    # The prompt goes in a UTF-8 file and not on the command line: on Windows accents
    # and quotes get mangled when passed as an argument.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as fh:
        fh.write(prompt)
    try:
        return clean_output(lead, _run_llama(fh.name, paragraph, threads, temperature))
    finally:
        os.remove(fh.name)


def _run_llama(prompt_file, paragraph, threads, temperature):
    llama = llama_binary()
    cmd = [llama, "-m", os.path.join(MODEL_DIR, BASE),
           "--lora", os.path.join(MODEL_DIR, ADAPTER),
           "-ngl", "0", "-dev", "none", "-t", str(threads), "-c", "4096",
           "-n", str(int(len(paragraph.split()) * 3) + 100),
           "--temp", str(temperature), "--top-p", "0.95", *SAMPLING_EXTRA,
           "-no-cnv", "--no-display-prompt", "-r", "</target_text>", "-f", prompt_file]
    if llama.endswith(".py"):  # a fake llama, for the tests
        cmd = [sys.executable] + cmd
    extra = {}
    if os.name == "nt":  # low priority, like nice on macOS and Linux
        extra["creationflags"] = subprocess.BELOW_NORMAL_PRIORITY_CLASS
    elif shutil.which("nice"):
        cmd = ["nice", "-n", "15"] + cmd
    # llama.cpp writes UTF-8; without an encoding, Windows would read it as cp1252.
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL, **extra)
    return r.stdout


def restore_percent_signs(original, rewritten):
    """The HIP adapter eats the % sign: «60%» comes out as «60». If the original had
    that number with %, it is given back. Numbers the original did not have with %
    are left alone."""
    for n in set(re.findall(r"(\d+(?:[.,]\d+)?)\s?%", original)):
        if not re.search(rf"(?<![\d.,]){re.escape(n)}\s?%", rewritten):
            rewritten = re.sub(rf"(?<![\d.,]){re.escape(n)}(?![\d.,]*\d)(?!\s?%)",
                               n + "%", rewritten, count=1)
    return rewritten


def concepts_in(text, concepts):
    t = check.norm(text)
    return {n for n, variants in concepts if any(check.pattern(v).search(t) for v in variants)}


COPY_RUN = check.COPY_RUN
copied_share = check.copied_share


QUOTE = re.compile(r'["“«]([^"”»]{12,})["”»]')
REFERENCE = re.compile(r"\(([^()]*\b(?:[ivxlc]+|\d+)\b[^()]*)\)", re.I)


def citation_problem(original, rewritten):
    """A quotation of the original that is no longer verbatim, or a reference in
    brackets the original never had («(De Anima, libro i, cap. vi)»). HIP did both on a
    test essay; a changed quote or an invented source is worse than any detector score.
    It also wrote Bible verses that do not exist: «Mateo 9,36: "¿Cuántos pastores hay
    entre vosotros?"» - a quotation must be words the original has."""
    norm = lambda s: " ".join(s.lower().split()).strip(" .,;:")  # noqa: E731
    have = norm(rewritten)
    for q in QUOTE.findall(original):
        if norm(q) not in have:
            return "(quote changed)"
    whole = norm(re.sub(r"[\"“”«»]", "", original))
    for q in QUOTE.findall(rewritten):  # quoting the original's own words is fine
        if norm(q) not in whole:
            return "(invented quote)"
    known = {norm(r) for r in REFERENCE.findall(original)}
    for r in REFERENCE.findall(rewritten):
        if norm(r) not in known:
            return "(invented reference)"
    return None


ACCENTED = "áéíóúüñ"


def _plain(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def spelling_problem(original, rewritten):
    """HIP sometimes eats Spanish accents: «comunio'n», «oraci n», «composicin»,
    «acompanar», «Espiritu». On a 60-paragraph test text it did so in 11 of them; the
    concepts survived (the comparison ignores accents), so nothing caught it."""
    low = original.lower()
    if not any(c in low for c in ACCENTED):
        return None
    if re.search(r"[^\W\d_]'[^\W\d_]", rewritten) and not re.search(r"\w'\w", original):
        return "(broken accents)"
    have = set(re.findall(r"\w+", rewritten.lower()))
    for w in sorted(set(re.findall(r"\w+", low))):
        if len(w) < 6 or not any(c in w for c in ACCENTED):
            continue
        bad = {_plain(w)}
        for i, c in enumerate(w):
            if c in ACCENTED:
                bad.add(w[:i] + _plain(c) + w[i + 1:])
                if i < len(w) - 1:  # «composicin»; a final «evaluará» -> «evaluar» is a word
                    bad.add(w[:i] + w[i + 1:])
        bad.discard(w)
        if bad & have:
            return "(accents lost: " + sorted(bad & have)[0] + ")"
    n = sum(c in ACCENTED for c in low)  # a short sentence may reword its only accent away
    a = n / max(1, len(original.split()))
    b = sum(c in ACCENTED for c in rewritten.lower()) / max(1, len(rewritten.split()))
    if n >= 4 and a >= 0.05 and b < 0.4 * a:
        return "(accents lost)"
    return None


SPANISH_WORDS = set("de la el que y en los las del se un una por con para no es su al lo como "
                    "más pero sus le ya o este sí porque esta entre cuando muy sin sobre también".split())
ENGLISH_WORDS = set("the and of to in is that for with as it be are on this was by an at from "
                    "or which not but have has their they its without people we our you "
                    "would will should can there these those been were".split())


def language_problem(original, rewritten):
    """HIP was trained in English and sometimes translates mid-text even with the
    original's opening words: «VER significa listening and understanding the situation»."""
    def counts(t):
        ws = re.findall(r"[^\W\d_]+", t.lower())
        return sum(w in SPANISH_WORDS for w in ws), sum(w in ENGLISH_WORDS for w in ws)
    oes, oen = counts(original)
    res, ren = counts(rewritten)
    # two words are enough in a short sentence: «VER significa listening and understanding
    # the situation, without blaming people immediately» has no Spanish function word at all
    if oes > oen and ren >= 2 and ren > 0.5 * res:
        return "(switched to English)"
    # a short list of nouns can be English without one function word («Offering identity,
    # self-esteem, emotion management…»): no Spanish word at all in five or more is not Spanish
    if oes > oen and res == 0 and len(re.findall(r"[^\W\d_]+", rewritten)) >= 5:
        return "(switched to English)"
    if oen > oes and res >= 2 and res > 0.5 * ren:
        return "(switched to Spanish)"
    return None


NEGATION = re.compile(rf"(?<!\w)({check.NEGATIONS})(?!\w)")


def negation_problem(original, rewritten):
    """A try that drops the negations an idea rests on. «el criterio no sería solo el de
    la asistencia» came out as «el criterio sería el de la asistencia»: same concepts,
    opposite idea. Single negations are often reworded legitimately («no propiedades» ->
    «en lugar de propiedades»), so only clear losses are rejected."""
    t, u = check.norm(original), check.norm(rewritten)
    o, r = len(NEGATION.findall(t)), len(NEGATION.findall(u))
    if o >= 2 and r < o - max(1, o // 3):
        return f"(negations lost: {o} -> {r})"
    # «no se medirá solo por la asistencia, sino por…» -> «no se medirá en términos de
    # asistencia, sino de…»: a negation is left, but «only» became «not at all»
    # «no quedará un solo sector» is not that construction: it needs «sino» and no «un»
    not_only = r"(?<!\w)no (\w+ ){0,3}(?<!un )(solo|solamente|unicamente)(?!\w).*(?<!\w)sino(?!\w)"
    kept = r"(?<!\w)(solo|solamente|unicamente|simplemente|meramente|limit\w*|tambien|ademas)(?!\w)"
    if re.search(not_only, t) and (r == 0 or not re.search(kept, u)):
        return "(«no solo» lost)"
    return None


def repetition_problem(original, rewritten, n=COPY_RUN):
    """HIP sometimes runs on, repeating a sentence it invented: «2.- La parroquia es el
    lugar privilegiado para hacer proselitismo… 3.- La parroquia es el lugar privilegiado
    para hacer proselitismo…». A run of n words said more times than in the original is
    rejected; the original's own repetitions are allowed."""
    def grams(t):
        w = re.findall(r"\w+", check.norm(t))
        return collections.Counter(tuple(w[i:i + n]) for i in range(len(w) - n + 1))
    have, had = grams(rewritten), grams(original)
    for g, k in have.items():
        if k >= 2 and k > had[g]:
            return "(repeated: " + " ".join(g) + ")"
    return None


# Spanish of Mexico: «venid», «vuestra», «os prometisteis», «coincidáis» are Spain's
# «vosotros». HIP writes them now and then; they read as a different voice in a text that
# never used them (a prayer came back as «venid y darme la fuerza de creer en vuestra
# misericordia»).
VOSOTROS = re.compile(
    r"(?<!\w)(?:vuestr[oa]s?|sois|veis|os|[^\W\d_]+[áé]is|"
    r"venid|recibidme|dadme|escuchad|mirad|acompañad|seguid|tened|sed|haced|ved|perdonad)(?!\w)",
    re.I)


def _looks_spanish(text):
    ws = re.findall(r"[^\W\d_]+", text.lower())
    return sum(w in SPANISH_WORDS for w in ws) > sum(w in ENGLISH_WORDS for w in ws)


def vosotros_problem(original, rewritten):
    if _looks_spanish(original) and not VOSOTROS.search(original):
        m = VOSOTROS.search(rewritten)
        if m:
            return "(vosotros form: " + m.group(0) + ")"
    return None


def proper_accent_problem(original, rewritten):
    """«Ruiz Pérez» came back as «Ruiz Perez». spelling_problem only looks at words of
    6+ letters; a name of 4-5 letters («Pérez», «Ríos», «Jesús») slipped through."""
    low = {w.lower() for w in re.findall(r"\w+", rewritten)}
    plain = {_plain(w) for w in low}
    for w in sorted(set(re.findall(r"\b[A-ZÁÉÍÓÚÑ][^\W\d_]*[áéíóúüñ][^\W\d_]*", original))):
        if len(w) >= 4 and w.lower() not in low and _plain(w.lower()) in plain:
            return "(accent lost in a name: " + w + ")"
    return None


def encoding_problem(original, rewritten):
    """The base model sometimes writes the UTF-8 bytes of an accent as two characters
    («oraciÃ³n»), turns it into a digit («oraci6n») or into an HTML entity
    («presi&oacute;n»). None of it is Spanish and a reader sees it at once."""
    for rx, what in ((r"[ÃÂ][\u0080-\u00bf¡-¿]", "mojibake"),
                     (r"&(?:[a-zA-Z]{2,8}|#\d{2,5});", "HTML entity"),
                     (r"\b[^\W\d_]+\d[^\W\d_]+\b", "digit inside a word")):
        mine = set(re.findall(rx, rewritten))
        theirs = set(re.findall(rx, original))
        if mine - theirs:
            return f"(broken characters: {what} {sorted(mine - theirs)[0]!r})"
    return None


def acceptable(p, r, wanted, concepts, max_copied, strict_short=False):
    """(problem, copied share) for one try: problem is None when the try can be used."""
    if len(r.split()) < 0.6 * len(p.split()) or len(r.split()) > 1.6 * len(p.split()) + 10:
        return "(truncated or too long)", 0.0
    missing = wanted - concepts_in(r, concepts)
    if missing:
        return sorted(missing)[0], 0.0
    for guard in (encoding_problem, citation_problem, spelling_problem, proper_accent_problem,
                  language_problem,
                  vosotros_problem, negation_problem, repetition_problem):
        problem = guard(p, r)
        if problem:
            return problem, 0.0
    if strict_short and len(p.split()) <= SHORT_BLOCK:
        # runs of 8 miss a short bullet that only lost an «y» every seven words
        share = check.copied_share(p, r, SHORT_RUN)
        return ("(copied)" if share > min(max_copied, SHORT_MAX_COPIED) else None), share
    share = copied_share(p, r)
    return ("(copied)" if share > max_copied else None), share


# «1. Dimensión individual: conocerme.», «2.3. Método.», «2.- Fines.», «4) Cierre.»
NUMBERED_HEADING = re.compile(r"\d+(?:\.\d+)*(?:\.-?|\))\s+(?P<rest>.+)")


def is_title(p):
    if len(p.split()) > 12:
        return False
    # «Objetivo.» came back as «Objetivo; the purpose of this study is»: up to four
    # words is a heading, whatever it ends with (docx_tools.py uses the same rule)
    if len(p.split()) <= 4:
        return True
    # «Introducción:», «A mis seres queridos:» - a short line closing with a colon is a
    # heading or a greeting, not prose. HIP turned «Introducción:» into «Introducción: Abstract».
    if (p.rstrip().endswith(":") and len(p.split()) <= 8
            and not re.search(r"[.!?…]\s", p.strip())):
        return True
    if not p.rstrip().endswith((".", "!", "?", "…", ":")):
        return True
    # a numbered heading that closes with a period: one sentence after the list number
    m = NUMBERED_HEADING.fullmatch(p.strip())
    return bool(m) and not re.search(r"[.!?…]\s", m.group("rest"))


def main():
    ap = argparse.ArgumentParser(description="Rewrite with a local base model (HIP), paragraph by paragraph.")
    ap.add_argument("original")
    ap.add_argument("-o", "--output", "--salida", dest="output", required=True)
    ap.add_argument("--concepts", "--conceptos", dest="concepts",
                    help="file of concepts that must not be lost")
    ap.add_argument("--tries", "--intentos", dest="tries", type=int, default=6,
                    help="tries per paragraph (6); only a paragraph that fails uses more than one")
    ap.add_argument("--rescue", type=int, default=2,
                    help="extra rounds (2) for a paragraph with no usable try: the temperature "
                    "goes up 0.1 each round, so the paragraph is rewritten instead of "
                    "staying as the original")
    ap.add_argument("--max-copied", dest="max_copied", type=float, default=0.6,
                    help="retry a try that copies more than this share of the original (0.6)")
    ap.add_argument("--threads", "--hilos", dest="threads", type=int, default=4,
                    help="CPU threads (4)")
    ap.add_argument("--only", help="redo only these paragraphs (e.g. 7,11) of an existing output, "
                    "from the original, keeping the others and their hand fixes")
    ap.add_argument("--lead", help="opening words for the rewritten paragraphs instead of the "
                    "original's first two (e.g. \"Desde la\"); use it with --only")
    ap.add_argument("--dry", action="store_true",
                    help="DRY sampler + min-p: penalises copying runs of the original that sit "
                    "in the prompt (short bullets stay 47%% word for word without it)")
    ap.add_argument("--lead-words", dest="lead_words", type=int, default=2,
                    help="how many of the original's first words open the rewrite (2); 0 lets "
                    "the model choose how to start, which breaks the original's skeleton in "
                    "short bullets")
    ap.add_argument("--vary-bullets", dest="vary_bullets", action="store_true",
                    help="Spanish lists: a bullet that starts with a bare infinitive («Ofrecer…») starts "
                    "from that verb conjugated, in a form that rotates («Ofrecemos», «Formaremos», "
                    "«Vamos a establecer», «Queremos promover»), and blocks of up to 25 words are "
                    "held to a stricter copy check (runs of 4, at most 50%%)")
    ap.add_argument("--temperature", type=float, default=1.0,
                    help="sampling temperature (1.0); 1.1-1.2 gives more varied candidates")
    ap.add_argument("--candidates", type=int, metavar="N",
                    help="with --only: write N acceptable versions of each paragraph to "
                    "<output>.candidates/ instead of changing the output")
    ap.add_argument("--take", metavar="N=FILE", action="append",
                    help="put the text of FILE in paragraph N of the output (no model needed); "
                    "repeat it to adopt several paragraphs at once")
    args = ap.parse_args()
    global LEAD_WORDS
    LEAD_WORDS = args.lead_words
    if args.dry:
        SAMPLING_EXTRA.extend(DRY_FLAGS)

    if args.take:
        return take(args.original, args.output, args.take)
    if args.candidates and not args.only:
        print("ERROR: --candidates needs --only (which paragraphs)", file=sys.stderr)
        return 2

    if not llama_binary():
        print("ERROR: llama.cpp is missing. " + HOW_TO_INSTALL_LLAMA, file=sys.stderr)
        return 2
    for f in MODEL_FILES:
        if not os.path.isfile(os.path.join(MODEL_DIR, f)):
            print(f"ERROR: {f} is missing in {MODEL_DIR}; run scripts/install_model.py",
                  file=sys.stderr)
            return 2

    with open(args.original, encoding="utf-8") as fh:
        text = fh.read()
    concepts = check.load_concepts(args.concepts) if args.concepts else []
    paragraphs = [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()]
    kept = None
    if args.only:
        only = {int(n) for n in args.only.split(",")}
        if not os.path.isfile(args.output):
            print(f"ERROR: --only needs the existing {args.output}", file=sys.stderr)
            return 2
        with open(args.output, encoding="utf-8") as fh:
            kept = [x.strip() for x in re.split(r"\n\s*\n", fh.read()) if x.strip()]
        if len(kept) != len(paragraphs):
            print(f"ERROR: {args.output} has {len(kept)} paragraphs and the original "
                  f"{len(paragraphs)}; --only needs the same count", file=sys.stderr)
            return 2
    output, untouched, copied, t0 = [], [], [], time.time()
    varied = 0
    for i, p in enumerate(paragraphs, 1):
        lead, bullet = args.lead, None
        if args.vary_bullets and not args.lead and not is_title(p) and bullet_lead(p, 0):
            bullet, varied = varied, varied + 1
        if kept is not None and i not in only:
            output.append(kept[i - 1])
            continue
        if is_title(p):
            output.append(p)
            continue
        wanted = concepts_in(p, concepts)
        if args.candidates:
            write_candidates(args, i, p, wanted, concepts, lead, bullet)
            output.append(kept[i - 1])
            continue
        chosen, mostly_copied, lost = None, [], collections.Counter()
        n, rescued = 0, 0
        for rnd in range(args.rescue + 1):
            temperature = min(1.4, args.temperature + 0.1 * rnd)
            for n in range(1, args.tries + 1):
                if bullet is not None:  # another form on every try
                    lead = bullet_lead(p, bullet + n - 1 + rnd * args.tries)
                r = restore_percent_signs(p, rewrite_paragraph(p, args.threads, temperature,
                                                               lead))
                problem, share = acceptable(p, r, wanted, concepts, args.max_copied,
                                            strict_short=args.vary_bullets)
                if problem == "(copied)":
                    mostly_copied.append((share, r))
                    continue
                if problem:
                    lost[problem] += 1
                    continue
                chosen = r
                break
            if chosen is not None:
                rescued = rnd
                break
            if rnd < args.rescue:
                print(f"Paragraph {i}: no usable try, round {rnd + 2} at temperature "
                      f"{min(1.4, args.temperature + 0.1 * (rnd + 1)):.1f}", flush=True)
        if chosen is None and mostly_copied:
            share, chosen = min(mostly_copied, key=lambda c: c[0])
            copied.append(f"{i} ({share:.0%})")
        if chosen is None:
            untouched.append(f"{i} (" + ", ".join(c for c, _ in lost.most_common(2)) + ")")
            chosen = p
        output.append(chosen)
        with open(args.output, "w", encoding="utf-8") as fh:  # saves after every paragraph
            fh.write("\n\n".join(output + (kept or paragraphs)[i:]) + "\n")
        status = ("unchanged" if chosen == p else f"done, rescue {rescued}" if rescued
                  else f"done, try {n}" if n > 1 else "done")
        print(f"Paragraph {i} of {len(paragraphs)}: {status} ({time.time() - t0:.0f} s)", flush=True)

    if args.candidates:
        print(f"\nCandidates in {args.output}.candidates/ — the output was not changed. Measure them\n"
              "joined and inside the whole text, then adopt one with --take N=FILE.")
        return 0
    print(f"\nWritten: {args.output}")
    if untouched:
        nums = ",".join(u.split(" ")[0] for u in untouched)
        print("WARNING: kept as the original, the concept they kept losing in brackets: "
              + "; ".join(untouched) + ". Check the spelling of that concept in the concepts file.")
        print("ACTION REQUIRED: these paragraphs are still the ORIGINAL text, so a detector will "
              "flag them. Redo them before joining:\n"
              f"  python3 {sys.argv[0]} {args.original} -o {args.output} "
              + (f"--concepts {args.concepts} " if args.concepts else "")
              + f"--only {nums} --tries {args.tries * 2} --temperature 1.2\n"
              "or, if one concept keeps failing, fix its spelling in the concepts file first.")
    if copied:
        nums = ",".join(c.split(" ")[0] for c in copied)
        print("WARNING: every try copied long stretches of the original; the least copied one "
              "was kept: " + "; ".join(copied) + ". Redo them with --only and more --tries.")
        print("ACTION REQUIRED: those paragraphs are still mostly the ORIGINAL, so a detector "
              "will flag them. Redo them (try --dry and --lead-words 0, or --candidates):\n"
              f"  python3 {sys.argv[0]} {args.original} -o {args.output} "
              + (f"--concepts {args.concepts} " if args.concepts else "")
              + f"--only {nums} --tries {args.tries * 2} --temperature 1.2 --dry")
    print("Next step: reread against the original and fix by hand what changed (HIP\n"
          "sometimes changes a detail, like «they clean» into «they wash the dishes»);\n"
          "then scripts/join.py --original " + args.original + ".")
    return 3 if (untouched or copied) else 0


def write_candidates(args, i, p, wanted, concepts, lead=None, bullet=None):
    """Up to N acceptable versions of paragraph i, each in its own file. A detector can
    score two samples of the same paragraph 0% and 100%; measuring several and keeping the
    one that passes adds no chat fingerprint, since the same base model wrote them all."""
    folder = args.output + ".candidates"
    os.makedirs(folder, exist_ok=True)
    found, tries = 0, 0
    while found < args.candidates and tries < args.candidates * args.tries:
        tries += 1
        if bullet is not None:
            lead = bullet_lead(p, bullet + tries - 1)
        r = restore_percent_signs(p, rewrite_paragraph(p, args.threads, args.temperature, lead))
        problem, share = acceptable(p, r, wanted, concepts, args.max_copied,
                                    strict_short=args.vary_bullets)
        if problem:
            continue
        found += 1
        path = os.path.join(folder, f"p{i:02d}-{found}.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(r + "\n")
        print(f"Paragraph {i}: {path} (copied {share:.0%})", flush=True)
    if found < args.candidates:
        print(f"Paragraph {i}: only {found} acceptable of {tries} tries", flush=True)


def take(original, output, specs):
    """Paragraph N of the output becomes the text of FILE; everything else stays. All the
    N=FILE pairs are checked before writing, so a bad one changes nothing."""
    with open(output, encoding="utf-8") as fh:
        paragraphs = [x.strip() for x in re.split(r"\n\s*\n", fh.read()) if x.strip()]
    adopted = {}
    for spec in specs:
        n, _, path = spec.partition("=")
        if not n.isdigit() or not os.path.isfile(path):
            print(f"ERROR: --take needs N=FILE with an existing FILE: {spec}", file=sys.stderr)
            return 2
        if not 1 <= int(n) <= len(paragraphs):
            print(f"ERROR: {output} has {len(paragraphs)} paragraphs: {spec}", file=sys.stderr)
            return 2
        if int(n) in adopted:
            print(f"ERROR: --take gives paragraph {n} twice", file=sys.stderr)
            return 2
        adopted[int(n)] = path
    for n, path in sorted(adopted.items()):
        with open(path, encoding="utf-8") as fh:
            paragraphs[n - 1] = " ".join(fh.read().split())
    with open(output, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(paragraphs) + "\n")
    for n, path in sorted(adopted.items()):
        print(f"Paragraph {n} of {output} now comes from {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
