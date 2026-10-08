# PHASE 0 审计 · 产品需求与市场来源核验

- 任务：t1（product-research）
- 审计对象：仓库 `D:\systemDir\Desktop\悟典`，branch `codex/overall-optimization`，HEAD `64c8618`
- 审计日期：2026-02-12（本地）
- 性质：**只读审计**。未修改任何产品代码、测试、数据或配置。
- 证据原则：所有事实性陈述均给出 `文件:行号` 或可复现命令输出。无法核验的一律标注「未核验」，不以分享会话或记忆作为事实。

---

## 0. 结论摘要（先读这一段）

| # | 结论 | 严重度 |
|---|---|---|
| C1 | `RAGService.retrieve()` **恒定返回空列表**，因 `RAGReference.verse_no` 为 `Optional[int]` 而 Chroma 元数据存的是 `"1.1"` 字符串，转换抛 `ValidationError` 被静默吞掉。该缺陷使 `/api/ai/retrieve`、`/api/ai/explain`、`/api/ai/generate-quiz` 的 RAG 依据**全部为空**。 | **blocker** |
| C2 | `retrieve_for_sage_chat()` **没有学派/scope 过滤**，实测「上善若水」在孔子对话路径中把《道德经·第八章》排在第一位。多学派隔离只在 debate 路径存在。 | **blocker**（P0 多学派差异） |
| C3 | `_debate_keyword_search()` 给**每一条**语料兜底 `score = 0.25`，使检索在任何不相关问题上都必然返回结果。实测「如何面对亲人的离世？」在韩非子/墨子/老子路径均返回 3 条。这直接摧毁「检索不到就不硬编」。 | **blocker**（P0 防编造） |
| C4 | 语料真实规模远小于 V1 目标：论语 **107 条**（文件自述「512 章」），百家论道 **21 条 / 9 位圣贤**（孔子 3、老子 4、墨子 4、韩非子 4），注疏 **15 条且仅朱熹一家**。`classics_catalog.json` 声明 **123 部书**，但只有论语有真实内容。 | **high** |
| C5 | 后端测试**当前无法运行**：`backend/.venv` 缺 `jwt`，`conftest.py` 导入 `app.main` 即失败，0 个测试被执行。任何「测试通过」的宣称在本次环境下均不成立。 | **blocker**（证据链） |
| C6 | 前端 Evidence Drawer（`EvidenceDock.tsx`）只展示 原文/出处/释义/边界/核验布尔，**缺** 注疏者、数据来源、文本类型、可信等级 A/B/C/D；且 `verified` 在字段缺失时默认 `true`。 | **high** |
| C7 | 市场/竞品/用户痛点结论**全部未核验**：本环境 web_search 无 API key、web_fetch 被网络策略拒绝。仓库内所有市场陈述均为**未经独立验证的产品自述**。 | **high**（诚实性） |
| C8 | 前端「一键跳转原文上下文」**不生效**：`SageChat.tsx:333-341` 传 `highlight`/`source` 参数，`frontend/app/reader/page.tsx:13-14` 只读 `book`，参数被丢弃。 | **medium**（对外承诺不符） |

---

## 1. 现状能力清单

图例：**代码存在** = 有实现；**有测试** = 有自动化断言覆盖；**真实数据支撑** = 有真实语料/真实检索可用。
「真实可用」列是三者综合判定。

### 1.1 问答与检索主链路

| 能力 | 支撑位置 | 实测/读取到的行为 | 代码存在 | 有测试 | 真实数据支撑 | 真实可用 |
|---|---|---|---|---|---|---|
| 圣贤对话（非流式） | `backend/app/services/ai_service.py:431` `chat_with_sage_structured` | RAG 检索 → LLM JSON → `_validate_citations` | 是 | 部分 | 是（107 条） | **是，但有缺陷**（C2） |
| 圣贤对话（SSE 流式） | `backend/app/api/ai.py:80-227` | 先发 `chapters` 事件，再流式正文，最后发 `citations` | 是 | 部分 | 是 | 是 |
| RAG 检索（调试接口） | `backend/app/api/ai.py:317-327` → `rag_service.py:906` | **返回恒为空** | 是 | 否 | — | **否**（C1） |
| 逐句精讲 | `backend/app/services/ai_service.py:87-150` | `rag.retrieve` 恒空 → `is_low_confidence` 恒 `True` | 是 | 否 | — | **否**（C1） |
| 文白翻译 | `backend/app/services/ai_service.py`（`translate_text`） | 纯 LLM，不经检索 | 是 | 否 | 不适用 | 是 |
| 生成测验题 | `backend/app/api/ai.py:288-311` | `rag.retrieve(req.verse_id)` 恒空 → `references=[]` | 是 | 否 | — | **否**（C1） |
| 混合检索 | `backend/app/services/rag_service.py:854-901` | 向量 + 关键词加权融合 | 是 | 否 | 是 | 部分 |
| 百家论道检索（按派隔离） | `rag_service.py:992-1009` `retrieve_for_debate_sage` | 按 `sage_key` 过滤；无结果时兜底恒返回 | 是 | 是（`test_debate_classic_rag.py`） | 是（21 条） | 是，但**必然有结果**（C3） |
| 与圣贤对话检索（**无派别过滤**） | `rag_service.py:914-990` | 全库检索，**无 scope 过滤** | 是 | 否 | 是 | 是，但**跨派泄露**（C2） |

复现 C1（命令与原始输出）：

```powershell
cd backend
@'
import sys, asyncio
sys.path.insert(0, ".")
from app.services.rag_service import get_rag_service
rag = get_rag_service()
for q in ["仁", "学而时习之", "人不知而不愠", "how to lead a team", "x"]:
    print(f"retrieve({q!r}) -> n={len(asyncio.run(rag.retrieve(q, top_k=5)))}")
print("vector_search raw:", [(r['metadata'].get('verse_no'), round(r['similarity'],3))
                             for r in rag.vector_search("如何面对亲人的离世？", top_k=3)])
'@ | .venv/Scripts/python.exe -
```

实际输出：

```
RAG retrieve 异常，返回空列表: 1 validation error for RAGReference
verse_no
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='1.1', input_type=str]
retrieve('仁') -> n=0
retrieve('学而时习之') -> n=0
retrieve('人不知而不愠') -> n=0
retrieve('how to lead a team') -> n=0
retrieve('x') -> n=0
vector_search raw: [('1.5', 0.221), ('3.3', 0.206), ('15.16', 0.18)]
```

根因：`backend/app/schemas/ai.py:17` 定义 `verse_no: Optional[int]`；`backend/app/services/rag_service.py:897` 传入 `r["metadata"].get("verse_no")`，而元数据在 `rag_service.py:690`、`rag_service.py:721`（sage_chat 路径）与 `rag_service.py:532`、`rag_service.py:325`（debate / 文件索引路径）写入的都是 `vid`（如 `"1.5"`、`"lunyu-taibo-01"`）这类**字符串**。转换异常在 `rag_service.py:910-912` 被 `except` 捕获并降级为 `[]`。

### 1.2 引用与可信展示

| 能力 | 支撑位置 | 实测/读取到的行为 | 真实可用 |
|---|---|---|---|
| 引用子串校验 | `backend/app/services/citation_validator.py:70-93` | 双向子串 + 去标点，**不校验出处** | 是（弱） |
| 跨派归属校验 | `citation_validator.py:95-101` | 仅 `SAGE_CLASSICS` 白名单字串包含 | 是（弱） |
| 引用的另一套校验 | `backend/app/services/ai_service.py:352-411` | 与 `citation_validator` **重复实现** | 是 |
| 引用另一套校验（debate） | `backend/app/services/debate_engine.py:86-111` | **第三套**重复实现 | 是 |
| 逐句证据绑定 | `debate_engine.py:130-155` `_bind_sentence_evidence` | 每句检索 top-1，`verifiable=bool(refs and ...)` | 是 |
| Trust State | — | **不存在**。仅有 `confidence: high/medium/low` 与 `honest_note` | **否** |
| Evidence Pack 白名单 | — | **不存在**。LLM 可返回检索结果之外的 `出处/原文` | **否** |
| Quote Verifier | — | **不存在**。无 `/api/knowledge/verify-quote` | **否** |
| Claim-Evidence 绑定 | `debate_engine.py:130-155`（逐句） | 仅 debate 路径有逐句证据；sage-chat 无 claim 拆分 | 部分 |

### 1.3 前端用户可见能力

| 能力 | 支撑位置 | 实测行为 | 真实可用 |
|---|---|---|---|
| 问→证→辩→判 四幕 | `frontend/components/thought-court/ThoughtCourtExperience.tsx`、`useThoughtCourt.ts` | 状态机 `thoughtCourtState.ts:42` | 是 |
| 经典依据抽屉 | `frontend/components/thought-court/EvidenceDock.tsx` | 展示 原文/出处/释义/边界/已核验 | 是（字段不全，C6） |
| 引用汇总面板 | `frontend/components/roundtable/CitationPanel.tsx` | 原文 + 出处 + 相关度 | 是 |
| 圣贤对话引用侧栏 | `frontend/components/sage/CitationSidebar.tsx:197-218` | 序号/出处/相关度/原文摘要/注疏标记 | 是 |
| 今日行动 | `frontend/components/thought-court/VerdictScroll.tsx:116-120` | 渲染 `verdict.actions` | 是 |
| 继续追问 | `frontend/components/sage/SageChat.tsx`（`onSubmit` + history） | 有输入框与历史 | 是 |
| 辩论中追问/站队/互问 | `backend/app/api/debate.py`（`intervene` / `stand` / `mutual_question`） | 接口存在 | 是 |
| 可信等级 A/B/C/D 展示 | — | **不存在** | **否** |
| 文本类型（原文/注疏/译文/现代解释）分层展示 | `thoughtCourtTypes.ts:9-16`（无 `text_type` 字段） | **不存在** | **否** |

C6 证据 — `EvidenceDock.tsx:92-105` 展开区仅渲染三项：

```
释义  {item.interpretation}
边界  {item.boundary}
已核验 {item.verified ? "已核验" : "待核验"}
```

`frontend/lib/thoughtCourtSession.ts:35` 的默认值处理：

```ts
verified: citation.verifiable !== false,
```

即后端**未返回** `verifiable` 字段时，前端判定为 `true`（已核验）。这是「未核验当作已核验」的默认放行路径。

`frontend/lib/thoughtCourtSession.ts:66` 的聚合逻辑：

```ts
const citationStatus = verifiedCount === 0 ? "unavailable"
  : verifiedCount === evidence.length && speeches.every(...) ? "verified" : "partial";
```

由于上游默认 `true`，`unavailable` 分支在字段缺失时不可达。

### 1.4 语料与数据（真实统计）

命令：

```powershell
cd backend
@'
import json
d = json.load(open("../data/processed/lunyu.json", encoding="utf-8"))
print("book:", d["book"], "| self-declared:", d.get("total_chapters"), "chapters")
print("actual chapters:", len(d["chapters"]), "| actual verses:", sum(len(c["verses"]) for c in d["chapters"]))
c = json.load(open("../data/processed/debate_classics.json", encoding="utf-8"))["classics"]
print("debate classics:", {k: len(v["verses"]) for k, v in c.items()})
print("debate total:", sum(len(v["verses"]) for v in c.values()))
print("commentaries:", len(json.load(open("data/commentaries/lunyu_zhuxi.json", encoding="utf-8"))["commentaries"]))
cat = json.load(open("../data/processed/classics_catalog.json", encoding="utf-8"))
print("catalog books declared:", len(cat["books"]))
'@ | .venv/Scripts/python.exe -
```

实际输出：

```
book: 论语 | self-declared: 20 chapters
actual chapters: 20 | actual verses: 107
debate classics: {'confucius': 3, 'laozi': 4, 'mozi': 4, 'hanfeizi': 4, 'li_bai': 2,
                  'su_shi': 1, 'fan_zhongyan': 1, 'wang_anshi': 1, 'zhuge_liang': 1}
debate total: 21
commentaries: 15
catalog books declared: 123
```

> 注：`lunyu.json` 的 `description` 字段自述「共20篇512章」，而实际条目为 20 篇 107 条。该自述与文件内容不一致，属于**文件内的不准确描述**，须在 PHASE 1 一并修正（不得当作规模证据）。

Chroma 持久化真实状态（只读查询 `backend/chroma_db/chroma.sqlite3`）：

```
collections: [('c523cef2-...', 'wudian_verses')]
embeddings total: 143
scope 分布: debate_classic = 21, sage_chat = 122
doc_type 分布: verse = 128, commentary = 15
```

即索引总量 **143 条**，与源码语料总量一致（107 论语 + 15 注疏 + 21 百家 = 143）。索引**已持久化**，非每次重建。

### 1.5 测试基线（实测）

命令与结果：

```powershell
cd backend; .venv/Scripts/python.exe -m pytest tests -q
```

实际输出（尾部）：

```
ImportError while loading conftest 'D:\systemDir\Desktop\悟典\backend\tests\conftest.py'.
tests\conftest.py:40: in <module>
    from app.main import app
app\main.py:199: in <module>
    from app.api import ai
app\core\security.py:9: in <module>
    import jwt
E   ModuleNotFoundError: No module named 'jwt'
[exit code: 1]
```

**结论：0 个后端测试被执行。** `backend/.venv` 未安装 `jwt`（`pip list` 中无 PyJWT/python-jose）。系统 Python 有 `jwt`，但缺 `chromadb`。因此**当前环境不存在可用的后端测试基线**，任何「后端测试通过」的说法在本次审计中均**未验证**。

依赖缺失清单（实测 `pip list`，venv 内）：有 `chromadb 1.5.9`、`fastapi 0.138.2`、`pydantic 2.13.4`、`pytest 9.1.1`；缺 `jwt`。

---

## 2. P0 / P1 逐条对照表

### P0-1 防 AI 编造古籍

| 项 | 内容 |
|---|---|
| 要求 | 模型不得输出知识库中不存在的「经典原文」；无法核验即不得展示为原文 |
| 现状证据 | `prompt_templates.py:97-102` 有「绝不编造经典中没有的原文」提示词约束；`citation_validator.py:70-93` 做子串匹配；`ai_service.py:521-535` 对未匹配引用做降级替换 |
| 差距 | ①**无白名单**：模型可返回检索结果之外的 `出处`，校验只比对 `原文`，**不校验 `出处`**（`citation_validator.py:70-93` 完全未使用 `cit_source` 做存在性判断，仅 `_check_classic_belonging` 做字串包含）；②**无 Quote Verifier**：无法在原始知识库中精确复核；③存在 5 处硬编码 `verifiable=True` 未经任何校验即宣称可溯源：`backend/app/api/ai.py:146`、`ai.py:159`（流式 citations）、`ai.py:208`（兜底 citations）、`ai.py:265`（兜底 `ChatSageResponse`），以及 `backend/app/services/ai_service.py:424`（缓存 citations）；④C3 的兜底 `score=0.25` 让「检索不到」这一分支几乎不可达；⑤C1 使 `explain`/`retrieve` 路径的依据恒空 |
| 验收判据（可自动化） | ①对 PROJECT-BRIEF 第十六章全部对抗输入（假古文、真古文+错误出处、繁体、部分引用、网络鸡汤），系统 `verifiable=false` 或 `trust_state=insufficient_evidence` 的比例 = 100%；②`Fabricated Classical Quote ≈ 0`：eval 中伪造名言被判定为「可溯源」的数量 = 0；③白名单外 `source` 一律 `verifiable=false`；④`backend/app` 中不存在硬编码 `verifiable=True`（当前 5 处，见上） |

### P0-2 现代问题能检索到古典思想

| 项 | 内容 |
|---|---|
| 要求 | 现代口语问题（如「同事抢了我的功劳」）能检索到相关原典 |
| 现状证据 | `rag_service.py:152-205` `SYNONYM_MAP`（实测 **52** 组现代→古词映射）；`_expand_synonyms`（`rag_service.py:503-509`）拼接扩展 query |
| 差距 | ①**C1 使 `retrieve()` 全链路失效**，现代问题→原典的正式入口返回空；②实测现代问题经 `retrieve_for_sage_chat` 得到的相似度极低（0.14–0.24），远低于 `RAG_SIMILARITY_THRESHOLD = 0.65`（`backend/app/core/config.py`），即**全部被判为低置信**；③`SYNONYM_MAP` 是人工小表，无 Modern Issue Ontology，无 scenario→concept 映射；④无 BM25、无 reranker、无 diversity |
| 实测（`retrieve_for_sage_chat`，top_k=3） | 「同事抢了我的功劳，我该不该跟他撕破脸？」→ 3 条，相似度 0.148/0.140/0.140；「我很努力却总不被领导认可」→ 0.22/0.176/0.176；「稳定但不喜欢的工作，要不要离开」→ 0.242/0.24/0.212 |
| 验收判据（可自动化） | ①`retrieval_gold.jsonl` 上 `Recall@1 / Recall@3 / Recall@5 / MRR` 四个指标均输出真实数值；②`Recall@5 >= 90%`；③现代问题（`modern_to_classic.jsonl`）经结构化后能映射出非空 `concepts[]`；④P50 < 1s、P95 < 3s（排除外部 LLM） |

### P0-3 答案不能空泛

| 项 | 内容 |
|---|---|
| 要求 | 回答必须落到具体原典与具体情境，不能是泛泛安慰 |
| 现状证据 | `prompt_templates.py:149-160` 有 `MODERN_APPLICATION_SYSTEM`（「建议要具体、可执行，不要空泛」）；`SageChatResponse.modern_takeaway` 字段 |
| 差距 | ①**该 prompt 无调用点**（`MODERN_APPLICATION_SYSTEM` / `MODERN_APPLICATION_USER` 在 `backend/app` 内无引用）；②无「空泛度」可测定义；③C3 使辩论发言**总能**拿到 3 条低相似度语料，模型据此生成的「引用」与问题无关却仍被标 `verifiable` |
| 可证伪判据 | 见 §3.1 |
| 验收判据（可自动化） | ①`Core Claim Evidence Coverage >= 95%`：答案中每个核心 claim 均绑定到至少 1 条 Evidence Pack 证据；②答案中 `modern_takeaway`/行动建议非空且含可执行动词（规则化检查）；③相似度低于阈值时输出「当前知识库没有检索到足够可靠的原典支持这一判断。」的比例 = 100% |

### P0-4 多学派差异真实存在

| 项 | 内容 |
|---|---|
| 要求 | 儒/道/墨/法 的差异来自各自原典，而非角色扮演 prompt |
| 现状证据 | `debate_classics.json` 按 `sage_key` 分桶；`rag_service.py:992-1009` 按 `sage_key` 过滤；`citation_validator.py:18-30` `SAGE_CLASSICS` 白名单 |
| 差距 | ①**C2**：`retrieve_for_sage_chat`（sage-chat 主路径）**无派别过滤**，实测孔子路径返回《道德经》《韩非子》《墨子》；②**C3**：`_debate_keyword_search` 兜底 `score=0.25`，任何问题都返回本派 3–4 条，即使语义完全无关；③各派语料仅 3–4 条，`hanfeizi` 4 条、`mozi` 4 条、`laozi` 4 条、`confucius` 3 条，**差异由 3–4 条语料决定**，样本量不足以支撑「多学派差异真实存在」 |
| 验收判据（可自动化） | ①`School Leakage < 1%`：`school_consistency.jsonl` 上跨派引用率；②每个学派在 V1 书目中拥有独立且可追溯的原典语料，且每条带 `school` 字段；③对同一问题，各派 Evidence Pack 的 `evidence_id` 交集为空（除明确标注的共用原典） |

### P1-1 原文 / 注疏 / AI 解释明确分层

| 项 | 内容 |
|---|---|
| 要求 | 三种文本类型在前端与数据层清晰分层，不得混同 |
| 现状证据 | 后端有 `doc_type`（`verse` / `commentary`，见 `rag_service.py:684-696`、`716-726`）；前端 `CitationSidebar.tsx:305` 有 `type: "commentary" \| "verse"`；`build_sage_chat_context`（`rag_service.py:1020-1048`）分节输出 |
| 差距 | ①**无 `text_type` 四值枚举**（`original`/`commentary`/`translation`/`modern_explanation`）；译文与原文在同一 `verse` 对象内，`translation` 与 `original` 并列存储（`lunyu.json` verse keys: `verse_id, original, translation, annotations, keywords, title`）；②**AI 解释与原典未分层**：`CitationSidebar.tsx:305` 只有二值；③`EvidenceDock.tsx:95-97` 的「释义」字段由 `thoughtCourtSession.ts:33` 用 `citation.commentary || "该原文为当前观点提供思想依据。"` 填充，**缺省时用模板话术冒充释义**；④前端无 A/B/C/D 可信等级 |
| 验收判据（可自动化） | ①每条 passage 有 `text_type ∈ {original, commentary, translation, modern_explanation}`；②前端 Evidence Drawer 对四类文本使用不同视觉层级与标签；③`modern_explanation` 类型不得出现在「经典原文」区域；④不存在以模板字符串充当释义的缺省路径 |

### P1-2 回答最终给现代行动建议

| 项 | 内容 |
|---|---|
| 要求 | 回答收口到可执行的现代行动 |
| 现状证据 | `thoughtCourtVerdict.ts:9` `actions: string[]`；`VerdictScroll.tsx:116-120` 渲染「今日行动」；`buildVerdict`（`thoughtCourtVerdict.ts:28-39`）按权重 `flatMap` 出 actions |
| 差距 | ①`actions` 来自 `report.actions[key]`，其内容由 LLM 生成，**无证据绑定**；②sage-chat 路径无 actions 字段，只有 `modern_takeaway`；③无「行动建议必须可执行」的判定 |
| 验收判据（可自动化） | ①最终回答含非空行动建议；②每条行动建议可追溯到至少 1 条 Evidence Pack 证据（Claim-Evidence Coverage 的一部分）；③`actions` 为空时前端明确提示证据不足，而非渲染空列表 |

### P1-3 支持用户继续追问

| 项 | 内容 |
|---|---|
| 要求 | 用户可对回答继续追问 |
| 现状证据 | `SageChat.tsx`（`onSubmit`、`history`、`messagesRef`）；`backend/app/api/debate.py` 提供 `intervene` / `stand` / `mutual-question`；`ChatSageRequest.history`（`backend/app/schemas/ai.py`） |
| 差距 | 追问链路上的 `history` 会被送入 LLM（`ai_service.py:472-476`），但**每轮重新检索、无会话级 Evidence Pack 复用**；追问后的引用仍走同一套弱校验 |
| 验收判据（可自动化） | ①多轮追问下 citation 校验规则与首轮一致；②追问不降低 `trust_state` 判定标准；③多轮会话中引用的证据可完整回溯 |

---

## 3. 关键要求的可证伪判据与反例风险

### 3.1 「答案不能空泛」— 当前可证伪判据与反例

**可证伪判据（建议纳入 GATE-4/GATE-5）**

- D1：答案中每条「思想结论」必须绑定 ≥1 条 `evidence_id`。可证伪：存在一条无绑定的核心结论即 FAIL。
- D2：绑定证据的检索相似度必须 ≥ `RAG_SIMILARITY_THRESHOLD`（当前 0.65）。可证伪：绑定证据相似度低于阈值即视为「无有效证据」。
- D3：当无有效证据时，答案必须包含固定拒答句「当前知识库没有检索到足够可靠的原典支持这一判断。」可证伪：缺失即 FAIL。
- D4：`modern_takeaway` / `actions` 非空且不含纯情绪安慰模板（规则化词表检查）。

**反例风险（已实测，非假设）**

| 反例 | 当前实际结果 | 风险 |
|---|---|---|
| 现代问题「同事抢了我的功劳，我该不该跟他撕破脸？」 | `retrieve_for_sage_chat` 最高相似度 **0.148**，全部 < 0.65 | 依据实际不相关，但流程不会拒答 |
| 同一问题走 debate 路径（韩非子） | 返回 3 条，相似度 0.0646 / 0.0394 / 0.0206 | 兜底 `score=0.25`（`rag_service.py:496`）使「无结果」分支不可达 |
| 「如何面对亲人的离世？」（与四家原典均无关） | 韩非子/墨子/老子/孔子**均返回 3 条** | 模型将基于无关语料生成「有出处的」安慰，正是 PROJECT-BRIEF 要禁止的「空泛 + 伪引用」 |

复现：

```powershell
cd backend
@'
import sys, asyncio
sys.path.insert(0, ".")
from app.services.rag_service import get_rag_service
rag = get_rag_service()
for sage in ["confucius", "laozi", "mozi", "hanfeizi"]:
    r = asyncio.run(rag.retrieve_for_debate_sage(sage, "如何面对亲人的离世？", top_k=3))
    print(sage, [(v["source"], round(v["similarity"], 4)) for v in r["verses"]])
'@ | .venv/Scripts/python.exe -
```

实际输出：

```
confucius: 3 条, sims=[0.0337, 0.0, 0.0]
laozi:     3 条, sims=[0.0281, 0.0, 0.0]
mozi:      3 条, sims=[0.0655, 0.0597, 0.0]
hanfeizi:  3 条, sims=[0.0646, 0.0394, 0.0206]
```

### 3.2 「多学派差异真实存在」— 当前可证伪判据与反例

**可证伪判据（建议纳入 GATE-6）**

- S1：`school_consistency.jsonl` 上跨派引用泄露率 < 1%。
- S2：同一问题下，各派 Evidence Pack 的 `evidence_id` 集合两两不相交（共用原典须显式标注）。
- S3：每个学派语料条数 ≥ 该学派 V1 书目核心篇章数，且每条带 `school` + `source_url`。
- S4：各派发言中的引用必须能在该派语料中逐字命中。

**反例风险（已实测）**

**风险 1 — sage-chat 主路径跨派泄露（C2）。** `retrieve_for_sage_chat`（`rag_service.py:914-990`）调用 `vector_search`（`rag_service.py:801-820`），后者 `collection.query` **不带 `where` 过滤**，因此返回全库结果。实测：

```powershell
cd backend
@'
import sys, asyncio
sys.path.insert(0, ".")
from app.services.rag_service import get_rag_service
rag = get_rag_service()
for q in ["上善若水，水善利万物而不争", "兼相爱，交相利", "法不阿贵，绳不挠曲"]:
    r = asyncio.run(rag.retrieve_for_sage_chat(q, top_k=5))
    print(q, [(v["source"], round(v["similarity"], 3)) for v in r["verses"]])
'@ | .venv/Scripts/python.exe -
```

实际输出：

```
上善若水，水善利万物而不争 -> [('《道德经·第八章》', 0.68), ('《道德经·第二十二章》', 0.17),
                               ('《论语·泰伯》', 0.149), ('《韩非子·有度》', 0.134), ('《论语·为政》', 0.132)]
兼相爱，交相利             -> [('《墨子·兼爱上》', 0.519), ('《论语·学而》', 0.189), ...]
法不阿贵，绳不挠曲         -> [('《韩非子·有度》', 0.52), ('《论语·子路》', 0.256), ...]
```

即：**在孔子对话路径中，《道德经》《韩非子》《墨子》都会作为「经典依据」被返回并展示**。这与 `citation_validator` 的 `SAGE_CLASSICS` 白名单**只在 debate 路径生效**形成不对称——sage-chat 的引用校验（`ai_service.py:352-411`）**完全不做归属检查**。

**风险 2 — 差异可能只是 prompt 差异。** 各派语料 3–4 条，且 `_debate_keyword_search` 对所有条目兜底 `score = 0.25`（`rag_service.py:493-496`），使「按派检索」在语义层面近似**固定返回该派全部语料**。当某个现代问题与四家原典均无关时，四派发言的差异主要由 `build_sage_system_prompt` 的角色设定产生，而非由各自原典证据产生。**这一点必须在 GATE-6 用 `school_consistency.jsonl` 的实测数字裁决，不能靠设计声明。**

---

## 4. 市场 / 竞品 / 用户痛点核验

### 4.1 核验能力声明

本次审计**无法完成任何外部市场核验**：

| 手段 | 结果 |
|---|---|
| `web_search` | 失败：`DeepSeek search has no API key for "DEEPSEEK_API_KEY"` |
| `web_fetch`（ctext.org） | 失败：`URL hostname "ctext.org" resolves to a non-public IP address` |

因此，**下述所有市场/竞品/用户痛点陈述均标记为「未核验假设」**，仅作为待核验线索记录，**不得**作为 GATE-0 事实或产品结论。

### 4.2 仓库内的市场自述（未核验）

| 陈述 | 出处 | 状态 |
|---|---|---|
| 竞品「识典古籍」= 研究型数据库，偏学术、无互动对话 | `frontend/app/about/page.tsx:107-112` | **未核验假设** |
| 竞品「Duolingo」= 语言学习 App，无中文经典内容 | `frontend/app/about/page.tsx:113-118` | **未核验假设** |
| 竞品「百度汉语 / 古诗文网」= 工具型网站，仅原文查阅 | `frontend/app/about/page.tsx:119-124` | **未核验假设** |
| 定位「大众化 × AI 对话 × 中文经典」的空白交叉点 | `frontend/app/about/page.tsx:126-130` | **未核验假设**（由上述三条推出） |
| 目标用户：现实困惑的年轻用户 / 教育内容运营者 / 文化 IP 机构 | `docs/hackathon/investor-qa.md:5-9` | **未核验假设**（无用户调研数据支撑） |
| 商业模型：B2B2C 试点（课程/账号包、内容 IP 合作、个人增强版） | `docs/hackathon/investor-qa.md:11-19` | **未核验假设** |
| 「大模型降低交互门槛，但普通问答容易空泛安慰、无法追溯」 | `docs/hackathon/investor-qa.md:23` | **未核验假设** |
| 下一步用 2–3 个试点验证留存、复问率、引用点击率、信任提升 | `docs/hackathon/investor-qa.md:51` | **计划，非结果**（尚无试点数据） |
| 数据来源为「本地经典原文 / 代表章节 / 注疏材料 / 安全问答缓存」 | `docs/hackathon/data-trust-statement.md:7-14` | **部分核验**：语料确实存在（143 条），但**无 `source_url` / `source_edition` / `license` 字段**，底本不可追溯（见 §4.3） |
| 数据来源指向 ctext.org / 维基文库 | `data/processed/classics_catalog.json` `sources` 数组 | **仅目录声明**：`sources` 列出了 ctext.org、维基文库等 3 个来源与 URL，但**未与任何具体 passage 建立映射**，无法据此证明某条原文出自某底本 |

### 4.3 与市场承诺直接冲突的现状（已核验）

| 对外承诺 | 出处 | 实际核验结果 | 判定 |
|---|---|---|---|
| 「每条引用均标注篇章出处，可一键跳转原文上下文阅读」 | `frontend/app/about/page.tsx:90-92` | 引用确有 `source` 字串，但**跳转不生效**：`SageChat.tsx:333-341` 打开 `/reader?highlight=...&source=...`，而 `frontend/app/reader/page.tsx:13-14` **只读取 `book` 参数**，`highlight` 与 `source` 被忽略，无法定位到具体篇章 | **未达成** |
| 「严格约束 AI 在经典原文范围内回答，杜绝『AI 编造孔子说过』」 | `frontend/app/about/page.tsx:85-87` | 无白名单、无 Quote Verifier、5 处硬编码 `verifiable: True`（`ai.py:146,159,208,265`、`ai_service.py:424`）；C3 使「无证据」分支不可达 | **未达成** |
| 「基于《论语》原文构建向量知识库」 | `frontend/app/about/page.tsx:80-81` | 索引 143 条中仅 107 条为论语；**C1 使该向量库在 `retrieve()` 路径不可用** | **部分未达成** |
| 「检索不到不硬编」 | `docs/hackathon/data-trust-statement.md:3, 27` | C3：`score=0.25` 兜底使「检索不到」永不发生 | **未达成** |
| 「先检索、再生成、可追溯」 | `README.md:89`、`docs/hackathon/investor-qa.md:32` | 主链路 `retrieve_for_sage_chat` 可用，但跨派泄露（C2）使「可追溯」的**归属**不可靠 | **部分未达成** |
| 「当前黑客松演示围绕本地整理材料展开……不等同于完整权威古籍数据库」 | `docs/hackathon/data-trust-statement.md:14` | **与实测一致**，表述诚实 | **达成** |

> 说明：`docs/hackathon/data-trust-statement.md:14` 的免责表述是仓库内**唯一**与真实语料规模相符的诚实声明。`frontend/app/about/page.tsx:126-130`「空白交叉点」等市场结论则缺乏可核验依据。

### 4.4 未核验项清单（需外部输入）

1. 竞品（识典古籍、Duolingo、古诗文网/百度汉语）的真实功能与定位 —— 需网络检索或人工调研。
2. 目标用户痛点是否真实、强度如何 —— 需用户访谈或问卷。
3. 「经典问答化」市场规模与付费意愿 —— 需市场报告。
4. 古籍底本的**版权与授权**状态 —— 需法务/出版方确认。**在获得授权确认前，不得将任何外部语料标记为 `verification_level = A` 或声明 `license`。**

---

## 5. 不确定性与风险清单

### 5.1 高不确定性

| # | 不确定性 | 影响 | 建议核验方式 |
|---|---|---|---|
| U1 | 竞品与市场结论全部未核验 | P0/P1 需求优先级可能建立在错误前提上 | PHASE 1 前完成一次人工竞品调研；在调研完成前，产品需求以 PROJECT-BRIEF 为唯一权威来源 |
| U2 | 107 条论语 vs V1 书目（论语/孟子/荀子/大学/中庸/道德经/庄子/墨子/韩非子/商君书/传习录/孙子兵法） | 覆盖率约 1/12 部；`Recall@5 >= 90%` 在现有语料上大概率不可达 | GATE-4 必须输出真实 Recall 数字，**不得调参至达标** |
| U3 | 古籍底本授权状态未知 | 无法合规声明 `license`；无法标记 `verification_level = A` | 需法务确认；在此之前一律标 `C`（来源可靠但尚未复核）或 `D` |
| U4 | 外部 LLM 不可用（实测 `LLM API_KEY 未配置，provider=agnes`） | 无法端到端验证 LLM 输出质量；所有 LLM 相关结论均未验证 | 需用户提供 key 或明确「LLM 路径未验证」 |
| U5 | 后端测试基线缺失（`jwt` 缺失） | 无法验证回归；「测试通过」无证据 | 由 backend/evaluation 修复 venv 依赖后重跑 |

### 5.2 高风险

| # | 风险 | 触发条件 | 后果 |
|---|---|---|---|
| R1 | **C1 被误判为「已修复」** | 仅修 `verse_no` 类型而未加回归测试 | `retrieve()` 再次静默返回 `[]` |
| R2 | **C3 兜底分数被保留** | 为「保证 demo 有输出」而保留 `score = 0.25` | 「检索不到不硬编」永久失效，对抗测试必然 FAIL |
| R3 | **跨派泄露被 prompt 掩盖** | 仅加强 `build_sage_system_prompt` 而不加检索层 `where` 过滤 | GATE-6 `School Leakage < 1%` 不可达 |
| R4 | **`verified` 默认 true 蔓延** | 新增 Evidence 字段但沿用 `citation.verifiable !== false` 模式 | 「未核验」被展示为「已核验」，直接违背核心可信承诺 |
| R5 | **为达标而降低断言** | 面对 `Recall@5 >= 90%` 等目标 | 违反 PROJECT-BRIEF 第十七章；必须在 eval 报告中如实标注不可达 |
| R6 | **123 部书目录被误当作语料规模** | `classics_catalog.json` 声明 123 部 | 对外宣称「支持 123 部古籍」而实际只有 1 部有内容 |

### 5.3 需用户决策的开放问题

1. **V1 语料范围是否收窄？** 现有 107 条论语 + 21 条百家语料无法支撑 12 部书目。建议 V1 先聚焦《论语》《道德经》《孟子》《庄子》《墨子》《韩非子》6 部，且明确每部的篇章覆盖目标。
2. **底本与授权如何解决？** 是否接受在无授权确认前，所有语料 `verification_level` 上限为 `C`（来源可靠但尚未复核），并据此设计 A/B/C/D 展示？
3. **是否允许接入外部 embedding？** 当前 `RAG_EMBEDDING_PROVIDER = "local"`（hash embedding）。正式检索质量依赖 Dense embedding，但接入外部模型涉及成本与合规。
4. **LLM 凭证是否提供？** 无 key 时所有 LLM 端到端验证均无法进行。
5. **市场结论是否需要补充调研？** 若要保留 `about/page.tsx` 的竞品对比，需要可核验来源；否则建议在 V1 中移除或标注为「产品观点」。

---

## 6. 本次审计的边界与未做事项

- 未修改任何产品代码、测试、数据、配置；`git status` 仅显示 `docs/kb-v1/`（审计文档）、`backend/wudian.db-shm`、`backend/wudian.db-wal`（SQLite 运行时副文件，`*.db` 已被 `.gitignore:25` 忽略）。
- 未提交、未推送、未部署。
- 未运行前端测试（属 evaluation/t6 范围）。
- 未修复 venv 依赖（属 backend/evaluation 范围）——因此**后端测试基线在本次审计中为「未验证」**。
- 未进行任何外部网络核验（环境限制，见 §4.1）。
- 未评估 RAG 的算法细节（属 t3 rag-expert）；未评估引用校验的完整漏洞面（属 t4 trust-verification）。本报告只覆盖**产品需求视角**的现状与差距。

---

## 7. 交付给 lead-architect 的输入摘要

**必须进入 `00-current-state.md` 的事实：**

- 语料真实规模：论语 107 条 / 20 篇；百家论道 21 条 / 9 位圣贤（孔子 3、老子 4、墨子 4、韩非子 4）；注疏 15 条且仅朱熹一家；Chroma 索引 143 条，已持久化。
- `classics_catalog.json` 声明 123 部书，仅论语有真实内容。
- `lunyu.json` 自述「512 章」与实际的 107 条不一致。
- 后端测试当前**无法运行**（venv 缺 `jwt`）。

**必须进入 `01-gap-analysis.md` 的缺陷：**

- C1（`retrieve()` 恒空）、C2（sage-chat 跨派泄露）、C3（检索兜底恒有结果）、C6（`verified` 默认 true + Evidence 字段缺失）。
- 三套重复的引用校验实现（`citation_validator.py` / `ai_service.py:352-411` / `debate_engine.py:86-111`）。
- 无 Trust State、无 Evidence Pack 白名单、无 Quote Verifier、无 `text_type` 四值枚举、无 A/B/C/D 可信等级。
- `MODERN_APPLICATION_SYSTEM` 提示词无调用点。

**必须进入 `02-architecture.md` 的约束：**

- 增量修复 C1/C2/C3，不得推翻 `RAGService`；`citation_validator.py` 需扩展而非替换。
- 检索层必须新增 `where` 学派过滤，与现有 `SAGE_CLASSICS` 白名单对齐。
- 新增字段须同时贯穿 backend schema → API 响应 → 前端 Evidence Drawer。
- 禁止沿用 `citation.verifiable !== false` 的默认放行模式。

**必须进入 `03-task-dag.md` 的 Gate 判据：**

- GATE-0：本节 §1–§5 的全部事实已列明，且标注了 U1–U5 未验证项。
- GATE-4：输出真实 Recall@1/3/5、MRR；若因语料规模不可达，如实标注。
- GATE-5：对抗套件中任何伪造名言通过验证即 FAIL。
- GATE-6：`School Leakage < 1%` 以实测为准，且 sage-chat 与 debate 两条路径都必须覆盖。
