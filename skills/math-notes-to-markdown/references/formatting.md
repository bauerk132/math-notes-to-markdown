# Formatting conventions

Read this before drafting the body. It covers the patterns that make notes across many
modules look like one coherent set, plus the edge cases where the automated passes need
help.

## Contents

- [Heading skeleton](#heading-skeleton)
- [Key ideas](#key-ideas)
- [Worked examples](#worked-examples)
- [Practice sets](#practice-sets)
- [Tables](#tables)
- [Repairing broken math](#repairing-broken-math)
- [How the automated passes behave](#how-the-automated-passes-behave)
- [Sources that are not LMS pastes](#sources-that-are-not-lms-pastes)

## Heading skeleton

The document has no H1 — the title lives in frontmatter and the HTML renders it as the
page header. Starting the body with an H1 duplicates it.

- **H2** — one per page or major section of the source.
- **H3** — the subsections the source already uses. Prefer the source's own labels
  (`Overview & Key Concepts`, `Factoring Steps`, `Practice Exercises`) over imposing a
  vocabulary the courseware doesn't use; the person is reading these alongside the real
  thing and matching labels help them find their place.
- **H4** — rare. Only when a section genuinely nests three deep.

Separate H2 sections with `---`. The builder normalizes `***` to `---` and drops stray
rules at the very top and bottom, so either style in the source is fine.

## Key ideas

Definitions and rules are the part students reread most, so they earn tight formatting.
Bold the term being defined, keep one idea per bullet, and let the math carry the meaning
rather than restating it in prose:

```markdown
- If $a > 0$, the parabola opens upward and the vertex $(h, k)$ is the **minimum**.
- If $a < 0$, the parabola opens downward and the vertex $(h, k)$ is the **maximum**.
- The vertical line $x = h$ is the **axis of symmetry**.
```

When the source states a named formula, give it its own display equation — it is what
someone flipping through the file is hunting for:

```markdown
For $ax^2 + bx + c = 0$:

$$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$
```

## Worked examples

An example is a small narrative: the problem, the steps, the result. Keep the steps as
separate display equations rather than collapsing them into one line — the intermediate
steps are the teaching content, and squashing them destroys the value.

```markdown
**Example 2.** Find the vertex of $f(x) = 2x^2 - 8x + 3$.

$$h = -\frac{-8}{2(2)} = \frac{8}{4} = 2$$

$$k = f(2) = 2(2)^2 - 8(2) + 3 = 8 - 16 + 3 = -5$$

Vertex $(2, -5)$; axis of symmetry $x = 2$; minimum value $-5$ since $a = 2 > 0$.
```

If the source shows an example without its steps, don't invent them. Transcribe what is
there. Fabricated intermediate steps are worse than none, because they look authoritative
and may be wrong.

## Practice sets

Number them, keep the answer on the same line behind an arrow, and bold the answer label
so the eye can skip it while working:

```markdown
**1.** Find the GCF of $32x^2 - 8x + 40$ → **Answer:** $8$
**2.** Factor $35x^2 - 42x$ → **Answer:** $7x(5x - 6)$
**3.** Factor $81y^4 - x^4$ completely → **Answer:** $(3y - x)(3y + x)(9y^2 + x^2)$
```

Every problem in the source appears in the output. This is the single most important
fidelity rule in the skill: a dropped problem is invisible to the reader and costs them
practice they paid for.

## Tables

Tables survive as GFM tables. Keep math inside cells inline (`$...$`) — display math in a
table cell breaks the row in both Obsidian and the HTML renderer.

For a point-plotting or evaluation table, keep the middle "work" column. The arithmetic
is the point:

```markdown
| $x$ | $y = x^2 - 5x + 6$ | $y$ | Point |
| :--- | :--- | :--- | :--- |
| $-2$ | $(-2)^2 - 5(-2) + 6 = 4 + 10 + 6$ | $20$ | $(-2, 20)$ |
| $0$ | $(0)^2 - 5(0) + 6$ | $6$ | $(0, 6)$ |
```

Wide tables scroll horizontally in the HTML rather than overflowing the page.

## Repairing broken math

Pasted material — especially from PDFs, OCR, or slide decks — arrives with predictable
damage. Fix these while drafting, since the normalizer only touches delimiters:

| Symptom | Fix |
| :--- | :--- |
| `x2`, `x3` where an exponent is meant | `x^2`, `x^3` |
| `x^2y` when the exponent covers more | `x^{2y}` — brace anything past one character |
| Unicode minus `−`, en-dash `–` inside math | ASCII `-` |
| `sqrt(b^2-4ac)` | `\sqrt{b^2 - 4ac}` |
| `-b +/- sqrt(...)` | `-b \pm \sqrt{...}` |
| `<=`, `>=`, `!=` | `\le`, `\ge`, `\ne` |
| `(-inf, inf)`, `R` for the reals | `(-\infty, \infty)`, `\mathbb{R}` |
| Fractions written `b/2a` | `\frac{b}{2a}` — and check whether the source meant $\frac{b}{2a}$ or $\frac{b}{2}a$ |
| `f(x)= ax2+bx+c` run together | `f(x) = ax^2 + bx + c`, spaced around operators |

Interval and set notation is worth care because it is easy to get subtly wrong: brackets
include endpoints, parentheses exclude, and infinity always takes a parenthesis —
`[k, \infty)`, never `[k, \infty]`.

## How the automated passes behave

Knowing the boundaries keeps you from doing work the script already does, or assuming it
handles something it doesn't.

**Math delimiters.** `\(...\)` becomes `$...$`; `\[...\]` becomes `$$...$$`. Multi-line
display math gets `$$` on its own lines at the original indent, so equations nested under
a list item stay inside that list item. Content already using `$` is left alone. Anything
inside backticks or a fenced code block is never touched.

Inline conversion deliberately does not span newlines — an unbalanced `\(` therefore stays
put rather than swallowing the rest of the document. That is why the `grep` check in the
workflow matters: leftover delimiters mean the source was unbalanced there.

**Citations.** A URL appearing three or more times is treated as LMS boilerplate: every
inline instance is removed, lines consisting of nothing but that citation are deleted, and
the most frequent such URL becomes the `source:` field. Links appearing once or twice are
left in place, so a genuine reference someone wants to keep survives. `--keep-links`
disables the whole pass.

**What is not automatic.** Heading structure, table repair, math correctness, and deciding
what counts as a section. Those are the drafting job.

## Sources that are not LMS pastes

- **Slide decks** — slide titles become H2s. Merge trivially short slides into one section;
  a document with fourteen two-line sections is harder to study from than five real ones.
- **Textbook chapters** — use the book's own section numbering in the H2s (`## 3.2 The
  Discriminant`), and set `--pages` to the printed page range.
- **Handwritten or photographed notes** — transcribe faithfully, then flag in your handoff
  message anything you could not read rather than guessing. A note saying "the third
  example's second line was illegible" is far more useful than a plausible invention.
- **Mixed modules in one paste** — if the paste clearly spans two modules, build two files.
  One file per module keeps the index meaningful.
