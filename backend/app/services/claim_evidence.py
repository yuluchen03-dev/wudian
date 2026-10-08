"""
悟典 - Claim-Evidence 绑定（PHASE 5 / PROJECT-BRIEF 第十三章）

职责
----
PROJECT-BRIEF 第十三章要求：**不能只验证引用**。最终答案必须拆成若干 claim，
每个核心思想结论都要绑定到证据，并给出该 claim 的验证状态。

本模块提供：
1. ``Claim`` / ``ClaimVerification`` 数据契约（复用 ``schemas.knowledge`` 已冻结的
   ``EvidenceItem`` / ``EvidencePack``，不另建第二套真值）。
2. ``bind_claims``：把 (claim 文本, 引用的 evidence_id) 绑定到 Evidence Pack 中的
   真实证据；**引用了 Pack 之外的 evidence_id 一律判为 unsupported**。
3. ``verify_claim``：对单个 claim 做逐字/归一化校验（复用 ``quote_verifier``），
   产出 ``supported`` / ``partially_supported`` / ``unsupported`` 三态。
4. ``coverage``：计算「核心 claim 的证据覆盖率」，供 GATE-8
   「Core Claim Evidence Coverage >= 95%」度量。

设计原则（与项目纪律一致）
------------------------
- **不得编造证据**：claim 引用的 evidence_id 必须存在于传入的 Evidence Pack 中，
  否则判 unsupported —— 不允许凭 claim 文本自行"找"一个出处。
- **不得把"看起来像"当成 supported**：只有 ``quote_verifier`` 判定
  ``quote_exists=True`` 才可能 supported；出处是否一致单独记录，不掩盖。
- **诚实三态**：证据不足时明确 ``unsupported``，由上层走
  ``insufficient_evidence`` 与拒答文案，而不是硬编。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from app.schemas.knowledge import EvidenceItem, EvidencePack, TrustState
from app.services.quote_verifier import verify_quote
from app.services.trust_state import INSUFFICIENT_EVIDENCE_MESSAGE

__all__ = [
    "CLAIM_SUPPORT_STATES",
    "Claim",
    "ClaimBinding",
    "ClaimSupport",
    "ClaimVerificationResult",
    "bind_claims",
    "coverage",
    "extract_claims",
    "verify_claim",
    "verify_claims",
]

#: claim 的支持状态三态（brief 第十三章的 ``verification: supported`` 是其首态）
CLAIM_SUPPORT_STATES = ("supported", "partially_supported", "unsupported")

#: 低于该归一化长度视为「过短片段」，不足以支撑一个思想结论。
#: 与 quote_verifier 的长度下限保持一致的保守值。
_MIN_CLAIM_EVIDENCE_LEN = 4


@dataclass(frozen=True)
class Claim:
    """一个待验证的思想结论。"""

    claim_id: str
    text: str
    #: 该 claim 声称引用的证据 id（必须存在于 EvidencePack 中）
    evidence_ids: Tuple[str, ...] = ()
    #: 是否为「核心 claim」。覆盖率只统计核心 claim（brief 第十三章
    #: 「每个核心思想结论必须有 evidence」）。
    is_core: bool = True


@dataclass
class ClaimBinding:
    """claim 与一条证据的绑定结果。"""

    claim_id: str
    evidence_id: str
    #: 该 evidence_id 是否真的存在于传入的 EvidencePack
    in_pack: bool
    #: 证据原文（仅当 in_pack 为真时有值）
    evidence_original: Optional[str] = None
    evidence_source: Optional[str] = None
    #: quote_verifier 的判定（仅当 in_pack 为真时有值）
    quote_exists: bool = False
    source_correct: bool = False
    correct_source: Optional[str] = None
    trust_state: Optional[TrustState] = None
    reason: str = ""


@dataclass
class ClaimVerificationResult:
    """单个 claim 的验证结果。"""

    claim_id: str
    text: str
    is_core: bool
    support: str  # one of CLAIM_SUPPORT_STATES
    bindings: List[ClaimBinding] = field(default_factory=list)
    message: str = ""

    @property
    def has_evidence(self) -> bool:
        """是否至少绑定到一条**存在于 Pack 且引文真实存在**的证据。"""
        return any(b.in_pack and b.quote_exists for b in self.bindings)


@dataclass
class ClaimSupport:
    """整体验证结果（供 API/前端消费）。"""

    results: List[ClaimVerificationResult] = field(default_factory=list)

    @property
    def core_claims(self) -> List[ClaimVerificationResult]:
        return [r for r in self.results if r.is_core]

    def coverage(self) -> float:
        """核心 claim 的证据覆盖率（0.0–1.0）。

        定义（可自动化复现，供 GATE-8 使用）：
            分子 = 核心 claim 中 ``support != "unsupported"`` 且确实绑定到
                   至少一条真实存在证据的条数
            分母 = 核心 claim 总数
        分母为 0 时返回 0.0（**不返回 1.0** —— 没有核心 claim 不等于覆盖良好，
        避免"空答案拿满分"）。
        """
        core = self.core_claims
        if not core:
            return 0.0
        covered = sum(1 for r in core if r.support != "unsupported" and r.has_evidence)
        return covered / len(core)

    @property
    def unsupported_core_claims(self) -> List[ClaimVerificationResult]:
        return [r for r in self.core_claims if r.support == "unsupported"]


# ---------------------------------------------------------------------------
# claim 抽取
# ---------------------------------------------------------------------------

#: 中文句末标点。用于把一段答案切成候选 claim。
_SENTENCE_SPLIT = re.compile(r"[。！？；\n]+")

#: 明显的「非思想结论」句式，不应作为核心 claim 统计覆盖率：
#: 纯转场、免责声明、以及项目规定的证据不足文案本身。
_NON_CLAIM_PATTERNS = (
    re.compile(r"^以上为"),
    re.compile(r"^白话[:：]"),
    re.compile(r"^注[:：]"),
    re.compile(r"当前知识库没有检索到"),
    re.compile(r"^综上"),
)


def extract_claims(
    answer: str,
    *,
    min_len: int = 6,
    include_non_claims: bool = False,
) -> List[Claim]:
    """把一段答案文本切成候选 claim。

    这是**确定性**切分（不调用 LLM），便于测试与复现。
    过短的句子（< ``min_len``）与明显的转场/免责句式默认被排除，
    避免用"好的""谢谢"这类句子虚增覆盖率分母。

    注意：``include_non_claims=True`` 时保留全部句子，仅用于调试。
    """
    if not answer:
        return []
    claims: List[Claim] = []
    idx = 0
    for raw in _SENTENCE_SPLIT.split(answer):
        text = raw.strip()
        if not text or len(text) < min_len:
            continue
        if not include_non_claims and any(p.search(text) for p in _NON_CLAIM_PATTERNS):
            continue
        idx += 1
        claims.append(Claim(claim_id=f"c{idx}", text=text))
    return claims


# ---------------------------------------------------------------------------
# 绑定与验证
# ---------------------------------------------------------------------------


def _pack_index(pack: EvidencePack) -> Dict[str, EvidenceItem]:
    return {item.evidence_id: item for item in pack.evidence}


def _normalize(text: str) -> str:
    return re.sub(r"[\s，。！？；：、（）()「」『』\"']", "", text or "")


def verify_claim(claim: Claim, pack: EvidencePack) -> ClaimVerificationResult:
    """验证单个 claim。

    判定规则（可自动化复现）：
    - claim 未声明任何 evidence_id            -> unsupported（无证据）
    - 声明的 evidence_id 不在 Pack 中         -> unsupported（**不得编造证据**）
    - 证据存在但引文在语料中找不到            -> unsupported
    - 证据存在且引文真实存在：
        * 出处一致                            -> supported
        * 出处不一致（但引文真实）            -> partially_supported
          （即 brief 第十一章的 citation_corrected：文本真、出处假）
    - 命中的证据原文过短（< _MIN_CLAIM_EVIDENCE_LEN）-> 降级为 unsupported
      （2 字片段不足以支撑一个思想结论）
    """
    bindings: List[ClaimBinding] = []

    if not claim.evidence_ids:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            text=claim.text,
            is_core=claim.is_core,
            support="unsupported",
            bindings=[],
            message=INSUFFICIENT_EVIDENCE_MESSAGE,
        )

    index = _pack_index(pack)
    for eid in claim.evidence_ids:
        item = index.get(eid)
        if item is None:
            # 关键纪律：claim 引用了 Pack 之外的证据 -> 直接 unsupported，
            # 绝不去语料里"帮它找"一个出处。
            bindings.append(
                ClaimBinding(
                    claim_id=claim.claim_id,
                    evidence_id=eid,
                    in_pack=False,
                    reason="evidence_id 不在 EvidencePack 中（不得引用 Pack 之外的来源）",
                )
            )
            continue

        # 证据原文过短 -> 不足以支撑思想结论
        if len(_normalize(item.original)) < _MIN_CLAIM_EVIDENCE_LEN:
            bindings.append(
                ClaimBinding(
                    claim_id=claim.claim_id,
                    evidence_id=eid,
                    in_pack=True,
                    evidence_original=item.original,
                    evidence_source=item.source,
                    reason="证据原文过短，不足以支撑思想结论",
                )
            )
            continue

        # 复用 quote_verifier 做逐字/归一化校验（单一真值来源）
        verification = verify_quote(item.original, item.source)
        bindings.append(
            ClaimBinding(
                claim_id=claim.claim_id,
                evidence_id=eid,
                in_pack=True,
                evidence_original=item.original,
                evidence_source=item.source,
                quote_exists=verification.quote_exists,
                source_correct=verification.source_correct,
                correct_source=verification.correct_source,
                trust_state=verification.trust_state,
                reason="" if verification.quote_exists else "引文在语料中找不到",
            )
        )

    has_real = any(b.in_pack and b.quote_exists for b in bindings)
    if not has_real:
        support = "unsupported"
        message = INSUFFICIENT_EVIDENCE_MESSAGE
    elif all(b.source_correct for b in bindings if b.in_pack and b.quote_exists):
        support = "supported"
        message = ""
    else:
        # 文本真实但至少一条出处不一致 -> citation_corrected 语义
        support = "partially_supported"
        corrected = next(
            (b.correct_source for b in bindings if b.in_pack and b.quote_exists and not b.source_correct),
            None,
        )
        message = (
            f"引文真实但出处不一致，正确出处应为 {corrected}"
            if corrected
            else "引文真实但出处不一致"
        )

    return ClaimVerificationResult(
        claim_id=claim.claim_id,
        text=claim.text,
        is_core=claim.is_core,
        support=support,
        bindings=bindings,
        message=message,
    )


def verify_claims(claims: Iterable[Claim], pack: EvidencePack) -> ClaimSupport:
    """批量验证并返回可计算覆盖率的聚合结果。"""
    return ClaimSupport(results=[verify_claim(c, pack) for c in claims])


def bind_claims(
    answer: str,
    pack: EvidencePack,
    *,
    claim_evidence_map: Optional[Dict[str, Sequence[str]]] = None,
) -> ClaimSupport:
    """把一段答案的 claim 绑定到 Evidence Pack 并验证。

    ``claim_evidence_map``：可选，把 ``claim_id`` 映射到 evidence_id 列表。
    通常由上层（LLM 输出结构化引用后）提供；不提供时所有 claim 都按
    「未声明证据」处理 -> unsupported，这是**保守且诚实**的默认，
    避免在缺少结构化引用时假装已验证。
    """
    claims = extract_claims(answer)
    if claim_evidence_map:
        claims = [
            Claim(
                claim_id=c.claim_id,
                text=c.text,
                evidence_ids=tuple(claim_evidence_map.get(c.claim_id, ())),
                is_core=c.is_core,
            )
            for c in claims
        ]
    return verify_claims(claims, pack)


def coverage(answer: str, pack: EvidencePack, *, claim_evidence_map: Optional[Dict[str, Sequence[str]]] = None) -> float:
    """便捷函数：直接返回核心 claim 的证据覆盖率。"""
    return bind_claims(answer, pack, claim_evidence_map=claim_evidence_map).coverage()
