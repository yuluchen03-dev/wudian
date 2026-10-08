# 引文校验合同（QUOTE-VERIFICATION-CONTRACT）

- **编号**：CONTRACT-001
- **版本**：**v2 — 已并入独立复核 RC1–RC8**
- **状态**：**FROZEN（待第二轮复核确认）**
- **范围**：`quote_exists` / `exact_match` / `source_correct` / `verifiable` /
  `is_displayable_as_classic` / `trust_state`
- **不动**：任何 `TARGETS`；任何失败 case；任何数据集条目

**评审记录**：v1 经独立、fresh-context、只读复核，结论为
**ACCEPT WITH REQUIRED CHANGES**（8 项）。本 v2 已逐条并入 RC1–RC8，
并保留复核提出的 3 项 RFC（§11）。

本文件是**语义合同**，不是实现说明。实现与本合同冲突时以本合同为准。

---

## 0. 为什么需要这份合同

同一输入在不同模块曾得到**互相矛盾**的判定：

| 输入 | `quote_verifier` | `citation_guard`（修复前） |
|---|---|---|
| 「勿施于人」 | `match_type=partial`, `quote_relaxed` | `verifiable=True`, `verified` |

且 `exact_match` 当前要求「引文 == **整条** passage」（`quote_verifier.py:570`），
而语料是**按 passage（章/verse）存储**：`lunyu:15.24` 的 `original` 已含
`子贡问曰：「…」子曰：「其恕乎！己所不欲，勿施于人。」`。
因此**任何单句引用都不可能** `exact_match=true`，而
`eval/quote_verification.jsonl` 明确期望单句引用 `exact_match=true`。
实现与数据集互相矛盾，实测 `quote_exactness` 只有 0.333（6/18）。

> 语料构成（修正 v1 的「整章」措辞）：共 143 条 —— 128 条 `text_type="original"`
> （论语 110、道德经/墨子/韩非子 各 4、李白诗文 2、苏轼/范仲淹/王安石/诸葛亮 各 1）
> 与 **15 条 `text_type="commentary"`（朱熹《论语集注》）**。v1 未提及 L2 注疏，
> 该遗漏导致 §3 的真实漏洞（见 RC4）。

---

## 1. 归一化

**权威实现**：`backend/app/services/quote_verifier.py:124` `normalize_text()`

固定顺序：`NFKC`(:133) → `to_simplified`(:134) → `_strip_punctuation`(:135) → `.strip()`(:136)

记 `N(x)` 为上述结果。

### 1.1 允许的归一化

Unicode NFKC；繁体/异体 → 简体；标点/空白/引号剥离。

### 1.2 禁止的归一化

同义改写、LLM 语义等价、自动补词、语序调整、
以及**任何用于存在性判定的模糊匹配**（编辑距离等）。

### 1.3 已知局限（**必须一并披露**）

RC7 实测，本局限比 v1 描述的更严重：

1. **映射不完整**：内置映射 148 条，而语料归一化字符集有 698 个不同字符。
2. **已造成真实误拒**：`溫故而知新，可以為師矣。` 与 `學而不思則罔`
   都是语料中**真实存在**的论语原句，却因 `溫` / `則` 未映射（而 `學` 已映射，
   属**不对称**）而 `quote_exists=False` → 误判为 `insufficient_evidence`。
   方向是保守的（fail-closed），但属**假阴性**，与项目核心承诺冲突。
3. **映射还是有损的**（不止不完整）：`雲→云`、`後→后`、`裏→里` 属语义合并。
   当前潜伏（实测 0/143 语料条目受影响），但不得当作「只是不完整」。
4. **「唯一口径」只在 backend 成立**：`eval/scripts/metrics.py:52-61` 另有一份
   **不同的** T2S 表；`metrics.normalize_all` 与 `normalize_text` 在 `惡`、`處`
   上结果不同（实测），且已被 `backend/tests/test_eval_baseline.py:205` 使用。
   两份表必须由 **RFC-3** 统一或明确各自适用范围。

---

## 2. 判定项定义

设 `q` 为待校验引文，`S` 为 canonical corpus 条目集合，`p.original` 为条目原文。

### 2.0 全局前置（RC1）

**以下两条对 `q` 恒成立，必须先判：**

```
admissible(q) := len(N(q)) >= MIN_FRAGMENT_CHARS(=4)
quote_exists = false  ->  exact_match = false  且  source_correct = false
```

`MIN_FRAGMENT_CHARS` 定义于 `quote_verifier.py:51`。

> 为什么必须显式写入门槛：v1 的 §2.2/§2.3 未写门槛，复核实测其字面值对
> `""`、`"   "`、`"，。！？"`、`"「」"`（`N("")` 是任何串的子串）以及 `"己"`
> 都会给出 `exact_match=true` / `source_correct=true`。
> 真实实现之所以安全，是因为 `quote_verifier.py:513` 在计算之前就先按门槛短路。
> 合同必须与实现同样显式，否则字面语义是错的。

### 2.1 `quote_exists`

```
quote_exists = admissible(q)
               且 ∃ p ∈ S : N(q) 是 N(p.original) 的连续子串
```

- **只允许单向包含**：`N(q) ⊆ N(p.original)`；
  **禁止反向**（否则「伪造长文内嵌真实短句」会通过）。
- `S` 含 L1 与 L2 条目；**`quote_exists` 允许 L2 命中**（注疏中确实存在该文字），
  但 L2 **不得**成为「经典原文」展示依据（见 §3.2 / RC4）。

### 2.2 `exact_match`（是否为逐字连续引用，RC2）

```
exact_match = quote_exists
              且 ∃ p ∈ S : N(q) 是 N(p.original) 的连续子串
              且 **该匹配跨度不跨越源文句界**（见 §3.3 句界规则）
```

**明确不要求** `q == p.original`（不要求等于整条 passage）。
因此**一个完整经典句子，即使 passage 含前后文，仍可 `exact_match=true`。**

**关于 `exact_match` 与 `quote_exists` 的关系（RC2，取代 v1 的「决策点」）**：

二者在当前实现下**由构造而重合** —— 它们**共用同一个谓词**
（`quote_verifier.py:570` 遍历的正是 `:528/:546` 生成的那一个 `matches` 列表）。
本合同**不再把这种重合描述为「今天的事实」**，而是明确规定：

- 二者由构造共用同一谓词；**唯一允许的分离**是 §2.0 的守卫输入
  （`quote_exists=false` ⇒ `exact_match=false`）。
- **必须有一个具名测试**断言该分离（§7 用例 13），
  否则将来 `matches` 被放宽（如 PHASE 4 的 query expansion）时，
  仅通过扩展命中的引文会静默获得 `exact_match=true`，
  并在满足 source+gate 后变成 `verified` + 可展示，而**没有任何测试能发现**。
- 保留 `exact_match` 作为独立字段的理由：PHASE 4 若放宽 `quote_exists`，
  `exact_match` 必须继续表示严格连续子串。

匹配类型（**只记录、不替代**上述断言）：

| match_type | 含义 |
|---|---|
| `exact` | 原文**逐字**连续子串 |
| `normalized` | 需经 §1.1 归一化后才连续 |
| `partial` | 连续子串，但 `len(N(q)) < MIN_FULL_QUOTE_CHARS(=6)` |
| `none` | 未命中 |

### 2.3 `source_correct`

```
source_correct = quote_exists
                 且 ∃ p ∈ S : N(q) ⊆ N(p.original)
                 且 p 的出处与 claimed_source 一致
```

- 同样受 §2.0 门槛约束：`quote_exists=false` ⇒ `source_correct=false`
  （v1 未写门槛，复核实测 `q="君子"`、`q=""`、`q="，。"` 会得到
  `quote_exists=false` 但 `source_correct=true` 的自相矛盾元组；
  真实实现于 `:518` 强制为 `false`）。
- `quote_exists=true` **不代表** `source_correct=true`，二者必须**分别返回**。
- 空出处或「无」→ `source_correct=false`。
- `source_correct=false` 且 `quote_exists=true` 时必须给出 `correct_source`。
- **RC（非阻塞但必须满足）**：`correct_source` 必须**可作为 `claimed_source` 回灌
  并通过校验**。复核实测注疏条目的 `correct_source="朱熹《论语集注》"` 无法被
  `parse_source` 往返解析（回灌后 `source_correct=False`），必须在实现中修正。

### 2.4 `verifiable`（RC8，v1 遗漏）

```
verifiable = quote_exists AND source_correct AND ≥1 条可用 evidence
```

`is_verifiable(trust_state, match_type)`（`trust_state.py:122-134`）当前对
`quote_relaxed` 返回 **True**，与本合同 §4.2（`quote_relaxed` 不可展示）**不一致**，
必须同步收紧；`citation_guard.py:345` 使用该函数。

---

## 3. 完整性门与展示合同

### 3.1 完整性门

```
completeness_gate(q) = len(N(q)) >= MIN_FULL_QUOTE_CHARS(=6)
```

共享常量 `quote_verifier.py:55`，由 `quote_verifier` 与 `citation_guard` 共用。

**已知误判（RC8，须由 RFC-2 处理）**：字符数无法区分「完整短句」与「碎片」。
语料实测的真实完整句却只有 4–5 字：

| 条目 | 完整原句 | `len(N)` | 现门结果 |
|---|---|---|---|
| `lunyu:2.12` | 君子不器（整章） | 4 | 不通过 |
| `lunyu:2.4` | 三十而立 | 4 | 不通过 |
| `lunyu:1.8` | 过则勿惮改 | 5 | 不通过 |
| `lunyu:2.10` | 人焉廋哉 | 4 | 不通过 |
| `lunyu:1.4` | 传不习乎 | 4 | 不通过 |

**骤降门槛到 4 不是解法**（会让 `勿施于人` 变成可展示，破坏 §5 用例 3 与
aq-0010）。正确方向是**句界/覆盖度**完整性规则，见 **RFC-2**。
本 RFC 未决前，本条按现状执行并**如实记录该误判**。

### 3.2 `is_displayable_as_classic`（产品展示合同）

```
is_displayable_as_classic(trust_state) := (trust_state == "verified")
```

展开即：

```
quote_exists AND exact_match AND source_correct AND completeness_gate(q)
AND 命中条目为 L1（text_type == "original"）      # RC4
```

**明确禁止** `is_displayable_as_classic ≡ exact_match`。

**RC4 —— v1 的真实漏洞**：v1 的 `S` 含 L2 注疏且未加 `text_type` 条件。
复核实测：`人性皆善而觉有先后后觉者必效先觉之所为`（朱熹注文，语料中逐字存在）
claim 为《论语集注》→ v1 判定为 `verified` + 可作**经典原文**展示。
注疏是宋人解释，**不是经典原文**。因此 `verified` 与展示都必须要求 L1。

**RC3 —— 与既有断言的冲突只有一个解**：
`backend/tests/test_quote_verifier.py:421` 断言
`is_displayable_as_classic("quote_relaxed") is True`。

v1 提出「改签名」或「收窄断言」两个选项，复核证明**选项 1 逻辑上不可能**：
按 §3.2 + §4，`trust_state == "quote_relaxed"` 只在
`quote_exists ∧ source_correct ∧ ¬(exact_match ∧ gate)` 时出现；
而 §3.2 要求四项全真——若全真则 §4 规则 3 已返回 `verified`。
**任何附加参数都无法让 `is_displayable_as_classic("quote_relaxed")` 为真。**

因此**唯一解**（也是本轮实现必须照做的）：

1. 保持签名不变，语义改为 `(trust_state == "verified")`；
2. 把 `test_quote_verifier.py:421` 改为 `is False`
   —— 这是**合同变更**（因为 §4 已把四个谓词全部折叠进 `trust_state`），
   **不是**降低断言；
3. 在合同中明确恒等式：**可展示 ⇔ `verified`**。

影响面（复核实测）：该函数**没有任何产品调用方** —— 全仓库仅
`trust_state.py:110/:170`、其 docstring `:40`、以及测试 `:419-423`。

### 3.3 句界规则（RC5，v1 的真实漏洞）

`_strip_punctuation` 会删除 `。！？「」`，因此**相邻两句直接拼接**也会命中：
`不亦说乎有朋自远方来`，更严重的是
`有一言而可以终身行之者乎子曰其恕乎`（把子贡的问句与孔子的答句粘成一句）。

当前实现判定为 `normalized` / `quote_relaxed`（不可展示）；
而 v1 的字面规则会判 `verified` + **可展示**——
即 §2.2 让展示**更宽松**，反而抵消了 §4.2 的收紧。

**规则（本合同采用）**：

```
若匹配跨度在源文中跨越句界（。！？），则该匹配 exact_match = false，
除非原始引文本身含有该句界标点（即引用者明确引用了跨句原文）。
```

**可行性（已实测）**：`eval/quote_verification.jsonl` 中
**0 / 21** 条引文的匹配跨度跨越句界，因此本规则**不会**降低
`quote_exactness` 的可达性。

---

## 4. `trust_state` 四态合同

判定自上而下，命中即返回：

| 顺序 | 条件 | `trust_state` |
|---|---|---|
| 1 | `quote_exists == false` | `insufficient_evidence` |
| 2 | `quote_exists ∧ ¬source_correct` | `citation_corrected` |
| 3 | `quote_exists ∧ exact_match ∧ source_correct ∧ gate ∧ L1` | `verified` |
| 4 | 其余（存在且出处正确，但不满足完整性门 / 非 L1 / 跨句界） | `quote_relaxed` |

**RC6-§4 补齐**：规则 1 已把 §2.0 的两个「悬空组合」
（`quote_exists=false` 而 `exact_match=true`；`quote_exists=false` 而
`source_correct=true`）**短路**，故映射对全部 16 种组合都是**全函数**
（复核逐组合枚举确认无遗漏状态）。

**恒等式**：规则 3 是通往 `verified` 的唯一路径，故
**`is_displayable_as_classic` ⇔ `verified`**。

### 4.1 各态语义

- **`verified`**：文本存在 + 逐字连续 + 出处正确 + 完整性门 + L1。必须有可靠 evidence。
- **`citation_corrected`**：文本存在但声称出处错误，系统已给出正确出处
  （展示须用 `correct_source`）。
- **`quote_relaxed`**：**仅**用于合同允许的轻量格式差异**遗留**情形。
  不得用它接受改写、意译、伪造句子。
  **RC8**：`explain("quote_relaxed")`（`trust_state.py:144`）现文案为
  「仅在归一化（标点/繁简）后与原文一致」，在 `quote_relaxed` 还包含
  「完整短句未过门」与「非 L1」之后**已不准确，必须同步更新文案**。
- **`insufficient_evidence`**：证据不足；**严禁生成新古文作为事实依据**，
  必须返回 `trust_state.py:53` 的拒答文案。

### 4.2 四态与展示

| `trust_state` | `is_displayable_as_classic` |
|---|---|
| `verified` | **true** |
| `citation_corrected` | false（须改用 `correct_source`） |
| `quote_relaxed` | **false**（v1 为 true → **本合同有意变更**） |
| `insufficient_evidence` | false |

---

## 5. 合同用例表（Worked Examples，共 10 条）

以语料含 `lunyu:15.24`（`《论语·卫灵公》`，L1）为例：

| # | `q` | claimed_source | exists | exact | src | gate | displayable | trust_state |
|---|---|---|---|---|---|---|---|---|
| 1 | `己所不欲，勿施于人。` | 《论语·卫灵公》 | T | T | T | T(8) | **T** | `verified` |
| 2 | `己所不欲，勿施于人。` | 《孟子·公孙丑上》 | T | T | F | T | F | `citation_corrected` |
| 3 | `勿施于人` | 《论语·卫灵公》 | **T** | **T** | T | **F(4)** | **F** | `quote_relaxed` |
| 4 | `君子` | 《论语·学而》 | F(§2.0门槛) | F | F | F | F | `insufficient_evidence` |
| 5 | `己所不欲，勿施於人。`（繁体） | 《论语·卫灵公》 | T | T | T | T | T | `verified` |
| 6 | `己所不欲勿施于人`（去标点） | 《论语·卫灵公》 | T | T | T | T | T | `verified` |
| 7 | `己所不欲, 勿施于人。`（异标点） | 《论语·卫灵公》 | T | T | T | T | T | `verified` |
| 8 | `天行健，君子以自强不息。` | 《周易》 | **F**（语料无） | F | F | — | F | `insufficient_evidence` |
| 9 | `子曰：吾从未说过此言，此乃后人伪托之辞也。` | 《论语·学而》 | F | F | F | — | F | `insufficient_evidence` |
| 10 | `己所不欲，勿施于人，是故君子慎独。`（真句+伪造后缀） | 《论语·卫灵公》 | **F**（单向包含失败） | F | F | — | F | `insufficient_evidence` |

**全部 10 条已由复核在真实语料上逐条复现一致**（含 `於→于` 归一化、
去标点、异标点、用例 10 的伪造后缀被正确拒绝）。

> 用例 10 的诚实附注（复核提出）：由于规则丢弃部分重叠，系统返回 `candidates=[]`，
> **无法**告诉用户「前半句是真的」。该信息损失**记录在案**（非阻塞）。

---

## 6. 与当前实现的差异（Delta）

| 项 | 当前实现 | 本合同 | 影响 |
|---|---|---|---|
| `exact_match` | 等于**整条** passage | `N(q)` 为 `N(original)` 的**连续子串**（且不跨句界、过 §2.0 门槛） | 单句引用从此可 `exact_match=true` |
| `verified` 条件 | `exact_match ∧ match_type=="exact"` | `quote_exists ∧ exact_match ∧ source_correct ∧ gate ∧ L1` | 摘句/注疏不再 `verified` |
| `quote_relaxed` 可展示 | true | **false** | 摘句不再作为完整经典原文展示 |
| `is_displayable_as_classic` | 入参仅 `trust_state` | `≡ (trust_state=="verified")` | 与 §4 一致的恒等式 |
| `verifiable` | `is_verifiable` 对 `quote_relaxed` 为 true | 须与 §4.2 同步收紧 | 见 §2.4 |
| `citation_guard` 的 `match_type` | 无条件 `"exact"` | 由完整性门决定 | 已修（D3），须与新合同对齐并加测试 |

### 6.1 实测证据

| 判据 | 命中 |
|---|---|
| 原文**逐字**连续子串 | **17 / 21** |
| 经 §1.1 归一化后连续子串 | **18 / 21**（仅多 `qv-0017` 繁体 於 变体） |
| 两者皆非 | **3**（`qv-0019` / `qv-0020` / `qv-0021`） |
| 上述 3 条 `expected.quote_exists == false` | **是（3/3）** |
| 匹配跨度跨越句界 | **0 / 21** |

### 6.2 关于 `quote_exactness` 的重要更正（RC6）

按本合同语义，`quote_exactness` 的分母 =「系统判为 exists」= 18，
分子 = 其中 `exact_match=true` 且 `expected.quote_exists=true` = 18
→ **预测 1.000**。

> **必须纠正 v1 的一句错话**：v1 §6 称该定义「与数据集期望一致」。
> **这对 3/21 条记录是错的**：
> `qv-0016`（`己所不欲勿施于人`，去标点）、`qv-0017`（繁体 於）、
> `qv-0018`（`勿施于人`，4 字）的 **`expected.exact_match` 均为 `false`**，
> 且 `expected.trust_state` 均为 `quote_relaxed`。
> 而冻结公式（`metrics.py:98`）要求这些条目的 `pred.exact_match` 为 **true**
> 才能达到 ≥0.99。

**这是一处必须显式升级的数据集/公式冲突（RFC-1）**：

- 冻结分子**从不读取** `expected.exact_match`；
  全仓库该字段只在 `.jsonl` 内与 `schema.py:64` 的 `expected_keys` 出现，
  **没有任何指标或脚本消费它**。
- 因此 **1.000 不能作为 `exact_match` 判定正确的证据**。
- 冲突是**双向**的：任何**更严格**的 `exact_match` 都会**不达标** ——
  逐字原文口径 → 0.9444（17/18）；逐字+门槛 → 0.8889（16/18）。
- 即：**数据集标签与冻结公式互相不可同时满足**，任何实现都无法两者兼顾。
- 本合同选择服从**冻结指标**，并**把冲突升级为 RFC-1**，
  而不是静默采纳一侧。
  （注意：这与 §8「不得为取得 PASS 而更换指标口径」相邻，故必须留痕。）

**诚实声明**：上述 1.000 是**按合同推导**的预测，**不是**已达成的事实；
实现后必须以 `run_eval.py` 实测复核，并把
`pred.exact_match` 与 `expected.exact_match` 逐条对比、公开差异清单。

---

## 7. 必须的合同测试（CONTRACT TESTS FIRST）

**先写测试并看到 RED，再改实现。** 每条都要断言
`quote_exists` / `exact_match` / `source_correct` / `is_displayable_as_classic` / `trust_state`：

1. 完整原句 + 正确来源
2. 完整原句 + 错误来源
3. 部分 quote（长摘句 ≥6 字但非完整句）
4. 4 字 fragment（`勿施于人`）
5. 繁体写法（`於`）—— **并新增一条未映射繁体字的用例**（RC7，
   如 `溫故而知新，可以為師矣。` 当前会被误拒，用例须暴露该假阴性）
6. 简体写法
7. 不同标点（全角/半角、逗号句号差异）
8. 去标点
9. 网络伪名言（语料不存在）
10. 同义改写但非原文（**不得**靠语义放行）
11. quote 真但**书名**错
12. quote 真但**篇章**错
13. **（RC2）守卫输入分离**：断言 `quote_exists=false` 时 `exact_match=false`
    且 `source_correct=false`（覆盖 `""`、`"   "`、`"，。！？"`、`"君子"`）
14. **（RC4）L2 注疏**：注疏原文命中时 `quote_exists=true` 但
    `verified=false` 且 `is_displayable_as_classic=false`
15. **（RC5）相邻句拼接**：`有一言而可以终身行之者乎子曰其恕乎`、
    `不亦说乎有朋自远方来` → `exact_match=false`，不得 `verified`
16. **（RC3）恒等式**：`is_displayable_as_classic(ts) is (ts == "verified")`，
    并据此把 `test_quote_verifier.py:421` 改为 `is False`

---

## 8. 禁止事项（Non-Goals）

- 不得为让任何测试通过而降低断言（**唯一例外**：§3.2 RC3 的合同变更，
  且必须说明理由与影响面）
- 不得删除任何失败 case
- 不得修改 `TARGETS`
- 不得把某指标换成另一口径以取得 PASS
- 不得用 LLM 语义等价替代逐字判定
- 不得引入未在 §1.1 声明的归一化
- 不得在本轮扩大 scope（新功能 / 新 UI / 新学派 / 新 provider）

---

## 9. 阈值变更政策

`MIN_FRAGMENT_CHARS` / `MIN_FULL_QUOTE_CHARS` 的任何变更必须：
单独 RFC + 改动前后全量 Eval 与全量测试对比 + 独立 Review。
**不得**为变绿而随意调整。

---

## 10. 复核记录与 RC 处置

| RC | 内容 | v2 处置 |
|---|---|---|
| RC1 | §2.2/§2.3 补门槛 | §2.0 新增全局前置；§2.2/§2.3 引用 |
| RC2 | 重合改为「由构造」+ 分离测试 | §2.2 重写；§7 用例 13 |
| RC3 | 展示恒等式；翻转 :421；删选项 1 | §3.2 重写；§7 用例 16 |
| RC4 | 要求 L1（`text_type=="original"`） | §3.2 / §4 规则 3；§7 用例 14 |
| RC5 | 句界规则 + 测试 | §3.3；§7 用例 15 |
| RC6 | 升级数据集/公式冲突 | §6.2 + RFC-1 |
| RC7 | §1 口径收敛 + 重复表 + 假阴性 | §1.3 + RFC-3 |
| RC8 | 纳入 `verifiable`；文案；≤5 字完整句 | §2.4 / §4.1 / §3.1 + RFC-2 |

**非阻塞修正**：§5 为 **10 行**（v1 误称 11）；§0 语料措辞已改；
§2.3 新增 `correct_source` 可回灌要求。

---

## 11. 待决 RFC（不在本轮实现范围内）

- **RFC-1（数据集缺陷）**：`qv-0016/0017/0018` 的 `expected.exact_match=false`
  与冻结 `quote_exactness` 分子互相不可满足；且 `expected.exact_match`
  **无任何消费者**。需决定：修数据集、修公式、还是明确废弃该字段。
- **RFC-2（完整性规则）**：以句界/覆盖度替换纯字符数门槛，
  以修复 `君子不器`/`三十而立`/`过则勿惮改` 等**真实完整短句**被永久判为
  不可展示的问题。
- **RFC-3（归一化统一）**：`backend` 的 `normalize_text` 与
  `eval/scripts/metrics.py:52-61` 的 `_T2S` 表必须统一或明确各自适用范围。
