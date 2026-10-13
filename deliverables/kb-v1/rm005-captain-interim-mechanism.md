# DSH-RM-005 — uq-0009 vs sc-0003 trace (captain-verified)

Current Gate: DSH-RM-005
Functional Task: UNSUPPORTED-REFUSAL
Historical Reference: FIX-002 / earlier RM-005

Status: this is the captain's own line-level reproduction. The rag-expert trace
task (`t2`) produces the full side-by-side report; this document records the
decisive mechanism and is the evidence the implementation task must confront.

## 1. Reproduction method

Probe: `deliverables/kb-v1/dsh-rm005-mechanism.py`
Raw output: `deliverables/kb-v1/dsh-rm005-mechanism-out.txt`

Isolation: `CHROMA_PERSIST_DIR` is pointed at a `tempfile.mkdtemp` copy of
`backend/chroma_db`. Production was never opened; only read for the copy.

## 2. Where the hits come from

For `uq-0009` (`如何面对亲人的离世？`) vector search returns **0** results for all
four sages. Every surviving hit is produced by `_debate_keyword_search`
(`backend/app/services/rag_service.py:526-570`).

That function scores three ways:

```python
for kw in item.get("keywords", []):
    if kw in query or kw in expanded_query:
        score += 3.0                       # (1) corpus keyword is a substring of the query
if query and (query in original or query in translation or query in text):
    score += 4.0                           # (2) whole query appears in the verse
for term in query_terms:
    if term in original:
        score += 1.5                       # (3) query term appears in the original
    elif term in translation or term in text:
        score += 1.0                       # (4) query term appears in translation/text
```

`query_terms` is `_extract_keywords(query) + _extract_keywords(expanded_query)`.
`_extract_keywords` (`rag_service.py:1491-1524`) emits the whole segment, then
**bigrams, then single characters**. For `uq-0009` that produces 28 terms,
including the bare characters `人`, `对`, `世`, `亲`, `离`.

## 3. Exact scoring evidence for uq-0009

| sage | verse | score | sim | reason |
|---|---|---|---|---|
| confucius | `lunyu-taibo-01` | 2.0 | 0.2500 | `term-in-text(人)` ×2 |
| confucius | `lunyu-weilinggong-01` | 2.0 | 0.2500 | `term-in-text(人)` ×2 |
| laozi | `daodejing-33-01` | 3.0 | 0.3750 | `term-in-original(人)` ×2 |
| laozi | `daodejing-22-01` | 2.0 | 0.2500 | `term-in-text(人)` ×2 |
| laozi | `daodejing-08-01` | 2.0 | 0.2500 | `term-in-text(世)` ×2 |
| mozi | `mozi-feile-01` | 2.0 | 0.2500 | `term-in-text(人)` ×2 |
| mozi | `mozi-jianai-01` | 2.0 | 0.2500 | `term-in-text(人)` ×2 |
| mozi | `mozi-feigong-01` | 2.0 | 0.2500 | `term-in-text(对)` ×2 |
| hanfeizi | `hanfeizi-wuzhu-01` | 3.0 | 0.3750 | `term-in-original(世)` ×2 |

Four-sage total for the Gate E hit count: **9 verses**.

Every single surviving hit is justified **only** by a single common character.
`lunyu-taibo-01` is `士不可以不弘毅，任重而道远。` — it has nothing to do with
bereavement; it survives purely because the character `人` is a substring of its
translation text.

## 4. Exact scoring evidence for sc-0003 (the legal control)

| sage | verse | score | sim | reason |
|---|---|---|---|---|
| mozi | `mozi-feigong-01` | 2.0 | 0.2500 | `term-in-text(对)` ×2 |
| hanfeizi | `hanfeizi-wai-chu-shuo-01` | 3.0 | 0.3750 | `term-in-original(败)` ×2 |

Plus confucius survives via the `retrieve_for_sage_chat` fallback
(`《论语·为政》` 2.20, sim 0.1125, above `DEBATE_MIN_SIMILARITY = 0.10`).

Four-sage total: **3 verses**.

## 5. The exact divergence

**The two queries are distinguished by nothing at all in the current code.**
Both are carried by the same defect: single-character fragments from
`_extract_keywords` matching against verse text.

- `uq-0009` is not refused because `人` occurs in `人生`/`知人` etc.
- `sc-0003` is not *incorrectly* refused only because `败` and `对` happen to
  match, plus a marginal 0.1125 fallback above the 0.10 floor.

`sc-0003`'s survival is therefore **also accidental** and only 0.0125 above the
relevance floor. Any fix that raises the floor, or that removes single-character
matching, will clear both — which is precisely why the previous word-level guard
round collapsed legal hits, was rejected, and would have shrunk Gate J's
denominator from 19 to 18.

## 6. Secondary defect: duplicated terms double-count

`_extract_keywords(q)` and `_extract_keywords(expanded_query)` return essentially
the same list when `SYNONYM_MAP` does not fire (`uq-0009`: the expansion adds
nothing, so all 14 terms appear **twice**). Every score is therefore inflated
~2×. This is a scoring bug, not a semantics decision, but it must be fixed
carefully because it also feeds `_debate_keyword_search`'s ordering.

## 7. Primary root cause classification

Selected: **C — weak evidence binder.**

Justification: the owning layer is the evidence-binding/scoring layer, not
retrieval (vector returns 0), not trust state (`decide_trust_state` is never
reached because a verse is returned), not the corpus (a correct refusal is
*possible*), and not the metric (the frozen Gate E formula is sound and its
denominator is intact). The binder accepts a single common character as
evidence, so "no supporting evidence" is structurally unreachable for any query
containing a frequent character.

Secondary contributing factors, separate from the primary cause:

- **B — retrieval score mistaken for entailment** in the sense that
  `similarity = score/8.0` is normalized into a value that reads like a
  relevance probability; 0.25 looks like weak-but-real relevance when it is
  actually a single-character coincidence.
- **I (partial) — fixture-adjacent signal gap**: the *dataset* is sound, but
  `uq-0009` is labelled `partial_corpus_support` while no minimum-evidence
  signal exists to detect that partial support is not sufficient.

## 8. Consequence for the fix — the constraint that must be satisfied

The fix must make **which lexical overlap counts as evidence** structural:

- a single common character must not be able to carry a hit;
- yet `sc-0003` must remain reachable with positive hits;
- and Gate J's denominator must remain 19 (no clearing of legal `sc-*` hits).

Because `sc-0003`'s current survival is itself accidental, the fix cannot be a
threshold move. It must (a) stop single-character fragments from scoring, and
(b) restore genuine reachability for the legal queries that lose their
accidental hits — otherwise the reject-all guard fails.

This is recorded so the implementer and the independent reviewer can check the
same invariant: **refusal must become correct without supported acceptance
collapsing.**
