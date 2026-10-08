# -*- coding: utf-8 -*-
"""PHASE 0 read-only audit helper: L1-L5 layer mapping + attribution risk scan."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data" / "processed"

def load(p):
    return json.load(open(p, encoding="utf-8"))

d = load(P / "lunyu.json")
lv = {v["verse_id"]: v["original"] for c in d["chapters"] for v in c["verses"]}
db = load(P / "debate_classics.json")

print("=== substring overlap: debate verses vs lunyu.json ===")
for k, v in db["classics"].items():
    for x in v["verses"]:
        o = x["original"].rstrip("。")
        hit = [vid for vid, t in lv.items() if o in t]
        if hit:
            print("  %-14s %-26s -> substring of lunyu %s" % (k, x["id"], hit))
        else:
            print("  %-14s %-26s -> NOT in lunyu.json" % (k, x["id"]))

print("\n=== internal attribution conflicts (same sentence, two claimed sources) ===")
idioms = load(P / "idioms.json")["idioms"]
for x in idioms:
    for k, v in db["classics"].items():
        for y in v["verses"]:
            a = x["original_text"].rstrip("。").replace("，", "").replace("：", "")
            b = y["original"].rstrip("。").replace("，", "").replace("：", "")
            if a and b and (a in b or b in a):
                print("  CONFLICT: idioms.json says 论语/%s/%s  |  debate_classics[%s] says %s" % (
                    x["chapter"], x["idiom"], k, y["source"]))

print("\n=== L1-L5 layer inventory ===")
print("L1 authoritative originals (text_type=original):")
print("   lunyu.json verses:", len(lv))
print("   debate_classics.json verses:", sum(len(v['verses']) for v in db['classics'].values()))
print("L2 commentaries:")
cm = load(ROOT / "backend" / "data" / "commentaries" / "lunyu_zhuxi.json")
print("   lunyu_zhuxi.json:", len(cm["commentaries"]), "commentator(s):", {x["source"] for x in cm["commentaries"]})
kg = load(P / "knowledge_graph.json")
persons = [n for n in kg["nodes"] if n.get("type") == "person"]
concepts = [n for n in kg["nodes"] if n.get("type") == "concept"]
print("L3 persons/schools/relations (knowledge_graph.json):")
print("   nodes:", len(kg["nodes"]), "persons:", len(persons), "concepts:", len(concepts),
      "edges:", len(kg["edges"]))
print("   persons:", [n["id"] for n in persons])
print("   concepts:", [n.get("label") for n in concepts])
print("L4 thought concepts (other sources):")
tags = set()
for x in idioms:
    tags |= set(x.get("tags", []))
for x in load(P / "quote_cards.json"):
    tags |= set(x.get("tags", []))
print("   concept-ish tags from idioms/quote_cards:", len(tags), sorted(tags)[:40])
print("L5 modern problems:")
qc = load(P / "quote_cards.json")
print("   quote_cards.json modern_interpretation:", sum(1 for x in qc if x.get("modern_interpretation")))
q = load(P / "lunyu_quotes.json")["quotes"]
print("   lunyu_quotes.json scene (modern scenario):", sum(1 for x in q if x.get("scene")))
print("   lunyu_quotes.json level:", sorted({x.get("level") for x in q}))
th = load(P / "theater_scripts.json")
print("   theater_scripts.json modern_setting:", [x.get("modern_setting") for x in th])
print("   timeline.json events:", len(load(P / "timeline.json")["events"]))
print("   idioms.json modern_usage:", sum(1 for x in idioms if x.get("modern_usage")))

print("\n=== D-grade (AI-authored explanation) content inventory ===")
print("quote_cards.json modern_interpretation sample:")
print("  ", qc[0]["modern_interpretation"][:120])
print("comics.json:", len(load(P / "comics.json")), "AI-illustrated script entries")
print("theater_scripts.json:", len(th), "entries; sample moral:",
      th[0].get("moral", "")[:80])
