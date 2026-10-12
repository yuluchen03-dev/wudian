import json
from pathlib import Path

d = json.loads(Path(r"eval/eval-run.json").read_text(encoding="utf-8"))
r = d["results"]
print("chroma.used_production:", d.get("chroma", {}).get("used_production"))
print()
for k in ("quote_exactness", "unsupported_correct_refusal",
          "core_claim_evidence_coverage", "source_attribution",
          "fabricated_classical_quote", "school_leakage"):
    m = r.get(k, {})
    print(f"{k:32s} num={m.get('numerator')} den={m.get('denominator')} "
          f"value={m.get('value')} target={m.get('target')} passed={m.get('passed')}")
print()
rt = r.get("retrieval", {})
for k in ("recall_at_1", "recall_at_3", "recall_at_5"):
    m = rt.get(k)
    v = m.get("value") if isinstance(m, dict) else m
    print(f"retrieval.{k:14s} = {v}")
print(f"retrieval.mrr               = {rt.get('mrr')}")
print(f"retrieval.target_recall_at_5= {rt.get('target_recall_at_5')}")
print(f"retrieval.passed            = {rt.get('passed')}")
print(f"retrieval.samples           = {rt.get('samples')}")
print(f"retrieval.failures (len)    = {len(rt.get('failures') or [])}  <- truncated to 10 in harness")
