# DSH-RM-005 / DSH-RM-006 — entry-point isolation (captain, static)

Current Gate: DSH-RM-006
Functional Task: RETRIEVAL-RECALL
Method: **source reading only — no command executed**
Purpose: establish which code path each frozen gate exercises, because two
earlier assumptions in this goal were wrong about it.

## The three gates do NOT share one entry point

Verified by reading `eval/scripts/run_eval.py`:

| Gate | Metric | Call site | Function invoked |
|---|---|---|---|
| E | `unsupported_correct_refusal` | `:252` | `retrieve_for_debate_sage` |
| J | `school_leakage` | `:296` | `retrieve_for_debate_sage` |
| F | `recall_at_5` | `:320` | **`retrieve_for_sage_chat`** |

E and J share a path. **F does not.**

## The two paths are fully disjoint

`retrieve_for_sage_chat` (`rag_service.py:1307-1396`) retrieves via
`:1332-1334`:

```
vec_results = self.vector_search(expanded_query, top_k=top_k * 2)
kw_results  = self._kw_search_chroma(expanded_query, top_k=top_k * 2)
results     = self._merge_retrieval(vec_results, kw_results, limit=top_k * 2)
```

`retrieve_for_debate_sage` (`:1398-1463`) retrieves via `:1418-1434`:

```
results = self._debate_vector_search(sage_key, query, top_k=top_k)
if results: return self._format_debate_results(results)
results = self._debate_keyword_search(sage_key, query, top_k=top_k)
```

Confirmed by call-graph grep over the whole module:

| Helper | Defined | Called from | In `retrieve_for_sage_chat`? |
|---|---|---|---|
| `_debate_keyword_search` | `:672` | `:1434` only | **NO** |
| `_query_has_corpus_support` | `:634` | `:1453` only | **NO** |
| `_kw_search_chroma` | `:1134` | `:1333` only | **YES** |
| `_debate_vector_search` | `:769` | `:1418` only | **NO** |

**Every RM-005 helper is reachable only from the debate path.** RM-005's change
therefore cannot move Gate F at all, and the reported "Recall@5 unchanged at 0.55"
is **structurally expected**, not merely an empirical observation.

## Correction to two earlier statements

**1. `DSH-CURRENT-STATE.md` §7c was inaccurate.** It stated that "Gate F shares a
code path with E/J". That is **false**. The gates share the *metric module* and the
*same Chroma collection*, but not a retrieval entry point. This document supersedes
that claim.

**2. RM-005 cannot regress Gate F, and RM-006 cannot fix Gate E.** The two tasks
own disjoint retrieval surfaces. This is a stronger independence property than the
DAG assumed, and it has a concrete benefit: RM-006's work is **not** at risk of
silently disturbing the RM-005 refusal result, and vice versa. It also means the
"RM-005 already moved Gate F" hypothesis can be discarded — it is impossible.

## What this means for RM-006

RM-006's real surface is `retrieve_for_sage_chat` and its three helpers:
`vector_search`, `_kw_search_chroma`, `_merge_retrieval`. The goal's fix order maps
onto them as follows, and the analysis should target these and nothing else:

| Order | Fix | Owning layer for Gate F |
|---|---|---|
| 1 | ID normalization | `retrieve_for_sage_chat` output shaping (`:1363-1372`, the existing `debate:{sage}:{id}` prefix alignment) |
| 2 | canonical ID mapping | same, plus whatever Gold expects |
| 3 | metadata | `_kw_search_chroma` / collection metadata |
| 4 | query normalization | `_expand_synonyms` (shared) |

Fixes 5-11 (ontologies, BM25, dense, fusion, rerank, diversity) live in the
`vector_search` / `_kw_search_chroma` / `_merge_retrieval` trio.

**A caution worth recording:** the goal's fix order lists "BM25" and "dense" as
separate steps, but `retrieve_for_sage_chat` already implements a **two-layer
fusion** (`:1332-1334`) and the comment at `:1329-1331` records that FIX-003
introduced it precisely because "hash embedding 非语义，纯向量召回不足（Recall@5
基线 0.325）". So steps 7-9 are not greenfield — they describe an existing, already-
tuned mechanism whose behaviour must be measured before being changed. Re-tuning a
fusion layer without measurement is how a 0.55 becomes a 0.40.

## Gate J's denominator interacts with this

`compute_school_leakage` (`metrics.py:256-270`) increments its denominator per
**retrieved** citation, and Gate J calls the **debate** path. So Gate J's
denominator (currently 19) is driven by `retrieve_for_debate_sage` reachability —
the same path RM-005 modified. This is why the RM-005 denominator-preservation
result matters and why RFC-GATE-J remains open: any future change to the debate
path that reduces reachability silently shrinks J's denominator. RM-006, on the
chat path, **cannot** affect it.

## Status

Recording this as a **structural finding**, verified by grep and by reading both
function bodies. It requires no execution and no test to establish, because it is a
call-graph fact, not a behavioural measurement.
