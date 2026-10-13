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

## Requirements

- macOS with [Wispr Flow](https://wisprflow.ai) (the live meeting transcript is the source).
- Python 3 (standard library only; no pip installs).
- [Claude Code](https://claude.com/claude-code) to run it as a skill (optional: the program
  also runs standalone in a terminal).

## Install

```bash
git clone <this-repo> ~/canopy-live
cd ~/canopy-live
./install.sh
```

`install.sh` copies the skill into `~/.claude/skills/canopy-live/` and points it at wherever
you cloned the kit. You can clone anywhere; the installer records the path.

Optionally set the name you want to appear as in the feed:

```bash
export CANOPY_MIC_NAME="Your Name"   # default is "Me"
```

## Run

1. Start a Wispr recording. **Wear headphones** — without them the mic hears your speakers and
   every voice is attributed to you.
2. In Claude Code, say **`start canopy`** (or `/canopy-live`). The agent opens the ear, checks
   it can hear you, and starts reflecting on a tick.
3. Say **stop** when the call is over. The catch is saved in `program/*.ndjson`.

Standalone, no agent (gives you the bins, not the reflection):

```bash
~/canopy-live/program/run.sh      # Ctrl-C to stop
```

## What's in here

```
skill/SKILL.md        the Claude Code skill: the start ritual and the reflection sequence.
program/              the loop. Zero-token classifier, the ear, the tick, the gate.
  run.sh              ear -> feed.log -> classifier, every 5s.
  tick.sh             the agent's read: the pulse + only new rows.
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

MIT. Set your name in [`LICENSE`](LICENSE) (it ships with a `<COPYRIGHT HOLDER>` placeholder).
