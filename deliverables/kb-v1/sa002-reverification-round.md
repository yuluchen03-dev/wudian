# SA-002 — re-verification this round (captain, executed, read-only)

Question: can the **production citation path** distinguish an L1 canonical
original from an L2 commentary? Gate I being green does **not** answer this.

## Verdict: SA-002 remains **OPEN** — the limitation is confirmed present in code

### 1. `RAGReference` has no `text_type` field

`backend/app/schemas/ai.py:12-26` — the complete field list is:

```python
class RAGReference(BaseModel):
    text: str
    source: str
    chapter: Optional[str]
    verse_no: Optional[str]
    similarity: float
```

**No `text_type`.** So a `RAGReference` produced by retrieval carries no
machine-readable indication of whether the passage is a canonical original or a
later commentary.

### 2. The guard itself documents the gap

`backend/app/services/citation_guard.py:379-397`:

```
#   L1 判定  = 支持该引文的 ref 是否为原典（text_type == "original"）
# ⚠️ 已知限制（如实记录，不掩盖）：`RAGReference` 目前**没有
# `text_type` 字段**，rag_service 也未传播它，因此本函数**无法**从 refs
# 判断 L1。这里的处理是：ref 显式带 text_type 时按它判定；缺失时**保守**
...
if _supporting is not None and _supporting.get("text_type") is not None:
    is_l1 = _supporting.get("text_type") == "original"
```

The branch is guarded by `is not None`, and **nothing in the production
retrieval path sets `text_type` on a ref**. Therefore `is_l1` never takes its
`== "original"` value from retrieval data; the guard falls back.

### 3. The distinction exists elsewhere — but is not propagated

`text_type` is a first-class, frozen concept in the schema and model layers:

- `backend/app/schemas/knowledge.py:43` — `TextType` "恰四值（冻结）";
  `:321-337` enforces `commentary` must not appear in `Passage` (L1).
- `backend/app/models/knowledge.py:64-87` — DB constraints including
  `text_type <> 'commentary'` for the L1 table and a separate L2 commentary table.
- `backend/app/services/quote_verifier.py:190-283,507,635` — does construct
  entries with `text_type="original"` / `"commentary"` and uses
  `getattr(attribution_source, "text_type", None) == "original"`.

So the type information **exists in the ingestion/verification layer** but is
**dropped at the `RAGReference` boundary**. Both production call sites that build
refs (`rag_service.py:1286`, `ai_service.py:367/379/386`, `api/ai.py:201`) omit it.

### 4. Why Gate I cannot see this

Gate I (`fabricated_classical_quote`) is an absolute count of
`quote_exists is False`. A genuine L2 commentary **does exist in the corpus**, so
`quote_exists` is `True` and Gate I passes — even if that commentary is presented
to the user as "经典原文". This is precisely the structural invisibility recorded
in `deliverables/kb-v1/dsh-sa002-gate-invisibility-proof.md`; nothing this round
changes it.

## Status

```
SA-002 = OPEN  (confirmed this round, executed evidence)
fix required as a SEPARATE task -- NOT bundled into RM-005 or RM-006
```

The scope of the eventual fix is now pinned: add `text_type` to `RAGReference`
(schema), propagate it from the retrieval rows at the four construction sites,
and let `citation_guard` consume it instead of the `is not None` fallback.

**Not implemented here.** This round's authorization covers RM-005 verification;
inventing a schema change during a review round would violate the sequencing rule
and the "do not mix" instruction.
