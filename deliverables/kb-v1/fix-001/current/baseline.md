# FIX-001 基线（冻结 quote_exactness）

- 数据集：`quote_verification.jsonl`，条数 **21**
- 分子：**18**
- 分母：**18**（= 系统判为 `quote_exists=True` 的条数）
- 分数：**1.0000**（目标 ≥ 0.99）
- 判定：**PASS**

> 计分完全由冻结实现 `eval/scripts/metrics.py:compute_quote_exactness` 产生，
> 本报告未重新实现任何指标逻辑。

## 逐用例

| id | quote | claimed | exists | exact(pred) | exact(exp) | counted | pass |
|---|---|---|---|---|---|---|---|
| qv-0001 | `己所不欲，勿施于人。` | 《论语·卫灵公》 | True | True | True | True | True |
| qv-0002 | `己所不欲，勿施于人。` | 《论语·颜渊》 | True | True | True | True | True |
| qv-0003 | `己所不欲，勿施于人。` | 《孟子·公孙丑上》 | True | True | True | True | True |
| qv-0004 | `己所不欲，勿施于人。` | 《论语·学而》 | True | True | True | True | True |
| qv-0005 | `上善若水，水善利万物而不争。` | 《道德经·第八章》 | True | True | True | True | True |
| qv-0006 | `上善若水，水善利万物而不争。` | 《庄子·逍遥游》 | True | True | True | True | True |
| qv-0007 | `学而时习之，不亦说乎？` | 《论语·学而》 | True | True | True | True | True |
| qv-0008 | `温故而知新，可以为师矣。` | 《论语·为政》 | True | True | True | True | True |
| qv-0009 | `学而不思则罔，思而不学则殆。` | 《论语·为政》 | True | True | True | True | True |
| qv-0010 | `三人行，必有我师焉。` | 《论语·述而》 | True | True | True | True | True |
| qv-0011 | `士不可以不弘毅，任重而道远。` | 《论语·泰伯》 | True | True | True | True | True |
| qv-0012 | `君子喻于义，小人喻于利。` | 《论语·里仁》 | True | True | True | True | True |
| qv-0013 | `法不阿贵，绳不挠曲。` | 《韩非子·有度》 | True | True | True | True | True |
| qv-0014 | `赖其力者生，不赖其力者不生。` | 《墨子·非乐上》 | True | True | True | True | True |
| qv-0015 | `知人者智，自知者明。` | 《道德经·第三十三章》 | True | True | True | True | True |
| qv-0016 | `己所不欲勿施于人` | 《论语·卫灵公》 | True | True | False | True | True |
| qv-0017 | `己所不欲，勿施於人。` | 《论语·卫灵公》 | True | True | False | True | True |
| qv-0018 | `勿施于人` | 《论语·卫灵公》 | True | True | False | True | True |
| qv-0019 | `以德报怨。` | 《孟子·公孙丑上》 | False | False | False | False | None |
| qv-0020 | `天行健，君子以自强不息。` | 《周易》 | False | False | False | False | None |
| qv-0021 | `知行合一。` | 《传习录》 | False | False | False | False | None |
