# -*- coding: utf-8 -*-
"""PHASE 0 read-only audit helper: generator reproducibility + textual defect detail.
Imports build_lunyu.py in memory and compares to the on-disk JSON. Writes nothing."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data" / "processed"

spec = importlib.util.spec_from_file_location("build_lunyu", ROOT / "data" / "scripts" / "build_lunyu.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

gen_lunyu = mod.build_lunyu()
gen_quotes = mod.build_quotes()
disk_lunyu = json.load(open(P / "lunyu.json", encoding="utf-8"))
disk_quotes = json.load(open(P / "lunyu_quotes.json", encoding="utf-8"))

print("=== reproducibility: build_lunyu.py output vs on-disk lunyu.json ===")
print("lunyu identical:", gen_lunyu == disk_lunyu)
print("quotes identical:", gen_quotes == disk_quotes)
if gen_lunyu != disk_lunyu:
    gl = {(c["chapter_title"], v["verse_id"]) for c in gen_lunyu["chapters"] for v in c["verses"]}
    dl = {(c["chapter_title"], v["verse_id"]) for c in disk_lunyu["chapters"] for v in c["verses"]}
    print("  only in generator:", sorted(gl - dl))
    print("  only on disk:", sorted(dl - gl))

print("\n=== 3.22 textual defect detail ===")
d = disk_lunyu
for c in d["chapters"]:
    for v in c["verses"]:
        if v["verse_id"] == "3.22":
            o = v["original"]
            print("original repr:", repr(o))
            print("count「:", o.count("「"), " count」:", o.count("」"))
            print("contains 曰：「邦君:", "曰：「邦君" in o)
            print("tail:", repr(o[-30:]))
            print("translation:", v["translation"][:200])

print("\n=== all verses: 「/」 balance ===")
bad = []
for c in d["chapters"]:
    for v in c["verses"]:
        o = v["original"]
        if o.count("「") != o.count("」"):
            bad.append((v["verse_id"], o.count("「"), o.count("」")))
print("unbalanced:", bad)

print("\n=== annotation totals ===")
tot = sum(len(v.get("annotations", [])) for c in d["chapters"] for v in c["verses"])
print("total annotations on disk:", tot)

print("\n=== script size / structure ===")
src = (ROOT / "data" / "scripts" / "build_lunyu.py").read_text(encoding="utf-8")
print("build_lunyu.py lines:", len(src.splitlines()))
print("contains network imports (requests/urllib/http):",
      any(t in src for t in ["import requests", "urllib", "http.client", "openai"]))
print("CH1/CH2/CH3 present:", all(t in src for t in ["CH1 = {", "CH2 = {", "CH3 = {"]))
print("OTHER_CHAPTERS present:", "OTHER_CHAPTERS" in src)
