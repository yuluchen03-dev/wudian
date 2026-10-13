# RM-008 — `RAGReference.text_type` 缺口与保真 OPEN 项评估

- **任务**：`t7` / DSH-RM-008
- **执行者**：classical-knowledge（古籍知识工程师）
- **attempt**：`ca50fe2b-6b60-4b6c-b0c8-d1c0b7f1cf40`
- **仓库**：`D:\systemDir\Desktop\悟典`，分支 `codex/overall-optimization`，HEAD `34afd1d`
- **约束**：本次为**只读评估**。未修改任何源文件、测试、Gold、`TARGETS` 或冻结指标函数；未提交、未推送。
- **Chroma 安全**：所有运行时探针均把 `CHROMA_PERSIST_DIR` 指向 `shutil.copytree` 出来的临时副本，从未打开生产库。
  生产 `backend/chroma_db/chroma.sqlite3` SHA-256 探针前后一致：
  `4c97b5d03991e436457206d7d26682c71c634d2c09f93f639e769172479eda31`（before == after）。

## 0. 结论摘要（TL;DR）

| 项 | 结论 |
|---|---|
| **`text_type` 缺口** | **代码缺口确认存在**，且**不是潜在限制**：已构造出**真实生产信任绕过**（注疏被判 `verified`）。 |
| **严重级别** | **高（blocker 级安全缺陷）**，但**当前未被任何冻结 Gate 度量捕获**，且**无生产展示消费者**。 |
| **本轮动作** | 按任务要求**只评估、不修**。已给出精确复现与最小修复方案，交由队长排期独立实现任务。 |
| **RFC-1** | **OPEN**。代码与数据集状态未变，证据复核通过。 |
| **RFC-2** | **OPEN**。运行时复现确认 3 条真实短句仍判 `quote_relaxed`（不可展示）。 |
| **RFC-3** | **OPEN**。两表实测规模 148 vs 47；但 `FIX-001-FINAL-REVIEW.md:220` 的举例**部分不实**，见 §5.4。 |
| **EVAL-FIDELITY-001** | 接线**属实且有效**（11 项测试通过）；但它**不覆盖** L1/L2 判定，§6 给出精确的"证明/未证明"边界。 |

**给队长的建议**：把 §3.3 列为**独立阻塞安全实现任务**（不是夜间重构）；RFC-1/2/3 保持 OPEN，**本轮不自动关闭**。

---

## 1. 问题 1 — `citation_guard` 是否仍无法区分原典/注疏（L1/L2）？

**是。缺口仍在，且回退语义是"缺失即当作 L1"。**

### 1.1 精确代码路径

`backend/app/services/citation_guard.py:377-406`，位于 `guard_citations()` 主循环内：

```python
377        # CONTRACT-001 v2 §3.1/§3.2/§4：
378        #   完整性门 = 非片段（len(N(q)) >= MIN_FULL_QUOTE_CHARS）
379        #   L1 判定  = 支持该引文的 ref 是否为原典（text_type == "original"）
380        #
381        # ⚠️ 已知限制（如实记录，不掩盖）：`RAGReference` 目前**没有
382        # `text_type` 字段**，rag_service 也未传播它，因此本函数**无法**从 refs
383        # 判断 L1。这里的处理是：ref 显式带 text_type 时按它判定；缺失时**保守
384        # 视为 L1**（否则 citation_guard 将永远拿不到 verified，等于改变既有行为）。
385        # 后果：**RC4（注疏不得判 verified）在 citation_guard 这条路径上尚未强制**，
386        # 仅由契约的权威实现 `quote_verifier.verify_quote` 强制。
387        # 该缺口已登记为待办（需向 RAGReference 传播 text_type）。
388        _supporting = None
389        for _ref in refs:
390            _ref_orig = str(_ref.get("original", ""))
391            _qn = normalize_text(original)
392            if _qn and _qn in normalize_text(_ref_orig):
393                _supporting = _ref
394                break
395        is_l1 = True
396        if _supporting is not None and _supporting.get("text_type") is not None:
397            is_l1 = _supporting.get("text_type") == "original"
```

该 `is_l1` 随后进入 `trust_state.decide_trust_state(..., is_l1=is_l1)`（`citation_guard.py:399-406`），
而 `decide_trust_state` 的规则 3 是 `citation_guard` 拿到 `verified` 的**唯一**路径
（`backend/app/services/trust_state.py:123`）：

```python
123    if exact_match and completeness_gate and is_l1:
124        return "verified"
```

### 1.2 缺失 `text_type` 时的确切回退行为

- `_supporting` 为**首条**其 `original` 归一化后包含引文的 ref（`citation_guard.py:388-394`）；
  注意这里匹配的是 `ref["original"]`，与生产 ref 字典的键一致。
- **回退点**：`citation_guard.py:395` 无条件 `is_l1 = True`。
  第 396-397 行只在 `text_type` **存在且非 `None`** 时才改写它。
- 因此三种输入形态的行为：

| ref 形态 | `_supporting.get("text_type")` | `is_l1` | 说明 |
|---|---|---|---|
| 无 `text_type` 键（**生产形态**） | `None`（`.get` 缺省） | **`True`** | 注疏被当作原典 |
| `text_type=None` | `None` | **`True`** | 同上，`is not None` 为假 |
| `text_type="commentary"` | `"commentary"` | `False` | 唯一能拦住的形态 |
| `text_type="original"` | `"original"` | `True` | 正确 |

即：**回退方向是"缺失 ⇒ 放行"，不是"缺失 ⇒ 拒绝"。** 这与 `trust_state.py:94-96` 自己写明的纪律
（"默认值取保守方向 … 调用方若未显式提供这两项，就拿不到 `verified`"）**相反**——
`guard_citations` 作为调用方，把本该保守的 `is_l1` 显式传成了 `True`。

### 1.3 运行时实测（`deliverables/kb-v1/rm008-probe.py`）

对同一条**朱熹《论语集注》注文**（27 字，过完整性门）跑生产 `guard_citations`：

| 用例 | `trust_state` | `verifiable` | `is_displayable_as_classic` |
|---|---|---|---|
| **生产 RAGReference 形态（无 `text_type`）** | **`verified`** | `true` | **`true`** |
| 同一 ref 带 `text_type="commentary"` | `quote_relaxed` | `true` | `false` |
| 同一 ref 带 `text_type=None` | **`verified`** | `true` | **`true`** |

对照：**契约的权威实现** `quote_verifier.verify_quote`（`quote_verifier.py:635` 用
`getattr(attribution_source, "text_type", None) == "original"`，因 `CorpusEntry` 真的带 `text_type`，`quote_verifier.py:157`）对同一批注文**正确**返回 `quote_relaxed`：

```
'人性皆善而觉有先后后觉者' -> quote_relaxed exists=True exact=True src_ok=True
'学之为言效也'            -> quote_relaxed exists=True exact=True src_ok=True
```

**两条路径对同一输入给出不同 verdict**——`quote_verifier` 守住了 RC4，`citation_guard` 没有。

---

## 2. 问题 2 — 真实爆炸半径：所有把 refs 喂进 `guard_citations` 的生产调用点

`guard_citations` 在**整个仓库只有一个生产调用点**（测试除外）：

### 调用点 A（唯一）— `backend/app/services/ai_service.py:397-414`

```python
397    def _validate_citations(
398        self, citations: List[dict], rag_refs: List[dict]
399    ) -> tuple[List[Citation], bool]:
400        """Validate citations through the shared CitationGuard for both transports."""
401        from app.services.citation_guard import guard_citations
402
403        guarded, status = guard_citations(citations, rag_refs=rag_refs)
```

`whitelist` 未传 → `None` → 白名单本就不启用。**refs 是唯一的信息来源**，所以 `text_type` 缺口在这里**必然生效**。

该函数有 **3 个生产调用点**，全部来自 `sage_result`：

| # | 位置 | refs 来源 | 注入的 ref 类型 |
|---|---|---|---|
| A1 | `ai_service.py:246`（`chat_with_sage`，流式） | `ai_service.py:245` `verses + commentaries` | **L1 + L2** |
| A2 | `ai_service.py:426`（`_build_citations_from_cache`，缓存/降级路径） | 由 `ai_service.py:434` / `:506` 传入 `sage_result["verses"] + ["commentaries"]` | **L1 + L2** |
| A3 | `ai_service.py:532`（`chat_with_sage_structured`，非流式） | `ai_service.py:526-530` `verses + commentaries` | **L1 + L2** |

三者都追溯到 `rag_service.retrieve_for_sage_chat`，其**注释明确区分**两类结果
（`rag_service.py:1156-1161`），并在 `rag_service.py:1194-1203` 把 `doc_type == "commentary"` 的注疏放进
`commentaries`，字段为 `verse_id / original / commentary / chapter / source / similarity` ——
**没有 `text_type`**。`ai_service.py:499` / `:526-530` 把两类**拼进同一个 refs 列表**，丢失类型区分。

### 2.1 生产可达性实测（`deliverables/kb-v1/rm008-probe-reach.py`）

用生产 Chroma 的**临时副本**跑真实 `retrieve_for_sage_chat`，再对每条注疏跑生产 `guard_citations`：

| 查询 | `n_verses` | `n_commentaries` | 注疏 ref 带 `text_type`？ | 注疏 verdict |
|---|---|---|---|---|
| `学而时习之` | 5 | **5** | `false` | 5/5 **`verified` / `displayable_as_classic=true`** |
| `己所不欲勿施于人` | 5 | **5** | `false` | 5/5 **`verified` / `displayable_as_classic=true`** |
| `朱熹如何解释学而时习之` | 4 | **5** | `false` | 5/5 **`verified` / `displayable_as_classic=true`** |
| `什么是恕道` | 5 | 0 | — | 不适用 |

**4 条查询里 3 条真的把 5 条 L2 注疏送进了 `guard_citations`，并全部判 `verified`。**
这不是理论推演——注疏语料确实存在（`backend/data/commentaries/lunyu_zhuxi.json` 15 条，
已索引；`load_corpus()` 实测 `{original: 128, commentary: 15}`），且**默认进入 sage-chat 检索结果**。

### 2.2 逐调用点的错误 trust verdict 判定

| 调用点 | 缺失 `text_type` 能否产生**错误** trust verdict？ | 说明 |
|---|---|---|
| **A1**（流式 `chat_with_sage`） | **能，真实可达** | 模型若引用注文并声称 `《论语集注》`，`source_correct=True` + 过门槛 + 回退 `is_l1=True` → `verified`、`verifiable=true`。`ai_service.py:247-252` 只在 `not all_verified` 时才降级，`verified` 不触发任何告警。 |
| **A2**（缓存/降级路径） | **能，真实可达** | 同 A1；缓存引文同样是注文时重演。此路径恰是 LLM 不可用时的兜底，用户最易信。 |
| **A3**（非流式结构化） | **能，真实可达** | `ai_service.py:535-548` 的"诚实降级"以 `verifiable` 为门；L2 被判 `verifiable=true`（且 `verified`）→ **不降级**。 |

**结论：三者都是真实生产信任绕过，不是"当前未触发的限制"。**

---

## 3. 问题 3 — 升级为阻塞安全任务 + 具体复现

### 3.1 为什么定级为"真实生产信任绕过"而不是潜在限制

三条同时成立：
1. **可达**：L2 注疏是 `retrieve_for_sage_chat` 的**默认返回内容**（§2.1，15 条索引，3/4 查询命中）；
2. **有错误判定**：`guard_citations` 判 `verified` / `verifiable=true`，而权威实现 `quote_verifier` 判 `quote_relaxed`（§1.3）——这是**分歧**，不是口径差异；
3. **影响用户可见输出**：`Citation.verification_status`（`schemas/ai.py:118-125`）直接回传 API，
   且 `verifiable=true` 会让 `ai_service.py:535-548` 的诚实降级**不触发**。

### 3.2 但同时必须如实说明的三条限制（避免夸大）

- **无生产展示消费者**：`is_displayable_as_classic` 全仓库**没有任何生产调用点**
  （只出现在 `trust_state.py` 定义与 `run_eval.py` / 测试中）。所以"注疏被当经典原文展示"
  目前**是 API 契约层的错误标注**，不是已渲染的 UI 错误。
- **无冻结 Gate 捕获**：`fabricated_classical_quote`（GATE I）只统计
  `expected.quote_exists=False` 且 `pred.verifiable=True`（`metrics.py:157`）。
  注疏在语料中**真实存在**，故**不落入**该分母——**GATE I 全绿与 L1 缺口可以共存**。
  **这是本次评估最重要的口径结论：任何当前绿色指标都不能证明 L1 已被强制。**
- **口径冲突未决**：`is_verifiable`（`trust_state.py:150-162`）把 `quote_relaxed` 也视为 `verifiable`。
  所以即便修好 L1，L2 注疏仍会 `verifiable=true`，只是 `trust_state` 从 `verified` 变 `quote_relaxed`。
  "L2 是否允许 `verifiable=true`"是**合同问题**，超出本任务范围，需队长/合同负责人裁决（见 §7-I2）。

### 3.3 具体复现（最小、确定性、无网络）

见 `deliverables/kb-v1/rm008-probe.py`，输出存 `deliverables/kb-v1/rm008-probe-out.txt`：

```
backend\.venv\Scripts\python.exe deliverables\kb-v1\rm008-probe.py
```

核心断言（生产形态 ref，无 `text_type`）：

```python
from app.services.citation_guard import guard_citations
from app.services.trust_state import is_displayable_as_classic

L2 = "此章圣人之恕道，推己及人，己所不欲，勿施于人，乃终身可行之恕也。"  # 朱熹注文
ref = {"verse_id": "commentary:15.24", "original": L2, "commentary": "",
       "chapter": "", "source": "《论语集注》", "similarity": 0.9}   # 无 text_type

g, _ = guard_citations([{"id": "引1", "source": "《论语集注》", "original": L2}], rag_refs=[ref])
assert g[0].trust_state == "verified"                      # 实际观察值（RC4 应禁止）
assert is_displayable_as_classic(g[0].trust_state) is True # 实际观察值（RC4 应禁止）
```

加 `ref["text_type"] = "commentary"` 后同一断言变为 `quote_relaxed` / `False`，
**证明缺口确实由缺失 `text_type` 造成**。

端到端可达性复现（需生产 Chroma 副本，脚本已自动隔离）：

```
backend\.venv\Scripts\python.exe deliverables\kb-v1\rm008-probe-reach.py
```

### 3.4 建议的最小修复（**不在本任务实施**，交队长排期）

按"增量、不推翻架构"原则，建议**单点 + 传播**：

1. **`schemas/ai.py:12-26`** `RAGReference` 增加 `text_type: Optional[str] = None`
   （**不要**设默认 `"original"`——默认即放行会原样复现缺口；默认 `None` 让缺省落在**拒绝**侧）。
2. **`citation_guard.py:395`** 把无条件 `is_l1 = True` 改为 `is_l1 = False`，
   并把第 396-397 行改为：仅当 `text_type == "original"` 时置 `True`。
   → 这样"缺失 ⇒ 不 verified"，与 `trust_state.decide_trust_state` 的保守默认一致。
3. **`rag_service.py:1196-1203` / `:1225-1232`** 在 `verses` / `commentaries` 字典里显式写
   `text_type: "original"` / `"commentary"`；`ai_service.py:499` / `:526-530` 透传该字段。
4. **回归测试**：把 §3.3 断言写进 `backend/tests/test_citation_guard.py`；
   并**先看到 RED**（当前必红）。
5. **必须同时评估的风险**：第 2 步会**改变既有行为**——任何依赖 `guard_citations` 在
   L1 形态下拿到 `verified` 的既有断言需复核；`backend/tests/test_eval_fidelity.py:205-219`
   的用例**只断言忠实回传、不断言 `verified`**，故不会因该修改而失败，但应在实现时确认。
6. **不得**顺手改 `metrics.py`、`TARGETS`、Gold 或 `is_verifiable` 语义（后者是合同问题）。

---

## 4. 问题 4 — RFC-1 / RFC-2 / RFC-3 当前真实状态

**三者全部保持 OPEN。本轮未关闭任何一项，也未做任何相关修改。**

`docs/kb-v1/DSH-CURRENT-STATE.md:185-188` 与 `AGENTS.md:104-106` 仍将其列为必须显式的未决事项。

### 4.1 RFC-1 — 冻结 `exact_match` / `expected.trust_state` 标签冲突（**OPEN，确认**）

**现状（原样引用 `eval/quote_verification.jsonl`）**：

```json
{"id": "qv-0016", "quote": "己所不欲勿施于人", "claimed_source": "《论语·卫灵公》",
 "expected": {"quote_exists": true, "exact_match": false, "source_correct": true,
              "correct_source": "《论语·卫灵公》", "trust_state": "quote_relaxed"}}
{"id": "qv-0017", "quote": "己所不欲，勿施於人。", "claimed_source": "《论语·卫灵公》",
 "expected": {"quote_exists": true, "exact_match": false, "source_correct": true,
              "correct_source": "《论语·卫灵公》", "trust_state": "quote_relaxed"}}
{"id": "qv-0018", "quote": "勿施于人", "claimed_source": "《论语·卫灵公》",
 "expected": {"quote_exists": true, "exact_match": false, "source_correct": true,
              "correct_source": "《论语·卫灵公》", "trust_state": "quote_relaxed"}}
```

**冲突仍成立，复核证据**：

- 冻结分子 `eval/scripts/metrics.py:98`：
  `ok = bool(pred.get("exact_match")) and bool(rec["expected"].get("quote_exists"))`
  —— **从不读** `expected.exact_match`。故 §6.2 的判断（该字段无消费者）**仍正确**。
- 因此 `quote_exactness == 1.000` **不能**作为 `exact_match` 判定正确的证据；
  更严格的口径反而会掉到 0.9444 / 0.8889（`contracts/QUOTE-VERIFICATION-CONTRACT.md:372-374`）。
- **RFC-1 未决的实质**（数据集 / 公式 / 字段三选一）**未被解决**，且**不属本任务范围**。
  `qv-0018`（4 字 `勿施于人`）同时压在 RFC-1 与 RFC-2 上。

> 诚实说明：本次**未重新运行 `run_eval.py`** 复算 1.000。上表为读取数据集与冻结公式后的
> 静态复核；运行态数值属 RM-011 冻结评测范围，本评估不据其宣称 PASS。

### 4.2 RFC-2 — 短完整句的完整性规则（**OPEN，运行时已复现**）

**代码现状**（`quote_verifier.py:55`，`citation_guard` 亦复用该常量）：

```python
55: MIN_FULL_QUOTE_CHARS = 6
```

**运行时复现**（本次实测，权威路径 `verify_quote`）：

```
君子不器   -> quote_relaxed  quote_exists=True exact_match=True match_type=partial
三十而立   -> quote_relaxed  quote_exists=True exact_match=True match_type=partial
过则勿惮改 -> quote_relaxed  quote_exists=True exact_match=True match_type=partial
```

三条**真实完整句**因 4–5 字被完整性门挡住，永久无法 `verified` / 不可展示——
与 `contracts/QUOTE-VERIFICATION-CONTRACT.md:187-193` 的表格**逐行一致**。
合同已明确"骤降门槛到 4 不是解法"（会让 `勿施于人` 变可展示，破坏 aq-0010），
正确方向是句界/覆盖度规则。**该 RFC 未决，现状按原样执行并如实记录。**
（`contracts/...:192-193` 另列 `人焉廋哉`、`传不习乎`，本次未逐条复现，标注为**未验证**。）

### 4.3 RFC-3 — 重复且不一致的 `_T2S` 表（**OPEN，实测确认，且证据需更正**）

**两表当前代码状态（原样引用，均未修改；`eval/scripts/metrics.py` 在 `git diff HEAD` 中无改动，确认仍是冻结态）**：

`eval/scripts/metrics.py:49-61`：

```python
49  # Traditional -> Simplified map for the characters that actually occur in this
50  # corpus and its adversarial variants.  Kept explicit rather than pulling a
51  # heavyweight dependency; extend as the corpus grows.
52  _T2S = str.maketrans({
53      "於": "于", "爲": "为", "為": "为", "說": "说", "樂": "乐", "學": "学",
54      "習": "习", "禮": "礼", "義": "义", "聖": "圣", "賢": "贤", "德": "德",
55      "無": "无", "與": "与", "己": "己", "惡": "恶", "愛": "爱", "親": "亲",
56      "靜": "静", "遠": "远", "過": "过", "國": "国", "時": "时", "書": "书",
57      "車": "车", "馬": "马", "見": "见", "言": "言", "語": "语", "問": "问",
58      "對": "对", "應": "应", "當": "当", "萬": "万", "歲": "岁", "風": "风",
59      "雲": "云", "處": "处", "從": "从", "來": "来", "會": "会", "後": "后",
60      "進": "进", "這": "这", "個": "个", "們": "们", "實": "实", "義": "义",
61  })
```

`backend/app/services/quote_verifier.py:80-116`（节选；完整表共 148 条）：

```python
80  #: 繁体/异体 → 简体。**不完整**，仅覆盖本语料常见字形。
81  #: 未覆盖字符不会误报（只会漏判 ``normalized_match``）。
82  _TRADITIONAL_TO_SIMPLIFIED: Dict[str, str] = {
83      # 虚词与高频字
84      "於": "于", "與": "与", "為": "为", "無": "无", "後": "后", "從": "从",
...
116 }
```

**实测差异（`deliverables/kb-v1/rm008-probe-rfc3.py`）**：

| 指标 | 值 |
|---|---|
| `backend` 表规模 | **148** |
| `eval` 表规模 | **47** |
| **仅 backend 映射**（eval 原样保留） | **106** 字 |
| **仅 eval 映射**（backend 原样保留） | **5** 字：`己 惡 爲 處 言` |
| **同字映射到不同结果** | **0** 条 |

- 两表**同时存在、规模相差 3 倍**，且**双向**存在对方没有的映射 → **"重复且不一致"属实**。
- 有趣的是 `己` 是**恒等映射**（`"己": "己"`），两表都写；`言` 也是 `"言": "言"`。
  这两个条目**无功能效果**，属冗余但无害。
- 因为两表映射目标无冲突，实际分歧表现为**单向漏映射**（某侧少转一批字）。

**一个必须更正的既有说法**：`docs/kb-v1/FIX-001-FINAL-REVIEW.md:220` 称

> "已造成真实假阴性（如 `溫`/`則` 未映射、`aq-0009` 繁体 `萬`/`爭` miss）"

实测（`rm008-probe-rfc3-out.txt`）：

| 字 | backend | eval | 判定 |
|---|---|---|---|
| `萬` | `万` | `万` | **两表都已映射**，不存在 miss |
| `爭` | 未映射 | 未映射 | **两表都未映射**（不是"表不一致"，是**两表共同缺字**） |
| `溫` | 未映射 | 未映射 | **两表都未映射**（同上） |
| `則` | 未映射 | 未映射 | **两表都未映射**（同上） |

即：`FIX-001-FINAL-REVIEW.md:220` 把**两类不同问题混为一谈**——
`萬` 的映射其实完好；`爭/溫/則` 属**共同覆盖不足**，不是 RFC-3 所定义的"两表不一致"。
在 `aq-0009`（`上善若水，水善利萬物而不爭。`）上两套归一化输出**完全相同**：

```
backend normalize_text : 上善若水水善利万物而不爭
eval    normalize_all  : 上善若水水善利万物而不爭
equal: True
```

`爭` 的漏映射在**两侧同时**发生，所以它造成的假阴性**不能**归因于 RFC-3，
而应是 RFC-3 之外的一个**表覆盖不足**问题。**建议在 RFC-3 文本里分开记录**，
避免后续修复者按"统一两表"去修却修不掉 `爭/溫/則` 这类假阴性（**修完仍红**）。

### 4.4 RFC 状态汇总

| RFC | 本轮复核结论 | 是否关闭 |
|---|---|---|
| RFC-1 | 冲突仍成立；`expected.exact_match` 仍无消费者 | **否，保持 OPEN** |
| RFC-2 | 3 条真实短句运行时复现仍不可展示 | **否，保持 OPEN** |
| RFC-3 | 两表 148 vs 47，双向不一致；但既有证据需更正（§4.3） | **否，保持 OPEN** |

---

## 5. 问题 5 — EVAL-FIDELITY-001 状态复核

### 5.1 接线属实（代码已逐行确认）

`eval/scripts/run_eval.py:186-209` `eval_adversarial()`：

```python
195    records = _load("adversarial_quotes")
196    refs = _production_refs()
197    preds = [_production_adversarial_prediction(r, refs) for r in records]
199    frozen = compute_fabricated_classical_quote(records, preds)
```

`run_eval.py:150-166`：

```python
159    from app.services.citation_guard import guard_citations, metric_prediction_from_guarded
161    quote, claimed = _extract_quote(rec)
162    guarded, _status = guard_citations(
163        citations=[{"id": rec.get("id"), "source": claimed, "original": quote}],
164        rag_refs=refs,
165    )
166    return metric_prediction_from_guarded(guarded[0])
```

`refs` 由 `run_eval.py:133-147` `_production_refs()` 从 `load_corpus()` 构造，
并**刻意只保留 `original` / `source`**（`:147` `return [{"original": e.original, "source": e.source} for e in load_corpus()]`），
**明确省略 `text_type`** —— 这正是 §1 的生产形态，注释 `:139-143` 亦如实说明。
映射函数 `citation_guard.py:262-288` 只做字段搬运，注释 `:266-268` 声明
"It does NOT re-run matching, source, completeness, L1 or trust-state logic"，与代码一致。

**验收测试**：`backend/.venv/Scripts/python.exe -m pytest tests/test_eval_fidelity.py -q`
→ **`11 passed`**（本次实测）。

### 5.2 它**证明了**什么

1. 冻结 `fabricated_classical_quote` 的 `pred.verifiable` **确实**来自生产
   `citation_guard.guard_citations`，而非 `_quote_prediction` 里的合成布尔值
   （`run_eval.py:129` 那个 `r.quote_exists and r.source_correct and r.match_type != "partial"`）。
2. 该链路走的是生产裁决函数，背后是 `trust_state.decide_trust_state` / `is_verifiable`。
3. 映射层**不重算**匹配、出处、完整性门、L1 或 trust-state（纯字段搬运，可审计）。
4. 若未来有人把 run_eval 改回合成 `verifiable`，`metric_prediction_from_guarded` 的
   `verdict_basis: "production citation_guard.guard_citations"`
   （`citation_guard.py:287`，断言见 `test_eval_fidelity.py:160`）会立刻失败。

### 5.3 它**不证明**什么（精确边界）

1. **不证明 L1/L2 被强制**。`_production_refs()` **故意不带 `text_type`**，
   于是 guard 走 §1.2 的回退 `is_l1 = True`。**adapter 忠实映射了这个回退**，
   所以它证明的是"生产裁决被如实消费"，**不是**"生产裁决正确"。
   两者常被混为一谈——本评估明确切开。
2. **不覆盖注疏类伪造**。`metrics.py:157` 的分母要求 `expected.quote_exists is False`；
   L2 注疏在语料中**真实存在**，**永不进入**该分母。故 **GATE I 为 0 与 L1 缺口并存**，
   §3.2 已述。
3. **不覆盖 `quote_exactness` / `source_attribution`**。这两项仍走
   `run_eval.py:177-178` 的 `_quote_prediction`（`quote_verifier` 路径），**不是** guard 路径。
   两条路径的 L1 行为**不一致**（§1.3），而这种不一致**没有任何指标度量**。
4. **不构成端到端生产验证**。`_production_refs()` 直接喂 `load_corpus()` 结果，
   **绕过**了 `rag_service.retrieve_for_sage_chat` 与 `ai_service._validate_citations`。
   真实生产链路的可达性由本评估的 §2.1 探针独立证明（**且结果比 harness 更糟**：
   生产 ref 真带 5 条注疏）。
5. **不涉及真实 LLM / 真实网络**。§2.1 的复现亦为本地检索 + 本地裁决，
   不含真实模型输出——**Q5 仍阻塞**。

### 5.4 EVAL-FIDELITY-001 状态判定

| 维度 | 状态 |
|---|---|
| "fabricated 指标已接线到生产 citation_guard" | **已确认（PASS）** |
| "接线覆盖 L1/L2 判定正确性" | **不成立**（§5.3-1） |
| "RAGReference 缺 `text_type` ⇒ RC4 未被统一强制" | **仍然成立，保持 OPEN** |

`docs/kb-v1/DSH-CURRENT-STATE.md:189-191` 对该项的表述**准确，无需修正**。

---

## 6. 本轮验证清单（可复查）

| # | 命令 | 结果 |
|---|---|---|
| 1 | `backend\.venv\Scripts\python.exe deliverables\kb-v1\rm008-probe.py` | 输出 `rm008-probe-out.txt`；L2 生产形态 → `verified` |
| 2 | `backend\.venv\Scripts\python.exe deliverables\kb-v1\rm008-probe-reach.py` | 孤立 Chroma 副本；3/4 查询真实命中 5 条 L2 并判 `verified` |
| 3 | `backend\.venv\Scripts\python.exe deliverables\kb-v1\rm008-probe-rfc3.py` | 表规模 148 vs 47；106/5 单向差异 |
| 4 | `python -m pytest tests/test_eval_fidelity.py -q`（cwd=`backend`） | **11 passed** |
| 5 | SHA-256 `backend/chroma_db/chroma.sqlite3` before/after | `4c97b5d0…da31` **两次一致** |
| 6 | `git diff --stat HEAD -- eval/scripts/metrics.py` | **无输出**（冻结文件未改） |
| 7 | `git status --porcelain` | 仅新增 `deliverables/kb-v1/rm008-*`（探针与本文档），源文件零改动 |

**未验证 / 未复现项（如实标注）**：
- 未运行 `run_eval.py` 复算 `quote_exactness`/`fabricated` 数值（属 RM-011 范围，本任务为只读评估）。
- `人焉廋哉`、`传不习乎`（合同 `:192-193`）未逐条运行时复现。
- 未验证真实 LLM 是否会**实际**引用注文（那需真实凭证，Q5 阻塞）；
  本评估证明的是**若模型引用注文，裁决必然错误**，以及注文**已默认进入** refs。
- `Q3`（语料授权/权威底本）、`Q5`（真实凭证）**未被本评估触及，保持阻塞**。

---

## 7. 建议的后续任务（供队长排期，**本轮不实施**）

| ID | 类型 | 内容 | 依赖 |
|---|---|---|---|
| **I1** | **阻塞安全实现** | 按 §3.4 六步修 `text_type` 传播与 `is_l1` 保守回退；**先写 RED 测试** | 本评估 |
| **I2** | **合同裁决（需人工）** | 裁决 `is_verifiable` 是否允许 L2 `verifiable=true`；决定是否新增 L1 gate | 合同负责人 |
| **I3** | 文档更正 | 修正 `FIX-001-FINAL-REVIEW.md:220` 对 `萬`/`爭` 的表述；在 RFC-3 中分出"共同覆盖不足" | 无 |
| **I4** | 指标补盲 | 评估是否需一条 L2 专用 Gate（当前 GATE I 结构上无法发现该缺口） | I2 |

**RFC-1 / RFC-2 / RFC-3 本轮一律保持 OPEN**，等待人工裁决，不自动关闭。

---

## 8. 诚实性声明

- 本评估未编造任何古籍原文、出处或版本信息；所引注文均来自仓库内
  `backend/data/commentaries/lunyu_zhuxi.json`，引文均来自 `eval/*.jsonl` 与源文件原文照录。
- 未声称任何人工复核、来源授权或生产密钥已获得；`Q3`/`Q5` 保持阻塞。
- 所有"当前状态"陈述均基于本轮实际读取的代码与运行的探针，不依赖旧会话摘要。
- 生产 Chroma 全程只读：仅 `shutil.copytree` 读取字节，指纹前后一致。
