# PHASE 0 审计：引用校验、可信判定与 Trust State 现状

- 任务：t4（PHASE 0 只读审计）
- 负责人：trust-verification
- 仓库：`D:\systemDir\Desktop\悟典`
- 分支 / HEAD：`codex/overall-optimization` / `64c8618`
- 审计日期：见本文件所在提交的 git 记录
- 审计范围：`backend/app/services/citation_validator.py`、`ai_service.py`、`debate_engine.py`、
  `prompt_templates.py`、`sage_persona.py`、`sage_cache.py`、`backend/app/api/{ai,debate}.py`、
  `backend/app/schemas/{ai,debate}.py`、`backend/tests/*`、`frontend/components/{sage,roundtable,thought-court}/*`、
  `frontend/lib/{api,roundtableFlow,thoughtCourtSession,thoughtCourtCases}.ts`
- 纪律声明：本审计只读；未修改任何产品代码、测试、数据或配置。复现脚本仅新增于
  `docs/kb-v1/audit/` 下，不写入产品目录。

## 0. 复现方式

本报告全部结论均可复现。脚本（新增，只读调用现有实现）：

```powershell
# 在仓库根目录
backend\.venv\Scripts\python.exe docs\kb-v1\audit\trust_repro.py    # 六类+四类对抗输入、三实现对比
backend\.venv\Scripts\python.exe docs\kb-v1\audit\trust_repro2.py   # 逐句证据、状态语义、跨派探针
backend\.venv\Scripts\python.exe docs\kb-v1\audit\trust_repro3.py   # 离线兜底引用可验证性
backend\.venv\Scripts\python.exe docs\kb-v1\audit\trust_repro4.py   # 前端硬编码 verified:true 核对
```

相关测试：

```powershell
# 在 backend 目录
python -m pytest tests/test_debate_classic_rag.py tests/test_debate_plan_completion.py tests/test_debate_sentence_evidence.py -q
# 实测输出：7 passed, 2 skipped, 8 subtests passed in 0.14s
# 其中 2 个 skip 原因为：ChromaDB collection is not available（见 §7 测试基线）
```

环境实测：`.venv` Python 3.12.10、chromadb 1.5.9、pydantic 2.13.4、fastapi 0.138.2。
真实 Chroma collection：`wudian_verses`，`count() = 143`。

---

## 1. 现状语义：`verifiable` 到底验证了什么

### 1.1 代码路径

| 实现 | 位置 | 是否被真实调用 |
|---|---|---|
| `CitationValidator.validate` | `backend/app/services/citation_validator.py:39-68` | 是（debate 链路） |
| `CitationValidator._match_citation` | `citation_validator.py:70-93` | 是 |
| `CitationValidator._check_classic_belonging` | `citation_validator.py:95-101` | 是 |
| `AIService._validate_citations` | `backend/app/services/ai_service.py:352-411` | 是（非流式 chat-sage，`:519`） |
| `debate_engine._validate_citations` | `backend/app/services/debate_engine.py:86-111` | **否 —— 死代码，无任何调用点** |

`_match_citation`（`citation_validator.py:70-93`）的实际判定只有两条：

1. 对每条 `rag_refs` 取 `ref["original"]`；
2. 做**双向子串匹配**，并在匹配前删掉 `。，？！；` 五种标点。

```python
# citation_validator.py:83-91（摘要）
if cit_original in ref_original or ref_original in cit_original:
    return True
cleaned_cit = cit_original.replace("。","").replace("，","").replace("？","").replace("！","").replace("；","").strip()
cleaned_ref = ref_original.replace("。","").replace("，","").replace("？","").replace("！","").replace("；","").strip()
if cleaned_cit in cleaned_ref or cleaned_ref in cleaned_cit:
    return True
```

关键事实：

- **`verifiable` 的唯一含义是「该 citation 的 `原文` 字符串与本次检索返回的某条 `original` 互为子串」。**
- `出处` / `source` 字段**从不参与文本匹配**，只被 `_check_classic_belonging` 用做「是否含本派书名关键词」的字符串包含检查（`citation_validator.py:95-101`）。
- 匹配集是**本次 `rag_refs`**，不是全库。未检索到的真实原典同样判 `False`（见 C8）。
- 没有归一化繁简、没有去除空白、没有相似度阈值、没有全库回查。

### 1.2 对抗输入实测结果（`trust_repro.py` 原始输出）

`rag_refs` 使用真实《论语》两条：`己所不欲，勿施于人。`（《论语·卫灵公》）、`学而时习之，不亦说乎？`（《论语·学而》）。

| 用例 | 输入 | 期望 | `citation_validator` 实测 | 判定 |
|---|---|---|---|---|
| C1 伪造古文 | `子贡问曰：同事抢功，当何以处之？` / 《论语·子贡》 | 不存在 | `verifiable=False`, `unverified` | 正确拦截 |
| C2 真实古文+错误出处 | `己所不欲，勿施于人。` / 《孟子·梁惠王上》 | 文本真、出处错 | `verifiable=False`（因 `孟子` 不在 confucius 的 `SAGE_CLASSICS` 名单） | **跨派检查偶然拦截，非出处正确性检查** |
| C3 同句不同标点 | `己所不欲 勿施于人` / 《论语·卫灵公》 | 应识别为同句 | `verifiable=False` | **误判（假阴性）** |
| C4 繁体版本 | `己所不欲，勿施於人。` / 《论语·卫灵公》 | 应识别为同句 | `verifiable=False` | **误判（假阴性）** |
| C5 部分引用 | `己所不欲` / 《论语·卫灵公》 | 部分引用 | `verifiable=True`, `all_verified` | 命中 |
| C6 网络鸡汤冒充孔子 | `你若不勇敢，没人替你坚强。` / 《论语·述而》 | 不存在 | `verifiable=False` | 正确拦截 |
| C7 真实古文+同派错误篇章 | `己所不欲，勿施于人。` / 《论语·学而》 | 出处错（正确为《卫灵公》） | **`verifiable=True`, `all_verified`** | **未拦截：出处错误被完全放过** |
| C8 真实古文+未检索到 | `三人行，必有我师焉。` / 《论语·述而》 | 文本真实存在于库 | `verifiable=False` | **误判（假阴性）** |
| C9 真实短句嵌入伪造长文 | `网络鸡汤：己所不欲，勿施于人。所以你要坚强，别让任何人看轻你。` / 《论语·卫灵公》 | 应判伪造 | **`verifiable=True`, `all_verified`** | **未拦截：伪造长文被接受为「原文」** |
| C10 空出处 | `己所不欲，勿施于人。` / `""` | 出处缺失 | **`verifiable=True`, `all_verified`** | **未拦截** |

C8 已独立验证：直接对真实 collection 做 `where_document={"$contains":"三人行，必有我师焉"}` 命中 **2** 条（`《论语·述而》`、`朱熹《论语集注》`），证明「文本在库里」但「未进入本次 rag_refs」→ `verifiable=False`。同一探针显示 `己所不欲，勿施于人。` 命中 3 条，`上善若水…` 命中 1 条（`《道德经·第八章》`），伪造古文与现代鸡汤命中 **0** 条。

**C2 的拦截来源已单独复核**（`trust_repro.py` 同源探针）：

| `出处` | `verifiable` | 拦截来源 |
|---|---|---|
| `《孟子·梁惠王上》` | `False` | `_check_classic_belonging`：`孟子` 不在 `SAGE_CLASSICS["confucius"]` |
| `《论语·学而》` | **`True`** | 通过 —— 同书错篇无法察觉（即 C7） |
| `""`（空） | **`True`** | 通过 —— 空出处直接放行（即 C10） |

即：C2 被拦下**不是**因为系统发现「出处错了」，而是因为「孟子」不属于孔子的书名白名单。
若把同一错误出处换成同书另一篇（C7），系统立即放行。**该拦截不具备出处正确性语义。**

### 1.3 C9 的机制解释（高危）

因为 `_match_citation` 使用**双向**子串匹配（`citation_validator.py:83`、`:90`），
只要伪造文本**包含**任一真实原文短句作为子串，整段伪造文本即被判 `verifiable=True`。
`ai_service._validate_citations`（`ai_service.py:390-395`）与死代码 `debate_engine._validate_citations`
（`debate_engine.py:103-106`）使用同一双向子串逻辑，同样可被绕过。

### 1.4 C10 的机制解释

`_check_classic_belonging`（`citation_validator.py:95-101`）：

```python
source = citation.get("出处", citation.get("source", ""))
classics = SAGE_CLASSICS.get(sage_key, [])
if not source or source == "无":
    return True      # ← 空出处直接放行
return any(c in source for c in classics)
```

空 `出处` 或 `"无"` → 直接 `return True`。实测：把孟子原文 `人皆有不忍人之心` 配空出处、
以 `confucius` 身份提交，得到 `verifiable=True, status='all_verified'`（`trust_repro2.py` §C）。

---

## 2. 「这句话存在」与「出处正确」是否被区分

**结论：完全没有区分。当前实现中不存在任何出处正确性判定路径。**

证据：

1. `Citation` 模型（`backend/app/schemas/ai.py:103-111`）只有 `id / source / original / verifiable` 四个字段，
   `verifiable` 是**单一布尔**，无法同时表达「存在」与「出处对」。
   `backend/app/schemas/debate.py:95-102` 同构。
2. `_match_citation` 全程只读 `原文`，从不读 `出处`（`citation_validator.py:71-93`）。
3. `_check_classic_belonging` 只做「书名关键词是否出现」的字符串包含，
   对 C7 这种「同书错篇」完全无感（`《论语·学而》` 含 `论语` → 通过）。
4. C7 实测：`verifiable=True, status='all_verified'`，且 `kept_source` 原样保留错误出处 `《论语·学而》`。
5. 全仓库不存在 `quote_exists`、`source_correct`、`correct_source`、`trust_state` 等标识符
   （grep 结果：仅 `security.py`/`auth.py` 中的 `verify_password` 与本题无关）。

PROJECT-BRIEF 第十一章要求输出 `quote_exists` 与 `source_correct` 两个独立指标 —— **当前为 0 实现。**

---

## 3. 白名单机制现状

**结论：不存在 Evidence Pack 白名单。LLM 可以引用检索结果之外的 source，且默认路径连「文本是否在检索结果里」都不检查。**

### 3.1 有约束的部分（且约束对象错位）

- `_match_citation` 把 `原文` 与本次 `rag_refs` 比对 —— 这构成一个**很弱的**「文本在本次检索结果内」约束，
  但它作用在 `原文` 上，不作用在 `出处` 上。
- `prompt_templates.SAGE_CHAT_SYSTEM_PREFIX`（`prompt_templates.py:97-103`）与
  `sage_persona.build_sage_system_prompt`（`sage_persona.py:366-368`）在提示词层面要求
  「绝不编造」「宁可填无」。**这是提示词约束，不是程序约束。**

### 3.2 无约束的部分（关键）

**`/api/ai/chat-sage` 的流式路径（默认路径）完全不做引用校验。**
`ChatSageRequest.stream` 默认 `True`（`backend/app/schemas/ai.py:98`），
前端固定传 `stream: true`（`frontend/lib/api.ts:1064`）。该分支：

1. 调用 `ai_service.chat_with_sage`（`ai_service.py:180-255`）**逐字流式转发 LLM 输出**，
   期间不解析、不校验、不拦截任何 `<<<QUOTE>>>` 内容；
2. 随后在 `backend/app/api/ai.py:133-167` **另行构造** citations：
   ```python
   # backend/app/api/ai.py:146,159
   "verifiable": True,     # ← 硬编码
   ```
   这些 citations 来自 `sage_result`（检索结果），**与 LLM 实际引用了什么无关**。

因此：**LLM 输出的 `<<<QUOTE>>>` 块（未校验）会被前端作为「原文」渲染，而 citations 面板展示的
是检索结果并硬编码 `verifiable: true`。** 二者可以完全不一致，UI 却呈现为「可溯源证据」。

同源问题：

- `ai_service._build_citations_from_cache`（`ai_service.py:413-426`）：`verifiable=True` 硬编码，注释自陈
  「缓存内容预设为可溯源」。
- `backend/app/api/ai.py:204-209`：缓存兜底 citations 同样硬编码 `verifiable: True`。
- `Citation.verifiable` 字段默认值为 `True`（`schemas/ai.py:109`、`schemas/debate.py:100`）——
  **缺省即视为通过**。

### 3.3 跨派泄露检查的有效性边界

`SAGE_CLASSICS`（`citation_validator.py:18-30`）仅按 sage_key 维护书名关键词。
实测（`trust_repro.py` §5）：把「上善若水」挂到 `《庄子·逍遥游》`、以 `confucius` 身份提交：

- 场景 A（检索未命中）：`verifiable=False`
- 场景 B（检索命中该文本）：`verifiable=False`，`kept_source` 仍为 `《庄子·逍遥游》`

即该检查能拦「完全不属于本派书名」的引用，但**拦不住 C7（同书错篇）与 C10（空出处）**。

---

## 4. Trust State 现状

**结论：无。`verified` / `citation_corrected` / `quote_relaxed` / `insufficient_evidence` 四个状态全部不存在，需新增。**

- 全仓库 grep `trust_state|trustState|insufficient_evidence|quote_relaxed|citation_corrected` → **无匹配**。
- 现有最接近的状态是 `CitationValidator.validate` 返回的三值字符串
  （`citation_validator.py:64-67`）：`all_verified` / `partial_verified` / `unverified`。
  它不是 Trust State：不含「存在但出处被纠正」「放宽匹配」「证据不足」语义。
- 该状态在 debate 链路被**全部丢弃**：`debate_engine.py:391,502,579,730` 均写作
  `validated_citations, _ = ...` / `vc, _ = ...`，状态值不进入任何响应模型
  （`SageSpeech` 无 status 字段，`schemas/debate.py:114-127`）。
- 空引用时状态语义错误：`validate("confucius", [], [])` → `status='all_verified'`
  （`all_verified` 初值 `True`，`citation_validator.py:42`），实测见 `trust_repro2.py` §B。
- 前端 `citationStatus`（`frontend/lib/thoughtCourtState.ts:7`）取值为
  `verified | partial | unavailable`，与 PROJECT-BRIEF 要求的四态**不等价**，
  且其 `verified` 由前端自行推算（`frontend/lib/thoughtCourtSession.ts:66`），非后端判定。

---

## 5. Claim-Evidence 绑定现状

**结论：无 claim 级绑定。现有 `sentence_evidence` 是「按句检索」，不是「claim→evidence→verification」，且其 `verifiable` 判定有严重误报。**

### 5.1 现有机制

`debate_engine._bind_sentence_evidence`（`debate_engine.py:130-155`）把发言按 `。！？` 切句，
**每句单独发起一次检索**，取 `top_k=1` 的第一条作为该句的「经典证据」：

```python
# debate_engine.py:149
verifiable=bool(refs and original != "无" and source != "无"),
```

该判定**不比较句子与检索到的原文之间是否存在任何文本关系**。只要本派索引非空且返回了结果，
`verifiable` 即为 `True`。

### 5.2 实测（`trust_repro2.py` §A）

| 输入句子 | `verifiable` | `similarity` | 绑定到的「证据」 |
|---|---|---|---|
| `己所不欲，勿施于人。` | `True` | 0.0748 | `《论语·泰伯》` 士不可以不弘毅，任重而道远。 |
| `今天天气不错，我打算去打球。` | **`True`** | 0.0796 | `《论语·卫灵公》` 君子谋道不谋食。 |
| `股价暴跌让我很焦虑。` | **`True`** | 0.0951 | `《论语·述而》` 用之则行，舍之则藏。 |

即：**与《论语》毫无关系的现代句子，也被标注为拥有「可验证的经典依据」。**
根因之一是 `rag_service._debate_keyword_search` 对零分条目强制赋分：

```python
# backend/app/services/rag_service.py:495-496
if score == 0:
    score = 0.25     # 保证辩论 prompt 总有上下文
```

该设计使本派索引非空时**几乎不会返回空结果**（实测无关 query 均返回 3 条），
从而 `refs` 恒非空 → `verifiable` 恒 `True`。

### 5.3 现有测试未覆盖该误报

`backend/tests/test_debate_sentence_evidence.py:69` 断言
`all(evidence.verifiable for evidence in speech.sentence_evidence)`，
但其 `FakeRAG`（同文件 `:14-31`）对任意 query 都返回同一条「包含 query 字样」的构造文本，
因此该断言无法暴露上述误报。

`is_low_confidence`（`rag_service.py:1077-1081`，阈值 `RAG_SIMILARITY_THRESHOLD=0.65`）
仅被 `ai_service.explain` 使用一次（`ai_service.py:101`），
**未用于 debate 链路，也未用于 `chat_with_sage_structured`**，因此上述低相关度不会被拦截。

---

## 6. 漏洞清单

严重度：blocker / high / medium / low。

| ID | 严重度 | 问题 | 证据 | 违背章节 |
|---|---|---|---|---|
| T-01 | **blocker** | 默认对话路径（SSE）不做任何引用校验，LLM 的 `<<<QUOTE>>>` 原样作为「原文」展示 | `schemas/ai.py:98`（stream 默认 True）、`api.ts:1064`（前端固定 true）、`ai_service.py:242-252`（逐字转发）、`SageChat.tsx:595-617`（渲染为「原文」标签） | 十、十二、十六 |
| T-02 | **blocker** | citations 的 `verifiable` 硬编码为 `True`，与 LLM 实际引用无关 | `api/ai.py:146,159,208`；`ai_service.py:424`；`schemas/ai.py:109`、`schemas/debate.py:100`（默认 True） | 十、十二、十四 |
| T-03 | **blocker** | 「文本存在」与「出处正确」无区分，出处正确性零校验 | `citation_validator.py:71-101`；C7 实测 `all_verified` + 保留错误出处 | 十一、十二 |
| T-04 | **high** | 双向子串匹配可被「伪造长文内嵌真实短句」绕过 | `citation_validator.py:83,90`；C9 实测 `verifiable=True` | 十、十六 |
| T-05 | **high** | 空 `出处`/`"无"` 使跨派检查直接放行 | `citation_validator.py:99-100`；C10 实测 | 十、十六 |
| T-06 | **high** | `sentence_evidence.verifiable` 不校验句子与原文关系，无关句恒判 True | `debate_engine.py:149`；`rag_service.py:495-496`；§5.2 实测 | 十三、十六 |
| T-07 | **high** | 无 Trust State；四态全缺，且 debate 链路丢弃已有 status | `citation_validator.py:64-67`；`debate_engine.py:391,502,579,730` | 十二 |
| T-08 | **high** | 前端把「未提供 verifiable」当作「已核验」展示 | `roundtableFlow.ts:181`（`similarity` 缺省→1）；`thoughtCourtSession.ts:35`（`!== false`→true）；`EvidenceDock.tsx:103`（显示「已核验」）；`CitationSidebar.tsx:293-298` | 十二、十四 |
| T-09 | **high** | 前端硬编码引用标 `verified: true`，其中 6/9 在当前语料中不存在 | `frontend/lib/thoughtCourtCases.ts:13,14,15,45,46,47,77,78,79`；`trust_repro4.py` 实测 9 条中 6 条未找到 | 十、十四、十六 |
| T-10 | **medium** | Mock 数据以 `verifiable: true` 冒充真实检索结果 | `frontend/lib/api.ts:2012,2038`；`roundtable/page.tsx:571,590`（异常时回退 mock，`similarity: 0.98` 硬编码） | 禁止 mock 冒充真实 RAG |
| T-11 | **medium** | 空引用被报告为 `all_verified` | `citation_validator.py:42,64-67`；`trust_repro2.py` §B 实测 | 十二 |
| T-12 | **medium** | 三处引用校验实现并存且语义有分歧，其中一处为死代码 | `citation_validator.py:70`、`ai_service.py:352`、`debate_engine.py:86`（无调用点）；`debate_engine._validate_citations` 缺少 `_check_classic_belonging`，故对 C2 会判 `True` 而 `citation_validator` 判 `False` | 增量升级一致性 |
| T-13 | **medium** | 繁简与空白未归一化导致假阴性 | C3、C4、C8 实测 `verifiable=False` | 十六（繁体、部分引用） |
| T-14 | **low** | 前端把 `verifiable` 折算成 `similarity`，制造虚假相关度数值 | `roundtableFlow.ts:181`；`CitationSidebar.tsx:214`（显示百分比） | 十四 |

### 复现步骤（关键三条）

```powershell
# T-01 / T-02：默认路径不校验
#   schemas/ai.py:98  stream: bool = Field(True, ...)
#   frontend/lib/api.ts:1064  stream: true
#   backend/app/api/ai.py:146  "verifiable": True   ← 硬编码

# T-04：伪造长文内嵌真实短句绕过双向子串匹配
backend\.venv\Scripts\python.exe docs\kb-v1\audit\trust_repro.py   # 见 [C9] 段

# T-09：前端 verified:true 与真实语料不符
backend\.venv\Scripts\python.exe docs\kb-v1\audit\trust_repro4.py  # 9 条中 6 条「语料中未找到」
```

---

## 7. 测试基线（可信层相关）

```powershell
# backend 目录
python -m pytest tests/test_debate_classic_rag.py tests/test_debate_plan_completion.py tests/test_debate_sentence_evidence.py -q
# => 7 passed, 2 skipped, 8 subtests passed in 0.14s
# 2 个 skip：tests/test_debate_classic_rag.py:15 与 :46 —— "ChromaDB collection is not available"
```

注意：skip 是因为测试进程内未启用 collection（与 `trust_repro.py` 中直接构造 `RAGService()`
得到 `count=143` 不矛盾，属测试夹具差异），**不是**通过。

现有可信层测试及其盲区：

| 测试 | 断言 | 盲区 |
|---|---|---|
| `test_debate_classic_rag.py:125-126` | `status == "all_verified"` 且 `verifiable is True` | 只测正例；无出处错误、伪造、繁体、部分引用反例 |
| `test_debate_plan_completion.py:54` | 跨派引用 `verifiable is False` | 依赖书名关键词不匹配；未覆盖空出处与同书错篇 |
| `test_debate_plan_completion.py:66` | 本派引用 `verifiable is True` | 正例 |
| `test_debate_sentence_evidence.py:69` | 所有句证据 `verifiable` | `FakeRAG` 恒返回构造文本，无法暴露 §5.2 误报 |
| `frontend/tests/hackathonReadiness.test.cjs:44-58` | 断言源码含「可溯源证据」「可溯源引用汇总」**字样** | 纯字符串存在性断言，不验证任何引用真实性 |

**结论：当前没有任何测试能在 PROJECT-BRIEF 第十六章的对抗输入下失败。**
即 GATE-5「任何明显伪造名言通过验证 → FAIL」目前**无测试可判定**。

---

## 8. 可信层最小增量设计约束（供 PHASE 5 使用，不推翻现有实现）

### 8.1 新增 `POST /api/knowledge/verify-quote`

现状：`backend/app/api/` 下**不存在** `knowledge.py`，无 `/api/knowledge/*` 路由
（grep `api/knowledge|knowledge.router` → 无匹配）。`main.py` 已注册 `ai/community/content/learning/exploration/auth/classics/debate`。

输入（对齐 PROJECT-BRIEF 第十一章）：

```json
{ "quote": "己所不欲，勿施于人。", "claimed_source": "《孟子·梁惠王上》" }
```

输出契约（**必须区分两个独立指标**）：

```json
{
  "quote_exists": true,
  "exact_match": false,
  "normalized_match": true,
  "source_correct": false,
  "correct_source": "《论语·卫灵公》",
  "similarity": 1.0,
  "match_type": "normalized",
  "candidates": [
    { "passage_id": "lunyu_15_24", "source": "《论语·卫灵公》",
      "original": "己所不欲，勿施于人。", "similarity": 1.0,
      "text_type": "original", "verification_level": "B" }
  ],
  "trust_state": "citation_corrected",
  "evidence_scope": "corpus",
  "verified_at": "<ISO8601>"
}
```

判定语义（必须分别计算、分别可测）：

| 字段 | 含义 | 判定规则 |
|---|---|---|
| `quote_exists` | **这句话在知识库里存在** | 在**全库**（非本次检索结果）中按归一化文本找到匹配 |
| `exact_match` | 逐字匹配 | 原样字符串相等 |
| `normalized_match` | 归一化后匹配 | 去标点/空白 + 繁简统一后相等 |
| `source_correct` | **出处正确** | 命中的 passage 的 `book_id/chapter_id` 与 `claimed_source` 解析结果一致 |
| `correct_source` | 正确出处 | 命中的 passage 的真实出处（仅在 `source_correct=false` 时有意义） |
| `trust_state` | 四态 | 见 §8.3 |

`quote_exists` 与 `source_correct` **必须是两个独立字段**，且允许出现
`quote_exists=true, source_correct=false`（即 PROJECT-BRIEF 的 `citation_corrected`）。

### 8.2 与现有 `citation_validator` 的复用与兼容（不推翻）

原则：**新增能力，保留旧接口；旧接口语义收紧但不删除。**

1. **保留** `citation_validator.py` 全部现有函数与 `SAGE_CLASSICS`（debate 链路仍在用）。
2. **新增** `backend/app/services/quote_verifier.py`：
   - 复用现有 `_match_citation` 的标点剥离思路，但**替换双向子串为「归一化后整句相等或前缀/后缀完整包含」**，
     以消除 T-04（C9）绕过；
   - 新增繁简归一化与空白归一化，消除 T-13；
   - 新增**全库回查**能力（区别于「本次 rag_refs」），以消除 T-01/C8 的假阴性；
   - 出处正确性单独实现，不回写进 `verifiable`。
3. **收紧** `citation_validator._match_citation`：将双向子串改为「单向、且要求匹配片段长度 ≥ 原文长度的一半」，
   并补齐空出处分支（`source` 为空时不得直接 `return True`）。
   → 这会改变 C2/C7/C9/C10 的判定，**必须同步新增回归测试**，并接受现有测试可能需按新语义更新（不得降低断言）。
4. **统一**三处实现：删除死代码 `debate_engine._validate_citations`（`debate_engine.py:86-111`，无调用点），
   `ai_service._validate_citations` 改为委托 `citation_validator`，消除 T-12 分歧。
5. **状态透传**：`SageSpeech` 新增可选 `trust_state` 字段（向后兼容，默认 `None`），
   `debate_engine` 把当前被 `_` 丢弃的 status 映射为四态后写入。
6. **修正默认值**：`Citation.verifiable` 的默认值从 `True` 改为**必填**（或默认 `False`），
   消除 T-02 的「缺省即通过」。此改动影响 `schemas/ai.py:109` 与 `schemas/debate.py:100`，
   需核查所有构造点（`api/ai.py:146,159,208`、`ai_service.py:424`、`debate_engine.py:149,398,504,581,732`）。
7. **前端**：`roundtableFlow.ts:181` 与 `thoughtCourtSession.ts:35` 不得再用 `verifiable !== false`
   推断「已核验」；改为消费后端显式 `trust_state`，未知时显示「未核验」。
   `thoughtCourtCases.ts` 的 9 条硬编码 `verified: true` 必须改为经后端核验或降级标注（T-09）。

### 8.3 Trust State 四态映射（新增）

| 状态 | 触发条件 |
|---|---|
| `verified` | `quote_exists=true` 且 `source_correct=true` |
| `citation_corrected` | `quote_exists=true` 且 `source_correct=false`（返回 `correct_source`） |
| `quote_relaxed` | 仅归一化后匹配（`exact_match=false`，`normalized_match=true`） |
| `insufficient_evidence` | `quote_exists=false`，或知识库中无任何候选；**此时禁止编造古文，必须输出 PROJECT-BRIEF 第十二章的拒答文案** |

---

## 9. 不确定性与未核验项

- 本审计未运行真实 LLM（`backend/.env` 未配置对应 `API_KEY`，启动日志提示
  `LLM API_KEY 未配置，provider=agnes`）。因此 T-01 中「LLM 实际会输出什么」属**代码路径推导 + 前端渲染路径核对**，
  非端到端实跑观测。**标注为未端到端验证。**
- `stream_round1/round2` 的 SSE 路径（`debate_engine.py:480-521,553-602`）确实调用了
  `_validate_sage_citations`（`:502,579`），与 chat-sage SSE 不同；但 `sentence_evidence`
  仍按 §5.2 误报。该差异已在 T-06 中体现。
- 本报告未评估 A/B/C/D 数据质量等级的实际赋值（属 classical-knowledge / 前端任务范围）。
- 未核验：`frontend/lib/roundtableData.ts` 中 mock 引用的其余条目是否全部存在于语料；
  本报告只核对了 `thoughtCourtCases.ts`（9 条）。
- 未核验：PROJECT-BRIEF 要求的 `SourceVerifier`、`CitationWhitelist` 是否应复用现有
  `_check_classic_belonging` 还是新建；这属 PHASE 5 设计决策，本报告只给约束不给定论。

---

## 10. 结论摘要

1. 当前 `verifiable` 的语义是 **「该原文与本次检索结果互为子串」**，
   **既不等于「这句话存在」，也不等于「出处正确」**。
2. **「文本存在」与「出处正确」两个指标当前完全未区分**，出处正确性零校验（PROJECT-BRIEF 第十一章为 0 实现）。
3. **无 Evidence Pack 白名单**；默认对话路径（SSE，`stream` 默认 `True`）**不做任何引用校验**，
   且 citations 的 `verifiable` 被硬编码为 `True`。
4. **无 Trust State**，四态全缺，需新增；debate 链路还把已有的三值 status 丢弃。
5. **无 Claim-Evidence 绑定**；`sentence_evidence` 是逐句检索，且对无关句子恒判 `verifiable=True`。
6. 六类对抗输入中，**明确伪造的用例存在真实绕过**（C9 内嵌绕过），
   且 **C7（同书错篇）与 C10（空出处）被完全放过**。
7. 前端存在 **6/9 硬编码 `verified: true` 的引用在当前语料中不存在**，
   以及「缺省即视为已核验」的展示逻辑。
8. 现有测试**无法在第十六章对抗输入下失败**，GATE-5 当前不可判定。

以上第 1–8 条均为 PHASE 5 Trust Layer 的**输入约束**，不构成实现。
