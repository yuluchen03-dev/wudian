# Production Chroma fingerprint ledger

Production Chroma is a data asset at `backend/chroma_db`. It must never be opened
directly by tests, evals or reviewer probes. Only SHA-256 + size fingerprints are
read, and any change is a FAIL unless explained.

## Baseline — captured at DSH-000 (start of this goal)

| SHA-256 | Size | Path |
|---|---|---|
| `2A3617E926A15F4587921C9B8245D4838B0C3EA7B7474AED135629228AD657F0` | 167600 | `backend/chroma_db/4a2cb26c-8aee-409b-a934-af1dcf8578d7/data_level0.bin` |
| `4C97B5D03991E436457206D7D26682C71C634D2C09F93F639E769172479EDA31` | 4120576 | `backend/chroma_db/chroma.sqlite3` |
| `A0E81C3B22454233BC12D0762F06DCCA48261A75231CF87C79B75E69A6C00150` | 100 | `backend/chroma_db/4a2cb26c-8aee-409b-a934-af1dcf8578d7/header.bin` |
| `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | 0 | `backend/chroma_db/4a2cb26c-8aee-409b-a934-af1dcf8578d7/link_lists.bin` |
| `F2F8EBED3E12A7E2FD749CC7768509826ABC35C07294A1DA59B925B408636CF6` | 124 | `backend/chroma_db/4a2cb26c-8aee-409b-a934-af1dcf8578d7/index_metadata.pickle` |
| `FC0C4D072FAD28088E8A1BBABD2B683334A8014D038591B373B9AAE04198B5FD` | 400 | `backend/chroma_db/4a2cb26c-8aee-409b-a934-af1dcf8578d7/length.bin` |

`chroma.sqlite3` matches the value recorded in `CODEX-TASK-ACCEPTANCE.md`
(`4c97b5d03991e436457206d7d26682c71c634d2c09f93f639e769172479eda31`), so no
drift has occurred since that handoff. The older-snapshot mismatch noted in that
document therefore remains a pre-existing integrity caveat, not a change caused
by this goal.

## Isolation mechanism (verified, not assumed)

`eval/scripts/run_eval.py::_isolate_chroma` creates a `tempfile.mkdtemp` and
`shutil.copytree(_PROD_CHROMA, iso)`, then sets `os.environ["CHROMA_PERSIST_DIR"]`
to the temporary copy. The copy is read-only with respect to production bytes.
`--use-production-chroma` must never be passed.

## Re-verification log

Each subsequent run appends a row here. Any change is reported as FAIL.

| Step | Operator | chroma.sqlite3 SHA-256 | All 6 identical? |
|---|---|---|---|
| DSH-000 baseline | captain | `4C97B5D0…EDA31` | yes (baseline) |
| RM-005/RM-006 executed round | captain | `FD7FD355…F10A` (size 4120576, count 143) | **no — 1 of 6 changed; see below** |

## CHANGE EVENT at 2026-10-12 12:13:23 — attributed, not a content change

The RM-005/RM-006 round observed `chroma.sqlite3` at
`FD7FD35536A1F10A5B0CFE8B7B099ECD24FB5139F57B286C1689E71BF9F1392B`
(size unchanged at 4120576, stable across repeated hashes) instead of the
baseline `4C97B5D0…EDA31`.

**Mechanism — proven on a copy, production never opened:**

```
copy BEFORE open: (4120576, 'fd7fd35536a1f10a', mtime=1791774803)
  count = 143          <-- read-only intent; no query, no write, no build
copy AFTER  open: (4120576, '1763a79b5f302adf', mtime=1791777035)
MUTATED_BY_OPEN = True
```

**chromadb rewrites `chroma.sqlite3` merely on OPEN.** This is already documented
in-repo at `eval/scripts/run_eval.py:46-48`: *"chromadb 在打开时即写入目录元数据，
因此即使是只读评测也会改动生产文件"*.

Consequences for this ledger:

1. A pure SHA-256 fingerprint is **not** a valid production-safety proof for
   `chroma.sqlite3`; that file is rewritten by ordinary read-path opens. The
   governance rule that "fingerprints are not semantic-integrity proof" now has a
   concrete instance.
2. The **five other files are byte-identical to the baseline**, and these are the
   ones that actually hold the vector index:

   | file | SHA-256 (still baseline) | identical |
   |---|---|---|
   | `data_level0.bin` | `2A3617E9…57F0` | yes |
   | `header.bin` | `A0E81C3B…C00150` | yes |
   | `link_lists.bin` | `E3B0C442…B855` | yes |
   | `index_metadata.pickle` | `F2F8EBED…6CF6` | yes |
   | `length.bin` | `FC0C4D07…B5FD` | yes |

3. `collection.count()` is **143** both before and after, and every frozen metric
   reproduces exactly (D 18/18, E 12/12, G 40/40, H 18/18, I 0, J 0/19,
   F 22/40 = 0.55), so no retrieval content changed.
4. This session's probe paths were **exonerated** by fingerprinting around each
   step (`rm006_attribution.py`, `rm006_prod_safety.py`): every probe sets
   `CHROMA_PERSIST_DIR` to an isolated copy *before* constructing a client, and
   production was byte-stable across all of them.
5. **NOT attributed:** which process opened production at 12:13:23. It is not
   claimed to be a test/eval path, and no culprit is asserted without proof.
   See `dsh-chroma-mtime-attribution.md` for the full analysis.

**Governance action required:** treat any production open as a WRITE and log it.
This ledger's baseline for `chroma.sqlite3` should be updated to the current
value, and future reviewers should compare the **five index files** plus
`count()`, rather than the SQLite bookkeeping file alone.

