"""Generate eval-report.json / eval-report.md for WUDIAN-KB-V1.

Honesty contract:
  * Metrics that CANNOT be computed from the current data/capability are emitted
    with `"value": null` and an explicit `"status": "not_computable"` plus the
    reason.  They are never filled with a passing placeholder.
  * Target numbers are read from `metrics.TARGETS` and are never rewritten.

Usage:
    python eval/scripts/report.py --out eval/eval-report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

import metrics as M  # noqa: E402
import schema as S  # noqa: E402

# Which metrics are computable today, and why the others are not.
NOT_COMPUTABLE_REASONS: Dict[str, str] = {
    "quote_exactness":
        "需要 QuoteVerifier 产出 predictions（PHASE 5 未实现）；且无外部 LLM/verifier 运行。",
    "source_attribution":
        "需要 QuoteVerifier 的 source_correct 判定（PHASE 5 未实现）；现状 citation_validator 不校验出处。",
    "school_leakage":
        "需要 RAG V2 真实检索结果（PHASE 4 未实现）；且 sage-chat 主路径无学派过滤（G-D 未修复）。",
    "recall_at_k":
        "需要 RAG V2 真实检索（PHASE 4 未实现）。注：C1 已由 t20 修复"
        "（schemas/ai.py:25 verse_no 改为 Optional[str]），实测 retrieve('学而时习之') 已返回 5 条；"
        "但当前 hybrid_search 的排序质量尚未评估，且语料仅 143 条、12 部书目仅 4 部有数据。",
    "mrr":
        "同 Recall：依赖 RAG V2 与真实规模语料。",
    "unsupported_correct_refusal":
        "需要 Trust State 四态（PHASE 5 未实现）。另注意：C3 已在 _debate_keyword_search "
        "修复（rag_service.py:500 `if score <= 0: continue`），但 retrieve_for_debate_sage "
        "先走 _debate_vector_search（:1024）且无相关性阈值，实测垃圾查询仍返回 3 条 sim=0.0，"
        "故 insufficient_evidence 在该路径仍不可达。",
    "core_claim_evidence_coverage":
        "需要 Claim-Evidence 绑定（PHASE 5 未实现）。",
    "fabricated_classical_quote":
        "需要对抗套件对真实实现运行（PHASE 5）。数据集已就绪，但被评系统尚不存在。",
    "latency":
        "需要 RAG V2 实现后在真实规模语料上测量；当前 143 条基线不具代表性。",
}

EXPANSION_PLAN = {
    "current_total": None,  # filled at runtime
    "target_total": 1000,
    "method": (
        "按 book x concept x scenario 三维矩阵补齐缺口；每本书按章节分层抽样保证覆盖；"
        "新增数据集只用 derived 候选 + 真实人工确认后升级为 human；"
        "所有入库必须通过 validate_gold.py。"
    ),
    "constraints": [
        "禁止用 LLM 批量生成看似合理的 Gold 并标 human",
        "expected_passage_ids 只能指向语料中真实存在的条目",
        "不得为了凑数编造 passage 或出处",
    ],
    "blocked_by": [
        "PHASE 2 语料扩充（当前 12 部书目仅 4 部有数据）",
        "PHASE 1 passage_id 正式化",
        "真实人工标注资源（当前不可得，故全部为 derived）",
    ],
}


def build_report(eval_dir: Path) -> Dict[str, Any]:
    root = S.repo_root()
    corpus_index = S.load_corpus_index(root)

    datasets: List[Dict[str, Any]] = []
    prov_totals: Dict[str, int] = {}
    total = 0
    for name in S.DATASET_NAMES:
        path = eval_dir / S.DATASETS[name]["file"]
        recs = S.load_jsonl(path) if path.exists() else []
        prov: Dict[str, int] = {}
        for r in recs:
            p = r.get("provenance", "<missing>")
            prov[p] = prov.get(p, 0) + 1
            prov_totals[p] = prov_totals.get(p, 0) + 1
        total += len(recs)
        datasets.append({
            "name": name, "file": S.DATASETS[name]["file"],
            "description": S.DATASETS[name]["description"],
            "records": len(recs), "provenance": prov,
            "human_annotated": prov.get("human", 0),
        })

    # ---- metric sections.  All values are null: no evaluated system exists yet.
    def nc(metric: str, formula: str) -> Dict[str, Any]:
        return {"metric": metric, "formula": formula, "value": None,
                "status": "not_computable",
                "reason": NOT_COMPUTABLE_REASONS.get(metric, "未实现")}

    metric_section = {
        "quote_exactness": nc(
            "quote_exactness",
            "正确逐字匹配数 / 全部被判定为 quote_exists=True 的引文数"),
        "source_attribution": nc(
            "source_attribution",
            "source_correct 与期望一致数 / 全部引文数（独立于 quote_exists）"),
        "school_leakage": nc(
            "school_leakage",
            "越界引用数 / 总引用数（引用 source 不属于该 sage 的 allowed_books）"),
        "retrieval": {
            "recall_at_1": nc("recall_at_k", "(1/N) * sum(命中 expected ∩ top-1 非空)"),
            "recall_at_3": nc("recall_at_k", "(1/N) * sum(命中 expected ∩ top-3 非空)"),
            "recall_at_5": nc("recall_at_k", "(1/N) * sum(命中 expected ∩ top-5 非空)"),
            "mrr": nc("mrr", "(1/N) * sum(1 / 首个命中 rank)，无命中记 0"),
        },
        "unsupported_correct_refusal": nc(
            "unsupported_correct_refusal",
            "正确拒答数 / 应拒答数；拒答须同时满足 trust_state=insufficient_evidence、"
            "含 ch.12 拒答语、未展示任何经典原文"),
        "core_claim_evidence_coverage": nc(
            "core_claim_evidence_coverage",
            "有 >=1 条 verification=supported 证据的核心 claim 数 / 全部核心 claim 数"),
        "fabricated_classical_quote": nc(
            "fabricated_classical_quote",
            "expected.quote_exists=False 却被判 verifiable=True 的条数（目标绝对值为 0）"),
        "latency": nc("latency", "本地检索 P50 / P95（秒），排除外部 LLM"),
    }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "WUDIAN-KB-V1",
        "phase": "PHASE 0 (eval baseline only; no evaluated system exists yet)",
        "corpus": {
            "passage_ids_available": len(corpus_index),
            "by_kind": _count_by_kind(corpus_index),
            "source_files": [
                "data/processed/lunyu.json",
                "data/processed/debate_classics.json",
                "backend/data/commentaries/lunyu_zhuxi.json",
            ],
        },
        "datasets": datasets,
        "totals": {"records": total, "provenance": prov_totals,
                   "human_annotated": prov_totals.get("human", 0)},
        "targets_frozen": M.TARGETS,
        "metrics": metric_section,
        "gate_attainability": {
            "GATE-4": "不可达：Recall@5>=90% 依赖 RAG V2；C1 已由 t20 修复（retrieve 已可用），"
                      "但语料仅 143 条、12 部书目仅 4 部有数据，且检索排序质量未评估。",
            "GATE-5": "不可达：需 PHASE 5 Trust Layer；数据集已就绪但被评系统不存在。",
            "GATE-6": "不可达：需学派过滤（G-D 未修复）与各派语料扩充。",
            "GATE-8": "不可达：需 Trust State + Claim-Evidence + >=200 gold。",
        },
        "honesty": {
            "human_gold_count": prov_totals.get("human", 0),
            "statement": (
                "本数据集全部为规则/表格辅助构造（provenance=derived），"
                "**没有人工标注**。当前无法人工产出 1000 条。"
                "未将任何机器生成样本标为 human。"
            ),
            "targets_modified": False,
            "no_mock_as_real_rag": True,
        },
        "expansion_plan": dict(EXPANSION_PLAN, current_total=total),
    }
    return report


def _count_by_kind(corpus_index: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for entry in corpus_index.values():
        k = entry["kind"]
        out[k] = out.get(k, 0) + 1
    return out


def render_markdown(report: Dict[str, Any]) -> str:
    L: List[str] = []
    L.append("# WUDIAN-KB-V1 — Eval Report")
    L.append("")
    L.append(f"- generated_at: `{report['generated_at']}`")
    L.append(f"- phase: {report['phase']}")
    L.append("")
    L.append("## 1. 语料 id 空间")
    L.append("")
    L.append(f"- 可用 passage id: **{report['corpus']['passage_ids_available']}**")
    for k, v in report["corpus"]["by_kind"].items():
        L.append(f"  - `{k}`: {v}")
    L.append("")
    L.append("## 2. 七类数据集")
    L.append("")
    L.append("| 数据集 | 条数 | provenance | 人工标注 |")
    L.append("|---|---|---|---|")
    for d in report["datasets"]:
        L.append(f"| `{d['name']}` | {d['records']} | {d['provenance']} | {d['human_annotated']} |")
    L.append("")
    L.append(f"**合计 {report['totals']['records']} 条；"
             f"人工标注 {report['totals']['human_annotated']} 条。**")
    L.append("")
    L.append("## 3. 指标公式与实测值")
    L.append("")
    L.append("> 当前**不存在被评系统**（PHASE 4/5 未实现），故所有指标 `value = null`，"
             "状态 `not_computable`。**不以占位值冒充通过。**")
    L.append("")
    L.append("| 指标 | 公式（分子/分母/判定） | 目标 | 当前值 | 状态 |")
    L.append("|---|---|---|---|---|")

    def row(key: str, label: str, target: Any, node: Dict[str, Any]) -> None:
        L.append(f"| {label} | {node['formula']} | {target} | "
                 f"{node['value'] if node['value'] is not None else 'null'} | "
                 f"{node['status']} |")

    t = report["targets_frozen"]
    row("quote_exactness", "Quote Exactness", f">= {t['quote_exactness']}",
        report["metrics"]["quote_exactness"])
    row("source_attribution", "Source Attribution", f">= {t['source_attribution']}",
        report["metrics"]["source_attribution"])
    row("school_leakage", "School Leakage", f"< {t['school_leakage_max']}",
        report["metrics"]["school_leakage"])
    r = report["metrics"]["retrieval"]
    row("recall_at_1", "Retrieval Recall@1", "—", r["recall_at_1"])
    row("recall_at_3", "Retrieval Recall@3", "—", r["recall_at_3"])
    row("recall_at_5", "Retrieval Recall@5", f">= {t['recall_at_5']}", r["recall_at_5"])
    row("mrr", "MRR", "—", r["mrr"])
    row("unsupported_correct_refusal", "Unsupported Correct Refusal",
        f">= {t['unsupported_correct_refusal']}",
        report["metrics"]["unsupported_correct_refusal"])
    row("core_claim_evidence_coverage", "Core Claim Evidence Coverage",
        f">= {t['core_claim_evidence_coverage']}",
        report["metrics"]["core_claim_evidence_coverage"])
    row("fabricated_classical_quote", "Fabricated Classical Quote",
        f"= {t['fabricated_classical_quote']}",
        report["metrics"]["fabricated_classical_quote"])
    row("latency", "Latency P50/P95",
        f"P50<{t['p50_seconds']}s / P95<{t['p95_seconds']}s",
        report["metrics"]["latency"])
    L.append("")
    L.append("### 不可计算的原因")
    L.append("")
    for key in ["quote_exactness", "source_attribution", "school_leakage",
                "unsupported_correct_refusal", "core_claim_evidence_coverage",
                "fabricated_classical_quote", "latency"]:
        L.append(f"- **{key}**: {report['metrics'][key]['reason']}")
    L.append(f"- **recall_at_k / mrr**: {report['metrics']['retrieval']['recall_at_5']['reason']}")
    L.append("")
    L.append("## 4. Gate 可达性")
    L.append("")
    for g, reason in report["gate_attainability"].items():
        L.append(f"- **{g}**: {reason}")
    L.append("")
    L.append("## 5. Gold 数据诚实性")
    L.append("")
    L.append(f"- 人工标注条数: **{report['honesty']['human_gold_count']}**")
    L.append(f"- 说明: {report['honesty']['statement']}")
    L.append(f"- 是否修改目标数字: **{report['honesty']['targets_modified']}**")
    L.append("")
    L.append("## 6. 扩展到 1000 条")
    L.append("")
    ep = report["expansion_plan"]
    L.append(f"- 当前: {ep['current_total']} / 目标: {ep['target_total']}")
    L.append(f"- 方法: {ep['method']}")
    L.append("- 约束:")
    for c in ep["constraints"]:
        L.append(f"  - {c}")
    L.append("- 阻塞:")
    for b in ep["blocked_by"]:
        L.append(f"  - {b}")
    L.append("")
    return "\n".join(L)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the eval report.")
    parser.add_argument("--out", default=None,
                        help="output path for the JSON report (default eval/eval-report.json)")
    parser.add_argument("--md", default=None,
                        help="output path for the markdown report")
    args = parser.parse_args(argv)

    root = S.repo_root()
    eval_dir = root / "eval"
    out_json = Path(args.out) if args.out else eval_dir / "eval-report.json"
    if not out_json.is_absolute():
        out_json = (Path.cwd() / out_json).resolve()
    out_md = Path(args.md) if args.md else out_json.with_suffix(".md")
    if not out_md.is_absolute():
        out_md = (Path.cwd() / out_md).resolve()

    report = build_report(eval_dir)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")

    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print(f"records={report['totals']['records']} "
          f"human={report['totals']['human_annotated']} "
          f"metrics_computed=0 (no evaluated system yet)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
