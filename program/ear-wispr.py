#!/usr/bin/env python3
"""THE EAR - Wispr Flow. Reads the live meeting transcript, prints the ONE format
the sequencer eats. Read only. Never writes inside the Wispr folder.

Output line:  [HH:MM:SS.mmm] Name: text
Also writes roster.txt next to this script: the speaker names actually observed.

Speaker rule (lookup, never inference):
  source == "mic"     -> you, the mic holder. Named by CANOPY_MIC_NAME (default "Me").
  source == "system"  -> everyone else. Named by Wispr's own name field, or left blank.
A blank name stays UNATTRIBUTED downstream. Never guess a name from context.
"""
import json, os, sys, glob, platform, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows console defaults can break output
except Exception:
    pass

MIC_NAME = os.environ.get("CANOPY_MIC_NAME", "Me")   # the mic holder's name in the feed


def wispr_dir():
    """Where Wispr Flow writes meeting transcripts. CANOPY_WISPR_DIR overrides; else per-OS."""
    env = os.environ.get("CANOPY_WISPR_DIR")
    if env:
        return os.path.expanduser(env)
    sysname = platform.system()
    if sysname == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "Wispr Flow", "meetings")
    if sysname == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Wispr Flow/meetings")
    return os.path.expanduser("~/.config/Wispr Flow/meetings")


WISPR = wispr_dir()


def newest(d=None):
    f = glob.glob(os.path.join(d or wispr_dir(), "*", "live.ndjson"))
    return max(f, key=os.path.getmtime) if f else None


def run(path, start=0):
    names, n = set(), 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        fh.seek(start)
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                j = json.loads(ln)
            except Exception:
                continue
            if j.get("marker") or not j.get("text"):
                continue
            sp = j.get("speaker") or {}
            who = MIC_NAME if sp.get("source") == "mic" else (sp.get("name") or "")
            who = (who.split()[0] if who else "")            # "Firstname Last" -> "Firstname"
            t = datetime.datetime.fromtimestamp(
                (j.get("startEpochMs") or 0) / 1000).strftime("%H:%M:%S.%f")[:-3]
            if who:
                names.add(who)
            print(f"[{t}] {who + ': ' if who else ''}{j['text'].strip()}", flush=True)
            n += 1
        pos = fh.tell()
    return n, pos, names


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else newest()
    if not src:
        sys.exit("no live.ndjson found")
    n, pos, names = run(src, int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    here = os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(here, "roster.txt"), "w").write("\n".join(sorted(names)) + "\n")
    print(f"(ear: {n} lines, byte {pos}, roster {sorted(names)})", file=sys.stderr)
