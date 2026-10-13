# canopy-live · config · every tunable, one home

Nothing here is secret. These are the dials. One home per fact.

## Environment variables

```
CANOPY_MIC_NAME    the name the mic holder appears as in the feed. Default "Me".
                   Set it to your own name:  CANOPY_MIC_NAME="Alex" python3 canopy_run.py
CANOPY_WISPR_DIR   the folder that holds Wispr's meeting subfolders. Overrides the per-OS
                   default below. On Windows you will likely need to set this (see Paths).
NOTION_TOKEN       only used by the optional --page path in jev-compile.py, which is not part
                   of the live loop. Leave unset for normal use.
```

## Paths

```
Wispr transcripts  <wispr-dir>/<meeting-id>/live.ndjson, discovered automatically (newest by
                   mtime). <wispr-dir> is CANOPY_WISPR_DIR if set, else the per-OS default:
                     macOS    ~/Library/Application Support/Wispr Flow/meetings   (confirmed)
                     Windows  %APPDATA%\Wispr Flow\meetings                        (UNCONFIRMED)
                     Linux    ~/.config/Wispr Flow/meetings                        (best guess)
the program        wherever you installed this kit (default ~/canopy-live/program/).
                   The scripts locate themselves and their siblings; no path to set.
the bins           written into the program folder as *.ndjson. Gitignored.
```

### Finding the Windows transcript folder

Wispr's Windows build may store transcripts differently (its docs describe cloud storage and
do not document a local live file). Confirm the file exists before relying on canopy-live.
Start a meeting, then in PowerShell:

```
Get-ChildItem $env:APPDATA\'Wispr Flow' -Recurse -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 10 FullName,Length,LastWriteTime
```

Run it twice ~10s apart and watch for a `live.ndjson` whose `Length` grows while you talk. Set
`CANOPY_WISPR_DIR` to the folder that CONTAINS the meeting subfolders. If no growing local file
exists, canopy-live's local, zero-token design does not apply to that Wispr build yet.

## Cadence

```
loop poll          5s, hardcoded in run.sh. The transcript lands in bursts; 5s misses none.
agent tick         pass it to tick.sh:  tick.sh 10  (floor) ... tick.sh 120 (long call).
pulse cadence      emitted on any move of 0.5+, or at least every 120s, inside jev-compile.py.
staging threshold  pulse >= 6.5 stages a window, at most every 180s.
```

## The word lists (in jev-compile.py)

These are what make the classifier yours. Edit them for your domain.

```
VNOUNS       the "things that hold value" in your conversations. The shipped list is generic
             software/meeting nouns (app, system, agent, plan, feed, dashboard, metric, ...).
             Swap in the nouns that matter to you. A noun or verb only becomes a catch when a
             VNOUN is present, so this list sets recall.

ACTION       verbs that count as "a move that makes a difference" (build, ship, deploy, ...).
AGREE        the explicit agreement markers that make a line "agreed" (exactly, 100%, let's do
             that, that's aligned, for sure, full body yes, that's the one, ...). Nine words.
             A bare "yes" or "yeah" is deliberately NOT one of them (a nod is not a yes).
SELFLABEL    the phrasings that mark a stated intention ("the goal is", "my intention is", ...).
PROBLEM      the phrasings that mark a stated blocker ("the problem is", "I'm stuck", ...).
ADDRESSED    the wake word (canopy and its mishearings). Change it if you rename the tool.
```

## Tuning guidance

```
widen recall   add words to VNOUNS. But widening recall without a way to grade catches is how
               you lose behaviour you had. Build a small labelled set of real lines (caught /
               not caught) before loosening the classifier much.
tighten        the AGREE and SELFLABEL lists are intentionally small and strict. A false catch
               trains distrust faster than a missed one.
privacy        the PRIVACY stage in SPEC-PIPELINE.md is a standing rule and is NOT in the code.
               If other people are on the call, implement it before storing anything.
```
