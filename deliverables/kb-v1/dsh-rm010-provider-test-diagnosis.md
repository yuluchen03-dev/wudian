# DSH-RM-010 — `test_default_provider_is_openai` failure diagnosis (captain, static)

Current Gate: DSH-RM-010
Functional Task: FULL-REGRESSION — attribution of the single backend failure
Method: **source reading only — no command executed**
Status: **diagnosed as ENVIRONMENTAL — not a regression.** The goal explicitly
requires this attribution to be made rather than assumed, and forbids writing
"all backend tests pass".

## The requirement

The goal states the historical backend result as `522 PASS + 1 FAIL`, with the
failure being `test_default_provider_is_openai`, and requires deciding whether it is
a **pre-existing environment mismatch** or a **current regression**. It also
forbids changing the product's default provider just to make a test pass.

## The chain, fully traced

| Step | Evidence |
|---|---|
| Code default | `config.py:56` — `LLM_PROVIDER: str = "openai"` |
| Settings loads a dotenv file | `config.py:12` — `env_file=".env"` |
| The dotenv sets a different value | `backend/.env:25` — `LLM_PROVIDER=agnes` |
| The test uses no overrides | `test_ai_provider.py:141` — `settings = Settings()` |
| The assertion | `test_ai_provider.py:142` — `assert settings.LLM_PROVIDER == "openai"` |

Since pydantic `BaseSettings` resolves `env_file` **into the object it returns**,
`Settings()` picks up `.env` and yields `LLM_PROVIDER == "agnes"`. The assertion at
`:142` then fails — not because the code default changed, but because the
**environment overrides it**.

**Verdict: pre-existing environment mismatch. Not a regression.** The code default
is still `"openai"` exactly as the test expects; the value observed at runtime comes
from an untracked local `.env`.

## Corroborating evidence from the same test class

Every neighbouring test in the file **passes explicit keyword arguments** to
`Settings(...)` rather than relying on the environment — e.g. `:130-136` passes
`LLM_PROVIDER="agnes"` and the associated keys explicitly. Those tests are
environment-independent and pass.

The failing test is the **only one** in the class that constructs a bare
`Settings()`. So the test is asserting a *code* default while being executed in an
*environment* that overrides it. That asymmetry is the whole defect, and it is a
test-fragility issue, not a product defect.

## Why the fix must NOT be to change the provider

The goal forbids changing the product default provider to make the test pass
("不要为了测试通过改产品默认 provider，除非 contract 明确要求"). That is the correct
call: `LLM_PROVIDER="openai"` is the documented code default, and `.env` is a
**local, untracked, deployment-specific** file. Changing `config.py:56` to `agnes`
would hard-code one deployment's choice into the product.

If this test is ever fixed, the correct fix is one of:
1. pass an explicit `LLM_PROVIDER="openai"` in the test, mirroring its neighbours; or
2. isolate the test from `env_file` (e.g. point `env_file` at a fixture).

Both are **test-side** changes. Neither is authorised by this goal, so **no change
was made** — this document is a diagnosis only.

## Honest limits

This attribution is established by **reading the source chain**, not by running the
suite. What it does not prove:

- That the suite is otherwise green. `522 PASS` is a historical figure; re-running
  is required before quoting any count.
- That this is the *only* failure. Other failures could exist that the historical
  record predates.
- That `backend/.env` is the only source. An exported shell variable or CI variable
  could also set `LLM_PROVIDER`, producing the same outcome — the same conclusion
  holds either way.

**Reporting rule, reaffirmed:** the backend result must **never** be written as
"all backend tests pass". The accurate form is
`N PASS + 1 FAIL with the failure attributed to environment`, where `N` is
re-measured rather than carried forward.
