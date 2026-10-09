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

## 未计入分母的用例（合同与实现一致：均判不存在）

| id | quote | pred exists | exp exists | 合同根因 |
|---|---|---|---|---|
| qv-0019 | `以德报怨。` | False | False | `corpus absence` |
| qv-0020 | `天行健，君子以自强不息。` | False | False | `corpus absence` |
| qv-0021 | `知行合一。` | False | False | `corpus absence` |
