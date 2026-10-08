# WUDIAN-KB-V1 — Eval Report

- generated_at: `2026-10-08T09:38:48.068706+00:00`
- phase: PHASE 0 (eval baseline only; no evaluated system exists yet)

## 1. 语料 id 空间

- 可用 passage id: **143**
  - `l1_original`: 128
  - `l2_commentary`: 15

## 2. 七类数据集

| 数据集 | 条数 | provenance | 人工标注 |
|---|---|---|---|
| `retrieval_gold` | 40 | {'derived': 40} | 0 |
| `quote_verification` | 21 | {'derived': 21} | 0 |
| `source_attribution` | 18 | {'derived': 18} | 0 |
| `modern_to_classic` | 20 | {'derived': 20} | 0 |
| `school_consistency` | 17 | {'derived': 17} | 0 |
| `adversarial_quotes` | 20 | {'derived': 20} | 0 |
| `unsupported_questions` | 12 | {'derived': 12} | 0 |

**合计 148 条；人工标注 0 条。**

## 3. 指标公式与实测值

> 当前**不存在被评系统**（PHASE 4/5 未实现），故所有指标 `value = null`，状态 `not_computable`。**不以占位值冒充通过。**

| 指标 | 公式（分子/分母/判定） | 目标 | 当前值 | 状态 |
|---|---|---|---|---|
| Quote Exactness | 正确逐字匹配数 / 全部被判定为 quote_exists=True 的引文数 | >= 0.99 | null | not_computable |
| Source Attribution | source_correct 与期望一致数 / 全部引文数（独立于 quote_exists） | >= 0.98 | null | not_computable |
| School Leakage | 越界引用数 / 总引用数（引用 source 不属于该 sage 的 allowed_books） | < 0.01 | null | not_computable |
| Retrieval Recall@1 | (1/N) * sum(命中 expected ∩ top-1 非空) | — | null | not_computable |
| Retrieval Recall@3 | (1/N) * sum(命中 expected ∩ top-3 非空) | — | null | not_computable |
| Retrieval Recall@5 | (1/N) * sum(命中 expected ∩ top-5 非空) | >= 0.9 | null | not_computable |
| MRR | (1/N) * sum(1 / 首个命中 rank)，无命中记 0 | — | null | not_computable |
| Unsupported Correct Refusal | 正确拒答数 / 应拒答数；拒答须同时满足 trust_state=insufficient_evidence、含 ch.12 拒答语、未展示任何经典原文 | >= 0.95 | null | not_computable |
| Core Claim Evidence Coverage | 有 >=1 条 verification=supported 证据的核心 claim 数 / 全部核心 claim 数 | >= 0.95 | null | not_computable |
| Fabricated Classical Quote | expected.quote_exists=False 却被判 verifiable=True 的条数（目标绝对值为 0） | = 0 | null | not_computable |
| Latency P50/P95 | 本地检索 P50 / P95（秒），排除外部 LLM | P50<1.0s / P95<3.0s | null | not_computable |

### 不可计算的原因

- **quote_exactness**: 需要 QuoteVerifier 产出 predictions（PHASE 5 未实现）；且无外部 LLM/verifier 运行。
- **source_attribution**: 需要 QuoteVerifier 的 source_correct 判定（PHASE 5 未实现）；现状 citation_validator 不校验出处。
- **school_leakage**: 需要 RAG V2 真实检索结果（PHASE 4 未实现）；且 sage-chat 主路径无学派过滤（G-D 未修复）。
- **unsupported_correct_refusal**: 需要 Trust State 四态（PHASE 5 未实现）。另注意：C3 已在 _debate_keyword_search 修复（rag_service.py:500 `if score <= 0: continue`），但 retrieve_for_debate_sage 先走 _debate_vector_search（:1024）且无相关性阈值，实测垃圾查询仍返回 3 条 sim=0.0，故 insufficient_evidence 在该路径仍不可达。
- **core_claim_evidence_coverage**: 需要 Claim-Evidence 绑定（PHASE 5 未实现）。
- **fabricated_classical_quote**: 需要对抗套件对真实实现运行（PHASE 5）。数据集已就绪，但被评系统尚不存在。
- **latency**: 需要 RAG V2 实现后在真实规模语料上测量；当前 143 条基线不具代表性。
- **recall_at_k / mrr**: 需要 RAG V2 真实检索（PHASE 4 未实现）。注：C1 已由 t20 修复（schemas/ai.py:25 verse_no 改为 Optional[str]），实测 retrieve('学而时习之') 已返回 5 条；但当前 hybrid_search 的排序质量尚未评估，且语料仅 143 条、12 部书目仅 4 部有数据。

## 4. Gate 可达性

- **GATE-4**: 不可达：Recall@5>=90% 依赖 RAG V2；C1 已由 t20 修复（retrieve 已可用），但语料仅 143 条、12 部书目仅 4 部有数据，且检索排序质量未评估。
- **GATE-5**: 不可达：需 PHASE 5 Trust Layer；数据集已就绪但被评系统不存在。
- **GATE-6**: 不可达：需学派过滤（G-D 未修复）与各派语料扩充。
- **GATE-8**: 不可达：需 Trust State + Claim-Evidence + >=200 gold。

## 5. Gold 数据诚实性

- 人工标注条数: **0**
- 说明: 本数据集全部为规则/表格辅助构造（provenance=derived），**没有人工标注**。当前无法人工产出 1000 条。未将任何机器生成样本标为 human。
- 是否修改目标数字: **False**

## 6. 扩展到 1000 条

- 当前: 148 / 目标: 1000
- 方法: 按 book x concept x scenario 三维矩阵补齐缺口；每本书按章节分层抽样保证覆盖；新增数据集只用 derived 候选 + 真实人工确认后升级为 human；所有入库必须通过 validate_gold.py。
- 约束:
  - 禁止用 LLM 批量生成看似合理的 Gold 并标 human
  - expected_passage_ids 只能指向语料中真实存在的条目
  - 不得为了凑数编造 passage 或出处
- 阻塞:
  - PHASE 2 语料扩充（当前 12 部书目仅 4 部有数据）
  - PHASE 1 passage_id 正式化
  - 真实人工标注资源（当前不可得，故全部为 derived）
