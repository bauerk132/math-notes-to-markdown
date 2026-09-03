<#
.SYNOPSIS
  Install the math-notes-to-markdown skill for Claude Code.
.EXAMPLE
  .\install.ps1
.EXAMPLE
  .\install.ps1 -Check
#>
[CmdletBinding()]
param([switch]$Check)

$ErrorActionPreference = 'Stop'

$skill = 'math-notes-to-markdown'
$src   = Join-Path $PSScriptRoot "skills\$skill"
$root  = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME '.claude\skills' }
$dest  = Join-Path $root $skill
$test  = Join-Path $PSScriptRoot 'tests\smoke_test.py'

function Ok   ($m) { Write-Host "  [OK] $m"   -ForegroundColor Green }
function Warn ($m) { Write-Host "  [!]  $m"   -ForegroundColor Yellow }
function Die  ($m) { Write-Host "  [X]  $m"   -ForegroundColor Red; exit 1 }

# --- python ------------------------------------------------------------
$py = $null
foreach ($candidate in @('python', 'python3', 'py')) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        & $candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $candidate; break }
    }
}
if (-not $py) { Die 'Python 3.8+ is required and was not found on PATH.' }
Ok "Python found: $(& $py --version 2>&1)"

# --- check mode --------------------------------------------------------
if ($Check) {
    if (-not (Test-Path $dest)) { Die 'Not installed. Run .\install.ps1' }
    Ok "Installed at $dest"
    & $py $test *>$null
    if ($LASTEXITCODE -eq 0) { Ok 'Smoke test passed' } else { Warn "Run: $py tests\smoke_test.py" }
    exit 0
}

if (-not (Test-Path $src)) { Die "Source skill folder missing at $src" }

# --- install -----------------------------------------------------------
if (-not (Test-Path $root)) { New-Item -ItemType Directory -Path $root -Force | Out-Null }

if (Test-Path $dest) {
    $backup = "$dest.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Move-Item -Path $dest -Destination $backup
    Warn "Existing install moved to $(Split-Path $backup -Leaf)"
}

Copy-Item -Path $src -Destination $dest -Recurse
Ok "Installed to $dest"

# --- verify ------------------------------------------------------------
foreach ($f in @('SKILL.md', 'scripts\build_notes.py', 'assets\note-template.html', 'references\formatting.md')) {
    if (-not (Test-Path (Join-Path $dest $f))) { Die "Missing after copy: $f" }
}
Ok 'All 4 skill files present'

& $py $test *>$null
if ($LASTEXITCODE -eq 0) { Ok 'Smoke test passed (20 checks)' } else { Warn "Run: $py tests\smoke_test.py" }

Write-Host ''
Write-Host 'Done. Start a new Claude Code session, then paste your course notes and say:'
Write-Host '  "save this as markdown"'
Write-Host ''
Write-Host 'Or use the converter directly, with no Claude involved:'
Write-Host "  $py `"$dest\scripts\build_notes.py`" --body notes.md --title `"Module 6`" --outdir math-notes"
