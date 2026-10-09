"""
FIX-001：quote_exactness 的基线抓取与失败分类。

纪律
----
- **不重新实现任何指标逻辑**：聚合分数一律调用
  ``metrics.compute_quote_exactness``（冻结实现）。
- 逐用例的 pass/fail 直接取该冻结实现返回的 ``failures`` 列表，
  不另写一套判分。
- 本脚本**不修改任何产品代码/测试/数据集**，只读并产出报告。

产物
----
``deliverables/kb-v1/fix-001/baseline.json`` / ``baseline.md``
``deliverables/kb-v1/fix-001/failure-analysis.json`` / ``failure-analysis.md``
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_THIS = Path(__file__).resolve()
_EVAL_DIR = _THIS.parent.parent
_REPO_ROOT = _EVAL_DIR.parent
_BACKEND = _REPO_ROOT / "backend"
for _p in (str(_BACKEND), str(_EVAL_DIR / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# SAFETY-001：绝不打开生产索引；本脚本若需索引只用生产副本
import os
import shutil
import tempfile  # noqa: E402

_PROD = (_BACKEND / "chroma_db").resolve()
_ISO = Path(tempfile.mkdtemp(prefix="wudian_fix001_iso_"))
if _PROD.exists():
    shutil.copytree(_PROD, _ISO, dirs_exist_ok=True)
os.environ["CHROMA_PERSIST_DIR"] = str(_ISO)

from metrics import TARGETS, compute_quote_exactness  # noqa: E402
from schema import load_jsonl  # noqa: E402

_DATASET = _EVAL_DIR / "quote_verification.jsonl"
_OUT_DIR = _REPO_ROOT / "deliverables" / "kb-v1" / "fix-001"

# 合同常量（与 quote_verifier 同源，不另造数字）
from app.services.quote_verifier import (  # noqa: E402
    MIN_FRAGMENT_CHARS,
    MIN_FULL_QUOTE_CHARS,
    _strip_punctuation,
    load_corpus,
    normalize_text,
    verify_quote,
)

_SENTENCE_MARKS = "。！？；"


# ---------------------------------------------------------------------------
# 合同语义判定（用于分类，**不用于计分**）
# ---------------------------------------------------------------------------

def _raw_span(entry_original: str, quote_norm: str) -> Optional[tuple]:
    """把归一化命中区间映射回原文下标区间 (start, end)，含端点。"""
    pos = 0
    start = end = None
    for i, ch in enumerate(entry_original):
        if _strip_punctuation(ch):
            if pos == 0 and start is None:
                start = i
            if pos == len(quote_norm) - 1:
                end = i
                break
            pos += 1
    if start is None or end is None:
        return None
    return start, end


def contract_view(quote: str, claimed_source: str, corpus) -> Dict[str, Any]:
    """按 CONTRACT-001 v2 推导各字段（分析用，计分仍用冻结实现）。"""
    qn = normalize_text(quote)
    if len(qn) < MIN_FRAGMENT_CHARS:
        return {
            "admissible": False, "quote_exists": False, "exact_match": False,
            "matched_passage": None, "matched_text_type": None,
            "crosses_sentence_boundary": None, "gate": False,
            "displayable": False, "root_cause": "minimum-length gate",
        }

    hits = [e for e in corpus if qn in e.norm]
    if not hits:
        return {
            "admissible": True, "quote_exists": False, "exact_match": False,
            "matched_passage": None, "matched_text_type": None,
            "crosses_sentence_boundary": None, "gate": len(qn) >= MIN_FULL_QUOTE_CHARS,
            "displayable": False, "root_cause": "corpus absence",
        }

    # 选最佳命中：优先 L1，其次正文最短（与实现同精神）
    def rank(e):
        return (0 if e.text_type == "original" else 1, len(e.norm), e.passage_id)

    best = sorted(hits, key=rank)[0]
    span = _raw_span(best.original, qn)
    crosses = False
    if span is not None:
        inner = best.original[span[0]: span[1] + 1]
        # 原始引文自身含句界标点 -> 属显式跨句引用，不算违规
        raw_has_mark = any(m in quote for m in _SENTENCE_MARKS)
        crosses = any(m in inner for m in _SENTENCE_MARKS) and not raw_has_mark

    gate = len(qn) >= MIN_FULL_QUOTE_CHARS
    is_l1 = best.text_type == "original"
    return {
        "admissible": True,
        "quote_exists": True,
        "exact_match": not crosses,          # §2.2：不跨句界即为 exact
        "matched_passage": best.passage_id,
        "matched_text_type": best.text_type,
        "crosses_sentence_boundary": crosses,
        "gate": gate,
        "displayable": bool(not crosses and gate and is_l1),
        "root_cause": None,
    }


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def build() -> Dict[str, Any]:
    records = load_jsonl(_DATASET)
    corpus = load_corpus()

    preds: List[Dict[str, Any]] = []
    for rec in records:
        r = verify_quote(rec.get("quote", ""), rec.get("claimed_source", ""))
        preds.append({
            "quote_exists": r.quote_exists,
            "exact_match": r.exact_match,
            "normalized_match": r.normalized_match,
            "source_correct": r.source_correct,
            "correct_source": r.correct_source,
            "trust_state": r.trust_state,
            "match_type": r.match_type,
            "similarity": r.similarity,
        })

    # === 冻结实现：唯一计分来源 ===
    frozen = compute_quote_exactness(records, preds)
    failed_ids = {f["id"] for f in frozen["failures"]}

    cases = []
    for rec, pred in zip(records, preds):
        cv = contract_view(rec.get("quote", ""), rec.get("claimed_source", ""), corpus)
        counted = bool(pred["quote_exists"])          # 冻结分母口径
        passed = None if not counted else (rec["id"] not in failed_ids)
        cases.append({
            "id": rec.get("id"),
            "quote": rec.get("quote"),
            "claimed_source": rec.get("claimed_source"),
            "expected": rec.get("expected"),
            "predicted": pred,
            "contract_view": cv,
            "counted_in_denominator": counted,
            "pass": passed,
        })

    return {
        "dataset": _DATASET.name,
        "dataset_size": len(records),
        "frozen_metric": frozen,
        "targets": {"quote_exactness": TARGETS["quote_exactness"]},
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------

def write_reports(b: Dict[str, Any]) -> None:
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    frozen = b["frozen_metric"]

    baseline = {
        "note": "冻结实现 metrics.compute_quote_exactness 的原始输出，未经改动。",
        "dataset": b["dataset"],
        "dataset_size": b["dataset_size"],
        "numerator": frozen["numerator"],
        "denominator": frozen["denominator"],
        "score": frozen["value"],
        "target": frozen["target"],
        "passed": frozen["passed"],
        "cases": b["cases"],
    }
    (_OUT_DIR / "baseline.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# FIX-001 基线（冻结 quote_exactness）", "",
        f"- 数据集：`{b['dataset']}`，条数 **{b['dataset_size']}**",
        f"- 分子：**{frozen['numerator']}**",
        f"- 分母：**{frozen['denominator']}**（= 系统判为 `quote_exists=True` 的条数）",
        f"- 分数：**{frozen['value']:.4f}**（目标 ≥ {frozen['target']}）",
        f"- 判定：**{'PASS' if frozen['passed'] else 'FAIL'}**",
        "",
        "> 计分完全由冻结实现 `eval/scripts/metrics.py:compute_quote_exactness` 产生，",
        "> 本报告未重新实现任何指标逻辑。",
        "",
        "## 逐用例", "",
        "| id | quote | claimed | exists | exact(pred) | exact(exp) | counted | pass |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in b["cases"]:
        exp = c["expected"] or {}
        p = c["predicted"]
        lines.append(
            f"| {c['id']} | `{c['quote']}` | {c['claimed_source']} | "
            f"{p['quote_exists']} | {p['exact_match']} | {exp.get('exact_match')} | "
            f"{c['counted_in_denominator']} | {c['pass']} |"
        )
    (_OUT_DIR / "baseline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_failure_analysis(b: Dict[str, Any]) -> None:
    frozen = b["frozen_metric"]
    failures = [c for c in b["cases"] if c["pass"] is False]
    # 仅供参考：这些不在冻结分母内，但值得并列显示
    excluded = [c for c in b["cases"] if c["pass"] is None]

    classified = []
    for c in failures:
        exp = c["expected"] or {}
        cv = c["contract_view"]
        p = c["predicted"]
        # 主根因判定（单一）
        if cv["quote_exists"] and cv["exact_match"] and not p["exact_match"]:
            cause = "substring contract"
            detail = ("实现要求引文等于**整条** passage；合同要求"
                      "「归一化后为连续子串」。引文确实逐字存在于该 passage 中。")
        elif not cv["quote_exists"]:
            cause = cv["root_cause"] or "corpus absence"
            detail = "按合同该引文不存在（或不可采），故不应计入分子。"
        else:
            cause = "verifier implementation defect"
            detail = "实现判定与合同不符。"
        # RFC-1 叠加标记：期望标签与冻结分子互相矛盾
        conflict = (exp.get("exact_match") is False
                    and cv["quote_exists"] and cv["exact_match"])
        classified.append({
            "id": c["id"],
            "quote": c["quote"],
            "claimed_source": c["claimed_source"],
            "expected_exact_match": exp.get("exact_match"),
            "expected_trust_state": exp.get("trust_state"),
            "predicted_exact_match": p["exact_match"],
            "predicted_match_type": p["match_type"],
            "contract_exact_match": cv["exact_match"],
            "contract_matched_passage": cv["matched_passage"],
            "contract_text_type": cv["matched_text_type"],
            "crosses_sentence_boundary": cv["crosses_sentence_boundary"],
            "primary_root_cause": cause,
            "detail": detail,
            "dataset_semantic_conflict": conflict,
        })

    from collections import Counter
    tally = Counter(x["primary_root_cause"] for x in classified)

    doc = {
        "note": ("失败分类。聚合分数取自冻结实现；分类为分析结论，不改动任何数据。"),
        "denominator": frozen["denominator"],
        "numerator": frozen["numerator"],
        "score": frozen["value"],
        "failure_count": len(classified),
        "root_cause_tally": dict(tally),
        "failures": classified,
        "excluded_from_denominator": [
            {
                "id": c["id"], "quote": c["quote"],
                "predicted_quote_exists": c["predicted"]["quote_exists"],
                "expected_quote_exists": (c["expected"] or {}).get("quote_exists"),
                "contract_quote_exists": c["contract_view"]["quote_exists"],
                "contract_root_cause": c["contract_view"]["root_cause"],
            }
            for c in excluded
        ],
    }
    (_OUT_DIR / "failure-analysis.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# FIX-001 失败分类", "",
        f"- 冻结分母 {frozen['denominator']}，分子 {frozen['numerator']}，"
        f"分数 {frozen['value']:.4f}",
        f"- 失败条数：**{len(classified)}**",
        "",
        "## 主根因统计", "",
    ]
    for k, v in tally.most_common():
        lines.append(f"- `{k}`：**{v}**")
    lines += ["", "## 逐条失败", "",
              "| id | quote | contract exact | pred exact | exp exact | 主根因 | RFC-1 冲突 |",
              "|---|---|---|---|---|---|---|"]
    for x in classified:
        lines.append(
            f"| {x['id']} | `{x['quote']}` | {x['contract_exact_match']} | "
            f"{x['predicted_exact_match']} | {x['expected_exact_match']} | "
            f"`{x['primary_root_cause']}` | {x['dataset_semantic_conflict']} |")
    lines += ["", "## 未计入分母的用例（合同与实现一致：均判不存在）", "",
              "| id | quote | pred exists | exp exists | 合同根因 |", "|---|---|---|---|---|"]
    for c in excluded:
        lines.append(
            f"| {c['id']} | `{c['quote']}` | {c['predicted']['quote_exists']} | "
            f"{(c['expected'] or {}).get('quote_exists')} | "
            f"`{c['contract_view']['root_cause']}` |")
    (_OUT_DIR / "failure-analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    b = build()
    write_reports(b)
    write_failure_analysis(b)
    f = b["frozen_metric"]
    print(f"dataset_size={b['dataset_size']} numerator={f['numerator']} "
          f"denominator={f['denominator']} score={f['value']:.4f} passed={f['passed']}")
    print(f"wrote -> {_OUT_DIR}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        shutil.rmtree(_ISO, ignore_errors=True)
