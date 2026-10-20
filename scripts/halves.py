#!/usr/bin/env python3
"""Splits the final text into halves to measure, each with a check phrase. No models.

Two measurements went wrong on a test essay, and both read as a real score:
- the user pasted the ORIGINAL instead of the final version (53%, read as «it failed»);
- the text reached the clipboard with its accents broken («a√±os»), because `pbcopy`
  without a UTF-8 locale reads the file as MacRoman (0%, read as «it passed»).

This script cuts at a paragraph boundary near the middle (Grammarly's free scan reads
1,400 words), and for each half prints a check phrase that appears only in the version,
never in the original: if the detector shows that phrase, the right text was pasted.
With --copy N it puts half N on the clipboard in UTF-8 and reads it back to verify.

usage:
  python3 scripts/halves.py 02-final.txt --original 00-original.txt
  python3 scripts/halves.py 02-final.txt --original 00-original.txt --copy 1
"""
import argparse
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):  # so a Windows console does not choke on «» or ñ
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

UTF8 = dict(os.environ, LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8")


def split_halves(text, max_words=1400):
    """Paragraphs split near the word midpoint; one half if the text fits in max_words."""
    paragraphs = [x.strip() for x in re.split(r"\n\s*\n", text.strip()) if x.strip()]
    words = [len(p.split()) for p in paragraphs]
    if sum(words) <= max_words or len(paragraphs) < 2:
        return ["\n\n".join(paragraphs) + "\n"]
    total = sum(words)
    before = [sum(words[:i]) for i in range(len(paragraphs) + 1)]  # words before paragraph i
    heading = lambda p: len(p.split()) <= 12 and not p.endswith((".", "!", "?"))  # noqa: E731
    # cut before the heading nearest the middle, if one is within 15% of it, so a section
    # is not split in two; otherwise at the paragraph nearest the middle
    cuts = [i for i in range(1, len(paragraphs)) if heading(paragraphs[i])
            and abs(before[i] - total / 2) <= 0.15 * total]
    cuts = cuts or range(1, len(paragraphs))
    cut = min(cuts, key=lambda i: abs(before[i] - total / 2))
    while cut > 1 and heading(paragraphs[cut - 1]):  # a heading never closes a half
        cut -= 1
    return ["\n\n".join(paragraphs[:cut]) + "\n", "\n\n".join(paragraphs[cut:]) + "\n"]


def check_phrase(half, original, size=7):
    """The first run of `size` words of the half whose opening and closing four words are
    both missing from the original: «Al llegar a los 61 años de» is new only in its last
    word, and someone looking at the original would believe they see it."""
    norm = lambda s: " ".join(re.findall(r"\w+", s.lower()))  # noqa: E731
    have = norm(original)
    for p in re.split(r"\n\s*\n", half):
        words = p.split()
        if len(words) <= 12 or "\n" in p.strip():  # headings and cover pages are never rewritten
            continue
        for i in range(0, len(words) - size + 1):
            piece = words[i:i + size]
            if norm(" ".join(piece[:4])) not in have and norm(" ".join(piece[-4:])) not in have:
                return " ".join(piece)
    return None


def copy(text):
    """Clipboard in UTF-8, read back. Returns None if it worked, or the reason."""
    for put, get in ((["pbcopy"], ["pbpaste"]),
                     (["wl-copy"], ["wl-paste", "-n"]),
                     (["xclip", "-selection", "clipboard"], ["xclip", "-selection", "clipboard", "-o"]),
                     (["clip"], None)):
        try:
            subprocess.run(put, input=text.encode("utf-8"), env=UTF8, check=True)
        except (OSError, subprocess.CalledProcessError):
            continue
        if get is None:
            return None  # Windows clip.exe has no paste to read back
        back = subprocess.run(get, capture_output=True, env=UTF8).stdout.decode("utf-8", "replace")
        if back.strip() != text.strip():
            return "the clipboard does not match the file (accents broken?)"
        return None
    return "no clipboard tool found"


def main():
    ap = argparse.ArgumentParser(description="Splits the final text into halves to measure.")
    ap.add_argument("final")
    ap.add_argument("--original", required=True, help="the original, to pick check phrases")
    ap.add_argument("-o", "--prefix", help="output prefix (default: the final's name)")
    ap.add_argument("--max-words", type=int, default=1400,
                    help="words the detector reads at once (1400, Grammarly's free scan)")
    ap.add_argument("--copy", type=int, metavar="N", help="put half N on the clipboard")
    args = ap.parse_args()

    with open(args.final, encoding="utf-8") as fh:
        final = fh.read()
    with open(args.original, encoding="utf-8") as fh:
        original = fh.read()
    prefix = args.prefix or os.path.splitext(args.final)[0]
    halves = split_halves(final, args.max_words)
    for n, half in enumerate(halves, 1):
        path = f"{prefix}-MEASURE-{n}.txt"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(half)
        phrase = check_phrase(half, original)
        print(f"Half {n}: {path} ({len(half.split())} words)")
        if phrase:
            print(f"  check: the detector must show «{phrase}»")
        else:
            print("  WARNING: every stretch of this half is in the original: is it the final?")
    if args.copy:
        if not 1 <= args.copy <= len(halves):
            print(f"ERROR: there are {len(halves)} halves", file=sys.stderr)
            return 2
        problem = copy(halves[args.copy - 1])
        if problem:
            print(f"ERROR: {problem}; open {prefix}-MEASURE-{args.copy}.txt and copy it by hand",
                  file=sys.stderr)
            return 2
        print(f"Half {args.copy} is on the clipboard (checked in UTF-8).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
