# -*- coding: utf-8 -*-
"""PHASE 0 read-only audit helper: semantics of the existing 'source' fields.
Distinguishes citation-label vs provenance-provider. Writes nothing."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data" / "processed"

def load(p):
    return json.load(open(p, encoding="utf-8"))

print("=== semantics of existing 'source' fields ===")
q = load(P / "lunyu_quotes.json")
print("lunyu_quotes.json source samples:", [x["source"] for x in q["quotes"][:5]])
print("  -> citation label (chapter), NOT a data provider\n")

db = load(P / "debate_classics.json")
print("debate_classics.json source samples:")
for k, v in list(db["classics"].items())[:3]:
    print("  ", k, [x["source"] for x in v["verses"][:2]])
print("  -> citation label (book·chapter), NOT a data provider\n")

cm = load(ROOT / "backend" / "data" / "commentaries" / "lunyu_zhuxi.json")
print("lunyu_zhuxi.json top-level source:", cm["source"])
print("  per-item source:", {x["source"] for x in cm["commentaries"]})
print("  -> commentator attribution (朱熹《论语集注》), NOT a text provider/edition\n")

cat = load(P / "classics_catalog.json")
print("classics_catalog.json sources (catalog-level only):")
for s in cat["sources"]:
    print("   ", s["name"], s["url"])
print("  books with per-book source_url:", sum(1 for b in cat["books"] if "source_url" in b))
print("  books with per-book source_edition:", sum(1 for b in cat["books"] if "source_edition" in b))
print("  books with per-book license:", sum(1 for b in cat["books"] if "license" in b))
print("  total books in catalog:", len(cat["books"]))

print("\n=== 'license' / 'verification' prose-only claims ===")
print("lunyu_zhuxi.json description:", cm["description"])
kg = load(P / "knowledge_graph.json")
print("knowledge_graph.json meta:", kg["meta"])
tl = load(P / "timeline.json")
print("timeline.json meta:", tl["meta"])
idm = load(P / "idioms.json")
print("idioms.json meta:", idm["meta"])

print("\n=== author/dynasty coverage per book-level container ===")
print("lunyu.json:", {k: load(P / "lunyu.json").get(k) for k in ["book", "author", "dynasty"]})
print("debate_classics.json: per-sage keys =", list(db["classics"]["laozi"].keys()))
print("  -> no author/dynasty/school at sage level; 'book' only")
for k, v in db["classics"].items():
    print("   ", k, "keys:", sorted(v.keys()), "| school field:", v.get("school"))

print("\n=== proofread / human-confirmation evidence search ===")
hits = []
for p in [P / "lunyu.json", P / "debate_classics.json",
          ROOT / "backend" / "data" / "commentaries" / "lunyu_zhuxi.json",
          P / "idioms.json", P / "quote_cards.json"]:
    t = p.read_text(encoding="utf-8")
    for kw in ["校对", "复核", "人工", "审定", "proofread", "verified", "reviewed"]:
        if kw in t:
            hits.append((p.name, kw))
print("keyword hits:", hits if hits else "NONE - no structured or prose human-review record found")
