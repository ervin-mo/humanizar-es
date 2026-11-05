#!/usr/bin/env python3
"""Take the body of a .docx to humanize it, and put the result back in the same file.

The recipe works on plain text, but a student's assignment or a client's document is a
.docx with a header, logos, a bibliography. This script moves only the prose:

  extract   reads the .docx and writes the original text (one paragraph per block,
            blank line between them) plus a map of which Word paragraphs each block is.
  build     takes the final text and writes a copy of the .docx with the same formatting,
            replacing only the prose paragraphs. Titles (12 words or fewer), the header
            and everything after --stop (bibliography) stay byte for byte.

Standard library only. The .docx is read as a zip; nothing else is touched.

usage:
  python3 scripts/docx_tools.py extract tarea.docx -o 00-original.txt --map mapa.json \\
          --start "Introducción" --stop "Bibliografía"
  ... rewrite.py, join.py, check.py as usual ...
  python3 scripts/docx_tools.py build tarea.docx --map mapa.json --text 02-final.txt \\
          -o tarea-final.docx

--start / --stop: the first paragraph that starts with that text (case and accents are
ignored). Without --start the body begins at the first paragraph; without --stop it goes
to the end. --merge-short N joins a prose paragraph of fewer than N words with the next
one («En el plano filosófico, las ideas son diversas.» + its paragraph): one short
sentence alone is hard for the model and for the joiner.
"""
import argparse
import html
import json
import re
import sys
import unicodedata
import zipfile

if hasattr(sys.stdout, "reconfigure"):  # so a Windows console does not choke on «» or ñ
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

PARAGRAPH = re.compile(r"<w:p(?=[ >]).*?</w:p>", re.S)
RUN = re.compile(r"<w:r(?=[ >]).*?</w:r>", re.S)
TEXT = re.compile(r"<w:t(?: [^>]*)?>.*?</w:t>", re.S)
TITLE_WORDS = 12  # same threshold as rewrite.is_title: up to this many words is a title


def _plain(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def read_document(path):
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def paragraph_text(p):
    parts = re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>|(<w:tab/>)", p, re.S)
    return " ".join("".join(" " if tab else html.unescape(t) for t, tab in parts).split())


def leading_spaces(p):
    """The indent a paragraph starts with, counted over all its runs (Word often splits
    «   Texto» into a run of spaces and a run of text)."""
    raw = "".join(html.unescape(t) for t in re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", p, re.S))
    return raw[:len(raw) - len(raw.lstrip(" "))]


def is_prose(text):
    return len(text.split()) > TITLE_WORDS


def extract(args):
    xml = read_document(args.docx)
    paras = PARAGRAPH.findall(xml)
    texts = [paragraph_text(p) for p in paras]
    start, stop = 0, len(paras)
    if args.start:
        key = _plain(args.start)
        hits = [i for i, t in enumerate(texts) if _plain(t).startswith(key)]
        if not hits:
            print(f"ERROR: no paragraph starts with --start «{args.start}»", file=sys.stderr)
            return 2
        start = hits[0]
    if args.stop:
        key = _plain(args.stop)
        hits = [i for i, t in enumerate(texts) if i > start and _plain(t).startswith(key)]
        if not hits:
            print(f"ERROR: no paragraph after the start begins with --stop «{args.stop}»",
                  file=sys.stderr)
            return 2
        stop = hits[0]
    body = [i for i in range(start, stop) if texts[i]]
    units, k = [], 0
    while k < len(body):
        group = [body[k]]
        if (args.merge_short and is_prose(texts[body[k]])
                and len(texts[body[k]].split()) < args.merge_short and k + 1 < len(body)
                and is_prose(texts[body[k + 1]])):
            group.append(body[k + 1])
            k += 1
        units.append({"paragraphs": group, "texts": [texts[i] for i in group]})
        k += 1
    blocks = [" ".join(u["texts"]) for u in units]
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(blocks) + "\n")
    with open(args.map, "w", encoding="utf-8") as fh:
        json.dump({"source": args.docx, "units": units}, fh, ensure_ascii=False, indent=1)
    prose = sum(is_prose(b) for b in blocks)
    print(f"Written: {args.output} ({len(blocks)} blocks, {prose} of prose) and {args.map}")
    print(f"Body: Word paragraphs {start}-{stop - 1} of {len(paras)}"
          + (f", from «{texts[start][:40]}»" if texts[start] else ""))
    return 0


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(args):
    with open(args.map, encoding="utf-8") as fh:
        units = json.load(fh)["units"]
    with open(args.text, encoding="utf-8") as fh:
        blocks = [x.strip() for x in re.split(r"\n\s*\n", fh.read()) if x.strip()]
    if len(blocks) != len(units):
        print(f"ERROR: {args.text} has {len(blocks)} blocks and the map {len(units)}. "
              "Titles and paragraphs must stay one block each.", file=sys.stderr)
        return 2
    xml = read_document(args.docx)
    paras = PARAGRAPH.findall(xml)
    out, changed = xml, 0
    for unit, block in zip(units, blocks):
        idx = unit["paragraphs"]
        if not is_prose(" ".join(unit["texts"])):
            continue  # a title stays as it was
        for i, expected in zip(idx, unit["texts"]):
            if i >= len(paras) or paragraph_text(paras[i]) != expected:
                print(f"ERROR: Word paragraph {i} is not the one extract saw; build the map "
                      "again from this same .docx.", file=sys.stderr)
                return 2
        first = paras[idx[0]]
        runs = [r for r in RUN.findall(first) if "<w:t" in r]
        if not runs:
            print(f"ERROR: Word paragraph {idx[0]} has no text run", file=sys.stderr)
            return 2
        keep = runs[0]
        m = TEXT.search(keep)
        new_run = (keep[:m.start()] + '<w:t xml:space="preserve">' + leading_spaces(first)
                   + esc(block) + "</w:t>" + keep[m.end():])
        new_p = first
        for r in runs[1:]:
            new_p = new_p.replace(r, "", 1)
        new_p = new_p.replace(keep, new_run, 1)
        if first not in out:
            print(f"ERROR: could not find paragraph {idx[0]} in the document", file=sys.stderr)
            return 2
        out = out.replace(first, new_p, 1)
        for i in idx[1:]:
            out = out.replace(paras[i], "", 1)  # the merged paragraph's text is in the first
        changed += 1
    with zipfile.ZipFile(args.docx) as zin, zipfile.ZipFile(args.output, "w",
                                                              zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = out.encode("utf-8")
            zout.writestr(item, data)
    print(f"Written: {args.output} ({changed} prose paragraphs replaced; header, titles and "
          "the rest untouched)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Extract the body of a .docx and put the "
                                 "humanized text back.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("docx")
    e.add_argument("-o", "--output", required=True)
    e.add_argument("--map", required=True)
    e.add_argument("--start")
    e.add_argument("--stop")
    e.add_argument("--merge-short", type=int, default=0, dest="merge_short")
    b = sub.add_parser("build")
    b.add_argument("docx")
    b.add_argument("--map", required=True)
    b.add_argument("--text", required=True)
    b.add_argument("-o", "--output", required=True)
    args = ap.parse_args()
    return extract(args) if args.cmd == "extract" else build(args)


if __name__ == "__main__":
    sys.exit(main())
