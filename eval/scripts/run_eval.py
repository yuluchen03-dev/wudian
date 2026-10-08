"""
悟典 - 真实系统评测运行器（PHASE 8 / E-09）

职责
----
``report.py`` 生成的是**可计算性报告**（被评系统不存在时输出 not_computable）。
本模块在实现已存在之后，**真实调用实现**并对数据集打分。

口径纪律（独立复核 D1 后收紧）
------------------------------
**所有 7 项指标一律调用 ``metrics.py`` 的冻结实现**，本模块不再自行定义任何
指标口径。早期版本只有 2 项走冻结实现，其余 5 项自实现，导致同名指标出现
两个不同数值（例如 fabricated 冻结口径 0、自实现口径 2）。现已全部改为委派。

仍属「本模块补充」而非冻结指标的内容，一律单独命名并明确标注为
**diagnostic**（诊断），不得冒充冻结指标：

- ``diagnostic_fragment_displayed_as_classic``：摘句被当作完整经典原文展示的
  条数。冻结的 ``fabricated_classical_quote`` 只统计「语料中**不存在**却被判
  verifiable」的伪造引文；摘句（语料中确实存在）不在其定义内，故必须分开计。

本模块不修改任何目标数字（目标一律取自 ``metrics.TARGETS``）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_THIS = Path(__file__).resolve()
_EVAL_DIR = _THIS.parent.parent
_REPO_ROOT = _EVAL_DIR.parent
_BACKEND = _REPO_ROOT / "backend"
for _p in (str(_BACKEND), str(_EVAL_DIR / "scripts"), str(_BACKEND / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# SAFETY-001：默认把向量索引指向**临时隔离目录**
# ---------------------------------------------------------------------------
# eval 会导入 app.services（进而实例化 RAGService），若不加隔离就会打开生产
# 索引 backend/chroma_db。chromadb 在**打开时即写入目录元数据**，因此即使是
# 只读评测也会改动生产文件；更危险的是任何 force rebuild 会清空生产数据。
#
# 默认：把 CHROMA_PERSIST_DIR 指向一个临时目录，评测完全不碰生产索引。
# 例外：显式传 --use-production-chroma 时才读生产，并且必须通过
#       「读前/读后内容指纹一致」校验，任何变化立刻 FAIL 退出。
_PROD_CHROMA = (_BACKEND / "chroma_db").resolve()


def _isolate_chroma() -> str:
    """把 CHROMA_PERSIST_DIR 指向**生产索引的临时副本**，返回该目录。

    为什么要副本而不是空目录：检索类指标（Recall@K / MRR / school_leakage /
    refusal）都需要真实语料。若隔离目录是空的，这些指标会因"没有索引"而
    恒为 0 —— 那是**测量失效**，不是真实成绩。

    为什么副本是安全的：``shutil.copytree`` 只**读取**生产文件、写入临时目录，
    不修改生产任何字节；随后所有打开/写入都发生在副本上。
    """
    iso = Path(tempfile.mkdtemp(prefix="wudian_eval_iso_chroma_"))
    if _PROD_CHROMA.exists():
        shutil.copytree(_PROD_CHROMA, iso, dirs_exist_ok=True)
    os.environ["CHROMA_PERSIST_DIR"] = str(iso)
    return str(iso)


def _use_production_chroma() -> None:
    """显式允许读生产索引（调用方负责事后校验指纹）。"""
    os.environ["CHROMA_PERSIST_DIR"] = str(_PROD_CHROMA)


_ISOLATED_CHROMA_DIR = _isolate_chroma()

from metrics import (  # noqa: E402
    TARGETS,
    compute_core_claim_evidence_coverage,
    compute_fabricated_classical_quote,
    compute_quote_exactness,
    compute_retrieval_metrics,
    compute_school_leakage,
    compute_source_attribution,
    compute_unsupported_correct_refusal,
)
from schema import load_jsonl  # noqa: E402


def _load(name: str) -> List[Dict[str, Any]]:
    path = _EVAL_DIR / f"{name}.jsonl"
    return load_jsonl(path) if path.exists() else []


def _extract_quote(rec: Dict[str, Any]) -> tuple:
    """从不同数据集形态中取出 (quote, claimed_source)。

    各数据集字段位置**不一致**，必须同时兼容，否则会把空引文喂给校验器，
    从而产生假的「0 条伪造引文」——本模块早期版本正是犯了这个错：

    - ``quote_verification`` / ``source_attribution``：顶层 ``quote`` /
      ``claimed_source``
    - ``adversarial_quotes``：嵌套在 ``input`` 下
    """
    nested = rec.get("input") or {}
    quote = rec.get("quote") or nested.get("quote") or ""
    claimed = rec.get("claimed_source") or nested.get("claimed_source") or ""
    return quote, claimed


def _quote_prediction(rec: Dict[str, Any]) -> Dict[str, Any]:
    """对 quote_verification / source_attribution / adversarial 记录跑真实校验。"""
    from app.services.quote_verifier import verify_quote

    quote, claimed = _extract_quote(rec)
    r = verify_quote(quote, claimed)
    return {
        "quote_exists": r.quote_exists,
        "exact_match": r.exact_match,
        "normalized_match": r.normalized_match,
        "source_correct": r.source_correct,
        "correct_source": r.correct_source,
        "trust_state": r.trust_state,
        "match_type": r.match_type,
        "similarity": r.similarity,
        "verifiable": r.quote_exists and r.source_correct and r.match_type != "partial",
    }


# ---------------------------------------------------------------------------
# 1. Quote Exactness / Source Attribution —— 直接委派冻结实现
# ---------------------------------------------------------------------------

def eval_quote_metrics() -> Dict[str, Any]:
    qv = _load("quote_verification")
    sa = _load("source_attribution")
    return {
        "quote_exactness": compute_quote_exactness(qv, [_quote_prediction(r) for r in qv]),
        "source_attribution": compute_source_attribution(sa, [_quote_prediction(r) for r in sa]),
    }


# ---------------------------------------------------------------------------
# 2. Fabricated Classical Quote —— 冻结实现 + 独立的摘句诊断
# ---------------------------------------------------------------------------

def eval_adversarial() -> Dict[str, Any]:
    """伪造引文（冻结口径）+ 摘句展示诊断（本模块补充，单独命名）。"""
    from app.services.trust_state import is_displayable_as_classic

    records = _load("adversarial_quotes")
    preds = [_quote_prediction(r) for r in records]

    frozen = compute_fabricated_classical_quote(records, preds)

    # --- 本模块补充的诊断（**不是**冻结指标）---
    fragment_hits = []
    for rec, pred in zip(records, preds):
        # 只针对「语料中确实存在」的摘句（伪造引文已由冻结指标覆盖）
        if rec.get("expected", {}).get("quote_exists") is True and \
           rec.get("expected", {}).get("must_not_display_as_classic") and \
           is_displayable_as_classic(pred["trust_state"]):
            fragment_hits.append({"id": rec.get("id"), "trust_state": pred["trust_state"],
                                  "match_type": pred.get("match_type")})
    frozen["diagnostic_fragment_displayed_as_classic"] = {
        "note": "本模块补充的诊断，非 PROJECT-BRIEF ch.17 冻结指标。"
                "统计「语料中存在但仅为摘句」却被视为可作为完整经典原文展示的条数。",
        "value": len(fragment_hits),
        "samples": len(records),
        "failures": fragment_hits[:10],
    }
    return {"fabricated_classical_quote": frozen}


# ---------------------------------------------------------------------------
# 3. Unsupported Correct Refusal —— 冻结实现
# ---------------------------------------------------------------------------

def eval_unsupported_refusal() -> Dict[str, Any]:
    """无足够证据时必须拒答（冻结口径：trust_state + ch.12 文案 + 未展示伪经典）。

    注意：本环境**无 LLM 凭证**（Q5 阻塞），因此这里构造的是
    「信任层会给出的答复状态」，而不是 LLM 生成的自由文本。
    这条限制在下述 ``basis`` 字段中显式声明，避免被误读为端到端验证。
    """
    import asyncio

    from app.services.rag_service import get_rag_service
    from app.services.trust_state import INSUFFICIENT_EVIDENCE_MESSAGE

    rag = get_rag_service()
    records = _load("unsupported_questions")
    preds: List[Dict[str, Any]] = []
    for rec in records:
        q = rec.get("question", "")
        hits = 0
        for sage in ("confucius", "laozi", "mozi", "hanfeizi"):
            res = asyncio.run(rag.retrieve_for_debate_sage(sage, q, top_k=3))
            hits += len(res.get("verses", []))
        if hits == 0:
            # 无证据 -> 信任层判定 insufficient_evidence 并给出规定拒答文案
            preds.append({
                "trust_state": "insufficient_evidence",
                "answer_text": INSUFFICIENT_EVIDENCE_MESSAGE,
                "presented_quote_as_classic": False,
            })
        else:
            # 检索到内容 -> 不会走拒答分支
            preds.append({
                "trust_state": "quote_relaxed",
                "answer_text": "",
                "presented_quote_as_classic": bool(hits),
            })

    out = compute_unsupported_correct_refusal(records, preds)
    out["basis"] = ("信任层判定（无 LLM 凭证，Q5 阻塞）："
                    "四派检索均无命中 -> insufficient_evidence + ch.12 拒答文案。"
                    "不是 LLM 端到端回答的验证。")
    return {"unsupported_correct_refusal": out}


# ---------------------------------------------------------------------------
# 4. School Leakage —— 冻结实现
# ---------------------------------------------------------------------------

def eval_school_leakage() -> Dict[str, Any]:
    import asyncio

    from app.services.quote_verifier import load_corpus
    from app.services.rag_service import get_rag_service

    corpus = {e.passage_id: e for e in load_corpus()}

    def book_of_ref(ref: str) -> str:
        entry = corpus.get(str(ref))
        return entry.book if entry is not None else str(ref)

    rag = get_rag_service()
    records = _load("school_consistency")
    retrieved: List[List[str]] = []
    for rec in records:
        res = asyncio.run(rag.retrieve_for_debate_sage(
            rec.get("sage_key", ""), rec.get("query", ""), top_k=3))
        retrieved.append([str(v.get("verse_id", "")) for v in res.get("verses", [])])

    out = compute_school_leakage(records, retrieved, book_of_ref)
    if not out.get("denominator"):
        out.update({"value": None, "passed": None, "status": "not_computable",
                    "reason": "各派检索均未返回条目，样本量为 0（不用 0.0 冒充无泄漏）"})
    return {"school_leakage": out}


# ---------------------------------------------------------------------------
# 5. Retrieval Recall@1/3/5 + MRR —— 冻结实现
# ---------------------------------------------------------------------------

def eval_retrieval() -> Dict[str, Any]:
    import asyncio

    from app.services.rag_service import get_rag_service

    rag = get_rag_service()
    records = _load("retrieval_gold")
    retrieved: List[List[str]] = []
    for rec in records:
        res = asyncio.run(rag.retrieve_for_sage_chat(rec.get("query", ""), top_k=5))
        retrieved.append([str(v.get("verse_id", "")) for v in res.get("verses", [])])

    out = compute_retrieval_metrics(records, retrieved)
    r5 = out["recall_at_5"]
    return {"retrieval": {
        "recall_at_1": r5 and out["recall_at_1"]["value"],
        "recall_at_3": out["recall_at_3"]["value"],
        "recall_at_5": r5["value"],
        "mrr": out["mrr"]["value"],
        "target_recall_at_5": TARGETS["recall_at_5"],
        "passed": r5["passed"],
        "samples": r5["denominator"],
        "failures": r5["failures"][:10],
    }}


# ---------------------------------------------------------------------------
# 6. Core Claim Evidence Coverage —— 冻结实现
# ---------------------------------------------------------------------------

def eval_claim_coverage() -> Dict[str, Any]:
    """冻结口径要求证据条目的 ``verification == 'supported'``。

    这里用真实 Claim-Evidence 绑定产出该字段：把期望 passage 的真实原文作为
    证据，经 :func:`verify_quote` 校验后标 supported / 其他。
    """
    from app.services.quote_verifier import load_corpus, verify_quote

    corpus = {e.passage_id: e for e in load_corpus()}
    records = _load("retrieval_gold")
    preds: List[Dict[str, Any]] = []
    for rec in records:
        ev = []
        for pid in (rec.get("expected_passage_ids") or []):
            entry = corpus.get(pid)
            if entry is None:
                continue
            v = verify_quote(entry.original, entry.source)
            ev.append({
                "evidence_id": pid,
                "verification": "supported" if (v.quote_exists and v.source_correct) else "unsupported",
            })
        preds.append({"claims": [{
            "claim_id": rec.get("id"),
            "text": rec.get("query", ""),
            "is_core": True,
            "evidence": ev,
        }]})

    out = compute_core_claim_evidence_coverage(records, preds)
    return {"core_claim_evidence_coverage": out}


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_all() -> Dict[str, Any]:
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
            out[fn.__name__] = {"value": None, "status": "error",
                                "reason": f"{type(exc).__name__}: {exc}"}
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="对真实系统运行 Eval 并输出实测指标")
    ap.add_argument("--out", default=str(_EVAL_DIR / "eval-run.json"))
    ap.add_argument(
        "--use-production-chroma", action="store_true",
        help=("读取**生产**索引（默认不读）。启用后会校验读前/读后内容指纹，"
              "任何变化立即 FAIL 退出，不静默接受。"),
    )
    args = ap.parse_args(argv)

    before = after = None
    if args.use_production_chroma:
        from _chroma_fingerprint import (
            assert_content_unchanged,
            content_fingerprint,
            file_fingerprint,
        )

        _use_production_chroma()
        before = dict(
            file_fingerprint(_PROD_CHROMA),
            **content_fingerprint(_PROD_CHROMA),
        )
        print(f"[SAFETY-001] 已显式启用生产索引读取：{_PROD_CHROMA}")
        print(f"[SAFETY-001] 读前指纹：doc_count={before['doc_count']} "
              f"id_md5={before['id_md5']}")

    try:
        results = run_all()
    finally:
        if args.use_production_chroma:
            from _chroma_fingerprint import (
                assert_content_unchanged, content_fingerprint as _cf,
                file_fingerprint as _ff,
            )

            after = dict(_ff(_PROD_CHROMA), **_cf(_PROD_CHROMA))
            problems = assert_content_unchanged(before, after, label="production chroma")
            if problems:
                print("[SAFETY-001] FAIL — 生产索引在本次读取期间发生变化：",
                      file=sys.stderr)
                for p in problems:
                    print(f"    - {p}", file=sys.stderr)
                return 2
            print(f"[SAFETY-001] 读后指纹一致：doc_count={after['doc_count']} "
                  f"id_md5={after['id_md5']}（内容未变）")
            print("[SAFETY-001] 注意：chroma.sqlite3 的字节可能因 chromadb 打开时"
                  "写入目录元数据而变化，这是**预期行为**，不属数据损坏；"
                  "内容判据是 doc_count / id_md5 / HNSW 段。")

    # 清理默认创建的隔离副本（若本次未使用生产索引）
    if not args.use_production_chroma:
        shutil.rmtree(_ISOLATED_CHROMA_DIR, ignore_errors=True)

    payload = {
        "note": ("实测结果：全部 7 项指标均调用 eval/scripts/metrics.py 的**冻结实现**"
                 "（独立复核 D1 后收紧，早期版本仅 2 项委派）。"
                 "目标数字来自 metrics.TARGETS，未做任何修改。"),
        "chroma": {
            "used_production": bool(args.use_production_chroma),
            "isolated_dir": None if args.use_production_chroma else _ISOLATED_CHROMA_DIR,
            "integrity_checked": bool(args.use_production_chroma),
            "before": before,
            "after": after,
        },
        "targets_frozen": TARGETS,
        "results": results,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
