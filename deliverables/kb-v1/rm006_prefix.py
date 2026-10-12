"""RM-006: test the prefix-normalization defect documented at rag_service.py:1367.

Claim in the code comment: gold ids are `debate:{sage}:{bare}` (two prefixes) but
the frozen `normalize_passage_id` strips only ONE prefix, so
  gold:  debate:laozi:daodejing-22-01 -> laozi:daodejing-22-01
  bare:  daodejing-22-01             -> daodejing-22-01
  => never equal (structural miss)
and the output layer PAPER-OVER is to emit the prefixed form so both sides
normalise to the same string.

Check against the ACTUAL gold file what form is used, and verify the frozen
normalizer behaviour directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EVAL = Path(r"D:\systemDir\Desktop\悟典\eval")
sys.path.insert(0, str(EVAL / "scripts"))
from metrics import normalize_passage_id as N  # noqa: E402

gold = [json.loads(l) for l in
        (EVAL / "retrieval_gold.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]

print("=== all distinct gold id FORMS ===")
forms = {}
for g in gold:
    for p in g["expected_passage_ids"]:
        n = p.count(":")
        forms.setdefault(n, []).append(p)
for k in sorted(forms):
    print(f"  colons={k}  count={len(forms[k])}  e.g. {forms[k][:4]}")

print("\n=== frozen normalize_passage_id behaviour ===")
for s in ["lunyu:4.16", "debate:laozi:daodejing-22-01",
          "daodejing-22-01", "laozi:daodejing-22-01"]:
    print(f"  {s:34s} -> {N(s)!r}")

print("\n=== would a two-prefix gold ever match a bare observed id? ===")
cases = [
    ("debate:laozi:daodejing-22-01", "daodejing-22-01"),
    ("debate:laozi:daodejing-22-01", "laozi:daodejing-22-01"),
    ("lunyu:4.16", "4.16"),
    ("lunyu:4.16", "lunyu:4.16"),
]
for gid, obs in cases:
    print(f"  gold={gid:34s} obs={obs:26s} N(gold)={N(gid):24s} "
          f"N(obs)={N(obs):24s} match={N(gid) == N(obs)}")
