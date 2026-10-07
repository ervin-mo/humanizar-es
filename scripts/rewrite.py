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


def build_prompt(paragraph, lead_words=2):
    """The format HIP was trained on, plus the first words of the paragraph so the
    model keeps writing in the language of the original."""
    lead = " ".join(paragraph.split()[:lead_words])
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


def rewrite_paragraph(paragraph, threads=4, temperature=1.0):
    prompt, lead = build_prompt(paragraph)
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
           "--temp", str(temperature), "--top-p", "0.95",
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


COPY_RUN = 8  # words in a row that count as copied, not as a shared phrase or a name


def copied_share(original, rewritten, run=COPY_RUN):
    """Share of the rewritten words that sit in runs of `run`+ words copied from the
    original. Calibrated on four essays: HIP's real rewrites copy 0.12-0.45; a paragraph
    it left half untouched, 0.80."""
    a = re.findall(r"\w+", original.lower())
    b = re.findall(r"\w+", rewritten.lower())
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(m.size for m in sm.get_matching_blocks() if m.size >= run) / max(1, len(b))


def is_title(p):
    return len(p.split()) <= 12 and not p.rstrip().endswith((".", "!", "?", "…", ":"))


def main():
    ap = argparse.ArgumentParser(description="Rewrite with a local base model (HIP), paragraph by paragraph.")
    ap.add_argument("original")
    ap.add_argument("-o", "--output", "--salida", dest="output", required=True)
    ap.add_argument("--concepts", "--conceptos", dest="concepts",
                    help="file of concepts that must not be lost")
    ap.add_argument("--tries", "--intentos", dest="tries", type=int, default=6,
                    help="tries per paragraph (6); only a paragraph that fails uses more than one")
    ap.add_argument("--max-copied", dest="max_copied", type=float, default=0.6,
                    help="retry a try that copies more than this share of the original (0.6)")
    ap.add_argument("--threads", "--hilos", dest="threads", type=int, default=4,
                    help="CPU threads (4)")
    ap.add_argument("--only", help="redo only these paragraphs (e.g. 7,11) of an existing output, "
                    "from the original, keeping the others and their hand fixes")
    args = ap.parse_args()

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
    for i, p in enumerate(paragraphs, 1):
        if kept is not None and i not in only:
            output.append(kept[i - 1])
            continue
        if is_title(p):
            output.append(p)
            continue
        wanted = concepts_in(p, concepts)
        chosen, mostly_copied, lost = None, [], collections.Counter()
        for n in range(1, args.tries + 1):
            r = restore_percent_signs(p, rewrite_paragraph(p, args.threads))
            if len(r.split()) < 0.6 * len(p.split()) or len(r.split()) > 1.6 * len(p.split()) + 10:
                lost["(truncated or too long)"] += 1
                continue
            missing = wanted - concepts_in(r, concepts)
            if missing:
                lost.update(missing)
                continue
            share = copied_share(p, r)
            if share > args.max_copied:
                mostly_copied.append((share, r))
                continue
            chosen = r
            break
        if chosen is None and mostly_copied:
            share, chosen = min(mostly_copied, key=lambda c: c[0])
            copied.append(f"{i} ({share:.0%})")
        if chosen is None:
            untouched.append(f"{i} (" + ", ".join(c for c, _ in lost.most_common(2)) + ")")
            chosen = p
        output.append(chosen)
        with open(args.output, "w", encoding="utf-8") as fh:  # saves after every paragraph
            fh.write("\n\n".join(output + (kept or paragraphs)[i:]) + "\n")
        status = "unchanged" if chosen == p else f"done, try {n}" if n > 1 else "done"
        print(f"Paragraph {i} of {len(paragraphs)}: {status} ({time.time() - t0:.0f} s)", flush=True)

    print(f"\nWritten: {args.output}")
    if untouched:
        print("WARNING: kept as the original, the concept they kept losing in brackets: "
              + "; ".join(untouched) + ". Check the spelling of that concept in the concepts file.")
    if copied:
        print("WARNING: every try copied long stretches of the original; the least copied one "
              "was kept: " + "; ".join(copied) + ". Redo them with --only and more --tries.")
    print("Next step: reread against the original and fix by hand what changed (HIP\n"
          "sometimes changes a detail, like «they clean» into «they wash the dishes»);\n"
          "then scripts/join.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
