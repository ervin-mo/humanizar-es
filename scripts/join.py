#!/usr/bin/env python3
"""Joins the sentences of each paragraph, the way someone writes in one go. No models.
In Spanish and English (it detects the language).

Grammarly recognizes the rhythm of AI text: sentences of even length, each with its
own period. Joining them with «and» / «y» (or with «, but» / «, pero» where it fits)
erases that rhythm without adding a single spelling or punctuation error. Applied
after scripts/rewrite.py, it took two full essays to 0% and 10% on Grammarly
(references/evidence.md). On the original text, without rewrite.py, it is not
enough (57%).

Respects proper nouns: it does not lowercase them if they are in --concepts or if
they appear capitalized mid-sentence in the text.

usage:
  python3 scripts/join.py rewritten.txt -o final.txt --concepts concepts.txt
"""
import argparse
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):  # so a Windows console does not choke on «» or ñ
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

# Per language: words that can be capitalized mid-sentence («San Cristobal de Las
# Casas», «The Hague») but are common words when they start a sentence; the
# connectors used to join; and what is not flagged as a possible proper noun.
LANGUAGES = {
    "es": {
        "common": set("""El La Los Las Lo Un Una Unos Unas De Del Al A En Y O Con Por Para Sin
        Su Sus Mi Mis Este Esta Estos Estas Ese Esa Esos Esas Esto Eso No Si Que""".split()),
        "and": "y", "but": ("Pero",), "contrast": ("Sin embargo, ",),
        "addition": {"Además": "además", "Asimismo": "además", "También": "también"},
        "always_proper": set(),
        "no_warn": set("""Antes Mientras Cuando Aunque Quizá Quizás Hoy Ahora Así Luego
        Entonces Incluso Tampoco Nunca Siempre Todo Toda Todos Todas Cada Otro Otra Más
        Menos Muy Desde Hasta Entre Sobre Tras Ante Según Durante Como Donde""".split()),
        "suffixes": r"(ar|er|ir|mente)$",
        "hints": set("de la que el en y los las del se por un una con para es".split()),
    },
    "en": {
        "common": set("""The A An This That These Those It Its In On At For Of To With By From
        As If When While And Or But Not No Our Their His Her We They He She You What Which
        There Here Some Many Most Each Every Such""".split()),
        "and": "and", "but": ("But", "Yet"), "contrast": ("However, ",),
        "addition": {"Also": "also", "Additionally,": "also", "Moreover,": "also",
                     "Furthermore,": "also"},
        "always_proper": {"I", "I'm", "I've", "I'd", "I'll"},
        "no_warn": set("""Before After Today Now Then Even Still Never Always Every Each
        Other Another More Less Very Since Until Between Over During How Where Why Once
        Instead Rather Despite Although Though Because Nevertheless Ultimately Finally
        Meanwhile Similarly Consequently Therefore Thus Yet So""".split()),
        "suffixes": r"(ly|ing|ed)$",
        "hints": set("the and of to is that in it for with as on are this be".split()),
    },
}
COMMON = LANGUAGES["es"]["common"]  # backward compatibility

# --pauses: sentences that already open with one of these change the idea, so a period
# goes there first; inside a block they are joined with «;» keeping the connector.
OPENERS = {
    "es": ("Sin embargo,", "No obstante,", "Por lo tanto,", "Por tanto,", "Por ello,", "Por eso,",
           "Así,", "Así también,", "Así pues,", "De esta forma,", "De esta manera,", "De este modo,",
           "Es decir,", "Por ejemplo,", "Por otro lado,", "Por otra parte,", "En cambio,",
           "Entonces,", "En primer lugar,", "En segundo lugar,", "En tercer lugar,", "Primero,",
           "Segundo,", "Tercero,", "Finalmente,", "Por último,", "En conclusión,", "Además,",
           "Asimismo,", "También,", "Incluso,", "Por el contrario,", "Con todo,", "Ahora bien,"),
    "en": ("However,", "Therefore,", "Thus,", "So,", "For example,", "For instance,", "In contrast,",
           "On the other hand,", "First,", "Second,", "Third,", "Finally,", "In short,",
           "Moreover,", "Furthermore,", "Also,", "Meanwhile,", "Instead,", "That is,"),
}
ENUMERATORS = {"Primero,", "Segundo,", "Tercero,", "En primer lugar,", "En segundo lugar,",
               "En tercer lugar,", "Finalmente,", "Por último,", "First,", "Second,", "Third,",
               "Finally,"}
# Plain joins inside a block rotate among connectors that never change the meaning.
NEUTRAL = {"es": (" y ", "; ", " y "), "en": (" and ", "; ", " and ")}


def opener(s, lang):
    return next((o for o in OPENERS[lang] if s.startswith(o)), None)


def split_blocks(sentences, pauses, rnd, lang):
    """Cut a paragraph into up to `pauses`+1 blocks of uneven length, cutting first where a
    sentence already opens with a connector. Every block keeps at least two sentences: a
    sentence left alone between two periods is read on its own, and the near-copies of the
    original hid inside a chain come out (measured: 6% in Grammarly, against 0% joined)."""
    n = len(sentences)
    allowed = range(2, n - 1)  # a cut at i leaves sentences[:i] and sentences[i:]
    natural = [i for i in allowed if opener(sentences[i], lang)]
    rnd.shuffle(natural)
    natural.sort(key=lambda i: opener(sentences[i], lang) not in ENUMERATORS)  # «Segundo,» first
    others = list(allowed)
    rnd.shuffle(others)
    cuts = []
    for i in natural + others:
        if len(cuts) == pauses:
            break
        if i not in cuts and all(abs(i - c) >= 2 for c in cuts):
            cuts.append(i)
    return [0] + sorted(cuts)


# «Dr. Smith», «Sr. García», «e.g. Slack»: the period does not close the sentence.
ABBREVIATION = re.compile(r"(?:^|\s)(?:Mr|Mrs|Ms|Dr|Prof|St|Sr|Sra|Srta|Dra|Lic|Ing|vs|etc|"
                          r"approx|e\.g|i\.e|U\.S|p\.ej)\.$", re.I)


def detect_language(text):
    words = re.findall(r"[a-záéíóúñü]+", text.lower())
    counts = {lang: sum(w in c["hints"] for w in words) for lang, c in LANGUAGES.items()}
    return max(counts, key=counts.get)


def proper_nouns(text, concepts=(), lang="es"):
    common = LANGUAGES[lang]["common"]
    mid = set(re.findall(r"(?<=[a-záéíóúñü,;:] )([A-ZÁÉÍÓÚÑ][\w'-]+)", text)) - common
    mid |= LANGUAGES[lang]["always_proper"]
    for _, variants in concepts:
        for v in variants:
            for w in v.rstrip("*").split():
                if w[:1].isupper() and w not in common:
                    mid.add(w)
    return mid


def join_paragraph(paragraph, proper, p=1.0, rnd=None, max_words=400, doubtful=None, lang="es"):
    rnd = rnd or random.Random(7)
    c = LANGUAGES[lang]
    sentences = re.split(r"(?<=\.) (?=[A-ZÁÉÍÓÚÑ¿¡])", paragraph.strip())
    out = [sentences[0]]
    for s in sentences[1:]:
        prev = out[-1]
        w = s.split()[0]
        base = w.strip(",;:")
        if (not prev.endswith(".") or prev.endswith("...") or ABBREVIATION.search(prev)
                or rnd.random() >= p or len(prev.split()) + len(s.split()) > max_words):
            out.append(s)
            continue
        body = prev[:-1]
        contrast = next((x for x in c["contrast"] if s.startswith(x)), None)
        if base in c["but"]:
            out[-1] = body + f", {base.lower()} " + s[len(w) + 1:]
        elif contrast:
            out[-1] = body + ", " + c["but"][0].lower() + " " + s[len(contrast):]
        elif w in c["addition"] or base in c["addition"]:
            out[-1] = (body + f" {c['and']} " + c["addition"].get(w, c["addition"].get(base))
                       + " " + s[len(w) + 1:])
        elif base.lower() == c["and"] and base[:1].isupper():
            out[-1] = body + f" {c['and']} " + s[len(w) + 1:]
        else:
            nxt = s if base in proper else s[0].lower() + s[1:]
            if doubtful is not None and base not in proper:
                doubtful.append(base)
            out[-1] = body + f" {c['and']} " + nxt
    return " ".join(out)


def join_with_pauses(paragraph, proper, pauses, rnd, doubtful=None, lang="es"):
    """2-3 periods per paragraph instead of one: blocks of uneven length; inside each
    block, sentences that open with a connector keep it after «;», the rest rotate
    among «y» and «;»."""
    sentences = re.split(r"(?<=\.) (?=[A-ZÁÉÍÓÚÑ¿¡])", paragraph.strip())
    starts = split_blocks(sentences, pauses, rnd, lang) + [len(sentences)]
    blocks = []
    for a, b in zip(starts, starts[1:]):
        out = sentences[a]
        for s in sentences[a + 1:b]:
            if not out.endswith(".") or out.endswith("...") or ABBREVIATION.search(out):
                out += " " + s
                continue
            w = s.split()[0].strip(",;:")
            o = opener(s, lang)
            if o:
                glue = "; "
            else:
                glue = NEUTRAL[lang][rnd.randrange(len(NEUTRAL[lang]))]
            if w in proper:
                nxt = s
            else:
                nxt = s[0].lower() + s[1:]
                if doubtful is not None and not o:
                    doubtful.append(w)
            out = out[:-1] + glue + nxt
        blocks.append(out)
    return " ".join(blocks)


def join_text(text, concepts=(), p=1.0, seed=7, max_words=400, doubtful=None, lang=None,
              pauses=None):
    """doubtful: if it is a list, it receives the words that were lowercased without
    appearing that way anywhere else in the text (possible proper nouns).
    lang: "es", "en" or None to detect it."""
    lang = lang or detect_language(text)
    c = LANGUAGES[lang]
    rnd = random.Random(seed)
    proper = proper_nouns(text, concepts, lang)
    paragraphs = [x for x in re.split(r"\n\s*\n", text.strip()) if x.strip()]
    lowered = []
    if pauses:
        output = "\n\n".join(join_with_pauses(x, proper, pauses, rnd, lowered, lang)
                             for x in paragraphs) + "\n"
    else:
        output = "\n\n".join(join_paragraph(x, proper, p, rnd, max_words, lowered, lang)
                             for x in paragraphs) + "\n"
    if doubtful is not None:
        words = set(re.findall(r"\w+", text))
        doubtful.extend(sorted({w for w in lowered if w.lower() not in words
                                and w not in c["common"] | c["no_warn"]
                                and not re.search(c["suffixes"], w)}))
    return output


def main():
    ap = argparse.ArgumentParser(description="Joins the sentences of each paragraph with «and».")
    ap.add_argument("input")
    ap.add_argument("-o", "--output", "--salida", dest="output", required=True)
    ap.add_argument("--concepts", "--conceptos", dest="concepts",
                    help="concepts file (its proper nouns are respected)")
    ap.add_argument("--ratio", "--proporcion", dest="ratio", type=float, default=1.0,
                    help="fraction of joins to make (1.0, the measured one; 0.6 gave 66%% on Grammarly)")
    ap.add_argument("--max-words", "--maximo", dest="max_words", type=int, default=400,
                    help="maximum words per joined sentence")
    ap.add_argument("--lang", "--idioma", dest="lang", choices=sorted(LANGUAGES),
                    help="es or en (detected by default)")
    ap.add_argument("--pauses", "--pausas", dest="pauses", type=int,
                    help="leave this many periods per paragraph (2 or 3) in blocks of uneven "
                    "length, instead of joining everything; reads better")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        text = fh.read()
    concepts = check.load_concepts(args.concepts) if args.concepts else []
    doubtful = []
    lang = args.lang or detect_language(text)
    joined = join_text(text, concepts, args.ratio, max_words=args.max_words, doubtful=doubtful,
                       lang=lang, pauses=args.pauses)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(joined)
    count = lambda t: len(re.findall(r"[.!?](?:\s|$)", t))  # noqa: E731
    print(f"Written: {args.output} ({count(text)} sentences -> {count(joined)}, language: {lang})")
    if doubtful:
        print("REVIEW: these were lowercased and do not appear that way in the text; if they "
              f"are proper nouns, add them to --concepts: {', '.join(doubtful)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
