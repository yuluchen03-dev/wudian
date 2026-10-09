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

# SAFETY-001：绝不打开生产索引。
# C5 修复：早前实现**无条件**把 4.3 MB 生产索引 copytree 到临时目录，
# 并且会覆盖调用方显式设置的 CHROMA_PERSIST_DIR，还在"被 import 而非 __main__"
# 时泄漏临时目录。本脚本实际**不使用 chroma**（只用 metrics 与 load_corpus 的
# JSON），因此：
#   1) 调用方已显式设置 CHROMA_PERSIST_DIR 时**不再覆盖**；
#   2) 不做无谓的生产索引复制；
#   3) 用 atexit 保证临时目录一定会被清理。
import atexit  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402

_PROD = (_BACKEND / "chroma_db").resolve()
if not os.environ.get("CHROMA_PERSIST_DIR"):
    _ISO = Path(tempfile.mkdtemp(prefix="wudian_fix001_iso_"))
    atexit.register(shutil.rmtree, _ISO, True)
    os.environ["CHROMA_PERSIST_DIR"] = str(_ISO)

from metrics import TARGETS, compute_quote_exactness  # noqa: E402
from schema import load_jsonl  # noqa: E402

_DATASET = _EVAL_DIR / "quote_verification.jsonl"
# 产物目录。
# ⚠️ **冻结的修复前基线**位于 `deliverables/kb-v1/fix-001/`（固定于 commit d7ef182），
# 属不可变证据，**不得**被本工具覆盖。本工具测的是**当前** production，
# 因此默认写入 `fix-001/current/` 子目录，避免把修复后的 1.0000 写进基线文件。
_OUT_DIR = _REPO_ROOT / "deliverables" / "kb-v1" / "fix-001" / "current"

# 合同常量（与 quote_verifier 同源，不另造数字）
from app.services.quote_verifier import (  # noqa: E402
    MIN_FRAGMENT_CHARS,
    MIN_FULL_QUOTE_CHARS,
    crosses_sentence_boundary,
    load_corpus,
    normalize_text,
    verify_quote,
)


# ---------------------------------------------------------------------------
# 合同语义判定（用于分类，**不用于计分**）
# ---------------------------------------------------------------------------
# 注：句界判定（§3.3）已改为直接复用 production 的
# `quote_verifier.crosses_sentence_boundary`（单一真值来源）。
# 早前本文件自带 `_raw_span`/`_SENTENCE_MARKS` 实现，存在两处缺陷（复核 C1/C2）：
#   C1 `_raw_span` 把归一化下标误当原文前 N 个非标点字符，跨度定位错误，
#      会在**错误的区间**上判句界（对 lunyu:15.24 得 (0,9) 而非真实跨度）；
#   C2 `_SENTENCE_MARKS` 多含「；」，而 §3.3 只列「。！？」。
# 二者对当期数据均无影响（18 条命中跨度全部未跨句），但作为第二套逻辑有分叉风险，
# 故整体删除、改为复用。


def contract_view(quote: str, claimed_source: str, corpus,
                  source_correct: Optional[bool] = None) -> Dict[str, Any]:
    """按 CONTRACT-001 v2 推导各字段（分析用，计分仍用冻结实现）。

    C3 修复：``displayable`` 原先漏掉 ``source_correct``，与 §3.2/§4 规则 3 不符
    （对一条**故意写错出处**的引文也会返回 displayable=true）。
    现要求调用方传入 ``source_correct``（取自 production 判定），并纳入合取。
    """
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
    # C1/C2 修复：**复用 production 的权威实现**，不再自带一套跨度/句界逻辑。
    # 旧实现的 `_raw_span` 把「归一化下标」错误地当成「原文前 N 个非标点字符」，
    # 对 lunyu:15.24 会得到 (0,9)（解码为「子贡问曰：「有一言而」」）而非真实跨度，
    # 因而在**错误的跨度**上判 §3.3；且它把「；」也当作句界，与 §3.3 不一致。
    # 现直接调用 quote_verifier.crosses_sentence_boundary（单一真值来源）。
    crosses = crosses_sentence_boundary(best.original, qn, quote)

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
        # §3.2/§4 规则 3：展示须同时满足 exists ∧ exact ∧ source ∧ gate ∧ L1
        "displayable": bool(
            (not crosses) and gate and is_l1
            and (source_correct if source_correct is not None else False)
        ),
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
        cv = contract_view(
            rec.get("quote", ""), rec.get("claimed_source", ""), corpus,
            source_correct=pred["source_correct"],
        )
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
    raise SystemExit(main())
