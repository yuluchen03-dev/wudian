# -*- coding: utf-8 -*-
"""PHASE 0 read-only audit helper: corpus scale + coverage matrix. No writes to product data."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data" / "processed"

def load(p):
    return json.load(open(p, encoding="utf-8"))

print("=== A. file-level scale ===")
files = ["lunyu.json", "lunyu_quotes.json", "debate_classics.json", "classics_catalog.json",
         "knowledge_graph.json", "quote_cards.json", "timeline.json", "idioms.json",
         "comics.json", "theater_scripts.json"]
for f in files:
    p = P / f
    d = load(p)
    n = len(d) if isinstance(d, list) else "dict"
    print("%-24s %8d bytes  top=%s  n=%s" % (f, p.stat().st_size, n, ""))

print("\n=== B. authoritative-passage counts (L1) ===")
d = load(P / "lunyu.json")
lv = [(c["chapter_title"], v["verse_id"], v["original"]) for c in d["chapters"] for v in c["verses"]]
print("lunyu.json verses:", len(lv))
db = load(P / "debate_classics.json")
tot = 0
for k, v in db["classics"].items():
    n = len(v["verses"])
    tot += n
    print("  debate_classics[%s] book=%s verses=%d" % (k, v["book"], n))
print("debate_classics total:", tot)
print("unique original texts across both (dedup by exact string):")
s1 = {t for _, _, t in lv}
s2 = {x["original"] for v in db["classics"].values() for x in v["verses"]}
print("  lunyu only:", len(s1), " debate only:", len(s2), " overlap:", len(s1 & s2),
      " union:", len(s1 | s2))

print("\n=== C. commentary layer (L2) ===")
cm = load(ROOT / "backend" / "data" / "commentaries" / "lunyu_zhuxi.json")
print("commentaries:", len(cm["commentaries"]), "distinct commentators:",
      {x.get("source") for x in cm["commentaries"]})
print("coverage: %d/%d lunyu verses = %.1f%%" % (len(cm["commentaries"]), len(lv),
      100.0 * len(cm["commentaries"]) / len(lv)))

print("\n=== D. V1 target booklist coverage ===")
catalog = {b["title"]: b for b in load(P / "classics_catalog.json")["books"]}
targets = ["论语", "孟子", "荀子", "大学", "中庸", "道德经", "庄子", "墨子", "韩非子",
           "商君书", "传习录", "孙子兵法"]
corpus = {}
for t, vid, o in lv:
    corpus.setdefault("论语", 0)
    corpus["论语"] += 1
for k, v in db["classics"].items():
    corpus[v["book"]] = corpus.get(v["book"], 0) + len(v["verses"])
for t in targets:
    print("  %-8s catalog=%-5s corpus_passages=%s" % (
        t, "yes" if t in catalog else "NO", corpus.get(t, 0)))

print("\n=== E. non-Lunyu corpus books present ===")
for k, v in db["classics"].items():
    print("  ", k, "->", v["book"], len(v["verses"]))

print("\n=== F. schema field presence (structured, not prose) ===")
BRIEF = ["passage_id", "book_id", "book_title", "chapter_id", "chapter_title", "section",
         "line_no", "original", "original_traditional", "original_simplified",
         "source_provider", "source_url", "source_edition", "author", "dynasty",
         "text_type", "commentator", "commentary_dynasty", "school", "concepts",
         "modern_topics", "modern_scenarios", "stance", "verification_level",
         "proofread_status", "license", "embedding_version", "created_at", "updated_at"]
allkeys = set()
for f in files:
    d = load(P / f)
    def walk(o):
        if isinstance(o, dict):
            for k2, v2 in o.items():
                allkeys.add(k2)
                walk(v2)
        elif isinstance(o, list):
            for v2 in o:
                walk(v2)
    walk(d)
cmk = set()
for x in cm["commentaries"]:
    cmk |= set(x.keys())
allkeys |= cmk
for b in BRIEF:
    print("  %-22s %s" % (b, "PRESENT" if b in allkeys else "ABSENT"))
print("  all observed keys:", sorted(allkeys))
