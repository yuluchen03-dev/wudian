# PHASE 0 审计：RAG、embedding、索引持久化与检索链路

- 任务：t3（PHASE 0 只读审计）
- 执行者：rag-expert
- 仓库：`D:\systemDir\Desktop\悟典`，branch `codex/overall-optimization`，HEAD `64c8618`
- 审计日期：2026-02（本地实测）
- 审计范围：只读。未修改任何产品代码、测试、数据或索引。
- 证据脚本：`docs/kb-v1/audit/_rag_probe_*.py`（8 个只读探针，均可复现）

## 0. 审计方法与只读保证

绝大多数探针把 `backend/chroma_db` **复制到临时目录**，再把 `CHROMA_PERSIST_DIR` 指向副本，
并**从不调用 `build_index(force=True)`**。

**必须如实披露的一点**：`_rag_probe_enviro.py` 未设置 `CHROMA_PERSIST_DIR`，
因此该探针以 `CWD=backend` 打开了**真实索引**（`./chroma_db`）。它只执行
`vector_search` / `keyword_search` / `retrieve` / `hybrid_search`（均为只读查询），
未调用任何写入方法；但 ChromaDB `PersistentClient` 在打开时会触碰 `chroma.sqlite3`
（WAL/seq_id），实测该文件 `LastWriteTime` 因此发生变化。

审计结束时已重新校验真实索引**内容完整、未被破坏**：

```
count: 143
scope: {'sage_chat': 122, 'debate_classic': 21}
doc_type: {'verse': 128, 'commentary': 15}
integrity OK: True
```

结论：真实索引**语义内容未改变**（仍为 143 条，组成与审计开始时一致），
但"完全未触碰真实索引文件"的说法不成立，故在此更正。后续 Phase 若要求严格只读，
应对**所有**探针统一设置副本路径。

验证写入边界（工作树）：

```
$ git status --short
?? docs/kb-v1/
$ git diff --stat          # 空
```

工作树除 `docs/kb-v1/`（本审计产出）外无任何改动。`backend/chroma_db/` 被 `.gitignore` 忽略，非版本控制对象。

> 重要：`backend/tests/test_debate_classic_rag.py:20,51` 会调用 `rag.build_index(force=True)`，
> 即**清空并重建真实索引**。该文件属于写入型测试，本审计**未运行**其写入用例（详见 §8）。

---

## 1. 真实检索链路图

`RAGService` 是单例（`rag_service.py:149,207-211`），在 `__init__` 中根据 `chromadb` 是否可用分叉。

```
                        get_rag_service()  (rag_service.py:1144)
                                  │
                    RAGService.__init__ (rag_service.py:213)
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        │ HAS_CHROMADB = True                               │ HAS_CHROMADB = False
        │ (rag_service.py:239-255)                          │ (rag_service.py:223-235)
        ▼                                                   ▼
 PersistentClient(path=settings.CHROMA_PERSIST_DIR)   collection = None, embed_fn = None
 get_or_create_collection("wudian_verses")            _load_file_index()      -> 107 条
 _load_debate_classic_index()  (仅此一个!)             _load_commentary_index() -> 15 条
        │                                             _load_debate_classic_index() -> 21 条
        │                                                   │
        └─────────────────────────┬─────────────────────────┘
                                  ▼
                     ┌────────────────────────┐
                     │  对外检索入口（4 条）   │
                     └────────────────────────┘

 (A) retrieve(query, top_k)  rag_service.py:906
        └─> hybrid_search()  rag_service.py:854
              ├─ vector_search()   rag_service.py:801
              │     ├─ collection 存在 → collection.query(query_texts=[query])   :812-816
              │     └─ collection=None → _file_keyword_search()                  :809
              ├─ keyword_search()  rag_service.py:825
              │     ├─ collection 存在 → collection.query(where_document={$contains: keywords[0]}) :840-845
              │     └─ collection=None → _file_keyword_search()                  :833
              └─ 融合: weighted_score = similarity * 0.7 / 0.3, 按 text 去重 :876-891
                     └─> 构造 RAGReference(...)  :892-901   ★ 此处抛异常 → 返回 []

 (B) retrieve_for_sage_chat(query, top_k)  rag_service.py:914
        └─> 有 collection: vector_search(expanded_query, top_k*2)   :937
            collection=None: _file_keyword_search(...)             :940
        └─> 按 doc_type 拆 verses / commentaries，返回 dict  ★ 不经过 RAGReference

 (C) retrieve_for_debate_sage(sage_key, query, top_k)  rag_service.py:992
        ├─ _debate_vector_search(sage_key)  rag_service.py:542
        │     └─ collection.query(where={scope=debate_classic AND sage_key=...})  :557-563
        ├─ 若空 → _debate_keyword_search(sage_key)  rag_service.py:463
        └─ 若仍空且 sage_key=="confucius" → retrieve_for_sage_chat()  :1006-1007

 (D) vector_search / keyword_search（内部方法，返回原始 dict）
```

真实实现要点（与文档/注释声称的差异）：

| 环节 | 声称 | 实测 |
|---|---|---|
| `retrieve()` 混合检索 | 返回向量+关键词融合的 top_k 引用 | **恒返回 `[]`**（§2 阻塞项 B1） |
| `hybrid_search` 融合 | 加权融合 | 权重按 `text` 去重合并，`vector_weight=0.7/keyword_weight=0.3`（`:879,884`） |
| `keyword_search` | 关键词检索 | 只用 `keywords[0]` 做 `where_document` 子串过滤（`:843`），实测 0 命中 |
| `vector_search` | 语义检索 | 无 `where` 过滤，跨 `scope` 全库检索（`:812-816`） |
| 同义词扩展 | 现代词→古文词 | 52 条 `SYNONYM_MAP`（`:152-205`），对 brief 示例问题 **0 命中**（§5） |

---

## 2. 阻塞项：`RAGService.retrieve()` 恒定返回空列表

### B1（blocker）：`RAGReference.verse_no` 类型不匹配导致 `retrieve()` 全量失效

- `backend/app/schemas/ai.py:17`：`verse_no: Optional[int]`
- 索引中 `verse_no` 实际全部为**字符串**（`'1.1'`, `'15.16'`, `'daodejing-33-01'`）
- `rag_service.py:897` 传入 `verse_no=r["metadata"].get("verse_no")` → pydantic `int_parsing` 校验失败
- `retrieve()` 捕获异常并 `return []`（`rag_service.py:910-912`）

复现（`_rag_probe_enviro.py`）：

```
### env=chromadb PRESENT
    collection=set file_index=0 commentary_index=0
    raw search ('什么是仁') -> 3 hits
    RAGService.retrieve('什么是仁') -> 0 RAGReference
    => retrieve() BROKEN in this env: True
    hybrid_search() RAISED ValidationError
      1 validation error for RAGReference

### env=chromadb ABSENT (file fallback)
    collection=None file_index=107 commentary_index=15
    raw search ('什么是仁') -> 3 hits
    RAGService.retrieve('什么是仁') -> 0 RAGReference
    => retrieve() BROKEN in this env: True
    hybrid_search() RAISED ValidationError
```

量化（`_rag_probe_verseno.py`）：

```
### stored verse_no values: total=143 non-integer=143 integer=0
   sample non-integer: ['1.1', '1.10', '1.11', '1.12', '1.13', '1.14', '1.15', '1.16', '1.2', '1.3', '1.4', '1.5']
   sample integer    : []

### RAGService.retrieve(): 32/32 queries returned ZERO references
```

**影响面**（已核对调用点）：

| 调用点 | 影响 |
|---|---|
| `backend/app/api/ai.py:326` `POST /api/ai/retrieve`（RAG 调试接口） | 恒返回空 `results` |
| `backend/app/api/ai.py:305` 生成 quiz 时附带的 `references` | 恒为空 |
| `backend/app/services/ai_service.py:99` `explain_verse` 的 RAG 上下文 | 恒为"（无匹配原文）" |
| `backend/app/services/ai_service.py:563` 另一处 `retrieve` 调用 | 同上 |
| `rag_service.py:1077 is_low_confidence()` | `refs` 恒空 → **恒返回 True** |

即：`explain` 路径（`ai_service.py:101,138`）的 `low_conf` **永远为真**，`DISCLAIMER_LOW_CONFIDENCE`
成为无条件输出，而非"低置信度"信号。

**未受影响**（返回 dict，不经过 `RAGReference`）：`retrieve_for_sage_chat`、`retrieve_for_debate_sage`。
这正是现有测试全部通过的原因（§8）：测试只覆盖 dict 路径。

> 结论：这不是"指标未达标"，而是**公开 API 与 explain 链路的功能性失效**。
> PROJECT-BRIEF 第十八章的性能指标、第八章的检索质量都无从谈起，直到 B1 被修复。

### B2（high）：`CHROMA_PERSIST_DIR` 相对路径依赖 CWD

- `rag_service.py:237`：`self.persist_dir = settings.CHROMA_PERSIST_DIR` → `'./chroma_db'`（相对）
- `main.py:39`：`Path(settings.resolved_chroma_persist_dir)` → 绝对路径（`backend/chroma_db`）

实测（`_rag_probe_startup.py`）：

```
   if CWD=backend   -> D:\systemDir\Desktop\悟典\backend\chroma_db  <-- real index
   if CWD=repo root -> D:\systemDir\Desktop\悟典\chroma_db  <-- DIFFERENT, empty
   repo-root chroma_db exists: False
```

以仓库根目录启动后端，会创建一个**空的新索引**并静默降级为空检索，而 `main.py` 健康检查
（`main.py:154-158`）读的是同一实例，因此仍会报告 `rag_available`，掩盖问题。
CI（`.github/workflows/ci.yml`）的 `working-directory: ./backend` 使该缺陷在 CI 中不可见。

---

## 3. embedding 现状

| 项 | 实测值 | 证据 |
|---|---|---|
| 默认 provider | `local` | `config.py:86` `RAG_EMBEDDING_PROVIDER: str = "local"` |
| 实际类 | `LocalHashEmbeddingFunction` | `_rag_probe_retrieval.py` 输出 `embed_fn: LocalHashEmbeddingFunction` |
| 维度 | 384 | `rag_service.py:44`；chroma `collections.dimension = 384` |
| 算法 | blake2b 哈希分桶 + 符号，L2 归一化 | `rag_service.py:61-74` |
| 切 OpenAI 条件 | `RAG_EMBEDDING_PROVIDER=="openai"` **且** `OPENAI_API_KEY` 非空 | `rag_service.py:273` |
| 当前 `.env` | 未设置 `RAG_EMBEDDING_PROVIDER`；`OPENAI_API_KEY` 被注释 | `backend/.env` |
| `EMBEDDING_MODEL` | `text-embedding-3-small`（但未被使用，因 provider=local） | `config.py:53`, `backend/.env` |

`LocalHashEmbeddingFunction` 是**词袋式哈希**，非语义模型。稀疏性实测：5 字短语仅 **9/384** 维非零。

### 语义能力边界（可复现失败例）

字面相同 → 高分；语义相同但字面不同 → 接近 0：

```
cosine similarity under LocalHashEmbeddingFunction:
   -0.0334  '同事抢了我的功劳我该不该撕破脸' vs '君子喻于义小人喻于利'
   +0.6974  '同事抢了我的功劳我该不该撕破脸' vs '同事抢了我的功劳'      (字面重叠)
   +0.1669  '领导不公平时我该忍吗' vs '不患寡而患不均'
   +0.0000  '我很焦虑怎么办' vs '君子坦荡荡小人长戚戚'                 (语义相关→0)
   +0.9037  '己所不欲勿施于人' vs '己所不欲，勿施于人'                 (仅标点差异)
   +0.2010  '学而时习之' vs '學而時習之'                              (繁体/简体)
```

检索层面（`_rag_probe_semantic_fair.py`，**仅使用索引中确实存在的条目**，避免不公平判定）：

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

结论：hash embedding 在**逐字引用**场景可用（top1 5/5），在**现代问题→古典思想**场景不可用。
这正是 PROJECT-BRIEF 第七章（"不能直接丢给 embedding"）与第八章（现代→古典扩展）针对的问题。

补充：`_rag_probe_semantic.py` 的 6 个"期望命中"用例中有 5 条**根本不在语料库内**
（如"德不孤，必有邻"、"君子坦荡荡，小人长戚戚"、"不患寡而患不均"、"以直报怨，以德报德"），
说明语料覆盖不足本身就是一个独立缺陷（见 §7、§9）。

---

## 4. 索引持久化现状（实测 count）

### 4.1 持久化确实存在，且启动不重建

```
$ python docs/kb-v1/audit/_rag_probe_chroma.py
collections rows:
   ('c523cef2-acab-4181-adfa-d39c33059531', 'wudian_verses', 384)
segments rows:
   ('4a2cb26c-8aee-409b-a934-af1dcf8578d7', 'urn:chroma:segment/vector/hnsw-local-persisted', 'VECTOR')
   ('551b559b-e6d0-4624-a8ce-edaa51e3a316', 'urn:chroma:segment/metadata/sqlite', 'METADATA')
row counts:
   embeddings 143
   embedding_metadata 1686
   embedding_fulltext_search 143
```

- 文件：`backend/chroma_db/chroma.sqlite3`（4,120,576 bytes）+ HNSW 段目录
- collection：`wudian_verses`，dimension **384**
- **实测 count = 143**

组成校验（`_rag_probe_startup.py`）：

```
   lunyu verses=107 + commentaries=15 + debate_classics=21 = 143
   observed chroma embeddings = 143
   match: True
```

启动行为（`main.py:70-80` 调用 `rag.build_index()`，`force` 默认 `False`）：

```
### A. build_index() with force=False on the real (copied) index
   count before: 143
   _collection_has_debate_classics(): True
   build_index() returned 143; count before=143 after=143
   => rebuild happened: False
```

**满足 PROJECT-BRIEF 第十八章"索引必须持久化、启动不得每次全量重建"。**

### 4.2 但存在 4 个持久化缺陷

| id | 缺陷 | 证据 |
|---|---|---|
| D1 | 相对路径依赖 CWD（同 B2） | `rag_service.py:237` vs `main.py:39` |
| D2 | 无索引版本管理 | 无 `embedding_version` 字段；换 embedding 后不会失效重建，`_collection_has_debate_classics()` 只检查 `scope=debate_classic` 是否存在（`:592-605`） |
| D3 | metadata 截断 200 字符 | `rag_service.py:533-534,691-692,722-723`；当前 `max original=95`、`max commentary=149`，尚未触发，但**注疏文本超 200 字即被静默截断**，会破坏逐字引用校验 |
| D4 | `_file_index`/`_commentary_index` 在 chromadb 可用时为空 | 仅在 `HAS_CHROMADB=False` 分支加载（`:231-233`）；实测 chromadb 环境 `file_index=0 commentary_index=0` |

D4 的后果：`vector_search` 的降级路径 `_file_keyword_search`（`:809`）在 chromadb 已加载但
查询失败时返回 **0 条**，而非退回关键词检索——降级形同虚设。

### 4.3 索引内语料分布（决定检索可达上限）

```
book counts (n=143):
    '论语' 125
    '道德经' 4
    '墨子' 4
    '韩非子' 4
    '李白诗文' 2
    '苏轼词文' 1
    '范仲淹文' 1
    '王安石诗文' 1
    '诸葛亮文' 1
```

对照 PROJECT-BRIEF 第四章 V1 必选书目：

| 书目 | 索引内 | 备注 |
|---|---|---|
| 论语 | ✅ 125（107 经文 + 15 注疏 + 3 百家） | 唯一有实质规模的语料 |
| 道德经 | ⚠️ 4 | 仅 4 章 |
| 墨子 | ⚠️ 4 | |
| 韩非子 | ⚠️ 4 | |
| 孟子 / 荀子 / 大学 / 中庸 | ❌ 0 | |
| 庄子 | ❌ 0 | |
| 商君书 | ❌ 0 | |
| 传习录 | ❌ 0 | |
| 孙子兵法（可选） | ❌ 0 | |

**这直接决定 RAG 指标的可达性**：即使检索算法完美，孟子/庄子/荀子/传习录相关查询
的 Recall@5 也**必然为 0**，因为没有可召回的文档。PROJECT-BRIEF 第十七章
`Retrieval Recall@5 >= 90%` 在当前语料下**不可达**——这不是算法问题，是数据缺口。
多学派差异目前也主要由 4 条/派的极小语料 + 角色 prompt 支撑，而非真实语料规模。

### 4.4 chromadb 缺失时的降级

```
### env=chromadb ABSENT (file fallback)
    collection=None file_index=107 commentary_index=15
    raw search ('什么是仁') -> 3 hits
    RAGService.retrieve('什么是仁') -> 0 RAGReference
```

- 降级**能加载** 107 条论语 + 15 条注疏 + 21 条百家语料
- 但 `retrieve()` 同样因 B1 返回 `[]`
- 环境事实：`backend/.venv`（Python 3.12.10）有 `chromadb 1.5.9`；系统 Python 3.11.9 **无 chromadb**
  → 两套环境行为不同（§8）

---

## 5. 现有 `hybrid_search` 的真实融合方式与缺陷

代码（`rag_service.py:854-901`）：

```python
vec_results = self.vector_search(query, top_k=top_k)      # :869
kw_results  = self.keyword_search(query, top_k=top_k)     # :870
for r in vec_results: r["weighted_score"] = r["similarity"] * vector_weight   # 0.7
for r in kw_results:  r["weighted_score"] = r["similarity"] * keyword_weight   # 0.3
ranked = sorted(merged.values(), key=..., reverse=True)   # :891
return [RAGReference(...) for r in ranked[:top_k]]        # :892-901  ★ 抛异常
```

| id | 缺陷 | 证据 |
|---|---|---|
| H1 | **恒抛异常 → 返回 `[]`**（=B1） | `:897` 传字符串 `verse_no` |
| H2 | `keyword_search` 只用 `keywords[0]` | `:843` `where_document={"$contains": keywords[0]}`；实测 `'什么是仁'`→0 命中、`'同事抢了我的功劳我该不该撕破脸'`→0 命中 |
| H3 | 无 reranker | 无 cross-encoder / LLM rerank，仅线性加权 |
| H4 | 无 metadata filter | `vector_search`（`:812-816`）不带 `where`；`scope`/`school`/`book`/`text_type` 均未用于过滤 |
| H5 | 无 diversity | 无 MMR / 同章去重；Top-5 可全来自同一章（PROJECT-BRIEF 第八章明令禁止） |
| H6 | 距离→相似度粗糙 | `sim = max(0.0, 1.0 - dist)`（`:1096`），cosine 距离截断至 [0,1] |
| H7 | 融合按 `text` 去重 | `:876-891` 以整段文本为 key，同一经文的原文/注疏不会合并 |
| H8 | `top_k` 无上限 | `top_k*2`（`:842`）无 cap，大 `top_k` 会放大 Chroma 查询 |

H2 复现（`_rag_probe_final.py`）：

```
### B. keyword_search (rag_service.py:825-849) uses keywords[0] only
    q=什么是仁                     keywords[0]='什么是仁'             -> 0 hits
    q=同事抢了我的功劳我该不该撕破脸          keywords[0]='同事抢了我的功劳我该不该撕破'   -> 0 hits
```

即 `keyword_search` 实际上**几乎永不命中**：`_extract_keywords` 把整段（含虚词）作为
`keywords[0]`（`:1116-1123`），而索引文档并不包含该整串。

---

## 6. PROJECT-BRIEF 第八章 Stage 1-7 逐条对照

| Stage | 要求 | 现状 | 判定 | 增量策略 |
|---|---|---|---|---|
| 1 | Query Analyzer | 无。仅 `_expand_synonyms`（`:503-509`）字符串拼接 | **缺失** | 新增独立模块 |
| 2 | Modern→Classical Query Expansion | `SYNONYM_MAP` 52 条（`:152-205`），词级替换；brief 示例问题 0 命中 | **部分**（不足以支撑第七章） | 新增概念映射层，保留 `SYNONYM_MAP` 作 fallback |
| 3 | Hybrid: BM25 + Dense | `hybrid_search` 存在但恒返回 `[]`；`keyword_search` 非 BM25（无 IDF/长度归一化）；Dense 为 hash 非语义 | **形式有、实质无** | 先修 B1，再新增真 BM25 + 语义 embedding |
| 4 | Metadata Filtering | 无。`scope`/`school`/`book`/`text_type`/`concept` 均未用于过滤（`:812-816`） | **缺失** | 新增过滤层（`scope`/`sage_key` 已存在于 metadata，可复用） |
| 5 | Reranker | 无 | **缺失** | 新增 |
| 6 | Diversification | 无 | **缺失** | 新增 MMR/同章去重 |
| 7 | Evidence Pack | 无 `EvidencePack` 结构；`build_sage_chat_context`（`:1020`）拼字符串 | **缺失** | 新增，`build_*_context` 保留作兼容 |

**必须新增而非改写**：Stage 1/2/4/5/6/7 与 `EvidencePack`。
**必须在现有实现上修复**：B1（`RAGReference.verse_no`）、B2（路径）、H2（`keywords[0]`）、D4（降级索引）。
**必须保留**：`RAGService` 单例、`retrieve_for_sage_chat`、`retrieve_for_debate_sage`、
`build_sage_chat_context`、`build_debate_context`、`is_low_confidence` 的对外签名（第十九章兼容要求）。

---

## 7. 性能基线（实测）

命令：

```powershell
cd backend
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_final.py
```

结果（warm，40 次/方法，**不含任何外部 LLM 调用**；embedding 为本地 hash）：

```
### C. clean latency (warm, 40 iterations each)
    vector_search                              n=40 P50=    1.3ms P95=    1.7ms max=    1.9ms
    keyword_search                             n=40 P50=    1.7ms P95=    2.4ms max=    2.7ms
    retrieve (hybrid, BROKEN->empty)           n=40 P50=    4.3ms P95=    6.3ms max=    7.0ms
    retrieve_for_sage_chat                     n=40 P50=    2.2ms P95=    2.9ms max=    3.0ms
    retrieve_for_debate_sage(mozi)             n=40 P50=    2.7ms P95=    3.5ms max=    5.1ms
    NOTE: no external LLM call anywhere in the above; embedding is local hash.
```

含冷启动（首次构造 `RAGService`，另一轮，32 次查询）：`P50=48.0ms P95=119.9ms`。

对照 PROJECT-BRIEF 第十八章（P50<1s / P95<3s，不含外部 LLM）：

- **当前实测远优于目标**（P95 ≤ 6.3ms），但这是 **143 条文档**规模下的结果。
- `retrieve` 的 4.3ms **不代表检索有效**——它测的是"抛异常→返回空列表"的耗时。
- 该基线**不可作为 RAG V2 的性能承诺**：引入语义 embedding 与 reranker 后必然显著上升。
- 结论：性能目标当前**无风险但未验证**，需在 RAG V2 完成后重测。

---

## 8. 测试环境与现有测试的真实覆盖

### 8.1 两个 Python 环境都不能跑 RAG 相关测试

| 环境 | chromadb | pyjwt | RAG 测试结果 |
|---|---|---|---|
| `backend/.venv`（3.12.10） | ✅ 1.5.9 | ❌ 缺失 | **无法收集**：`ModuleNotFoundError: No module named 'jwt'` |
| 系统 Python（3.11.9） | ❌ 缺失 | ✅ 2.15.0 | 可跑，但 chromadb 用例 **SKIPPED** |

```
--- venv (chromadb yes, jwt no) ---
app\core\security.py:9: in <module>
    import jwt
E   ModuleNotFoundError: No module named 'jwt'

--- system python (jwt yes, chromadb no) ---
tests/test_debate_classic_rag.py::...::test_build_index_writes_debate_classics_to_chromadb SKIPPED
tests/test_debate_classic_rag.py::...::test_debate_rag_can_retrieve_from_chromadb_without_memory_index SKIPPED
tests/test_debate_classic_rag.py::...::test_debate_rag_retrieves_only_the_requested_sage_classic PASSED
tests/test_debate_classic_rag.py::...::test_debate_rag_supports_verified_core_fallback_quotes PASSED
=============== 2 passed, 2 skipped, 8 subtests passed in 0.10s ================
```

`requirements.txt:18` 声明了 `pyjwt>=2.8.0`，但 `.venv` 未安装 → **`backend/.venv` 不是可用的测试环境**。

### 8.2 写入型测试（本审计未运行）

`backend/tests/test_debate_classic_rag.py:20,51` 调用 `rag.build_index(force=True)`
→ 内部 `_clear_collection()`（`:607-617`）**先删除全部 143 条**再重建。
该用例属于"重建索引"的破坏性测试，与"只读审计"冲突，故**未运行**。
其存在本身也是一个风险：任何人在生产索引目录执行 `pytest` 都会触发全量重建。

### 8.3 覆盖缺口：`retrieve()` 路径零测试

```
=== tests referencing rag.retrieve / hybrid_search / RAGReference ===
(无匹配)
```

**没有任何测试引用 `rag.retrieve()`、`hybrid_search` 或 `RAGReference`。**
这就是 B1（阻塞级缺陷）能长期存在而测试全绿的原因。

现有 RAG 测试只覆盖 dict 路径：
- `test_rag_embedding_config.py:14-22`：只断言 `_build_embed_fn()` 不是 OpenAI 且返回等长向量
- `test_debate_classic_rag.py:76-99`：断言各派 `source` 含对应书名（隔离）
- `test_debate_classic_rag.py:101-126`：断言 `citation_validator.validate` 返回 `all_verified`

---

## 9. 多学派隔离现状与跨派泄露风险

### 9.1 隔离在 RAG 层**有效**

```
### 2. retrieve_for_debate_sage isolation (sage_key filter IS applied)
    confucius   books=['论语']
    laozi       books=['道德经']
    mozi        books=['墨子']
    hanfeizi    books=['韩非子']
```

`_debate_vector_search` 使用 `where={$and:[{scope=debate_classic},{sage_key=...}]}`（`:557-563`），
隔离机制真实有效。这是**可以保留并复用的增量基础**。

### 9.2 但存在 4 个泄露/失真风险

| id | 风险 | 证据 |
|---|---|---|
| L1 | **无关查询也返回"证据"**：`_debate_keyword_search` 有 `if score == 0: score = 0.25` 兜底，然后**无条件 append**（`:495-498`） | `'量子计算机如何优化神经网络'` → 3 条韩非子"证据"（sim 0.110/0.105/0.016） |
| L2 | `retrieve_for_sage_chat` **无 `scope` 过滤**，可返回 `debate_classic` 行 | 实测 `'我该不该躺平'` top-5 含 `scope=debate_classic` 的《论语·述而》 |
| L3 | 孔子 fallback 是**死代码**：因 L1 永不返回空，`:1006-1007` 分支不可达 | 清空 `_debate_classic_index` 后结果与未清空时**完全一致** |
| L4 | `_check_classic_belonging` 在 `source` 为空/`"无"` 时**返回 True**（放行） | `citation_validator.py:99-100`：`if not source or source == "无": return True` |

L1 复现：

```
### A. Does _debate_keyword_search ever return EMPTY? (rag_service.py:493-498)
    query='zzzz完全不相关的问题xyz'      -> 3 verses, sims=[0.099, 0.082, 0.051]
    query='量子计算机如何优化神经网络'    -> 3 verses, sims=[0.071, 0.037, 0.0]
    query='asdfghjkl'                -> 3 verses, sims=[0.0, 0.0, 0.0]
    => never empty: relevance floor injects unrelated 'evidence'
```

L1 直接冲击 PROJECT-BRIEF 第十二章"没有可靠证据时必须明确拒答"：当前系统**不会**拒答，
而是把一个 0.0 相似度的段落当作"检索到的原典"注入 prompt。这属于**"用 mock 假装真实 RAG 成功"的变体**。

L4 复现：

```
### 3. citation_validator._check_classic_belonging bypass cases
    sage=confucius   src=''               belongs=True
    sage=confucius   src='无'              belongs=True
    sage=confucius   src='<missing>'      belongs=True
    sage=confucius   src='《墨子·兼爱》'        belongs=False
    sage=mozi        src='《论语·学而》'        belongs=False
```

即：**不填出处即可绕过学派归属检查**（`belongs=True`）。

### 9.3 与 citation_validator 的交互（跨派泄露的真实边界）

两条校验路径并存：

- `citation_validator.validate()`（含学派检查）— 用于 debate：`debate_engine.py:391,502,579,730`
- `ai_service._validate_citations()`（**不含**学派检查）— 用于 sage chat：`ai_service.py:519`

子串匹配方向性（`citation_validator.py:83`）：

```
### 4. _match_citation substring direction
    citation='不患人之不己知，患不知人也'   verifiable=True
    citation='不患人之不己知'            verifiable=True
    citation='患不知人也'              verifiable=True
    citation='不己知'                 verifiable=True      ★ 3 字片段即"可验证"
```

**短片段引用会被长 ref 包含而判为 verified** —— 这是 quote_relaxed 场景当前被静默判为
`verifiable=True` 的根因。

好消息：**完全伪造的句子无法通过**（因需子串包含）：

```
### 5. does a FABRICATED quote pass against real refs?
    fabricated='孔子曰：忍一时风平浪静，退一步海阔天空'   verifiable=False
    fabricated='老子云：努力必有回报'                verifiable=False
    fabricated='子曰：职场PUA当以直报怨'             verifiable=False
```

但注意前提：这些判 False 是因为 refs 里**恰好没有**可被包含的片段。若伪造句**包含**某真实
短句（如"子曰：不己知者，何以言勇"），子串方向性会让它通过——属于 t4（trust）的深挖范围，
此处仅记录 RAG 侧接口事实。

---

## 10. 结论与对 RAG V2 的输入

### 10.1 阻塞项（必须先修，否则任何 RAG 指标无意义）

| id | 严重度 | 问题 | 位置 | 修复方向 |
|---|---|---|---|---|
| B1 | **blocker** | `retrieve()`/`hybrid_search()` 恒返回 `[]` | `schemas/ai.py:17` + `rag_service.py:897` | 使 `verse_no` 兼容字符串（改类型或规范化），并加 `retrieve()` 回归测试 |
| B2 | high | 相对 `CHROMA_PERSIST_DIR` 依赖 CWD | `rag_service.py:237` | 改用 `settings.resolved_chroma_persist_dir` |
| L1 | high | 无关查询注入"证据"，系统不拒答 | `rag_service.py:495-498` | 移除无条件兜底，改为显式 `insufficient_evidence` |
| H2 | medium | `keyword_search` 只用 `keywords[0]`，实际 0 命中 | `rag_service.py:843` | 换真 BM25 |
| D4 | medium | chromadb 可用时降级索引为空 | `rag_service.py:231-233` | 始终加载文件索引作 fallback |
| L4 | medium | 空出处绕过学派检查 | `citation_validator.py:99-100` | 空 source 应判 False（归 t4 修复） |

### 10.2 可直接复用的增量基础

- `RAGService` 单例与 4 个对外入口签名（兼容要求）
- `scope` / `sage_key` metadata 与按派过滤机制（隔离已验证有效）
- ChromaDB 持久化索引（143 条，启动不重建，满足第十八章）
- `_debate_classic_index` 按 `sage_key` 的隔离设计
- 现有 dict 返回结构（`verses` / `commentaries`），已被前端与 debate 依赖

### 10.3 必须在后续 Phase 新增

Stage 1 Query Analyzer、Stage 2 现代→古典概念扩展、Stage 3 真 BM25 + 语义 embedding、
Stage 4 metadata filter、Stage 5 reranker、Stage 6 diversity、Stage 7 `EvidencePack`；
以及 embedding 版本化（`embedding_version`）与索引失效重建策略。

### 10.4 未验证 / 证据不足

- **语义检索质量**：当前 hash embedding 下 Recall@5 = 2/5（小样本，n=5，非 Gold Set）。
  引入真实 embedding 后的表现**未验证**，且需要真实外部 API key（当前 `.env` 无 `OPENAI_API_KEY`）。
- **性能目标**：P50<1s / P95<3s 在 143 条规模下宽松满足，但 RAG V2 引入 reranker 后**未验证**。
- **`backend/.venv` 可测性**：缺失 `pyjwt`，无法运行完整后端测试套件；该环境问题**未修复**（PHASE 0 只读）。
- **检索质量指标**：`retrieval_gold` 数据集不存在（`eval/` 目录不存在），
  Recall@1/3/5 与 MRR **无法计算**。
- **索引写入型测试风险**：`test_debate_classic_rag.py:20,51` 会清空真实索引；本审计未运行，
  其"通过"状态**未经本人验证**。

---

## 附：可复现命令

```powershell
cd D:\systemDir\Desktop\悟典\backend
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"

# 索引内容与 count（只读 sqlite）
python ..\docs\kb-v1\audit\_rag_probe_chroma.py

# 检索链路 + 语义能力 + 延迟
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_retrieval.py
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_semantic_fair.py
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_final.py

# B1 量化（两个环境对比）
python ..\docs\kb-v1\audit\_rag_probe_enviro.py
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_enviro.py
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_verseno.py

# 启动重建 / 路径 / 降级
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_startup.py
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_config.py

# 多学派隔离与泄露
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_debate.py
.\.venv\Scripts\python.exe ..\docs\kb-v1\audit\_rag_probe_leakage.py
```

> 除 `_rag_probe_enviro.py` 外，所有探针均在 `backend/chroma_db` 的**临时副本**上运行，不写入真实索引。
> `_rag_probe_enviro.py` 会以只读查询打开真实索引（见 §0 披露）。
> **切勿**直接运行 `pytest tests/test_debate_classic_rag.py`（会 `force=True` 重建真实索引）。
