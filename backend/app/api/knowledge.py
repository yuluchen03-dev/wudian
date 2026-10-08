"""
悟典 - 可信知识库 API（PHASE 5 / P5-08）

提供 ``POST /api/knowledge/verify-quote``：把「**这句话存在**」与
「**出处正确**」拆成两个可独立判定的指标（PROJECT-BRIEF 第十一章）。

契约
----
输入 ``{quote, claimed_source}``；输出字段与 ``02-architecture.md`` §9.4 冻结一致：
``quote_exists`` / ``exact_match`` / ``normalized_match`` / ``source_correct`` /
``correct_source`` / ``similarity`` / ``match_type`` / ``candidates[]`` /
``trust_state`` / ``evidence_scope`` / ``verified_at``。

允许出现 ``quote_exists=true`` 且 ``source_correct=false``（即 ``citation_corrected``）
—— 这是本接口存在的**根本理由**，旧 ``citation_validator`` 无法表达该组合。

诚实性
------
- 不编造原典：``correct_source`` / ``candidates`` 均来自仓库内真实语料。
- 证据不足时返回 ``insufficient_evidence`` 与 PROJECT-BRIEF 第十二章的拒答文案，
  **不硬编**古文。
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.knowledge import EvidenceItem, EvidencePack, QuoteVerification
from app.services.quote_verifier import verify_quote
from app.services.trust_state import INSUFFICIENT_EVIDENCE_MESSAGE, explain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["可信知识库"])


# ============================================================
# 请求 / 响应模型
# ============================================================

class VerifyQuoteRequest(BaseModel):
    """引文校验请求（PROJECT-BRIEF 第十一章）。"""

    model_config = ConfigDict(extra="forbid")

    quote: str = Field(
        ..., min_length=1, max_length=2000,
        description="待校验的引文（如『己所不欲，勿施于人。』）",
    )
    claimed_source: str = Field(
        "", max_length=200,
        description=(
            "声称出处（如《孟子·公孙丑上》）。允许为空或『无』，"
            "此时 source_correct 必为 false（不得放行）"
        ),
    )


class VerifyQuoteResponse(QuoteVerification):
    """引文校验响应。

    继承冻结契约 :class:`~app.schemas.knowledge.QuoteVerification`，
    追加 ``message`` 供前端直接展示（不改变既有字段语义）。
    """

    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        "", description="该 trust_state 对应的诚实中文说明（含证据不足时的拒答文案）",
    )


# ============================================================
# 端点
# ============================================================

@router.post(
    "/verify-quote",
    response_model=VerifyQuoteResponse,
    summary="校验引文：分别判定『这句话存在』与『出处正确』",
)
async def verify_quote_endpoint(payload: VerifyQuoteRequest) -> VerifyQuoteResponse:
    """校验一句引文是否真实存在、以及声称出处是否正确。

    两个指标**互相独立**：

    - ``quote_exists``：该句是否存在于知识库（归一化 + 长度下限后判定）
    - ``source_correct``：声称出处是否与真实出处一致

    典型返回：

    - 逐字命中 + 出处正确 → ``verified``
    - 文本存在 + 出处错误 → ``citation_corrected``（附 ``correct_source``）
    - 仅归一化命中（繁简/标点）→ ``quote_relaxed``
    - 文本不存在 / 过短片段 → ``insufficient_evidence``（附拒答文案）
    """
    try:
        result = verify_quote(payload.quote, payload.claimed_source)
    except Exception as exc:  # 语料缺失等基础设施问题
        logger.error("verify-quote 失败: %s", exc)
        raise HTTPException(status_code=500, detail="引文校验内部错误") from exc

    message = explain(result.trust_state)
    if result.trust_state == "insufficient_evidence":
        # PROJECT-BRIEF 第十二章：证据不足时明确说明，禁止编造古文
        message = INSUFFICIENT_EVIDENCE_MESSAGE

    return VerifyQuoteResponse(**result.model_dump(), message=message)


@router.get(
    "/corpus-stats",
    summary="可信语料规模（只读，供健康检查/证据面板核对）",
)
async def corpus_stats() -> dict:
    """返回当前可核验语料条数，便于确认「证据范围」是否真实可用。"""
    from app.services.quote_verifier import load_corpus

    entries = load_corpus()
    by_type: dict = {}
    for entry in entries:
        by_type[entry.text_type] = by_type.get(entry.text_type, 0) + 1
    return {
        "total": len(entries),
        "by_text_type": by_type,
        "scope": "corpus",
    }


# ============================================================
# Claim-Evidence（PROJECT-BRIEF 第十三章）
# ============================================================

class ClaimBindingModel(BaseModel):
    """单条 claim 与一条证据的绑定结果。"""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    in_pack: bool
    evidence_source: Optional[str] = None
    quote_exists: bool = False
    source_correct: bool = False
    correct_source: Optional[str] = None
    trust_state: Optional[str] = None
    reason: str = ""


class ClaimResultModel(BaseModel):
    """单个 claim 的验证结果。"""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    text: str
    is_core: bool
    support: str = Field(..., description="supported / partially_supported / unsupported")
    has_evidence: bool
    message: str = ""
    bindings: List[ClaimBindingModel] = Field(default_factory=list)


class VerifyClaimsRequest(BaseModel):
    """claim 校验请求。

    ``claim_evidence_map`` 把 claim_id 映射到 Evidence Pack 中的 evidence_id 列表。
    未提供时所有 claim 按「未声明证据」处理 → ``unsupported``（保守且诚实）。
    """

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(..., min_length=1, max_length=20000, description="待拆解的答案文本")
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="Evidence Pack 的证据条目（claim 只能引用其中存在的 evidence_id）",
    )
    scenario: Optional[str] = None
    concepts: List[str] = Field(default_factory=list)
    claim_evidence_map: Dict[str, List[str]] = Field(default_factory=dict)


class VerifyClaimsResponse(BaseModel):
    """claim 校验响应，含 GATE-8 所需的覆盖率。"""

    model_config = ConfigDict(extra="forbid")

    core_claim_count: int
    core_claim_evidence_coverage: float = Field(
        ..., ge=0.0, le=1.0,
        description="核心 claim 证据覆盖率（分母为 0 时返回 0.0，不返回 1.0）",
    )
    unsupported_core_claim_ids: List[str] = Field(default_factory=list)
    claims: List[ClaimResultModel] = Field(default_factory=list)


@router.post(
    "/verify-claims",
    response_model=VerifyClaimsResponse,
    summary="把答案拆成 claim 并逐条绑定证据（PROJECT-BRIEF 第十三章）",
)
async def verify_claims_endpoint(payload: VerifyClaimsRequest) -> VerifyClaimsResponse:
    """把答案拆成 claim，逐条绑定 Evidence Pack 中的证据并判定支持状态。

    判定规则（可自动化复现）：

    - claim 引用了 Pack 之外的 ``evidence_id`` → ``unsupported``（**不得编造证据**）
    - 引文在语料中找不到 → ``unsupported``
    - 引文真实但出处不一致 → ``partially_supported``（对应 ``citation_corrected``）
    - 引文真实且出处正确 → ``supported``

    覆盖率分母为核心 claim 数；**分母为 0 时返回 0.0**，避免空答案拿满分。
    """
    from app.services.claim_evidence import bind_claims

    pack = EvidencePack(
        query=payload.answer[:200] or "q",
        scenario=payload.scenario,
        concepts=list(payload.concepts),
        evidence=list(payload.evidence),
    )
    try:
        result = bind_claims(
            payload.answer, pack, claim_evidence_map=payload.claim_evidence_map or None
        )
    except Exception as exc:
        logger.error("verify-claims 失败: %s", exc)
        raise HTTPException(status_code=500, detail="claim 校验内部错误") from exc

    return VerifyClaimsResponse(
        core_claim_count=len(result.core_claims),
        core_claim_evidence_coverage=result.coverage(),
        unsupported_core_claim_ids=[c.claim_id for c in result.unsupported_core_claims],
        claims=[
            ClaimResultModel(
                claim_id=r.claim_id,
                text=r.text,
                is_core=r.is_core,
                support=r.support,
                has_evidence=r.has_evidence,
                message=r.message,
                bindings=[
                    ClaimBindingModel(
                        evidence_id=b.evidence_id,
                        in_pack=b.in_pack,
                        evidence_source=b.evidence_source,
                        quote_exists=b.quote_exists,
                        source_correct=b.source_correct,
                        correct_source=b.correct_source,
                        trust_state=b.trust_state,
                        reason=b.reason,
                    )
                    for b in r.bindings
                ],
            )
            for r in result.results
        ],
    )
