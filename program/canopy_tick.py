#!/usr/bin/env python3
"""canopy-live - the agent's tick, cross-platform. Replaces tick.sh.

Every N seconds (arg, default 120; pass 10 for quicker) print:
  1. the PULSE, every tick, with its arrow. The momentum readout.
  2. ONLY the bin rows that are new since the last tick.
STOPPED when the loop's heartbeat (.canopy.pid) goes stale. Read only.
"nothing new" is NOT proof of a quiet room.
"""
import os, sys, time, json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PIDFILE = os.path.join(HERE, ".canopy.pid")


def count(name):
    try:
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def tail(name, start, end):
    try:
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            return f.read().splitlines()[start:end]
    except OSError:
        return []


def heartbeat_age():
    try:
        return time.time() - os.path.getmtime(PIDFILE)
    except OSError:
        return 10 ** 9


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    sa, sc = count("agreed.ndjson"), count("candidates.ndjson")
    prev = None
    while True:
        time.sleep(n)
        if heartbeat_age() > 15:
            print(f"STOPPED {time.strftime('%H:%M:%S')} the loop is not running")
            return

        # THE PULSE - every tick, caught or not.
        try:
            rows = [json.loads(l) for l in open(os.path.join(HERE, "pulse.ndjson"), encoding="utf-8") if l.strip()]
        except OSError:
            rows = []
        if rows:
            cur = rows[-1]["pulse"]
            d = 0.0 if prev is None else cur - prev
            arrow = "->" if prev is None or abs(d) < 0.2 else ("up" if d > 0 else "down")
            word = {"up": "moving", "down": "stalling", "->": "flat"}[arrow]
            ax = rows[-1].get("axes", {})
            filled = max(0, min(10, int(round(cur))))
            bar = "#" * filled + "." * (10 - filled)
            print(f"PULSE {cur:.1f} {arrow} {word}  [{bar}]  " +
                  " ".join(f"{k}{v:.1f}" for k, v in ax.items()))
            prev = cur

        a, c = count("agreed.ndjson"), count("candidates.ndjson")
        for ln in tail("agreed.ndjson", sa, a):
            print("agreed " + ln)
        for ln in tail("candidates.ndjson", sc, c):
            print("candidates " + ln)
        if a == sa and c == sc:
            print(f"  nothing new - feed.log {count('feed.log')} lines")
        sa, sc = a, c


if __name__ == "__main__":
    main()
