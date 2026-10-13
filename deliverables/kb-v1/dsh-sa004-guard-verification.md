# DSH-SA-004 — destructive-guard verification (captain, static)

Current Gate: DSH-SA-004
Functional Task: DESTRUCTIVE-OPERATION-GUARD
Method: **source tracing only — no command executed**
Purpose: t16 implemented an 18-table destructive guard but could not execute it.
This document verifies the guard by tracing its logic against the **real
production path**, which is the only question that matters for a safety control.

## Why this is worth doing without execution

t16's own report says it is `0% executed`. For a *feature* that is merely
incomplete evidence. For a **safety control** it is more serious: an unverified
guard protecting the production database is indistinguishable from no guard, if
its allow-list is wrong. So the specific question is not "do the tests pass" but
**"would this guard actually stop the real production wipe?"** That is answerable
by tracing, and I traced it.

## The production target, resolved

`config.py:34` sets the default:

```python
DATABASE_URL: str = "sqlite+aiosqlite:///./wudian.db"
```

`resolved_database_url` (`:173-186`) pins relative SQLite paths to the backend
directory, so the real resolved URL is
`sqlite+aiosqlite:///D:/systemDir/Desktop/悟典/backend/wudian.db`.

## Trace through the guard

`ensure_destructive_allowed` (`init_db.py:138-185`):

1. `url = settings.resolved_database_url`
   → `sqlite+aiosqlite:///D:/…/backend/wudian.db`
2. `db_file = _resolve_db_file(url)` (`:102-113`)
   → splits on `:///` → `D:/…/backend/wudian.db` → absolute → `.resolve()`
   → `<repo>/backend/wudian.db`
3. `env = settings.APP_ENV`, `confirmed = env var or _CLI_CONFIRMED`
4. Problem checks (`:149-168`), evaluated in order:

| Check | Result for production `wudian.db` | Fires? |
|---|---|---|
| `db_file is None` | not None | no |
| `name in _FORBIDDEN_DB_NAMES` (`("wudian.db",)`) | **`"wudian.db" == "wudian.db"`** | **YES** |
| `not _is_allowed_target(...)` | `_is_allowed_target` returns False (forbidden name short-circuits at `:130-131`) | would also fire |
| `env == "production"` | only if APP_ENV=production | maybe |
| `not confirmed` | only if no `--yes` | maybe |

5. Because at least one problem exists, `:170-171` **raises
   `DestructiveOperationRefused`** before any DELETE.

**Conclusion: yes — the guard blocks the real production database, and it does so
on the forbidden-name check, which is independent of `--yes` and of `APP_ENV`.**

## Defence in depth confirmed

Three independent layers would each have to fail:

1. **Forbidden-name list** (`:95`, `:130-131`) — name-based, not bypassable by
   `--yes`.
2. **Allow-list** (`:91-92`, `:132-135`) — positive identification required;
   fail-closed for anything unrecognised.
3. **Directory containment** (`:124-125`) — the target must live under
   `BACKEND_DIR`.

Plus `APP_ENV=production` refusal (`:163-164`) and the explicit-intent
requirement (`:165-168`).

## The critical design decision, verified correct

The comment at `:88-90` explains that `wudian.db` was deliberately **excluded**
from the allow-list, and placed in `_FORBIDDEN_DB_NAMES` instead:

> 把它放进白名单会让 `--yes` 直接清空生产库，违背 fail-closed。

This is the difference between a guard and a speed bump. Had `wudian.db` been
allow-listed as a "_dev"-style target, `python init_db.py --yes` would have wiped
production. The implementer initially made exactly that mistake and caught it
before submitting. **That self-caught near-miss is the single most valuable thing
in t16**, and it is recorded here because a future editor "simplifying" the
allow-list would reintroduce it.

## Guard placement, verified

- `clear_data` (`:200-236`): `ensure_destructive_allowed(session)` is at `:208`,
  the **first statement**, with an explicit comment `:207` forbidding the addition
  of any DELETE above it. The 18 DELETEs run at `:234`. **Verified: no DELETE can
  precede the guard.**
- `main()` (`:664`): calls `ensure_destructive_allowed(None)` **before** any
  destructive path, so the CLI refuses early rather than mid-operation.

## What remains genuinely unverified (honest limits)

1. **The 18 tests have never run.** They may contain syntax errors or wrong
   assertions. This trace validates the *implementation*; it says nothing about
   the *tests*. t16 stays unverified for that reason.
2. **`Optional`/`List` imports — VERIFIED PRESENT AND USED.** t16 self-reported
   fixing a missing-import bug that would have raised `NameError`. Confirmed by
   reading: `init_db.py:21` has `from typing import List, Optional`, and both names
   are genuinely used — `Optional[Path]` at `:102` and `:116`, `List[str]` at
   `:192`. **The `NameError` risk is closed.** This was checked specifically
   because a guard that raises `NameError` mid-operation would be worse than a
   clearly absent one; it is not that.
3. **`_CLI_CONFIRMED` timing** (`:189`, set by `__main__` after argv parsing) —
   correct if `clear_data` is only reached via `main()`; a direct programmatic call
   to `clear_data` would see the default `False`, which is the fail-closed
   direction. Verified as safe, but the ordering deserves a test.
4. **The `session` parameter is unused** in `ensure_destructive_allowed` — it
   validates against settings, not the live session. That is a *design choice*
   (it means the guard cannot be fooled by a session bound elsewhere, but also
   cannot verify the session's actual target). Worth noting, not a defect.

## Verdict

**Implementation: verified sound by source trace, including the production path.**
**Tests: unexecuted — no evidence.** t16 remains **IMPL — UNVERIFIED**, not FAIL
and not PASS. The safety question the guard exists to answer is answered
affirmatively: the production database cannot be wiped by this path.
