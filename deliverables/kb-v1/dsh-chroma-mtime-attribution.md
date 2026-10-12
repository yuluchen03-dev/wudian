# Production Chroma — the 12:13:23 mtime anomaly, attributed

An unexplainable production change is a FAIL by governance. This document
attributes the anomaly instead of hand-waving it.

## 1. The anomaly

During this session `backend/chroma_db/chroma.sqlite3` showed a **different
SHA-256** than the value recorded in earlier rounds:

```
earlier recorded : 4120576 / DDDFBE1BA0249309
observed now     : 4120576 / FD7FD35536A1F10A   (stable over 3 re-hashes)
same size, mtime = 2026-10-12 12:13:23
```

Size identical, hash different, and the mtime falls inside this session → this
required explanation, not dismissal.

## 2. Mechanism — proven

**chromadb rewrites `chroma.sqlite3` merely on OPEN, even with no query and no
write.** Proof on a copy (production never touched):

```
copy BEFORE open: (4120576, 'fd7fd35536a1f10a', mtime=1791774803)
  count = 143                      <-- read-only intent; no query, no build
copy AFTER  open: (4120576, '1763a79b5f302adf', mtime=1791777035)
MUTATED_BY_OPEN = True
production during the test: unchanged (fd7fd35536a1f10a / mtime=1791774803)
```

`eval/scripts/run_eval.py:46-48` already documents this exact behaviour:

> chromadb 在**打开时即写入目录元数据**，因此即使是只读评测也会改动生产文件；
> 更危险的是任何 force rebuild 会清空生产数据。

So any code path that instantiates a `PersistentClient` against
`backend/chroma_db` — even to merely read — rewrites the file and moves its
mtime/hash. The **bytes on disk are re-written by SQLite/chroma bookkeeping**,
not by any content change: the collection still reports `count = 143` both
before and after, and all my functional measurements reproduce exactly
(recall@5 = 22/40, E = 12/12, etc.).

## 3. Exoneration of this session's probe paths

Every probe I ran sets `CHROMA_PERSIST_DIR` to an isolated temp copy first.
Verified directly, with fingerprinting around each step:

```
BEFORE:                                            4120576/fd7fd35536a1f10a/mtime=1791774803
after `import metrics` (eval/scripts):             unchanged
after `import app.services.rag_service`:           unchanged
collection count 143, persist dir = %TEMP%\...\chroma
after `retrieve_for_sage_chat(...)`:               unchanged
FINAL:                                             4120576/fd7fd35536a1f10a/mtime=1791774803
```

Also verified: the isolated-env path leaves production byte-identical
(`rm006_prod_safety.py`, `rm006_attribution.py`), and production is currently
**stable** at `fd7fd35536a1f10a / mtime=1791774803` across three consecutive
re-hashes and across every subsequent probe.

## 4. Honest conclusion

- **Attributed:** the mechanism is chromadb's open-time metadata write,
  documented in-repo and reproduced on a copy. It is not a content change and
  not caused by this session's probes (all of which use isolated copies).
- **NOT attributed:** *which* process opened production at 12:13:23. Candidates
  are: (a) an earlier/parallel agent or reviewer turn whose import path did not
  isolate before a client was constructed, (b) `conftest.py`'s fallback path, or
  (c) any manual/IDE action. I could not reproduce a session probe that opens
  production, so I am **not** claiming a culprit I cannot prove.
- **Integrity status:** the ledger therefore needs a correction — the previously
  recorded hash `DDDFBE1BA0249309` is stale. The authoritative check is now
  **size 4120576, count 143, content-stable**, and the associated data files are
  byte-identical to their long-standing values:

```
data_level0.bin       167600  2A3617E926A15F45   (unchanged)
header.bin               100  A0E81C3B22454233   (unchanged)
index_metadata.pickle    124  F2F8EBED3E12A7E2   (unchanged)
length.bin               400  FC0C4D072FAD2808   (unchanged)
link_lists.bin             0  E3B0C44298FC1C14   (unchanged)
```

  Only `chroma.sqlite3` (the SQLite bookkeeping file) changed hash, and that is
  precisely the file chromadb rewrites on open.

## 5. Consequence for the gate verdicts

This does **not** invalidate any metric: the vector index itself
(`data_level0.bin` / `header.bin` / `length.bin`) is byte-identical, and every
functional value reproduces. It **does** mean:

- a pure size+hash fingerprint is **not** a sufficient production-safety proof
  for chromadb (governance already says fingerprints are not semantic proof —
  this is a concrete instance);
- the fingerprint ledger must record the open-time-write caveat;
- any future production-open must be treated as a **write** and logged as such.
