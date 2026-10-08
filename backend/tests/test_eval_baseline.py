"""Baseline tests for the WUDIAN-KB-V1 eval infrastructure (PHASE 0 / PHASE 8).

These tests assert REAL properties of the eval assets:
  * all seven datasets load and pass the admission gate;
  * the gate genuinely REJECTS a fabricated passage id (negative test);
  * the metric functions produce the expected values on hand-computed inputs;
  * provenance discipline holds (nothing is marked `human` without an annotator);
  * every `expected_passage_ids` entry resolves against the real corpus.

They deliberately do NOT call the RAG service, so they neither need chromadb nor
touch `backend/chroma_db`.  No tautological `assert True` placeholders.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
EVAL_DIR = REPO_ROOT / "eval"
SCRIPTS = EVAL_DIR / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import metrics as M  # noqa: E402
import schema as S  # noqa: E402


def _load_validate_gold():
    """Import validate_gold.py by path (it is a script, not a package module)."""
    spec = importlib.util.spec_from_file_location(
        "validate_gold", SCRIPTS / "validate_gold.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def corpus_index():
    return S.load_corpus_index(REPO_ROOT)


# ---------------------------------------------------------------- assets exist


def test_eval_directory_and_all_seven_datasets_exist():
    assert EVAL_DIR.is_dir(), f"missing eval dir: {EVAL_DIR}"
    missing = [S.DATASETS[n]["file"] for n in S.DATASET_NAMES
               if not (EVAL_DIR / S.DATASETS[n]["file"]).exists()]
    assert missing == [], f"missing dataset files: {missing}"
    assert len(S.DATASET_NAMES) == 7


def test_every_dataset_loads_and_is_non_empty():
    for name in S.DATASET_NAMES:
        recs = S.load_jsonl(EVAL_DIR / S.DATASETS[name]["file"])
        assert len(recs) > 0, f"{name} is empty"


# ---------------------------------------------------------------- gate


def test_admission_gate_passes_on_committed_datasets():
    """The shipped datasets must be valid (exit code 0)."""
    vg = _load_validate_gold()
    rc = vg.main(["--dir", str(EVAL_DIR)])
    assert rc == 0, "validate_gold.py reported violations on the committed datasets"


def test_gate_rejects_fabricated_passage_id(tmp_path, corpus_index):
    """NEGATIVE TEST: a made-up passage id must be rejected, not silently kept."""
    fabricated = "lunyu:99.99"
    assert fabricated not in corpus_index, "test precondition: id must be absent"

    record = {
        "id": "rg-negative-1", "dataset": "retrieval_gold", "provenance": "derived",
        "query": "negative test", "query_type": "modern_scenario",
        "expected_passage_ids": [fabricated],
        "expected_books": ["论语"], "difficulty": "easy",
    }
    errors = S.validate_record("retrieval_gold", record, corpus_index)
    assert any("does NOT exist in corpus" in e for e in errors), errors


def test_gate_rejects_duplicate_ids(corpus_index):
    seen: set = set()
    rec = {
        "id": "rg-dup", "dataset": "retrieval_gold", "provenance": "derived",
        "query": "dup", "query_type": "modern_scenario",
        "expected_passage_ids": ["lunyu:1.1"], "expected_books": ["论语"],
        "difficulty": "easy",
    }
    first = S.validate_record("retrieval_gold", rec, corpus_index, seen)
    second = S.validate_record("retrieval_gold", rec, corpus_index, seen)
    assert first == []
    assert any("duplicate id" in e for e in second), second


def test_gate_rejects_illegal_provenance(corpus_index):
    rec = {
        "id": "rg-prov", "dataset": "retrieval_gold", "provenance": "official",
        "query": "q", "query_type": "modern_scenario",
        "expected_passage_ids": ["lunyu:1.1"], "expected_books": ["论语"],
        "difficulty": "easy",
    }
    errors = S.validate_record("retrieval_gold", rec, corpus_index)
    assert any("illegal provenance" in e for e in errors), errors


def test_all_expected_passage_ids_resolve(corpus_index):
    """Cross-check every dataset entry against the real corpus."""
    for name in S.DATASET_NAMES:
        for rec in S.load_jsonl(EVAL_DIR / S.DATASETS[name]["file"]):
            for ref in rec.get("expected_passage_ids", []) or []:
                assert ref in corpus_index, f"{name}:{rec.get('id')} bad ref {ref}"


# ---------------------------------------------------------------- provenance


def test_no_record_is_falsely_marked_human():
    """No human annotation exists; nothing may claim provenance=human."""
    total_human = 0
    for name in S.DATASET_NAMES:
        for rec in S.load_jsonl(EVAL_DIR / S.DATASETS[name]["file"]):
            assert rec["provenance"] in S.PROVENANCE_VALUES
            if rec["provenance"] == "human":
                total_human += 1
    assert total_human == 0, (
        "no human annotator is available in this project; "
        f"found {total_human} records falsely marked human"
    )


# ---------------------------------------------------------------- adversarial coverage


def test_adversarial_dataset_covers_required_categories():
    recs = S.load_jsonl(EVAL_DIR / S.DATASETS["adversarial_quotes"]["file"])
    kinds = {r["attack_type"] for r in recs}
    required = {
        "real_quote_wrong_source_cross_school",   # ch.16 #1/#2, 以德报怨
        "real_quote_wrong_source_same_book",      # 同书错篇
        "fake_classic",                           # 假古文
        "punctuation_variant",                    # 同句不同标点
        "traditional_variant",                    # 繁体
        "partial_quote",                          # 部分引用
        "internet_chicken_soup",                  # 网络鸡汤冒充孔子
        "two_char_fragment",                      # 2 字片段
        "modern_question_no_classic",             # ch.16 #3/#4/#5
        "quote_absent_wrong_attribution",         # 语料中不存在
    }
    missing = required - kinds
    assert missing == set(), f"missing adversarial categories: {sorted(missing)}"


def test_brief_ch16_first_case_is_present_and_marked_failing_today():
    """brief ch.16 example #1 must exist as an explicit case (known to FAIL now)."""
    recs = S.load_jsonl(EVAL_DIR / S.DATASETS["adversarial_quotes"]["file"])
    hits = [r for r in recs
            if "己所不欲" in r["input"]["quote"] and "孟子" in r["input"]["claimed_source"]]
    assert hits, "brief ch.16 case 1 (己所不欲勿施于人 attributed to 孟子) is missing"
    case = hits[0]
    assert case["expected"]["quote_exists"] is True, "the quote DOES exist (it is genuine)"
    assert case["expected"]["verifiable"] is False, "wrong attribution must not be verifiable"
    assert case["expected"]["trust_state"] == "citation_corrected"
    assert case["expected"]["must_not_display_as_classic"] is True


def test_two_char_fragment_negative_exists():
    recs = S.load_jsonl(EVAL_DIR / S.DATASETS["adversarial_quotes"]["file"])
    frag = [r for r in recs if r["attack_type"] == "two_char_fragment"]
    assert frag, "2-char fragment negative case missing"


# ---------------------------------------------------------------- refusal dataset


def test_unsupported_questions_require_the_mandated_phrase():
    recs = S.load_jsonl(EVAL_DIR / S.DATASETS["unsupported_questions"]["file"])
    assert recs
    for rec in recs:
        assert rec["expected"]["must_refuse"] is True
        assert rec["expected"]["required_phrase"] == S.REQUIRED_REFUSAL_PHRASE
        assert rec["expected"]["trust_state"] == "insufficient_evidence"


# ---------------------------------------------------------------- metrics


def test_normalize_does_not_conflate_different_sentences():
    a = M.normalize("己所不欲，勿施于人。")
    b = M.normalize("己所不欲勿施于人")
    c = M.normalize("上善若水。")
    assert a == b, "punctuation-only difference must normalize equal"
    assert a != c, "different sentences must NOT normalize equal"


def test_traditional_folding_matches_simplified():
    assert M.normalize_all("己所不欲，勿施於人。") == M.normalize_all("己所不欲，勿施于人。")


def test_recall_at_k_on_known_input():
    records = [
        {"id": "a", "expected_passage_ids": ["lunyu:1.1"]},
        {"id": "b", "expected_passage_ids": ["lunyu:2.1"]},
        {"id": "c", "expected_passage_ids": ["lunyu:3.1"]},
    ]
    retrieved = [
        ["lunyu:1.1", "x"],   # hit at rank 1
        ["y", "z", "lunyu:2.1"],  # hit at rank 3
        ["y", "z", "w", "v", "u"],  # miss
    ]
    r1 = M.recall_at_k(records, retrieved, 1)
    r3 = M.recall_at_k(records, retrieved, 3)
    r5 = M.recall_at_k(records, retrieved, 5)
    assert r1["value"] == pytest.approx(1 / 3)
    assert r3["value"] == pytest.approx(2 / 3)
    assert r5["value"] == pytest.approx(2 / 3)
    mrr = M.reciprocal_rank(records, retrieved)
    assert mrr["value"] == pytest.approx((1.0 + 1 / 3 + 0.0) / 3)


def test_quote_exactness_on_known_input():
    records = [
        {"id": "1", "expected": {"quote_exists": True}},
        {"id": "2", "expected": {"quote_exists": True}},
    ]
    preds = [
        {"quote_exists": True, "exact_match": True},
        {"quote_exists": True, "exact_match": False},
    ]
    out = M.compute_quote_exactness(records, preds)
    assert out["numerator"] == 1 and out["denominator"] == 2
    assert out["value"] == pytest.approx(0.5)
    assert out["passed"] is False, "50% must not pass the 99% target"


def test_source_attribution_is_independent_of_quote_existence():
    """A quote can exist while its attribution is wrong (PROJECT-BRIEF ch.11)."""
    records = [
        {"id": "1", "expected": {"quote_exists": True, "source_correct": False}},
    ]
    preds = [{"quote_exists": True, "source_correct": False}]
    out = M.compute_source_attribution(records, preds)
    assert out["value"] == pytest.approx(1.0)


def test_fabricated_classical_quote_counts_any_pass():
    records = [
        {"id": "1", "expected": {"quote_exists": False}, "attack_type": "fake_classic",
         "input": {"quote": "伪古文"}},
        {"id": "2", "expected": {"quote_exists": True}},
    ]
    preds = [{"verifiable": True}, {"verifiable": True}]
    out = M.compute_fabricated_classical_quote(records, preds)
    assert out["value"] == 1
    assert out["passed"] is False, "any fabricated pass must fail"


def test_school_leakage_on_known_input():
    records = [
        {"id": "1", "sage_key": "confucius", "allowed_books": ["论语"]},
    ]
    retrieved = [["lunyu:1.1", "debate:laozi:daodejing-08-01"]]
    books = {"lunyu:1.1": "论语", "debate:laozi:daodejing-08-01": "道德经"}
    out = M.compute_school_leakage(records, retrieved, lambda r: books.get(r, ""))
    assert out["numerator"] == 1 and out["denominator"] == 2
    assert out["value"] == pytest.approx(0.5)
    assert out["passed"] is False, "50% leakage must fail the <1% target"


def test_unsupported_correct_refusal_requires_all_three_conditions():
    records = [{"id": "1", "expected": {"must_refuse": True}}]
    good = [{"trust_state": "insufficient_evidence",
             "answer_text": f"抱歉，{S.REQUIRED_REFUSAL_PHRASE}",
             "presented_quote_as_classic": False}]
    bad_state = [{"trust_state": "verified",
                  "answer_text": S.REQUIRED_REFUSAL_PHRASE,
                  "presented_quote_as_classic": False}]
    bad_quote = [{"trust_state": "insufficient_evidence",
                  "answer_text": S.REQUIRED_REFUSAL_PHRASE,
                  "presented_quote_as_classic": True}]
    assert M.compute_unsupported_correct_refusal(records, good)["value"] == 1.0
    assert M.compute_unsupported_correct_refusal(records, bad_state)["value"] == 0.0
    assert M.compute_unsupported_correct_refusal(records, bad_quote)["value"] == 0.0


def test_core_claim_evidence_coverage_counts_only_supported():
    records = [{"id": "1"}]
    preds = [{"claims": [
        {"is_core": True, "text": "c1",
         "evidence": [{"verification": "supported"}]},
        {"is_core": True, "text": "c2",
         "evidence": [{"verification": "unsupported"}]},
        {"is_core": False, "text": "c3", "evidence": []},
    ]}]
    out = M.compute_core_claim_evidence_coverage(records, preds)
    assert out["numerator"] == 1 and out["denominator"] == 2
    assert out["value"] == pytest.approx(0.5)


def test_percentile_nearest_rank():
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert M.percentile(vals, 50) == 3.0
    assert M.percentile([], 50) is None


# ---------------------------------------------------------------- report


def test_report_is_generated_with_null_metrics_and_no_fabrication(tmp_path):
    import report as R  # noqa: E402

    rep = R.build_report(EVAL_DIR)
    assert rep["totals"]["records"] > 0
    assert rep["honesty"]["human_gold_count"] == 0
    assert rep["honesty"]["targets_modified"] is False

    # every metric must be explicitly not-computable, never a fake pass
    for key in ["quote_exactness", "source_attribution", "school_leakage",
                "unsupported_correct_refusal", "core_claim_evidence_coverage",
                "fabricated_classical_quote", "latency"]:
        node = rep["metrics"][key]
        assert node["value"] is None, f"{key} must not carry a fabricated value"
        assert node["status"] == "not_computable"
        assert node["reason"], f"{key} needs a stated reason"

    # frozen targets must equal PROJECT-BRIEF ch.17
    assert M.TARGETS["quote_exactness"] == 0.99
    assert M.TARGETS["source_attribution"] == 0.98
    assert M.TARGETS["school_leakage_max"] == 0.01
    assert M.TARGETS["recall_at_5"] == 0.90
    assert M.TARGETS["unsupported_correct_refusal"] == 0.95
    assert M.TARGETS["core_claim_evidence_coverage"] == 0.95
    assert M.TARGETS["fabricated_classical_quote"] == 0


def test_validate_gold_cli_returns_zero_on_shipped_data():
    vg = _load_validate_gold()
    assert vg.main(["--dir", str(EVAL_DIR), "--json"]) == 0
