# DSH-RM-005 — vector-layer contingency: resolved from in-repo evidence

Current Gate: DSH-RM-005
Functional Task: UNSUPPORTED-REFUSAL
Method: **source and docstring evidence only — no command executed**
Status: closes the "CONTINGENCY NOT YET QUANTIFIED" item as **PARTIALLY RESOLVED**

## Why this document exists

The independent reviewer (t17) and the captain both flagged that the Gate E pass
appeared **contingent**: `retrieve_for_debate_sage` returns early on vector hits
(`rag_service.py:1419-1420`), so the new sufficiency gate at `:1441` is reached
only when the vector layer draws nothing. If `uq-0009` refused merely because the
hash embedding *happened* to score it low, the fix would rest on luck.

t18 was to measure this with a per-case table, but the shell outage made
execution impossible. The question turns out to be answerable **without execution**
from evidence already committed in the repository.

## The decisive evidence

`_debate_vector_search` (`rag_service.py:769-830`) applies a **hard relevance
floor** before returning anything:

```
:818  filtered = [
:819      item for item in formatted
:820      if item.get("similarity", 0.0) >= self.DEBATE_MIN_SIMILARITY
:821  ]
...
:830  return filtered
```

`DEBATE_MIN_SIMILARITY = 0.10` (`rag_service.py:297` region).

The function's own docstring records the **measured distribution** that the floor
was calibrated against (`:781-795`):

```
有真实关联的现代问题（brief ch.7/P0 要求必须能检索到）：
   我该不该躺平      -> confucius 0.165 / laozi 0.143 / mozi 0.106 / hanfeizi 0.109
语料无支撑、应拒答的问题（brief ch.12 要求不硬编）：
   如何面对亲人的离世 -> 最高 0.092
   asdfghjkl          -> 最高 0.071
   孔子怎么看职场PUA   -> 最高 0.140（注意：此例与合法问题区间重叠）
   韩非子会建议我辞职吗 -> 最高 0.152（同上）
```

**`uq-0009`'s documented maximum vector similarity is 0.092, which is below the
0.10 floor.** The vector layer therefore excludes it at `:818-821` **by design of
the existing floor**, computed before RM-005 existed — not by chance in this
particular run.

## What this changes

**The narrower claim is now supported by repository evidence rather than luck.**
For `uq-0009` specifically, the outcome is *deterministic given the measured
similarity*, not a coin flip: 0.092 < 0.10, so `filtered == []`, so `:1419-1420`
does not early-return, so the flow reaches `:1422` and then the `:1441` gate.

So the correct characterisation is more precise than either earlier statement:

- It is **not** "pure luck" — the floor is what excludes `uq-0009`, and the floor
  is a deliberate, documented, pre-existing control.
- It is **still contingent**, because the floor is a **scalar threshold over a
  non-semantic hash embedding**. The docstring itself concedes the two classes
  **overlap in the 0.10–0.16 band**, and lists two legitimate modern questions
  (`孔子怎么看职场PUA` at 0.140, `韩非子会建议我辞职吗` at 0.152) that sit *above*
  the floor while resembling the refused class. `uq-0009` is excluded because it
  lands at 0.092; a paraphrase of the same question that scored 0.11 would not be.

**Therefore the accurate statement is:** the sufficiency gate is a genuine second
line of defence, and for `uq-0009` the vector layer independently excludes the
query via a documented floor — but the exclusion is a **threshold margin**, not a
semantic guarantee, and the code explicitly says so.

## The residual risk, stated precisely

The margin for `uq-0009` is `0.10 − 0.092 = 0.008`. That is thin. The docstring
documents overlap up to 0.152 on the "should refuse" side and down to 0.106 on
the "must retrieve" side, so the two populations are genuinely inseparable by
threshold. Any paraphrase of `uq-0009` whose hash similarity crosses 0.10 would
reach `:1441`, and `_query_has_corpus_support` would then have to catch it — which
it should, because the corpus has no grief vocabulary. That is exactly why the
gate matters and why the two layers are complementary rather than redundant.

## Empirical confirmation already on disk

The captain's earlier read-only probe captured actual `vec` counts, and its output
is preserved at `deliverables/kb-v1/dsh-rm005-probe-out.txt`. It **directly
confirms `vec=0` for all four sages on `uq-0009`**:

```
uq-0009: '如何面对亲人的离世？'
  [confucius] vec=0 kw=2 final=2
  [laozi]     vec=0 kw=3 final=3
  [mozi]      vec=0 kw=3 final=3
  [hanfeizi]  vec=0 kw=1 final=1
  TOTAL hits across 4 sages = 9
```

So the earlier claim is **measured for `uq-0009`**, not merely inferred from the
docstring. Note this probe ran **before** RM-005 (it exposes the original 9-hit
behaviour carried by single characters), so it establishes the pre-fix vector
behaviour, which is what determines whether `:1419-1420` early-returns.

It also shows the discriminating contrast that matters for the legal control:

```
sc-0003: '如何面对失败'
  [hanfeizi]  vec=1 kw=1 final=1
      vec  sim=0.1151 id=hanfeizi-wai-chu-shuo-01
      FINAL sim=0.1151 id=hanfeizi-wai-chu-shuo-01 src=《韩非子·外储说左上》
```

`sc-0003` **does** obtain a real vector hit (0.1151 > 0.10) for `hanfeizi` via its
`失败 → 败` expansion, while `uq-0009` obtains none. That asymmetry is the
corpus-grounded distinction the whole fix rests on, and it is measured rather than
assumed.

Caveat recorded honestly: this probe predates RM-005 and covers only 2 queries
(`uq-0009`, `sc-0003`). It does not supply the other 10 `must_refuse` cases.



1. **The full per-case table for all 12 `must_refuse` queries.** The docstring
   gives values for only 4 illustrative queries (`如何面对亲人的离世`, `asdfghjkl`,
   `孔子怎么看职场PUA`, `韩非子会建议我辞职吗`). The other 8 `uq-*` cases have **no
   recorded vector similarity anywhere in the repository**, so their margin is
   genuinely unknown without running `_debate_vector_search`.
2. **Confirmation that the docstring's 0.092 still holds** — it was measured
   before RM-005 and before the `/8.0` normalisation change; the vector layer was
   not modified, so it should, but that is an inference, not a measurement.
3. **The ten substring false-positive probes** on `_query_has_corpus_support`.

Note in particular that `孔子怎么看职场PUA` (0.140) and `韩非子会建议我辞职吗`
(0.152) **exceed the floor**, so for those two the vector layer does **not**
exclude the query — they must be refused (or not) by some other layer. They are not
in the `uq-*` refusal set (they appear as `t-PUA` / `t-辞职` legal probes), but the
docstring's own warning shows the floor cannot be relied on generally. This is
recorded as a **candidate weakness for RM-006**, not a RM-005 defect.

## Correction to the record

Two earlier statements should be read as superseded by this document:

- The captain's `dsh-rm005-validity-assessment.md` said the pass "is contingent
  rather than enforced" and implied the exclusion was luck. More precisely: it is
  contingent on a **documented scalar floor with a 0.008 margin**, which is a real
  control but not a semantic guarantee.
- The implementer's §10 "luck, not engineering" characterisation is **half right**:
  the *exclusion* is engineered (the floor), while the *margin* is only 0.008 and
  the two distributions provably overlap, so the guarantee is weak. The honest
  phrasing is: **engineered control, thin margin, no semantic guarantee.**

This remains a `CONDITIONAL` result and must not be reported as an unconditional
`12/12`.
