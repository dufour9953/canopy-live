#!/bin/bash
# canopy-live - the agent's tick. Every N seconds (default 120, pass 10 for quicker) print:
#   1. the PULSE, every single tick, with its arrow. This is the momentum readout.
#   2. ONLY the bin rows that are new since the last tick.
# Each printed block is one event for the agent reading this. Read only.
# STOPPED when run.sh is gone. "nothing new" is not proof of a quiet room.
# bash 3.2 safe (macOS): no associative arrays.
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE" || exit 1
N=${1:-120}
count() { if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else echo 0; fi; }
SA=$(count agreed.ndjson); SC=$(count candidates.ndjson); PREV=""
while true; do
  sleep "$N"
  if ! pgrep -f "canopy-live/program/run.sh" >/dev/null && ! pgrep -f "program/run.sh" >/dev/null; then
    echo "STOPPED $(date +%H:%M:%S) run.sh is not running"; exit 0
  fi

  # --- THE PULSE - every tick, caught or not. Momentum is the point.
  if [ -f pulse.ndjson ]; then
    PLINE=$(python3 - "$PREV" <<'PY'
import json,sys
prev = sys.argv[1]
try:
    rows=[json.loads(l) for l in open("pulse.ndjson") if l.strip()]
except Exception: rows=[]
if rows:
    cur=rows[-1]["pulse"]
    p=float(prev) if prev not in ("","None") else None
    d=0.0 if p is None else cur-p
    arrow="->" if p is None or abs(d)<0.2 else ("up" if d>0 else "down")
    word={"up":"moving","down":"stalling","->":"flat"}[arrow]
    ax=rows[-1].get("axes",{})
    bar="#"*int(round(cur))+"."*(10-int(round(cur)))
    print(f'PULSE {cur:.1f} {arrow} {word}  [{bar}]  ' +
          " ".join(f"{k}{v:.1f}" for k,v in ax.items()))
    print(cur)
PY
)
    [ -n "$PLINE" ] && echo "$(echo "$PLINE" | head -1)" && PREV=$(echo "$PLINE" | tail -1)
  fi

  A=$(count agreed.ndjson); C=$(count candidates.ndjson)
  [ "$A" -gt "$SA" ] && sed -n "$((SA+1)),${A}p" agreed.ndjson | sed 's/^/agreed /'
  [ "$C" -gt "$SC" ] && sed -n "$((SC+1)),${C}p" candidates.ndjson | sed 's/^/candidates /'
  [ "$A" -eq "$SA" ] && [ "$C" -eq "$SC" ] && echo "  nothing new - feed.log $(count feed.log) lines"
  SA=$A; SC=$C
done
