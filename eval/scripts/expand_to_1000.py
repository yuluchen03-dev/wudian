"""Expansion planner: current eval scale -> 1000 high-quality gold records.

This script does NOT fabricate data.  It reports the honest gap and the concrete
matrix needed to close it, and it can emit *candidate* slots (provenance=derived)
for a human annotator to confirm.  It never writes provenance="human".

Usage:
    python eval/scripts/expand_to_1000.py                # report the gap
    python eval/scripts/expand_to_1000.py --plan         # emit the work matrix
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

import schema as S  # noqa: E402

TARGET_TOTAL = 1000

# Allocated quota per dataset.  Sums to 1000.
QUOTA: Dict[str, int] = {
    "retrieval_gold": 350,
    "quote_verification": 200,
    "source_attribution": 150,
    "modern_to_classic": 120,
    "school_consistency": 60,
    "adversarial_quotes": 80,
    "unsupported_questions": 40,
}

# Books that PHASE 2 must supply before retrieval_gold can grow honestly.
REQUIRED_BOOKS = {
    "论语": True, "道德经": True, "墨子": True, "韩非子": True,
    "孟子": False, "荀子": False, "大学": False, "中庸": False,
    "庄子": False, "商君书": False, "传习录": False, "孙子兵法": False,
}

CONCEPTS = ["仁", "义", "礼", "智", "信", "孝", "忠", "恕", "正名", "尚贤",
            "赏罚", "名实", "不争", "无为", "自然", "兼爱", "非攻", "法",
            "变", "天命", "知命", "修己", "学", "思"]

SCENARIOS = ["career", "workplace_conflict", "leadership", "achievement", "money",
             "competition", "family", "parent_child", "marriage", "friendship",
             "anxiety", "failure", "anger", "loneliness", "self_doubt", "choice",
             "responsibility", "justice", "fairness", "meaning", "ambition"]


def current_counts(eval_dir: Path) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for name in S.DATASET_NAMES:
        path = eval_dir / S.DATASETS[name]["file"]
        out[name] = len(S.load_jsonl(path)) if path.exists() else 0
    return out


def build_plan(eval_dir: Path) -> Dict[str, Any]:
    counts = current_counts(eval_dir)
    total = sum(counts.values())
    rows = []
    for name in S.DATASET_NAMES:
        have = counts[name]
        want = QUOTA[name]
        rows.append({"dataset": name, "current": have, "quota": want,
                     "needed": max(0, want - have)})

    missing_books = [b for b, present in REQUIRED_BOOKS.items() if not present]
    return {
        "target_total": TARGET_TOTAL,
        "current_total": total,
        "gap": max(0, TARGET_TOTAL - total),
        "quota_sum": sum(QUOTA.values()),
        "by_dataset": rows,
        "matrix": {
            "dimensions": ["book", "concept", "scenario"],
            "books_available": [b for b, p in REQUIRED_BOOKS.items() if p],
            "books_missing": missing_books,
            "concepts": CONCEPTS,
            "scenarios": SCENARIOS,
            "max_grid_cells": len(REQUIRED_BOOKS) * len(CONCEPTS) * len(SCENARIOS),
        },
        "blockers": [
            f"PHASE 2 必须补齐 {len(missing_books)} 部书目：{missing_books}",
            "PHASE 1 必须正式化 passage_id（当前使用 lunyu:/debate:/commentary: 引用格式）",
            "需要真实人工标注资源才能产出 provenance=human 的记录（当前为 0）",
        ],
        "rules": [
            "每个新增记录的 expected_passage_ids 必须通过 validate_gold.py",
            "机器生成的候选必须先标 derived，经人工确认后才可升级为 human",
            "禁止用 LLM 批量生成看似合理的 Gold 并标 human",
            "禁止为凑数编造 passage 或出处",
        ],
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan eval expansion to 1000 records.")
    parser.add_argument("--plan", action="store_true", help="print the work matrix")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    eval_dir = S.repo_root() / "eval"
    plan = build_plan(eval_dir)

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    print(f"current total : {plan['current_total']}")
    print(f"target total  : {plan['target_total']}")
    print(f"gap           : {plan['gap']}")
    print("")
    print(f"{'dataset':<24}{'current':>8}{'quota':>8}{'needed':>8}")
    for row in plan["by_dataset"]:
        print(f"{row['dataset']:<24}{row['current']:>8}{row['quota']:>8}{row['needed']:>8}")
    print("")
    m = plan["matrix"]
    print(f"books available: {m['books_available']}")
    print(f"books missing  : {m['books_missing']}")
    print(f"grid cells     : {m['max_grid_cells']} "
          f"({len(REQUIRED_BOOKS)} books x {len(CONCEPTS)} concepts x {len(SCENARIOS)} scenarios)")
    print("")
    print("blockers:")
    for b in plan["blockers"]:
        print(f"  - {b}")
    print("rules:")
    for r in plan["rules"]:
        print(f"  - {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
