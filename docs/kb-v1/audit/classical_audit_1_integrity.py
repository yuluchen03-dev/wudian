# -*- coding: utf-8 -*-
"""PHASE 0 read-only audit helper: referential integrity checks. No writes to product data."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / "data" / "processed"

d = json.load(open(P / "lunyu.json", encoding="utf-8"))
ids = set()
for c in d["chapters"]:
    for v in c["verses"]:
        ids.add(v["verse_id"])
print("lunyu verse ids:", len(ids))

CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
      "十": 10, "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15, "十六": 16,
      "十七": 17, "十八": 18, "十九": 19, "二十": 20}

print("\n=== lunyu_quotes.json source -> verse_id resolution ===")
q = json.load(open(P / "lunyu_quotes.json", encoding="utf-8"))
bad = []
for x in q["quotes"]:
    s = x["source"]
    m = re.match(r"^(.*?)(第[一二三四五六七八九十]+)·(\d+)$", s)
    if not m:
        bad.append((x["id"], s, "UNPARSED"))
        continue
    chap = CN[m.group(2).lstrip("第")]
    vid = "%d.%s" % (chap, m.group(3))
    if vid not in ids:
        bad.append((x["id"], s, "-> " + vid + " NOT IN lunyu.json"))
print("unresolvable:", len(bad))
for x in bad:
    print("  ", x)

print("\n=== idioms.json chapter_num.verse_num -> verse_id resolution ===")
i = json.load(open(P / "idioms.json", encoding="utf-8"))
bad2 = []
for x in i["idioms"]:
    vid = "%s.%s" % (x["chapter_num"], x["verse_num"])
    if vid not in ids:
        bad2.append((x["idiom"], vid, x["source"], x["original_text"][:30]))
print("unresolvable:", len(bad2))
for x in bad2:
    print("  ", x)

print("\n=== idioms original_text vs lunyu original (substring check) ===")
orig = {}
for c in d["chapters"]:
    for v in c["verses"]:
        orig[v["verse_id"]] = v["original"]
mismatch = 0
for x in i["idioms"]:
    vid = "%s.%s" % (x["chapter_num"], x["verse_num"])
    if vid in orig:
        t = x["original_text"].rstrip("。")
        if t not in orig[vid]:
            mismatch += 1
            print("  MISMATCH", x["idiom"], vid, "|", t[:40])
print("text mismatches:", mismatch)

print("\n=== quote_cards.json quote -> lunyu original (substring check) ===")
qc = json.load(open(P / "quote_cards.json", encoding="utf-8"))
joined = "".join(orig.values())
miss = 0
for x in qc:
    t = x["quote"].rstrip("。")
    if t not in joined:
        miss += 1
        print("  NOT FOUND IN lunyu.json:", x["id"], "|", x["quote"], "|", x["source"])
print("quote_cards not verbatim in lunyu.json:", miss, "/", len(qc))
