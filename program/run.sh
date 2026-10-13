#!/bin/bash
# canopy-live - the loop. One command, no arguments. Ctrl-C to stop.
# Ear: newest Wispr live.ndjson -> feed.log. Sequencer: jev-compile.py --live, every 5 seconds.
# Read only on the Wispr side. Bins land in this folder.
#
# Optional: set CANOPY_MIC_NAME to the name you want the mic holder to appear as.
#   CANOPY_MIC_NAME="Alex" ./run.sh      (default is "Me")
HERE="$(cd "$(dirname "$0")" && pwd)"
EARPY="$HERE/ear-wispr.py"
cd "$HERE" || exit 1
WISPR_DIR="${CANOPY_WISPR_DIR:-$HOME/Library/Application Support/Wispr Flow/meetings}"

EAR=$(ls -t "$WISPR_DIR/"*/live.ndjson 2>/dev/null | head -1)
if [ -z "$EAR" ]; then echo "BLIND: no Wispr live.ndjson found. Start a Wispr recording first."; exit 1; fi
AGE=$(( $(date +%s) - $(stat -f %m "$EAR") ))
echo "ear: $EAR"
echo "     last written ${AGE}s ago. If that is old, this is NOT today's call: start Wispr, then rerun."
rm -f .live-state.json        # new call, new cursor. Tick 1 seeds at end of file.
trap 'echo; echo "stopped."; echo "feed: $HERE/feed.log"; echo "bins: $HERE/{agreed,candidates,insights,intents,staged}.ndjson"; exit 0' INT TERM
tick=0
while true; do
  # self-heal: a new Wispr meeting started mid-run?
  # re-latch to it when the current ear has gone stale AND a newer file is live.
  NEWEAR=$(ls -t "$WISPR_DIR/"*/live.ndjson 2>/dev/null | head -1)
  if [ -n "$NEWEAR" ] && [ "$NEWEAR" != "$EAR" ]; then
    EARAGE=$(( $(date +%s) - $(stat -f %m "$EAR") ))
    NEWAGE=$(( $(date +%s) - $(stat -f %m "$NEWEAR") ))
    if [ "$NEWAGE" -lt "$EARAGE" ] && [ "$EARAGE" -gt 45 ]; then
      EAR="$NEWEAR"; rm -f .live-state.json
      echo "RE-LATCHED to newer meeting: $EAR"
    fi
  fi
  python3 "$EARPY" "$EAR" > feed.log 2>/dev/null || echo "ear FAILED on tick $((tick+1))"
  python3 jev-compile.py --live --from-log feed.log
  tick=$((tick+1))
  [ $tick -eq 1 ] && echo "(seeded, listening)"
  sleep 5
done
