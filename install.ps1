# canopy-live installer (Windows / PowerShell).
# Copies the skill into ~\.claude\skills\canopy-live\ and points it at this kit's location.
# Safe to re-run. Installs nothing else, touches no data.
$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillSrc = Join-Path $Here "skill\SKILL.md"
$SkillDir = Join-Path $HOME ".claude\skills\canopy-live"

if (-not (Test-Path $SkillSrc)) {
    Write-Error "skill\SKILL.md not found. Run this from inside the cloned kit."
    exit 1
}

New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null
# Substitute the install location into the skill's paths.
(Get-Content -Raw $SkillSrc).Replace("{{CANOPY_HOME}}", $Here) |
    Set-Content -Encoding UTF8 (Join-Path $SkillDir "SKILL.md")

Write-Host "installed:"
Write-Host "  skill   -> $SkillDir\SKILL.md  (points at $Here)"
Write-Host "  program -> $Here\program\"
Write-Host ""
Write-Host "next:"
Write-Host "  1. confirm the Wispr live file exists (see README: 'Windows: confirm the live file first')"
Write-Host "  2. set your name (optional):   `$env:CANOPY_MIC_NAME = 'Your Name'"
Write-Host "  3. set the Wispr folder:       `$env:CANOPY_WISPR_DIR = '<folder holding meeting subfolders>'"
Write-Host "  4. start a Wispr recording, then in Claude Code say:  start canopy  (or /canopy-live)"
Write-Host ""
Write-Host "to run it standalone, no agent:  python $Here\program\canopy_run.py   (Ctrl-C to stop)"
