---
name: math-notes-to-markdown
description: Turn pasted course notes into a clean, downloadable Markdown file with LaTeX math preserved, plus a printable HTML copy and a running index of every module filed so far. Use this whenever someone pastes raw material from courseware or an LMS (Acrobatiq, Canvas, Blackboard, WGU, Sophia), a textbook page, lecture slides, or a PDF and wants it saved, filed, formatted, cleaned up, converted, or "turned into a markdown file I can download." Trigger on phrases like "format these notes", "clean this up and save it", "make this downloadable", "convert my notes to markdown", "put this in my Obsidian vault", "save this module", or a bare paste of chapter/module content with any request to keep it. Also use it for follow-up modules once a notes folder exists, so the index and file naming stay consistent. This files material as reference notes; if the person wants new practice problems generated, a quiz, or to be taught the concepts, that is a different job.
---

# Math notes to Markdown

Someone is handing over course material — usually pasted straight out of an LMS, so it
arrives cluttered with repeated citation links, inconsistent math delimiters, and page
furniture. The job is to file it as a clean study document they own: one `.md` they can
drop in Obsidian or VS Code, one `.html` they can print, and an index that keeps the
folder navigable as modules pile up.

The guiding instinct is **archival, not editorial**. These are their notes for an actual
course. Reorganize and clean freely; do not compress, summarize, or drop content. A
practice problem that vanishes is a problem they will not study.

## Workflow

### 1. Pull the metadata out of the paste

Read the material and identify: course name/code, module or chapter number, page range,
a short descriptive title, and 3–6 topic keywords. Nearly always these are stated in the
content itself ("MAT201 Precalculus: Module 6 – Quadratic Functions", "Page 48").

If something is genuinely absent, infer it and say so in one line when you deliver —
don't stall a filing task with interview questions. Only ask if you cannot tell what
course it belongs to *and* a notes folder already exists with several courses in it.

### 2. Draft the body to a scratch file

Write the structured Markdown body — content only, no YAML frontmatter, no title
heading (the script adds both). Read `references/formatting.md` before your first pass;
it covers the heading skeleton, how to render worked examples and practice sets, and the
edge cases that show up in OCR'd or slide-derived material.

Two things worth knowing up front, because they save real effort:

- **Do not hand-convert math delimiters.** The script rewrites `\(x^2\)` to `$x^2$` and
  `\[...\]` to `$$...$$`, preserving list indentation. Paste the math through as-is.
- **Do not strip the repeated citation links.** The script detects any URL appearing 3+
  times as LMS boilerplate, removes every inline instance, and promotes it to a `source:`
  field in the frontmatter. One-off links you actually want survive untouched.

What *does* need your judgment: heading hierarchy, turning wall-of-text into scannable
structure, fixing genuinely broken math (`x2` that means `x^2`, unbalanced braces,
OCR'd `−` vs `-`), and keeping tables intact.

### 3. Build

```bash
python "<skill-dir>/scripts/build_notes.py" \
  --body /tmp/body.md \
  --title "Quadratic Functions" \
  --course "MAT201 Precalculus" \
  --module 6 \
  --pages "48-56" \
  --topics "quadratics, factoring, vertex form, discriminant" \
  --outdir "math-notes"
```

It prints JSON with the paths it wrote and the source URL it detected.

| Flag | Effect |
| :--- | :--- |
| `--outdir` | Where notes live. Default `math-notes/` under the working directory. If the person names a vault or folder, use it. |
| `--slug` | Override the filename. Default is built from course + module + title. |
| `--keep-links` | Leave repeated citation links inline instead of stripping them. |
| `--no-html` / `--no-index` | Skip those artifacts. |
| `--source` | Set the source URL explicitly when auto-detection has nothing to go on. |

Re-running with the same slug is safe: it overwrites the files and replaces that row in
the index rather than duplicating it. That is the normal way to apply a correction.

### 4. Check, then hand it over

Two fast checks that catch the failures that actually happen:

```bash
grep -nF -e '\(' -e '\[' math-notes/<slug>.md
```

Fixed-string matching (`-F`) rather than a pattern here — escaping backslash-paren for a
regex varies between shells and gets silently wrong. Anything returned is math the
normalizer missed, almost always a stray unbalanced delimiter in the source. Fix it in
the `.md` directly.

Then confirm nothing was lost: count the practice problems and worked examples in the
source paste, and confirm the same number survived. Under-transcription is the one error
mode a reader cannot detect on their own.

Finally, send both files with `SendUserFile` (`status: "normal"`, `display: "attach"`) so
they can download them, and say in one line where they landed, what the HTML is for, and
any assumption you made about the metadata.

## Structure

The body follows the source's own divisions — that is what makes the notes usable
alongside the courseware. Default skeleton:

```markdown
## Page 48 — Quadratic Functions & Domain/Range

### Key ideas
...

### Worked examples
...

### Practice
...

---

## Page 49 — Factoring by GCF
```

Keep page numbers in the H2 when the source has them; cross-referencing back to the
courseware is the main reason a student keeps page numbers at all. When the source has no
page structure (slides, a textbook chapter), use topic names alone.

Practice problems keep their answers by default — they are notes, not a test. Format them
so the answer is visually separable, which lets the person cover the right-hand side and
self-test:

```markdown
**1.** Factor $35x^2 - 42x$ → **Answer:** $7x(5x - 6)$
```

If they ask for a self-quiz version, move answers to an `### Answers` subsection at the
end of each section rather than hiding them in collapsible blocks — collapsed math
renders unreliably.

## Where files go

Default to `math-notes/` in the working directory, and keep using whatever folder already
holds their notes once one exists — consistency across modules is most of the value here.
If they mention an Obsidian vault path, that is the folder.

Each build produces `<slug>.md`, `<slug>.html`, and updates `NOTES-INDEX.md`.

## Reference

- `references/formatting.md` — heading conventions, worked-example and table patterns,
  LaTeX repair for OCR'd material, and how the citation and math normalizers behave in
  edge cases. Read it before the first drafting pass.
- `scripts/build_notes.py` — the builder. Pure standard library.
- `assets/note-template.html` — the printable HTML shell (MathJax + marked from CDN).
  Equations need an internet connection to render; the `.md` always has the full LaTeX.
