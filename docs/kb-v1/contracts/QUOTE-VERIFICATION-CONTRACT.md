# 引文校验合同（QUOTE-VERIFICATION-CONTRACT）

- **编号**：CONTRACT-001
- **状态**：**DRAFT — 待独立 Review**（未 Review 通过前不得据此改代码）
- **范围**：`quote_exists` / `exact_match` / `source_correct` /
  `is_displayable_as_classic` / `trust_state` 四项判定语义
- **不动**：任何 `TARGETS` 目标数字；任何失败 case；任何数据集条目

本文件是**语义合同**，不是实现说明。实现必须服从本合同；
若实现与本合同冲突，以本合同为准，并单独立项修正实现。

---

## 0. 为什么需要这份合同

当前同一个输入在不同模块得到**互相矛盾**的判定，属于真实缺陷：

| 输入 | `quote_verifier` | `citation_guard`（修复前） |
|---|---|---|
| 「勿施于人」 | `match_type=partial`, `quote_relaxed` | `verifiable=True`, `verified` |

以及 `exact_match` 的当前实现要求「引文 == **整条** passage」，而语料按**整章**
存储（`lunyu:15.24` 的 `original` 含 `子贡问曰：「…」子曰：「其恕乎！己所不欲，勿施于人。」`），
导致**任何单句引用都不可能** `exact_match=true`——
而 `eval/quote_verification.jsonl` 明确期望单句引用 `exact_match=true`。
**数据集与实现互相矛盾**，实测 `quote_exactness` 因此只有 0.333。

---

## 1. 归一化：唯一口径

**唯一权威实现**：`backend/app/services/quote_verifier.py:124` `normalize_text()`

流水线（顺序固定）：

1. `unicodedata.normalize("NFKC", text)` —— 全角→半角、部分异体字标准化
2. `to_simplified()` —— 繁体/异体 → 简体（`quote_verifier.py:119`）
3. `_strip_punctuation()` —— 剥离标点/空白/引号（`quote_verifier.py:73`）
4. `.strip()`

记 `N(x)` 为上述归一化结果。

### 1.1 合同允许的归一化

- Unicode NFKC
- 繁体/异体 → 简体
- 标点、空白、引号的剥离

### 1.2 合同**禁止**的归一化

- 同义改写 / 近义词替换
- LLM 语义等价判定
- 自动补词后再判存在
- 语序调整
- 任意模糊匹配（编辑距离等）用于**存在性**判定

> **已知限制（必须随合同披露，不得掩盖）**：
> `to_simplified()` 的内置映射**不完整**，未覆盖字符原样保留
> （见其 docstring）。因此「繁体写法在语料中能被正确归一化」这一结论
> **只在映射覆盖范围内成立**。超出覆盖范围时 `N()` 不改变字符，
> 可能导致真实的繁简差异被判为「不存在」。此为**已知局限**，
> 需单独立项补全映射，**不得**用模糊匹配掩盖。

---

## 2. 判定项定义

设 `q` 为待校验引文，`S = {p₁…pₙ}` 为 canonical corpus 全量条目，
`p.original` 为条目原文。

### 2.1 `quote_exists`（该文字是否存在）

```
quote_exists = ∃ p ∈ S :  N(q) 是 N(p.original) 的连续子串
               且 len(N(q)) ≥ MIN_FRAGMENT_CHARS(=4)
```

- 允许 NFKC / 繁简 / 标点归一化（§1.1）
- **只允许单向包含**：`N(q) ⊆ N(p.original)`。
  **禁止反向**（`N(p.original) ⊆ N(q)`）——否则「伪造长文内嵌真实短句」会通过
- 低于 `MIN_FRAGMENT_CHARS` 的片段（如「君子」）→ `quote_exists=false`，
  因为 2 字不足以支撑一条结论

### 2.2 `exact_match`（是否为逐字连续引用）

```
exact_match = ∃ p ∈ S :  N(q) 是 N(p.original) 的连续子串（CONTIGUOUS VERBATIM SUBSTRING）
```

**明确不要求** `q == p.original`（不要求等于整条 passage）。

因此：**一个完整的经典句子，即使其 passage 还包含前后文，仍可 `exact_match=true`。**

> **决策点（提请 Reviewer 裁定）**：按本节字面定义，`exact_match` 与
> `quote_exists` 在当前实现下**取值相同**（都只走同一条连续子串路径）。
> 本合同保留 `exact_match` 作为**独立断言字段**的理由是：
> 后续 PHASE 4 若引入 query expansion / 语义检索，`quote_exists` 可能经
> 更宽路径为真，而 `exact_match` 必须保持严格连续子串语义。
> **今日二者重合是事实，合同如实记录，不假装它们是不同判据。**
> 若 Reviewer 认为应当让二者今天就分离，请给出明确的分离规则。

**必须记录但不改变判定**的匹配类型（`match_type`）：

| match_type | 含义 | `quote_exists` | `exact_match` |
|---|---|---|---|
| `exact` | 原文**逐字**连续子串 | true | true |
| `normalized` | 需经 §1.1 归一化后才连续 | true | true |
| `partial` | 连续子串，但 `len(N(q)) < MIN_FULL_QUOTE_CHARS(=6)` | true | true |
| `none` | 未命中 | false | false |

`match_type` **只用于**记录与展示，**不得**用它替代 `quote_exists` / `exact_match`。

### 2.3 `source_correct`（声称出处是否正确）

**独立于 `quote_exists` 判定。**

```
source_correct = ∃ p ∈ S :  N(q) ⊆ N(p.original)  且  p 的出处与 claimed_source 一致
```

- `quote_exists=true` **不代表** `source_correct=true`
- 二者必须**分别返回**（这是 PROJECT-BRIEF 第十一章的核心要求）
- 当 `source_correct=false` 且 `quote_exists=true` 时，
  必须返回系统找到的**正确出处** `correct_source`
- 空出处或「无」→ `source_correct=false`（**不得**因缺失而放行）

---

## 3. 完整性门与展示合同

### 3.1 完整性门（completeness gate）

复用**共享常量**，不得另造阈值：

```
completeness_gate(q) = len(N(q)) ≥ MIN_FULL_QUOTE_CHARS(=6)
```

`MIN_FULL_QUOTE_CHARS` 定义于 `quote_verifier.py:55`，为
`quote_verifier` 与 `citation_guard` **共用**。

符合：`勿施于人`（4 字）→ 门不通过；`己所不欲，勿施于人。`（8 字）→ 门通过。

### 3.2 `is_displayable_as_classic`（产品展示合同）

**这不是** `exact_match` 的同义词。必须同时满足：

```
is_displayable_as_classic(q, source_correct)
    = quote_exists
      AND exact_match
      AND source_correct
      AND completeness_gate(q)
```

**明确禁止** `is_displayable_as_classic ≡ exact_match`。

理由：`exact_match` 回答「这段字是否逐字出现在原典中」，
而展示合同回答「我们是否可以在产品里把它当作**完整经典原文**呈现」。
一个 4 字片段确实逐字存在于原典，但把它当作完整经典引文展示是**误导**。

### 3.3 与既有断言的冲突（必须由 Reviewer 裁定）

`backend/tests/test_quote_verifier.py:421` 断言
`is_displayable_as_classic("quote_relaxed") is True`。

而按本合同 §5，摘句（`partial`）的 `trust_state` 为 `quote_relaxed`，
其 `is_displayable_as_classic` 应为 **false**。

**冲突是真实的，本项目不当场偷偷改测试。** 两个可行方向：
1. 保留该断言，则 `is_displayable_as_classic` 的入参必须**不止** `trust_state`
   （需同时传入 `quote_exists` / `exact_match` / 完整性门），
   并新增针对完整签名的新断言；
2. 或收窄该断言的输入域并明确其语义。

**提请 Reviewer 明确选择**，未裁定前不修改该测试。

---

## 4. `trust_state` 四态合同

判定按**从上到下**顺序，命中即返回。

| 顺序 | 条件 | `trust_state` |
|---|---|---|
| 1 | `quote_exists == false` | `insufficient_evidence` |
| 2 | `quote_exists == true` 且 `source_correct == false` | `citation_corrected` |
| 3 | `quote_exists && exact_match && source_correct && completeness_gate` | `verified` |
| 4 | 其余（存在且出处正确，但**不满足完整性门**） | `quote_relaxed` |

### 4.1 各态语义（与 PROJECT-BRIEF 一致）

- **`verified`**：文本存在 + 逐字连续 + 出处正确 + 完整性门通过。
  必须有可靠 evidence。
- **`citation_corrected`**：文本存在，但声称出处错误，系统已找到正确出处。
  展示时必须使用 `correct_source`，不得沿用错误出处。
- **`quote_relaxed`**：**仅**用于合同明确允许的轻量格式差异遗留情形
  （本合同下 = 存在且出处正确，但未通过完整性门，即摘句）。
  **不得**用它接受：改写、意译、伪造句子。
- **`insufficient_evidence`**：没有足够可靠证据支持核心回答。
  **此时严禁生成新的古文作为事实依据**，必须返回 PROJECT-BRIEF 第十二章的
  拒答文案（`trust_state.py:53`）。

### 4.2 四态与「可否作为经典原文展示」

| `trust_state` | `is_displayable_as_classic` |
|---|---|
| `verified` | true |
| `citation_corrected` | false（须改用 `correct_source` 展示） |
| `quote_relaxed` | false（摘句，不完整） |
| `insufficient_evidence` | false |

> 注意：本合同下 `quote_relaxed` 不再是「可展示」态。
> 这与当前实现（`trust_state.py:110-119` 把 `quote_relaxed` 视为可展示）**不同**，
> 属本合同的**有意变更**，需 Reviewer 明确同意。

---

## 5. 合同用例表（Worked Examples）

以 canonical corpus 含
`p = 「子贡问曰：「有一言而可以终身行之者乎？」子曰：「其恕乎！己所不欲，勿施于人。」」`（`《论语·卫灵公》`）为例：

| # | 输入 `q` | claimed_source | quote_exists | exact_match | source_correct | 完整性门 | is_displayable | trust_state |
|---|---|---|---|---|---|---|---|---|
| 1 | `己所不欲，勿施于人。` | 《论语·卫灵公》 | true | true | true | 通过(8字) | **true** | `verified` |
| 2 | `己所不欲，勿施于人。` | 《孟子·公孙丑上》 | true | true | **false** | 通过 | false | `citation_corrected` |
| 3 | `勿施于人` | 《论语·卫灵公》 | **true** | **true** | true | **不通过(4字)** | **false** | `quote_relaxed` |
| 4 | `君子` | 《论语·学而》 | false（<4 字） | false | false | 不通过 | false | `insufficient_evidence` |
| 5 | `己所不欲，勿施於人。`（繁体） | 《论语·卫灵公》 | true（经 §1.1） | true | true | 通过 | true | `verified` |
| 6 | `己所不欲勿施于人`（去标点） | 《论语·卫灵公》 | true | true | true | 通过 | true | `verified` |
| 7 | `己所不欲, 勿施于人。`（异标点） | 《论语·卫灵公》 | true | true | true | 通过 | true | `verified` |
| 8 | `天行健，君子以自强不息。` | 《周易》 | **false**（语料无此条） | false | false | — | false | `insufficient_evidence` |
| 9 | `子曰：吾从未说过此言，此乃后人伪托之辞也。` | 《论语·学而》 | false | false | false | — | false | `insufficient_evidence` |
| 10 | `己所不欲，勿施于人，是故君子慎独。`（真实短句 + 伪造后缀） | 《论语·卫灵公》 | false（单向包含失败） | false | false | — | false | `insufficient_evidence` |

**用例 3 是本合同与当前实现差异的核心**：当前实现给
`exact_match=false`，合同要求 **`exact_match=true`**，
并靠**完整性门**（而非 `exact_match`）把展示挡掉。
这样 `exact_match` 只回答「是否逐字连续」，展示由独立门控制，两个概念不再混淆。

---

## 6. 与当前实现的差异（Delta）

| 项 | 当前实现 | 本合同 | 影响 |
|---|---|---|---|
| `exact_match` | `entry.original == quote`（**等于整条** passage） | `N(q)` 是 `N(original)` 的**连续子串** | 单句引用从此可 `exact_match=true`；与数据集期望一致 |
| `verified` 条件 | `exact_match && match_type=="exact"` | `quote_exists && exact_match && source_correct && 完整性门` | 摘句不再 `verified` |
| `quote_relaxed` 可展示 | `true`（`trust_state.py:119`） | **`false`** | 摘句不再作为完整经典原文展示 |
| `citation_guard` 的 `match_type` | 无条件写 `"exact"` | 由完整性门决定 `partial` | 已修（D3），需与新合同对齐并加测试 |

### 6.1 实测证据（本合同方向的可行性）

对 `eval/quote_verification.jsonl` 21 条实测：

| 判据 | 命中 |
|---|---|
| 原文**逐字**连续子串 | **17 / 21** |
| 经 §1.1 归一化后连续子串 | **18 / 21** |
| 两者皆非（语料确实无此条） | **3**（`qv-0019 以德报怨。` / `qv-0020 天行健，君子以自强不息。` / `qv-0021 知行合一。`） |

且这 3 条的 `expected.quote_exists` 均为 **false**，即数据集**同意**它们不在语料中。

**因此按本合同：`quote_exactness` 的分母 =「系统判为 exists」的条数 = 18，
分子 = 其中 `exact_match=true` 且 `expected.quote_exists=true` = 18 → 1.000。**

> **诚实声明**：上述预测是**按合同推导**的结果，**不是**已达成的事实。
> 实现改动后必须以 `run_eval.py` 实测复核；若实测低于 1.000，
> 按 §7 的失败分类逐条给出 root cause，**不得**调整目标或数据集。

---

## 7. 必须的合同测试（CONTRACT TESTS FIRST）

**先写测试并看到 RED，再改实现。**

必须逐条断言 `quote_exists` / `exact_match` / `source_correct` /
`is_displayable_as_classic` / `trust_state` 五项：

1. 完整原句 + 正确来源
2. 完整原句 + 错误来源
3. 部分 quote（长摘句，≥6 字但非完整句）
4. 4 字 fragment（`勿施于人`）
5. 繁体写法
6. 简体写法
7. 不同标点（全角/半角、逗号句号差异）
8. 去标点
9. 网络伪名言（语料中不存在）
10. 同义改写但非原文（必须判不存在/不逐字，**不得**靠语义放行）
11. quote 真但**书名**错
12. quote 真但**篇章**错

---

## 8. 禁止事项（Non-Goals）

- 不得为让任何测试通过而降低断言
- 不得删除任何失败 case
- 不得修改 `TARGETS`
- 不得把某个指标换成另一个口径来取得 PASS
- 不得用 LLM 语义等价替代逐字判定
- 不得引入未在 §1.1 声明的归一化
- 不得在本轮扩大 scope（新功能 / 新 UI / 新学派 / 新 provider）

---

## 9. 阈值变更政策

`MIN_FRAGMENT_CHARS` / `MIN_FULL_QUOTE_CHARS` 的**任何**变更必须：

1. 单独 RFC
2. 附 regression evidence（改动前后全量 Eval + 全量测试对比）
3. 经独立 Review 通过

**不得**为让某个指标变绿而随意创造或调整阈值。

---

## 10. Review 清单（供独立 Reviewer 逐条裁定）

- [ ] §2.2 决策点：`exact_match` 与 `quote_exists` 今日重合，是否接受？
      若要求今日分离，给出分离规则。
- [ ] §3.3：`is_displayable_as_classic` 与
      `test_quote_verifier.py:421` 的冲突如何裁定（改签名 or 收窄断言）？
- [ ] §4.2：`quote_relaxed` 由「可展示」改为「不可展示」是否同意？
- [ ] §4 判定顺序是否有遗漏状态组合？
- [ ] §5 用例 10（真实短句 + 伪造后缀）判 `insufficient_evidence` 是否正确？
- [ ] §1.2 已知局限（繁简映射不完整）的处理是否可接受？
- [ ] §6.1 的 1.000 **预测**是否被误当作已达成结论？（应为「否」）
