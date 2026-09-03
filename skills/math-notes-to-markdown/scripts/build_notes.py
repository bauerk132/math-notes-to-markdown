#!/usr/bin/env python3
"""
build_notes.py - turn a drafted Markdown body into filed, downloadable study notes.

Does the mechanical work so the model can spend its effort on structuring content:
  1. normalizes LaTeX delimiters  \\(..\\) -> $..$   and  \\[..\\] -> $$..$$
  2. strips repeated boilerplate citation links, keeping the URL as a `source:` field
  3. writes <slug>.md with YAML frontmatter
  4. renders a printable <slug>.html (MathJax, no Python dependencies)
  5. keeps NOTES-INDEX.md up to date, idempotently

Everything is safe to re-run: rebuilding the same slug overwrites cleanly and
replaces (not duplicates) its index row.
"""

import argparse
import base64
import datetime
import json
import re
import sys
from collections import Counter
from html import escape as html_escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "note-template.html"

# --------------------------------------------------------------------------
# code protection: never rewrite math or links inside code spans/fences
# --------------------------------------------------------------------------

CODE_RE = re.compile(r"(```.*?```|~~~.*?~~~|`[^`\n]+`)", re.DOTALL)


def protect_code(text):
    stash = []

    def sub(m):
        stash.append(m.group(0))
        return "\x00CODE{}\x00".format(len(stash) - 1)

    return CODE_RE.sub(sub, text), stash


def restore_code(text, stash):
    for i, snippet in enumerate(stash):
        text = text.replace("\x00CODE{}\x00".format(i), snippet)
    return text


# --------------------------------------------------------------------------
# LaTeX delimiter normalization
# --------------------------------------------------------------------------

DISPLAY_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
INLINE_RE = re.compile(r"\\\((.+?)\\\)")  # not DOTALL on purpose: inline math is one line


def convert_display_math(text):
    """Turn display math into $$..$$, keeping list indentation intact."""
    out, pos = [], 0
    for m in DISPLAY_RE.finditer(text):
        inner = m.group(1).strip()
        line_start = text.rfind("\n", 0, m.start()) + 1
        prefix = text[line_start:m.start()]
        indent = prefix if prefix.strip() == "" else ""
        out.append(text[pos:m.start()])
        if "\n" in inner:
            body = "\n".join(indent + ln.strip() for ln in inner.split("\n") if ln.strip())
            out.append("$$\n" + body + "\n" + indent + "$$")
        else:
            out.append("$$" + inner + "$$")
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def normalize_math(text):
    text, stash = protect_code(text)
    text = convert_display_math(text)
    text = INLINE_RE.sub(lambda m: "$" + m.group(1).strip() + "$", text)
    return restore_code(text, stash)


# --------------------------------------------------------------------------
# citation stripping
# --------------------------------------------------------------------------

# Link text excludes brackets on purpose. Math notes are full of interval notation like
# $[k, \infty)$, and allowing "[" inside the label lets an interval opened mid-sentence
# pair with the "]" of a citation further along, deleting everything between them.
LINK_RE = re.compile(r"[ \t]*\[([^\[\]\n]{1,150})\]\((https?://[^\s)]+)\)")


def strip_boilerplate_links(text, min_repeats=3, keep=False):
    """Remove citation links that repeat throughout the document.

    A link counts as boilerplate when the same URL shows up min_repeats+ times -
    that is the signature of an LMS export stamping its source after every bullet.
    Genuinely useful one-off links appear once or twice and survive untouched.
    """
    text, stash = protect_code(text)
    counts = Counter(m.group(2) for m in LINK_RE.finditer(text))
    boiler = set(u for u, c in counts.items() if c >= min_repeats)
    source = None
    if counts:
        url, n = counts.most_common(1)[0]
        if n >= min_repeats:
            source = url

    if keep or not boiler:
        return restore_code(text, stash), source

    # drop lines that are nothing but a citation
    kept = []
    for line in text.split("\n"):
        m = LINK_RE.fullmatch(line)
        if m and m.group(2) in boiler:
            continue
        kept.append(line)
    text = "\n".join(kept)

    # drop trailing citations from content lines
    text = LINK_RE.sub(lambda m: "" if m.group(2) in boiler else m.group(0), text)

    # tidy the wreckage
    text = re.sub(r"[ \t]+\|", " |", text)
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return restore_code(text, stash), source


def normalize_rules(text):
    """Page separators to a single style, with no stray rule directly under frontmatter."""
    text, stash = protect_code(text)
    text = re.sub(r"^[ \t]*\*\*\*[ \t]*$", "---", text, flags=re.M)
    text = re.sub(r"\A(\s*---\s*\n)+", "", text)
    text = re.sub(r"(\n---\s*)+\Z", "\n", text)
    return restore_code(text, stash), None


# --------------------------------------------------------------------------
# frontmatter + slugs
# --------------------------------------------------------------------------

def slugify(value, maxlen=70):
    value = re.sub(r"[^\w\s-]", "", value or "", flags=re.UNICODE).strip().lower()
    value = re.sub(r"[\s_-]+", "-", value)
    return value[:maxlen].strip("-") or "notes"


def yaml_scalar(value):
    value = str(value)
    if re.search(r"[:#\[\]{}&*!|>'\"%@`]|^\s|\s$", value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def yaml_list(values):
    return "[" + ", ".join(yaml_scalar(v) for v in values) + "]"


def build_frontmatter(meta):
    lines = ["---"]
    for key in ("title", "course", "module", "pages"):
        if meta.get(key) not in (None, "", []):
            lines.append("{}: {}".format(key, yaml_scalar(meta[key])))
    for key in ("topics", "tags"):
        if meta.get(key):
            lines.append("{}: {}".format(key, yaml_list(meta[key])))
    if meta.get("source"):
        lines.append("source: {}".format(yaml_scalar(meta["source"])))
    lines.append("created: {}".format(meta["created"]))
    lines.append("---")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# printable HTML
# --------------------------------------------------------------------------

MATH_SPAN_RE = re.compile(r"(\$\$.+?\$\$|\$[^$\n]+?\$)", re.DOTALL)


def render_html(markdown_body, meta, template_path=TEMPLATE):
    """Pull math into placeholders so the client-side Markdown parser cannot mangle
    underscores and asterisks inside equations, then hand both halves to the template
    as one base64 payload (immune to quoting and stray </script> issues)."""
    protected, stash = protect_code(markdown_body)
    math = []

    def grab(m):
        math.append(m.group(0))
        return "MATHPLACEHOLDER{}ENDMATH".format(len(math) - 1)

    protected = MATH_SPAN_RE.sub(grab, protected)
    protected = restore_code(protected, stash)

    payload = {"md": protected, "math": math, "meta": meta}
    blob = base64.b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    html = template_path.read_text(encoding="utf-8")
    title = html_escape(meta.get("title", "Notes"), quote=True)
    return html.replace("__TITLE__", title).replace("__PAYLOAD__", blob)


# --------------------------------------------------------------------------
# index
# --------------------------------------------------------------------------

INDEX_START = "<!-- notes-index:start -->"
INDEX_END = "<!-- notes-index:end -->"
INDEX_HEADER = (
    "| Module | Title | Topics | Files | Added |\n"
    "| ---: | :--- | :--- | :--- | :--- |"
)


def module_sort_key(row):
    m = re.search(r"\d+", row.get("module", "") or "")
    return (0, int(m.group(0))) if m else (1, 0)


def update_index(outdir, entry):
    path = outdir / "NOTES-INDEX.md"
    rows = {}
    if path.exists():
        body = path.read_text(encoding="utf-8")
        block = body.split(INDEX_START)[-1].split(INDEX_END)[0] if INDEX_START in body else ""
        for line in block.strip().split("\n"):
            if not line.startswith("|") or set(line) <= set("|-: "):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 5 or cells[0].lower() == "module":
                continue
            link = re.search(r"\(([^)]+\.md)\)", cells[1])
            if not link:
                continue
            rows[link.group(1)] = {
                "module": cells[0],
                "title_cell": cells[1],
                "topics": cells[2],
                "files": cells[3],
                "added": cells[4],
            }

    md_name = entry["md_name"]
    rows[md_name] = {
        "module": entry.get("module") or "-",
        "title_cell": "[{}]({})".format(entry["title"], md_name),
        "topics": ", ".join(entry.get("topics", [])) or "-",
        "files": "[html]({})".format(entry["html_name"]) if entry.get("html_name") else "-",
        "added": entry["created"],
    }

    ordered = sorted(rows.values(), key=lambda r: (module_sort_key(r), r["title_cell"]))
    table = "\n".join(
        "| {module} | {title_cell} | {topics} | {files} | {added} |".format(**r)
        for r in ordered
    )
    content = (
        "# Notes index\n\n"
        "{} set{} of notes in this folder.\n\n".format(len(ordered), "s" if len(ordered) != 1 else "")
        + "{}\n{}\n{}\n{}\n".format(INDEX_START, INDEX_HEADER, table, INDEX_END)
    )
    path.write_text(content, encoding="utf-8")
    return path


# --------------------------------------------------------------------------

def csv_list(value):
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--body", required=True, help="path to the drafted Markdown body, or - for stdin")
    p.add_argument("--title", required=True)
    p.add_argument("--course", default="")
    p.add_argument("--module", default="")
    p.add_argument("--pages", default="")
    p.add_argument("--topics", default="", help="comma separated")
    p.add_argument("--tags", default="math,notes", help="comma separated")
    p.add_argument("--source", default="", help="override the auto-detected source URL")
    p.add_argument("--outdir", default="math-notes")
    p.add_argument("--slug", default="")
    p.add_argument("--keep-links", action="store_true", help="keep repeated citation links inline")
    p.add_argument("--no-html", action="store_true")
    p.add_argument("--no-index", action="store_true")
    args = p.parse_args()

    raw = sys.stdin.read() if args.body == "-" else Path(args.body).read_text(encoding="utf-8")

    # strip a frontmatter block if the draft already carried one; we rebuild it
    raw = re.sub(r"\A---\n.*?\n---\n", "", raw, flags=re.DOTALL)

    body = normalize_math(raw)
    body, detected = strip_boilerplate_links(body, keep=args.keep_links)
    body, _ = normalize_rules(body)
    body = body.strip() + "\n"

    created = datetime.date.today().isoformat()
    meta = {
        "title": args.title,
        "course": args.course,
        "module": args.module,
        "pages": args.pages,
        "topics": csv_list(args.topics),
        "tags": csv_list(args.tags),
        "source": args.source or detected or "",
        "created": created,
    }

    slug = args.slug or slugify(
        " ".join(
            x for x in [args.course, "module {}".format(args.module) if args.module else "", args.title] if x
        )
    )
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    md_path = outdir / (slug + ".md")
    md_path.write_text(build_frontmatter(meta) + "\n\n" + body, encoding="utf-8")

    html_path = None
    if not args.no_html:
        if TEMPLATE.exists():
            html_path = outdir / (slug + ".html")
            html_path.write_text(render_html(body, meta), encoding="utf-8")
        else:
            print("warning: template missing at {}; skipped HTML".format(TEMPLATE), file=sys.stderr)

    index_path = None
    if not args.no_index:
        index_path = update_index(outdir, {
            "md_name": md_path.name,
            "html_name": html_path.name if html_path else "",
            "title": args.title,
            "module": args.module,
            "topics": meta["topics"],
            "created": created,
        })

    print(json.dumps({
        "markdown": str(md_path),
        "html": str(html_path) if html_path else None,
        "index": str(index_path) if index_path else None,
        "source_detected": meta["source"] or None,
        "words": len(body.split()),
    }, indent=2))


if __name__ == "__main__":
    main()
