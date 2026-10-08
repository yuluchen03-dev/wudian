"""The single admission gate for WUDIAN-KB-V1 eval data.

Rules enforced (all hard failures, never warnings):
  1. every `expected_passage_ids` entry must exist in the REAL corpus;
  2. `provenance` must be one of human / derived / synthetic;
  3. no duplicate ids within a dataset;
  4. required fields present, types correct, enums legal;
  5. dataset-specific contracts (refusal wording, dual quote/source fields, ...).

Exit codes: 0 = all datasets valid, 1 = at least one violation.

Usage:
    python eval/scripts/validate_gold.py --dir eval
    python eval/scripts/validate_gold.py --dir eval --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

import schema as S  # noqa: E402


def validate_dataset(name: str, path: Path,
                     corpus_index: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Validate one dataset file.  Returns a report dict."""
    if not path.exists():
        return {"dataset": name, "path": str(path), "exists": False,
                "records": 0, "errors": [f"file not found: {path}"],
                "provenance_counts": {}}

    records = S.load_jsonl(path)
    errors: List[str] = []
    seen: set = set()
    prov_counts: Dict[str, int] = {}

    for rec in records:
        errors.extend(S.validate_record(name, rec, corpus_index, seen))
        prov = rec.get("provenance", "<missing>")
        prov_counts[prov] = prov_counts.get(prov, 0) + 1

    return {"dataset": name, "path": str(path), "exists": True,
            "records": len(records), "errors": errors,
            "provenance_counts": prov_counts}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate eval gold datasets.")
    parser.add_argument("--dir", default=None,
                        help="eval directory (default: repository eval/)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--only", default=None,
                        help="validate a single dataset name")
    args = parser.parse_args(argv)

    root = S.repo_root()
    eval_dir = Path(args.dir).resolve() if args.dir else root / "eval"

    corpus_index = S.load_corpus_index(root)
    names = [args.only] if args.only else S.DATASET_NAMES

    reports = []
    for name in names:
        spec = S.DATASETS[name]
        reports.append(validate_dataset(name, eval_dir / spec["file"], corpus_index))

    total_records = sum(r["records"] for r in reports)
    all_errors = [(r["dataset"], e) for r in reports for e in r["errors"]]
    prov_total: Dict[str, int] = {}
    for r in reports:
        for k, v in r["provenance_counts"].items():
            prov_total[k] = prov_total.get(k, 0) + v

    summary = {
        "corpus_passage_ids": len(corpus_index),
        "datasets": reports,
        "total_records": total_records,
        "total_errors": len(all_errors),
        "provenance_totals": prov_total,
        "valid": not all_errors,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"corpus passage ids available : {len(corpus_index)}")
        print(f"eval dir                     : {eval_dir}")
        print("")
        for r in reports:
            mark = "OK  " if not r["errors"] and r["exists"] else "FAIL"
            print(f"[{mark}] {r['dataset']:<24} records={r['records']:<4} "
                  f"errors={len(r['errors'])} provenance={r['provenance_counts']}")
        print("")
        print(f"TOTAL records={total_records} errors={len(all_errors)} "
              f"provenance={prov_total}")
        if all_errors:
            print("")
            print("VIOLATIONS:")
            for ds, err in all_errors:
                print(f"  - ({ds}) {err}")
        else:
            print("ALL DATASETS VALID")

    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
