#!/usr/bin/env python3
# jev-compile.py  -  canopy-live sequencer. Zero tokens, pure pattern matching.
#
# Treats the transcript as a stream of lines. The only attribution is a lookup:
# the ear labels each line with a speaker (mic holder, or a named system speaker),
# and a self-announcement in the text ("this is Alex") can set the current speaker.
# Everything else is UNATTRIBUTED and we say so. No inference, ever.
#
# Stages: COMPILE (type each line) + ACCUMULATE (noun/verb -> bins WITH the quote) + EMIT.
# Movement Grammar: NOUN = a thing that holds value, VERB = a move that makes a difference, else NOISE.
# SURE is NOT self-reported: an ensemble of 3 rule-strictness variants; SURE = their agreement.
#
# Ranks (honest about what text alone can prove):
#   A  a proposal followed within a few turns by an agreement marker. Labelled
#      "AGREEMENT FOLLOWS, SPEAKER UNKNOWN" unless a name was announced. Strongest signal.
#   B  a self-label ("my mission is", "so the goal is"). Needs no attribution. Most RELIABLE here.
#   D  the vivid line. Last, on purpose.
#
# Usage (live, the normal path, driven by run.sh):
#   python3 jev-compile.py --live --from-log feed.log
# Usage (batch / self-test):
#   python3 jev-compile.py --from-log feed.log --last 100
#   python3 jev-compile.py --selftest

import os, sys, re, json, time, glob, argparse, urllib.request, urllib.parse, urllib.error, datetime

MIC_NAME = os.environ.get("CANOPY_MIC_NAME", "Me")   # the mic holder's name in the feed
TOKEN = os.environ.get("NOTION_TOKEN")               # only used by the optional --page path
HDRS = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28"}


def notion_get(block_id, cursor=None):
    url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
    if cursor:
        url += "&start_cursor=" + urllib.parse.quote(cursor)
    for _ in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS)) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After", "2"))); continue
            raise
    raise RuntimeError("too many 429s")


def text_of(b):
    rt = b.get(b.get("type", ""), {})
    rt = rt.get("rich_text") if isinstance(rt, dict) else None
    return "".join(t.get("plain_text", "") for t in rt) if rt else ""


def find_container(page):
    j = notion_get(page); best, bestn = page, -1
    for b in j["results"]:
        if not b.get("has_children"):
            continue
        n = sum(1 for x in notion_get(b["id"])["results"] if text_of(x))
        if n > bestn:
            bestn, best = n, b["id"]
    return best


def split_sents(t):
    # Blocks are coarse multi-sentence paragraphs; a quote should be one utterance.
    return [p.strip() for p in re.split(r'(?<=[.?!])\s+', t) if p.strip()]


def collect_lines(container):
    out, cur = [], None
    while True:
        j = notion_get(container, cur)
        for b in j["results"]:
            t = text_of(b).strip()
            if t:
                out += split_sents(t)
        if j.get("has_more"):
            cur = j["next_cursor"]
        else:
            break
    return out


# ---- Movement Grammar ----
AGREE = [r"\bexactly\b", r"\bthat'?s it\b", r"\blet'?s do that\b", r"(?<![\w%])100%", r"\bi'?m down\b",
         r"\bthat'?s aligned\b", r"\bfor sure\b", r"\bfull body yes\b", r"\bthat'?s the one\b"]
CONTINUER = re.compile(r"^\s*(yeah|yep|yes|mm+ ?hm+|uh ?huh|right|okay|ok|got it|sure|cool|perfect)[\s,]*(yeah|yep|yes|ok|okay|sure)?\s*[.!]?\s*$", re.I)
QWORDS = re.compile(r"^(what|why|how|when|where|who|do you|does|can we|can you|should we|would you|is it|are we|is that)\b", re.I)
ACTION = ["build","ship","deploy","create","write","add","parse","wire","run","connect","catch","emit",
          "merge","pull","push","split","judge","onboard","route","make","set up","record","attach",
          "map","stage","hand off","generate","store","check","prove","use","take",
          "stop","start","open","close","send","share","show","fix","change","update","move","name",
          "test","try","keep","put","set","turn","hook","save","delete","remove","rename","point",
          "focus","finish","switch","swap","tighten","loosen","park","unpark","restart","kill"]
MODAL = {"should","need","needs","have","has","got","gotta","gonna","can","could","will","must","let's","lets","wanna","want"}
LEAD = re.compile(r"^(so|and|but|okay|ok|like|well|then|we|i|you|you'?ll|let'?s|i'?m gonna|gonna|we'?re gonna|we'?ll|just)\b[\s,]*", re.I)
# VNOUNS is a tunable word list: the "things that hold value" in your domain.
# Swap these for the nouns that matter in YOUR conversations. See docs/CONFIG.md.
VNOUNS = ["app","system","tool","agent","transcript","plan","board","intent","skill","product","mvp",
          "pipeline","file","os","node","gate","feed","workflow","script","engine","method","rubric",
          "loop","folder","sequence","trigger","insight","repo","terminal","prompt","context","token",
          "call","demo","version","structure","feature","model","design","report","dashboard","metric"]
SELFLABEL = [r"that'?s the intention", r"the intention is", r"my intention is", r"my mission is",
             r"what i want is", r"so the goal is", r"the goal is", r"the whole point is",
             r"what i'?m trying to do", r"what we'?re trying to do", r"the idea is", r"the point is",
             r"what i'?m saying is", r"the priority is"]
# NOT self-labels: "i want to", "we want to", "we need to". Too common in ordinary speech; adding them
# turned B (the most reliable rank in a single-voice feed) into the loosest one. Removed after a false catch.
ROSTER = {MIC_NAME.lower()}
# The ear writes roster.txt next to the feed: the names it actually heard. A speaker missing
# from ROSTER silently inherited the LAST valid name, which is a false attribution.
def seed_roster(feed_path):
    rp = os.path.join(os.path.dirname(os.path.abspath(feed_path)), "roster.txt")
    added = set()
    if os.path.exists(rp):
        for ln in open(rp, encoding="utf-8", errors="replace"):
            if ln.split():
                added.add(ln.split()[0].lower())
    ROSTER.update(added)
    return added
ANNOUNCE = [re.compile(r"\bthis is (\w+)", re.I), re.compile(r"\b(\w+) here\b", re.I),
            re.compile(r"\b(\w+) speaking\b", re.I)]
# DELETED: r"it's (\w+)" - cannot distinguish an announcement from a list ("it's Dana, Sam and Alex")
# A useful convention, if the room adopts it: say your name when you agree -> "Sam: yes, that's it".
NAMEPREFIX = re.compile(r"^\s*(\w+)\s*:")
ATTR_WINDOW = 40  # lines an announcement stays valid (proxy for "a few minutes")
# A triage heuristic worth adopting: speak on Intention, Problem, Yes, or when addressed by name.
#   Intention (= B self-label), Problem, Yes (= A agreement), addressed-by-name.
# Echo is NOT adopted: it needs two identified speakers, which is dead rank C.
PROBLEM = [r"\bthe problem is\b", r"\bthe issue is\b", r"\bdoesn'?t work\b", r"\bis broken\b",
           r"\bnot working\b", r"\bi'?m stuck\b", r"\bwe'?re stuck\b", r"\bthe blocker\b",
           r"\bwhat'?s blocking\b", r"\bfalls apart\b", r"\bthat breaks\b"]
ADDRESSED = re.compile(r"\b(canopy|kanopy|canope|canopi)\b", re.I)  # transcribers mangle the wake word
NAMES_A_THING = re.compile(r"\b(is|are|was|were|means|holds|becomes|that'?s|this is|we have|there'?s|it'?s|we need|we built)\b", re.I)


def is_agree(s):
    if CONTINUER.match(s):
        return False
    if any(re.search(p, s, re.I) for p in AGREE):
        return True
    # DELETED: the len<=4 + \b(yes|perfect)\b fallback. It made a bare "Yes." an
    # agreement. The agreement list has nine words and "yes" is not one of them.
    return False


def is_question(s):
    return s.strip().endswith("?") or bool(QWORDS.match(s.strip()))


def starts_action(s):
    t = LEAD.sub("", s.strip().lower()); toks = re.findall(r"[a-z']+", t)
    head = " ".join(toks[:4])
    if any(head == v or head.startswith(v + " ") for v in ACTION):
        return True
    if any(t in ACTION for t in toks[:5]):
        return True      # action verb early in the clause
    for i, tok in enumerate(toks[:4]):
        if tok in MODAL:
            nxt = " ".join(toks[i+1:i+3])
            if any(nxt == v or nxt.startswith(v + " ") or nxt.split(" ")[0] == v for v in ACTION):
                return True
    return False


def has_vnoun(s):
    return any(re.search(r"\b" + re.escape(n) + r"s?\b", s, re.I) for n in VNOUNS)


def is_selflabel(s):
    return any(re.search(p, s, re.I) for p in SELFLABEL)


def classify(s, maxw):
    if is_agree(s):
        return "agreement"
    if is_question(s):
        return "question"
    w = len(s.split())
    if re.search(r"\bi was\b|\bwe were\b|\bwas doing\b", s, re.I):
        return "noise"
    # a VERB is a move that makes a difference: an action AND something of value it acts on,
    # otherwise "I'm going to share my screen" counts as a node and the board inflates.
    if w <= maxw and starts_action(s) and has_vnoun(s):
        return "verb"
    # a NOUN is a thing that HOLDS value: it must be named or asserted, not merely mentioned,
    # otherwise "A good tool as well." becomes a node and the board fills with fragments.
    if w <= max(6, maxw - 6) and has_vnoun(s) and NAMES_A_THING.search(s):
        return "noun"
    return "noise"


def typed(s):
    v = [classify(s, 12), classify(s, 18), classify(s, 24)]
    if len(set(v)) == 1:
        return v[1], "sure"
    for t in set(v):
        if v.count(t) >= 2:
            if t != "noise" and v[0] == "noise" and v[1] == "noise" and v[2] == t:
                return t, "does not fit"
            return t, "probably"
    return v[1], "torn"


def is_problem(s):
    return any(re.search(p, s, re.I) for p in PROBLEM)


def detect_announce(s):
    # DELETED: bare-roster-name match. It fired on names merely MENTIONED ("it's Dana, Sam and
    # Alex"), producing false attribution, which is worse than none. Announcements only now.
    m = NAMEPREFIX.match(s)          # "Sam: yes, that's it"
    if m and m.group(1).lower() in ROSTER:
        return m.group(1).title()
    for p in ANNOUNCE:
        m = p.search(s)
        if m and m.group(1).lower() in ROSTER:
            return m.group(1).title()
    return None


def attribute(lines):
    who, cur, since = [], "UNATTRIBUTED", 0
    for s in lines:
        a = detect_announce(s)
        if a:
            cur, since = a, 0
        else:
            since += 1
            if cur != "UNATTRIBUTED" and since > ATTR_WINDOW:
                cur = "UNATTRIBUTED"
        who.append(cur)
    return who


# --- WINDOW LEVEL - THE PULSE - Pulse = (P*S*T)^(1/3) * exp(-0.1*F), 0-10 over ~40 lines.
# GEOMETRIC MEAN on purpose: one dead axis zeroes the read. A high P must not rescue a zero T.
# Three variants per axis; if they disagree by more than 3 the axis is UNKNOWN and NO pulse is emitted.
# CAVEAT, same as SURE: these variants are deterministic, so they agree more than a real sampler would.
PRAGMA_PATS = [r"\bi will\b", r"\bwe will\b", r"\bi'?ll\b", r"\bwe'?ll\b", r"\blet'?s\b", r"\bwe did\b",
               r"\bi did\b", r"\bshipped\b", r"\bdeployed\b", r"\bfinished\b", r"\bby (tomorrow|monday|tuesday|wednesday|thursday|friday)\b",
               r"\b\d+ ?(minute|hour|day|week)s?\b", r"\$\d+", r"\bi'?m going to\b", r"\bnext step\b",
               # agent instructions ARE real action named, when you are talking to an agent
               r"\bdeploy\b", r"\bpush (this|that|it)\b", r"\bsend (it|this|that)\b", r"\bbuild the\b",
               r"\brun (it|that|this)\b", r"\btell (it|him|her|them)\b", r"\bhave (it|him|her|them)\b",
               r"\bgive (it|him|her|them)\b", r"\bprompt\b", r"\bstage (it|that|this)\b"]
SPIRIT_PATS = SELFLABEL + [r"\bi think\b", r"\bi reali[sz]e\b", r"\bactually\b", r"\bchanged my mind\b",
                           r"\bi was wrong\b", r"\bhonestly\b", r"\bwhat i want\b", r"\bi feel like\b",
                           # dictating what you want to an agent IS saying what you want
                           r"\bi want (you|it) to\b", r"\bmake sure\b", r"\bwhat i need\b", r"\bgo ahead and\b"]
HANDOFF_PATS = [r"\byeah,? and\b", r"\bbuilding on\b", r"\bto your point\b", r"\bwhat you said\b",
                r"\blike you said\b", r"\bthat'?s what (you|he|she|they)\b", r"\bexactly what\b",
                r"\byou mentioned\b", r"\bto piggyback\b"]
ARRIVAL_PATS = [r"\bwhat'?s up\b", r"\bbonjour\b", r"\bwelcome\b", r"\bcatch (him|her|them|you) up\b",
                r"\byou'?re on the call\b", r"\bthis is \w+ talking\b", r"\bjust joined\b", r"\bhey guys\b"]
URGENCY_PATS = [r"\bright now\b", r"\bhurry\b", r"\basap\b", r"\bimmediately\b", r"\bwe have to\b"]


def _rate(window, pats):
    n = max(1, len(window))
    return sum(1 for s in window if any(re.search(p, s, re.I) for p in pats)) / n


# MODE 1 (pre-MVP, active): Pulse = (P*S*Q)^(1/3) * exp(-0.1*F)
# MODE 2 (post-MVP, dormant): T replaces Q. T measures a RUNNING system and reads near
# zero before a working product exists, so it is NOT scored and NOT mentioned until the
# trigger fires: one person who is not the author uses this unsupervised and gets something out of it.
def pulse(window, whos, extra_friction=0.0, third=None, third_name="Q"):
    """ONE pass. No sampling, no variants, no UNKNOWN. A dial, not a measurement."""
    import math
    K, n = 35, max(1, len(window))
    P = min(10.0, _rate(window, PRAGMA_PATS) * K)
    S = min(10.0, _rate(window, SPIRIT_PATS) * K)
    norm = [re.sub(r"[^a-z ]", "", x.lower()).strip() for x in window]
    rep_r = (len(norm) - len(set(norm))) / n
    F = min(10.0, (rep_r * K * 0.5 + _rate(window, URGENCY_PATS) * K * 0.5) + extra_friction)
    third = 0.0 if third is None else float(third)
    axes = {"P": P, "S": S, third_name: third, "F": F}
    score = ((max(P, 0.0) * max(S, 0.0) * max(third, 0.0)) ** (1.0 / 3.0)) * math.exp(-0.1 * F)
    return score, axes


# --- THE BINS - append-only files, idempotent by id.
BINS = {"insights": "insights.ndjson", "intents": "intents.ndjson", "staged": "staged.ndjson",
        "agreed": "agreed.ndjson", "candidates": "candidates.ndjson"}
def _bin(name): return os.path.join(os.path.dirname(os.path.abspath(__file__)), BINS[name])
def _ids(path):
    out = set()
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            try:
                out.add(json.loads(ln)["id"])
            except Exception:
                pass
    return out
# The ear writes "Name: text". The name is not part of what was said, so it leaves the quote.
def split_who(s):
    m = re.match(r"^\s*(\w+):\s(.*)$", s, re.S)
    if m and m.group(1).lower() in ROSTER:
        return m.group(1), m.group(2)
    return None, s


# THE WIDE bin. Everything that is not provable noise: not a backchannel-only line, not torn,
# 5 or more words. It reads classify() and changes nothing; the four bins above behave as before.
def is_candidate(s):
    q = split_who((s or "").strip())[1].strip()
    if CONTINUER.match(q) or len(q.split()) < 5:
        return False
    return typed(q)[1] != "torn"


def stage(name, t, c, q, at=None, who=None):
    """Append only. Idempotent by id. No quote, no row."""
    import hashlib
    n, q = split_who((q or "").strip())
    q = q.strip()
    who = who or n or "UNATTRIBUTED"
    if not q:
        return False
    rid = hashlib.sha1(q.encode("utf-8")).hexdigest()[:4]
    path = _bin(name)
    if rid in _ids(path):
        return False
    at = at or datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
    with open(path, "a") as f:
        f.write(json.dumps({"id": rid, "t": t, "c": round(float(c), 2), "q": q, "who": who, "at": at}, ensure_ascii=False) + "\n")
    return True


def stream_row(s):
    """ONE pass, no ensemble. Speed over certainty: the operator corrects faster than sampling would."""
    t = classify(s, 18)
    w = len(s.split())
    if t == "agreement":
        t, c = "yes", 0.85
    elif t == "question":
        t, c = "ask", 0.75
    elif t == "verb":
        c = 0.80
    elif t == "noun":
        c = 0.70
    else:
        t = "skip"; c = 0.20 + (0.15 if has_vnoun(s) else 0.0) + (0.10 if w >= 8 else 0.0)
    # Agreement words are short BY NATURE ("exactly", "100%"). The under-5 penalty
    # silently demoted every one of them from the declared 0.85 floor to 0.70.
    if w < 5 and t != "yes":
        c -= 0.15
    return t, max(0.0, min(1.0, round(c, 2)))


# Q - QUESTION QUALITY, scored against the four tests, never against how it feels.
FORK_PATS = [r"\bor\b.*\?", r"\bversus\b", r"\bshould we\b", r"\bwhich (one|way)\b", r"\beither\b", r"\btrade ?off\b"]
def q_score(window, qpath, lookback_s=3600):
    import datetime as _d
    now = _d.datetime.now(_d.timezone.utc); qs = []
    if os.path.exists(qpath):
        for ln in open(qpath, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                q = json.loads(ln); t = _d.datetime.fromisoformat(q["ts"].replace("Z", "+00:00"))
            except Exception:
                continue
            if (now - t).total_seconds() <= lookback_s:
                qs.append(q)
    if not qs:
        return 2.0 if any(re.search(p, s, re.I) for s in window for p in FORK_PATS) else 5.0
    tests = ("one_not_three", "human_only", "changes_build", "novel")
    return min(10.0, sum(2.5 * sum(int(q.get(t, 0)) for t in tests) for q in qs) / len(qs))


# --- P1 attribution: Wispr as a LOOKUP. NEVER a merge. mic = the mic holder, system = the room.
WISPR_DIR = os.path.expanduser("~/Library/Application Support/Wispr Flow/meetings")
_STOP = set("the a an and or but so like just really you i we it that this is are was were to of in on for with".split())
def _toks(t): return {w for w in re.findall(r"[a-z']+", t.lower()) if w not in _STOP and len(w) > 2}
_WIDX = None
def wispr_index():
    global _WIDX
    if _WIDX is not None:
        return _WIDX
    _WIDX = []
    try:
        files = glob.glob(os.path.join(WISPR_DIR, "*", "live.ndjson"))
        if files:
            newest = max(files, key=os.path.getmtime)
            if time.time() - os.path.getmtime(newest) < 900:
                for ln in open(newest, encoding="utf-8", errors="replace"):
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
                    who = MIC_NAME if sp.get("source") == "mic" else f"room-{sp.get('id','?')}"
                    _WIDX.append((_toks(j["text"]), who))
    except Exception:
        pass
    return _WIDX
def wispr_who(line, min_overlap=0.45, min_shared=4):
    idx = wispr_index()
    if not idx:
        return None
    lt = _toks(line)
    if len(lt) < min_shared:
        return None
    best, bw = 0.0, None
    for wt, w in idx:
        shared = len(lt & wt)
        if shared < min_shared:
            continue
        jac = shared / len(lt | wt)
        if jac > best:
            best, bw = jac, w
    return bw if best >= min_overlap else None


def emit(lines, who):
    """Rank A is DELETED. Nothing is agreed automatically; a human pick IS the agreement."""
    cands, seen = [], set()
    def add(quote, w, rank, sure, agreed):
        if quote and quote not in seen:
            seen.add(quote); cands.append({"quote": quote, "who": w, "rank": rank, "sure": sure, "agreed_by": agreed})
    for i, s in enumerate(lines):
        t, sure = typed(s)
        if t in ("noun", "verb"):
            add(s, wispr_who(s) or who[i], "PROPOSAL", sure, "unconfirmed - your pick is the agreement")
    for i, s in enumerate(lines):
        if is_selflabel(s):
            _, sure = typed(s)
            add(s, wispr_who(s) or who[i], "SELF-LABEL", sure, "self-label, no agreement needed")
    nonnoise = [s for s in lines if typed(s)[0] != "noise"]
    pool = nonnoise or lines
    if pool:
        v = max(pool, key=len)
        add(v, who[lines.index(v)], "VIVID", "n/a", "vivid, lowest tier")
    order = {"PROPOSAL": 0, "SELF-LABEL": 1, "VIVID": 2}
    cands.sort(key=lambda c: order[c["rank"]])
    return cands[:5]


# SKIP on torn applies to CANDIDATES only, never the stream. Showing a torn answer trains distrust.
def log_skip(c):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "skipped.ndjson"), "a") as f:
        f.write(json.dumps({"line": c["quote"], "rank": "SKIP", "confidence": c["sure"],
                            "would_have_been": c["rank"], "who": c["who"],
                            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}) + "\n")
def pick_top(cands):
    for c in cands:
        if c["rank"] not in ("PROPOSAL", "SELF-LABEL"):
            continue
        if c["sure"] == "torn":
            log_skip(c); continue
        return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default=None)
    ap.add_argument("--last", type=int, default=100)
    ap.add_argument("--from-log", dest="from_log", default=None)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--catchline", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))

    if a.selftest:
        for c in ["Let's build the parser tonight.", "The intent file is the gate.", "Yeah, that's it.",
                  "How would that even work?", "this is Alex", "A good tool as well."]:
            print(f"{stream_row(c)[0]:5} {stream_row(c)[1]:.2f} | announce={detect_announce(c)} | {c}")
        return

    def lines_from_log(path):
        out = []
        for l in open(path, encoding="utf-8", errors="replace"):
            l = re.sub(r'^\[\d\d:\d\d:\d\d\.\d+\]\s*', '', l).strip()
            if not l or l.startswith(("Following", "poller starting", "fast heartbeat")):
                continue
            out += split_sents(l)
        return out

    if a.from_log:
        seed_roster(a.from_log)
    raw = open(a.from_log, encoding="utf-8", errors="replace").readlines() if a.from_log else []
    lines = lines_from_log(a.from_log) if a.from_log else collect_lines(find_container(a.page))
    who = attribute(lines)

    if a.emit or a.catchline:
        cands = emit(lines[-120:], who[-120:])
        if a.catchline:
            top = pick_top(cands)
            print(f'CAUGHT: "{top["quote"][:110]}" - {top["rank"]} - {top["sure"]}' if top else "nothing clean to catch")
        else:
            for c in cands:
                print(f'{c["rank"]:11} | {c["sure"]:9} | {c["who"]:12} | {c["quote"][:70]}')
            print("STOP. The room picks. canopy-live does not pick.")
        return

    if a.live:
        import time as _t, datetime as _dt
        statef = os.path.join(here, ".live-state.json")
        total = len(raw)
        st = {"pos": total}
        if os.path.exists(statef):
            try:
                st = json.load(open(statef))
            except Exception:
                pass
        pos = min(int(st.get("pos", total)), total)
        new_lines = []
        for l in raw[pos:total]:
            l = re.sub(r'^\[\d\d:\d\d:\d\d\.\d+\]\s*', '', l).strip()
            if not l or l.startswith(("Following", "poller starting", "fast heartbeat")):
                continue
            new_lines += split_sents(l)

        msgs = []
        cur, since = st.get("who", "UNATTRIBUTED"), int(st.get("since", 0))
        announced = set(st.get("announced", []))
        win, winwho = lines[-40:], who[-40:]
        gaps = 0
        secs = [int(h)*3600+int(m)*60+int(x) for h, m, x in re.findall(r"\[(\d\d):(\d\d):(\d\d)\.", "".join(raw[-40:]))]
        for i in range(1, len(secs)):
            if secs[i] - secs[i-1] > 45:
                gaps += 1
        qv = q_score(win, os.path.join(here, "questions.ndjson"))
        score, axes = pulse(win, winwho, extra_friction=min(4.0, gaps * 0.8), third=qv, third_name="Q")
        now_ts = _t.time()
        last_pulse = float(st.get("last_pulse_ts", 0))
        last_score = st.get("last_score")
        last_stage = float(st.get("last_stage_ts", 0))
        last_stream = float(st.get("last_stream_ts", 0))
        last_addr = float(st.get("last_addr_ts", 0))

        # READOUT ONLY, with the arrow. Never gates anything.
        prev = None if last_score is None else float(last_score)
        delta = 0.0 if prev is None else score - prev
        # room turnover holds the score steady; a new person is not degradation
        if any(re.search(p, x, re.I) for x in win[-12:] for p in ARRIVAL_PATS) and prev is not None:
            score, delta = prev, 0.0
        if (abs(delta) >= 0.5) or (now_ts - last_pulse >= 120):
            arrow = "->" if prev is None or abs(delta) < 0.2 else ("up" if delta > 0 else "down")
            word = {"up": "moving", "down": "stalling", "->": "flat"}[arrow]
            msgs.append(f"pulse {score:.1f} {arrow}  {word}")
            with open(os.path.join(here, "pulse.ndjson"), "a") as pf:
                pf.write(json.dumps({"t": _dt.datetime.now(_dt.timezone.utc).strftime("%H:%M:%S"),
                                     "pulse": round(score, 2),
                                     "axes": {k: round(v, 2) for k, v in axes.items()}}) + "\n")
            last_pulse, last_score = now_ts, score
        if score >= 6.5 and now_ts - last_stage >= 180:
            anchor = max(win, key=lambda x: stream_row(x)[1]) if win else ""
            stage("staged", "window", min(1.0, score / 10.0), anchor)
            msgs.append(f"pulse {score:.1f} - STAGED"); last_stage = now_ts

        # TYPED STREAM is classified internally, never printed here.

        if new_lines:
            for s in new_lines:
                an = detect_announce(s)
                if an:
                    cur, since = an, 0
                else:
                    since += 1
                    if cur != "UNATTRIBUTED" and since > ATTR_WINDOW:
                        cur = "UNATTRIBUTED"
                t, c = stream_row(s)
                if t == "yes":
                    stage("agreed", t, c, s, who=cur)
                if t in ("verb", "noun"):
                    stage("insights", t, c, s, who=cur)
                if is_candidate(s):
                    stage("candidates", t, c, s, who=cur)
            if any(is_agree(s) or is_selflabel(s) or is_problem(s) or ADDRESSED.search(s) for s in new_lines):
                top = pick_top(emit(win, winwho))
                prob = next((s for s in reversed(new_lines) if is_problem(s)), None)
                if top and top["quote"] not in announced:
                    announced.add(top["quote"])
                    stage("intents" if (is_selflabel(top["quote"]) or re.search(r"\b(want|need|should|let'?s|going to)\b", top["quote"], re.I)) else "insights",
                          "intent", stream_row(top["quote"])[1], top["quote"], who=top["who"])
                    nm = f' - {top["who"]}' if top["who"] != "UNATTRIBUTED" else ""
                    # say which bin it is headed for: intents (what someone wants) or insights (what is now true)
                    lane = "intent" if (is_selflabel(top["quote"]) or
                                        re.search(r"\b(want|need|should|let'?s|going to)\b", top["quote"], re.I)) else "insight"
                    msgs.append(f'catch -> {lane}: "{top["quote"][:110]}"{nm}')
                elif prob and prob not in announced:
                    announced.add(prob); msgs.append(f'CAUGHT (problem): "{prob[:110]}"')
                elif any(ADDRESSED.search(s) for s in new_lines) and now_ts - float(st.get("last_addr_ts", 0)) > 90:
                    msgs.append("CAUGHT: you called me. Listening."); last_addr = now_ts

        idle = 0 if new_lines else int(st.get("idle", 0)) + 1
        if idle and idle % 60 == 0:
            msgs.append(f"FEED STALLED (~{idle*3//60} min, no new lines) - {total} lines")
        json.dump({"pos": total, "who": cur, "since": since, "idle": idle,
                   "announced": list(announced)[-200:], "last_pulse_ts": last_pulse,
                   "last_score": last_score, "last_stage_ts": last_stage,
                   "last_stream_ts": last_stream, "last_addr_ts": last_addr}, open(statef, "w"))
        for m in msgs:
            print(m)
        return

    sample = lines[-a.last:]
    counts = {}
    for s, w in zip(sample, who[-len(sample):] if sample else []):
        t, c = stream_row(s)
        counts[t] = counts.get(t, 0) + 1
        if t == "yes":
            stage("agreed", t, c, s, who=w)
        if t in ("verb", "noun"):
            stage("insights", t, c, s, who=w)
        if is_candidate(s):
            stage("candidates", t, c, s, who=w)
    print(f"=== {len(sample)} lines === {counts}")


if __name__ == "__main__":
    main()
