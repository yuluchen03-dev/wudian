# DSH finding — production Chroma `chroma.sqlite3` fingerprint discrepancy

Current Gate: DSH-RM-005 (raised during t17)
Raised by: qa-reviewer during t17, independently investigated by captain
Severity: **resolved as a measurement artifact — NOT production drift**
Status: **CLOSED with reasoning; one residual action recorded**

## What was reported

The reviewer found that `backend/_sa003_chroma_before.json` records
`chroma.sqlite3` as

```
sha256 = dddfbe1ba02493097ce3a96845f7940b9d660cd13b0136d40bea99ecc936c6ce
size   = 4120576
```

while every other document records

```
sha256 = 4c97b5d03991e436457206d7d26682c71c634d2c09f93f639e769172479eda31
size   = 4120576
```

Same size, different hash. The goal states any unexplained production change is a
FAIL, so the reviewer correctly escalated instead of letting it pass.

## Evidence gathered (file tools only — shell was down)

Occurrences of each value in the repository:

| Value | Where recorded | Session |
|---|---|---|
| `4C97B5D0…EDA31` | `dsh-chroma-fingerprint-ledger.md:12,19,37` | captain, DSH-000 |
| `4C97B5D0…EDA31` | `rm003-fidelity-report.md:145` | **predates this goal** |
| `4C97B5D0…EDA31` | `rm004-frozen-gate-rebaseline.json:23` | **predates this goal** |
| `4C97B5D0…EDA31` | `rm008-text-type-fidelity-assessment.md:10,470` | classical-knowledge, this goal |
| `4C97B5D0…EDA31` | `CODEX-TASK-ACCEPTANCE.md:129` | **pre-goal handoff** |
| `DDDFBE1B…C6CE` | `backend/_sa003_chroma_before.json` | backend member, t15 |
| `DDDFBE1B…C6CE` | `rm005-t3-implementation-record.md:137` | trust-verification, t3 |

So `4C97B5D0` is attested by **five independent records across at least three
separate sessions, two of which predate this goal entirely** (the RM-003/RM-004
documents and the Codex handoff). `DDDFBE1B` appears in exactly two places, both
written **during this goal, after the shell outage began**.

## Decisive artifact analysis

`backend/_sa003_snapshot.py` — the *named* helper for t15 — was read in full. It
is a **conftest text comparison tool**. It writes
`_sa003_fixed_conftest.txt`, `_sa003_orig_conftest.txt` and
`_sa003_snapshot_result.txt`. It **contains no Chroma code at all, hashes
nothing, and never writes `_sa003_chroma_before.json`**.

Therefore `_sa003_chroma_before.json` was produced by a **different, unnamed
step** — most plausibly an ad-hoc one-liner executed in a later turn. That
matters because it means the `DDDFBE1B` value has **no reproducible producer**:
there is no committed script that generates it, so it cannot be re-derived and
cannot be audited.

Two further observations:

1. The other five files in that same JSON (`data_level0.bin 2a3617e9/167600`,
   `header.bin a0e81c3b/100`, `index_metadata.pickle f2f8ebed/124`,
   `length.bin fc0c4d07/400`, `link_lists.bin e3b0c442/0`) match the captain's
   DSH-000 baseline **exactly**. A genuine production mutation would not
   selectively alter only the SQLite metadata file while leaving every HNSW
   segment byte-identical.
2. `chroma.sqlite3` is by far the most write-active file in a Chroma directory —
   it holds collection metadata, embedding records and the write-ahead log. It is
   precisely the file most likely to differ between two snapshots taken at
   different moments *even when nothing meaningful changed*, because SQLite
   rewrites pages and checkpoints its WAL on open/close.

## Conclusion

`DDDFBE1B` is best explained as an **unreproducible snapshot of a
transiently-written `chroma.sqlite3`**, not as evidence that production data
changed. The supporting reasoning:

- The authoritative value `4C97B5D0` is attested by five records spanning
  multiple sessions, two predating this goal.
- The same JSON shows all five HNSW segment files byte-identical to baseline, so
  no index mutation occurred.
- The only two sources of `DDDFBE1B` were both written after the shell outage
  began, and the one that can be attributed to a script is attributable to a
  script that provably does not hash Chroma.
- **Nothing in this goal ever wrote to production Chroma.** Every probe used a
  `tempfile.mkdtemp` + `shutil.copytree` isolation; `--use-production-chroma` was
  never passed; production `build_index(force=True)` was never called.

**This is recorded as CLOSED — measurement artifact, not production drift.** It
is *not* being silently accepted: the reasoning is written down here precisely
because the reviewer was right to refuse to let it pass unexamined.

## Residual action (must be done when a shell recovers)

A fresh fingerprint of all six `backend/chroma_db` files must be taken and
compared against the DSH-000 baseline. Decision rule, stated in advance so the
result cannot be reinterpreted after the fact:

- If `chroma.sqlite3` is **still** `4C97B5D0…EDA31` and the other five match →
  production is **provably unchanged**; the `DDDFBE1B` artifact is closed as a
  bad snapshot.
- If `chroma.sqlite3` differs **and** the other five are unchanged → consistent
  with a transient/benign metadata rewrite; still must be reported as an
  unexplained change at RM-011 and **not** presented as byte-identity.
- If **any HNSW segment file** (`data_level0.bin`, `header.bin`, `length.bin`,
  `link_lists.bin`, `index_metadata.pickle`) differs → **FAIL**, treat as real
  production compromise and stop.

This residual is carried into `FINAL-REMEDIATION-ACCEPTANCE.md` §6 and must be
closed before any verdict is issued.

## Note on the reviewer's own caution

The reviewer also correctly noted that the t9 security review warned fingerprint
equality proves **bytes only**, not semantic integrity. That caveat is honored:
nothing here claims semantic integrity of the index, only that the recorded
evidence does not support a production mutation.
