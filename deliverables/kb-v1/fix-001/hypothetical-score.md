# FIX-001A/A5 — 合同正确实现下的理论分数（不改 production code）

本文件是**在不修改任何 production code** 的前提下，对「若严格按
`QUOTE-VERIFICATION-CONTRACT v2` 实现，冻结指标会是多少」的逐用例推演。

- 分母口径：**冻结规则**（`metrics.py:98` 之前的分母 = `pred.quote_exists == True`）
- `Contract exact`：按合同 §2.0/§2.2/§3.3 推导
- `Before`：当前 `verify_quote().exact_match`
- `Hypothetical After`：合同正确实现后的 `exact_match`
- `Counted`：是否进入冻结分母

> 计分聚合仍由冻结实现产生；本表只做逐用例推演，不构成新的指标实现。

## 逐用例

| Case | quote | Contract exact | Before | Hypothetical After | Counted | exp.exact_match |
|---|---|---|---|---|---|---|
| qv-0001 | `己所不欲，勿施于人。` | True | False | True | True | True |
| qv-0002 | `己所不欲，勿施于人。` | True | False | True | True | True |
| qv-0003 | `己所不欲，勿施于人。` | True | False | True | True | True |
| qv-0004 | `己所不欲，勿施于人。` | True | False | True | True | True |
| qv-0005 | `上善若水，水善利万物而不争。` | True | True | True | True | True |
| qv-0006 | `上善若水，水善利万物而不争。` | True | True | True | True | True |
| qv-0007 | `学而时习之，不亦说乎？` | True | False | True | True | True |
| qv-0008 | `温故而知新，可以为师矣。` | True | False | True | True | True |
| qv-0009 | `学而不思则罔，思而不学则殆。` | True | False | True | True | True |
| qv-0010 | `三人行，必有我师焉。` | True | False | True | True | True |
| qv-0011 | `士不可以不弘毅，任重而道远。` | True | True | True | True | True |
| qv-0012 | `君子喻于义，小人喻于利。` | True | False | True | True | True |
| qv-0013 | `法不阿贵，绳不挠曲。` | True | True | True | True | True |
| qv-0014 | `赖其力者生，不赖其力者不生。` | True | True | True | True | True |
| qv-0015 | `知人者智，自知者明。` | True | True | True | True | True |
| **qv-0016** | `己所不欲勿施于人` | True | False | True | True | **False** ⚠️ |
| **qv-0017** | `己所不欲，勿施於人。` | True | False | True | True | **False** ⚠️ |
| **qv-0018** | `勿施于人` | True | False | True | True | **False** ⚠️ |
| qv-0019 | `以德报怨。` | False | False | False | **False** | False |
| qv-0020 | `天行健，君子以自强不息。` | False | False | False | **False** | False |
| qv-0021 | `知行合一。` | False | False | False | **False** | False |

## 结论

| 项 | 值 |
|---|---|
| 当前冻结分数 | **6 / 18 = 0.3333** |
| 合同正确实现下的理论分数 | **18 / 18 = 1.0000** |
| 目标 | ≥ 0.99 |
| 分母是否变化 | **否**（仍为 18） |
| 理论最大值是否达标 | **是** |

**分母不变**这一点很重要：本次修复**不会**通过减少分母（例如把某些 case
判为不存在而被排除）来抬分。18 个 case 的 `quote_exists` 在修复前后**完全一致**，
变化的只有 `exact_match`。

## ⚠️ RFC-1：3 个 case 的期望标签与冻结公式互相矛盾（**未修改**）

`qv-0016` / `qv-0017` / `qv-0018`：

| 字段 | 值 |
|---|---|
| `dataset expected.exact_match` | **false** |
| 合同 `exact_match` | **true** |
| 冻结分子要求 | `pred.exact_match == true`（否则不计分） |

即：**数据集说这三条不应算 exact，冻结公式却要求它们算 exact 才能达标。**

- 本表**不声称**二者语义等价；
- 数据集**保持原样**，未做任何修改；
- 本合同选择服从**冻结指标**，并把该冲突记录为 **RFC-1**，由 dataset governance 决策；
- 因此 `1.0000` **不能**作为「`exact_match` 判定与数据集意图一致」的证据，
  只能作为「冻结指标在合同实现下达标」的证据。

## 可达性判定

合同正确实现下理论分数 1.0000 ≥ 0.99，**且**该结果不依赖对数据集、目标数字
或指标口径的任何修改。故 **target 可达到**，不属于
`BLOCKED_BY_FROZEN_DATASET_CONTRACT`。

（RFC-1 是**诚实性**问题，不是**可达性**问题：它影响的是我们能否宣称
「与数据集标注一致」，不影响冻结指标能否达标。）
