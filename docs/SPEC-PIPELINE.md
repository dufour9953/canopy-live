# canopy-live · pipeline spec · what happens to ONE line, in order

The sequence every line passes through. Tunables live in `CONFIG.md` and are not repeated here.

## The three laws of the pipeline

```
LAW 1   A stage may REJECT a line or ANNOTATE a line. No stage may REWRITE its text.
        The original words are immutable from first stage to last. Verbatim or nothing.

LAW 2   One stage, one job, one reason to reject. A stage that can reject for two different
        reasons is two stages.

LAW 3   The pulse is LAST and gates nothing. Filtering belongs in the classifier, not stacked
        on top of it. Stacked filters strangle the output.
```

## The sequence

### 1 · RECEIVE
Take one line plus the timestamp the source served, not the time we asked.
```
rejects   nothing
emits     a line record
```

### 2 · FRESHNESS · the BLIND gate
Compare the served timestamp to the wall clock and to the previous pull.
```
rejects   nothing, but if the served timestamp has NOT advanced, the pull is BLIND and no
          line from it is treated as evidence of quiet
why       silence from a cached source is not silence from the room
```

### 3 · INTEGRITY
Is this a whole line, or a fragment torn by the poller mid sentence?
```
rejects   torn lines, held for the next pull to complete
```

### 4 · PRIVACY · before anything is stored
Does the line touch family, relationships, childhood, health, religion, the deeply personal?
```
rejects   the line AND its text entirely
why       people who are not on the call did not consent
note      this is a STANDING RULE. It is described here but is NOT implemented in the shipped
          classifier. If you run canopy-live on a call with other people, add this stage
          before storing anything. See the warning in the README.
```

### 5 · ATTRIBUTE · by declared source only
Apply the label grammar for the service feeding us.
```
rejects   nothing. Assigns a name, or assigns UNATTRIBUTED
law       no label and no announcement means UNATTRIBUTED. Not a guess.
law       inference from context is NOT attribution, at any confidence
```
For Wispr: `mic` is the mic holder (CANOPY_MIC_NAME); `system` uses the name field, never the
id. A self-announcement in the text ("this is Alex") can set the current speaker for a window.

### 6 · NORMALIZE · for matching only
Lowercase and strip into a separate match field. The original text is not touched (LAW 1).

### 7 · CONTINUER · a nod is not a yes
Is the line nothing but a backchannel word?
```
rejects   the line as noise
law       matches only when the line is NOTHING BUT that word.
          "Yeah, and we should ship it" survives. "Yeah." does not.
```

### 8 · CLASSIFY · exactly one rank
Assign one of: `yes` · `ask` · `verb` · `noun` · `skip`.
```
law       one rank per line. No line is two things. skip is a rank.
```

### 9 · SCORE
Apply the confidence floor for that rank, plus length penalties.
```
law       SURE is never self-reported. It comes from ensemble disagreement across three
          rule-strictness variants, which are deterministic, so the number is optimistic and
          is labelled as such.
```

### 10 · GROUND · the gate with teeth
Does this catch carry a verbatim quote and the timestamp it came from?
```
rejects   any catch with no quote. No quote, no node.
why       this is the stage that makes invention impossible.
```

### 11 · EMIT · into a bin
```
agreed      an agreed line, in its own words
intents     what someone said they want
insights    nouns and verbs that hold or make value
candidates  the wide net: everything that survived
law         absence is a result. A run that emits nothing reports FAIL, not silence.
```

### 12 · PULSE · readout, never a gate
Compute and record. Suppress nothing. See `PULSE.md`.

### 13 · LOG
One append-only event line, naming the stage and the count. This is what a grep reads to
prove what actually happened versus what the output claimed.
