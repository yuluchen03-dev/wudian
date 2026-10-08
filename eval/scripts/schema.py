"""Eval schema definitions and authoritative passage-id space (WUDIAN-KB-V1).

Single source of truth for:
  * the field schema of the seven eval datasets (PROJECT-BRIEF ch.15), and
  * the **real** passage-id space, derived from the actual corpus files.

Design rule (non-negotiable): a passage id is only valid if it resolves against
the real corpus on disk.  Ids are never invented, and no dataset may reference a
passage that does not exist.  `validate_gold.py` enforces this.

Passage-id reference format (current corpus, pre-PHASE-1):
    lunyu:<verse_id>                     e.g. lunyu:1.1
    debate:<sage_key>:<verse_id>         e.g. debate:laozi:daodejing-08-01
    commentary:<verse_id>                e.g. commentary:1.1

PHASE 1 will introduce a formal `passage_id`; this module is the single place to
re-point once that schema exists.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

# ---------------------------------------------------------------- enums

PROVENANCE_VALUES = {"human", "derived", "synthetic"}
TRUST_STATES = {"verified", "citation_corrected", "quote_relaxed", "insufficient_evidence"}
DIFFICULTY_VALUES = {"easy", "medium", "hard"}
VARIANT_TYPES = {"wrong_book", "wrong_chapter", "correct"}
QUERY_TYPES = {"modern_scenario", "classical_concept", "exact_quote", "adversarial"}

# PROJECT-BRIEF ch.12 mandated refusal wording (exact substring).
REQUIRED_REFUSAL_PHRASE = "当前知识库没有检索到足够可靠的原典支持这一判断"

# ---------------------------------------------------------------- dataset specs
# `fields` maps field name -> expected python type name ("str", "int", "list",
# "dict", "bool").  `required` lists the mandatory field names.

DATASETS: Dict[str, Dict[str, Any]] = {
    "retrieval_gold": {
        "file": "retrieval_gold.jsonl",
        "description": "现代问题 -> 期望命中的真实原典 passage id（GATE-4 Recall@K / MRR）",
        "fields": {
            "id": "str", "dataset": "str", "provenance": "str",
            "query": "str", "query_type": "str",
            "expected_passage_ids": "list", "expected_books": "list",
            "difficulty": "str",
            "scenario": "str", "notes": "str", "generation_method": "str",
        },
        "required": ["id", "dataset", "provenance", "query", "query_type",
                     "expected_passage_ids", "expected_books", "difficulty"],
        "id_fields": ["expected_passage_ids"],
    },
    "quote_verification": {
        "file": "quote_verification.jsonl",
        "description": "引文存在性与逐字精确度；必须区分 quote_exists 与 source_correct（GATE-5）",
        "fields": {
            "id": "str", "dataset": "str", "provenance": "str",
            "quote": "str", "claimed_source": "str", "expected": "dict",
            "generation_method": "str",
        },
        "required": ["id", "dataset", "provenance", "quote", "claimed_source", "expected"],
        "expected_keys": ["quote_exists", "exact_match", "source_correct",
                          "correct_source", "trust_state"],
    },
    "source_attribution": {
        "file": "source_attribution.jsonl",
        "description": "出处正确性（独立于引文是否存在）（GATE-5）",
        "fields": {
            "id": "str", "dataset": "str", "provenance": "str",
            "quote": "str", "claimed_source": "str", "expected_source": "str",
            "expected_source_correct": "bool", "variant_type": "str",
            "generation_method": "str",
        },
        "required": ["id", "dataset", "provenance", "quote", "claimed_source",
                     "expected_source", "expected_source_correct", "variant_type"],
    },
    "modern_to_classic": {
        "file": "modern_to_classic.jsonl",
        "description": "现代问题结构化（scene/actors/conflict/emotion/choices/concepts）（GATE-3）",
        "fields": {
            "id": "str", "dataset": "str", "provenance": "str",
            "modern_query": "str", "expected": "dict", "required_concepts": "list",
            "generation_method": "str",
        },
        "required": ["id", "dataset", "provenance", "modern_query", "expected",
                     "required_concepts"],
        "expected_keys": ["scene", "actors", "conflict", "emotion", "choices", "concepts"],
    },
    "school_consistency": {
        "file": "school_consistency.jsonl",
        "description": "多学派隔离；School Leakage = 越界引用 / 总引用（GATE-6）",
        "fields": {
            "id": "str", "dataset": "str", "provenance": "str",
            "sage_key": "str", "allowed_books": "list", "forbidden_books": "list",
            "query": "str", "generation_method": "str",
        },
        "required": ["id", "dataset", "provenance", "sage_key", "allowed_books",
                     "forbidden_books", "query"],
    },
    "adversarial_quotes": {
        "file": "adversarial_quotes.jsonl",
        "description": "对抗输入（PROJECT-BRIEF ch.16 全部 12 类）（GATE-5，硬前置）",
        "fields": {
            "id": "str", "dataset": "str", "provenance": "str", "attack_type": "str",
            "input": "dict", "expected": "dict", "sage_key": "str",
            "note": "str", "generation_method": "str",
        },
        "required": ["id", "dataset", "provenance", "attack_type", "input", "expected"],
        "input_keys": ["quote", "claimed_source"],
        "expected_keys": ["quote_exists", "verifiable", "trust_state",
                          "must_not_display_as_classic"],
    },
    "unsupported_questions": {
        "file": "unsupported_questions.jsonl",
        "description": "语料无支撑的问题，期望诚实拒答（GATE-8）",
        "fields": {
            "id": "str", "dataset": "str", "provenance": "str", "question": "str",
            "out_of_scope_reason": "str", "expected": "dict", "generation_method": "str",
        },
        "required": ["id", "dataset", "provenance", "question",
                     "out_of_scope_reason", "expected"],
        "expected_keys": ["must_refuse", "trust_state", "required_phrase"],
    },
}

DATASET_NAMES: List[str] = list(DATASETS.keys())

# ---------------------------------------------------------------- corpus index


def repo_root() -> Path:
    """Repository root, resolved from this file's location (eval/scripts/)."""
    return Path(__file__).resolve().parents[2]


def _corpus_paths(root: Path) -> Dict[str, Path]:
    return {
        "lunyu": root / "data" / "processed" / "lunyu.json",
        "debate": root / "data" / "processed" / "debate_classics.json",
        "commentary": root / "backend" / "data" / "commentaries" / "lunyu_zhuxi.json",
    }


def load_corpus_index(root: Path | None = None) -> Dict[str, Dict[str, Any]]:
    """Build the authoritative passage-id space from the REAL corpus files.

    Returns {ref: {"kind", "book", "chapter", "text"}}.  Missing files are an
    error: silently shrinking the id space would let fabricated ids pass.
    """
    root = root or repo_root()
    paths = _corpus_paths(root)
    for name, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"corpus file missing for '{name}': {path}")

    index: Dict[str, Dict[str, Any]] = {}

    lunyu = json.loads(paths["lunyu"].read_text(encoding="utf-8"))
    book = lunyu.get("book", "论语")
    for chapter in lunyu.get("chapters", []):
        title = chapter.get("chapter_title", "")
        for verse in chapter.get("verses", []):
            vid = verse.get("verse_id")
            if not vid:
                continue
            index[f"lunyu:{vid}"] = {
                "kind": "l1_original", "book": book, "chapter": title,
                "text": verse.get("original", ""),
            }

    debate = json.loads(paths["debate"].read_text(encoding="utf-8"))
    for sage_key, block in (debate.get("classics") or {}).items():
        bname = block.get("book", "")
        for verse in block.get("verses", []):
            vid = verse.get("id")
            if not vid:
                continue
            index[f"debate:{sage_key}:{vid}"] = {
                "kind": "l1_original", "book": bname,
                "chapter": verse.get("chapter", verse.get("source", "")),
                "text": verse.get("original", ""), "sage_key": sage_key,
            }

    commentaries = json.loads(paths["commentary"].read_text(encoding="utf-8"))
    for item in commentaries.get("commentaries", []):
        vid = item.get("verse_id")
        if not vid:
            continue
        index[f"commentary:{vid}"] = {
            "kind": "l2_commentary",
            "book": commentaries.get("source", "朱熹《论语集注》"),
            "chapter": item.get("chapter", ""),
            "text": item.get("commentary", ""),
        }

    return index


def book_of(ref: str, index: Dict[str, Dict[str, Any]]) -> str:
    """Book label for a passage ref ('' when unknown)."""
    entry = index.get(ref)
    return entry["book"] if entry else ""


# ---------------------------------------------------------------- validation


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "str":
        return isinstance(value, str)
    if expected == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "bool":
        return isinstance(value, bool)
    if expected == "list":
        return isinstance(value, list)
    if expected == "dict":
        return isinstance(value, dict)
    return True


def validate_record(
    dataset: str,
    record: Dict[str, Any],
    corpus_index: Dict[str, Dict[str, Any]],
    seen_ids: Set[str] | None = None,
) -> List[str]:
    """Validate one record.  Returns a list of human-readable errors ([] == ok)."""
    errors: List[str] = []
    spec = DATASETS.get(dataset)
    if spec is None:
        return [f"unknown dataset '{dataset}'"]
    if not isinstance(record, dict):
        return [f"[{dataset}] record is not an object"]

    rid = record.get("id", "<no-id>")

    for field in spec["required"]:
        if field not in record:
            errors.append(f"[{dataset}:{rid}] missing required field '{field}'")
        elif record[field] in ("", None) and spec["fields"].get(field) != "bool":
            errors.append(f"[{dataset}:{rid}] field '{field}' is empty")

    for field, expected in spec["fields"].items():
        if field in record and record[field] is not None:
            if not _type_ok(record[field], expected):
                errors.append(
                    f"[{dataset}:{rid}] field '{field}' should be {expected}, "
                    f"got {type(record[field]).__name__}"
                )

    # dataset tag must match the file it lives in
    if record.get("dataset") not in (None, dataset):
        errors.append(f"[{dataset}:{rid}] dataset tag '{record['dataset']}' != '{dataset}'")

    # provenance discipline
    prov = record.get("provenance")
    if prov is not None and prov not in PROVENANCE_VALUES:
        errors.append(f"[{dataset}:{rid}] illegal provenance '{prov}'")

    # duplicate id
    if seen_ids is not None:
        if rid in seen_ids:
            errors.append(f"[{dataset}:{rid}] duplicate id '{rid}'")
        else:
            seen_ids.add(rid)

    # dataset-specific rules
    if dataset == "retrieval_gold":
        ids = record.get("expected_passage_ids") or []
        if not ids:
            errors.append(f"[{dataset}:{rid}] expected_passage_ids is empty")
        for ref in ids:
            if ref not in corpus_index:
                errors.append(
                    f"[{dataset}:{rid}] expected_passage_id '{ref}' does NOT exist in corpus"
                )
        if record.get("query_type") and record["query_type"] not in QUERY_TYPES:
            errors.append(f"[{dataset}:{rid}] illegal query_type '{record['query_type']}'")
        if record.get("difficulty") and record["difficulty"] not in DIFFICULTY_VALUES:
            errors.append(f"[{dataset}:{rid}] illegal difficulty '{record['difficulty']}'")

    if dataset in ("quote_verification", "modern_to_classic",
                   "adversarial_quotes", "unsupported_questions"):
        exp = record.get("expected")
        if isinstance(exp, dict):
            for key in spec.get("expected_keys", []):
                if key not in exp:
                    errors.append(f"[{dataset}:{rid}] expected.{key} missing")
        elif exp is not None:
            errors.append(f"[{dataset}:{rid}] 'expected' must be an object")

    if dataset == "quote_verification":
        exp = record.get("expected") or {}
        if "trust_state" in exp and exp["trust_state"] not in TRUST_STATES:
            errors.append(f"[{dataset}:{rid}] illegal trust_state '{exp['trust_state']}'")

    if dataset == "adversarial_quotes":
        inp = record.get("input")
        if isinstance(inp, dict):
            for key in spec.get("input_keys", []):
                if key not in inp:
                    errors.append(f"[{dataset}:{rid}] input.{key} missing")
        elif inp is not None:
            errors.append(f"[{dataset}:{rid}] 'input' must be an object")
        exp = record.get("expected") or {}
        if "trust_state" in exp and exp["trust_state"] not in TRUST_STATES:
            errors.append(f"[{dataset}:{rid}] illegal trust_state '{exp['trust_state']}'")

    if dataset == "unsupported_questions":
        exp = record.get("expected") or {}
        if exp.get("must_refuse") is not True:
            errors.append(f"[{dataset}:{rid}] expected.must_refuse must be true")
        if exp.get("required_phrase") != REQUIRED_REFUSAL_PHRASE:
            errors.append(f"[{dataset}:{rid}] expected.required_phrase must equal the "
                          f"PROJECT-BRIEF ch.12 refusal wording")

    if dataset == "source_attribution":
        vt = record.get("variant_type")
        if vt and vt not in VARIANT_TYPES:
            errors.append(f"[{dataset}:{rid}] illegal variant_type '{vt}'")

    return errors


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file, raising on malformed lines (no silent skipping)."""
    records: List[Dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{lineno} invalid JSON: {exc}") from exc
    return records
