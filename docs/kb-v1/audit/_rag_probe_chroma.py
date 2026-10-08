"""PHASE 0 read-only probe: inspect the persisted ChromaDB index.

Opens backend/chroma_db/chroma.sqlite3 in SQLite read-only URI mode.
Writes nothing. Safe to run repeatedly.
"""
import json
import sqlite3
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3] / "backend"
DB = BACKEND / "chroma_db" / "chroma.sqlite3"

print("db_path:", DB)
print("db_exists:", DB.exists(), "size:", DB.stat().st_size if DB.exists() else None)

con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
cur = con.cursor()

tables = [r[0] for r in cur.execute(
    "select name from sqlite_master where type='table' order by name")]
print("\nTABLES:", tables)

for t in ("collections", "segments"):
    if t in tables:
        cols = [d[1] for d in cur.execute(f"PRAGMA table_info({t})")]
        print(f"\n{t} columns:", cols)

print("\ncollections rows:")
for row in cur.execute("select id, name, dimension from collections"):
    print("  ", row)

print("\nsegments rows:")
for row in cur.execute("select id, type, scope from segments"):
    print("  ", row)

print("\nrow counts:")
for t in ("embeddings", "embedding_metadata", "embedding_fulltext_search"):
    if t in tables:
        print("  ", t, list(cur.execute(f"select count(*) from {t}"))[0][0])

# Distinct metadata keys actually stored, and the scope/doc_type distribution.
print("\nmetadata key distribution:")
# NOTE: use a separate cursor; reusing `cur` inside the loop resets the outer
# iteration and silently truncates the result to a single key.
cur2 = con.cursor()
keys = {}
for (k,) in cur.execute("select distinct key from embedding_metadata"):
    n = list(cur2.execute(
        "select count(*) from embedding_metadata where key=?", (k,)))[0][0]
    keys[k] = n
for k, n in sorted(keys.items(), key=lambda x: -x[1]):
    print(f"   {k}: {n}")

print("\nscope distribution:")
for scope, n in cur.execute(
    "select string_value, count(*) from embedding_metadata where key='scope' "
    "group by string_value order by 2 desc"
):
    print("   ", scope, n)

print("\ndoc_type distribution:")
for dt, n in cur.execute(
    "select string_value, count(*) from embedding_metadata where key='doc_type' "
    "group by string_value order by 2 desc"
):
    print("   ", dt, n)

print("\nsage_key distribution (debate_classic only):")
for sk, n in cur.execute(
    "select string_value, count(*) from embedding_metadata where key='sage_key' "
    "group by string_value order by 2 desc"
):
    print("   ", sk, n)

con.close()
