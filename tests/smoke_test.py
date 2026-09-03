#!/usr/bin/env python3
"""
Smoke test for build_notes.py. Run it after installing, or before sharing a change:

    python tests/smoke_test.py

It builds a fixture that packs in every transform the script performs plus the
edge cases that have actually broken before, then asserts on the output. No
dependencies, no network, writes only to a temp directory.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUILDER = REPO / "skills" / "math-notes-to-markdown" / "scripts" / "build_notes.py"

CITE = "https://courses.example.edu/precalc/module6"
ONE_OFF = "https://en.wikipedia.org/wiki/Quadratic_formula"

FIXTURE = r"""## Page 48 — Domain and Range

Written as \(y = ax^2 + bx + c\), the graph is a parabola. [source](CITE)

- If \(a > 0\) (opens up): range is \([k, \infty)\), or \(y \ge k\). [source](CITE)
- If \(a < 0\) (opens down): range is \((-\infty, k]\), or \(y \le k\). [source](CITE)
- Interval \([7, 12]\) includes both endpoints. [source](CITE)

See also the [full derivation](ONE_OFF) for background.

***

## Page 55 — The Quadratic Formula

\[x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}\]

Multi-line display math nested under a list item:

- Vertex of \(f(x) = 2x^2 - 8x + 3\):
  \[h = -\frac{-8}{2(2)} = 2
  k = f(2) = -5\]

A fenced block must survive untouched:

```latex
\(this stays literal\) and \[so does this\]
```

| Discriminant | Roots |
| :--- | :--- |
| \(b^2 - 4ac > 0\) | Two real |
| \(b^2 - 4ac < 0\) | Two complex |
""".replace("CITE", CITE).replace("ONE_OFF", ONE_OFF)

CHECKS = []


def check(label, condition, detail=""):
    CHECKS.append((label, bool(condition), detail))


def main():
    if not BUILDER.exists():
        print("FAIL: builder not found at {}".format(BUILDER))
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        body = tmp / "body.md"
        body.write_text(FIXTURE, encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, str(BUILDER),
             "--body", str(body),
             "--title", "Quadratic Functions",
             "--course", "MAT201 Precalculus",
             "--module", "6",
             "--pages", "48-56",
             "--topics", "quadratics, discriminant",
             "--outdir", str(tmp / "out"),
             "--slug", "test-notes"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print("FAIL: builder exited {}\n{}".format(proc.returncode, proc.stderr))
            return 1

        result = json.loads(proc.stdout)
        md = Path(result["markdown"]).read_text(encoding="utf-8")
        html = Path(result["html"]).read_text(encoding="utf-8")
        index = Path(result["index"]).read_text(encoding="utf-8")

        # --- delimiters -------------------------------------------------
        outside_fence = md.split("```latex")[0] + md.split("```")[-1]
        check("inline math converted to $..$", "$y = ax^2 + bx + c$" in md)
        check("display math converted to $$..$$", "$$x = \\frac{-b \\pm" in md)
        check("no LaTeX delimiters left outside code",
              "\\(" not in outside_fence and "\\[" not in outside_fence)
        check("fenced code left literal",
              "\\(this stays literal\\) and \\[so does this\\]" in md)

        # --- the interval-notation regression ---------------------------
        # "[k, \infty)" opens a bracket; if link-stripping lets "[" into link
        # text it pairs with the "]" of the citation and eats the line.
        check("interval [k, inf) line intact", "range is $[k, \\infty)$, or $y \\ge k$." in md)
        check("interval (-inf, k] line intact", "range is $(-\\infty, k]$, or $y \\le k$." in md)
        check("bracketed interval [7, 12] intact", "$[7, 12]$ includes both endpoints." in md)

        # --- citations --------------------------------------------------
        check("repeated citation stripped from body", CITE not in md.split("---\n\n", 1)[-1])
        check("citation promoted to frontmatter source", "source: " in md and CITE in md)
        check("source reported by builder", result["source_detected"] == CITE)
        check("one-off link preserved", "[full derivation]({})".format(ONE_OFF) in md)

        # --- structure --------------------------------------------------
        check("frontmatter present", md.startswith("---\ntitle: Quadratic Functions"))
        check("no duplicate H1", "\n# " not in md)
        check("*** normalized to ---", "***" not in md)
        check("table preserved", "| Discriminant | Roots |" in md)
        check("nested display math kept in list item", "\n  $$\n" in md)

        # --- html + index -----------------------------------------------
        check("html has no unreplaced placeholders",
              "__PAYLOAD__" not in html and "__TITLE__" not in html)
        check("html carries a payload", 'PAYLOAD = "ey' in html or "PAYLOAD = \"" in html)
        check("index lists the note", "test-notes.md" in index)

        # --- idempotency ------------------------------------------------
        subprocess.run(
            [sys.executable, str(BUILDER), "--body", str(body), "--title", "Quadratic Functions",
             "--module", "6", "--outdir", str(tmp / "out"), "--slug", "test-notes"],
            capture_output=True, text=True,
        )
        index2 = Path(result["index"]).read_text(encoding="utf-8")
        check("rebuild does not duplicate index row", index2.count("test-notes.md") == 1)

    failed = [c for c in CHECKS if not c[1]]
    for label, ok, detail in CHECKS:
        print("  {} {}{}".format("PASS" if ok else "FAIL", label, (" - " + detail) if detail and not ok else ""))
    print("\n{}/{} checks passed".format(len(CHECKS) - len(failed), len(CHECKS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
