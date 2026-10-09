"""
悟典 - Trust State 判定规则（PHASE 5 / P5-04、P5-07）

单一真值来源
------------
四态**枚举**已在 ``app.schemas.knowledge.TrustState`` 冻结
（``docs/kb-v1/02-architecture.md`` §9.2），本模块**不重新定义枚举**，
只承载**判定规则**，避免两套真值分叉。

四态判定规则（与 §9.2 冻结表逐行一致）
-------------------------------------
判定按**优先级**自上而下短路，保证任意输入组合都有唯一确定结果：

1. ``quote_exists == False``
   → ``insufficient_evidence``
   该句在知识库中**不存在**（或短于长度下限、无法判定）。**禁止编造古文**，
   必须输出 :data:`INSUFFICIENT_EVIDENCE_MESSAGE`（PROJECT-BRIEF 第十二章）。
2. ``quote_exists == True`` 且 ``source_correct == False``
   → ``citation_corrected``（须给出 ``correct_source``）
   文本真实存在，但声称出处错误 —— 这正是 PROJECT-BRIEF 第十一章要求
   能独立表达的组合（``quote_exists=true & source_correct=false``）。
3. ``quote_exists == True`` 且 ``source_correct == True`` 且 ``exact_match == True``
   → ``verified``
   逐字命中且出处正确，最强状态。
4. ``quote_exists == True`` 且 ``source_correct == True`` 且 ``exact_match == False``
   → ``quote_relaxed``
   仅**归一化后**命中（繁简/标点差异），出处正确但非逐字。

优先级说明
----------
第 2 条（出处错误）优先于第 3/4 条：**出处错误是比"是否逐字"更严重的问题**，
不能因为文本逐字存在就报 ``verified``。这与 ``02-architecture.md`` §9.2
「``citation_corrected`` 须返回 ``correct_source``」的意图一致。

诚实性约束
----------
- 本模块**不**提供任何"默认通过"路径：无法判定即 ``insufficient_evidence``。
- ``verifiable`` 的旧语义（"文本在本次检索结果中互为子串"）**不再**作为通过依据；
  是否可展示为经典原文由 ``quote_exists AND source_correct`` 共同决定
  （见 :func:`is_displayable_as_classic`）。
"""
from __future__ import annotations

from typing import Optional

from app.schemas.knowledge import TRUST_STATES, TrustState

# ============================================================
# 拒答文案（PROJECT-BRIEF 第十二章，原文照录，不得改写）
# ============================================================

#: 证据不足时的标准拒答文案。**不得**用编造的古文替代。
INSUFFICIENT_EVIDENCE_MESSAGE = (
    "当前知识库没有检索到足够可靠的原典支持这一判断。"
)

#: 出处被纠正时的提示模板。
CITATION_CORRECTED_MESSAGE_TEMPLATE = (
    "该句确实存在于知识库中，但出处并非{claimed}；正确出处为{correct}。"
)

#: 仅归一化命中（繁简/标点差异）时的提示模板。
QUOTE_RELAXED_MESSAGE_TEMPLATE = (
    "该句与知识库中的原文仅在标点或繁简写法上有差异（{source}），已按归一化匹配。"
)


# ============================================================
# 判定规则
# ============================================================

def decide_trust_state(
    *,
    quote_exists: bool,
    source_correct: bool,
    exact_match: bool,
    match_type: str = "exact",
    completeness_gate: bool = False,
    is_l1: bool = False,
) -> TrustState:
    """按 CONTRACT-001 v2 §4 判定 Trust State（四态之一）。

    Args:
        quote_exists: 该句是否**真实存在**于知识库（经归一化 + 长度下限判定）。
        source_correct: 声称出处是否与真实出处一致。
        exact_match: 是否为**连续逐字子串**（§2.2；含归一化，不要求等于整条 passage）。
        match_type: ``exact`` / ``normalized`` / ``partial`` / ``none``（仅记录用）。
        completeness_gate: 是否通过完整性门（§3.1，``len(N(q)) >= MIN_FULL_QUOTE_CHARS``）。
        is_l1: 命中条目是否为 L1 原典（``text_type == "original"``，§3.2 / RC4）。

    Returns:
        ``verified`` / ``citation_corrected`` / ``quote_relaxed`` / ``insufficient_evidence``

    默认值取**保守**方向（``completeness_gate=False`` / ``is_l1=False``）：
    调用方若未显式提供这两项，就拿不到 ``verified``，而不是"缺省即通过"。
    这与本项目「缺省即不可验证」的纪律一致。

    §4 规则（自上而下，命中即返回）：

    1. ``not quote_exists``                                  → ``insufficient_evidence``
    2. ``quote_exists and not source_correct``               → ``citation_corrected``
    3. ``quote_exists and exact_match and source_correct
        and completeness_gate and is_l1``                    → ``verified``
    4. 其余                                                  → ``quote_relaxed``

    与旧实现的差异（CONTRACT-001 v2 §4 / RC3 / RC4）：

    - 旧规则 3 要求 ``match_type == "exact"``，而 ``match_type`` 只在「引文等于
      **整条** passage」时才为 ``exact``，导致 ``verified`` 在真实语料下几乎不可达。
      现按 §4 改为由 ``exact_match`` + 完整性门 + L1 决定。
    - 摘句（``partial``）本就不满足完整性门，故仍不可能 ``verified``（保持 P5-05 B2）。
    - **注疏（L2）不得**因为逐字存在而被判 ``verified``（RC4）。
    """
    # 1. 文本不存在 → 证据不足（禁止编造）
    if not quote_exists:
        return "insufficient_evidence"

    # 2. 文本存在但出处错误 → citation_corrected（优先于 verified）
    if not source_correct:
        return "citation_corrected"

    # 3. 文本存在 + 逐字连续命中 + 出处正确 + 过完整性门 + L1 → verified
    if exact_match and completeness_gate and is_l1:
        return "verified"

    # 4. 其余（含摘句、注疏、未过完整性门）→ quote_relaxed（**不可**作为经典原文展示）
    return "quote_relaxed"


def is_displayable_as_classic(trust_state: TrustState) -> bool:
    """该状态下，文本是否**可**作为"经典原文"展示。

    CONTRACT-001 v2 §3.2 / RC3：**恒等于** ``trust_state == "verified"``。

    - ``verified``：存在 + 逐字连续 + 出处正确 + 完整性门 + L1 → 可展示。
    - ``citation_corrected``：文本真实，但**必须**改用 ``correct_source`` 展示 → False。
    - ``quote_relaxed``：**不可**展示（CONTRACT-001 v2 有意变更）。
      它包括摘句、注疏，以及未过完整性门的引用 —— 都不是「完整经典原文」。
    - ``insufficient_evidence``：不得展示。

    RC3 说明：旧实现返回 ``trust_state in ("verified", "quote_relaxed")``，
    即把 ``quote_relaxed`` 也视为可展示。这与 §3.2 的四项合取要求矛盾：
    既然 §4 规则 3 是通往 ``verified`` 的唯一路径，
    「可展示」就**恒等于** ``verified``。任何"再加参数"的方案在逻辑上不可能
    让 ``quote_relaxed`` 变为可展示，故这里直接取恒等式。
    """
    return trust_state == "verified"


def is_verifiable(trust_state: TrustState, match_type: str = "exact") -> bool:
    """``verifiable`` 的统一口径：文本存在 **且** 出处正确 **且** 非摘句。

    取代旧语义「与本次检索结果互为子串」。``citation_corrected``
    **不算** verifiable —— 因为原声称出处是错的。

    ``match_type="partial"``（摘句）**不算** verifiable：摘句只能说明"这些字
    在原典里出现过"，不足以支撑一条思想结论（P5-05 用例 B2
    「标为 partial 且不计入 verified」）。
    """
    if match_type == "partial":
        return False
    return trust_state in ("verified", "quote_relaxed")


def explain(trust_state: TrustState) -> str:
    """给出该状态对应的**诚实**中文说明（供 API / 前端展示）。"""
    if trust_state == "insufficient_evidence":
        return INSUFFICIENT_EVIDENCE_MESSAGE
    if trust_state == "citation_corrected":
        return "该句真实存在，但声称出处有误，已按正确出处修正。"
    if trust_state == "quote_relaxed":
        return "该句真实存在且出处正确，但仅在归一化（标点/繁简）后与原文一致。"
    if trust_state == "verified":
        return "该句逐字存在于知识库，且出处正确。"
    # 不可达：TrustState 为 Literal 四值，由 pydantic 保证
    raise ValueError(f"未知 trust_state: {trust_state!r}")


def build_corrected_message(
    *, claimed_source: Optional[str], correct_source: Optional[str],
) -> Optional[str]:
    """构造 ``citation_corrected`` 的用户可读提示；缺少必要信息时返回 ``None``。"""
    if not (correct_source or "").strip():
        return None
    claimed = (claimed_source or "").strip() or "未标注出处"
    return CITATION_CORRECTED_MESSAGE_TEMPLATE.format(
        claimed=claimed, correct=correct_source,
    )


__all__ = [
    "INSUFFICIENT_EVIDENCE_MESSAGE",
    "CITATION_CORRECTED_MESSAGE_TEMPLATE",
    "QUOTE_RELAXED_MESSAGE_TEMPLATE",
    "TRUST_STATES",
    "TrustState",
    "decide_trust_state",
    "is_displayable_as_classic",
    "is_verifiable",
    "explain",
    "build_corrected_message",
]
