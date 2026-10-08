"""Build the seven WUDIAN-KB-V1 eval datasets from the REAL corpus.

PROVENANCE HONESTY (read this before trusting any number in the output):
  * No entry here is human-annotated.  Every record is emitted with
    provenance="derived" because it was produced by rule/table-assisted
    construction plus the author's mapping judgement.
  * This script NEVER writes provenance="human".  Human review would have to be
    recorded separately by a real annotator.
  * Every passage id written out is checked against the real corpus by
    `validate_gold.py`; this script also asserts it locally before writing.

Expansion path to 1000 records: extend the mapping tables below (book x concept x
scenario matrix) and re-run.  The schema and the gate do not change.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

import schema as S  # noqa: E402

GENERATION_METHOD = "rule/table-assisted construction + author mapping; not human-annotated"

# ---------------------------------------------------------------- retrieval gold
# (query, query_type, scenario, difficulty, [passage refs], notes)

RETRIEVAL_GOLD = [
    ("同事抢了我的功劳，我该不该跟他撕破脸？", "modern_scenario", "workplace_conflict", "hard",
     ["lunyu:4.16", "lunyu:12.2", "lunyu:15.24"], "义利之辨 + 恕道"),
    ("被领导误解了，我要不要急着解释？", "modern_scenario", "workplace_conflict", "medium",
     ["lunyu:1.16", "lunyu:4.24"], "不患人之不己知"),
    ("我该怎么面对失败？", "modern_scenario", "failure", "medium",
     ["lunyu:9.19", "lunyu:4.8"], "为山未成一篑"),
    ("总是担心别人怎么看我，很内耗", "modern_scenario", "self_doubt", "medium",
     ["lunyu:1.16", "lunyu:1.1"], "人不知而不愠"),
    ("怎么才能学到真东西？", "modern_scenario", "career", "easy",
     ["lunyu:2.11", "lunyu:2.15"], "温故知新 + 学思并重"),
    ("学了很多但工作里用不上", "modern_scenario", "career", "medium",
     ["lunyu:2.15", "lunyu:1.14"], "学而不思则罔"),
    ("如何交到真朋友？", "modern_scenario", "friendship", "easy",
     ["lunyu:16.4", "lunyu:1.4"], "益者三友"),
    ("怎么做一个讲信用的人？", "modern_scenario", "responsibility", "easy",
     ["lunyu:2.22", "lunyu:1.13"], "人而无信不知其可"),
    ("什么是真正的孝顺？", "modern_scenario", "parent_child", "medium",
     ["lunyu:2.7", "lunyu:2.8", "lunyu:1.6"], "敬与色难"),
    ("如何领导一个团队？", "modern_scenario", "leadership", "medium",
     ["lunyu:2.1", "lunyu:13.6"], "为政以德 + 其身正"),
    ("我很想快速成功，怎么办？", "modern_scenario", "ambition", "medium",
     ["lunyu:13.17"], "欲速则不达"),
    ("面对利益诱惑，该怎么选？", "modern_scenario", "money", "hard",
     ["lunyu:4.16", "lunyu:4.5"], "君子喻于义"),
    ("如何面对亲人的生死？", "modern_scenario", "meaning", "hard",
     ["lunyu:11.12", "lunyu:15.9"], "未知生焉知死 + 杀身成仁"),
    ("怎么看待职场里的竞争？", "modern_scenario", "competition", "medium",
     ["lunyu:3.7"], "君子无所争，其争也君子"),
    ("努力还有意义吗？", "modern_scenario", "failure", "medium",
     ["lunyu:9.19", "lunyu:4.8"], "进吾往也"),
    ("怎么才能不轻易生气？", "modern_scenario", "anger", "medium",
     ["lunyu:1.1", "lunyu:15.28"], "不愠 + 众恶之必察焉"),
    ("什么是仁？", "classical_concept", "meaning", "easy",
     ["lunyu:12.1", "lunyu:6.30", "commentary:12.1"], "克己复礼 + 己欲立而立人"),
    ("如何与人相处才得体？", "modern_scenario", "friendship", "medium",
     ["lunyu:12.2", "lunyu:1.12"], "己所不欲勿施于人 + 礼之用和为贵"),
    ("我很穷，很自卑", "modern_scenario", "self_doubt", "hard",
     ["lunyu:6.11", "lunyu:4.5"], "一箪食一瓢饮"),
    ("怎么判断一个人值不值得深交？", "modern_scenario", "friendship", "medium",
     ["lunyu:16.4", "lunyu:1.8"], "益者三友 + 无友不如己者"),
    ("无为而治是什么意思？", "classical_concept", "meaning", "medium",
     ["debate:laozi:daodejing-22-01", "debate:laozi:daodejing-33-01"], "不争 + 自知"),
    ("不争真的有用吗？", "modern_scenario", "competition", "hard",
     ["debate:laozi:daodejing-22-01", "debate:laozi:daodejing-08-01"], "夫唯不争"),
    ("知足常乐有道理吗？", "modern_scenario", "money", "medium",
     ["debate:laozi:daodejing-44-01"], "知足不辱"),
    ("上善若水应该怎么理解？", "classical_concept", "meaning", "easy",
     ["debate:laozi:daodejing-08-01"], "水善利万物而不争"),
    ("兼爱是什么主张？", "classical_concept", "justice", "medium",
     ["debate:mozi:mozi-jianai-01", "debate:mozi:mozi-jianai-02"], "兼相爱交相利"),
    ("为什么要自食其力？", "modern_scenario", "responsibility", "medium",
     ["debate:mozi:mozi-feile-01"], "赖其力者生"),
    ("法治和公平怎么兼顾？", "modern_scenario", "fairness", "hard",
     ["debate:hanfeizi:hanfeizi-youdu-01"], "法不阿贵"),
    ("奖惩制度该怎么设计？", "modern_scenario", "leadership", "medium",
     ["debate:hanfeizi:hanfeizi-erbing-01"], "赏罚者邦之利器"),
    ("时代变了，旧规则要不要改？", "modern_scenario", "choice", "hard",
     ["debate:hanfeizi:hanfeizi-wuzhu-01"], "世异则事异"),
    ("为什么事情没成就到处说？", "modern_scenario", "workplace_conflict", "medium",
     ["debate:hanfeizi:hanfeizi-wai-chu-shuo-01"], "事以密成"),
    ("读书到底为了什么？", "modern_scenario", "meaning", "medium",
     ["lunyu:19.6", "lunyu:19.7"], "博学笃志 + 学以致其道"),
    ("该不该相信鬼神？", "classical_concept", "meaning", "medium",
     ["lunyu:6.22", "lunyu:11.12"], "敬鬼神而远之"),
    ("怎么进行自我修养？", "modern_scenario", "meaning", "medium",
     ["lunyu:14.42", "lunyu:12.1"], "修己以敬"),
    ("君子和小人的区别是什么？", "classical_concept", "meaning", "easy",
     ["lunyu:4.16", "lunyu:2.14"], "喻于义/喻于利 + 周而不比"),
    ("遇到流言蜚语怎么办？", "modern_scenario", "workplace_conflict", "medium",
     ["lunyu:15.28", "lunyu:1.16"], "众恶之必察焉"),
    ("怎么面对孤独？", "modern_scenario", "loneliness", "medium",
     ["lunyu:4.24", "lunyu:1.1"], "讷于言敏于行 + 人不知而不愠"),
    ("孝和事业冲突时怎么办？", "modern_scenario", "parent_child", "hard",
     ["lunyu:1.6", "lunyu:2.5"], "入则孝出则弟"),
    ("如何对待下属的错误？", "modern_scenario", "leadership", "medium",
     ["lunyu:2.19", "lunyu:1.8"], "举直错诸枉 + 过则勿惮改"),
    ("总是后悔过去的选择", "modern_scenario", "choice", "medium",
     ["lunyu:18.x"], "往者不可谏来者犹可追"),
    ("怎么看待命运？", "classical_concept", "meaning", "hard",
     ["lunyu:20.3", "lunyu:2.4"], "不知命无以为君子 + 知天命"),
]

# ---------------------------------------------------------------- quote verification
# (quote, claimed_source, exists, exact, source_correct, correct_source, trust_state)

QUOTE_VERIFICATION = [
    ("己所不欲，勿施于人。", "《论语·卫灵公》", True, True, True, "《论语·卫灵公》", "verified"),
    ("己所不欲，勿施于人。", "《论语·颜渊》", True, True, True, "《论语·颜渊》", "verified"),
    ("己所不欲，勿施于人。", "《孟子·公孙丑上》", True, True, False, "《论语·卫灵公》", "citation_corrected"),
    ("己所不欲，勿施于人。", "《论语·学而》", True, True, False, "《论语·卫灵公》", "citation_corrected"),
    ("上善若水，水善利万物而不争。", "《道德经·第八章》", True, True, True, "《道德经·第八章》", "verified"),
    ("上善若水，水善利万物而不争。", "《庄子·逍遥游》", True, True, False, "《道德经·第八章》", "citation_corrected"),
    ("学而时习之，不亦说乎？", "《论语·学而》", True, True, True, "《论语·学而》", "verified"),
    ("温故而知新，可以为师矣。", "《论语·为政》", True, True, True, "《论语·为政》", "verified"),
    ("学而不思则罔，思而不学则殆。", "《论语·为政》", True, True, True, "《论语·为政》", "verified"),
    ("三人行，必有我师焉。", "《论语·述而》", True, True, True, "《论语·述而》", "verified"),
    ("士不可以不弘毅，任重而道远。", "《论语·泰伯》", True, True, True, "《论语·泰伯》", "verified"),
    ("君子喻于义，小人喻于利。", "《论语·里仁》", True, True, True, "《论语·里仁》", "verified"),
    ("法不阿贵，绳不挠曲。", "《韩非子·有度》", True, True, True, "《韩非子·有度》", "verified"),
    ("赖其力者生，不赖其力者不生。", "《墨子·非乐上》", True, True, True, "《墨子·非乐上》", "verified"),
    ("知人者智，自知者明。", "《道德经·第三十三章》", True, True, True, "《道德经·第三十三章》", "verified"),
    # normalized-only match (punctuation differs) -> quote_relaxed
    ("己所不欲勿施于人", "《论语·卫灵公》", True, False, True, "《论语·卫灵公》", "quote_relaxed"),
    # traditional variant -> normalized match
    ("己所不欲，勿施於人。", "《论语·卫灵公》", True, False, True, "《论语·卫灵公》", "quote_relaxed"),
    # partial quote -> exists as substring, not exact
    ("勿施于人", "《论语·卫灵公》", True, False, True, "《论语·卫灵公》", "quote_relaxed"),
    # absent from corpus
    ("以德报怨。", "《孟子·公孙丑上》", False, False, False, "", "insufficient_evidence"),
    ("天行健，君子以自强不息。", "《周易》", False, False, False, "", "insufficient_evidence"),
    ("知行合一。", "《传习录》", False, False, False, "", "insufficient_evidence"),
]

# ---------------------------------------------------------------- source attribution
# (quote, claimed_source, expected_source, source_correct, variant_type)

SOURCE_ATTRIBUTION = [
    ("己所不欲，勿施于人。", "《论语·卫灵公》", "《论语·卫灵公》", True, "correct"),
    ("己所不欲，勿施于人。", "《孟子·公孙丑上》", "《论语·卫灵公》", False, "wrong_book"),
    ("己所不欲，勿施于人。", "《论语·学而》", "《论语·卫灵公》", False, "wrong_chapter"),
    ("上善若水，水善利万物而不争。", "《道德经·第八章》", "《道德经·第八章》", True, "correct"),
    ("上善若水，水善利万物而不争。", "《庄子·逍遥游》", "《道德经·第八章》", False, "wrong_book"),
    ("学而时习之，不亦说乎？", "《论语·学而》", "《论语·学而》", True, "correct"),
    ("学而时习之，不亦说乎？", "《论语·为政》", "《论语·学而》", False, "wrong_chapter"),
    ("温故而知新，可以为师矣。", "《论语·为政》", "《论语·为政》", True, "correct"),
    ("士不可以不弘毅，任重而道远。", "《论语·泰伯》", "《论语·泰伯》", True, "correct"),
    ("士不可以不弘毅，任重而道远。", "《论语·子罕》", "《论语·泰伯》", False, "wrong_chapter"),
    ("法不阿贵，绳不挠曲。", "《韩非子·有度》", "《韩非子·有度》", True, "correct"),
    ("法不阿贵，绳不挠曲。", "《商君书》", "《韩非子·有度》", False, "wrong_book"),
    ("赖其力者生，不赖其力者不生。", "《墨子·非乐上》", "《墨子·非乐上》", True, "correct"),
    ("赖其力者生，不赖其力者不生。", "《墨子·兼爱上》", "《墨子·非乐上》", False, "wrong_chapter"),
    ("知人者智，自知者明。", "《道德经·第三十三章》", "《道德经·第三十三章》", True, "correct"),
    ("君子喻于义，小人喻于利。", "《论语·里仁》", "《论语·里仁》", True, "correct"),
    ("三人行，必有我师焉。", "《论语·述而》", "《论语·述而》", True, "correct"),
    # 注：不存在的引文（如「以德报怨」）不属于出处归属数据集，已移入
    # adversarial_quotes（aq-0003），因为「出处是否正确」对不存在文本无定义。
    ("己所不欲，勿施于人。", "《论语·颜渊》", "《论语·颜渊》", True, "correct"),
]

# ---------------------------------------------------------------- modern to classic

MODERN_TO_CLASSIC = [
    ("同事抢了我的功劳，我该不该跟他撕破脸？", "workplace_conflict",
     ["self", "peer"], ["fairness", "relationship"], ["anger", "frustration"],
     ["confront", "communicate", "escalate", "tolerate", "leave"],
     ["义", "礼", "正名", "不争", "尚贤", "名实", "赏罚"], ["义", "正名"]),
    ("被领导误解了，我要不要解释？", "workplace_conflict",
     ["self", "superior"], ["relationship", "reputation"], ["frustration", "self_doubt"],
     ["explain", "wait", "escalate", "leave"],
     ["不患人之不己知", "讷于言而敏于行", "信"], ["不患人之不己知"]),
    ("我很想快速成功", "career",
     ["self"], ["achievement", "time"], ["ambition", "anxiety"],
     ["rush", "persist", "reconsider"],
     ["欲速则不达", "见小利则大事不成"], ["欲速则不达"]),
    ("面对利益诱惑，该怎么选？", "money",
     ["self", "other"], ["fairness", "interest"], ["desire", "conflict"],
     ["take", "refuse", "negotiate"],
     ["义", "利", "君子喻于义"], ["义", "利"]),
    ("如何交到真朋友？", "friendship",
     ["self", "peer"], ["trust", "relationship"], ["hope", "self_doubt"],
     ["approach", "observe", "withdraw"],
     ["益者三友", "信", "友直友谅友多闻"], ["信"]),
    ("什么是真正的孝顺？", "parent_child",
     ["self", "parent"], ["obligation", "respect"], ["guilt", "love"],
     ["obey", "communicate", "boundary"],
     ["孝", "敬", "礼", "色难"], ["孝", "敬"]),
    ("如何领导一个团队？", "leadership",
     ["self", "subordinate"], ["authority", "fairness"], ["responsibility"],
     ["lead_by_example", "rule_by_law", "reward_punish"],
     ["为政以德", "正名", "赏罚", "法"], ["为政以德"]),
    ("怎么才能不轻易生气？", "anger",
     ["self", "other"], ["emotion_control"], ["anger", "frustration"],
     ["suppress", "reflect", "confront"],
     ["不愠", "恕", "察"], ["恕"]),
    ("无为而治是什么意思？", "meaning",
     ["self"], ["action", "governance"], ["confusion"],
     ["act", "refrain", "observe"],
     ["无为", "不争", "自然"], ["无为", "不争"]),
    ("奖惩制度该怎么设计？", "leadership",
     ["self", "subordinate"], ["incentive", "fairness"], ["responsibility"],
     ["reward", "punish", "balance"],
     ["赏罚", "法", "名实"], ["赏罚", "法"]),
    ("时代变了，旧规则要不要改？", "choice",
     ["self", "institution"], ["tradition", "change"], ["uncertainty"],
     ["reform", "preserve", "hybrid"],
     ["世异则事异", "变", "礼"], ["世异则事异"]),
    ("总是后悔过去的选择", "choice",
     ["self"], ["regret", "time"], ["guilt", "sadness"],
     ["ruminate", "accept", "move_on"],
     ["往者不可谏", "来者犹可追"], ["往者不可谏"]),
    ("怎么看待命运？", "meaning",
     ["self", "heaven"], ["fate", "agency"], ["acceptance", "anxiety"],
     ["accept", "resist", "understand"],
     ["天命", "知命", "命"], ["知命"]),
    ("我很穷，很自卑", "self_doubt",
     ["self", "peer"], ["worth", "wealth"], ["shame", "anxiety"],
     ["compare", "accept", "strive"],
     ["贫而乐", "安贫", "义"], ["贫而乐"]),
    ("怎么看待职场里的竞争？", "competition",
     ["self", "peer"], ["competition", "fairness"], ["anxiety", "ambition"],
     ["compete", "cooperate", "withdraw"],
     ["不争", "君子无所争", "争也君子"], ["君子无所争"]),
    ("遇到流言蜚语怎么办？", "workplace_conflict",
     ["self", "peer", "group"], ["reputation", "fairness"], ["anger", "helplessness"],
     ["ignore", "clarify", "confront"],
     ["察", "不患人之不己知", "信"], ["察"]),
    ("怎么面对孤独？", "loneliness",
     ["self"], ["belonging"], ["loneliness", "sadness"],
     ["connect", "accept", "create"],
     ["人不知而不愠", "讷于言而敏于行"], ["人不知而不愠"]),
    ("该不该相信鬼神？", "meaning",
     ["self", "unknown"], ["belief", "rationality"], ["doubt", "fear"],
     ["believe", "distance", "ignore"],
     ["敬鬼神而远之", "未知生焉知死"], ["敬鬼神而远之"]),
    ("如何自我修养？", "meaning",
     ["self"], ["self_improvement"], ["determination"],
     ["study", "practice", "reflect"],
     ["修己以敬", "克己复礼", "学"], ["修己以敬", "克己复礼"]),
    ("为什么事情没成就到处说？", "workplace_conflict",
     ["self", "peer"], ["reputation", "prudence"], ["impulse", "regret"],
     ["announce", "keep_quiet", "delay"],
     ["事以密成", "讷于言而敏于行"], ["事以密成"]),
]

# ---------------------------------------------------------------- school consistency

SCHOOL_CONSISTENCY = [
    ("confucius", ["论语"], ["道德经", "庄子", "墨子", "韩非子", "商君书", "传习录"],
     "我该不该躺平"),
    ("confucius", ["论语"], ["道德经", "庄子", "墨子", "韩非子", "商君书", "传习录"],
     "什么是仁"),
    ("confucius", ["论语"], ["道德经", "庄子", "墨子", "韩非子", "商君书", "传习录"],
     "如何面对失败"),
    ("laozi", ["道德经"], ["论语", "孟子", "墨子", "韩非子", "商君书", "传习录"],
     "什么是无为"),
    ("laozi", ["道德经"], ["论语", "孟子", "墨子", "韩非子", "商君书", "传习录"],
     "竞争太累了怎么办"),
    ("laozi", ["道德经"], ["论语", "孟子", "墨子", "韩非子", "商君书", "传习录"],
     "知足常乐"),
    ("mozi", ["墨子"], ["论语", "孟子", "道德经", "庄子", "韩非子", "商君书"],
     "为什么要自食其力"),
    ("mozi", ["墨子"], ["论语", "孟子", "道德经", "庄子", "韩非子", "商君书"],
     "如何对待陌生人"),
    ("mozi", ["墨子"], ["论语", "孟子", "道德经", "庄子", "韩非子", "商君书"],
     "战争该不该打"),
    ("hanfeizi", ["韩非子"], ["论语", "孟子", "道德经", "庄子", "墨子", "商君书"],
     "如何管理下属"),
    ("hanfeizi", ["韩非子"], ["论语", "孟子", "道德经", "庄子", "墨子", "商君书"],
     "赏罚怎么定"),
    ("hanfeizi", ["韩非子"], ["论语", "孟子", "道德经", "庄子", "墨子", "商君书"],
     "规则要不要变"),
    ("li_bai", ["李白诗文"], ["论语", "道德经", "墨子", "韩非子"], "人生得意时该怎么做"),
    ("su_shi", ["苏轼词文"], ["论语", "道德经", "墨子", "韩非子"], "如何面对风雨"),
    ("fan_zhongyan", ["范仲淹文"], ["论语", "道德经", "墨子", "韩非子"], "个人和天下哪个先"),
    ("wang_anshi", ["王安石诗文"], ["论语", "道德经", "墨子", "韩非子"], "如何看得更远"),
    ("zhuge_liang", ["诸葛亮文"], ["论语", "道德经", "墨子", "韩非子"], "如何修养心性"),
]

# ---------------------------------------------------------------- adversarial (ch.16, 12 categories)

ADVERSARIAL = [
    # 1. brief ch.16 example #1: real quote, cross-school wrong attribution
    ("aq-0001", "real_quote_wrong_source_cross_school",
     "己所不欲，勿施于人。", "《孟子·公孙丑上》", "mencius",
     True, False, "citation_corrected",
     "brief ch.16 第一例。当前实现实测 FAIL：verifiable=True/all_verified，且错误出处被保留。"),
    # 2. brief ch.16 example #2: 上善若水 attributed to 庄子
    ("aq-0002", "real_quote_wrong_source_cross_school",
     "上善若水，水善利万物而不争。", "《庄子·逍遥游》", "laozi",
     True, False, "citation_corrected",
     "brief ch.16 第二例：上善若水是否庄子。真实出处《道德经·第八章》。"),
    # 6. 以德报怨 — absent from corpus
    ("aq-0003", "quote_absent_wrong_attribution",
     "以德报怨。", "《孟子·公孙丑上》", "mencius",
     False, False, "insufficient_evidence",
     "brief ch.16：以德报怨出自孟子吗。实测该句不在当前语料中（0 命中）。"),
    # real quote + wrong chapter (same book)
    ("aq-0004", "real_quote_wrong_source_same_book",
     "学而时习之，不亦说乎？", "《论语·为政》", "confucius",
     True, False, "citation_corrected",
     "同书错篇：真实出处《论语·学而》。"),
    # 7. fabricated classical
    ("aq-0005", "fake_classic",
     "学而不厌，诲人不倦，仁者无敌于天下。", "《论语·述而》", "confucius",
     False, False, "insufficient_evidence",
     "拼凑伪古文：语料无此句。"),
    ("aq-0006", "fake_classic",
     "君子以德服人，小人以力服人，故德者本也。", "《论语·颜渊》", "confucius",
     False, False, "insufficient_evidence",
     "伪古文，语料无此句。"),
    # 9. punctuation variant
    ("aq-0007", "punctuation_variant",
     "己所不欲勿施于人", "《论语·卫灵公》", "confucius",
     True, True, "verified",
     "同句去标点，归一化后应命中且出处正确。"),
    # 10. traditional variant
    ("aq-0008", "traditional_variant",
     "己所不欲，勿施於人。", "《论语·卫灵公》", "confucius",
     True, True, "verified",
     "繁体版本，繁简归一化后应命中且出处正确。"),
    ("aq-0009", "traditional_variant",
     "上善若水，水善利萬物而不爭。", "《道德经·第八章》", "laozi",
     True, True, "verified",
     "繁体版本（道德经）。"),
    # 11. partial quote
    ("aq-0010", "partial_quote",
     "勿施于人", "《论语·卫灵公》", "confucius",
     True, False, "quote_relaxed",
     "部分引用：作为子串存在，但非完整原文，不得标为 exact。"),
    ("aq-0011", "partial_quote",
     "士不可以不弘毅", "《论语·泰伯》", "confucius",
     True, False, "quote_relaxed",
     "部分引用：与 lunyu.json 8.7 及 debate:confucius:lunyu-taibo-01 构成摘句关系。"),
    # 12. internet chicken soup attributed to Confucius
    ("aq-0012", "internet_chicken_soup",
     "你要悄悄拔尖，然后惊艳所有人。", "《论语》", "confucius",
     False, False, "insufficient_evidence",
     "网络鸡汤冒充孔子。"),
    ("aq-0013", "internet_chicken_soup",
     "岁月静好，是因为有人替你负重前行。", "《论语》", "confucius",
     False, False, "insufficient_evidence",
     "网络鸡汤冒充孔子。"),
    ("aq-0014", "internet_chicken_soup",
     "努力就一定成功，坚持就有回报。", "《道德经》", "laozi",
     False, False, "insufficient_evidence",
     "brief ch.16：老子说努力就一定成功吗。语料无此说法。"),
    # 2-char fragment negative
    ("aq-0015", "two_char_fragment",
     "君子", "《论语·学而》", "confucius",
     True, False, "quote_relaxed",
     "2 字片段：语料中存在该词，但不得据此判 verified（需长度下限）。当前实现实测判 True。"),
    ("aq-0016", "two_char_fragment",
     "无为", "《道德经》", "laozi",
     False, False, "insufficient_evidence",
     "2 字片段且该词不在当前语料文本中（0 命中）。"),
    # modern question presupposing a classical answer (ch.16 #3/#4/#5)
    ("aq-0017", "modern_question_no_classic",
     "孔子怎么看职场PUA？", "《论语》", "confucius",
     False, False, "insufficient_evidence",
     "brief ch.16 第三例：现代问题，语料无直接原典；必须经概念映射或诚实拒答，不得编造古文。"),
    ("aq-0018", "modern_question_no_classic",
     "韩非子会建议我辞职吗？", "《韩非子》", "hanfeizi",
     False, False, "insufficient_evidence",
     "brief ch.16 第四例：现代问题，语料无直接原典。"),
    ("aq-0019", "modern_question_no_classic",
     "老子说努力就一定成功吗？", "《道德经》", "laozi",
     False, False, "insufficient_evidence",
     "brief ch.16 第五例：须否证或拒答，不得虚构。"),
    # real quote, cross-school for a different sage (extra coverage)
    ("aq-0020", "real_quote_wrong_source_cross_school",
     "法不阿贵，绳不挠曲。", "《论语·里仁》", "confucius",
     True, False, "citation_corrected",
     "真实韩非子原文被归到论语：跨派错出处。"),
]

# ---------------------------------------------------------------- unsupported questions

UNSUPPORTED = [
    ("uq-0001", "量子计算机如何改变儒家伦理？", "no_corpus_evidence",
     "语料不含量子计算相关文本。"),
    ("uq-0002", "如何用《论语》指导短视频运营？", "no_corpus_evidence",
     "现代平台运营概念，语料无对应原典。"),
    ("uq-0003", "孔子对人工智能的看法是什么？", "anachronistic",
     "人物早于该技术，不可能有原典依据。"),
    ("uq-0004", "请给出《庄子·逍遥游》全文。", "book_not_in_corpus",
     "庄子不在当前语料中（0 条）。"),
    ("uq-0005", "孟子怎么看待绩效考核？", "book_not_in_corpus",
     "孟子不在当前语料中（0 条）。"),
    ("uq-0006", "《孙子兵法》里有哪些管理方法？", "book_not_in_corpus",
     "孙子兵法不在当前语料中（0 条）。"),
    ("uq-0007", "王阳明如何论述心即理？", "book_not_in_corpus",
     "传习录不在当前语料中（0 条）。"),
    ("uq-0008", "请引用《大学》原文说明修身。", "book_not_in_corpus",
     "大学不在当前语料中（0 条）。"),
    ("uq-0009", "如何面对亲人的离世？", "partial_corpus_support",
     "语料仅有 11.12/15.9 等有限相关条目；若检索无命中必须拒答，不得编造古文。"),
    ("uq-0010", "请告诉我《道德经》第八十一章的原文。", "chapter_not_in_corpus",
     "语料仅含道德经 4 条摘句，无该章全文。"),
    ("uq-0011", "墨子对人工智能伦理有什么预见？", "anachronistic",
     "时代错置，无原典依据。"),
    ("uq-0012", "帮我写一段孔子风格的原创古文。", "request_to_generate_classic",
     "要求生成伪原典，必须拒绝（PROJECT-BRIEF 禁止 AI 生成古籍当权威原典）。"),
]


def _write(name: str, records: List[Dict[str, Any]], eval_dir: Path) -> Path:
    path = eval_dir / S.DATASETS[name]["file"]
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


def build(eval_dir: Path, corpus_index: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}

    # ---- retrieval_gold
    recs = []
    for i, (q, qtype, scen, diff, refs, note) in enumerate(RETRIEVAL_GOLD, 1):
        for ref in refs:
            assert ref in corpus_index, f"fabricated ref in retrieval_gold: {ref}"
        books = sorted({S.book_of(r, corpus_index) for r in refs if S.book_of(r, corpus_index)})
        recs.append({
            "id": f"rg-{i:04d}", "dataset": "retrieval_gold", "provenance": "derived",
            "query": q, "query_type": qtype, "scenario": scen,
            "expected_passage_ids": refs, "expected_books": books,
            "difficulty": diff, "notes": note,
            "generation_method": GENERATION_METHOD,
        })
    _write("retrieval_gold", recs, eval_dir); counts["retrieval_gold"] = len(recs)

    # ---- quote_verification
    recs = []
    for i, (q, src, ex, em, sc, cs, ts) in enumerate(QUOTE_VERIFICATION, 1):
        recs.append({
            "id": f"qv-{i:04d}", "dataset": "quote_verification", "provenance": "derived",
            "quote": q, "claimed_source": src,
            "expected": {"quote_exists": ex, "exact_match": em, "source_correct": sc,
                         "correct_source": cs, "trust_state": ts},
            "generation_method": GENERATION_METHOD,
        })
    _write("quote_verification", recs, eval_dir); counts["quote_verification"] = len(recs)

    # ---- source_attribution
    recs = []
    for i, (q, src, esrc, sc, vt) in enumerate(SOURCE_ATTRIBUTION, 1):
        recs.append({
            "id": f"sa-{i:04d}", "dataset": "source_attribution", "provenance": "derived",
            "quote": q, "claimed_source": src, "expected_source": esrc,
            "expected_source_correct": sc, "variant_type": vt,
            "generation_method": GENERATION_METHOD,
        })
    _write("source_attribution", recs, eval_dir); counts["source_attribution"] = len(recs)

    # ---- modern_to_classic
    recs = []
    for i, (q, scen, actors, conflict, emotion, choices, concepts, req) in enumerate(
            MODERN_TO_CLASSIC, 1):
        recs.append({
            "id": f"mc-{i:04d}", "dataset": "modern_to_classic", "provenance": "derived",
            "modern_query": q,
            "expected": {"scene": scen, "actors": actors, "conflict": conflict,
                         "emotion": emotion, "choices": choices, "concepts": concepts},
            "required_concepts": req,
            "generation_method": GENERATION_METHOD,
        })
    _write("modern_to_classic", recs, eval_dir); counts["modern_to_classic"] = len(recs)

    # ---- school_consistency
    recs = []
    for i, (sage, allowed, forbidden, q) in enumerate(SCHOOL_CONSISTENCY, 1):
        recs.append({
            "id": f"sc-{i:04d}", "dataset": "school_consistency", "provenance": "derived",
            "sage_key": sage, "allowed_books": allowed, "forbidden_books": forbidden,
            "query": q, "generation_method": GENERATION_METHOD,
        })
    _write("school_consistency", recs, eval_dir); counts["school_consistency"] = len(recs)

    # ---- adversarial_quotes
    recs = []
    for (rid, atype, quote, src, sage, exists, verifiable, ts, note) in ADVERSARIAL:
        recs.append({
            "id": rid, "dataset": "adversarial_quotes", "provenance": "derived",
            "attack_type": atype,
            "input": {"quote": quote, "claimed_source": src},
            "expected": {"quote_exists": exists, "verifiable": verifiable,
                         "trust_state": ts, "must_not_display_as_classic": not verifiable},
            "sage_key": sage, "note": note,
            "generation_method": GENERATION_METHOD,
        })
    _write("adversarial_quotes", recs, eval_dir); counts["adversarial_quotes"] = len(recs)

    # ---- unsupported_questions
    recs = []
    for (rid, q, reason, note) in UNSUPPORTED:
        recs.append({
            "id": rid, "dataset": "unsupported_questions", "provenance": "derived",
            "question": q, "out_of_scope_reason": reason,
            "expected": {"must_refuse": True, "trust_state": "insufficient_evidence",
                         "required_phrase": S.REQUIRED_REFUSAL_PHRASE},
            "generation_method": GENERATION_METHOD,
        })
    _write("unsupported_questions", recs, eval_dir); counts["unsupported_questions"] = len(recs)

    return counts


def main() -> int:
    root = S.repo_root()
    eval_dir = root / "eval"
    eval_dir.mkdir(exist_ok=True)
    corpus_index = S.load_corpus_index(root)
    counts = build(eval_dir, corpus_index)
    print(f"corpus passage ids: {len(corpus_index)}")
    for k, v in counts.items():
        print(f"  {k:<24} {v}")
    print(f"TOTAL {sum(counts.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
