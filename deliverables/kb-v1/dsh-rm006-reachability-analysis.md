# DSH-RM-006 — retrieval reachability analysis (captain, static)

Current Gate: DSH-RM-006
Functional Task: RETRIEVAL-RECALL
Method: **source and dataset reading only — no command executed**
Status: partial analysis. Supersedes nothing; complements t19.

Purpose: answer the question that decides whether RM-006 is winnable — how many of
the 40 recall cases are reachable **in principle** from the current corpus. If
fewer than 36 are, the target is mathematically unreachable and the honest outcome
is `BLOCKED_BY_CORPUS`.

## The dataset

`eval/retrieval_gold.jsonl`, 40 records, `rg-0001` … `rg-0040`. Every record
carries `expected_passage_ids`, `expected_books`, `difficulty`, and a
`generation_method` that reads:

> `"rule/table-assisted construction + author mapping; not human-annotated"`

That provenance label matters and is recorded honestly: **this Gold is derived,
not human-annotated.** It is authoritative for the gate (the goal freezes it), but
"Gold" here means "the frozen expectation", not "verified ground truth".

Composition by expected book:

| Book | Records | IDs |
|---|---|---|
| 论语 | 26 | rg-0001…0020, 0031…0038, 0039, 0040 |
| 道德经 | 4 | rg-0021…0024 |
| 墨子 | 2 | rg-0025, 0026 |
| 韩非子 | 4 | rg-0027…0030 |
| mixed (论语 + 朱熹集注) | 1 | rg-0017 |

**Note the shape:** 26 of 40 are 论语, and `retrieve_for_sage_chat` (Gate F's entry
point) queries a **single unfiltered collection** — it does not take a `sage_key`.
So the four-school cases compete against a corpus dominated by 论语 entries. That
is a structural disadvantage for `rg-0021…0030` that no threshold tuning fixes.

## A suspected Gold error — investigated and CLEARED

`rg-0039` expects `["lunyu:18.x"]`. The `.x` suffix looked like a placeholder or a
typo, which would have been an objective Gold error worth escalating under the
Gold-governance rule.

**Verified it is real.** `data/processed/lunyu.json` contains an actual verse with
`"verse_id": "18.x"` (`:2268`), in chapter 18 微子, whose text is:

> 楚狂接舆歌而过孔子曰：「凤兮凤兮！何德之衰？**往者不可谏，来者犹可追。**已而
> 已而！今之从政者殆而！」

That is exactly the passage `rg-0039`'s note cites (往者不可谏来者犹可追), and the
query is `总是后悔过去的选择`. **Gold is correct; the case is reachable in
principle.** Recorded because it is the kind of thing that looks like a Gold bug and
would otherwise be "fixed" by editing Gold — which is forbidden and would have been
wrong.

## RESOLVED — every Gold passage exists in the corpus

This was the decisive open question, and it **is answerable without execution**.

**Two independent confirmations:**

**(1) An existing frozen test asserts it.** `backend/tests/test_eval_baseline.py:115-120`:

```python
def test_all_expected_passage_ids_resolve(corpus_index):
    """Cross-check every dataset entry against the real corpus."""
    for name in S.DATASET_NAMES:
        for rec in S.load_jsonl(EVAL_DIR / S.DATASETS[name]["file"]):
            for ref in rec.get("expected_passage_ids", []) or []:
                assert ref in corpus_index, f"{name}:{rec.get('id')} bad ref {ref}"
```

This asserts that **every** `expected_passage_id` in **every** dataset resolves
against the real corpus. It is part of the frozen eval-fidelity suite, so it is a
standing guarantee, not a one-off check.

**(2) Manually verified for the four-school cases**, which were the real risk since
they live in a separate file (`data/processed/debate_classics.json`, loaded by
`rag_service.py:536-583`). All 21 debate-classic IDs are present, including every
one the 40 Gold records expect:

| Gold expectation | Corpus ID | Present |
|---|---|---|
| `rg-0021`, `rg-0022` | `daodejing-22-01`, `daodejing-33-01` | yes |
| `rg-0022`, `rg-0024` | `daodejing-08-01` | yes |
| `rg-0023` | `daodejing-44-01` | yes |
| `rg-0025` | `mozi-jianai-01`, `mozi-jianai-02` | yes |
| `rg-0026` | `mozi-feile-01` | yes |
| `rg-0027` | `hanfeizi-youdu-01` | yes |
| `rg-0028` | `hanfeizi-erbing-01` | yes |
| `rg-0029` | `hanfeizi-wuzhu-01` | yes |
| `rg-0030` | `hanfeizi-wai-chu-shuo-01` | yes |

Plus `rg-0039`'s `lunyu:18.x`, verified earlier against
`data/processed/lunyu.json:2268`.

## Conclusion: `BLOCKED_BY_CORPUS` does NOT apply

**Every one of the 40 Gold passages exists in the corpus.** Therefore no RM-006
miss can be attributed to corpus absence, and the target of 36/40 is **not
mathematically unreachable**. RM-006 is a genuine **retrieval** problem, and the
honest engineering outcome is to fix retrieval — not to declare a corpus blocker
and not to edit Gold.

This is a strong and useful negative result. It **removes** the escape hatch:
0.90 must be reached by improving retrieval, and there is no defensible
`BLOCKED_BY_CORPUS` claim available for any of the 40 cases.

What remains genuinely unknown is only the **identity of the 18 misses** — which
requires executing `retrieve_for_sage_chat` and comparing through the frozen
`normalize_passage_id`. Reading cannot supply it.

## What this establishes

1. **No Gold error was found in this pass.** One candidate was checked and cleared.
   This is a negative result, stated as such — it does not prove Gold is clean.
2. **The corpus contains the content for at least one hard case** (`rg-0039`,
   difficulty `medium`), so its miss is a **retrieval** failure, not corpus absence.
3. **The school imbalance is structural**: 26/40 论语 against a single unfiltered
   collection for Gate F. This is a candidate explanation for clustered misses in
   `rg-0021…0030` and belongs to fix-order steps 1-4 (ID/canonical/metadata/query),
   not to threshold tuning.

## What CANNOT be established without execution

I can read Gold and the corpus; I **cannot** determine which cases currently miss,
because that requires running `retrieve_for_sage_chat` and comparing against
`expected_passage_ids` through the frozen `normalize_passage_id`. So the critical
number — *how many of the 40 are reachable* — remains **UNKNOWN**.

Specifically unknown:
- Which 18 of 40 currently miss (baseline is 22 hits, but the *identity* of the
  misses is unrecorded).
- Whether any miss is genuine corpus absence versus retrieval failure.
- Whether the 26/40 论语 concentration causes the four-school cases to be crowded
  out.

**I am not going to guess these.** The single most valuable measurement for RM-006
is a per-case miss table, and it needs a shell.

## The one thing t19 must produce

Of everything t19 was asked for, the decisive output is a table of all 40 cases
marked **hit / miss** with the retrieved IDs, so the misses can be classified. The
captain-side contribution here is the caveat that must accompany it: **a case
counts as reachable only if its Gold passage actually exists in the corpus.**
`rg-0039` shows that check cannot be skipped — it looks like a typo and is not.
For every miss, the first question must be "is the Gold passage in the corpus?",
not "what should we tune?".

## Standing caution for whoever implements RM-006

`retrieve_for_sage_chat:1329-1334` **already implements two-layer fusion**, added by
FIX-003 because the pure-vector baseline was 0.325. Fix-order steps 7-9
(BM25/dense/fusion) are therefore **not greenfield** and must be **measured before
being changed**. The comment at `:1329-1331` records that the fusion exists
*precisely* because hash embedding is non-semantic. Re-tuning an unmeasured fusion
layer is how 0.55 becomes 0.40.
