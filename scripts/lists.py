#!/usr/bin/env python3
"""Lists pasted as plain text: one bullet per line, no blank line between them.

The other scripts read a paragraph as the text between two blank lines. A list pasted from
a chat or from Word («• Ofrecer…», one per line) has no blank lines, so the whole section
(headings, purpose and every bullet) reached the model as ONE paragraph: it came back as a
block of prose, or lost the bullets. This script puts every line in its own block, takes the
bullet marks out (the model does not need them) and, at the end, puts the marks and the
original line breaks back.

  split    original.txt -o 00-original.txt --map lists.json [--merge]
  restore  02-final.txt --map lists.json -o 03-deliver.txt

`restore` refuses to run (exit 2) if the final text does not have one block per line of the
original: a bullet joined to the next one, or split in two, would put the marks in the
wrong place.

--merge turns the lists into prose instead: each run of bullets becomes one paragraph (a
sentence per bullet) for rewrite.py and join.py --pauses to give rhythm, and an inline
numbered list («Criterios: 1.- A; 2.- B.») becomes one enumeration. Headings stay.

Standard library only.
"""
import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

# «• », «- », «* », «· », «▪ », «– »… at the start of a line (numbers like «1.-» are content)
MARK = re.compile(r"^(\s*(?:[•●◦▪▫·‣⁃∙*]|[-–—](?=\s))\s*)")


def split_text(text):
    """(blocks, map): one block per non-empty line, marks taken out. The map keeps, for
    each block, its mark and how many blank lines followed it in the original."""
    lines = text.splitlines()
    blocks, info = [], []
    for k, line in enumerate(lines):
        if not line.strip():
            if info:
                info[-1]["blank_after"] += 1
            continue
        m = MARK.match(line)
        mark = m.group(1) if m else ""
        blocks.append(line[len(mark):].strip())
        info.append({"mark": mark, "blank_after": 0})
    return blocks, info


# «1.- Participación; 2.- Continuidad; 3.- …» inside one line: an inline numbered list
INLINE_ITEM = re.compile(r"(?:(?<=[:;])|^)\s*\d+(?:\.-|\.|\)|-)\s+")


def flatten_inline_list(line):
    """«Criterios: 1.- A; 2.- B; 3.- C.» → «Criterios: A, B y C.» A numbered list kept inside a
    paragraph of prose reads as a list again; with --merge it becomes one enumeration."""
    if len(INLINE_ITEM.findall(line)) < 2:
        return line
    head, sep, tail = line.partition(":")
    if not sep:
        return line
    end = tail.rstrip()[-1:] if tail.rstrip()[-1:] in ".!?" else ""
    items = [INLINE_ITEM.sub("", x).strip().rstrip(".") for x in tail.rstrip(".!? ").split(";")]
    items = [x[0].lower() + x[1:] if x[:1].isupper() and not x[1:2].isupper() else x
             for x in items if x]
    body = ", ".join(items[:-1]) + " y " + items[-1] if len(items) > 1 else items[0]
    return f"{head}: {body}{end or '.'}"


def merge_lists(blocks, info):
    """Every run of consecutive bullets becomes ONE block of prose (each bullet a sentence).
    A list of one-sentence bullets gives join.py nothing to join, and a list scored 34-85% in
    Grammarly where the same document in prose scored far less. The merged block loses its
    marks: restore writes it as a paragraph."""
    out_b, out_i, k = [], [], 0
    while k < len(blocks):
        if info[k]["mark"].strip():
            run = [k]
            while (k + 1 < len(blocks) and info[k + 1]["mark"].strip()
                   and not info[k]["blank_after"]):
                k += 1
                run.append(k)
            text = " ".join(b if b.rstrip().endswith((".", "!", "?", "…")) else b.rstrip(" ;,") + "."
                            for b in (blocks[j] for j in run))
            out_b.append(text)
            out_i.append({"mark": "", "blank_after": info[k]["blank_after"], "merged": len(run)})
        else:
            out_b.append(flatten_inline_list(blocks[k]))
            out_i.append(info[k])
        k += 1
    return out_b, out_i


def restore_text(blocks, info):
    out = []
    for b, i in zip(blocks, info):
        out.append(i["mark"] + b.strip())
        out.extend([""] * min(i["blank_after"], 1))
    while out and not out[-1]:
        out.pop()
    return "\n".join(out) + "\n"


def bullet_blocks(info):
    """Numbers (1-based) of the blocks that carried a bullet mark."""
    return [n for n, i in enumerate(info, 1) if i["mark"].strip()]


def main():
    ap = argparse.ArgumentParser(description="One block per line for lists; marks back at the end.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("original")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--map", required=True)
    s.add_argument("--merge", action="store_true",
                   help="lists to prose: each run of bullets becomes one paragraph and an inline "
                   "numbered list («1.- A; 2.- B») one enumeration")
    r = sub.add_parser("restore")
    r.add_argument("final")
    r.add_argument("--map", required=True)
    r.add_argument("-o", "--output", required=True)
    args = ap.parse_args()

    if args.cmd == "split":
        with open(args.original, encoding="utf-8") as fh:
            blocks, info = split_text(fh.read())
        if args.merge:
            blocks, info = merge_lists(blocks, info)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(blocks) + "\n")
        with open(args.map, "w", encoding="utf-8") as fh:
            json.dump(info, fh, ensure_ascii=False, indent=1)
        print(f"{len(blocks)} blocks ({len(bullet_blocks(info))} bullets) in {args.output}; "
              f"map in {args.map}")
        return 0

    with open(args.map, encoding="utf-8") as fh:
        info = json.load(fh)
    with open(args.final, encoding="utf-8") as fh:
        blocks = [x.strip() for x in re.split(r"\n\s*\n", fh.read()) if x.strip()]
    if len(blocks) != len(info):
        print(f"ERROR: {args.final} has {len(blocks)} blocks and the original had {len(info)} "
              "lines; the marks would land on the wrong lines. Rejoin with the same blocks.",
              file=sys.stderr)
        return 2
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(restore_text(blocks, info))
    print(f"Written: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
