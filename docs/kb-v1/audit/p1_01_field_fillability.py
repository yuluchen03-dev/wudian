# -*- coding: utf-8 -*-
"""PHASE 1 / P1-01 helper: 29-field fillability against the REAL current corpus.
Read-only. Prints which of the 29 PROJECT-BRIEF fields the existing data can
honestly populate, and which must stay explicitly empty (None)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data" / "processed"

lunyu = json.load(open(P / "lunyu.json", encoding="utf-8"))
verse = lunyu["chapters"][0]["verses"][0]
debate = json.load(open(P / "debate_classics.json", encoding="utf-8"))
dverse = debate["classics"]["laozi"]["verses"][0]

print("=== raw corpus field inventory ===")
print("lunyu.json verse keys:", sorted(verse.keys()))
print("lunyu.json container keys:", sorted(lunyu.keys()))
print("debate_classics laozi verse keys:", sorted(dverse.keys()))
print("debate_classics laozi container keys:", sorted(debate["classics"]["laozi"].keys()))

# Fields the existing corpus CAN honestly populate
FILLABLE = {
    "passage_id": "derive from verse_id / debate id (needs global scheme)",
    "book_id": "derive from book name -> slug (classics_catalog.json has ids)",
    "book_title": "lunyu.json 'book' / debate_classics[sage]['book']",
    "chapter_id": "lunyu.json chapter_id (int); debate only has chapter NAME",
    "chapter_title": "lunyu.json chapter_title / debate verse 'chapter'",
    "original": "present in both",
    "text_type": "constant 'original' for L1",
    "source_provider": "ONLY as explicit sentinel 'unknown' (no real provider exists)",
    "source_url": "ONLY as explicit sentinel 'unknown'",
    "source_edition": "ONLY as explicit sentinel 'unknown'",
    "license": "ONLY as explicit sentinel 'unknown'",
    "source_id": "src_unknown",
    "verification_level": "C or D only (zero human review -> cannot be A/B)",
    "proofread_status": "'unproofread' or 'machine_processed'",
    "author": "lunyu.json container only; debate has none",
    "dynasty": "lunyu.json container only; debate has none",
    "created_at": "generation timestamp",
    "updated_at": "generation timestamp",
}

# Fields that MUST stay None (no honest source of truth today)
MUST_BE_EMPTY = {
    "section": "corpus granularity stops at chapter",
    "line_no": "corpus granularity stops at chapter",
    "original_traditional": "corpus has simplified only (audit §4.2: zero traditional text)",
    "original_simplified": "only one simplified copy exists; no separate field",
    "commentator": "not applicable to L1; belongs to Commentary (L2)",
    "commentary_dynasty": "not applicable to L1; belongs to Commentary (L2)",
    "school": "debate_classics has NO school field; lunyu.json has none either",
    "concepts": "only free-text 'keywords'; no controlled vocabulary yet (PHASE 3)",
    "modern_topics": "no such annotation exists",
    "modern_scenarios": "only prose 'scene'/'modern_usage'; not structured",
    "stance": "PROJECT-BRIEF gives no controlled vocabulary; zero corpus support",
    "embedding_version": "index version written in PHASE 4",
    "verified_by": "zero human review records",
    "verified_at": "zero human review records",
}

print("\n=== 29-field fillability ===")
print("FILLABLE (%d):" % len(FILLABLE))
for k, v in FILLABLE.items():
    print("   %-22s %s" % (k, v))
print("\nMUST STAY None (%d):" % len(MUST_BE_EMPTY))
for k, v in MUST_BE_EMPTY.items():
    print("   %-22s %s" % (k, v))
print("\ntotal: %d fillable + %d empty = %d" % (
    len(FILLABLE), len(MUST_BE_EMPTY), len(FILLABLE) + len(MUST_BE_EMPTY)))
