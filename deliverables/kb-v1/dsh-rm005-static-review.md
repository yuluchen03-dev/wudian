# DSH-RM-005 — STATIC REVIEW

> **STATIC REVIEW — NO COMMAND EXECUTED. THIS IS NOT INDEPENDENT VERIFICATION.**
>
> Reviewer: `qa-reviewer` (t17 attempt). Every judgement below is derived from
> reading `rag_service.py`, `test_rm005_evidence_sufficiency.py` and the saved
> artifacts via file tools only. `pwsh` returns `spawn EPERM` for this session,
> so **not one assertion, test, evaluator run or fingerprint was executed by
> this reviewer**. Nothing here may be cited as reproduced evidence, as a
> `TERMINAL PASS`, or as closing any gate.
>
> Authority of this document: **advisory only**, ranked below independent test
> results per the goal's source-of-truth order.

Current Gate: **DSH-RM-005**
Functional Task: **UNSUPPORTED-REFUSAL**
Historical Reference: **FIX-002 / earlier RM-005**

Line numbers reference the **current working-tree** `rag_service.py`
(1704 lines, up from 1536 at HEAD).

---

## (a) Uncommitted diff hunks in `backend/app/services/rag_service.py`

The file carries **three** logical changes stacked together, which the t1
ownership audit already flagged as the only genuinely mixed file. I can separate
them only by content, not by index state (no shell).

| # | Lines (current tree) | Owning change | What it changes |
|---|---|---|---|
| 1 | 142–181 | FIX-002 (pre-existing) | Module constants for the G1–G4 out-of-scope guards: `_OUT_OF_SCOPE_BOOKS`, `_OUT_OF_SCOPE_BOOKS_BRACKETED`, `_MODERN_TECH_TERMS`, `_CN_DIGITS`/`_CN_UNITS`, `_GEN_VERB_RE`/`_GEN_VERB_RE2`. |
| 2 | 184–273 | **DSH-RM-005 (new)** | The evidence-bearing-term layer: explanatory header, `evidence_terms()` (drops `<2`-char terms, dedupes), `query_concept_space()`, `concept_resolves_in_corpus()`. |
| 3 | 373 | **DSH-RM-005 (new)** | `self._concept_vocab_cache_size: int = -1` instance field for the concept-vocabulary cache. |
| 4 | 621–658 | **DSH-RM-005 (new)** | `_evidence_terms()` bound wrapper; `_query_has_corpus_support()` the sufficiency predicate; `_corpus_concept_vocab()` cached 9-school vocabulary keyed on index size. |
| 5 | 678–700 | **DSH-RM-005 (new)** | `_debate_keyword_search` scoring rewrite: keyword tags now require `len(kw) >= 2`; scoring iterates **deduped** `lexical_terms` + `ontology_terms` instead of `_extract_keywords(q) + _extract_keywords(expand(q))`. **Weights (3.0/4.0/1.5/1.0) and the `/8.0` normalisation constant are unchanged.** |
| 6 | 710–711 | FIX-002/C3 (pre-existing) | `if score <= 0: continue` — the "no floor-fallback" guard. |
| 7 | 1436–1446 | **DSH-RM-005 (new)** | Sufficiency gate at the **confucius fallback admission point**: returns empty before calling `retrieve_for_sage_chat` when `_query_has_corpus_support(query)` is False. |
| 8 | 973–1085, 1171–1176, 1206–1214 | FIX-003 (pre-existing) | `_kw_search_chroma`, `_merge_retrieval`, fusion in `retrieve_for_sage_chat`, and the `debate:{sage_key}:` id-alignment. |
| 9 | 1500–c.1520 | FIX-002 (pre-existing) | `_cn_to_int` and `_query_out_of_scope`. |

**Not changed (verified by reading):** `DEBATE_MIN_SIMILARITY` is still
`0.10` at line 297. No new numeric floor, multiplier or tolerance was introduced
by the RM-005 hunks.

---

## (b) `concept_resolves_in_corpus` generality risk

**Assessment: the risk is real and should be probed, but it is a bounded risk,
not a fixture-shaped one.**

The predicate (line 255) returns True if a candidate term appears as a substring
in the concatenation of every corpus entry's `original`, `translation`, `text`
and `keywords`. Two properties create the risk:

1. **Substring matching on 2-character terms.** A 2-char concept can hit inside
   an unrelated longer word. The rule therefore inherits the same *class* of
   weakness it was written to remove — it merely raises the granularity from one
   character to two. The defence is that candidate terms come only from
   (i) curated corpus `keywords` tags and (ii) `SYNONYM_MAP` expansions, not from
   arbitrary query n-grams. That makes the *input* corpus-driven rather than
   query-driven, which is the substantive improvement.
2. **`keywords` are included in the blob.** So a term that appears only as a
   curated tag — never in the actual text — counts as "resolving". For
   sufficiency that is arguably intended (the tag asserts the entry is about the
   concept), but it means the predicate proves *concept-space overlap*, not
   *textual support*.

**Named probe queries a shell-capable reviewer must run** (I did not run any of
these; they are written down, not executed):

| Probe query | Intent | Expected under a general rule |
|---|---|---|
| `请问地铁几点停运` | The established negative control; must not gain support | `_query_has_corpus_support` False; keyword layer empty |
| `今天天气怎么样` | Second negative control already in the test file | False |
| `如何修理洗衣机` | **New.** Unrelated, but 修 could substring-hit 修养/修身 tags | False; guard against 2-char coincidence |
| `仁` (single character) | Single-char query; concept space should be empty or non-resolving | False, and no crash |
| `知足` | 2-char curated tag that genuinely resolves | True |
| `不争` | 2-char curated tag present in 道德经 entries | True |
| `失败` / `失败了怎么办` | Must stay supported via SYNONYM_MAP 败 | True |
| `亲人去世了很难过` | Paraphrase of the unsupported case | False |
| `什么是道` | High-frequency classical char | **Watch closely** — a True here is not necessarily wrong, but a True with zero real textual support would expose 2-char coincidence |
| `程序员的职业规划` | Modern domain with no corpus concept | False |

The decisive question is whether any **negative** probe above returns True.
A single False-positive on an unrelated query means the predicate is still
admitting coincidence and Gate E's 12/12 would rest on a weaker foundation than
claimed. This must be executed before RM-005 can be called terminal.

---

## (c) Does the test file actually cover all 10 required behaviours?

**Verdict: 8 of 10 are genuinely asserted; 2 are missing, and 2 more are only
nominally covered. This is the most important finding in this review.**

The RM-005 contract's 10-point matrix versus
`backend/tests/test_rm005_evidence_sufficiency.py`:

| # | Required behaviour | Coverage | Judgement |
|---|---|---|---|
| 1 | `uq-0009` → refusal | `test_behaviour_1_uq0009_refused` (L95) asserts four-sage hits `== 0` **and** predicate False | **Solid** |
| 2 | `sc-0003` → supported | `test_behaviour_2_legal_control_sc0003_supported` (L102) asserts hits `> 0` and predicate True | **Solid** |
| 3 | No evidence → refusal | `test_behaviour_3_no_evidence_refused` (L109) — but it only asserts the **predicate** is False for 2 negative queries; it never asserts four-sage hits `== 0` | **Partial** — the actual refusal outcome is unasserted for this class |
| 4 | Irrelevant evidence → refusal | `test_behaviour_4_irrelevant_evidence_not_admitted` (L116) asserts the keyword layer returns `[]` for uq-0009 across 4 sages | **Partial** — asserts the *keyword layer* only. Because `retrieve_for_debate_sage` falls through to the vector layer (L1418) and to the fallback, "keyword layer empty" does **not** imply "refused". Behaviour 1 covers the end-to-end case for uq-0009; behaviour 4 does not generalise it |
| 5 | **Verified but irrelevant quote → refusal** | **No test at all** | **MISSING** |
| 6 | **Supported evidence → supported** | **No dedicated test.** `test_behaviour_2` covers only sc-0003 | **MISSING as a distinct behaviour** |
| 7 | **Wrong-school evidence → refusal / not sufficient** | **No test at all** | **MISSING** |
| 8 | **Generic fallback quote must NOT be upgraded to support** | **No test at all** | **MISSING** |
| 9 | **Multiple weak evidence must NOT auto-suffice** | **No test at all** | **MISSING** |
| 10 | One strong relevant evidence → keeps support | `test_behaviour_10_strong_relevant_evidence_keeps_support` (L124), plus the reject-all guard's 19-entry reachability assertion | **Solid** — but note it asserts only `_query_has_corpus_support`, not end-to-end hits, and it explicitly skips sc-0009/sc-0017 |

Supporting tests that are genuinely valuable but not part of the 10:
`test_single_characters_are_never_evidence`, `test_ontology_terms_come_from_synonym_map`,
`test_lexical_terms_are_deduplicated`,
`test_corpus_support_predicate_rejects_empty_concept_space`,
`test_corpus_support_is_general_not_case_specific`
(`失败了怎么办` → True, `亲人去世了很难过` → False — a good generality check),
and the whole `RejectAllGuardTest` class including the pinned
`assertEqual(len(BASELINE_REACHABLE), 19)`.

**Behaviours 5, 7, 8, 9 are absent.** Note that 5, 8 and 9 concern the
**trust/citation layer**, not the retrieval layer this task touched — they may
legitimately belong to `test_citation_guard.py` / `test_quote_verifier.py`. But
the RM-005 contract listed them as required, so as written the matrix is
**incomplete**, and the task record's claim to have exercised "the 10-point
behaviour matrix" overstates what the file contains. That claim must be corrected
before RM-005 is accepted. Behaviour 7 (wrong-school) is plausibly covered by
existing school-leakage tests, but I could not confirm that by reading alone
without counting citations, and Gate J's 0/19 is itself a measurement I cannot
reproduce here.

---

## (d) Remaining gaming vectors identifiable by reading

1. **`concept_resolves_in_corpus` substring leniency** — see (b). Not gaming in
   intent, but it is the residual mechanism by which an unrelated query could
   slip through if its 2-char terms happen to be curated tags.
2. **`keywords` included in the resolution blob** — a term present only as a
   *tag* counts as resolving. Self-consistent, but it means "support" can be
   established without any textual occurrence of the term.
3. **The confucius-only gate placement (L1435).** The new sufficiency gate sits
   inside `if not results and sage_key == "confucius"`. For **laozi / mozi /
   hanfeizi** there is *no* equivalent admission gate — those sages rely solely
   on the keyword layer (now fixed) and the vector layer. Gate E counts all four
   sages, so uq-0009 must be zero on all four; the keyword fix plausibly handles
   that, but the *asymmetry* means the sufficiency boundary is not uniformly
   applied across sages. This is defensible (only confucius has a fallback) but
   it is a **structural asymmetry a reviewer must specifically probe**: confirm
   uq-0009 is zero for laozi/mozi/hanfeizi from the keyword layer alone, and
   confirm the residual vector hit does not reappear.
4. **The residual vector layer.** t3 discloses the subway negative control is
   `1`, not `0`, from `_debate_vector_search` (`mozi-jianai-01` sim 0.1044).
   Since `retrieve_for_debate_sage` returns early on vector results (L1418-1420),
   a vector hit **bypasses the keyword layer entirely**. So for any query where
   the vector layer fires, neither new guard applies except the confucius
   fallback gate. Gate E passes only because uq-0009 happens to get zero vector
   hits. That is a **contingent** pass, resting on hash noise rather than on the
   new rule. Worth stating plainly: the fix does not make the vector layer
   support-aware.
5. **`test_supported_acceptance_not_collapsed` skips non-baseline queries.**
   It iterates only `qid in BASELINE_REACHABLE`, so the other 2 legal queries are
   silently out of scope. Combined with the pinned `len == 19`, this correctly
   prevents denominator shrinking — good — but it also means the guard would not
   notice new regressions among queries never in the baseline set.
6. **No test asserts the negative control's end-to-end hit count.** The test
   explicitly restricts itself to the keyword layer (L236-239). So the known
   residual (subway = 1) is *not* pinned by any assertion, and could silently
   grow without failing the suite.

---

## (e) What CANNOT be concluded without execution

Explicitly, these remain **unverified**:

1. **That Gate E is 12/12.** The value in
   `deliverables/kb-v1/trust-rm005-eval-raw.txt` (numerator 12, denominator 12)
   is the author's saved artifact. I read it and it is internally consistent
   with t3's record, but it is **not** my execution, and a saved artifact cannot
   certify itself.
2. **That Gate J's denominator is still 19.** Same artifact (numerator 0,
   denominator 19). The denominator-shrink property is the single most important
   number in this task, because `compute_school_leakage` derives its denominator
   from *retrieved citations* — so a silent reachability loss shows up as a
   smaller, cleaner-looking denominator rather than a failure. It must be
   reproduced by a fresh run.
3. **That the tests pass, or even run.** `test_rm005_evidence_sufficiency.py` is
   **unexecuted** by the author (disclosed in the implementation record §7) and
   unexecuted by me. An unexecuted test file is not evidence.
4. **That no legal query regressed.** The reject-all guard exists but has never
   run. `sc-0009`/`sc-0017` are acknowledged baseline-dead; I cannot confirm the
   remaining 19 are still reachable.
5. **That Recall@5 is unchanged at 22/40** (artifact says 0.55; unverified).
6. **Production Chroma integrity.** I can verify nothing about hashes without a
   shell. The `DDDFBE1B` vs `4C97B5D0` discrepancy for `chroma.sqlite3` remains
   open; the captain's resolution document addresses its provenance but a fresh
   six-file fingerprint is still required.
7. **That the negative control's residual is exactly 1**, or that it does not
   grow under RM-006.
8. **Anything about the other gates (D/H/I) or the full regression suite.**

## Reviewer's bottom line

Read as code, the RM-005 implementation is **honest and non-gamed**: it contains
no case id, reads no Gold file, classifies no question topic, leaves
`DEBATE_MIN_SIMILARITY` and all weights untouched, and moves the decision from
"does this string resemble that string" to "does this query's concept space
reach real corpus content" — which is a genuine, corpus-grounded distinction and
matches the root cause two independent experts established.

But it is **not verified**, and two things must happen before it can be called
terminal:

1. **Execute** the evaluator plus the test suite, and reproduce E = 12/12 with
   J = 0/19 in the same run.
2. **Correct the behaviour-matrix claim.** Behaviours 5, 7, 8 and 9 are absent
   from the test file; behaviour 3 and 4 assert only the predicate and the
   keyword layer, not end-to-end refusal. Either add the missing assertions or
   amend the record to state precisely which behaviours are covered where.

I would **not** issue `TERMINAL PASS` on this evidence, and I would not accept
the phrase "10-point behaviour matrix" as currently written.
