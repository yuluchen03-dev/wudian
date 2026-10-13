# DSH-RM-005 — Independent mechanism verification (trust-verification)

Author: trust-verification. Purpose: verify the root cause **before** patching, as
the task contract requires. I did not take the captain's summary on trust; I ran
the mechanism probe myself.

Probe run: `backend/.venv/Scripts/python.exe deliverables/kb-v1/dsh-rm005-mechanism.py`
with an isolated temporary copy of production Chroma.
Raw output: `deliverables/kb-v1/trust-mechanism-out.txt`.

## 1. Verdict on the root cause

**CONFIRMED, and the captain's classification is correct but incomplete.**

Classification: **C — weak evidence binder.**
Owning layer: `RAGService._debate_keyword_search` (`backend/app/services/rag_service.py:526-570`).

All four sages return `vec=0` for `uq-0009`, so the pure vector layer produces no
hit at all. Every surviving hit comes from the keyword layer.

## 2. The exact firing term, per hit

Reproduced term-by-term. `_extract_keywords` emits 2-grams **and single
characters**, and the scoring loop awards +1.5 / +1.0 whenever such a term is a
substring of the corpus entry's `original` / `translation`/`text`.

`uq-0009` = `如何面对亲人的离世？`. Terms emitted: 14 unique, doubled to 28 by
`_extract_keywords(query) + _extract_keywords(expanded_query)` because
`SYNONYM_MAP` does not fire for this query (`_expand_synonyms` returns the query
unchanged). Every single hit is carried by a **single character**:

| sage | id | score | sim | firing term(s) | field |
|---|---|---|---|---|---|
| confucius | lunyu-taibo-01 | 2.0 | 0.2500 | `人` ×2 | text |
| confucius | lunyu-weilinggong-01 | 2.0 | 0.2500 | `人` ×2 | text |
| laozi | daodejing-22-01 | 2.0 | 0.2500 | `人` ×2 | text |
| laozi | daodejing-33-01 | 3.0 | 0.3750 | `人` ×2 | **original** |
| laozi | daodejing-08-01 | 2.0 | 0.2500 | `世` ×2 | text |
| mozi | mozi-feile-01 | 2.0 | 0.2500 | `人` ×2 | text |
| mozi | mozi-jianai-01 | 2.0 | 0.2500 | `人` ×2 | text |
| mozi | mozi-feigong-01 | 2.0 | 0.2500 | `对` ×2 | text |
| hanfeizi | hanfeizi-wuzhu-01 | 3.0 | 0.3750 | `世` ×2 | **original** |
| li_bai | libai-jiangjinjiu-01 | **6.0** | **0.7500** | `对`,`人` ×2 | **original** |
| li_bai | libai-xinglunan-01 | 2.0 | 0.2500 | `人` ×2 | text |
| fan_zhongyan | fanzhongyan-yueyanglouji-01 | 2.0 | 0.2500 | `人` ×2 | text |

`sc-0003` = `如何面对失败` (terms 10 unique, doubled to 20):

| sage | id | score | sim | firing term(s) | field |
|---|---|---|---|---|---|
| mozi | mozi-feigong-01 | 2.0 | 0.2500 | `对` ×2 | text |
| hanfeizi | hanfeizi-wai-chu-shuo-01 | 3.0 | 0.3750 | `败` ×2 | **original** |
| li_bai | libai-jiangjinjiu-01 | 3.0 | 0.3750 | `对` ×2 | **original** |

## 3. Three corrections to the earlier summary

1. **Two additional sages exist in the index.** `li_bai` and `fan_zhongyan` are
   present alongside the four classical schools (the dataset also carries
   `su_shi`, `wang_anshi`, `zhuge_liang`). `run_eval.py::eval_unsupported_refusal`
   iterates only `("confucius","laozi","mozi","hanfeizi")`, so those extra sages
   do not enter the Gate E count — but they matter for Gate J
   (`school_consistency` includes `sc-0013`=`li_bai`, `sc-0014`=`su_shi`,
   `sc-0015`=`fan_zhongyan`, `sc-0016`=`wang_anshi`, `sc-0017`=`zhuge_liang`).

2. **The highest-scoring hit in the entire system is a character coincidence.**
   `libai-jiangjinjiu-01` reaches similarity **0.75** for `uq-0009` on `对` + `人`
   alone. A character coincidence is being presented as 75% relevance. This is a
   trust-signal defect independent of Gate E.

3. **Single-character coincidence is the *only* mechanism at work.** Not one
   multi-character term fires for either query. The surviving "evidence" is
   therefore not weak-but-real; it is **not evidence at all**. That is what makes
   the honest fix structural rather than a tuned threshold.

## 4. The two-sided constraint (why a one-line guard is wrong)

Stopping single-character terms from scoring clears **both** queries:

- `uq-0009` loses all 12 hits → refusal ✓
- `sc-0003` loses `mozi-feigong-01` (`对`) and `hanfeizi-wai-chu-shuo-01` (`败`)

After that, `sc-0003` would survive only through the confucius
`retrieve_for_sage_chat` fallback at similarity **0.1125**, which sits a mere
**0.0125** above `DEBATE_MIN_SIMILARITY = 0.10` (`rag_service.py:205`). That is
an accidental margin, not a property. Making the legal control depend on it would
be exactly the reject-all collapse the goal forbids, and a prior round was
already rejected for clearing legal `sc-0003` hits and shrinking Gate J's
denominator from 19 to 18.

**Conclusion: the fix must be two-sided and structural.**
(a) single-character fragments must not carry a hit — they are not evidence;
(b) genuine reachability must be restored for `sc-0003` and the other legal
queries from *real* lexical evidence (multi-character concept overlap, corpus
keyword lists, `SYNONYM_MAP`-expanded whole terms).

No tuned scalar may be used for (a), and `sc-0003` must not be special-cased.

## 5. Secondary defect

`_extract_keywords(query) + _extract_keywords(expanded_query)` duplicates almost
the whole term list whenever `SYNONYM_MAP` does not fire (28 vs 14 for
`uq-0009`; 20 vs 10 for `sc-0003`), inflating every score roughly 2×. For
`sc-0003` `SYNONYM_MAP` *does* fire (`败`, `失`), yet the duplication still
occurs because the expanded text re-emits the original terms.

Deduplicating is a legitimate correctness fix, but it changes relative ordering,
so its effect on the legal queries must be measured before it is kept.

## 6. Sanity anchor for the fix

A correct binder must explain why `亲人离世` (bereavement) is unsupported while
`失败` (failure) is supported. The corpus does contain relevant material for
failure: `lunyu:2.20` / `lunyu-weilinggong-01` (`君子谋道不谋食`) sit under
confucius, and keyword lists include `失败`-adjacent concepts such as `现实`,
`判断`, `进退`, `退守`. By contrast **no** entry in
`data/processed/debate_classics.json` carries any keyword related to death,
grief, mourning, or bereavement (see the full keyword inventory: `弘毅`,
`任重道远`, `责任`, `志向`, `有为`, `躺平`, `担当`, `进退`, `退守`, `守志`,
`时机`, `选择`, `君子`, `谋道`, `价值`, `工作`, `人生`, `金钱`, `不争`, `自在`,
`放下`, `内卷`, `争胜`, `顺势`, `自知`, `明`, `困惑`, `判断`, `知足`, `知止`,
`长久`, `焦虑`, `欲望`, `柔弱`, `水`, `处世`, `安放`, `顺道`, `强力`, `努力`,
`非命`, `行动`, `生存`, `兼爱`, `利他`, `社会`, `公平`, `天下`, `实践`, `结果`,
`执行`, `承诺`, `实干`, `利害`, `发声`, `不公`, `法`, `规则`, `制度`, `赏罚`,
`功劳`, `职场`, `退路`, `计算`, `务实`, `策略`, `风险`, `变化`, `变通`).
The distinction is therefore representable from corpus content alone, which is
the test of a non-gamed fix.
