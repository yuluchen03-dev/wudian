"""Metric formulas for WUDIAN-KB-V1 eval (PROJECT-BRIEF ch.17).

Every metric is a pure function over records + predictions so that it can be
recomputed offline and unit-tested on known inputs.  Formulas are stated in
docstrings exactly as defined in `docs/kb-v1/audit/evaluation.md` §5.

Target numbers are **read-only targets**; this module never adjusts them and
never substitutes a passing value when the real measurement falls short.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Sequence

# PROJECT-BRIEF ch.17 gate targets (frozen; do NOT edit to force a pass).
TARGETS: Dict[str, Any] = {
    "quote_exactness": 0.99,
    "source_attribution": 0.98,
    "school_leakage_max": 0.01,
    "recall_at_5": 0.90,
    "unsupported_correct_refusal": 0.95,
    "core_claim_evidence_coverage": 0.95,
    "fabricated_classical_quote": 0,  # absolute count; any hit fails GATE-5
    "p50_seconds": 1.0,
    "p95_seconds": 3.0,
}

# ---------------------------------------------------------------- normalization

_PUNCT = "，。！？；：、（）()【】「」『』《》〈〉“”‘’\"'·…—～~!?,.;:[]{}<>"


def normalize(text: str) -> str:
    """Normalization used for quote matching.

    NFKC folds full-width forms; then whitespace and a fixed punctuation set are
    removed.  Deliberately conservative: it must NOT make two different
    sentences equal, otherwise `quote_relaxed` would become meaningless.
    """
    if not text:
        return ""
    out = unicodedata.normalize("NFKC", text)
    out = "".join(ch for ch in out if ch not in _PUNCT)
    out = re.sub(r"\s+", "", out)
    return out


# Traditional -> Simplified map for the characters that actually occur in this
# corpus and its adversarial variants.  Kept explicit rather than pulling a
# heavyweight dependency; extend as the corpus grows.
_T2S = str.maketrans({
    "於": "于", "爲": "为", "為": "为", "說": "说", "樂": "乐", "學": "学",
    "習": "习", "禮": "礼", "義": "义", "聖": "圣", "賢": "贤", "德": "德",
    "無": "无", "與": "与", "己": "己", "惡": "恶", "愛": "爱", "親": "亲",
    "靜": "静", "遠": "远", "過": "过", "國": "国", "時": "时", "書": "书",
    "車": "车", "馬": "马", "見": "见", "言": "言", "語": "语", "問": "问",
    "對": "对", "應": "应", "當": "当", "萬": "万", "歲": "岁", "風": "风",
    "雲": "云", "處": "处", "從": "从", "來": "来", "會": "会", "後": "后",
    "進": "进", "這": "这", "個": "个", "們": "们", "實": "实", "義": "义",
})


def to_simplified(text: str) -> str:
    """Best-effort traditional -> simplified folding (explicit table only)."""
    return (text or "").translate(_T2S)


def normalize_all(text: str) -> str:
    """Simplified + normalized: the space used for `normalized_match`."""
    return normalize(to_simplified(text))


# ---------------------------------------------------------------- quote metrics


def quote_exists(predicted: bool, expected: bool) -> bool:
    return bool(predicted) == bool(expected)


def compute_quote_exactness(records: Sequence[Dict[str, Any]],
                            predictions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Quote Exactness = correct verbatim matches / all quotes judged to exist.

    Denominator = predictions where the system claimed `quote_exists=True`.
    Numerator   = of those, how many are a true verbatim match
                  (`exact_match=True` and the quote really exists).
    A system that claims fewer quotes can score higher here, so this metric is
    only meaningful together with Source Attribution and coverage.
    """
    denom = 0
    numer = 0
    details = []
    for rec, pred in zip(records, predictions):
        if not pred.get("quote_exists"):
            continue
        denom += 1
        ok = bool(pred.get("exact_match")) and bool(rec["expected"].get("quote_exists"))
        numer += 1 if ok else 0
        if not ok:
            details.append({"id": rec.get("id"), "reason": "not an exact match"})
    value = (numer / denom) if denom else None
    return {"metric": "quote_exactness", "numerator": numer, "denominator": denom,
            "value": value, "target": TARGETS["quote_exactness"],
            "passed": (value is not None and value >= TARGETS["quote_exactness"]),
            "failures": details}


def compute_source_attribution(records: Sequence[Dict[str, Any]],
                               predictions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Source Attribution = correct attributions / all quotes.

    Denominator = every quote (regardless of whether it exists).
    Numerator   = predictions whose `source_correct` equals the expected value.
    Independent of `quote_exists` by contract (PROJECT-BRIEF ch.11).

    字段口径（与 ``schema.py`` 的 ``source_attribution`` 规格一致）：
    该数据集使用**扁平**字段 ``expected_source`` / ``expected_source_correct``，
    而不是 `quote_verification` 那样的嵌套 ``expected{...}``。
    早期版本读取 ``rec["expected"]["source_correct"]``，与实际数据不符，
    会直接抛 ``KeyError: 'expected'`` —— 属两半实现从未真正连通的集成缺陷。
    这里改为优先读扁平字段，并保留对嵌套写法的兼容。
    """
    denom = len(records)
    numer = 0
    details = []
    for rec, pred in zip(records, predictions):
        nested = rec.get("expected") or {}
        if "expected_source_correct" in rec:
            want = bool(rec["expected_source_correct"])
        else:
            want = bool(nested.get("source_correct"))
        got = bool(pred.get("source_correct"))
        if got == want:
            numer += 1
        else:
            details.append({"id": rec.get("id"), "expected": want, "got": got,
                            "expected_source": rec.get("expected_source"),
                            "correct_source": pred.get("correct_source")})
    value = (numer / denom) if denom else None
    return {"metric": "source_attribution", "numerator": numer, "denominator": denom,
            "value": value, "target": TARGETS["source_attribution"],
            "passed": (value is not None and value >= TARGETS["source_attribution"]),
            "failures": details}


def compute_fabricated_classical_quote(records: Sequence[Dict[str, Any]],
                                       predictions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Fabricated Classical Quote = count of fabricated quotes that passed.

    A fabricated quote is one where the corpus does not contain it
    (`expected.quote_exists=False`) yet the system marked it `verifiable=True`.
    Target is an absolute count of 0; ANY hit fails GATE-5.
    """
    hits = []
    for rec, pred in zip(records, predictions):
        if rec["expected"].get("quote_exists") is False and pred.get("verifiable") is True:
            hits.append({"id": rec.get("id"), "attack_type": rec.get("attack_type"),
                         "quote": (rec.get("input") or {}).get("quote")})
    value = len(hits)
    return {"metric": "fabricated_classical_quote", "value": value,
            "target": TARGETS["fabricated_classical_quote"],
            "passed": value <= TARGETS["fabricated_classical_quote"],
            "failures": hits}


# ---------------------------------------------------------------- retrieval


def recall_at_k(records: Sequence[Dict[str, Any]],
                retrieved: Sequence[Sequence[str]], k: int) -> Dict[str, Any]:
    """Recall@K = (1/N) * sum( hit_i ), hit_i = any(expected ∩ top-K) != ∅."""
    n = len(records)
    hits = 0
    details = []
    for rec, got in zip(records, retrieved):
        expected = set(rec.get("expected_passage_ids") or [])
        topk = list(got)[:k]
        if expected & set(topk):
            hits += 1
        else:
            details.append({"id": rec.get("id"), "expected": sorted(expected),
                            "topk": topk})
    value = (hits / n) if n else None
    return {"metric": f"recall_at_{k}", "numerator": hits, "denominator": n,
            "value": value, "failures": details}


def reciprocal_rank(records: Sequence[Dict[str, Any]],
                    retrieved: Sequence[Sequence[str]]) -> Dict[str, Any]:
    """MRR = (1/N) * sum(1 / rank of first hit); 0 when no hit."""
    n = len(records)
    total = 0.0
    details = []
    for rec, got in zip(records, retrieved):
        expected = set(rec.get("expected_passage_ids") or [])
        rr = 0.0
        for rank, ref in enumerate(got, start=1):
            if ref in expected:
                rr = 1.0 / rank
                break
        if rr == 0.0:
            details.append({"id": rec.get("id"), "expected": sorted(expected)})
        total += rr
    value = (total / n) if n else None
    return {"metric": "mrr", "value": value, "denominator": n, "failures": details}


def compute_retrieval_metrics(records: Sequence[Dict[str, Any]],
                              retrieved: Sequence[Sequence[str]]) -> Dict[str, Any]:
    r1 = recall_at_k(records, retrieved, 1)
    r3 = recall_at_k(records, retrieved, 3)
    r5 = recall_at_k(records, retrieved, 5)
    mrr = reciprocal_rank(records, retrieved)
    r5["target"] = TARGETS["recall_at_5"]
    r5["passed"] = (r5["value"] is not None and r5["value"] >= TARGETS["recall_at_5"])
    return {"recall_at_1": r1, "recall_at_3": r3, "recall_at_5": r5, "mrr": mrr}


# ---------------------------------------------------------------- school leakage


def compute_school_leakage(records: Sequence[Dict[str, Any]],
                           retrieved: Sequence[Sequence[str]],
                           book_of_ref) -> Dict[str, Any]:
    """School Leakage = cross-school citations / all citations.

    A citation is out-of-school when the retrieved passage's book is not in the
    sage's `allowed_books`.
    """
    total = 0
    leaked = 0
    details = []
    for rec, got in zip(records, retrieved):
        allowed = set(rec.get("allowed_books") or [])
        for ref in got:
            total += 1
            book = book_of_ref(ref)
            if allowed and book not in allowed:
                leaked += 1
                details.append({"id": rec.get("id"), "sage_key": rec.get("sage_key"),
                                "ref": ref, "book": book})
    value = (leaked / total) if total else None
    return {"metric": "school_leakage", "numerator": leaked, "denominator": total,
            "value": value, "target_max": TARGETS["school_leakage_max"],
            "passed": (value is not None and value < TARGETS["school_leakage_max"]),
            "failures": details}


# ---------------------------------------------------------------- refusal / claims


def compute_unsupported_correct_refusal(
        records: Sequence[Dict[str, Any]],
        predictions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Unsupported Correct Refusal = correct refusals / all cases that must refuse.

    A refusal counts only if ALL hold:
      * trust_state == 'insufficient_evidence'
      * the response contains the PROJECT-BRIEF ch.12 refusal wording
      * no classical "quote" was presented as authoritative
    """
    from schema import REQUIRED_REFUSAL_PHRASE  # local import: script-adjacent

    denom = 0
    numer = 0
    details = []
    for rec, pred in zip(records, predictions):
        if rec["expected"].get("must_refuse") is not True:
            continue
        denom += 1
        text = pred.get("answer_text", "") or ""
        ok = (pred.get("trust_state") == "insufficient_evidence"
              and REQUIRED_REFUSAL_PHRASE in text
              and not pred.get("presented_quote_as_classic"))
        if ok:
            numer += 1
        else:
            details.append({"id": rec.get("id"),
                            "trust_state": pred.get("trust_state"),
                            "has_phrase": REQUIRED_REFUSAL_PHRASE in text,
                            "presented_quote_as_classic": pred.get("presented_quote_as_classic")})
    value = (numer / denom) if denom else None
    return {"metric": "unsupported_correct_refusal", "numerator": numer,
            "denominator": denom, "value": value,
            "target": TARGETS["unsupported_correct_refusal"],
            "passed": (value is not None and value >= TARGETS["unsupported_correct_refusal"]),
            "failures": details}


def compute_core_claim_evidence_coverage(
        records: Sequence[Dict[str, Any]],
        predictions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Core Claim Evidence Coverage = supported core claims / all core claims.

    A core claim counts as covered only when it has >=1 evidence entry whose
    `verification == 'supported'`.
    """
    denom = 0
    numer = 0
    details = []
    for rec, pred in zip(records, predictions):
        for claim in pred.get("claims", []) or []:
            if not claim.get("is_core"):
                continue
            denom += 1
            ev = [e for e in (claim.get("evidence") or [])
                  if e.get("verification") == "supported"]
            if ev:
                numer += 1
            else:
                details.append({"id": rec.get("id"), "claim": claim.get("text")})
    value = (numer / denom) if denom else None
    return {"metric": "core_claim_evidence_coverage", "numerator": numer,
            "denominator": denom, "value": value,
            "target": TARGETS["core_claim_evidence_coverage"],
            "passed": (value is not None
                       and value >= TARGETS["core_claim_evidence_coverage"]),
            "failures": details}


# ---------------------------------------------------------------- percentiles


def percentile(values: Iterable[float], pct: float) -> Optional[float]:
    """Nearest-rank percentile (pct in 0..100).  None for empty input."""
    vals = sorted(values)
    if not vals:
        return None
    if pct <= 0:
        return vals[0]
    idx = int(round((pct / 100.0) * len(vals) + 0.5)) - 1
    idx = max(0, min(idx, len(vals) - 1))
    return vals[idx]


def compute_latency(latencies: Sequence[float]) -> Dict[str, Any]:
    """P50/P95 local retrieval latency in seconds (excludes external LLM)."""
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    return {"metric": "latency", "n": len(latencies), "p50": p50, "p95": p95,
            "target_p50": TARGETS["p50_seconds"], "target_p95": TARGETS["p95_seconds"],
            "passed": (p50 is not None and p95 is not None
                       and p50 < TARGETS["p50_seconds"]
                       and p95 < TARGETS["p95_seconds"])}
