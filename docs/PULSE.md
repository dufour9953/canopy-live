# canopy-live · the pulse

The pulse is a single number, 0 to 10, computed over roughly the last 40 lines. It gives a
feel for momentum, and on each tick it comes with a reason.

## The formula

```
Pulse = (P · S · Q)^(1/3) · exp(-0.1 · F)
```

A **geometric mean** of three axes, damped by a friction term. The geometric mean is the
point: one dead axis drags the whole score toward zero. A high P must not rescue a zero S.

```
P   pragmatics   real action named. "I'll deploy it Friday", "next step is...", dollar
                 amounts, time commitments, and (when talking to an agent) direct instructions.
S   spirit       what someone actually WANTS. Self-labels, "what I want is", "I think",
                 "honestly", "make sure", changed-my-mind.
Q   questions    question quality, scored against four tests (one question not three, only a
                 human could answer it, it changes what gets built, it is novel). Defaults to
                 a neutral 5.0 when no scored questions are on record.
F   friction     urgency and repetition. Subtracted. Repeated lines and "asap / right now /
                 we have to", plus long silent gaps in the feed.
```

## How to say it

The tick hands you a line like:

```
PULSE 1.8 -> flat  [##........]  P5.2 S0.9 Q5.0 F4.4
```

When a tick brings something new, say the number and the reason in plain words. The reason is
almost always "which axis is lowest", because the geometric mean makes the lowest axis the
story:

```
PULSE 1.8, flat. What anyone actually wants is still quiet, though action and questions
are strong.
```

Name the lowest axis plainly. Do not read the letters aloud ("S is 0.9"). Say what it means
("what you want is still quiet").

## The one rule

**The pulse is a readout. It gates nothing.** Never suppress a catch because the pulse is low.
The filtering lives in the classifier; the pulse only reports. Two things were asked of it and
only these two: give a feel for momentum, and give a periodic reason why the score is what it
is. It does nothing else.

## Modes

```
MODE 1 (active)    Pulse = (P·S·Q)^(1/3) · exp(-0.1·F). Q is question quality.
MODE 2 (dormant)   T replaces Q. T measures a RUNNING system and reads near zero before a
                   working product exists, so it is not scored or mentioned until one person
                   who is not the author uses this unsupervised and gets something out of it.
```
