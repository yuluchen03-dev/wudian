"""
悟典 - 真实系统评测运行器（PHASE 8 / E-09）

与 ``report.py`` 的区别
-----------------------
``report.py`` 生成的是**可计算性报告**：当被评系统不存在时，指标输出
``value=null`` + ``status=not_computable`` + 原因。

本模块在**被评系统已经存在**之后，真正调用它并对数据集打分：

- Quote Exactness / Source Attribution / Fabricated Classical Quote
      -> 调用 ``quote_verifier.verify_quote``（PHASE 5）
- Unsupported Correct Refusal
      -> 调用 RAG 检索；无足够证据时应走 insufficient_evidence 拒答
- Core Claim Evidence Coverage
      -> 调用 ``claim_evidence``（PHASE 5）
- School Leakage
      -> 调用 ``retrieve_for_debate_sage``，检查返回的 source 是否越派
- Retrieval Recall@1/3/5 与 MRR
      -> 调用 RAG 检索，比对 expected_passage_ids

纪律
----
- **不修改任何目标数字**：目标一律从 ``metrics.TARGETS`` 读取。
- **不为通过而放宽判据**：本模块只做测量；未达标就如实输出未达标。
- **无法测量的指标保持 not_computable**，绝不用占位值冒充。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# 允许以脚本方式运行（python eval/scripts/run_eval.py）
_THIS = Path(__file__).resolve()
_EVAL_DIR = _THIS.parent.parent
_REPO_ROOT = _EVAL_DIR.parent
_BACKEND = _REPO_ROOT / "backend"
for _p in (str(_BACKEND), str(_EVAL_DIR / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from metrics import TARGETS  # noqa: E402
from schema import load_jsonl  # noqa: E402


def _load(name: str) -> List[Dict[str, Any]]:
    path = _EVAL_DIR / f"{name}.jsonl"
    if not path.exists():
        return []
    return load_jsonl(path)


# ---------------------------------------------------------------------------
# Quote / Source 指标（PHASE 5 QuoteVerifier 真实运行）
# ---------------------------------------------------------------------------

def eval_quote_metrics() -> Dict[str, Any]:
    """在 quote_verification + source_attribution 上真实运行 QuoteVerifier。"""
    from app.services.quote_verifier import verify_quote

    qv = _load("quote_verification")
    sa = _load("source_attribution")

    q_total = q_correct = 0
    q_detail: List[Dict[str, Any]] = []
    for rec in qv:
        expected = rec.get("expected", {})
        result = verify_quote(rec.get("quote", ""), rec.get("claimed_source", ""))
        ok = result.quote_exists == bool(expected.get("quote_exists"))
        q_total += 1
        q_correct += int(ok)
        if not ok:
            q_detail.append({"id": rec.get("id"), "got": result.quote_exists,
                             "want": expected.get("quote_exists")})

    s_total = s_correct = 0
    s_detail: List[Dict[str, Any]] = []
    for rec in sa:
        result = verify_quote(rec.get("quote", ""), rec.get("claimed_source", ""))
        ok = result.source_correct == bool(rec.get("expected_source_correct"))
        s_total += 1
        s_correct += int(ok)
        if not ok:
            s_detail.append({"id": rec.get("id"), "got": result.source_correct,
                             "want": rec.get("expected_source_correct")})

    return {
        "quote_exactness": {
            "value": (q_correct / q_total) if q_total else None,
            "target": TARGETS["quote_exactness"],
            "passed": (q_correct / q_total) >= TARGETS["quote_exactness"] if q_total else None,
            "samples": q_total,
            "failures": q_detail[:10],
        },
        "source_attribution": {
            "value": (s_correct / s_total) if s_total else None,
            "target": TARGETS["source_attribution"],
            "passed": (s_correct / s_total) >= TARGETS["source_attribution"] if s_total else None,
            "samples": s_total,
            "failures": s_detail[:10],
        },
    }


# ---------------------------------------------------------------------------
# 对抗套件（Fabricated Classical Quote）
# ---------------------------------------------------------------------------

def eval_adversarial() -> Dict[str, Any]:
    """运行 adversarial_quotes，统计「明显伪造名言通过验证」的条数。

    brief 第十七章要求 Fabricated Classical Quote ≈ 0，且
    「任何明显伪造名言通过验证 -> 立即 FAIL」。
    """
    from app.services.quote_verifier import verify_quote
    from app.services.trust_state import is_displayable_as_classic

    records = _load("adversarial_quotes")
    fabricated_passed: List[Dict[str, Any]] = []
    checked = 0
    for rec in records:
        inp = rec.get("input", {})
        exp = rec.get("expected", {})
        result = verify_quote(inp.get("quote", ""), inp.get("claimed_source", ""))
        checked += 1
        if exp.get("quote_exists") is False and result.quote_exists:
            fabricated_passed.append({"id": rec.get("id"),
                                      "reason": "expected quote_exists=False but got True"})
            continue
        if exp.get("must_not_display_as_classic") and is_displayable_as_classic(result.trust_state):
            fabricated_passed.append({
                "id": rec.get("id"),
                "reason": f"trust_state={result.trust_state} is displayable as classic",
            })

    return {
        "fabricated_classical_quote": {
            "value": len(fabricated_passed),
            "target": TARGETS["fabricated_classical_quote"],
            "passed": len(fabricated_passed) <= TARGETS["fabricated_classical_quote"],
            "samples": checked,
            "failures": fabricated_passed[:10],
        }
    }


# ---------------------------------------------------------------------------
# 拒答（Unsupported Correct Refusal）
# ---------------------------------------------------------------------------

def eval_unsupported_refusal() -> Dict[str, Any]:
    """对 unsupported_questions 真实检索：无足够证据时必须拒答。"""
    import asyncio

    from app.services.rag_service import get_rag_service
    from app.services.trust_state import INSUFFICIENT_EVIDENCE_MESSAGE

    rag = get_rag_service()
    records = _load("unsupported_questions")
    correct = 0
    failures: List[Dict[str, Any]] = []
    for rec in records:
        q = rec.get("question", "")
        hits = 0
        for sage in ("confucius", "laozi", "mozi", "hanfeizi"):
            res = asyncio.run(rag.retrieve_for_debate_sage(sage, q, top_k=3))
            hits += len(res.get("verses", []))
        if hits == 0:
            correct += 1
        else:
            failures.append({"id": rec.get("id"), "question": q[:30], "spurious_hits": hits})

    total = len(records)
    return {
        "unsupported_correct_refusal": {
            "value": (correct / total) if total else None,
            "target": TARGETS["unsupported_correct_refusal"],
            "passed": (correct / total) >= TARGETS["unsupported_correct_refusal"] if total else None,
            "samples": total,
            "refusal_message_required": INSUFFICIENT_EVIDENCE_MESSAGE,
            "failures": failures[:10],
        }
    }


# ---------------------------------------------------------------------------
# 学派泄露（School Leakage）
# ---------------------------------------------------------------------------

def eval_school_leakage() -> Dict[str, Any]:
    """检查各派检索结果是否越派（school_consistency 数据集）。"""
    import asyncio

    from app.services.rag_service import get_rag_service

    rag = get_rag_service()
    records = _load("school_consistency")
    total = leaked = 0
    failures: List[Dict[str, Any]] = []
    for rec in records:
        sage = rec.get("sage_key", "")
        forbidden = rec.get("forbidden_books", []) or []
        res = asyncio.run(rag.retrieve_for_debate_sage(sage, rec.get("query", ""), top_k=3))
        for v in res.get("verses", []):
            total += 1
            src = v.get("source", "")
            if any(fb and fb in src for fb in forbidden):
                leaked += 1
                failures.append({"id": rec.get("id"), "sage": sage, "source": src})

    if total == 0:
        return {
            "school_leakage": {
                "value": None,
                "status": "not_computable",
                "reason": "各派检索均未返回条目，样本量为 0，无法计算泄漏率（不用 0.0 冒充无泄漏）",
                "target": TARGETS["school_leakage_max"],
                "passed": None,
                "samples": 0,
            }
        }
    return {
        "school_leakage": {
            "value": leaked / total,
            "target": TARGETS["school_leakage_max"],
            "passed": (leaked / total) < TARGETS["school_leakage_max"],
            "samples": total,
            "leaked": leaked,
            "failures": failures[:10],
        }
    }


# ---------------------------------------------------------------------------
# 检索 Recall / MRR
# ---------------------------------------------------------------------------

def _matches(got: str, expected: set) -> bool:
    """语料 passage_id 前缀不统一（lunyu:15.24 / daodejing-08-01 / commentary:12.2），
    而 sage_chat 返回 verse_id，故做双向宽松匹配。"""
    if not got:
        return False
    if got in expected:
        return True
    tail = got.split(":", 1)[-1]
    return any(exp.split(":", 1)[-1] == tail for exp in expected)


def eval_retrieval() -> Dict[str, Any]:
    """对 retrieval_gold 运行真实检索，计算 Recall@1/3/5 与 MRR。"""
    import asyncio

    from app.services.rag_service import get_rag_service

    rag = get_rag_service()
    records = _load("retrieval_gold")
    hits_at = {1: 0, 3: 0, 5: 0}
    rr_sum = 0.0
    total = 0
    failures: List[Dict[str, Any]] = []
    for rec in records:
        expected = set(rec.get("expected_passage_ids", []) or [])
        if not expected:
            continue
        total += 1
        res = asyncio.run(rag.retrieve_for_sage_chat(rec.get("query", ""), top_k=5))
        got_ids = [str(v.get("verse_id", "")) for v in res.get("verses", [])]
        rank = None
        for i, g in enumerate(got_ids, start=1):
            if _matches(g, expected):
                rank = i
                break
        for k in (1, 3, 5):
            if rank is not None and rank <= k:
                hits_at[k] += 1
        if rank is not None:
            rr_sum += 1.0 / rank
        else:
            failures.append({"id": rec.get("id"), "expected": sorted(expected)[:3], "got": got_ids[:3]})

    return {
        "retrieval": {
            "recall_at_1": (hits_at[1] / total) if total else None,
            "recall_at_3": (hits_at[3] / total) if total else None,
            "recall_at_5": (hits_at[5] / total) if total else None,
            "mrr": (rr_sum / total) if total else None,
            "target_recall_at_5": TARGETS["recall_at_5"],
            "passed": (hits_at[5] / total) >= TARGETS["recall_at_5"] if total else None,
            "samples": total,
            "failures": failures[:10],
        }
    }


# ---------------------------------------------------------------------------
# Claim-Evidence 覆盖率
# ---------------------------------------------------------------------------

def eval_claim_coverage() -> Dict[str, Any]:
    """在 retrieval_gold 的期望证据上运行 Claim-Evidence 绑定。"""
    from app.schemas.knowledge import EvidenceItem, EvidencePack
    from app.services.claim_evidence import Claim, verify_claims
    from app.services.quote_verifier import load_corpus

    corpus = {e.passage_id: e for e in load_corpus()}
    records = _load("retrieval_gold")
    total = covered = 0
    failures: List[Dict[str, Any]] = []
    for rec in records:
        expected = list(rec.get("expected_passage_ids", []) or [])
        if not expected:
            continue
        total += 1
        evidence = []
        for pid in expected:
            entry = corpus.get(pid)
            if entry is None:
                continue
            evidence.append(EvidenceItem(
                evidence_id=pid,
                original=entry.original,
                source=entry.source,
                text_type=entry.text_type,
                relevance=1.0,
            ))
        if not evidence:
            failures.append({"id": rec.get("id"), "reason": "no corpus entry for expected ids"})
            continue
        pack = EvidencePack(query=rec.get("query", ""), evidence=evidence)
        claim = Claim(claim_id="c1", text=rec.get("query", ""),
                      evidence_ids=tuple(e.evidence_id for e in evidence))
        result = verify_claims([claim], pack)
        if result.results[0].has_evidence:
            covered += 1
        else:
            failures.append({"id": rec.get("id"), "expected": expected[:3]})

    return {
        "core_claim_evidence_coverage": {
            "value": (covered / total) if total else None,
            "target": TARGETS["core_claim_evidence_coverage"],
            "passed": (covered / total) >= TARGETS["core_claim_evidence_coverage"] if total else None,
            "samples": total,
            "failures": failures[:10],
        }
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_all() -> Dict[str, Any]:
    """依次运行各指标。键名即指标名；单个失败不影响其余。"""
    out: Dict[str, Any] = {}
    for fn in (
        eval_quote_metrics,
        eval_adversarial,
        eval_unsupported_refusal,
        eval_school_leakage,
        eval_retrieval,
        eval_claim_coverage,
    ):
        try:
            produced = fn()
            if isinstance(produced, dict):
                out.update(produced)
        except Exception as exc:
            out[fn.__name__] = {
                "value": None,
                "status": "error",
                "reason": f"{type(exc).__name__}: {exc}",
            }
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="对真实系统运行 Eval 并输出实测指标")
    ap.add_argument("--out", default=str(_EVAL_DIR / "eval-run.json"))
    args = ap.parse_args(argv)

    results = run_all()
    payload = {
        "note": "实测结果：由 eval/scripts/run_eval.py 对真实实现运行得出。目标数字来自 metrics.TARGETS，未做任何修改。",
        "targets_frozen": TARGETS,
        "results": results,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
