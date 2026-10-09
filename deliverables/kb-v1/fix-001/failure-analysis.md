# FIX-001 失败分类

- 冻结分母 18，分子 6，分数 0.3333
- 失败条数：**12**

## 主根因统计

- `substring contract`：**12**

## 逐条失败

| id | quote | contract exact | pred exact | exp exact | 主根因 | RFC-1 冲突 |
|---|---|---|---|---|---|---|
| qv-0001 | `己所不欲，勿施于人。` | True | False | True | `substring contract` | False |
| qv-0002 | `己所不欲，勿施于人。` | True | False | True | `substring contract` | False |
| qv-0003 | `己所不欲，勿施于人。` | True | False | True | `substring contract` | False |
| qv-0004 | `己所不欲，勿施于人。` | True | False | True | `substring contract` | False |
| qv-0007 | `学而时习之，不亦说乎？` | True | False | True | `substring contract` | False |
| qv-0008 | `温故而知新，可以为师矣。` | True | False | True | `substring contract` | False |
| qv-0009 | `学而不思则罔，思而不学则殆。` | True | False | True | `substring contract` | False |
| qv-0010 | `三人行，必有我师焉。` | True | False | True | `substring contract` | False |
| qv-0012 | `君子喻于义，小人喻于利。` | True | False | True | `substring contract` | False |
| qv-0016 | `己所不欲勿施于人` | True | False | False | `substring contract` | True |
| qv-0017 | `己所不欲，勿施於人。` | True | False | False | `substring contract` | True |
| qv-0018 | `勿施于人` | True | False | False | `substring contract` | True |

## 未计入分母的用例（合同与实现一致：**本语料中不存在**）

> **措辞更正（复核 C6）**：这三条是**真实存在的经典引文**，只是**不在本仓库
> 这 143 条语料里**（论语仅收 110 章子集，且不含《周易》《传习录》）。
> 旧标题「均判不存在」易被误读为「这些句子不是真经典」，故更正。
>
> **风险记录**：`eval/scripts/metrics.py:147-164` 把
> `expected.quote_exists=false` 计为「伪造经典引文」。若将来扩充语料，
> **正确识别这些真实古句反而会被判为伪造**。该语义风险与 RFC-1 同族，
> 已登记；本轮**不改动数据集**。

| id | quote | pred exists | exp exists | 合同根因 |
|---|---|---|---|---|
| qv-0019 | `以德报怨。` | False | False | `corpus absence` |
| qv-0020 | `天行健，君子以自强不息。` | False | False | `corpus absence` |
| qv-0021 | `知行合一。` | False | False | `corpus absence` |

## RFC-1 的**第二半**：`trust_state` 同样冲突（复核补充）

除 `exact_match` 之外，合同正确实现还会在 `trust_state` 上与数据集标签不一致：

| id | 数据集 `expected.trust_state` | 合同正确实现的 `trust_state` | 原因 |
|---|---|---|---|
| qv-0016 | `quote_relaxed` | **`verified`** | 命中 L1、过完整性门、出处正确 |
| qv-0017 | `quote_relaxed` | **`verified`** | 同上（繁体经归一化后命中 L1） |
| qv-0018 | `quote_relaxed` | `quote_relaxed` | 4 字 < `MIN_FULL_QUOTE_CHARS`，未过门，**一致** |

冻结指标**同样不读取** `expected.trust_state`（只在
`compute_unsupported_correct_refusal` 里读 **pred** 的 trust_state），
故这半冲突不影响可达性，但**必须一并记录**，以免将来说成「与数据集一致」。
