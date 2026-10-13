#!/usr/bin/env python3
# grounded-check.py  -  the gate on the whole pipeline.
# The law: any measure you can edit, you are not graded by. A node without its
# verbatim quote does not exist and must not move the number.
#
# Reads a nodes file (one JSON object per line). FAILS (exit 1) if:
#   - ANY node carries no quote (empty/whitespace "line" or "q"), or
#   - --claim N is given and N != the count of quote-grounded nodes (the % is not earned).
# PASS (exit 0) only when every node carries a quote and any claim matches.
#
# Usage: python3 grounded-check.py <nodes.ndjson> [--claim N]

import sys, json, argparse

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--claim", type=int, default=None)
a = ap.parse_args()

nodes = []
for ln in open(a.file, encoding="utf-8"):
    ln = ln.strip()
    if not ln:
        continue
    nodes.append(json.loads(ln))


def quote_of(n):
    return str(n.get("line", n.get("q", ""))).strip()


total = len(nodes)
grounded = [n for n in nodes if quote_of(n)]
ungrounded = total - len(grounded)

fail = False
if ungrounded > 0:
    print(f"FAIL: {ungrounded} of {total} nodes carry no quote. A node without its quote does not exist.")
    fail = True
if a.claim is not None and a.claim != len(grounded):
    print(f"FAIL: board claims {a.claim} quote-grounded nodes; only {len(grounded)} carry a quote. The number is not earned.")
    fail = True

if fail:
    sys.exit(1)
print(f"PASS: {len(grounded)} nodes, every one carries a verbatim quote"
      + (f"; claim {a.claim} matches." if a.claim is not None else "."))
