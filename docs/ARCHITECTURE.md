# canopy-live · architecture

One map of how the pieces fit. Nothing here is private; it is the mechanism.

## What it does, in plain language

You talk. A small Python script reads every line of a live transcript, throws away most of
them, and keeps the moments that matter: agreements, stated intentions, named actions. An
agent reads only what the script kept, on a tick, and reflects.

```
it costs near-zero tokens   the classifier is pattern matching, not a model
it runs on your machine     nothing leaves the Mac during the call
it keeps the exact words    no stage rewrites a line. Verbatim or nothing.
```

The product is two buckets and nothing else:

```
DURING   the agreed lines, in the speakers' own words, as they happen
AFTER    what was agreed, and who said they would do what
```

## The two ears

```
WISPR    the DURING ear.  local, free, polled every 5s, speaker-labelled.
                          loses dictation. the mic hears your speakers.
NOTES    the AFTER ear.   optional, ONCE, on demand. Action items with owners.
                          pulled from whatever notes tool you use. Not shipped here.
```

They are not two feeds of the same thing. They answer different questions. The live ear is
what this kit runs. The after ear is a comparison you pull once at the end if you keep
meeting notes somewhere with action items.

## The ear, concretely

Wispr Flow writes a live transcript on this machine and it grows during a call:

```
~/Library/Application Support/Wispr Flow/meetings/<id>/live.ndjson
```

`ear-wispr.py` reads it (read only, never writes inside the Wispr folder) and emits one line
per utterance in a fixed format: `[HH:MM:SS.mmm] Name: text`. It also writes `roster.txt`,
the speaker names it actually observed.

Speaker labels, from the raw data:

```
source == "mic"      the mic holder. One person. Named by CANOPY_MIC_NAME.
source == "system"   everyone else, often sharing one id. The id cannot separate them;
                     the NAME field can. A missing name stays UNATTRIBUTED.
```

The mic holder can appear on both mic and system and must be de-duplicated. There is no
inference anywhere: a name comes from a label or a self-announcement ("this is Alex"), never
from context.

The transcript arrives in bursts, roughly every one to a few minutes, 1 to 8 seconds after a
sentence ends. Polling faster than that buys nothing. The loop polls every 5s so no burst is
missed; the agent reads on a longer tick.

## The three layers

```
LAYER 1 · THE FILTER     jev-compile.py. Python. Zero tokens. Reads 100% of lines.
                         Separates provable noise from candidates, wide. Keeps the quote.

LAYER 2 · THE REFLECTOR  an agent. Reads ONLY what Layer 1 kept, on the tick. Runs a fixed
                         sequence (R1 to R7, see the skill). Writes reflection to this chat.

LAYER 3 · THE FEED       what others watch during the session. In this kit it is the agent's
                         chat output plus the bin files.
```

**The filter is what makes the reflector cheap.** A survivor stream is a few hundred tokens a
tick. The moment the agent reads the raw transcript, the cost story is dead. Never let it.

### Why Layer 1 is wide, not narrow

An early version filtered hard (keep ~8% of lines). On a real short recording that kept zero
percent, and threw away a clearly stated intention, because a regex cannot know that "a live
feedback feature" is a value-noun and "Okay." is not.

```
WRONG     Layer 1 is the catch, Layer 2 polishes what it caught.
RIGHT     Layer 1 separates NOISE from CANDIDATES, wide.
          Layer 2 is where precision happens, because it can read meaning.
```

So `candidates.ndjson` is deliberately wide: any line of 5+ words that is not a bare
continuer and not torn. The four tight bins (agreed, insights, intents, staged) sit inside
that net for the high-confidence catches.

## The bins

Append-only, idempotent by a short hash of the quote. Every row carries `q` (the spoken
words) and `who`.

```
agreed.ndjson       the product. Explicit agreement markers only.
candidates.ndjson   the wide net. Everything that is not provable noise.
insights.ndjson     nouns and verbs: things that hold value, moves that make a difference.
intents.ndjson      what someone said they want (self-labels, "the goal is").
staged.ndjson       windows the pulse flagged as high-energy.
pulse.ndjson        the momentum readout over time (see PULSE.md).
```

## The gate

`grounded-check.py` is the law made executable: a node without its verbatim quote does not
exist and must not move any number. Run it against any bin to prove every row is
quote-grounded. This is what makes invention impossible.

## What it refuses

- No model call per line. The classifier is local. That is the whole cost story.
- No stage that rewrites text. Verbatim is the product.
- No attribution without a label or an announcement. Guessing a speaker is the cardinal sin.
- No gate inside the classifier. Stacking filters strangles the output.
- Absence is a result. A run that emits nothing reports FAIL, not silence.
