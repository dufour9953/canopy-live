# canopy-live · the live feed · target shape

Everything below is a **fabricated sample**, written to show the shape. No real conversation
is reproduced here. Use it as the target the reflector fills from real quotes.

## The sample call (invented)

Two people, Alex (mic holder) and Sam (on the call), talking through a dashboard idea.

```
10:00:01  Alex: So the goal is to ship the live feedback dashboard this week.
10:00:04  Sam:  Yeah, that's it.
10:00:07  Alex: Let's build the parser and wire the feed to the app.
10:00:10  Sam:  How would the pulse metric even work?
10:00:13  Alex: The problem is the transcript arrives in bursts.
10:00:16  Alex: I will deploy the dashboard by Friday.
10:00:19  Sam:  100%, that is aligned.
```

## What Layer 1 keeps (the bins)

```
agreed.ndjson
  {"q": "100%, that is aligned.", "who": "Sam", "t": "yes", "c": 0.85}

intents.ndjson
  {"q": "So the goal is to ship the live feedback dashboard this week.", "who": "Alex", "t": "intent"}

insights.ndjson
  {"q": "I will deploy the dashboard by Friday.", "who": "Alex", "t": "verb", "c": 0.8}

candidates.ndjson
  every 5+-word line that is not a bare nod and not torn, with its who.
```

## What the feed looks like · the agent's reflection

The same lines, after the reflector reads them on a tick. Append-only. Every entry carries its
quote and its timestamp.

```
──────────────────────────────────────────────────────────────────────
canopy-live · LIVE          tick 10:02        FRESH
──────────────────────────────────────────────────────────────────────

INTENTION EMERGED
  ship a live feedback dashboard this week
  "So the goal is to ship the live feedback dashboard this week."
  Alex · 10:00:01

NOW TRUE THAT WAS NOT TRUE AT THE LAST TICK
  the week's deliverable has a named owner and a date
  "I will deploy the dashboard by Friday."
  Alex · 10:00:16

WHO OWES WHAT
  Alex — deploy the dashboard by Friday

NOT SAID YET, AND NEEDED
  what "live feedback" means to look at: a number, a line, a list?
  no one has said who watches the feed besides the two on this call.

──────────────────────────────────────────────────────────────────────
                                              tick 10:04        BLIND
  served timestamp did not advance. The room may be talking.
  I cannot see it. This is not quiet.
──────────────────────────────────────────────────────────────────────
                                              tick 10:06     NOTHING NEW
  1 line since last tick, a backchannel. Nothing new emerged. That is a result.
──────────────────────────────────────────────────────────────────────
```

## Why this shape

```
INTENTION      what the room is reaching for. Quoted, never paraphrased into vapour.
NOW TRUE       the diff. What changed since the last tick, not a running summary.
WHO OWES       names only when the feed names them. Never a guess.
NOT SAID YET   the one a person cannot do while talking. This is why it is watchable.
BLIND          an honesty state, not an absence. Shown, never hidden.
NOTHING NEW    said out loud, so silence is never mistaken for working.
```

Three of the blocks exist to report a limit. A feed that can only show success is a feed you
stop trusting the first time it is wrong.
