# FIX-003 实施后最终独立验收报告（FINAL INDEPENDENT REVIEW）

- **日期**：2026-10-10（团队 `wudian-fix003`）
- **审计角色**：Independent QA Reviewer（fresh-context，未参与 FIX-003 实施）
- **审查方式**：STRICT READ-ONLY + 隔离评测；未修改 production code / frozen dataset / metric / TARGETS / contract / production Chroma / git 索引
- **被审提交**：工作区补丁（未提交）；HEAD=`899519b7735045c54d7a8fec44f87fef867cdc12` 未动

---

## 0. FINAL VERDICT

> # **BLOCKED**

FIX-003 实施**诚实、scope 干净、纪律合规**：D1（id 对齐）+ D2（词面关键词融合）使 GATE-F Recall@5 从 **0.325 → 0.55（22/40）**，净 +9 且旧 13 命中零丢失；合法可达性 0 误伤（J 分母维持 19）；D/H/I/J 无回退；frozen 资产与生产 Chroma 内容逐字节未变；无 gaming / 分母缩小 / 断言弱化。

但 **GATE-F 冻结目标 ≥0.90 未达成**：剩余 18 条失败中 **4 条（rg-0003/0021/0035/0036）为语义硬底**（hash embedding 下期望原文无任何查询词面、向量 top20 外，词面检索与纯向量均够不着），其余为词面竞争/排序不足以进 top5；在**当前 hash embedding 能力下**，0.90 由 t1 诊断为"理论上贴线、工程上极脆弱"，本回合实测封顶 22/40（t2 参数扫描 9 组无更高组合，未凑分）。

故按 AGENTS.md「若合同使目标数学上不可达，提供证据并报告 BLOCKED」：**BLOCKED，缺失「语义 embedding / 重排」能力**（PHASE-4 或等效），36/40=0.90 唯此可解。**FIX-003 不作为 TERMINAL PASS 宣称**；已有 0.325→0.55 为真实、可保留的改善。

---

## 1. Repository State（独立核验）

| 项 | 结果 |
|---|---|
| HEAD | `899519b7735045c54d7a8fec44f87fef867cdc12`（未动） |
| tracked 修改 | **仅 1 个**：`backend/app/services/rag_service.py`（+268/-3） |
| untracked 新增 | `backend/tests/test_fix003_recall.py`（FIX-003 定向测试）+ `backend/tests/test_fix002_refusal.py`（FIX-002 保留，未提交）+ 既有治理文件（.zcode/、AGENTS.md、FIX-001/002 报告、handoff 快照） |
| tracked `.pyc` / stash | 0 / 0 |
| `eval/eval-run.json` | 未被改动（`git status --porcelain eval/` 为空） |

---

## 2. 补丁范围审查（t1 设计 ↔ t2 实现的 diff 核对）

仅 `rag_service.py` 一处，新增函数/常量集中（read-only diff 核对）：

| 项 | 与 t1 设计一致 | 备注 |
|---|---|---|
| `_kw_search_chroma`（D2 词面检索） | ✅ | 对同义词展开词/汉字 bigram/单字逐词做 `where_document $contains` 并打分，修复原始 `keyword_search` 用整段现代句必空问题；按 `/12.0` 防单字泛命中挤掉向量命中 |
| `_merge_retrieval`（D2 融合） | ✅ | vector 0.7 + kw 0.3 加权融合去重，替换 `retrieve_for_sage_chat` 纯向量路径 |
| retrieve_for_sage_chat 输出层 id 对齐（D1） | ✅ | 对 scope=debate_classic 的 verse_id 对齐为 `debate:{sage_key}:{verse_id}`；**不改 metrics.py 冻结 `normalize_passage_id`** |

**不夹带核验**：`_query_out_of_scope`（G1-G4，FIX-002）与 `_cn_to_int` / `_GEN_VERB_RE` 均属 FIX-002 已保留代码，与 FIX-003 无新增行为耦合；`_debate_vector_search` / `_debate_keyword_search` / confucius 回退路径未被 FIX-003 触碰（diff 未改这些函数体）。`metrics.py` / `TARGETS` / 7 个 GL / 生产 chroma 均未被改动。

---

## 3. 补丁功能独立验证（read-only，隔离 Chroma）

- **D1 id 对齐生效**：rg-0022 查询「不争真的有用吗？」top5 含 `debate:laozi:daodejing-22-01`（gold 期望 `debate:laozi:daodejing-22-01`）；rg-0025 含 `debate:mozi:mozi-jianai-01`；rg-0027 含 `debate:hanfeizi:hanfeizi-youdu-01` → 经冻结 `normalize_passage_id`（只剥一层前缀）后与 Gold **相等**。✅
- **C 类语义硬底实测确认**：rg-0003 / rg-0021 / rg-0035 / rg-0036（用 Gold 正确 query 重放）top5 均**不含**任一期望 id → 确为不可救。✅（注意：t1 曾将 rg-0035 归 C 类，本 reviewer 用正确 query 验证其 top5=`15.16/16.9/20.3/5.9/2.10`，不含 `15.28`/`1.16` → 判定成立）

---

## 4. 冻结评测独立复现（read-only，run_eval 默认隔离副本）

本 reviewer 直接重跑 `eval/scripts/run_eval.py --out <临时>`（设 JWT_SECRET_KEY=conftest 测试专用值，未读 backend/.env；不传 `--use-production-chroma`）。`used_production=False`，isolation（临时 Chroma 副本）为真。

| Gate | 实测 | 冻结目标 | 判定 |
|---|---|---|---|
| **GATE-F recall_at_5** | **0.55（22/40，samples=40）** | 0.90 | **FAIL（未达）** |
| recall_at_1 | 0.325 | — | — |
| recall_at_3 | 0.475 | — | — |
| mrr | 0.409 | — | — |
| D quote_exactness | 1.0（18） | 0.99 | PASS |
| H source_attribution | 1.0（18） | 0.98 | PASS |
| I fabricated_classical_quote | 0 | 0 | PASS |
| J school_leakage | 0.0（denom=19） | <0.01 | PASS |
| E unsupported_correct_refusal | 0.9167（11/12） | 0.95 | FAIL（FIX-002 遗留，uq-0009 仍为 BLOCKED 项） |
| G core_claim_evidence_coverage | 0.75（40） | 0.95 | FAIL（允许失败不回退） |

**denominator 未缩小**：F=40、E=12、J=19、D=18，全部保持基线；**TARGETS `recall_at_5=0.90` 未动**（read-only 核对 metrics.py）。

---

## 5. 测试诚实性核验（test_fix003_recall.py）

- `test_old_13_hits_all_kept`：断言冻结基线 13 命中（rg-0002/0005/0007/0008/0009/0011/0013/0014/0017/0032/0033/0034/0040）零回归 ✅
- `test_d1_aligned_six_hits`（rg-0022/23/24/25/27/28）与 `test_kw_gained_hits_kept`（rg-0004/19/26）✅
- `test_semantic_hard_floor_measured_not_regressed_up`：**断言 C 类 4 条保持 miss，不假装清零** —— 这是反 gaming 的诚实边界断言 ✅
- `test_full_40_recall_measured`：断言实测命中集 == EXPECTED_HITS（22/40），交 t3 复现基线 ✅
- `test_sc0003_hits_preserved_j_denominator_not_shrunk`：断言「如何面对失败」（confucius 合法）命中保留 → J 分母不缩 ✅
- `test_fix002_guards_still_fire`：断言 G1-G4 守卫不回退（复用 FIX-002 语义） ✅
- 断言全部从冻结 `eval/retrieval_gold.jsonl` 读取，不硬编码 query/id（sample 筛选或弱化断言未发现）✅

---

## 6. 全量回归（t4）与 Chroma 完整性（t5）核验

- **后端**（venv 隔离真实命令）：486 PASS + 1 pre-existing agnes 环境失败（classification A：gitignored backend/.env LLM_PROVIDER=agnes 引起；对照实验从仓库根目录跑同测试 → 1 passed；FIX-003 仅改 rag_service.py，不触碰 config.py/test_ai_provider.py/llm_client.py）✅
- **前端**：tsc exit 0 PASS + vitest 41 tests PASS（FIX-003 未触碰前端，git diff -- frontend 为空）✅
- **Chroma 内容完整性（本 reviewer 独立指纹）**：8/8 protected_files SHA256+字节数与 ZCODE-HANDOFF-SNAPSHOT.json 逐字节一致；HNSW 段 data_level0.bin(167600B)/header.bin(100B)/length.bin(400B)/link_lists.bin(0B)+index_metadata.pickle(124B) 的 SHA-256 与快照逐字节一致；`chroma.sqlite3` 大小 4120576B 未变、SHA 现 `8c0170ca`（判读为 chromadb 打开即写 catalog 元数据的已知行为，模块 docstring 明示 sqlite sha 不作内容判据；mtime 落在 FIX-003 活动期，有成员探针或打开生产风险，已如实 NOTE、非 FIX-003 变更驱动）✅

---

## 7. 已知未解决事项（保持 OPEN，未偷关）

- RFC-1：冻结 exact_match/expected.trust_state 标签与指标/合同语义冲突（三条真实古句缺失不能称伪造）
- RFC-2：真实短句完整性规则（「君子不器」）
- RFC-3：重复且不一致的 `_T2S` 表
- EVAL-FIDELITY-001：fabricated 指标依赖 harness 合成 verifiable，未直接证明 production citation_guard 行为
- citation_guard / RAGReference 缺失 `text_type`，L1 限制不能被统一强制
- Q3：语料授权与权威底本阻塞
- Q5：真实 LLM 凭证与端到端验证阻塞
- uq-0009↔sc-0003 标签-语料张力（FIX-002 登记，E 门 11/12 上限）
- **新增**：FIX-003 `Recall@5` 语义硬底 —— 4 条（rg-0003/0021/0035/0036）在 hash embedding 下不可救，rhs 提升到 0.90 需语义 embedding/重排（PHASE-4）

---

## 8. 结论与建议

**BLOCKED**：实现与评测干净、无作弊；GATE-F Recall@5 从 0.325 → 0.55 是真实改善并保留。0.90 目标在当前 hash embedding + 词面检索能力下不可达（4 条语义硬底 + 词面竞争不足），唯语义 embedding/重排（PHASE-4）可解。FIX-003 不作为 TERMINAL PASS 宣称。

**前进选项（非本审计实施）**：
1. **PHASE-4 语义 embedding + reranker**（或等效），回填 4 条语义硬底并改善词面竞争后，重测 GATE-F → 目标 0.90；
2. 接受 0.55 为阶段上限，继续既有接力顺序（FIX-004 核心观点证据覆盖），待 PHASE-4 后再闭环 F 门；
3. 由用户另行授权专项处理。

未实施 FIX-004/E2E；未触碰 FIX-001/002 报告；未修改 production Chroma / frozen 资产 / git 索引。
