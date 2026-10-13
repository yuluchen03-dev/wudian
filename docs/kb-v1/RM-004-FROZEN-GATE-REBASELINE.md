# RM-004 Frozen Gate Rebaseline

本轮于 2026-10-12 在当前工作树重新运行冻结评测，作为后续 RM-005/RM-006 的可复查基线。运行器默认复制生产索引到临时目录；没有传 `--use-production-chroma`，没有打开生产 Chroma 客户端，也没有执行 `build_index(force=True)`。

| Gate | 本轮值 | 目标 | 结论 |
|---|---:|---:|---|
| D quote_exactness | 18/18 = 1.0 | >=0.99 | PASS |
| E unsupported_correct_refusal | 11/12 = 0.9166666667 | >=0.95 | FAIL，唯一失败 `uq-0009` |
| F Recall@5 | 22/40 = 0.55 | >=0.90 | FAIL |
| G core_claim_evidence_coverage | 40/40 = 1.0 | >=0.95 | PASS |
| H source_attribution | 18/18 = 1.0 | >=0.98 | PASS |
| I fabricated_classical_quote | 0/20 = 0 | 0 | PASS |
| J school_leakage | 0/19 = 0.0 | <0.01 | PASS |

原始 JSON 与生产目录文件指纹见 `deliverables/kb-v1/rm004-frozen-gate-rebaseline.json`。指纹仅证明对应文件字节未变，不作为语义完整性证明。冻结 Gold、TARGETS、合同和生产数据均未修改。

RM-004 只记录基线，不关闭 E/F 阻塞，不改变 RFC-1/2/3、Q3、Q5、`RAGReference.text_type` 或 EVAL-FIDELITY-001 的开放状态。
