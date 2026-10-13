# DSH-SA-003 — test DATABASE_URL isolation guard (captain, static)

Current Gate: DSH-SA-003
Functional Task: TEST-DB-ISOLATION
Method: **source tracing only — no command executed**
Purpose: t15 implemented the guard and reported a completed RED/GREEN cycle before
the outage, but could not finish the full-suite attribution. This verifies the
implementation by reading.

## The defect being fixed

The original code used `os.environ.setdefault("DATABASE_URL", …)`. A `setdefault`
is a **no-op when the variable is already present**, so any developer shell, CI
variable or `.env` that exported `DATABASE_URL` pointing at the real database
would cause the entire test suite to inherit it — creating tables and writing rows
into production data, with **no warning**. The same class of bug existed for
`CHROMA_PERSIST_DIR` and is documented in-source as the cause of the 2026-10-08
HNSW index corruption (`data_level0.bin 167600 → 958672`, `conftest.py:80-81`).

This is a genuine safety defect, not a style issue: it silently redirects
destructive test activity onto production assets.

## Verification by reading

`backend/tests/conftest.py:58-69`:

```python
_ISOLATED_DB_URL = f"sqlite+aiosqlite:///./test_wudian_{_PID}.db"

_inherited_db_url = os.environ.get("DATABASE_URL")
if _inherited_db_url and _inherited_db_url != _ISOLATED_DB_URL:
    print(
        "\n[SAFETY-001/DB] 检测到继承的 DATABASE_URL："
        f"{_inherited_db_url}\n"
        f"    已强制改用本进程隔离测试库 {_ISOLATED_DB_URL}，"
        "以免测试对真实数据库建表/写入。\n",
        file=sys.stderr,
    )
os.environ["DATABASE_URL"] = _ISOLATED_DB_URL
```

| Property | Verified |
|---|---|
| No longer `setdefault` | **Yes** — `:69` is an unconditional assignment |
| Inherited value detected | **Yes** — `:60` reads it before overwriting |
| Warning on unsafe inheritance | **Yes** — `:61-68`, to **stderr** |
| Per-process isolation | **Yes** — `_PID` suffix (`:58`), preventing concurrent races |
| Relative path preserved | **Yes** — deliberately `./test_wudian_{_PID}.db`, because an absolute path would break `test_hackathon_readiness.py`'s `startswith(backend_root)` assertion (`:54-56`) |

The comment at `:50-56` documents that this now uses **the same two rules** as
`CHROMA_PERSIST_DIR`, so the two isolation mechanisms can no longer diverge. That
consistency is the real fix: previously one was hard-assigned and the other was
`setdefault`, so the DB guard was airtight while the Chroma guard leaked.

## Ordering, verified safe

The assignment at `:69` executes at **import time**, before any test can run and
before `from app.main import app` (line 40, per the comment at `:74`) triggers
startup logic that reads the setting. So the guard cannot be raced by a
module-scope import. The warning is printed to `stderr` rather than `stdout`, so it
cannot be swallowed by test output capture.

## What remains genuinely unverified

1. **The full-suite attribution.** t15 completed its own RED/GREEN cycle
   (`8 failed` → `8 passed`, plus `33 passed` on verify(1)), but could not confirm
   that no *other* test depends on inheriting `DATABASE_URL`. That is the open
   item. It requires running the full suite, not reading.
2. **`test_conftest_db_isolation.py` (9,297 B) has never run.**
3. **The warning path is untested** — no evidence that a foreign `DATABASE_URL`
   actually produces the message and still gets overridden.

## Verdict

**Implementation: verified sound by source trace.** The `setdefault` asymmetry is
gone, the guard is unconditional, per-process, and warns to stderr.
**Full-suite attribution: absent.** t15 stays **IMPL — partial verification**, not
PASS. The specific claim that *other* tests do not depend on the inherited value
remains untested and should not be asserted.

## Note on the shared pattern

t15, t16 and t18 all failed for the same reason and all left behind *correct
implementations with absent execution evidence*. The consistent captain position
across all three: **source-traced soundness is recorded as such and given no
verdict above `IMPL — UNVERIFIED`.** Reading proves what the code does; only
execution proves that it does it.
