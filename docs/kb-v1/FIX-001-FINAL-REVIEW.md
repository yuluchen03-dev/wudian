# FIX-001 实施后最终独立验收报告（FINAL INDEPENDENT REVIEW）

- **日期**：2026-10-09（团队 `wudian-fix001-review`）
- **审计角色**：Independent QA Reviewer（fresh-context，未参与 FIX-001 实现）
- **审查方式**：STRICT READ-ONLY + 隔离评测；未修改任何 production code / frozen dataset / metric / TARGETS / contract / production Chroma / git 索引
- **被审提交**：`31afdc8`（FIX-001 实现）、`899519b`（supporting / reviewer-condition 分析工具）

---

## 0. FINAL VERDICT

> # **TERMINAL PASS**

FIX-001 通过最终独立验收。全部 11 项验收标准满足（详见 §10）。E / F / G 冻结指标继续 FAIL 属任务允许范围（handoff 一致），不构成 FIX-001 阻塞。已知 RFC / limitation 全部诚实保留 OPEN，未被偷偷关闭。**FIX-002 可以开始**（下一顺序：FIX-002 拒答修复）。

---

## 1. Repository State（与 handoff 逐项核验）

| 项 | handoff 声明 | 独立核验结果 | 一致 |
|---|---|---|---|
| working tree | clean | `git status`：工作树干净；仅存先前已存在的 untracked 项（`.zcode/`、`AGENTS.md`、`docs/kb-v1/ZCODE-HANDOFF*.md/json`） | ✅ |
| ahead of origin | 22 commits | `git branch -vv`：`codex/overall-optimization` ahead `origin/main` **22**，behind 0 | ✅ |
| nothing pushed | 未 push | 确认 ahead 22（未推送到 origin/main） | ✅ |
| HEAD | `899519b` | `git rev-parse HEAD` = `899519b7735045c54d7a8fec44f87fef867cdc12` | ✅ |
| FIX-001 实现提交 | `31afdc8` | 存在（`git cat-file -t` = commit），是 HEAD 的祖先 | ✅ |
| supporting 提交 | `899519b` | 存在，即 HEAD，message=「test(eval): close FIX-001 reviewer conditions C1-C6 in the analysis tool」 | ✅ |
| staged / untracked production change | 无 | `git status --porcelain`：无 staged 变更；untracked 仅上述 5 项（均非 production 代码） | ✅ |
| tracked `.pyc` | 无 | `git ls-files | Select-String '\.pyc$'`：**空**；无 stash | ✅ |

**结论**：仓库基础状态与 handoff 完全一致，无意外变更。

---

## 2. 提交范围审查（31afdc8 / 899519b）

### 2.1 `31afdc8`（FIX-001 实现提交）

涉及文件（`git show --stat`，6 个文件）：

| 文件 | 性质 |
|---|---|
| `backend/app/services/quote_verifier.py` | production 修复（exact_match/crosses_sentence_boundary） |
| `backend/app/services/trust_state.py` | production 修复（decide_trust_state / is_displayable_as_classic） |
| `backend/app/services/citation_guard.py` | production 修复（L1 / match_type 对齐） |
| `backend/tests/test_quote_contract.py` | **新增 37 用例**（合同测试） |
| `backend/tests/test_quote_verifier.py` | 3 处既有断言按合同变更 + **追加断言** |
| `eval/eval-run.json` | 评测运行记录更新 |

**独立判定**：

1. **scope 一致**：全部改动落在 FIX-001 目标（quote exactness / trust state / contract 对齐）内；无 unrelated refactor。
2. **未改 frozen metric**：`eval/scripts/metrics.py` 未被触碰（t4 指纹 8/8 一致；`git show --name-only` 无该文件）。
3. **未改 TARGET**：`metrics.py:17-27` 冻结 TARGETS 与 PROJECT-BRIEF ch.17 一致（t4 核验）。
4. **未改 Gold / frozen dataset**：7 个 eval JSONL 全部 SHA256 与接力快照逐字节一致（t4，8/8）。
5. **未削弱断言**：3 处既有断言（`test_c2_traditional_not_verified_when_not_exact`、`test_exists_correct_and_exact_is_verified`、`test_display_rules`）为 CONTRACT-001 v2 §3.2 RC3 明确要求的**合同变更**（`is_displayable_as_classic(quote_relaxed)` True→False），每处均**追加**断言（fail-closed 默认值、四项合取、恒等式）而非删减；并新增 37 个合同用例。
6. **未缩小 denominator**：冻结公式 `compute_quote_exactness`（`metrics.py:81-106`）未变；denominator = 系统判 `quote_exists=true` 的条数 = **18**（详见 §3）。
7. **符合 CONTRACT-001 v2**：§2.2 exact_match=连续子串+不跨句界；§3.3 crosses_sentence_boundary 拦截句界剥离拼接；§4 规则 3 `verified = exists∧exact∧source∧gate∧L1`；§3.2 可展示 ⇔ verified。实现逐项与合同一致（t1/t2 双独立通道 + 本次 spot-verify）。

**known-open 非阻塞（如实保留）**：
- **T1-01**：`is_verifiable`/`explain` 未按合同 §2.4/§4.1 同步收紧（`is_verifiable("quote_relaxed")` 仍为 True；`explain` 文案仍为归一化口径）。不影响 GATE-D scope，保持 OPEN。
- **T1-02**：`citation_guard` 因 `RAGReference` 缺 `text_type` 字段无法独立强制 L1（生产形态 refs 下注疏会被判 verified/verifiable=true）。保持 OPEN（详见 §6）。

### 2.2 `899519b`（supporting 提交）

涉及文件仅：`deliverables/kb-v1/fix-001/current/*`（baseline/failure-analysis）+ `eval/scripts/fix001_analysis.py`。

**独立判定**：纯分析工具与交付物修复；**无 production 改动**，未触碰 frozen metric / dataset / TARGETS / contract / Chroma。冻结 pre-fix 基线固定于 `d7ef182` 未被覆盖。

**未发现**：dataset gaming、metric gaming、target manipulation、denominator shrinking、断言弱化。

---

## 3. 独立复现 GATE-D（quote_exactness）

**必须调用 canonical frozen 实现**：本次直接读取冻结公式源码 `eval/scripts/metrics.py:81-106` 并核对 `eval/eval-run.json` 实际输出；t2 通道另以真实 `verify_quote` 端到端复现，两条独立路径结论一致。

| 项 | 值 |
|---|---|
| numerator | **18** |
| denominator | **18**（**未缩小**；冻结公式分母 = 系统判 exists 的预测条数，qv-0019/20/21 因 `expected.quote_exists=false` 且系统判 false 而被排除，属公式定义口径，非规避） |
| score | **18/18 = 1.0000** |
| target | 0.99 |
| verdict | **PASS** |
| 证据文件 | `eval/eval-run.json` → `.results.quote_exactness {numerator:18, denominator:18, value:1.0, target:0.99, passed:true, failures:[]}` |

---

## 4. 全部 Frozen Metrics（D/H/I/J 核验；E/F/G 允许 FAIL）

| Gate | 指标 | numerator/denominator | value | target | verdict |
|---|---|---|---|---|---|
| D | quote_exactness | 18/18 | **1.000** | ≥0.99 | **PASS** |
| H | source_attribution | 18/18 | **1.000** | ≥0.98 | **PASS** |
| I | fabricated_classical_quote | 0 | **0** | =0（绝对计数） | **PASS** |
| J | school_leakage | 0/19 | **0.000** | <0.01 | **PASS** |
| E | unsupported_correct_refusal | 0/12 | 0.000 | ≥0.95 | FAIL（允许） |
| F | Recall@5 | n/a | 0.325 | ≥0.90 | FAIL（允许） |
| G | core_claim_evidence_coverage | 30/40 | 0.750 | ≥0.95 | FAIL（允许） |

**H/I/J 无回退**：与 handoff/历史快照一致，FIX-001 未造成 H/I/J 回归。

**非冻结诊断（如实披露）**：`fabricated_classical_quote` 附带诊断 `fragment_displayed_as_classic=1`（aq-0011，`trust_state=verified, match_type=normalized`）—— 属 RFC-2 完整性门误判范畴，**不是**冻结指标失败。

---

## 5. Contract Probes（16+2 组）

t2 在隔离 Chroma 上运行全部探针，皆符合 CONTRACT-001 v2（§5 用例表）：

| # | case | quote_exists | exact_match | source_correct | trust_state | is_displayable_as_classic |
|---|---|---|---|---|---|---|
| 1 | `""`（empty） | F | F | F | insufficient_evidence | F |
| 2 | whitespace | F | F | F | insufficient_evidence | F |
| 3 | punctuation-only | F | F | F | insufficient_evidence | F |
| 4 | 君子（<门槛 4 字） | F | F | F | insufficient_evidence | F |
| 5 | **勿施于人** | **T** | **T** | T | **quote_relaxed** | **F**（完整性门 4<6） |
| 6 | 己所不欲，勿施于人。 | T | T | T | verified | T |
| 7 | 繁体 於 变体 | T | T | T | verified | T |
| 8 | full real quote + correct source | T | T | T | verified | T |
| 9 | full real quote + wrong source | T | T | F | citation_corrected（给出 correct_source《论语·卫灵公》） | F |
| 10 | commentary verbatim | T（存在） | T | – | quote_relaxed / citation_corrected | **F（不可升级 verified）** |
| 11 | cross-sentence fused quote | T | **F**（跨句拦截） | – | quote_relaxed | F |
| 12 | real prefix + fabricated suffix | F（单向包含失败） | F | F | insufficient_evidence | F |
| 13 | fake internet Confucius quote | F | F | F | insufficient_evidence | F |
| 14/15/16 | partial prefix / middle / suffix | T | T（子串） | T | quote_relaxed（过 gate 且 L1 则 verified，视长度） | 按 gate/L1 |

**重点验证（勿施于人）**：`quote_exists=true`、`exact_match=true`，但因 `len(N)=4 < MIN_FULL_QUOTE_CHARS=6` **unable 通过完整性门** → `trust_state=quote_relaxed`、`is_displayable_as_classic=false` —— 与合同 §5 行 3 **完全一致**。

---

## 6. 跨句安全 / Commentary / L1

### 6.1 跨句安全（§3.3 RC5）

`_strip_punctuation` 会删除 `。！？「」`，但新实现 `crosses_sentence_boundary()`（quote_verifier.py:398-428）在归一化前按句界切分原文，拦截跨句拼接：

- `不亦说乎有朋自远方来` → exact_match=F / quote_relaxed
- `有一言而可以终身行之者乎子曰其恕乎`（子贡问句+孔子答句粘合）→ exact_match=F / quote_relaxed

**PASS**：punctuation normalization 无法把两个不同句子的边界删除并制造 synthetic exact quote。例外（原始引文自身含句界标点）按合同 §3.3 允许，属引用者明确引用跨句原文。

### 6.2 Commentary / L1

- **verify_quote 路径**：注疏（朱熹《论语集注》）逐字文本经 `verify_quote` **不能**升级为 `verified`（RC4：`is_l1 = text_type=="original"` 参与 rule 3 → 注疏为 quote_relaxed，不可展示）。**已修复 ✅**
- **已知限制（保持 OPEN，不假装解决）**：`citation_guard` 因 `RAGReference` 缺少 `text_type` 字段（`schemas/ai.py`），在**生产形态 refs**（无 text_type 传播）下 `guard_citations` 对注疏原文会判 `verified / verifiable=true` —— **完整 L1 enforcement 无法在 citation_guard 独立执行**。该限制已在合同 §3.2 / RC4 与 QA-FINDINGS-PHASE-5 中记载，本报告如实确认仍存在，**不构成 FIX-001 回退，保持 OPEN**（对应 T1-02）。

---

## 7. GATE-I Fidelity Warning（诚实披露测量基）

冻结 `fabricated_classical_quote = 0` 成立，但必须明确：

> **这是 frozen harness measurement，不是完整 production citation_guard fidelity proof。**

`run_eval.py` 的 `_quote_prediction` 合成 `pred.verifiable = quote_exists ∧ source_correct ∧ match_type≠partial`（harness-synthesized），**非**严格 production `citation_guard` verdict。因此冻结 I=0 证明 harness 口径下无伪造通过，**不**证明生产 citation_guard 端到端行为（尤其 §6.2 的 L1 缺口）。**EVAL-FIDELITY-001 保持 OPEN**，不得过度声明。

---

## 8. 回归结果（Backend / Frontend）

### 8.1 Backend（t3 独立执行，隔离）

- 命令：`python -m pytest tests -q`（backend venv，conftest 强制 per-PID 隔离 Chroma）
- 结果：**470 passed + 1 failed**，243 subtests，3 warnings，86.14s
- 唯一失败：`test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai`（assert `settings.LLM_PROVIDER=="openai"` 实际为 "agnes"）
- **LLM_PROVIDER=agnes 定性 = A（pre-existing / environment-dependent / unrelated to FIX-001）**：
  1. `backend/.env` 为 gitignored + untracked，设置 `LLM_PROVIDER=agnes`；
  2. 决定性对照：同一测试从仓库**根目录**运行（不加载 backend/.env）→ **1 passed**（默认 openai）；从 **backend** 运行（加载 .env, agnes）→ failed；纯由本地环境变量引起；
  3. FIX-001 两提交未触碰 `config.py` / `test_ai_provider.py` / `llm_client.py`（`config.py` 最后修改 `64c8618` 早于 FIX-001）。
- **准确表述**：`470 PASS + 1 independently confirmed pre-existing environment failure`，**不是** `all backend tests passed`。

### 8.2 Frontend（t3 独立执行）

- typecheck：`npx tsc --noEmit` → **PASS**（exit 0）
- tests：`npm test` → 22 个 `.cjs` harness 全过 + vitest **23 files / 41 tests 全过**（exit 0）；`runtimeAssets` 因无 :3000 reachable 前端被 SKIP（环境依赖 skip，非失败）
- **未发明命令**：typecheck/test 均来自 package.json / CI 真实配置。

### 8.3 Lint 附加记录（如实）

CI 配置文件（`.github/workflows/ci.yml` + `linters.yml`）存在独立 lint 门禁：ESLint `--max-warnings 0` 实测 **1 error + 7 warnings**，全部位于 FIX-001 未触碰的 frontend 文件（如 `app/error.tsx`，最后提交 `a275867` 早于 FIX-001）→ **pre-existing lint 欠账，与 FIX-001 无关**；backend `ruff` 未在 venv 安装（CI-only），本地无法复现（环境限制）。handoff 声明仅含 typecheck + 41 tests，与此二项一致。

---

## 9. Production Chroma Integrity

- 指纹工具：`backend/tests/_chroma_fingerprint.py`（纯读文件指纹；内容指纹只在隔离临时副本上打开）。
- **内容未变（FIX-001 未改生产）**：
  - `doc_count = 143`，`id_md5 = 58795f71e427304cbe02a3e85f49498d` —— 与 t17 破坏前快照及 captain backup **完全一致**；
  - `data_level0.bin`（167,600B）等 5 个 HNSW/index 文件 SHA256 与接力快照**逐字节一致**；
  - 当前文件清单（6 文件）：`chroma.sqlite3` 4,120,576B；`data_level0.bin` 167,600B；`header.bin` 100B；`index_metadata.pickle` 124B；`length.bin` 400B；`link_lists.bin` 0B。
- **唯一差异（如实记录，非内容变更）**：`chroma.sqlite3` SHA256 由快照 `d5184ba4f9f77729…` 变为 `0ed9f2bdd1e7d325…`（mtime 13:08:30）。判读：与前一轮 QA reviewer 的 `backup/_qa_review_tmp/l1_gap_probe.py`（未设 `CHROMA_PERSIST_DIR`，import 时打开生产 PersistentClient）运行时刻吻合；属 chromadb 打开即写 catalog 元数据的**已知行为**（`_chroma_fingerprint.py` docstring 与 QA-FINDINGS-PHASE-5 §安全声明均记载）。**内容与全部 HNSW 段未变**，非 FIX-001 造成（FIX-001 提交未触及 chroma；eval-run.json 为 used_production=false/隔离目录）。
  - **纪律观察**：前一轮 reviewer 的探针未隔离即打开生产库（未走隔离机制），本报告如实记录；本次审计全部探针走隔离环境，未创建生产客户端。
- **提交范围**：31afdc8 / 899519b 均未触碰 `backend/chroma_db`。

---

## 10. 验收标准逐条核对（TERMINAL PASS 要求）

| # | 标准 | 结果 | 证据 |
|---|---|---|---|
| 1 | canonical Gate-D = 18/18 = 1.000 | ✅ | 冻结公式直接复算 + eval-run.json：18/18=1.0 |
| 2 | denominator 未变（=18） | ✅ | `metrics.py:81-106` 未变；denom=18 |
| 3 | implementation matches contract | ✅ | §2.2/§3.2/§3.3/§4 逐项一致（本章 §2.1、§5） |
| 4 | contract probes pass | ✅ | 16+2 探针全部符合合同（§5） |
| 5 | no target manipulation | ✅ | TARGETS 未变（t4 指纹 + git） |
| 6 | no dataset gaming | ✅ | 7 JSONL 逐字节未变（t4 8/8 指纹） |
| 7 | no metric gaming | ✅ | metrics.py 未变 |
| 8 | H/I/J no regression | ✅ | H=1.000, I=0, J=0.000（§4） |
| 9 | production Chroma unchanged | ✅ | 内容 143/id_md5 + HNSW 段逐字节一致（§9） |
| 10 | backend env failure 确认 unrelated | ✅ | classification A，对照实验（§8.1） |
| 11 | known RFCs/limitations 诚实保留 | ✅ | RFC-1/2/3、EVAL-FIDELITY-001、L1 缺口、T1-01/02 全部 OPEN（§11） |

---

## 11. Known Limitations / RFCs（全部保持 OPEN，未被 FIX-001 修改）

- **RFC-1**：`qv-0016/0017/0018` 的 `expected.exact_match=false` 与冻结 `quote_exactness` 分子互相不可满足；`expected.exact_match` 无消费者。1.000 是冻结公式口径，**不是**标签一致性证明。
- **RFC-2**：短完整经典句的 completeness 规则（`君子不器`/`三十而立`/`过则勿惮改` 等 4–5 字真实完整句被完整性门误判；aq-0011 诊断亦属此范畴）。
- **RFC-3**：重复且不一致的 `_T2S` 表（backend `normalize_text` vs `metrics.py:52-61`），已造成真实假阴性（如 `溫`/`則` 未映射、`aq-0009` 繁体 `萬`/`爭` miss）。
- **EVAL-FIDELITY-001**：GATE-I 消费 harness-synthesized `verifiable`，非严格 production citation_guard verdict；冻结 I=0 不构成完整 citation_guard fidelity proof。
- **citation_guard / RAGReference 缺 text_type**：完整 L1 enforcement 无法在 citation_guard 独立执行（T1-02）。
- **T1-01**：`is_verifiable` / `explain` 未按合同 §2.4 / §4.1 收紧。
- **future corpus expansion / fabricated metric semantic issue**：已登记（failure-analysis.md:33-36），保持 OPEN。
- **Q3 / Q5**（语料授权 / 真实 LLM 凭证）等既有阻塞不变。

---

## 12. 结论与后续

- **Verdict**：**TERMINAL PASS**
- **FIX-002 是否可开始**：**是**。FIX-001 独立验收已通过；按接力顺序（FIX-001 独立验收 → FIX-002 拒答 → EVAL-FIDELITY-001 → FIX-003 Recall@5 → FIX-004 核心观点证据覆盖），**FIX-002（unsupported_correct_refusal，当前 0.000）可以启动**。本审计不实施 FIX-002。
- 本报告仅写入 `docs/kb-v1/FIX-001-FINAL-REVIEW.md` 一个文件；未修改任何 production 文件、冻结资产或 git 索引。