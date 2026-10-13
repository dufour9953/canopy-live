#!/usr/bin/env python3
"""canopy-live - the loop, cross-platform. Replaces run.sh on macOS, Windows and Linux.

ear -> feed.log -> jev-compile.py --live, every 5 seconds. Read only on the Wispr side.
Finds the newest Wispr live.ndjson, self-heals to a newer meeting mid-run, and writes a
heartbeat file (.canopy.pid) so canopy_tick.py can tell the loop is alive. Ctrl-C to stop.

The Wispr transcript folder:
  - set CANOPY_WISPR_DIR to override, or
  - default per OS:  Windows  %APPDATA%\\Wispr Flow\\meetings
                     macOS    ~/Library/Application Support/Wispr Flow/meetings
                     Linux    ~/.config/Wispr Flow/meetings   (best guess)
"""
import os, sys, time, glob, signal, subprocess, platform

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows console defaults can break output
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
PIDFILE = os.path.join(HERE, ".canopy.pid")
STATEF = os.path.join(HERE, ".live-state.json")
FEED = os.path.join(HERE, "feed.log")


def wispr_dir():
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


def newest_ear():
    files = glob.glob(os.path.join(wispr_dir(), "*", "live.ndjson"))
    return max(files, key=os.path.getmtime) if files else None


def age(path):
    try:
        return int(time.time() - os.path.getmtime(path))
    except OSError:
        return 10 ** 9


def cleanup(*_):
    try:
        os.remove(PIDFILE)
    except OSError:
        pass
    print("\nstopped.")
    print(f"feed: {FEED}")
    print(f"bins: {HERE}  (agreed/candidates/insights/intents/staged .ndjson)")
    sys.exit(0)


def main():
    ear = newest_ear()
    if not ear:
        print(f"BLIND: no Wispr live.ndjson found under:\n  {wispr_dir()}")
        print("Start a Wispr recording first.")
        if platform.system() == "Windows":
            print("Windows note: Wispr may store transcripts differently than on macOS.")
            print("Confirm the live file with the diagnostic in the README before relying on this.")
        sys.exit(1)

    print(f"ear: {ear}")
    print(f"     last written {age(ear)}s ago. If that is old, this is NOT today's call.")
    try:
        os.remove(STATEF)
    except OSError:
        pass

    for sig in (signal.SIGINT, getattr(signal, "SIGTERM", signal.SIGINT)):
        try:
            signal.signal(sig, cleanup)
        except (ValueError, OSError):
            pass

    earpy = os.path.join(HERE, "ear-wispr.py")
    jev = os.path.join(HERE, "jev-compile.py")
    tick = 0
    try:
        while True:
            open(PIDFILE, "w").write(str(os.getpid()))   # heartbeat: rewritten every loop
            new = newest_ear()
            if new and new != ear and age(ear) > 45 and age(new) < age(ear):
                ear = new
                try:
                    os.remove(STATEF)
                except OSError:
                    pass
                print(f"RE-LATCHED to newer meeting: {ear}")
            with open(FEED, "w", encoding="utf-8") as fh:
                r = subprocess.run([sys.executable, earpy, ear], stdout=fh,
                                   stderr=subprocess.DEVNULL)
            if r.returncode != 0:
                print(f"ear FAILED on tick {tick + 1}")
            subprocess.run([sys.executable, jev, "--live", "--from-log", "feed.log"], cwd=HERE)
            tick += 1
            if tick == 1:
                print("(seeded, listening)")
            time.sleep(5)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
