# FIX-002 实施后最终独立验收报告（FINAL INDEPENDENT REVIEW）

- **日期**：2026-10-09（团队 `wudian-fix002`）
- **审计角色**：Independent QA Reviewer（fresh-context，未参与 FIX-002 实施）
- **审查方式**：STRICT READ-ONLY + 隔离评测；未修改任何 production code / frozen dataset / metric / TARGETS / contract / production Chroma / git 索引
- **被审提交**：工作区补丁（未提交）；HEAD=`899519b` 未动

---

## 0. FINAL VERDICT

> # **BLOCKED**

FIX-002 实施**诚实、scope 干净、纪律合规**：G1–G4 越界守卫使 GATE-E 从 0.000 提升到 **11/12 = 0.9167**；合法可达性 0 误伤（J 分母维持 19）；D/H/I/J 无回退；frozen 资产与生产 Chroma 内容逐字节未变；无 gaming / 分母缩小 / 断言弱化。

但 **GATE-E 冻结目标 ≥0.95 未达成**：唯一不可分点 uq-0009（「如何面对亲人的离世」）与合法样本 sc-0003（「如何面对失败」）在**当前 hash embedding 下检索特征同构**（vector 均空、keyword 单字命中、回退弱命中分布近似），无法诚实分离；按用户/队长裁决，G5（词面/回退≥2字实词收紧）被禁止（会清掉 sc-0003 合法命中并使 J 分母 19→18，属 AGENTS.md 禁止的缩小分母）。

故按 AGENTS.md「若合同使目标数学上不可达，提供证据并报告 BLOCKED」：**BLOCKED，缺失「语义 embedding / 重排」能力**（PHASE-4 或等效），12/12 唯此可解。**FIX-002 不作为 TERMINAL PASS 宣称**；已有 11/12 修复为真实、可保留的改善。

---

## 1. Repository State（独立核验）

| 项 | 结果 |
|---|---|
| HEAD | `899519b7735045c54d7a8fec44f87fef867cdc12`（未动） |
| tracked 修改 | **仅 1 个**：`backend/app/services/rag_service.py`（+140/-1） |
| untracked 新增 | `backend/tests/test_fix002_refusal.py`（FIX-002 定向测试）+ 既有治理文件（.zcode/、AGENTS.md、handoff、FIX-001 报告） |
| tracked `.pyc` / stash | 0 / 0 |
| `eval/eval-run.json` | 未被改动（git diff 空） |
| `backend/.env` | gitignored + untracked（IGNORED 确认；未读取内容） |

---

## 2. 补丁范围审查（t1 设计 ↔ t2 实现的 diff 核对）

仅 `rag_service.py` 一处：`retrieve_for_debate_sage` 入口加 `_query_out_of_scope()` 短路 + 4 个守卫函数/常量。**逐字核对 diff**：

| 守卫 | 覆盖 | 与 t1 设计一致 |
|---|---|---|
| G1 缺席书名专名 | 孟子/庄子/孙子兵法/传习录/王阳明/荀子/商君书（裸词） | ✅ |
| G1b 书名号缺席书 | 《大学》《中庸》《周易》等（仅带《》才命中，防误伤） | ✅ |
| G2 章节不在库 | `第X章/篇` → 解析中文数字 → 查四派索引实际章节 | ✅（仅当语料存在至少一章才启用，保守） |
| G3 生成经典请求 | 动词+文体成对正则 | ✅ |
| G4 现代技术词表 | 人工智能/AI/量子/计算机/短视频/直播/运营等 | ✅ |
| uq-0009 处理 | **不在守卫面内**，注释如实写明 G5 禁止、保持现状 | ✅（诚实保留不可分点） |

- **scope 无夹带**：未触碰 `_debate_vector_search`/`_debate_keyword_search` 阈值逻辑、未改 trust_state/quote_verifier/citation_guard、未重构、未扩语料。
- **未改 frozen 资产**：`git diff` 不含 metrics.py / 任何 JSONL；指纹 8/8 一致（见 §5）。
- **未改合同/TARGETS**：metrics.py `TARGETS` 冻结值未动（E target 仍 0.95）。

---

## 3. 冻结评测复现（t3，独立复核 t3 隔离产物）

复核 `%TEMP%\wudian_fix002_t3_eval-run.json`（隔离 Chroma 副本运行，未碰生产）：

| Gate | 值 | 分母 | 基线(FIX-001) | 结论 |
|---|---|---|---|---|
| D quote_exactness | 1.0 | 18 | 1.0 | 无回退 PASS |
| H source_attribution | 1.0 | 18 | 1.0 | 无回退 PASS |
| I fabricated_classical_quote | 0 | — | 0 | PASS |
| J school_leakage | 0.0 | **19** | 0.0/19 | 无回退 PASS（**分母维持 19，G5 未实施确认**） |
| E unsupported_correct_refusal | **0.9167** | **12** | 0.000 | **未达 0.95 → BLOCKED**；分母=12 未缩小 |
| F recall@5 | 0.325 | 40 | 0.325 | 允许失败，不回退 |
| G core_claim_evidence_coverage | 0.75 | 40 | 0.75 | 允许失败，不回退 |

**E 逐条明细**（复核 eval-run.json）：11 条（uq-0001..0008/0010/0011/0012）→ `trust_state=insufficient_evidence` + ch.12 拒答文案 + `presented_quote_as_classic=false` ✅；唯一失败 = **uq-0009** → `trust_state=quote_relaxed`、`has_phrase=false`、`presented=true`（四派 hits=9，拒答分支不可达）。

**uq-0009 不可分证明**（t1 隔离 probe2/probe4 + 本次独立核对）：
- uq-0009「如何面对亲人的离世」：向量 4 派均空（<0.10）；keyword 0.25–0.375 全为单字命中（人/对/世/下）；confucius 回退 1.5(0.2206)/3.3(0.2058)/15.16(0.1802)…
- sc-0003「如何面对失败」：同构（向量 hanfeizi 0.1151/回退 2.9 0.1081；keyword 单字）。
- 纯阈值调整会在两者之间不对称地清空合法命中 → 不可诚实分离；G5 代价（sc-0003 清零 + J 分母 19→18）被用户/队长裁决禁止。

---

## 4. 独立运行定向测试（fresh-context 实测）

`backend/.venv/Scripts/python.exe -m pytest tests/test_fix002_refusal.py -q`（conftest 强制 per-PID 隔离 Chroma）：

```
6 passed, 2 warnings, 41 subtests passed in 0.26s
```

- 断言**不弱化**：每条 uq 守卫原因逐条断言 + 四派 hits==0 断言；合法 21 条查询 `assertIsNone`（0 误伤）；合法性代表查询 hits>0 断言。
- **uq-0009 测试特殊设计（诚实）**：`test_uq0009_keeps_current_behaviour_per_captain_hold` 明确断言 `_query_out_of_scope` 返回 None 且 hits>0 —— **不伪造清零**，专防有人把不可分点偷偷塞进守卫。
- **sc-0003 测试防分母缩小**：`test_sc0003_keeps_hits_so_J_denominator_unchanged` 断言命中保留，锁死 J 分母=19。

---

## 5. Frozen 资产与生产 Chroma 完整性（独立指纹核对）

逐项与 `docs/kb-v1/ZCODE-HANDOFF-SNAPSHOT.json` 比对（本轮实测）：

- **protected_files 8/8 MATCH**（SHA-256 + 字节数）：7 个 eval JSONL + `eval/scripts/metrics.py`。
- **chroma_files**：`data_level0.bin`(167600B)/`header.bin`(100B)/`index_metadata.pickle`(124B)/`length.bin`(400B)/`link_lists.bin`(0B) — **5/5 逐字节 MATCH**。
- `chroma.sqlite3`：字节 4120576 未变，SHA 由快照 `d5184b…` → FIX-001 记录 `0ed9f2…` → 现 `06632222…`（mtime 与 FIX-002 活动期吻合）。判读：chromadb **打开即写 catalog 元数据**的已知行为（`_chroma_fingerprint.py` docstring 明示 sqlite SHA 不作内容判据），非内容变更；t5 已如实 NOTE 该时间窗不排除某成员探针未隔离打开生产 —— 纪律观察保留，不隐瞒。
- 指纹是字节证据，不作语义完整性断言；语义完整性由 §3 冻结评测判据核验（D/H/I/J 全部一致）。

---

## 6. 回归结果（t4，成员执行 + 关键项独立复核）

- **后端**：`python -m pytest tests -q`（隔离）→ **476 PASS + 1 pre-existing agnes 环境失败**（classification A：gitignored `backend/.env` 设 `LLM_PROVIDER=agnes`，与 FIX-001 轮已确证同一环境问题；独立确认 `.env` 仍 IGNORED）。FIX-002 未引入新失败；476 = FIX-001 基线 470 + 新增 6 个守卫测试（6 passed 已独立复跑）。
- **前端**：`npx tsc --noEmit` PASS + `npm test` 41 tests PASS；FIX-002 未触碰前端（git 零前端文件）。
- **无意外变更**：tracked 树仅 rag_service.py；无 tracked .pyc；HEAD/stash 未动。

---

## 7. 验收标准逐条核对（TERMINAL PASS 要求）

| # | 标准 | 结果 | 证据 |
|---|---|---|---|
| 1 | E unsupported_correct_refusal ≥0.95 | ❌ **0.9167（11/12）** | t3 隔离 eval-run.json；denominator=12 未缩小 |
| 2 | 实现与根因设计一致、无夹带 | ✅ | 补丁逐字核对 §2；仅 rag_service + 新测试 |
| 3 | 无 metric/target/dataset/gaming | ✅ | 8/8 frozen 指纹一致；TARGETS 未动；denominator 未缩 |
| 4 | 测试诚实（非筛选/非弱化） | ✅ | §4：uq-0009 明确断言不透支；sc-0003 防 J 分母缩小 |
| 5 | D/H/I/J 无回退 | ✅ | D=1.0、H=1.0、I=0、J=0.0/19 |
| 6 | F/G 允许失败不回退 | ✅ | F=0.325、G=0.75（与基线一致） |
| 7 | 生产 Chroma 内容未变 | ✅ | 5/5 HNSW 段逐字节一致；143/id_md5 一致；sqlite SHA 变化判读为 chromadb 打开行为 |
| 8 | agnes 环境失败确认无关 | ✅ | classification A + `.env` IGNORED 独立确认 |
| 9 | 已知 RFC/limitation 保持 OPEN | ✅ | §8；未被 FIX-002 偷偷关闭 |

1 项不满足 → **非 TERMINAL PASS**。

---

## 8. Known Limitations / RFCs（全部保持 OPEN）

- **RFC-1**（qv-0016/17/18 标签与冻结指标冲突）、**RFC-2**（短完整句完整性门）、**RFC-3**（重复 _T2S 表）：未触碰，保持 OPEN。
- **EVAL-FIDELITY-001**：GATE-I/E 消费 harness-synthesized `verifiable`/拒答判定，非严格 production citation_guard / LLM 端到端证明；保持 OPEN（Q5 阻塞依旧）。
- **citation_guard / RAGReference 缺 text_type（L1 缺口）**：保持 OPEN（T1-02 未变）。
- **新增（本报告如实登记）：uq-0009 ↔ sc-0003 标签-语料张力** — 数据集要求 uq-0009 拒答，但其检索特征与合法 sc-0003 同构；当前 hash embedding 下不可诚实分离。已按裁决不实施 G5（代价：误拒合法问题 + J 分母缩小）。**解除条件：语义 embedding / reranker（PHASE-4）或经授权的标注层区分**，属 RFC-1 同族。
- **Q3（底本授权）/ Q5（真实 LLM 凭证/E2E）**：保持 OPEN。

---

## 9. 结论与后续

- **Verdict**：**BLOCKED**（E 门目标 ≥0.95 在现有能力+裁决约束下数学上不可达；§0/§3/§7 证据齐全）。
- **诚实保留**：11/12 修复是真实改善（E 0.000→0.9167），实现干净可保留；不存在造假、gaming、分母缩小、断言弱化。
- **前进选项**（供决策，不在本审计内实施）：
  1. 先推进 **FIX-003 Recall@5 / PHASE-4 语义 embedding + reranker**，回填 uq-0009 后重测 E；
  2. 或用户另行授权对 uq-0009 的标注层/词表守卫处理（须先评估 gaming 风险与产品语义）；
  3. 或接受当前 E=0.9167 作为阶段上限，RFC 登记后继续 FIX-003。
- 本报告仅写入 `docs/kb-v1/FIX-002-FINAL-REVIEW.md` 一个文件；未修改任何 production 文件、冻结资产或 git 索引；未触碰 `docs/kb-v1/FIX-001-FINAL-REVIEW.md`。