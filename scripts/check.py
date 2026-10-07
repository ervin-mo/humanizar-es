#!/usr/bin/env python3
"""Checks that a rewrite keeps the content of the original.

Humanizing changes the surface (rhythm, syntax, vocabulary). The content -names,
figures, technical terms, negations- has to survive intact. This script checks it
in two ways:

  1. Concepts: every concept of the original must appear in every variant.
     Concepts come from a file (--concepts) or, if none is given, are extracted
     automatically from the original (proper nouns, figures, terms in
     parentheses or quotes).
  2. Negations: warns if a negative construction of the original ("no
     contradiction", "never", "without") disappears from the variant. It is the
     most dangerous error: it flips the meaning and no proofreader catches it.

Standard library only.

Usage:
  check.py original.txt variant.txt [variant2.txt ...]
  check.py original.txt variant.txt --concepts concepts.txt
  check.py original.txt --list     # show which concepts it extracts

Concepts file format (one per line, # for comments):
  Aristotle | the Stagirite       <- variants separated by |; any one is enough
  principle of non-contradiction
  antinomy                        <- whole word; accepts the plural (antinomies)
  subatomic*                      <- with * it matches by prefix: subatomic, subatomics...
Matching ignores case and accents.

Exit code: 0 if every variant keeps 100% of the concepts, 1 if any loses one,
2 on a usage error.
"""
import argparse
import re
import sys
import unicodedata

if hasattr(sys.stdout, "reconfigure"):  # so a Windows console does not choke on «» or ñ
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

# Spanish and English
NEGATIONS = (r"no|ni|nunca|jamas|tampoco|sin|nadie|nada|ningun|ninguna|ninguno|"
             r"not|never|nor|without|none|nobody|nothing|neither|cannot")

# Capitalized words that are not proper nouns even when they do not open a sentence.
NOT_PROPER = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o", "en",
    "a", "al", "por", "para", "con", "sin", "que", "se", "su", "sus", "lo", "es",
    "este", "esta", "estos", "estas", "ese", "esa", "como", "pero", "si", "no",
    "the", "an", "of", "and", "or", "in", "on", "at", "for", "to", "with", "by", "from",
    "this", "that", "these", "those", "it", "its", "but", "if", "when", "while", "as",
}


def norm(s):
    """Lowercase and without accents, to compare regardless of spelling."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def pattern(term):
    """Whole word (optional plural), flexible spaces. With a trailing *, matches
    by prefix. So "ser" does not match "servicio"."""
    term = norm(term).strip()
    prefix = term.endswith("*")
    parts = [re.escape(p) for p in term.rstrip("*").split()]
    end = "" if prefix else r"(?:e?s)?(?!\w)"
    return re.compile(r"(?<!\w)" + r"\s+".join(parts) + end)


def load_concepts(path):
    concepts = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            variants = [v.strip() for v in line.split("|") if v.strip()]
            concepts.append((variants[0], variants))
    return concepts


def extract_concepts(text):
    """Extracts candidates for untouchable content. It is a heuristic: review the
    list with --list and, for serious work, pass a file with --concepts."""
    found = {}

    def add(t, alternatives=()):
        t = t.strip(" .,;:«»\"'()")
        words = t.split()
        while len(words) > 1 and norm(words[0]) in NOT_PROPER:
            words = words[1:]  # "el noumeno" -> "noumeno"
        t = " ".join(words)
        if len(t) >= 3 and norm(t) not in found:
            found[norm(t)] = [t, *alternatives]

    # 1. proper nouns: capitalized words and their inner joins ("Tomas de Aquino").
    #    The word that opens a sentence is dropped because its capital may be only
    #    positional: a name that ONLY appears at the start of a sentence is not
    #    detected. That is why the automatic list is just a starting point.
    capital = r"[A-ZÁÉÍÓÚÑÜ][\wáéíóúñü]+"
    joiner = r"(?:\s+(?:de|del|la|las|los|y|of|the)\s+|\s+)"
    for m in re.finditer(rf"{capital}(?:{joiner}{capital})*", text):
        start = m.start()
        before = text[:start].rstrip()
        opens_sentence = not before or before[-1] in ".!?¿¡:\n«\"—"
        words = m.group(0).split()
        if opens_sentence:
            words = words[1:]  # the first one is capitalized by position
            while words and norm(words[0]) in NOT_PROPER:
                words = words[1:]
        if words and norm(words[0]) not in NOT_PROPER:
            # "Immanuel Kant" also counts as "Kant" in the variant
            alt = [words[-1]] if len(words) > 1 and words[-1][0].isupper() else []
            add(" ".join(words), alt)

    # 2. figures, percentages and dates
    for m in re.finditer(r"\d+(?:[.,]\d+)*\s*%?", text):
        add(m.group(0))

    # 3. short terms in parentheses or angle quotes
    for m in re.finditer(r"\(([^()]{2,40})\)|«([^«»]{2,40})»", text):
        add(m.group(1) or m.group(2))

    return [(v[0], v) for v in found.values()]


def negations(text):
    """Normalized 'negation + next word' pairs of the text. Quotes and parentheses
    are ignored: 'no «contradiccion»' counts as 'no contradiccion'."""
    clean = re.sub(r"[«»\"“”‘’()\[\]]", " ", norm(text))
    return set(
        f"{a} {b}"
        for a, b in re.findall(rf"(?<!\w)({NEGATIONS})\s+(\w+)", clean)
    )


def short_name(path, width=18):
    base = path.replace("\\", "/").split("/")[-1]
    return base if len(base) <= width else base[: width - 1] + "…"


def main():
    ap = argparse.ArgumentParser(
        description="Checks that a rewrite keeps the content of the original."
    )
    ap.add_argument("original")
    ap.add_argument("variants", nargs="*")
    ap.add_argument("--concepts", "--conceptos", dest="concepts",
                    help="file with one concept per line")
    ap.add_argument("--list", "--listar", dest="list", action="store_true",
                    help="show the concepts and exit")
    args = ap.parse_args()

    try:
        texts = {}
        for f in [args.original] + args.variants:
            with open(f, encoding="utf-8") as fh:
                texts[f] = fh.read()
        concepts = (
            load_concepts(args.concepts)
            if args.concepts
            else extract_concepts(texts[args.original])
        )
    except OSError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    source = "file " + args.concepts if args.concepts else "automatic extraction"
    if args.list or not args.variants:
        print(f"{len(concepts)} concepts ({source}):")
        if not args.concepts:
            print("  Heuristic: it misses names that only appear at the start of a sentence")
            print("  and lowercase concepts. Copy it to a file, complete it and use --concepts.")
        for name, variants in concepts:
            extra = f"   (or: {', '.join(variants[1:])})" if len(variants) > 1 else ""
            print(f"  - {name}{extra}")
        return 0

    if not concepts:
        print("ERROR: no concepts to check. Pass --concepts.", file=sys.stderr)
        return 2

    files = [args.original] + args.variants
    normalized = {f: norm(t) for f, t in texts.items()}
    print(f"Concepts: {len(concepts)} ({source})\n")
    print(f"{'concept':<30} " + " ".join(f"{short_name(f):>18}" for f in files))

    totals = {f: 0 for f in files}
    lost = {f: [] for f in files}
    for name, variants in concepts:
        pats = [pattern(v) for v in variants]
        row = []
        for f in files:
            hit = any(p.search(normalized[f]) for p in pats)
            totals[f] += hit
            if not hit:
                lost[f].append(name)
            row.append("ok" if hit else "LOST")
        print(f"{name[:30]:<30} " + " ".join(f"{v:>18}" for v in row))

    print("\nSUMMARY of fidelity:")
    failed = False
    for f in files:
        n = totals[f]
        pct = 100 * n / len(concepts)
        mark = "" if n == len(concepts) else "   <-- review"
        print(f"  {short_name(f, 30):<30} {n}/{len(concepts)} = {pct:.0f}%{mark}")
        if f != args.original and n < len(concepts):
            failed = True

    if totals[args.original] < len(concepts):
        failed = True
        print(
            "\nERROR: the ORIGINAL does not contain every concept. The list does not match"
            " this text (or a variant is misspelled); fix it."
        )

    neg_original = negations(texts[args.original])
    warnings = []
    for f in args.variants:
        missing = sorted(neg_original - negations(texts[f]))
        if missing:
            warnings.append((f, missing))
    if warnings:
        print("\nNEGATIONS from the original that no longer appear the same (review by hand):")
        print("  Many are legitimate rewordings. Look for the ones that change the meaning,")
        print("  like 'principle of non-contradiction' -> 'principle of contradiction'.")
        for f, missing in warnings:
            print(f"  {short_name(f, 30)}: " + ", ".join(f"«{x}»" for x in missing))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
