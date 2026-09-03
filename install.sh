#!/usr/bin/env bash
# Install the math-notes-to-markdown skill for Claude Code.
# Usage:  ./install.sh          install or update
#         ./install.sh --check  verify an existing install without changing anything
set -euo pipefail

SKILL="math-notes-to-markdown"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$REPO_DIR/skills/$SKILL"
TEST="$REPO_DIR/tests/smoke_test.py"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DEST="$SKILLS_DIR/$SKILL"

say()  { printf '%s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }

# --- python ------------------------------------------------------------
PY=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
      PY="$candidate"; break
    fi
  fi
done
[ -n "$PY" ] || die "Python 3.8+ is required and was not found on PATH."
ok "Python found: $($PY --version 2>&1)"

# --- check mode --------------------------------------------------------
if [ "${1:-}" = "--check" ]; then
  [ -d "$DEST" ] || die "Not installed. Run ./install.sh"
  ok "Installed at $DEST"
  "$PY" "$TEST" >/dev/null 2>&1 \
    && ok "Smoke test passed" || warn "Smoke test not run from this path; try: $PY tests/smoke_test.py"
  exit 0
fi

[ -d "$SRC" ] || die "Source skill folder missing at $SRC"

# --- install -----------------------------------------------------------
mkdir -p "$SKILLS_DIR"

if [ -d "$DEST" ]; then
  BACKUP="$DEST.backup.$(date +%Y%m%d%H%M%S)"
  mv "$DEST" "$BACKUP"
  warn "Existing install moved to $(basename "$BACKUP")"
fi

cp -R "$SRC" "$DEST"
ok "Installed to $DEST"

# --- verify ------------------------------------------------------------
for f in SKILL.md scripts/build_notes.py assets/note-template.html references/formatting.md; do
  [ -f "$DEST/$f" ] || die "Missing after copy: $f"
done
ok "All 4 skill files present"

if "$PY" "$TEST" >/dev/null 2>&1; then
  ok "Smoke test passed (20 checks)"
else
  warn "Smoke test did not run cleanly — try: $PY tests/smoke_test.py"
fi

say ""
say "Done. Start a new Claude Code session, then paste your course notes and say:"
say "  \"save this as markdown\""
say ""
say "Or use the converter directly, with no Claude involved:"
say "  $PY \"$DEST/scripts/build_notes.py\" --body notes.md --title \"Module 6\" --outdir math-notes"
