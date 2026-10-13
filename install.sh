#!/bin/bash
# canopy-live installer.
# Copies the skill into ~/.claude/skills/canopy-live/ and points it at this kit's location.
# Safe to re-run. Installs nothing else, touches no data.
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="$HERE/skill/SKILL.md"
SKILL_DIR="$HOME/.claude/skills/canopy-live"

if [ ! -f "$SKILL_SRC" ]; then
  echo "error: $SKILL_SRC not found. Run this from inside the cloned kit." >&2
  exit 1
fi

mkdir -p "$SKILL_DIR"
# Substitute the install location into the skill's paths.
sed "s#{{CANOPY_HOME}}#$HERE#g" "$SKILL_SRC" > "$SKILL_DIR/SKILL.md"

chmod +x "$HERE/program/run.sh" "$HERE/program/tick.sh" \
         "$HERE/program/ear-wispr.py" "$HERE/program/jev-compile.py" \
         "$HERE/program/grounded-check.py" 2>/dev/null || true

echo "installed:"
echo "  skill   -> $SKILL_DIR/SKILL.md  (points at $HERE)"
echo "  program -> $HERE/program/"
echo
echo "next:"
echo "  1. set your name (optional):   export CANOPY_MIC_NAME=\"Your Name\""
echo "  2. start a Wispr recording, on headphones"
echo "  3. in Claude Code, say:        start canopy  (or /canopy-live)"
echo
echo "to run it standalone, no agent:  $HERE/program/run.sh   (Ctrl-C to stop)"
