# canopy-live

A live-call listener for [Claude Code](https://claude.com/claude-code) and
[Wispr Flow](https://wisprflow.ai). You talk; a small local script reads the live transcript,
throws away the noise, and keeps the moments that matter: agreements, stated intentions, and
named actions. An agent reflects on only what survived, on a tick, and tells you what the room
is reaching for and what has not been said yet.

It costs almost nothing to run: the classifier is pattern matching, not a model, and the agent
only ever reads the handful of lines the classifier kept.

```
DURING   the agreed lines, in the speakers' own words, as they happen   (this kit)
AFTER    what was agreed, and who said they would do what                 (optional, your notes tool)
```

## Platform support

| | Status |
|---|---|
| **macOS** | Fully working and tested. The local growing `live.ndjson` is confirmed. |
| **Windows** | Provisional. Wispr Flow and Claude Code run natively on Windows, and the code is cross-platform, but Wispr's Windows docs describe **cloud-stored** transcripts and do not confirm a local growing `live.ndjson`. Run the one-time check below before relying on it. |
| **Linux** | Untested. The runner works; the Wispr path is a guess. Set `CANOPY_WISPR_DIR`. |

## Requirements

- [Wispr Flow](https://wisprflow.ai) with the meeting/Notetaker feature (the transcript is the source).
- Python 3 (standard library only; no pip installs). On Windows the command is `python` (or `py`).
- [Claude Code](https://claude.com/claude-code) to run it as a skill — native on macOS and
  Windows. Optional: the program also runs standalone in a terminal.

## Install

**macOS / Linux:**

```bash
git clone <this-repo> ~/canopy-live
cd ~/canopy-live
./install.sh
```

**Windows (PowerShell):**

```powershell
git clone <this-repo> $HOME\canopy-live
cd $HOME\canopy-live
.\install.ps1
```

The installer copies the skill into `~/.claude/skills/canopy-live/` and points it at wherever
you cloned the kit. Clone anywhere; the installer records the path.

Optionally set the name you want to appear as in the feed (default is `Me`):

```bash
export CANOPY_MIC_NAME="Your Name"        # macOS / Linux
```
```powershell
$env:CANOPY_MIC_NAME = "Your Name"        # Windows
```

## Windows: confirm the live file first

Before trusting canopy-live on Windows, verify the growing local transcript exists. Start a
Wispr meeting, then in PowerShell:

```powershell
Get-ChildItem $env:APPDATA\'Wispr Flow' -Recurse -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 10 FullName,Length,LastWriteTime
```

Run it twice ~10s apart and look for a `live.ndjson` whose `Length` grows while you talk. If you
find it, set `CANOPY_WISPR_DIR` to the folder that holds the meeting subfolders. If no growing
local file exists, Wispr is keeping that transcript in the cloud, and canopy-live's local,
zero-token design does not apply to that build yet.

## Run

1. Start a Wispr recording. **macOS: wear headphones** (otherwise the mic hears your speakers and
   every voice is attributed to you). **Windows: make sure call audio is on your default output
   device** (Wispr captures other participants only from there).
2. In Claude Code, say **`start canopy`** (or `/canopy-live`). The agent asks Mac or Windows,
   opens the ear, checks it can hear you, and starts reflecting on a tick.
3. Say **stop** when the call is over. The catch is saved in `program/*.ndjson`.

Standalone, no agent (gives you the bins, not the reflection):

```bash
python3 ~/canopy-live/program/canopy_run.py     # macOS / Linux  (or ./program/run.sh)
```
```powershell
python $HOME\canopy-live\program\canopy_run.py  # Windows   (Ctrl-C to stop)
```

## What's in here

```
skill/SKILL.md        the Claude Code skill: the start ritual and the reflection sequence.
program/              the loop. Zero-token classifier, the ear, the tick, the gate.
  canopy_run.py       the loop (cross-platform): ear -> feed.log -> classifier, every 5s.
  canopy_tick.py      the agent's read (cross-platform): the pulse + only new rows.
  run.sh / tick.sh    the macOS bash equivalents of the two above.
  ear-wispr.py        reads Wispr's live.ndjson, writes feed.log + roster.txt. Read only.
  jev-compile.py      the classifier. Where the word lists live. Tune this for your domain.
  grounded-check.py   the gate: no verbatim quote, no node.
docs/                 ARCHITECTURE, SPEC-PIPELINE, PULSE, CONFIG, FEED-EXAMPLE.
feedback.md           one line per wrong catch. You write these; tune the word lists from them.
```

## Make it yours

The classifier ships generic. The file to edit is `program/jev-compile.py`, and the dials are
documented in [`docs/CONFIG.md`](docs/CONFIG.md): the `VNOUNS` list (the "things that hold
value" in your conversations) sets recall, and `AGREE` / `SELFLABEL` / `PROBLEM` set what counts
as an agreement, an intention, a blocker. Start from the defaults, run a real call, and add a
line to `feedback.md` each time a catch is wrong.

## Privacy — read before running on a call with other people

- **The live transcript never leaves your machine.** The classifier makes no network calls. The
  bins are written locally and are gitignored, so a `git push` cannot leak them.
- **A privacy stage is specified but NOT implemented.** `docs/SPEC-PIPELINE.md` describes a stage
  that drops lines touching anything personal (family, health, relationships) before storage.
  The shipped classifier does not do this. If you run canopy-live on a call with other people,
  the people who are not you did not consent to being transcribed and stored — implement that
  stage, or run it only on your own voice, or get consent first.
- **Never commit the bins.** `.gitignore` already excludes every `*.ndjson`, `feed.log`,
  `roster.txt`, and the cursor file. Keep it that way.

## What is intentionally NOT included

- An "after ear" connector. The skill describes pulling a meeting note once at the end to compare
  action items against the live catch, but this kit ships no connector. Use whatever notes tool
  and connector you have already authorized.
- A Notion tail-poller. An earlier build had one; it is omitted here because it depended on a
  specific person's code and a token setup that is not part of this generic kit.

## License

MIT, (c) 2026 Chandler Dufour. See [`LICENSE`](LICENSE).
