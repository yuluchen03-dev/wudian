# DSH-Q35 — Q3 语料溯源 与 Q5 真实 Provider E2E 状态再核验

- **任务**：t10（DSH-Q35）
- **执行者**：evaluation
- **attempt_id**：`b0bb671a-7239-4dd0-b290-48dfeb75e466`
- **日期**：2026-10-11
- **仓库**：`D:\systemDir\Desktop\悟典`，branch `codex/overall-optimization`，HEAD `34afd1d`
- **性质**：**READ-ONLY 再核验**。未修改任何产品代码、测试、语料、配置或 Git 索引。
- **本任务不解决任何 blocker**。目标是把两个外部阻塞项的真实状态**如实固定**下来，禁止用猜测消解。

---

## 0. FINAL VERDICT

```
Q3_CORPUS_PROVENANCE = BLOCKED_EXTERNAL_EVIDENCE   （未解除）
Q5_REAL_PROVIDER_E2E = FAIL / UNRESOLVED           （未解除）
```

**两项均维持原判，本轮未取得任何可关闭它们的新证据。**

本报告**不**声称 Q3 或 Q5 已 PASS。**若任何下游文档、提交信息或 FINAL-ACCEPTANCE 因本报告而把 Q3/Q5 记为已解决，即为伪造 PASS。**

### 0.1 本轮的方法学约束（自我约束，逐条可核）

| 禁止事项 | 本轮是否违反 |
|---|---|
| 猜测出版年 | **否**（全文无任何推定年份；`classics_catalog.json` 的 `dynasty` 为仓库既有值，非本轮补写） |
| 猜测馆藏机构 | **否**（全文无任何馆藏推断） |
| 猜测底本/版本 | **否**（全文一律 `unknown`） |
| 编造 provenance | **否**（未向任何语料文件写入任何字段） |
| 用 DSH 模型调用冒充应用 Q5 通过 | **否**（§2.4 明确否认二者可互相替代） |
| 打印/落盘密钥值 | **否**（仅记录 `present_boolean`；见 §2.2） |
| 打开生产 Chroma | **否**（仅文件级指纹读取，见 §0.2） |

### 0.2 隔离与生产数据安全（实测）

| 项 | 值 |
|---|---|
| 生产 Chroma 指纹（读取前） | `backend/chroma_db` 6 files / 4,288,800 bytes |
| 生产 Chroma 指纹（读取后） | 6 files / 4,288,800 bytes —— **未变** |
| 是否创建生产 Chroma 客户端 | **否** |
| 是否执行 `build_index(force=True)` | **否** |
| 本轮是否发起网络调用 | **否** |
| `data/**` 与 `backend/data/**` 是否有本轮改动 | **否**（见 §0.3） |

### 0.3 本轮实际写入的文件（scope 合规声明）

| 文件 | 性质 |
|---|---|
| `deliverables/kb-v1/dsh-q3-q5-revalidation.md` | 本报告（任务 in-scope 交付物） |
| `deliverables/kb-v1/_q35_probe.py` | 只读探针脚本（证据可复现，不写入仓库任何数据） |
| `deliverables/kb-v1/_q35_probe_out.txt` | 探针原始输出（证据留存） |

`git status` 显示被修改的产品文件（`ai_service.py`、`quote_verifier.py`、`rag_service.py`、`run_eval.py` 等）**均为本任务开始前已存在的他人未提交改动**，不是本轮产生。本轮未 commit、未 push。

---

## 1. Q3 — 语料溯源 / 授权：逐事实表

### 1.1 范围界定

任务要求盘点「`data/processed/*.json`、`backend/data/commentaries/*.json`、quote_verifier 使用的 corpus 条目」。实测：

| 语料文件 | 规模 | 是否进入 RAG/校验链 |
|---|---|---|
| `data/processed/lunyu.json` | 107 章 | **是**（`rag_service.py:355` 加载） |
| `data/processed/debate_classics.json` | 9 学派 / 21 条 | **是**（`rag_service.py:432` 加载） |
| `backend/data/commentaries/lunyu_zhuxi.json` | 15 条注疏 | **是**（`rag_service.py:402`、`:805` 加载） |
| `data/processed/lunyu_quotes.json` | 36 条 | 间接（名句层） |
| `data/processed/quote_cards.json` | 22 条 | 间接（卡片层） |
| `data/processed/idioms.json` | 39 条（`meta.total` 写 35，**内部不一致**） | 间接 |
| `data/processed/knowledge_graph.json` | 21 节点 | 否（图谱） |
| `data/processed/timeline.json` | 30 事件 | 否 |
| `data/processed/classics_catalog.json` | 123 部书目 | 目录层 |
| `data/processed/comics.json` / `theater_scripts.json` | 1 / 6 | 否（衍生内容） |
| `data/processed/modern_issue_ontology.json` | — | 现代议题本体 |
| `data/sources/source_registry.json` | 3 来源 / 4 待核 | **新建的注册表，本身不是语料** |

### 1.2 机械扫描结果：provenance 字段存在性（原始计数）

对每个文件按 JSON **键名**精确匹配统计出现次数（探针 §A1）：

| 文件 | `source_provider` | `source_url` | `source_edition` | `license` | `verification_level` | `proofread_status` | `edition` | `publisher` | `publication_year` | `holding` |
|---|---|---|---|---|---|---|---|---|---|---|
| `classics_catalog.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `comics.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `debate_classics.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `idioms.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `knowledge_graph.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `lunyu.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `lunyu_quotes.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `modern_issue_ontology.json` | 0 | 0 | 0 | **1** | **1** | 0 | 0 | 0 | 0 | 0 |
| `quote_cards.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `theater_scripts.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `timeline.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **`lunyu_zhuxi.json`** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** |
| `source_registry.json` | 0 | 0 | 0 | 3 | 0 | 0 | 3 | 0 | 0 | 0 |

`modern_issue_ontology.json` 的 `license` / `verification_level` 是**现代议题本体自身的 schema 字段**，与古籍语料溯源无关，不构成任何古籍的授权证据。

**核心事实：`lunyu_zhuxi.json` 的 10 个溯源字段计数全为 0，`edition` / `license` / `publisher` 三个键在文件中根本不存在（探针实测 `has structured 'edition' field: False`，`'license': False`，`'publisher': False`）。**

### 1.3 逐来源事实表（只统计「仅凭仓库内容即可核验」的部分）

图例：`✅ 可核验` = 仓库内容直接支持；`❌ 缺失` = 仓库无此字段；`🔒 BLOCKED` = 需外部权威证据。

#### 来源 A：`lunyu.json`（论语正文 107 章，RAG 主输入）

| 事实 | 仓库内是否存在并可否核验 | 值 |
|---|---|---|
| 出版年 | ❌ 缺失 / 🔒 BLOCKED | 无任何年份字段 |
| 馆藏机构 | ❌ 缺失 / 🔒 BLOCKED | 无 `holding` / `institution` 字段 |
| 授权 / license | ❌ 缺失 / 🔒 BLOCKED | 无字段；无任何散文授权陈述 |
| 底本/版本溯源 | ❌ 缺失 / 🔒 BLOCKED | 无 `source_edition`；`data/raw/` 为空，无底本留档 |
| 作者归属 | ⚠️ **部分** | 顶层 `author` = 「孔子弟子及再传弟子」（**传统归属，非版本责任者**） |
| 数据提供方 | ❌ 缺失 / 🔒 BLOCKED | 探针实测：107 条 verse 的 item keys 为 `['annotations','keywords','original','title','translation','verse_id']`，**根本不存在 `source` 键**（`distinct source = 1`，即全部为 `None`） |

#### 来源 B：`debate_classics.json`（9 学派 / 21 条摘句）

| 事实 | 仓库内是否存在并可否核验 | 值 |
|---|---|---|
| 出版年 | ❌ 缺失 / 🔒 BLOCKED | 无 |
| 馆藏机构 | ❌ 缺失 / 🔒 BLOCKED | 无 |
| 授权 / license | ❌ 缺失 / 🔒 BLOCKED | 无 |
| 底本/版本溯源 | ❌ 缺失 / 🔒 BLOCKED | 无 |
| 作者归属 | ⚠️ **部分** | 顶层 `book` 字段给出书名（9 部），条目级 `source` 只写篇名如 `《论语·泰伯》` |
| **关键警示** | — | 该文件的 `source` **是引用标签（书名·篇名），不是数据提供方**（与既有审计 §3.4 结论一致） |

#### 来源 C：`backend/data/commentaries/lunyu_zhuxi.json`（朱熹《论语集注》15 条）—— **本任务重点**

| 事实 | 仓库内是否存在并可否核验 | 值 / 证据 |
|---|---|---|
| 出版年 | ❌ **缺失 / 🔒 BLOCKED** | 无 `publication_year`；`description` 仅称「元明清科举定本」——**这是刊刻时代范围，不是出版年** |
| 馆藏机构 | ❌ **缺失 / 🔒 BLOCKED** | 无任何馆藏/藏书机构字段 |
| 授权 / license | ❌ **缺失 / 🔒 BLOCKED** | **无结构化 license 字段**（探针实测 `False`）。唯一相关文字是 `description` 中的散文：「公版已过版权期」。**该散文不是可核验授权**：未记录所据底本、点校者、出版信息；现代点校本的标点/校勘可能另有版权。 |
| 底本/版本溯源 | ❌ **缺失 / 🔒 BLOCKED** | 无 `source_edition`；无出版者、无点校者、无版本谱系 |
| 作者归属 | ✅ **可核验（有限）** | 结构化字段 `author` = 「朱熹」；`dynasty` = 「南宋」；条目级 `source` = 「朱熹《论语集注》」（15 条全部一致）。朱熹为南宋人，属传统公有领域作者。**但「作者归属可核验」≠「所用文本的底本可核验」**——后者为 BLOCKED。 |

#### 来源 D：`classics_catalog.json`（123 部书目目录层）

| 事实 | 仓库内是否存在并可否核验 | 值 |
|---|---|---|
| 目录层引用 3 个外部站点 | ✅ **可核验（存在性）** | `sources[]` 各含 `name` / `url` / `note`：ctext.org 两条 + 维基文库一条 |
| 上述 URL 是否为正文来源 | ❌ **否** | **仅是「书目编目参考」。** 探针实测：123 部书中带 `source_url`/`source_edition`/`license` 的为 **0 部**（`books carrying any of ... : 0`）。既有审计已证实 `build_lunyu.py` 无任何网络导入，正文非抓取所得。 |
| 出版年 / 馆藏 / 授权 | ❌ 缺失 / 🔒 BLOCKED | 全局无这些字段 |
| 作者归属 | ⚠️ **部分** | 每部书有 `author` / `dynasty` 散文，属传统归属信息 |
| 授权核验可行性 | 🔒 **BLOCKED** | 既有审计记录：PHASE 0 期间对 `ctext.org`、`zh.wikisource.org` 的网络访问**被拒**（hostname resolves to a non-public IP address） |

#### 来源 E：`source_registry.json`（PHASE 1/P1-02 新建注册表）

**这是仓库内唯一带溯源结构的地方，但它的内容恰恰是对「无溯源」的登记：**

| 事实 | 实测值 |
|---|---|
| `registry_status` | `initialized_without_verified_sources` |
| `verified_at` | `null`（全局） |
| `src_unknown` | provider/edition/license **全部 `unknown`**；`authorization_status=unverified`；`verified_at=null` |
| `src_ctext_catalog_reference` | provider = 中国哲学书电子化计划；edition `unknown`；license `unknown`；`unverified` |
| `src_wikisource_catalog_reference` | provider = 维基文库；edition `unknown`；license `unknown`；`unverified` |
| `pending_verification` | **4 条，全部 `status = unverified`** |

4 条待核项原文（如实转录）：

1. 朱熹《论语集注》所据底本与点校版权 — `unverified`
2. 「言必信，行必果」的归属（仓库内自相矛盾：`idioms.json` 归《论语·子路》13.20；`debate_classics.json[mozi]` 归《墨子·兼爱下》）— `unverified`
3. `lunyu.json` 4.5 是否应作「不以其道去之」— `unverified`
4. 韩非子「赏罚者，邦之利器也」的篇目出处 — `unverified`

**注册表自证的 `provenance_policy` 明确禁止编造：**「严禁编造 provider / url / edition / license。真实未知一律写哨兵字符串 `unknown`」。本报告严格遵从。

### 1.4 Q3 缺失事实清单（需权威外部证据方能补全）

以下事实在仓库中**完全不可导出**，必须由人工携带外部权威证据补入。**本报告拒绝为其中任何一项填入示意值。**

| # | 缺失事实 | 适用来源 | 为何无法从仓库导出 | 所需权威证据 |
|---|---|---|---|---|
| M1 | **正文所据底本/版本** | A, B, D | 无 `source_edition`；`data/raw/` 为空，无底本留档；生成器为内置字面量脚本 | 具体版本的书名页/版权页（出版社、版次、年份、ISBN），或数字化库的稳定条目页 |
| M2 | **授权状态与 license 文本** | 全部 A–D | 无结构化 `license` 字段；仅 1 处散文声明 | 权利方的书面授权，或来源站点的授权声明页（须含许可类型与适用范围） |
| M3 | **出版年** | 全部 | 无 `publication_year` 字段；「元明清科举定本」是刊刻时代范围，不是出版年 | 版权页 / 版本著录 |
| M4 | **馆藏机构** | 全部 | 无 `holding` / `institution` 字段 | 馆藏著录记录或书影题跋 |
| M5 | **朱熹注疏所用底本的点校者与点校版权** | C | 无点校者、无出版信息 | 点校本版权页 + 点校者身份（现代点校成果可能另有版权） |
| M6 | **正文是否曾由 LLM 生成或改写** | A, B | 无生成日志、无 raw 底本；`git log --diff-filter=A` 显示语料在 `a275867` 一次性引入 | 数据生产方的来源声明与生成流水；**仓库内既无法证实也无法证伪** |
| M7 | **`idioms.json`「言必信，行必果」归属** | 衍生 | 仓库内自相矛盾（论语 13.20 vs 墨子·兼爱下） | 权威原典库比对裁决 |
| M8 | **`lunyu.json` 4.5「不以其道得之/去之」** | A | 通行本多作「不以其道去之」，本机无法外部核验 | 权威校勘本 |
| M9 | **韩非子「邦之利器」篇目出处（二柄 vs 喻老）** | B | 本机无法外部核验 | 权威原典库比对 |
| M10 | **`idioms.json` 计数自相矛盾**（`meta.total=35` vs 实际 39 条） | 衍生 | 仓库内数据不一致 | 无需外部证据，但需人工确认哪一侧为准 |

> **注意 M6**：这是一条**方法学**而非著录层面的缺口。即便补全 M1–M5，若无法证明正文非 LLM 生成，则「原典不得来自 LLM 生成」这一 Gate 仍不可达。

### 1.5 Q3 具体用户动作（关闭该阻塞所需）

1. **指定并交付底本**：对 `lunyu.json` / `debate_classics.json` / `lunyu_zhuxi.json` 明确所据版本，提供书名页或版权页证据（→ 可关闭 M1、M3、M4）。
2. **交付授权文件**：与权利方确认授权，或改用已明确许可的来源（如 ctext.org / 维基文库的授权页，须先离线获取并归档）；将结论写入 `source_registry.json` 并附 `evidence_ref` + `verified_at`（→ 可关闭 M2、M5）。
3. **提供数据生产来源声明**（→ 缓解 M6；若无法提供，须在验收中永久标注「原典非 LLM 生成的不可证」）。
4. **完成 `pending_verification` 中 4 条人工复核**并留痕（→ 可关闭 M7、M8、M9）。
5. **PHASE 0 审计期间网络受限**（对 ctext.org / zh.wikisource.org 的访问被拒）。若要在本机自行核验，需先解除该网络限制；否则必须由人工在受限环境外取证。

**在上述证据到位前，Q3 状态恒为 `BLOCKED_EXTERNAL_EVIDENCE`，任何语料的 `verification_level` 不得高于 C。**

---

## 2. Q5 — 真实应用 Provider E2E：逐事实表

### 2.1 报告与代码现状（已读）

| 项 | 值 | 证据 |
|---|---|---|
| Q5 报告结论 | **`Q5_REAL_PROVIDER_E2E = FAIL`** | `docs/kb-v1/FIX-005-Q5-REAL-PROVIDER-E2E.md:13` |
| 独立 reviewer verdict | **FAIL（不批准 PASS）** | 同上 §13，reviewer attempt `0ac3c970` |
| 决定性反例 F-1 | 初稿的 `agnes-3.0-flash` 身份不成立 | 同上 §0.1 / §13 |
| 应用默认 model | `agnes-2.0-flash` | `backend/app/core/config.py:59` —— **本轮已独立读取确认** |
| 端点为该默认 model 的行为 | **503 `model_not_found`** | 报告 §0.1（历史实测） |
| 报告是否已被推翻/修订 | **否** | 报告头部仍为 FAIL |

**本轮独立复核 `config.py` 确认（不依赖报告转述）：**

- `config.py:56` `LLM_PROVIDER: str = "openai"`（默认 provider 是 openai，**不是 agnes**）
- `config.py:57` `AGNES_API_KEY: str = ""`（默认空）
- `config.py:58` `AGNES_BASE_URL: str = "https://apihub.agnes-ai.com/v1"`
- `config.py:59` `AGNES_MODEL: str = "agnes-2.0-flash"`
- `config.py:200-205` `llm_config`：provider=="agnes" 时取 `AGNES_API_KEY or OPENAI_API_KEY`、`AGNES_BASE_URL`、`AGNES_MODEL`

即：F-1 所指的「持久配置默认指向 `agnes-2.0-flash`，而该 model 在该端点 503」这一结构性不匹配，**在代码中依然存在，未被修正**。

### 2.2 凭证存在性（仅 BOOLEAN，绝无取值）

按任务要求，**只报告变量名的存在布尔值，不打印、不落盘、不回显任何值**。

| 变量名（应用链） | Process 作用域 | User 作用域（持久） | Machine 作用域 |
|---|---|---|---|
| `AGNES_API_KEY` | **False** | **True** | False |
| `AGNES_MODEL` | **False** | **False** | False |
| `AGNES_BASE_URL` | **False** | **False** | False |
| `LLM_PROVIDER` | **False** | **False** | False |
| `DEEPSEEK_API_KEY` | False | False | False |
| `OPENAI_API_KEY` | False | — | — |
| `QWEN_API_KEY` | False | — | — |

（`ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `MOONSHOT_API_KEY` / `ZHIPU_API_KEY` 的 Process 存在性亦均为 **False**；这些并非本应用 `config.py` 支持的 provider 变量。）

**结论（诚实表述）：**
- 应用链凭证 `AGNES_API_KEY`：**User 作用域存在 = True；当前 DSH 进程作用域 = False。**
- 这一不对称说明：**该凭证存在，但当前 DSH 进程环境未继承它。** 因此当前进程**不能**代表「应用在持久配置下的真实行为」。
- `backend/.env` **存在**（2232 字节，**未被 git 跟踪**，`git ls-files --error-unmatch backend/.env` 返回 pathspec 不匹配）。`config.py:11-13` 使用 `SettingsConfigDict(env_file=".env")` —— 即**应用从 `backend/.env` 加载配置**。
- **本轮未读取 `backend/.env` 的内容**（该文件可能含密钥；任务禁止读取/回显）。因此**无法也不应**据此判断 `.env` 内 `LLM_PROVIDER` / `AGNES_MODEL` 究竟为何值。

> **这是 Q5 的一个关键未验证点**：应用真实生效的 `LLM_PROVIDER` 与 `AGNES_MODEL` 取决于 `backend/.env`，而该值本轮**被有意未读取**。FIX-005 报告称干净进程按应用自身持久配置解析得 `agnes-2.0-flash`，但该结论**本轮未独立复现**（复现它需要读取 `.env` 或启动应用并打印解析后的非敏感配置，二者均超出本轮只读凭证约束）。**按诚实原则记为「未独立复现」，而非「已证实」。**

### 2.3 Q5 状态判定

| 判定项 | 结果 |
|---|---|
| Q5 是否随本任务被解决 | **否** |
| 当前状态 | **FAIL / UNRESOLVED** |
| 是否有新的真实应用链 E2E 通过证据 | **无**（本轮未发起任何 provider 调用） |
| 报告是否需改判 | **否**，维持 FAIL |
| 阻塞性质 | **外部输入缺失**（凭证是否生效 + 持久配置与端点是否匹配，需应用侧实跑） |

### 2.4 DSH 模型调用 ≠ 应用 Provider 链通过（严格分离，明确声明）

| 维度 | DSH 桌面 Harness 链 | 悟典应用链 |
|---|---|---|
| 配置载体 | DSH 自身的 provider 配置（`llm-pi-ai`，`apiKeyEnv=AGENS_API_KEY`） | `backend/.env` → `config.py` → `llm_config` → `LLMClient` |
| 代码路径 | DSH harness（`app.asar/dsh`） | `backend/app/services/llm_client.py` + `ai_service.py` |
| 本轮 Process 内 DSH 密钥类变量数 | **0**（探针 §B2 实测） | 受 `AGNES_API_KEY` 是否注入影响 |
| 变量拼写 | DSH 侧为 `AGENS_API_KEY`（gens） | 应用侧为 `AGNES_API_KEY`（gnes） |
| 拼写是否互通 | **否**（两套拼写互不通用；FIX-005 §1 已记录） |

**明确声明：**

> **本 agent（evaluation）运行在 DSH 之上，DSH 本身能够调用模型这一事实，与「悟典应用的 provider 链可用」没有任何逻辑蕴含关系。**
>
> 二者使用**不同的配置载体、不同的代码路径、不同拼写的密钥变量**。任何以「DSH 能调模型」为依据宣布 Q5 解除的推论，均为无效推论，必须拒绝。
>
> 这与 `AGENTS.md` 的要求一致：**「不要因 ZCode 能调用模型，就宣布应用 Q5 已解除。」**

### 2.5 Q5 具体用户动作（关闭该阻塞所需）

1. **修正持久配置**：将 `AGNES_MODEL` 在应用持久生效的配置（`backend/.env` 或用户级环境变量）中设为该端点**实际支持**的 model（报告建议 `agnes-3.0-flash`），**或**明确改按当前持久配置测试并据实重写结论。
2. **确认应用能加载凭证**：确保应用运行环境（而非 DSH 进程）可加载 `AGNES_API_KEY`，通过 `backend/.env` 或显式注入；并提供**非敏感**的配置解析证据（如 provider/model/endpoint host 与 `credential_present=true`，**不得回显密钥**）。
3. **在应用自身进程内实跑 E2E**：在应用真实启动路径下重跑 Phase A/B/C，产出新的调用计数与结果表。
4. **重新独立终审**：由未参与实施的 fresh-context reviewer 重新出具 verdict。

**在上述输入到位前，Q5 状态恒为 `FAIL / UNRESOLVED`。**

---

## 3. 汇总：状态与所需动作

| ID | 阻塞项 | 本轮状态 | 是否可本地解决 | 具体用户动作 |
|---|---|---|---|---|
| **Q3** | 语料授权与权威底本 | 🔒 **BLOCKED_EXTERNAL_EVIDENCE** | **否** | 提供底本版权页/书名页、授权文件、（如需）解除对 ctext.org / zh.wikisource.org 的网络限制；完成 4 条人工复核 |
| **Q5** | 真实 LLM 凭证与端到端验证 | ❌ **FAIL / UNRESOLVED** | **否**（需应用侧实跑与配置修正） | 修正 `AGNES_MODEL` 持久配置、确认应用可加载凭证、在应用进程内重跑 E2E、重新独立终审 |

### 3.1 未验证项声明（不得表述为已验证）

| 项 | 状态 | 说明 |
|---|---|---|
| Q3 任何语料的底本 / 授权 | **未验证** | 仓库无可导出证据（§1.4） |
| 「原典非 LLM 生成」 | **既无法证实也无法证伪** | 无 raw 底本、无生成日志（M6） |
| 应用实际生效的 `LLM_PROVIDER` / `AGNES_MODEL` | **未独立复现** | 取决于 `backend/.env`，本轮有意未读取（§2.2） |
| 应用链真实 E2E | **未运行** | 本轮 READ-ONLY，未发起 provider 调用 |
| DSH 模型可用性 → 应用链可用性 | **无效推论，已拒绝** | §2.4 |
| 生产 Chroma 完整性 | 文件字节未变（6 files / 4,288,800 B） | 指纹仅证字节未变，**不构成语义完整性证明** |

### 3.2 对下游的硬约束

1. **`FINAL-ACCEPTANCE.md` 不得把 Q3 或 Q5 记为 PASS。** 二者保持 BLOCKED/FAIL。
2. **不得在任何语料文件中补写未经验证的 provenance 值。** 若必须占位，只能用哨兵 `unknown`（`source_registry.json` 的 `provenance_policy` 已如此规定）。
3. **不得以本报告为由宣布项目 CLOSED。** `GATE-I`、`EVAL-FIDELITY-001`、`STREAMING-SEMANTICS-001`、RFC-1/2/3 仍独立 OPEN。
4. **Q3/Q5 未解除不影响可完成的本地软件工作继续进行**，但相关 Gate 的验收必须携带「外部证据缺失」的限定语。

---

## 附录 A：可复现命令

```powershell
# 探针（只读；输出 UTF-8 到文件以避免控制台编码损坏 CJK）
$py = "C:\Users\hacjr\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
$env:PYTHONIOENCODING='utf-8'
& $py "deliverables\kb-v1\_q35_probe.py" 2>&1 | Out-File -Encoding utf8 "deliverables\kb-v1\_q35_probe_out.txt"
Get-Content "deliverables\kb-v1\_q35_probe_out.txt" -Encoding utf8

# 凭证存在性（仅 BOOLEAN，不回显值）
foreach($n in @('AGNES_API_KEY','AGNES_MODEL','AGNES_BASE_URL','LLM_PROVIDER')){
  "{0}: Process={1} User={2} Machine={3}" -f $n,
    [bool][System.Environment]::GetEnvironmentVariable($n,'Process'),
    [bool][System.Environment]::GetEnvironmentVariable($n,'User'),
    [bool][System.Environment]::GetEnvironmentVariable($n,'Machine')
}

# 生产 Chroma 指纹（只读，不建客户端）
Get-ChildItem 'backend\chroma_db' -Recurse -File | Measure-Object -Property Length -Sum

# 语料溯源字段键名计数（示例）
Select-String -Path 'backend\data\commentaries\lunyu_zhuxi.json' -Pattern '"license"\s*:','"edition"\s*:'
```

## 附录 B：本轮读取的关键文件（全部只读）

| 文件 | 用途 |
|---|---|
| `docs/kb-v1/FIX-005-Q5-REAL-PROVIDER-E2E.md` | Q5 报告与 reviewer verdict |
| `backend/app/services/ai_service.py` | 应用 AI 路径（`chat_with_sage_stream_response` 等） |
| `backend/app/core/config.py` | provider 配置与 `llm_config` 解析 |
| `backend/app/services/rag_service.py` | 语料加载路径（`:355` `:402` `:432` `:805`） |
| `data/sources/source_registry.json` | 唯一带溯源结构的注册表 |
| `backend/data/commentaries/lunyu_zhuxi.json` | 朱熹注疏（15 条） |
| `data/processed/*.json`（11 个） | 语料盘点 |
| `docs/kb-v1/audit/classical-knowledge.md` | 既有 PHASE 0 溯源审计 |
| `docs/kb-v1/audit/classical_audit_4_provenance.py` | 既有生成器取证脚本 |

## 附录 C：本轮写入范围声明

- **修改的产品代码 / 测试 / 语料 / 配置 / Git 索引：无。**
- 新增文件仅限 `deliverables/kb-v1/` 下的本报告与只读探针。
- 未 commit、未 push、未 deploy、未执行生产迁移。
- 生产 Chroma 未被打开，字节未变。
- 全文未出现任何密钥值。
