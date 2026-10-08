# 00 — 当前真实状态（PHASE 0 / GATE-0）

- 仓库：`D:\systemDir\Desktop\悟典`
- 分支 / HEAD：`codex/overall-optimization` / `64c861828eb8f1ec8816eb8d95212f78cdc7faeb`
- 依据：`docs/kb-v1/PROJECT-BRIEF.md`（第六章 Passage Schema、第七/八/十/十一/十二/十三章、第十七章质量指标、第十八章性能）
- 审计性质：**只读**。未修改 `backend/`、`frontend/`、`data/`、`PROJECT-BRIEF.md`；未 commit / push / deploy。
- 边界取证（本文件写作时实测）：

```powershell
$ git rev-parse HEAD
64c861828eb8f1ec8816eb8d95212f78cdc7faeb
$ git status --short
?? docs/kb-v1/
$ git diff --stat
(空)
```

**本文档的证据来源**：`docs/kb-v1/audit/` 下 7 份专家审计报告 + 本文作者独立复核的关键行号。凡标注「未核验」者，均因外部核验通道不可用（见 §8）。

**GATE-0 五项覆盖确认**：§1 当前数据 · §2 RAG · §3 embedding · §4 citation · §5 tests。另附 §6 其他必录事实、§7 兼容性边界、§8 未核验项。

---

## 1. 当前数据（GATE-0 第①项）

### 1.1 L1 原典真实规模：128 条，覆盖 V1 目标书目 4 部

| 数据源 | 文件 | 条目数 | 说明 |
|---|---|---|---|
| 论语 | `data/processed/lunyu.json` | **107** | 20 章 / 107 章句（`total_chapters: 20`） |
| 百家论道 | `data/processed/debate_classics.json` | **21** | 9 个 sage_key，其中 confucius 3、laozi 4、mozi 4、hanfeizi 4、其余各 1–2 |
| **L1 原典合计** | | **128** | |

**「零重叠」的确切含义（必须精确理解）**：

```powershell
$ python -c "compare normalized originals of lunyu.json vs debate_classics.json"
lunyu: 107 unique debate: 21 union: 128
debate verses also in lunyu: 0
```

故 L1 原典 **128 条**（107 + 21），非 143。

> **重要限定（精确表述，可枚举）**：语料间**完全相等重复 0 条**；**部分包含恰好 1 对**（可枚举）：
>
> `debate_classics[confucius]`「士不可以不弘毅，任重而道远。」是 `lunyu.json` **8.7** 的**摘句**。
> 8.7 完整原文为「曾子曰：「士不可以不弘毅，任重而道远。仁以为己任，不亦重乎？死而后已，不亦远乎？」」——该摘句仅取前半句且去掉了「曾子曰：」。
>
> 复现命令（队长提供，本文作者独立复跑一致）：
>
> ```powershell
> $ python -c "import json,re;lu=json.load(open('data/processed/lunyu.json',encoding='utf-8'));dc=json.load(open('data/processed/debate_classics.json',encoding='utf-8'));n=lambda s:re.sub(r'[，。！？；：、（）\u3000\s「」『』]','',s);L=[(v['verse_id'],n(v.get('original',''))) for c in lu['chapters'] for v in c['verses'] if v.get('original')];D=[(k,n(x.get('original',''))) for k,v in dc['classics'].items() for x in v['verses'] if x.get('original')];print('exact',sum(1 for k,d in D for i,l in L if d==l));print('partial',[(k,i) for k,d in D for i,l in L if d and d!=l and (d in l or l in d)])"
> lunyu entries: 107 debate entries: 21
> exact 0
> partial count: 1
> partial [('confucius', '8.7')]
> ```
>
> **因此 PHASE 2 去重不能只做等值判断，但需处理的冲突范围很小且已完全枚举**（恰好 1 对）。
>
> **下游影响（供 PHASE 2 / PHASE 5 参考）**：若该摘句与 8.7 都作为独立 L1 passage 入库，**同一句会有两个 `passage_id`**，Quote Verifier 的 `quote_exists` 候选集将出现重复来源。`02-architecture.md` §9 的 `candidates[]` 契约需能表达「同一 passage 的全句与摘句」关系。

### 1.2 注疏（L2）：15 条，仅朱熹一家

| 项 | 值 | 证据 |
|---|---|---|
| 文件 | `backend/data/commentaries/lunyu_zhuxi.json`（8397 B） | `classical-knowledge.md:350` |
| 条数 | **15** | 同上 |
| 注疏者 | **仅 1 家：朱熹**（`source` 恒为 `朱熹《论语集注》`） | `classical-knowledge.md:352` |
| 覆盖率 | 15 / 107 = **14.0%** 的论语章节 | `classical-knowledge.md:354` |
| 条目级 `commentary_dynasty` | **无**（仅文件级 `dynasty: 南宋`） | `classical-knowledge.md:353` |
| 与原文分离存储 | 物理文件分离，但条目内嵌原文副本（13/15 逐字相同，2 条为子串） | `classical-knowledge.md:355` |

### 1.3 向量索引：`wudian_verses` = 143 条

```powershell
$ python docs/kb-v1/audit/_rag_probe_chroma.py
collections rows:
   ('c523cef2-acab-4181-adfa-d39c33059531', 'wudian_verses', 384)
row counts:
   embeddings 143
```

组成校验：`107 论语 + 15 注疏 + 21 百家论道 = 143`（`rag.md:263-265`，本文作者亦独立复核一致）。

索引内语料分布（`rag.md:295-305`）：论语 125、道德经 4、墨子 4、韩非子 4、李白诗文 2、苏轼词文 1、范仲淹文 1、王安石诗文 1、诸葛亮文 1。

> **注意**：`debate_classics.json` 混入李白/苏轼/范仲淹/王安石/诸葛亮等文学史传人物，**不属中国思想学派语料**，且**无 `school` 字段**，会在学派维度污染 metadata filter（`classical-knowledge.md:495`）。

### 1.4 V1 目标书目覆盖：12 部中 **4 部**有数据、**8 部**零语料

```powershell
$ python docs/kb-v1/audit/classical_audit_2_scale.py
=== D. V1 target booklist coverage ===
  论语       catalog=yes   corpus_passages=110
  孟子       catalog=yes   corpus_passages=0
  荀子       catalog=yes   corpus_passages=0
  大学       catalog=yes   corpus_passages=0
  中庸       catalog=yes   corpus_passages=0
  道德经      catalog=yes   corpus_passages=4
  庄子       catalog=yes   corpus_passages=0
  墨子       catalog=yes   corpus_passages=4
  韩非子      catalog=yes   corpus_passages=4
  商君书      catalog=yes   corpus_passages=0
  传习录      catalog=yes   corpus_passages=0
  孙子兵法     catalog=yes   corpus_passages=0
```

| 书目 | 学派 | 实际语料 | 缺口 | 严重度 |
|---|---|---|---|---|
| 《论语》 | 儒家 | 107 章 | 完整本应 512 章 → 缺 ~79% | 高 |
| 《孟子》 | 儒家 | **0** | 全缺 | **blocker** |
| 《荀子》 | 儒家 | **0** | 全缺 | **blocker** |
| 《大学》 | 儒家 | **0** | 全缺 | **blocker** |
| 《中庸》 | 儒家 | **0** | 全缺 | **blocker** |
| 《道德经》 | 道家 | 4 条摘句 | 完整 81 章 → 缺 ~95% | **blocker** |
| 《庄子》 | 道家 | **0** | 全缺 | **blocker** |
| 《墨子》 | 墨家 | 4 条摘句 | 完整 53 篇 → 缺 ~92% | **blocker** |
| 《韩非子》 | 法家 | 4 条摘句 | 完整 55 篇 → 缺 ~93% | **blocker** |
| 《商君书》 | 法家 | **0** | 全缺 | **blocker** |
| 《传习录》 | 心学 | **0** | 全缺 | **blocker** |
| 《孙子兵法》 | 兵家（可选） | **0** | 全缺 | 高 |

（来源：`classical-knowledge.md:459-489`）

**计数汇总（可复现）**：

```powershell
$ python -c "count corpus passages per V1 target book"
per-book counts: {'论语': 110, '孟子': 0, '荀子': 0, '大学': 0, '中庸': 0, '道德经': 4, '庄子': 0, '墨子': 4, '韩非子': 4, '商君书': 0, '传习录': 0, '孙子兵法': 0}
books WITH data: 4 ['论语', '道德经', '墨子', '韩非子']
books ZERO      : 8 ['孟子', '荀子', '大学', '中庸', '庄子', '商君书', '传习录', '孙子兵法']
```

> **12 部 V1 目标书目中，4 部有数据（论语 / 道德经 / 墨子 / 韩非子），8 部零语料（孟子 / 荀子 / 大学 / 中庸 / 庄子 / 商君书 / 传习录 / 孙子兵法）。**
>
> 注：上方计数汇总中「论语 110」= `lunyu.json` 107 条 + `debate_classics[confucius]` 3 条（**按书目归并口径**）；而覆盖表的「论语 107 章」只计 `lunyu.json`。L1 去重后的**唯一原典数仍为 128 条**（§1.1）。三个数字口径不同，不可混用：
>
> | 数字 | 口径 |
> |---|---|
> | **107** | `lunyu.json` 单文件条数 |
> | **110** | 按 V1 书目归并（论语 107 + debate_classics[confucius] 3） |
> | **128** | L1 去重后的唯一 passage 数（lunyu 107 + debate_classics 21） |

### 1.5 `classics_catalog.json` 的关键澄清：纯书目元数据，**不是语料**

- 123 部书，字段为 `id/title/category/author/dynasty/description/coverColor/totalChapters`。
- **无任何内联正文**（无 `verses` / `chapters` / `passages` / `content` 字段）；实测 `books with inline passage content = 0`（`evaluation.md:363-366`）。
- **`totalChapters` 是"该书应有章数"的声明，不是"已收录章数"**。例如论语 `totalChapters: 20`、孟子 14、庄子 33、墨子 53 —— 这些数字与实际语料 0 条并存，**极易被误读为"已有数据"**（`classical-knowledge.md:500`）。
- 该文件仅 3 个 URL 且**只挂在目录层**，123 部书**没有任何一部**带 `source_url` / `source_edition` / `license`（`classical-knowledge.md:21`）。

**结论：任何覆盖率统计都必须把 `classics_catalog.json` 与 L1 语料严格区分，不得据此宣称"已覆盖 V1 书目"。**

### 1.6 Passage Schema：29 字段仅 6 个存在

PROJECT-BRIEF 第六章 Passage Schema 的 29 个字段中，**只有 6 个以结构化形式存在**：`chapter_id`、`chapter_title`、`original`、`author`、`dynasty`、`created_at`/`updated_at`。

**其余 23 个缺失**，包括：全部来源字段、全部授权字段、全部复核字段、全部分层字段（`text_type`）（`classical-knowledge.md:20`）。

### 1.7 可追溯性：**无任何 passage 可追溯底本**

- 语料里出现的 `source` 是**引用标签**（如 `《论语·泰伯》`），**不是数据提供方**（`classical-knowledge.md:21`）。
- **全仓库零命中** `source_provider` / `source_url` / `source_edition` / `license` / `verification_level` / `proofread_status`（本文作者独立复核：`backend/` 全目录 grep 上述 6 个标识符 → `No matches found`）。
- `data/raw/` **完全为空**，`git ls-files data/raw` = 0 → **没有任何原始底本留档**（`classical-knowledge.md:69`）。
- 语料生成器 `data/scripts/build_lunyu.py` 是**纯内置字典脚本，无任何网络导入**，输出与磁盘 JSON 逐字节一致 → 说明语料是**人工/LLM 辅助编写后固化的静态数据**，而非从权威库抓取（`classical-knowledge.md:24`）。

### 1.8 数据质量等级：只能 C/D 级，**禁止标 A**

对 5 个语料文件全文检索 `校对`/`复核`/`人工`/`审定`/`proofread`/`verified`/`reviewed` → **零命中**。**没有任何人工复核或校对记录**，故当前全部语料**只能定为 C 级或 D 级，不能定为 A 级**（`classical-knowledge.md:22`）。

这与 PROJECT-BRIEF 第十四章「A = 权威文本 + 人工确认」直接冲突：**当前不存在任何 A 级数据**。

### 1.9 已发现的数据完整性缺陷

1 处原文缺陷、1 处内部出处冲突、2 处引文悬空引用、16 条典故悬空引用、9 条 `quote_cards` 无法在语料中逐字定位（`classical-knowledge.md:23`）。
另：`idioms.json` 的 `meta.total` 写 35，实际 39，**自相矛盾**（`classical-knowledge.md:65`）。

#### 1.9.1 占位符 `verse_id`（F-03，PHASE 2 迁移前必须显式处理）

`data/processed/lunyu.json` 的 107 条中有 **2 条 `verse_id` 是占位符**（非 `章.节` 格式）：

| verse_id | 篇章 | chapter_id | 原文起 |
|---|---|---|---|
| `10.x` | 乡党 | 10 | 孔子于乡党，恂恂如也，似不能言者。其在宗庙朝廷，便便言，唯谨尔。 |
| `18.x` | 微子 | 18 | 楚狂接舆歌而过孔子曰：「凤兮凤兮！何德之衰？往者不可谏，来者犹可追。已而已而！今之从政者殆… |

复现命令：

```powershell
$ python -c "import json,re;d=json.load(open('data/processed/lunyu.json',encoding='utf-8'));print([v['verse_id'] for c in d['chapters'] for v in c['verses'] if re.search(r'\.x$',v['verse_id'])])"
['10.x', '18.x']

# 更严格：列出所有不匹配 ^\d+\.\d+$ 的 id
$ python -c "import json,re;d=json.load(open('data/processed/lunyu.json',encoding='utf-8'));print([v['verse_id'] for c in d['chapters'] for v in c['verses'] if not re.match(r'^\d+\.\d+$',v['verse_id'])])"
['10.x', '18.x']
```

**影响（两条，均为阻断级）**：

1. **Q1 方案 (c) 无法解析**：若采用「拆 `chapter_no` + `section_no`」的 `verse_no` 修复方向（见 §2.1 与 `03-task-dag.md` 的 Q1），`10.x` / `18.x` 的 `section_no` 无法从 id 解析出整数 → 该方案对这 2 条会失败或产生 `None`。
2. **PHASE 2 论语迁移时占位符会静默进入 L1**：这 2 条**已进入 143 条索引**（§1.3），迁移脚本若不显式校验 id 格式，会把占位符当作合法 `passage_id` 写入新表，造成 L1 中出现无法定位到具体章句的 passage。

**处置要求**：PHASE 2 论语迁移**之前**必须显式处理这 2 条（补全真实节号，或在 Schema 中允许并显式标注为「整篇合并条目」并禁止其作为精确引用证据）。**不得静默放过。**

### 1.10 GATE-2 前瞻判断

**GATE-2「所有 passage 必须有 source；原典不得来自 LLM 生成」在当前数据上无法通过**：现有 passage **没有** `source_provider`/`source_url`/`source_edition`，且生成方式无法证明非 LLM（`classical-knowledge.md:493`）。

---

## 2. RAG（GATE-0 第②项）

### 2.1 C1（blocker）：`RAGService.retrieve()` 恒定返回空列表

**四方独立互证**（t1 / t3 / t5 / t7 + 队长复核）。

**机制**：

| 环节 | 位置 | 事实 |
|---|---|---|
| 类型声明 | `backend/app/schemas/ai.py:17` | `verse_no: Optional[int]` |
| 索引写入 | `backend/app/services/rag_service.py:325`、`:690`、`:721` | 写入**字符串** `'1.1'`、`'15.16'`、`'daodejing-33-01'` |
| 构造对象 | `rag_service.py:897` | `verse_no=r["metadata"].get("verse_no")` → pydantic `int_parsing` 失败 |
| 异常吞没 | `rag_service.py:906-912` | `retrieve()` 用 `except Exception` 捕获后 `return []` |

**量化实测**：

```powershell
$ python docs/kb-v1/audit/_rag_probe_verseno.py
### stored verse_no values: total=143 non-integer=143 integer=0
   sample non-integer: ['1.1', '1.10', '1.11', ...]
   sample integer    : []

### RAGService.retrieve(): 32/32 queries returned ZERO references
```

（`rag.md:138-146`；本文作者独立复核为 `143/143` 非整数、`retrieve()` 返回 0 条。）

**影响面（已核对全部调用点）**：

| 调用点 | 影响 |
|---|---|
| `api/ai.py:326` `POST /api/ai/retrieve` | 恒返回空 `results`（HTTP 200 掩盖失效） |
| `api/ai.py:305` quiz 附带的 `references` | 恒为空 |
| `ai_service.py:99` `explain_verse` 的 RAG 上下文 | 恒为「（无匹配原文）」 |
| `ai_service.py:563` 另一处 `retrieve` | 同上 |
| `rag_service.py:1077 is_low_confidence()` | `refs` 恒空 → **恒返回 True** |

即 `explain` 路径的 `low_conf` **永远为真**，`DISCLAIMER_LOW_CONFIDENCE` 成为无条件输出，而非"低置信度"信号（`rag.md:158-159`）。

**未受影响**：`retrieve_for_sage_chat`、`retrieve_for_debate_sage` 返回 dict、不经过 `RAGReference`，仍正常。**这正是现有测试全部通过的原因**（测试只覆盖 dict 路径）。

> 结论：这不是"指标未达标"，而是**公开 API 与 explain 链路的功能性失效**。PROJECT-BRIEF 第十七章的 Recall@5、第十八章的性能指标在 C1 修复前**无从谈起**。

### 2.2 C2（high）：sage-chat 主路径无学派过滤

`sage-chat` 主路径（`ai_service.py:206,331` 的 `retrieve_for_sage_chat`）**不带 sage_key 过滤**，会跨学派返回结果。实测返回《诫子书》《定风波》等非本派文本（队长复核）。

### 2.3 C3（high）：`insufficient_evidence` 结构性不可达

`rag_service.py:493-496`：

```python
# Debate prompts need at least some authoritative context even when
# the modern topic vocabulary is sparse.
if score == 0:
    score = 0.25
```

实测「检索不到」分支不可达（`rag.md:507-511`）：

```
query='zzzz完全不相关的问题xyz'      -> 3 verses, sims=[0.099, 0.082, 0.051]
query='量子计算机如何优化神经网络'    -> 3 verses, sims=[0.071, 0.037, 0.0]
query='asdfghjkl'                -> 3 verses, sims=[0.0, 0.0, 0.0]
=> never empty: relevance floor injects unrelated 'evidence'
```

即系统**永不返回空**，而是把 0.0 相似度的段落当作「检索到的原典」注入 prompt → **PROJECT-BRIEF 第十二章「没有可靠证据时必须明确拒答」在当前实现中结构性不可达**（`rag.md:514-515`）。

### 2.4 B2（high）：`CHROMA_PERSIST_DIR` 相对路径依赖 CWD

| 位置 | 代码 | 路径形态 |
|---|---|---|
| `config.py:89` | `CHROMA_PERSIST_DIR: str = "./chroma_db"` | **相对** |
| `config.py:189-190` | `resolved_chroma_persist_dir` → `_resolve_backend_path(...)` | **绝对** |
| `rag_service.py:237` | `self.persist_dir = settings.CHROMA_PERSIST_DIR` | 用**相对**值 |
| `main.py:39` | `Path(settings.resolved_chroma_persist_dir)` | 用**绝对**值 |

实测（`rag.md:174-178`）：

```
if CWD=backend   -> D:\...\悟典\backend\chroma_db  <-- real index
if CWD=repo root -> D:\...\悟典\chroma_db          <-- DIFFERENT, empty
repo-root chroma_db exists: False
```

以仓库根启动后端会创建**空的新索引**并静默降级为空检索；而 `main.py:154-158` 健康检查读同一实例，**仍会报告 `rag_available`**，掩盖问题（无降级兜底）。CI 的 `working-directory: ./backend` 使该缺陷在 CI 中不可见（`rag.md:180-182`）。

### 2.5 索引持久化：满足"不重建"，但有 4 个缺陷

**已满足 PROJECT-BRIEF 第十八章**"索引必须持久化、启动不得每次全量重建"（`rag.md:278`）：

```powershell
### A. build_index() with force=False on the real (copied) index
   count before: 143
   _collection_has_debate_classics(): True
   build_index() returned 143; count before=143 after=143
   => rebuild happened: False
```

| id | 缺陷 | 证据 |
|---|---|---|
| D1 | 相对路径依赖 CWD（同 B2） | `rag_service.py:237` vs `main.py:39` |
| D2 | **无索引版本管理**（无 `embedding_version`），换 embedding 后不失效重建 | `rag_service.py:592-605` |
| D3 | metadata **截断 200 字符**（当前 max original=95、max commentary=149 未触发，但注疏超 200 字即被静默截断，破坏逐字引用校验） | `rag_service.py:533-534,691-692,722-723` |
| D4 | `_file_index`/`_commentary_index` 在 chromadb 可用时**为空** → 降级路径形同虚设 | `rag_service.py:231-233`；实测 chromadb 环境 `file_index=0 commentary_index=0` |

（来源：`rag.md:280-290`）

### 2.6 现有 `hybrid_search` 的缺陷

- `keyword_search` 只用 `keywords[0]` 单键过滤（`rag_service.py:825-849`，见 `rag.md:369`）。
- 非 BM25：**无 IDF、无长度归一化**（`rag.md:385`）。
- 无 metadata filter、无 rerank、无 diversity。
- 且因 C1，`hybrid_search` 本身恒抛异常。

### 2.7 PROJECT-BRIEF 第八章 Stage 1-7 逐条对照

| Stage | 要求 | 现状 | 判定 |
|---|---|---|---|
| 1 | Query Analyzer | 无，仅 `_expand_synonyms`（`:503-509`）字符串拼接 | **缺失** |
| 2 | Modern→Classical Query Expansion | `SYNONYM_MAP` 52 条（`:152-205`），词级替换；brief 示例问题 **0 命中** | **部分** |
| 3 | Hybrid: BM25 + Dense | `hybrid_search` 存在但恒返回 `[]`；`keyword_search` 非 BM25；Dense 为 hash 非语义 | **形式有、实质无** |
| 4 | Metadata Filtering | 无（`scope`/`school`/`book`/`text_type`/`concept` 均未用于过滤，`:812-816`） | **缺失** |
| 5 | Reranker | 无 | **缺失** |
| 6 | Diversification | 无 | **缺失** |
| 7 | Evidence Pack | 无 `EvidencePack` 结构；`build_sage_chat_context`（`:1020`）拼字符串 | **缺失** |

（来源：`rag.md:381-394`）

**必须新增而非改写**：Stage 1/2/4/5/6/7 与 `EvidencePack`。
**必须在现有实现上修复**：C1（`verse_no`）、B2（路径）、`keywords[0]`、D4（降级索引）。
**必须保留**：`RAGService` 单例、`retrieve_for_sage_chat`、`retrieve_for_debate_sage`、`build_sage_chat_context`、`build_debate_context`、`is_low_confidence` 的对外签名。

### 2.8 性能：当前可达，但需在 RAG V2 后重测

实测 P50≈5–11ms（`evaluation.md:379`），**满足 P50<1s / P95<3s**。但该数字是在 `retrieve()` 恒空的前提下测得，**RAG V2 落地后必须重测**。

### 2.9 多学派隔离

- RAG 层隔离**有效**：`retrieve_for_debate_sage` 的 `sage_key` filter 实际生效（`rag.md:485`）。
- 但存在 4 个泄露/失真风险（`rag.md:495`），核心是 C3 的 `score=0.25` 兜底会向任意派别注入不相关文本。

---

## 3. embedding（GATE-0 第③项）

### 3.1 实际实现：本地哈希，**非语义模型**

| 项 | 实测值 | 证据 |
|---|---|---|
| 默认 provider | `local` | `config.py:86` `RAG_EMBEDDING_PROVIDER: str = "local"` |
| 实际类 | `LocalHashEmbeddingFunction` | `rag_service.py:41-85` |
| 维度 | 384 | `rag_service.py:44`；chroma `collections.dimension = 384` |
| 算法 | blake2b 哈希分桶 + 符号，L2 归一化 | `rag_service.py:61-74` |
| 切 OpenAI 条件 | `RAG_EMBEDDING_PROVIDER=="openai"` **且** `OPENAI_API_KEY` 非空 | `rag_service.py:273` |
| 当前 `.env` | 未设 `RAG_EMBEDDING_PROVIDER`；`OPENAI_API_KEY` 被注释 | `backend/.env` |
| `EMBEDDING_MODEL` | `text-embedding-3-small`（**未被使用**，因 provider=local） | `config.py:53` |

（来源：`rag.md:188-198`）

`LocalHashEmbeddingFunction` 是**词袋式哈希**，稀疏性实测：5 字短语仅 **9/384** 维非零（`rag.md:198`）。

### 3.2 语义能力边界（可复现）

字面相同 → 高分；语义相同但字面不同 → 接近 0（`rag.md:205-212`）：

```
cosine similarity under LocalHashEmbeddingFunction:
   -0.0334  '同事抢了我的功劳我该不该撕破脸' vs '君子喻于义小人喻于利'
   +0.6974  '同事抢了我的功劳我该不该撕破脸' vs '同事抢了我的功劳'      (字面重叠)
   +0.1669  '领导不公平时我该忍吗' vs '不患寡而患不均'
   +0.0000  '我很焦虑怎么办' vs '君子坦荡荡小人长戚戚'                 (语义相关→0)
   +0.9037  '己所不欲勿施于人' vs '己所不欲，勿施于人'                 (仅标点差异)
   +0.2010  '学而时习之' vs '學而時習之'                              (繁体/简体)
```

**繁简余弦仅 0.13–0.20**（队长复核区间与上表一致）。

### 3.3 公平检索测试（仅用索引中确实存在的条目）

```
### fair semantic test on 5 pairs (expected passage IS in corpus)
    q=同事抢了我的功劳我该不该撕破脸   expected=不患人之不己知，患不知人   rank=1
    q=我不喜欢别人这样对我          expected=己所不欲，勿施于人      rank=2
    q=我犯错了怎么办              expected=过则勿惮改          rank=None
    q=我想换个环境工作            expected=道不同，不相为谋       rank=None
    q=我想学习该找谁              expected=三人行，必有我师焉      rank=None

    => Recall@5 (fair, expected present in corpus): 2/5

### exact-quote retrieval (upper bound of the hash embedding)
    => exact-quote top1 accuracy: 5/5
```

（来源：`rag.md:217-227`）

**现代问题 → 原典 Recall@5 = 2/5（40%）**；逐字引用 top1 = 5/5。

### 3.4 结论

hash embedding **只能作为明确标注的 fallback**。PROJECT-BRIEF 第八章明确要求"现有 hash embedding 只能保留做 fallback"。以当前实现，**GATE-4 的 Recall@5 ≥ 90% 不可达**（且因 C1 当前根本无法测量）。

---

## 4. citation（GATE-0 第④项）

### 4.1 `verifiable` 的真实语义

**`verifiable` = 「citation 的 `原文` 与本次 `rag_refs` 中某条 `original` 互为子串」**

- 实现：`backend/app/services/citation_validator.py:70-93`（`_match_citation`）
- 双向子串：`citation_validator.py:83`（`cit_original in ref_original or ref_original in cit_original`）与 `:90`（去标点后同向）

**该语义既不等于「这句话存在」，也不等于「出处正确」**（`trust.md:436`）。

### 4.2 「文本存在」与「出处正确」**完全没有区分**

**结论：当前实现中不存在任何出处正确性判定路径**（`trust.md:131`）。

证据：
1. `Citation` 模型只有 `id / source / original / verifiable` 四个字段，`verifiable` 是**单一布尔**，无法同时表达「存在」与「出处对」（`schemas/ai.py:103-111`、`schemas/debate.py:95-102`）。
2. `_match_citation` **全程只读 `原文`，从不读 `出处`**（`citation_validator.py:71-93`）。
3. `_check_classic_belonging` 只做「书名关键词是否出现」的字符串包含，对「同书错篇」完全无感（`《论语·学而》` 含 `论语` → 通过）（`citation_validator.py:95-101`）。
4. 全仓库 grep `quote_exists`、`source_correct`、`correct_source`、`trust_state` → **无匹配**。

> **PROJECT-BRIEF 第十一章要求输出 `quote_exists` 与 `source_correct` 两个独立指标 —— 当前为 0 实现。**

### 4.3 漏洞清单

| ID | 严重度 | 问题 | 证据 |
|---|---|---|---|
| T-01 | **blocker** | 默认对话路径（SSE）**不做任何引用校验**，LLM 的 `<<<QUOTE>>>` 原样作为「原文」展示 | `schemas/ai.py:98`（stream 默认 True）、`api.ts:1064`、`ai_service.py:242-252` |
| T-02 | **blocker** | citations 的 `verifiable` **硬编码为 `True`**，与 LLM 实际引用无关 | `api/ai.py:146,159,208`；`ai_service.py:424`；`schemas/ai.py:109`、`schemas/debate.py:100`（默认 True） |
| T-03 | **blocker** | 「文本存在」与「出处正确」无区分，出处正确性零校验 | `citation_validator.py:71-101` |
| T-04 | **high** | 双向子串匹配可被「伪造长文内嵌真实短句」绕过 | `citation_validator.py:83,90` |
| T-05 | **high** | **空 `出处`/`"无"` 使跨派检查直接放行**（`belongs=True`） | `citation_validator.py:99-100` |
| T-06 | **high** | `sentence_evidence.verifiable` 不校验句子与原文关系，**无关句恒判 True** | `debate_engine.py:149`；`rag_service.py:495-496` |
| T-07 | **high** | 无 Trust State；四态全缺，且 debate 链路**丢弃**已有 status | `citation_validator.py:64-67`；`debate_engine.py:391,502,579,730` |
| T-08 | **high** | 前端把「未提供 verifiable」当作「已核验」展示 | `roundtableFlow.ts:181`、`thoughtCourtSession.ts:35`、`EvidenceDock.tsx:103` |
| T-09 | **high** | 前端硬编码引用标 `verified: true`，其中 6/9 在当前语料中不存在 | `thoughtCourtCases.ts:13-79` |
| T-10 | **medium** | Mock 数据以 `verifiable: true` 冒充真实检索结果 | `api.ts:2012,2038`；`roundtable/page.tsx:571,590`（`similarity: 0.98` 硬编码） |
| T-11 | **medium** | 空引用被报告为 `all_verified` | `citation_validator.py:42,64-67` |
| T-12 | **medium** | 三处引用校验实现并存且语义分歧，其中 `debate_engine.py:86` 为**死代码** | `citation_validator.py:70`、`ai_service.py:352`、`debate_engine.py:86` |
| T-13 | **medium** | 繁简与空白未归一化导致**假阴性** | C3/C4/C8 实测 `verifiable=False` |
| T-14 | **low** | 前端把 `verifiable` 折算成 `similarity`，制造虚假相关度数值 | `roundtableFlow.ts:181`；`CitationSidebar.tsx:214` |

（来源：`trust.md:272-287`）

**本文作者独立复核的关键行号**：

```powershell
$ # 默认值矛盾
schemas/ai.py:108        verifiable: bool = Field(True,  ...)
schemas/debate.py:100    verifiable: bool = Field(True,  ...)   ← Citation
schemas/debate.py:111    verifiable: bool = Field(False, ...)   ← SentenceEvidence（相反默认）
$ # SSE 路径硬编码
api/ai.py:146   "verifiable": True,
api/ai.py:159   "verifiable": True,
api/ai.py:208   "verifiable": True,
```

**`verifiable` 默认值在 `schemas/ai.py:108` 与 `schemas/debate.py:100` 为 `True`，而 `schemas/debate.py:111` 的 `SentenceEvidence.verifiable` 为 `False`** —— 同一仓库内两个相反默认值，构成"缺省即视为已核验"与"缺省即未核验"的语义分裂。

### 4.4 白名单机制：**不存在**

**结论：不存在 Evidence Pack 白名单。LLM 可以引用检索结果之外的 source，且默认路径连「文本是否在检索结果里」都不检查**（`trust.md:151`）。

- `_match_citation` 对 `原文` 与本次 `rag_refs` 的比对，构成一个**很弱的**「文本在本次检索结果内」约束，但**它作用在 `原文` 上，不作用在 `出处` 上**（`trust.md:155-156`）。
- 提示词层面有要求（`prompt_templates.py:97-103`、`sage_persona.py:366-368`），但**无代码强制**。

### 4.5 Trust State：**无**

`verified` / `citation_corrected` / `quote_relaxed` / `insufficient_evidence` **四态全部不存在，需新增**（`trust.md:201`）。

- 全仓库 grep `trust_state|trustState|insufficient_evidence|quote_relaxed|citation_corrected` → **无匹配**。
- 现有最接近的是 `CitationValidator.validate` 的三值字符串（`citation_validator.py:64-67`）：`all_verified` / `partial_verified` / `unverified`，**不含**「存在但出处被纠正」「放宽匹配」「证据不足」语义。
- 该状态在 debate 链路被**全部丢弃**（`debate_engine.py:391,502,579,730` 写作 `validated_citations, _ = ...`）。
- 空引用时状态语义错误：`validate("confucius", [], [])` → `status='all_verified'`（`all_verified` 初值 `True`，`citation_validator.py:42`）。
- 前端 `citationStatus`（`thoughtCourtState.ts:7`）取值为 `verified | partial | unavailable`，与四态**不等价**，且由前端自行推算（`thoughtCourtSession.ts:66`）。

### 4.6 Claim-Evidence 绑定：**无**

**结论：无 claim 级绑定。现有 `sentence_evidence` 是「按句检索」，不是「claim→evidence→verification」，且其 `verifiable` 判定有严重误报**（`trust.md:220`）。

`debate_engine._bind_sentence_evidence`（`debate_engine.py:130-155`）把发言按 `。！？` 切句，**每句单独发起一次检索**，取 `top_k=1` 的第一条作为该句的「经典证据」。判定为（`debate_engine.py:149`）：

```python
verifiable=bool(refs and original != "无" and source != "无"),
```

**该判定不比较句子与检索到的原文之间是否存在任何文本关系。**

实测（`trust.md:239-241`）：

| 输入句子 | `verifiable` | 绑定到的「证据」 |
|---|---|---|
| `己所不欲，勿施于人。` | `True` | `《论语·泰伯》` 士不可以不弘毅，任重而道远。 |
| `今天天气不错，我打算去打球。` | **`True`** | `《论语·卫灵公》` 君子谋道不谋食。 |
| `股价暴跌让我很焦虑。` | **`True`** | `《论语·述而》` 用之则行，舍之则藏。 |

即**与《论语》毫无关系的现代句子，也被标注为拥有「可验证的经典依据」**。

### 4.7 六类对抗输入的结果（PROJECT-BRIEF 第十六章）

`trust.md:443-446` 摘要：

- **完全伪造的句子无法通过**（因需子串包含）—— 实测 `fabricated='孔子曰：忍一时风平浪静，退一步海阔天空'` → `verifiable=False`（`rag.md:554`）。
- 但 **C9（伪造长文内嵌真实短句）存在真实绕过** → `verifiable=True`。
- **C7（同书错篇）与 C10（空出处）被完全放过**。
- **短片段引用被长 ref 包含而判为 verified**：`citation='不己知'`（3 字）→ `verifiable=True`（`rag.md:544`），这是 `quote_relaxed` 场景当前被静默判为 `verifiable=True` 的根因。
- C3/C4/C8（繁体、部分引用等）因繁简与空白未归一化 → 假阴性。

**现有测试无法在第十六章对抗输入下失败，GATE-5 当前不可判定。**

---

## 5. tests（GATE-0 第⑤项）

### 5.1 关键前提：不存在单一可用解释器能跑完整后端套件

| 解释器 | 版本 | 有 `PyJWT` | 有 `chromadb` | 结果 |
|---|---|---|---|---|
| 系统 `python` | 3.11.9 | ✅ 2.15.0 | ❌ | **1 failed / 82 passed / 2 skipped / 13 subtests** |
| `backend/.venv/Scripts/python.exe` | 3.12.10 | ❌ | ✅ 1.5.9 | **collect 阶段 `ModuleNotFoundError`，0 个测试执行** |

- venv 失败点：`tests/conftest.py:40 from app.main import app` → `app/core/security.py:10 import jwt` → `ModuleNotFoundError: No module named 'jwt'`。
- `requirements.txt:18` 声明 `pyjwt>=2.8.0`，但 venv 未安装（venv 装的是 `python-jose 3.5.0`）→ **requirements.txt 与 .venv 已漂移**。
- **结论：不得宣称"后端测试全绿"**（`evaluation.md:29`）。

### 5.2 后端基线实测

**系统 Python（无 chromadb，降级模式）**：

```powershell
$ cd backend; python -m pytest tests -q
1 failed, 82 passed, 2 skipped, 1 warning, 13 subtests passed in 76.19s
FAILED tests/test_ai_provider.py::TestProviderSwitching::test_default_provider_is_openai
  assert 'agnes' == 'openai'   (tests/test_ai_provider.py:142)
```

- **2 skipped** = `test_debate_classic_rag.py` 中依赖 chromadb 的两个用例（`skipTest("ChromaDB collection is not available")`，第 18、49 行）。
- 该模式**掩盖**了 venv 模式下会暴露的第二个失败，故"降级模式通过"≠"真实 RAG 模式通过"。

**唯一失败的性质（F-4）**：`tests/test_ai_provider.py:140-144` 断言 `settings.LLM_PROVIDER == "openai"`，而 `config.py` 的 `model_config` 指定 `env_file=".env"`，`backend/.env` 中 `LLM_PROVIDER=agnes` 覆盖了 `config.py:56` 的默认值。已验证单独运行同样失败（**不是顺序问题**）；`backend/.env` 未被 git 跟踪（`.gitignore` 含 `.env`），**故该失败只在本机复现，CI 上不会出现**。属**既有环境相关失败**，非代码缺陷。

**venv + 隔离 chroma/db（推荐基线）**（`evaluation.md:43-59`）：

```powershell
$ cd backend; .\.venv\Scripts\python.exe -m pytest tests -q   # 借入 PyJWT + CHROMA_PERSIST_DIR 指向副本
1 failed, 84 passed, 3 warnings, 17 subtests passed in 72.80s
```

2 个 chromadb 用例真实执行（不再 skip），故 `passed 84 > 82`。**两次独立运行一致，判定为确定性基线。**

### 5.3 ⚠️ 必须声明的前提：串行、无其他 backend 进程

`backend/tests/conftest.py:14-19` 每个会话删除固定的 `backend/test_wudian.db`，`:26` 通过 `os.environ.setdefault` 把它设为默认 DB。**多个并发 pytest 进程会互相清表**，产生伪失败。

实测同一命令得到 **4 组不同失败集**（`evaluation.md:90-96`）：

```
run A: 1 failed (test_default_provider_is_openai)
run B: 1 failed (test_default_provider_is_openai)
run C: 5 failed (test_auth.py 4 项 + test_default_provider_is_openai)
run D: 6 failed (上述 + test_hackathon_readiness 路径断言)
```

排查：**无** `pytest-randomly` / `xdist` / `forked` 插件（`pip list` 为空）。根因 = 多个并发 pytest 进程共享同一 SQLite 文件；现场取证捕获到多个 `python.exe -m pytest tests -q` 进程同时运行。一方删除/重建该文件时，另一方的 `test_auth` 注册/登录即出现 `assert 409`、`KeyError`（`evaluation.md:97-103`）。

> **任何基线数字只有在「串行、无其他 backend 进程」前提下才可复现。**

### 5.4 前端测试：全绿但**不构成正确性证据**

```powershell
$ cd frontend; npm test
Test Files  23 passed (23)
     Tests  41 passed (41)
```

**该绿灯的验证力极低**，三点实测：

| 问题 | 实测 |
|---|---|
| `vitest.config.ts:16` 明确 `exclude: ["tests/*.test.cjs"]` | **22 个 `.cjs` 文件永不执行** |
| 20/41 为占位断言 | 22 个 `.test.tsx` 中 **20 个**唯一断言是 `expect(true).toBe(true)`；仅 `curtainPhysics(12)`、`thoughtCompass(5)`、`thoughtCourtState(4)` 有真实断言，合计 **21 个真实断言 / 20 个占位断言** |
| `npx tsc --noEmit` | **26 errors，全部位于 `tests/curtainPhysics.test.tsx`**，`TSC_EXIT=1` |
| `npx eslint . --ext .ts,.tsx ...` | **`ESLint couldn't find a configuration file`**，`ESLINT_EXIT=2`（frontend 下无任何 `.eslintrc*` / `eslint.config.*`）→ **CI lint 不可通过** |

（来源：`frontend.md:479-494`；本文作者独立复核 tsc=26 errors/exit 1、eslint 无配置/exit 2、`.cjs` 22 个、占位 20 个。）

> 关于 `tsc` 退出码：`frontend.md:487` 记录 `TSC_EXIT=2`，本文作者实测为 `TSC_EXIT=1`（错误数与文件范围一致：26 条、全部 `curtainPhysics.test.tsx`）。**退出码取值以本文实测为准**；该差异不影响"存在 26 个类型错误"这一结论。

### 5.5 破坏性测试：会清空并重建真实生产索引（F-1，blocker）

- 位置：`backend/tests/test_debate_classic_rag.py:20`、`:51` → `rag.build_index(force=True)`
- 破坏路径：`rag_service.py:638-639` → `_clear_collection()` → `rag_service.py:607-617` **删除全部 ids**
- **无隔离、无 fixture 副本、无标记**
- 真实索引 = 143 条
- **诚实说明**：PHASE 0 期间该测试曾触发（未隔离的那次运行），真实索引被清空+重建，**经核验内容无损**（id hash 一致）；收到提示后所有运行均隔离（`evaluation.md:83-84`）。
- 另注：`tests/conftest.py` **未覆盖 `CHROMA_PERSIST_DIR`**，故任何一次 `pytest tests` 都会改写真实索引。

### 5.6 断言强度缺陷清单

| ID | 严重度 | 问题 |
|---|---|---|
| F-1 | **blocker** | 破坏性测试清空并重建真实生产索引（见 §5.5） |
| F-2 | **blocker** | **22 个 `.cjs` 回归测试已被移出默认测试入口，静默失效** |
| F-3 | **high** | 20/22 个 vitest 用例是占位断言 `expect(true).toBe(true)` |
| F-4 | **high** | `test_default_provider_is_openai` 因本地 `.env` 确定性失败（见 §5.2） |
| F-5 | **medium** | 仅断言 HTTP 200 / 存在性的弱测试（`test_hackathon_readiness.py:27-44` 仅断言 `/health` 含 9 个 key 名，**不断言任何值**） |
| F-6 | **high** | 测试套件不可并行 / 共享固定 SQLite 路径（见 §5.3） |
| F-7 | **medium** | mock 替代真实检索（`test_debate_sentence_evidence.py:14-31,51`、`test_hackathon_readiness.py:48-68` 用 `FakeRag` + monkeypatch） |
| F-8 | **low** | `test_rag_embedding_config.py:14-22` 断言过弱（不断言维度 384、确定性、语义可区分性） |

（来源：`evaluation.md:144-187`）

**F-2 详证**（`evaluation.md:151-154`；本文作者独立复核）：

```powershell
$ git show HEAD~1:frontend/package.json | ...  # scripts.test
node tests/curtainPhysics.test.cjs && node tests/tengwangExperienceWiring.test.cjs && ... (21+ 个 .cjs 链)
$ git show HEAD:frontend/package.json | ...
vitest run
$ git log --oneline -1 -- frontend/package.json
64c8618 chore: prepare current Wudian project for GitHub publication
```

**HEAD `64c8618` 把 `frontend/package.json` 的 `test` 从 21 个 `.cjs` 链整体替换为 `vitest run`，而 `vitest.config.ts:16` 又 exclude 了 `tests/*.test.cjs`** → 这 **22 个文件永不执行**。手工直跑结果：**18 通过 / 4 失败**（失败：`comicExperienceWiring` / `readerExperience` / `tengwangExperienceWiring` / `runtimeAssets`）。

影响：前端真实回归保护从 **321 处断言降级为 41 处（其中 20 处为占位）**，属"以改测试入口达成绿灯"的实质等价物。

### 5.7 覆盖率缺口（对后续 Gate 直接致命）

| 缺口 | 证据 | 影响 Gate |
|---|---|---|
| `rag_service` 检索质量（Recall/MRR）**完全无测试** | 全仓库 `Recall@|MRR|recall` 命中 **0** | GATE-4 |
| `citation_validator` **对抗场景完全无测试** | 仅 2 处引用，均为"正例应通过"；无假古文/错出处/繁体/部分引用/鸡汤用例 | GATE-5 |
| 跨派泄露无测试 | `backend/tests/` 中 `leak|泄露|跨派` 命中 **0** | GATE-6 |
| `knowledge_graph` 无测试 | `backend/tests/` 中引用 **0** | 回归风险 |
| **无 `eval/` 目录，无任何 Gold Set** | `Test-Path eval` → `False`；全仓库无 `.jsonl` | GATE-8 |
| **无覆盖率工具** | `pip list` 无 `pytest-cov`/`coverage`，**但 `ci.yml` 执行 `--cov=app`** | GATE-9 |

（来源：`evaluation.md:124-133`；本文作者独立复核：`cd backend; python -m pytest tests -q --cov=app` → `error: unrecognized arguments: --cov=app`，本地**不可复现** CI 的覆盖率步骤。）

**关键澄清**：`api/ai.py` 的 5 个端点（explain/translate/chat-sage/generate-quiz/retrieve）**全部无端点级测试**；81 条 OpenAPI 路径中仅 `/api/auth/*`(4)、`/api/debate/*`(11)、`/health`(1) 有直接测试（`backend.md` §1.3）。

---

## 6. 其他必录事实

### 6.1 前端硬编码证据与"相关度"伪造

| 项 | 实测 | 证据 |
|---|---|---|
| `roundtableData.ts` 硬编码引用 | **32 条**，其中 **16 条**出自零语料书目（`《传习录》` 8 + 孟子 8） | 本文作者独立复核 |
| `sageData.ts` 兜底引用 | **19 条**，其中 **10 条**在真实语料中**无法逐字定位** | 本文作者独立复核 |
| `sageData.ts` 的"相关度" | 手写常量 **0.78–0.95**，非检索得分 | `frontend.md:26`、`frontend.md:382-391` |
| `thoughtCourtCases.ts` | 9 条 `verified: true`，其中 **6/9 在当前语料中不存在** | `trust.md:282`、`frontend.md:370` |
| 前端伪造相关度 | `normalizeCitations` 把 `verifiable: true` 折算为 `similarity = 1` → UI 显示「相关度 100%」 | `frontend.md:22,317-326` |
| 编造 source 实例 | `roundtableData.ts:199` `"事在四方，要在中央"` 标为 `《韩非子·物权》`（**无"物权"篇**，实出《韩非子·扬权》） | `frontend.md:409-422` |

`sageData.ts` 10 条无法逐字定位的引用（本文作者实测）：

```
《论语·卫灵公》 | 工欲善其事，必先利其器
《孟子·滕文公下》 | 富贵不能淫，贫贱不能移，威武不能屈
《孟子·公孙丑上》 | 我善养吾浩然之气
《孟子·公孙丑上》 | 恻隐之心，仁之端也
《传习录》 | 知者行之始，行者知之成
《传习录》 | 致良知
《传习录》 | 心外无物，心外无理
《道德经·第一章》 | 道可道，非常道；名可名，非常名
《韩非子·有度》 | 刑过不避大臣，赏善不遗匹夫
《韩非子·扬权》 | 事在四方，要在中央
```

其中 `《韩非子·有度》|刑过不避大臣，赏善不遗匹夫` 与 `《道德经·第一章》` 等属**真实存在的经典文句但不在本仓库语料中** —— 即系统以"本次可溯源证据 + 相关度 N%"展示，而语料内并无对应文本。

**结论：这些数据没有 `source_provider` / `source_url` / 复核状态，却以「已核验」呈现。它们不得被当作 A 级权威原典，也不得作为 Evidence Drawer 的验收样本**（`frontend.md:377`、`frontend.md:753`）。

### 6.2 两条互不相通的经典数据通道

| 通道 | 数据源 | 消费方 |
|---|---|---|
| A | `data/processed/lunyu.json` 等 JSON（运行时读取） | `classics_service`（`/api/classics/*`）、`rag_service`（检索） |
| B | `verses` 表（107 行，由 `init_db.py` 导入） | `learning.py` / `progress_service` / `srs_service` / `quiz_service` |

（来源：`backend.md` §2.4）PHASE 1 的 Passage Schema 必须决定二者如何统一或桥接，否则会产生第二套并行真值。

### 6.3 数据库与迁移：三者一致

```
migration tables: 18 ; db tables: 18 ; identical: True
alembic_version: [('601e9ee0d57f',)]
```

`verses` 107 行 / `chapters` 20 行 / `classic_books` 1 行 / `verse_embeddings` **0 行** / `ai_chat_logs` **0 行**（`backend.md` §2.1-2.3）。

### 6.4 既有测试中的 mock 替代真实 RAG（违反 brief 禁令）

- `test_debate_sentence_evidence.py:14-31` 定义 `FakeRAG`，`:51` 注入；`:38-46` 用 `fake_complete_json` 取代真实 LLM。
- `test_hackathon_readiness.py:48-68` 用 `FakeRag`（`retrieve_for_sage_chat` 返回空）+ monkeypatch 缓存。

**这些测试验证的是编排逻辑，不构成真实 RAG 成功证据**（`evaluation.md:183`）。Eval 必须独立于它们。

---

## 7. 兼容性边界（增量升级红线）

**必须保持不变的对外契约**（`backend.md` §5）：

| 约束 | 证据 |
|---|---|
| `POST /api/ai/chat-sage` 的 SSE 事件名：`{"type":"chapters"}`、`{"content":...}`、`{"type":"citations"}`、`[DONE]` | `api/ai.py:116-169`；前端 `frontend/lib/api.ts:1053` |
| SSE citations 的**中文 key**：`id`、`出处`、`原文`、`chapter`、`translation`、`verifiable` | `api/ai.py:140-147` |
| `ChatSageResponse`：`reply/citations/confidence/honest_note/modern_takeaway` | `schemas/ai.py:113-122` |
| `VerseExplanation` | `api/ai.py:44-56`；`lib/api.ts:908` |
| `POST /api/auth/refresh` | `lib/api.ts:135` |
| `POST /api/debate/{session_id}/{action}?stream=true` | `lib/api.ts:2060` |
| `SageSpeech.citations` / `sentence_evidence` / `quote` / `source` | `schemas/debate.py:114-127` |
| `GET /health` 的 `llm_available/rag_available/rag_count/...` | `main.py:171-183`；`test_hackathon_readiness.py:38-44` |
| `verifiable: bool`、`confidence`、`honest_note` 字段 | `schemas/ai.py:108,121-122` |

**前端实际只消费 3 类端点**（全量扫描 `frontend/**/*.ts,tsx`）：`/api/ai/chat-sage`、`/api/auth/refresh`、`/api/debate/`。故 §5.7 中大量无测试端点（community/content/learning/exploration）当前无前端调用方，兼容性风险低于表面。

**可安全扩展**：`Citation` / `SentenceEvidence` / `RAGReference` 新增**带默认值的可选字段**（`trust_state`、`evidence_id`、`verification_level`、`text_type`、`commentator` 等）向后兼容。

**必须修复才能继续（阻断项）**：`RAGReference.verse_no` 类型冲突（§2.1）。**PHASE 4 开始前必须解决，否则 Recall@5 恒为 0。**

---

## 8. 未核验项与阻塞（诚实声明）

### 8.1 外部核验通道不可用

- 本机对 `ctext.org`、`zh.wikisource.org` 的访问被拒（`non-public IP address`）；`web_search` 因缺少 `DEEPSEEK_API_KEY` 不可用（`classical-knowledge.md:25`）。
- **因此所有「与通行本一致」的结论一律标注「未核验」**。本报告不对任何一条文本作"与通行本一致"的断言，只报告可本地证实的内部一致性事实。
- **市场 / 竞品结论为「未核验假设」，不得写成事实**。

### 8.2 未验证项清单

| 项 | 状态 | 原因 |
|---|---|---|
| 全部文本与权威底本的一致性 | **未核验** | 外部通道不可用 |
| 语料是否为 LLM 生成 | **无法证明/否证** | 生成器为内置字典，无溯源元数据 |
| 真实 LLM 回答质量 | **未验证** | 无可用密钥；PHASE 0 未发起任何真实 LLM 请求 |
| 真实人工标注 / Gold Set | **不存在** | `eval/` 目录不存在，0 条 Gold |
| 来源授权 / 版权 | **不存在** | 零 `license` 字段 |
| PostgreSQL + pgvector 分支 | **未验证** | 本地仅 SQLite；`models/embedding.py:28-39` 未实测 |
| CI（GitHub Actions）实际是否通过 | **未验证** | 本地无法复现 CI 的 3.12 + pytest-cov + ruff 组合；且 CI **从不运行 `.cjs` 套件** |
| `init_db.py` 全量执行 | **未执行** | 有破坏性（清空 18 张表），只读审计中禁止执行 |
| `以德报怨` 是否在语料中 | **待复核** | `evaluation.md:387` 串查为 NOT-FOUND，待 t2/t9 复核 |
| 后端完整测试环境 | **阻塞** | `requirements.txt` 与 `.venv` 漂移（缺 pyjwt），**仓库无一条命令能开箱跑出完整后端基线** |

### 8.3 Gate 可达性判断（不修改目标数字）

| Gate | 目标 | 当前可达性 | 依据 |
|---|---|---|---|
| GATE-4 Recall@5 | ≥ 90% | **不可达（且当前无法测量）** | C1 使 `retrieve()` 恒空；L1 仅 128 条、仅 1 部完整书 |
| GATE-5 Quote Exactness | ≥ 99% | **不可达** | 无 QuoteVerifier；`citation_validator` 仅子串匹配（无繁简/标点归一化、无出处独立判定） |
| GATE-5 Source Attribution | ≥ 98% | **不可达** | 无独立"出处正确性"指标 |
| GATE-5 伪造引文放行 | ≈ 0 | **当前极可能失败** | 双向子串（`citation_validator.py:83-91`）+ 无对抗测试 |
| GATE-6 School Leakage | < 1% | **不可达** | 非儒家各派仅 3–4 条语料，必然回退 `score=0.25` 兜底；无泄露测试 |
| GATE-8 Unsupported Refusal | ≥ 95% | **不可达** | 无 Trust State；C3 使「检索不到」分支不可达 |
| GATE-8 Claim Evidence Coverage | ≥ 95% | **不可达** | 无 Claim-Evidence 绑定 |
| 性能 P50<1s / P95<3s | — | **可达（当前）** | 实测 P50≈5–11ms；RAG V2 后须重测 |
| GATE-8 ≥200 Gold | 200 条 | **当前 0 条** | `eval/` 不存在 |

（来源：`evaluation.md:370-382`）

**结论：以当前数据规模与实现状态，GATE-4/5/6 与 GATE-8 的多数指标明确不可达。** 必须先修复 C1、把语料扩到 V1 书目规模（PHASE 2）、实现 Trust Layer（PHASE 5），才能进入指标验收。

**禁止**：修改目标数字、放宽公式、用 mock 或占位断言冒充通过、以 HTTP 200 宣称功能通过。

### 8.4 PHASE 0 写入边界确认

```powershell
$ git status --short
?? docs/kb-v1/
$ git diff --stat
(空)
```

- **无 tracked 文件被修改**，`PROJECT-BRIEF.md` 未变。
- 唯一新增为 `docs/kb-v1/`（审计文档与复现脚本）。
- 未 commit / push / deploy。

---

## 附：本文件关键数字的一行式复核命令

```powershell
cd D:\systemDir\Desktop\悟典
# L1 原典 128 条；完全相等重复 0 条、部分包含恰好 1 对（confucius ⊂ lunyu 8.7）
python -c "import json,re;lu=json.load(open('data/processed/lunyu.json',encoding='utf-8'));dc=json.load(open('data/processed/debate_classics.json',encoding='utf-8'));n=lambda s:re.sub(r'[，。！？；：、（）\u3000\s「」『』]','',s);L=[(v['verse_id'],n(v.get('original',''))) for c in lu['chapters'] for v in c['verses'] if v.get('original')];D=[(k,n(x.get('original',''))) for k,v in dc['classics'].items() for x in v['verses'] if x.get('original')];print('exact',sum(1 for k,d in D for i,l in L if d==l));print('partial',[(k,i) for k,d in D for i,l in L if d and d!=l and (d in l or l in d)])"
# V1 书目覆盖 4 部有数据 / 8 部零语料
python -c "import json;lu=json.load(open('data/processed/lunyu.json',encoding='utf-8'));dc=json.load(open('data/processed/debate_classics.json',encoding='utf-8'));T=['论语','孟子','荀子','大学','中庸','道德经','庄子','墨子','韩非子','商君书','传习录','孙子兵法'];c={t:0 for t in T};c['论语']+=sum(len(x['verses']) for x in lu['chapters']);[c.__setitem__(t,c[t]+len(v['verses'])) for k,v in dc['classics'].items() for t in T if t in v.get('book','')];print(c);print('with data',[t for t in T if c[t]]);print('zero',[t for t in T if not c[t]])"
# 占位符 verse_id（应为 ['10.x','18.x']）
python -c "import json,re;d=json.load(open('data/processed/lunyu.json',encoding='utf-8'));print([v['verse_id'] for c in d['chapters'] for v in c['verses'] if re.search(r'\.x$',v['verse_id'])])"
# 注疏 15 条
python -c "import json;print(len(json.load(open('backend/data/commentaries/lunyu_zhuxi.json',encoding='utf-8'))['commentaries']))"
# 索引 143 条（需 chromadb，用 venv）
cd backend; .venv/Scripts/python.exe -c "import sys;sys.path.insert(0,'.');import os;os.environ.setdefault('JWT_SECRET_KEY','x');from app.services.rag_service import get_rag_service;print(get_rag_service().collection.count())"
# 后端基线（必须串行、无其他 backend 进程）
cd backend; python -m pytest tests -q
# 前端
cd frontend; npm test
cd frontend; npx tsc --noEmit          # 26 errors, exit 1
cd frontend; npx eslint . --ext .ts,.tsx --report-unused-disable-directives --max-warnings 0   # exit 2, 无配置
```
