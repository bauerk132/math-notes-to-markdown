# math-notes-to-markdown

A [Claude Code](https://claude.com/claude-code) skill that turns course notes pasted out of
an LMS into a clean Markdown file you actually want to study from — LaTeX preserved, a
printable HTML copy alongside it, and an index that keeps the folder navigable as modules
pile up.

Built for courseware exports (Acrobatiq, Canvas, Blackboard, WGU, Sophia) but it works on
anything: textbook pages, lecture slides, PDF text, handwritten transcriptions.

## The problem

Paste a page out of courseware and you get math in `\(...\)` delimiters that Obsidian and
GitHub render as literal backslashes, plus the same source link stamped after every single
bullet:

```markdown
- If \(a > 0\), the parabola opens upward, and the vertex \((h, k)\) represents the
  **minimum** point. [courses.acrobatiq](https://courses.acrobatiq.com/en-us/courseware/…)
- If \(a < 0\), the parabola opens downward, and the vertex \((h, k)\) represents the
  **maximum** point. [courses.acrobatiq](https://courses.acrobatiq.com/en-us/courseware/…)
```

Out the other side:

```markdown
---
title: Quadratic Functions
course: MAT201 Precalculus
module: 6
pages: 48-56
topics: [quadratic functions, factoring, vertex form, discriminant]
source: "https://courses.acrobatiq.com/en-us/courseware/…"
created: 2026-09-03
---

- If $a > 0$, the parabola opens upward and the vertex $(h, k)$ is the **minimum** point.
- If $a < 0$, the parabola opens downward and the vertex $(h, k)$ is the **maximum** point.
```

## Install

```bash
git clone https://github.com/bauerk132/math-notes-to-markdown.git
cd math-notes-to-markdown
./install.sh
```

On Windows PowerShell:

```powershell
git clone https://github.com/bauerk132/math-notes-to-markdown.git
cd math-notes-to-markdown
.\install.ps1
```

The installer copies the skill into `~/.claude/skills/`, backs up any previous version,
verifies the files landed, and runs the test suite. Set `CLAUDE_SKILLS_DIR` first if your
skills live somewhere else. To confirm an existing install without touching it, pass
`--check` (bash) or `-Check` (PowerShell).

Prefer to do it by hand? Copy `skills/math-notes-to-markdown/` into `~/.claude/skills/`.
That is the whole install — there is nothing to compile and nothing to configure.

## Use it

Start a new Claude Code session, paste your notes, and say what you want:

> *save this as markdown*
> *clean up module 7 and file it*
> *convert these notes for my Obsidian vault*

Claude reads the course, module number, page range, and topics out of the paste itself, so
there is no form to fill in. Files land in `math-notes/` under your working directory:

```
math-notes/
├── NOTES-INDEX.md                                   every module, newest build wins
├── mat201-precalculus-module-6-quadratic-functions.md
└── mat201-precalculus-module-6-quadratic-functions.html
```

The `.md` is for Obsidian, VS Code, GitHub — anywhere that speaks `$...$`. The `.html` is
for reading and printing: open it in a browser and hit **Print / Save as PDF**.

## Use it without Claude

The converter is a plain CLI with no dependencies beyond the standard library, so it is
useful on its own:

```bash
python ~/.claude/skills/math-notes-to-markdown/scripts/build_notes.py \
  --body notes.md \
  --title "Quadratic Functions" \
  --course "MAT201 Precalculus" \
  --module 6 \
  --pages "48-56" \
  --topics "quadratics, factoring, discriminant" \
  --outdir math-notes
```

| Flag | Effect |
| :--- | :--- |
| `--body` | Markdown to convert. `-` reads stdin. |
| `--title` | Required. Becomes the filename, frontmatter title, and HTML header. |
| `--course` `--module` `--pages` `--topics` `--tags` | Frontmatter and index metadata. |
| `--outdir` | Where notes go. Default `math-notes/`. |
| `--slug` | Override the generated filename. |
| `--source` | Set the source URL when there is no citation to detect. |
| `--keep-links` | Keep repeated citation links inline. |
| `--no-html` / `--no-index` | Skip those artifacts. |

Re-running with the same slug overwrites the files and replaces that index row rather than
duplicating it, so fixing a typo is just a rebuild.

## What gets transformed

- **Math delimiters.** `\(x^2\)` → `$x^2$`, `\[...\]` → `$$...$$`. Multi-line display math
  keeps its indentation, so equations nested under a list item stay in that list item.
  Anything inside backticks or a fenced code block is never touched.
- **Citations.** A URL appearing three or more times is LMS boilerplate: every inline copy
  is removed and the URL is promoted to the `source:` field. Links appearing once or twice
  are left alone, so a reference you meant to keep survives.
- **Structure.** `***` separators normalize to `---`, trailing whitespace goes, YAML
  frontmatter is generated, and wide tables get a horizontal scroll container in the HTML.

Content is never summarized or dropped. These are study notes; a practice problem that
quietly disappears is practice you paid for and won't get back.

## Requirements

Python 3.8+. Nothing else — no pip install, no Node, no build step. The printable HTML
pulls MathJax and marked from a CDN, so equations need a connection to *render*; the `.md`
carries the full LaTeX either way.

## Tests

```bash
python tests/smoke_test.py
```

20 checks covering every transform plus the edge cases that have actually broken: interval
notation like `$[k, \infty)$` colliding with citation stripping, display math nested under
list items, code fences that must stay literal, and index idempotency.

## Layout

```
skills/math-notes-to-markdown/
├── SKILL.md                     workflow and fidelity rules Claude follows
├── references/formatting.md     heading conventions, LaTeX repair for OCR'd material
├── scripts/build_notes.py       the converter
└── assets/note-template.html    printable HTML shell
tests/smoke_test.py
install.sh / install.ps1
```

To change how notes are structured, edit `SKILL.md` and `references/formatting.md` — that
is the part Claude reads. To change the mechanical transforms, edit `build_notes.py` and
run the tests.

## License

MIT — see [LICENSE](LICENSE).
