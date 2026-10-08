"""
悟典 - 可信知识库 Schema（L1 权威原典 / L2 历代注疏 **分离**）

设计依据
--------
- PROJECT-BRIEF 第五章（L1–L5 五层结构）、第六章（Passage Schema 29 字段）、
  第十章/十一章/十二章（Citation Guard / Quote Verifier / Trust State）、第十四章（A/B/C/D 质量等级）
- ``docs/kb-v1/02-architecture.md`` §3.1（模块清单）、§4.2（L1/L2 分表分 collection）、§9（字段冻结）
- ``docs/kb-v1/audit/classical-knowledge.md`` §2（字段对照）、§3（来源与授权审计）

本模块把"硬约束"实现为**可执行的校验**，而不是靠注释约定
--------------------------------------------------------
1. **原典与注疏分离**：注疏使用 :class:`Commentary`，经 ``target_passage_id`` 外键引用 L1，
   **不得内嵌原典原文副本**。现状 ``backend/data/commentaries/lunyu_zhuxi.json`` 15 条中
   13 条重复存储了 ``original``（``classical-knowledge.md`` §5.2）。因此 ``Commentary`` 使用
   ``extra="forbid"``，任何 ``original`` / ``original_text`` 字段会被**直接拒绝**。
2. **``text_type`` 强制枚举四值**，且 ``commentary`` **不允许出现在** :class:`Passage`
   （注疏必须走 :class:`Commentary`）。
3. **来源与复核字段必须显式提供**：``source_provider`` / ``source_url`` / ``source_edition`` /
   ``license`` / ``verification_level`` / ``proofread_status`` **无默认值**，杜绝静默缺省。
   真实未知须**显式**写哨兵 :data:`UNKNOWN`（``"unknown"``）。
4. **``verification_level == "A"`` 必须有人工确认依据**：``proofread_status == "human_verified"``
   且 ``verified_by`` 非空 且 ``verified_at`` 存在 且 ``license != "unknown"``。
   当前语料**零人工复核记录**（``classical-knowledge.md`` §3.2），故实际只能取 C/D。
5. **禁止把 AI 生成文本当权威原典**：``text_type == "original"`` 不得标 ``verification_level == "D"``。

字段命名与 ``docs/kb-v1/02-architecture.md`` §9.1/§9.2/§9.4 **冻结一致**，前端不得另造同义字段。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ============================================================
# 枚举与哨兵（冻结）
# ============================================================

#: 显式"真实未知"哨兵。**不得**用空字符串或省略字段来表达未知。
UNKNOWN = "unknown"

#: PROJECT-BRIEF 第六章 text_type，恰四值（冻结）
TextType = Literal["original", "commentary", "translation", "modern_explanation"]
TEXT_TYPES = frozenset({"original", "commentary", "translation", "modern_explanation"})

#: PROJECT-BRIEF 第十四章质量等级，恰四值（冻结）
VerificationLevel = Literal["A", "B", "C", "D"]
VERIFICATION_LEVELS = frozenset({"A", "B", "C", "D"})

#: 复核状态。只有 ``human_verified`` 才构成 A 级的"人工确认依据"。
ProofreadStatus = Literal["unproofread", "machine_processed", "human_verified"]
PROOFREAD_STATUSES = frozenset({"unproofread", "machine_processed", "human_verified"})

#: 授权状态。``authorized`` 必须附证据，否则视为编造授权。
AuthorizationStatus = Literal["authorized", "unverified", "pending", "denied", "unknown"]

#: PROJECT-BRIEF 第十二章 Trust State 四态（冻结）
TrustState = Literal["verified", "citation_corrected", "quote_relaxed", "insufficient_evidence"]
TRUST_STATES = frozenset(
    {"verified", "citation_corrected", "quote_relaxed", "insufficient_evidence"}
)

#: 等级序（用于"不得超过来源允许的上限"判定）
LEVEL_RANK = {"D": 0, "C": 1, "B": 2, "A": 3}

#: 当前语料**唯一**可诚实使用的等级下限。
#: 依据：零人工复核记录（不能 A）、零 source_* 字段（不能 B）→ 只能 C 或 D。
CONSERVATIVE_VERIFICATION_LEVEL: VerificationLevel = "C"

#: PROJECT-BRIEF 第六章 Passage Schema 的 29 个字段名（冻结，测试据此逐字段核对）
PASSAGE_FIELDS_29 = (
    "passage_id",
    "book_id",
    "book_title",
    "chapter_id",
    "chapter_title",
    "section",
    "line_no",
    "original",
    "original_traditional",
    "original_simplified",
    "source_provider",
    "source_url",
    "source_edition",
    "author",
    "dynasty",
    "text_type",
    "commentator",
    "commentary_dynasty",
    "school",
    "concepts",
    "modern_topics",
    "modern_scenarios",
    "stance",
    "verification_level",
    "proofread_status",
    "license",
    "embedding_version",
    "created_at",
    "updated_at",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# 溯源与复核：Passage / Commentary 共享的强制校验
# ============================================================

class _ProvenanceRecord(BaseModel):
    """L1 / L2 共用的溯源与复核强制规则。

    ``extra="forbid"``：未知字段（尤其是注疏内嵌的 ``original``）直接报错，
    而不是被静默丢弃——"静默丢弃"正是现状 13/15 重复存储得以长期存在的原因。
    """

    model_config = ConfigDict(extra="forbid")

    # --- 来源字段：**无默认值**，必须显式提供（真实未知写 UNKNOWN 哨兵）---
    source_provider: str = Field(
        ..., min_length=1,
        description='来源提供方。真实未知须显式写 "unknown"，不得省略或留空',
    )
    source_url: str = Field(
        ..., min_length=1,
        description='来源链接。真实未知须显式写 "unknown"，不得省略或留空',
    )
    source_edition: str = Field(
        ..., min_length=1,
        description='所据底本/版本。真实未知须显式写 "unknown"，不得省略或留空',
    )
    license: str = Field(
        ..., min_length=1,
        description='授权/版权状态。真实未知须显式写 "unknown"；禁止编造授权',
    )

    # --- 复核字段：**无默认值**，必须显式提供 ---
    verification_level: VerificationLevel = Field(
        ...,
        description=(
            "质量等级 A/B/C/D。A=权威文本+人工确认；B=权威来源+机器处理；"
            "C=来源可靠但尚未复核；D=AI 解释。当前语料零人工复核记录，只能 C/D。"
        ),
    )
    proofread_status: ProofreadStatus = Field(
        ..., description="复核状态。仅 human_verified 构成 A 级的人工确认依据",
    )

    # --- A 级的"人工确认依据"（非第六章字段，但 A 级必需，缺失即拒绝）---
    verified_by: Optional[str] = Field(
        None, description="人工确认者/机构标识。A 级必需且非空",
    )
    verified_at: Optional[datetime] = Field(
        None, description="人工确认时间。A 级必需",
    )

    @field_validator(
        "source_provider", "source_url", "source_edition", "license", mode="after",
    )
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        """拒绝空白串：``"   "`` 与省略字段同样是"静默缺省"，必须报错。"""
        stripped = value.strip()
        if not stripped:
            raise ValueError(
                "来源/授权字段不得为空白串；真实未知请显式写哨兵 'unknown'"
            )
        return stripped

    @model_validator(mode="after")
    def _enforce_verification_evidence(self) -> "_ProvenanceRecord":
        level = self.verification_level

        # --- A 级：必须有人工确认依据，且授权不得为未知 ---
        if level == "A":
            if self.proofread_status != "human_verified":
                raise ValueError(
                    "verification_level='A' 要求 proofread_status='human_verified'"
                    f"（当前为 {self.proofread_status!r}）；"
                    "当前语料零人工复核记录，不得标 A"
                )
            if not (self.verified_by or "").strip():
                raise ValueError(
                    "verification_level='A' 要求 verified_by 非空（人工确认者），"
                    "不得无依据标 A"
                )
            if self.verified_at is None:
                raise ValueError(
                    "verification_level='A' 要求 verified_at 存在（人工确认时间）"
                )
            if self.license.strip().lower() == UNKNOWN:
                raise ValueError(
                    "verification_level='A' 要求 license != 'unknown'"
                    "（授权未知不得标为权威文本+人工确认）"
                )

        # --- B 级：权威来源，要求 provider/url/edition 三者均为已知 ---
        if level == "B":
            unknown_fields = [
                name for name in ("source_provider", "source_url", "source_edition")
                if getattr(self, name).strip().lower() == UNKNOWN
            ]
            if unknown_fields:
                raise ValueError(
                    "verification_level='B' 要求权威来源，但以下字段为 'unknown'："
                    f"{unknown_fields}；来源未知不得标 B"
                )

        return self


# ============================================================
# L1 权威原典
# ============================================================

class Passage(_ProvenanceRecord):
    """L1 权威原典条目（PROJECT-BRIEF 第六章 29 字段全覆盖）。

    字段可空性说明（对应 acceptance「不适用者须显式标注理由」）：
    - ``section`` / ``line_no``：现有语料**无此粒度**（``lunyu.json`` 只到章），
      故允许 ``None``，但**必须显式传入 None**（无默认值），以区别于"忘记填"。
    - ``original_traditional`` / ``original_simplified``：现有语料**只有简体一份**
      （``classical-knowledge.md`` §4.2 实测无繁体文本），繁体须待真实底本导入后补齐，
      故当前显式传 ``None``。
    - ``author`` / ``dynasty``：仅 ``lunyu.json`` 容器级有；``debate_classics.json``
      各派**无** author/dynasty（同审计 §3.3），故允许 ``None``。
    - ``commentator`` / ``commentary_dynasty``：这两个字段在 L1 行**本就不适用**
      （注疏者属于 L2 ``Commentary``）。保留字段以满足第六章 29 字段要求，
      L1 行显式传 ``None``；L1 若填非空值不会报错，但属于数据错误，由 ingestion 校验。
    - ``stance``：PROJECT-BRIEF 未给受控词表，当前无语料支撑，显式传 ``None``。
    - ``embedding_version``：索引版本在 PHASE 4 写入，当前显式传 ``None``。
    """

    # --- 身份 ---
    passage_id: str = Field(..., min_length=1, description="全局唯一 passage 主键（跨书统一）")
    book_id: str = Field(..., min_length=1, description="书籍 slug，与 classics_catalog.id 对齐")
    book_title: str = Field(..., min_length=1, description="书名")
    chapter_id: Union[int, str] = Field(
        ..., description="篇章 id。现有 lunyu.json 为 int，其余语料为 str，故允许二者",
    )
    chapter_title: str = Field(..., min_length=1, description="篇章名")
    section: Optional[str] = Field(..., description="节/小节。现有语料无此粒度，**须显式传 None**")
    line_no: Optional[int] = Field(..., description="行号。现有语料无此粒度，**须显式传 None**")

    # --- 正文 ---
    original: str = Field(..., min_length=1, description="原典正文。不可变且可溯源")
    original_traditional: Optional[str] = Field(
        ..., description="繁体原文。现有语料只有简体，**须显式传 None**",
    )
    original_simplified: Optional[str] = Field(
        ..., description="简体原文。现有语料只有简体一份，**须显式传 None**",
    )

    # --- 作者 / 时代 ---
    author: Optional[str] = Field(
        ..., description="作者。debate_classics 各派无此字段，**须显式传 None**",
    )
    dynasty: Optional[str] = Field(
        ..., description="朝代。debate_classics 各派无此字段，**须显式传 None**",
    )

    # --- 分层 ---
    text_type: TextType = Field(
        ..., description="文本类型。L1 应为 'original'；'commentary' 必须走 Commentary",
    )

    # --- 注疏元信息（L1 不适用，保留字段以满足 29 字段要求）---
    commentator: Optional[str] = Field(
        ..., description="注疏者。L1 不适用，**须显式传 None**（该信息属于 L2 Commentary）",
    )
    commentary_dynasty: Optional[str] = Field(
        ..., description="注疏朝代。L1 不适用，**须显式传 None**（该信息属于 L2 Commentary）",
    )

    # --- 学派与概念 ---
    school: Optional[str] = Field(
        ..., description="学派。现有 debate_classics 无 school 字段，**须显式传 None**",
    )
    concepts: List[str] = Field(
        ...,
        description="思想概念标签（受控词表见 PHASE 3）。**须显式传 []**（空=尚未标注）",
    )
    modern_topics: List[str] = Field(
        ..., description="现代议题标签。**须显式传 []**（空=尚未标注）",
    )
    modern_scenarios: List[str] = Field(
        ..., description="现代情境标签。**须显式传 []**（空=尚未标注）",
    )
    stance: Optional[str] = Field(
        ..., description="学派立场。PROJECT-BRIEF 未给受控词表，**须显式传 None**",
    )

    # --- 来源注册表外键（02-architecture §4.2 要求）---
    source_id: str = Field(
        ..., min_length=1,
        description="指向 data/sources/source_registry.json 的 source_id",
    )

    # --- 索引版本 ---
    embedding_version: Optional[str] = Field(
        ..., description="向量索引版本。PHASE 4 写入，**须显式传 None**",
    )

    # --- 时间戳 ---
    created_at: datetime = Field(default_factory=_utcnow, description="创建时间（UTC）")
    updated_at: datetime = Field(default_factory=_utcnow, description="更新时间（UTC）")

    @field_validator("passage_id", "book_id", "book_title", "chapter_title", "original", "source_id", mode="after")
    @classmethod
    def _reject_blank_identity(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("身份/正文字段不得为空白串")
        return value

    @model_validator(mode="after")
    def _enforce_layer_separation(self) -> "Passage":
        # 注疏必须使用 Commentary，不得塞进 L1
        if self.text_type == "commentary":
            raise ValueError(
                "text_type='commentary' 不允许出现在 Passage："
                "注疏必须使用 Commentary 模型（L1/L2 物理分离）"
            )
        # 禁止把 AI 生成文本当权威原典
        if self.text_type == "original" and self.verification_level == "D":
            raise ValueError(
                "text_type='original' 不得标 verification_level='D'："
                "禁止把 AI 生成文本当作权威原典"
            )
        # D 级只能是派生内容
        if self.verification_level == "D" and self.text_type not in (
            "modern_explanation", "translation",
        ):
            raise ValueError(
                "verification_level='D'（AI 解释）只适用于 text_type 为 "
                "'modern_explanation' 或 'translation' 的派生内容"
            )
        return self


# ============================================================
# L2 历代注疏（与 L1 分离，**不内嵌原文副本**）
# ============================================================

class Commentary(_ProvenanceRecord):
    """L2 历代注疏条目。

    **不内嵌原典原文副本**：通过 ``target_passage_id`` 外键引用 L1。
    现状 ``lunyu_zhuxi.json`` 13/15 条重复存储 ``original``，
    与 ``lunyu.json`` 逐字相同（``classical-knowledge.md`` §5.2）——
    该重复会造成"注疏里的原文"与"原典"出现第二套真值，必须消除。

    ``extra="forbid"`` 使 ``original`` / ``original_text`` 等字段**构造即报错**。
    """

    commentary_id: str = Field(..., min_length=1, description="注疏条目主键")
    target_passage_id: str = Field(
        ..., min_length=1,
        description="外键 → L1 Passage.passage_id。**替代**内嵌原文副本",
    )
    commentator: str = Field(..., min_length=1, description="注疏者（如 朱熹）")
    commentary_dynasty: str = Field(..., min_length=1, description="注疏者朝代（如 南宋）")
    commentary_text: str = Field(..., min_length=1, description="注疏正文")
    text_type: Literal["commentary"] = Field(
        "commentary", description="固定为 'commentary'（L2 分层标记）",
    )
    source_id: str = Field(
        ..., min_length=1, description="指向 source_registry.json 的 source_id",
    )
    embedding_version: Optional[str] = Field(
        ..., description="向量索引版本。PHASE 4 写入，**须显式传 None**",
    )
    created_at: datetime = Field(default_factory=_utcnow, description="创建时间（UTC）")
    updated_at: datetime = Field(default_factory=_utcnow, description="更新时间（UTC）")

    @field_validator("commentary_id", "target_passage_id", "commentator",
                     "commentary_dynasty", "commentary_text", "source_id", mode="after")
    @classmethod
    def _reject_blank_commentary(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("注疏字段不得为空白串")
        return value

    @model_validator(mode="after")
    def _enforce_commentary_level(self) -> "Commentary":
        # D 级 = AI 解释。注疏是历代注疏者的文本，不是 AI 解释；
        # 若确为 AI 生成的对注疏的解读，应作为 text_type='modern_explanation'
        # 的 L1 派生条目，而不是 L2 注疏。
        if self.verification_level == "D":
            raise ValueError(
                "Commentary 不得标 verification_level='D'（D 级为 AI 解释）。"
                "AI 生成的对注疏的解读应使用 Passage(text_type='modern_explanation')，"
                "不得冒充历代注疏。"
            )
        return self


# ============================================================
# 来源注册表记录
# ============================================================

class SourceRecord(BaseModel):
    """来源注册表条目。

    **严禁编造来源、版本或授权信息**：真实未知一律写 :data:`UNKNOWN`，
    并保持 ``authorization_status="unverified"``。
    ``authorization_status="authorized"`` 必须附证据（``verified_at`` +
    ``evidence_ref`` + 已知 ``license``），否则视为编造授权并拒绝。
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1, description="来源主键")
    provider: str = Field(
        ..., min_length=1, description='来源提供方。未知须显式写 "unknown"',
    )
    url: str = Field(
        ..., min_length=1, description='来源链接。未知须显式写 "unknown"',
    )
    edition: str = Field(
        ..., min_length=1, description='所据底本/版本。未知须显式写 "unknown"',
    )
    license: str = Field(
        ..., min_length=1, description='授权/版权状态。未知须显式写 "unknown"',
    )
    authorization_status: AuthorizationStatus = Field(
        ..., description="授权状态。authorized 必须附证据，否则视为编造",
    )
    verified_at: Optional[datetime] = Field(
        None, description="来源核验时间。authorized 必需",
    )
    verification_method: Optional[str] = Field(
        None, description="核验方式（如 人工比对 ctext.org 页面）",
    )
    evidence_ref: Optional[str] = Field(
        None, description="仓库内证据引用（路径或 路径#锚点）。authorized 必需",
    )
    notes: Optional[str] = Field(None, description="补充说明与不确定性")

    @field_validator("source_id", "provider", "url", "edition", "license", mode="after")
    @classmethod
    def _reject_blank_source(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError(
                "来源字段不得为空白串；真实未知请显式写哨兵 'unknown'"
            )
        return stripped

    @model_validator(mode="after")
    def _enforce_authorization_evidence(self) -> "SourceRecord":
        if self.authorization_status == "authorized":
            missing = [
                name for name, value in (
                    ("verified_at", self.verified_at),
                    ("evidence_ref", self.evidence_ref),
                ) if value is None
            ]
            if self.license.strip().lower() == UNKNOWN:
                missing.append("license(不得为 unknown)")
            if missing:
                raise ValueError(
                    "authorization_status='authorized' 必须附证据，缺少："
                    f"{missing}；禁止编造授权"
                )
        return self

    # --- 便捷判定 ---

    @property
    def has_known_provenance(self) -> bool:
        """provider / url / edition 三者是否均为已知（非哨兵）。"""
        return all(
            getattr(self, name).strip().lower() != UNKNOWN
            for name in ("provider", "url", "edition")
        )

    @property
    def max_verification_level(self) -> VerificationLevel:
        """本来源**允许**的最高质量等级。

        - 未注册/来源未知 → C（来源可靠但尚未复核的诚实下限）
        - provider/url/edition 均已知 → B（权威来源+机器处理）
        - 且已授权 + license 已知 + 有核验时间 → A（仍需 Passage 侧人工确认依据）
        """
        if not self.has_known_provenance:
            return "C"
        if (
            self.authorization_status == "authorized"
            and self.license.strip().lower() != UNKNOWN
            and self.verified_at is not None
        ):
            return "A"
        return "B"


# ============================================================
# Evidence Pack / Quote Verification（PHASE 4/5 消费，字段名冻结）
# ============================================================

class EvidenceItem(BaseModel):
    """Evidence Pack 中的单条证据（PROJECT-BRIEF 第九章）。

    注意：此处的 ``original`` 是**证据展示字段**，不是 L2 存储——
    存储层的"不内嵌原文副本"约束由 :class:`Commentary` 保证。
    """

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    original: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    school: Optional[str] = None
    text_type: TextType
    commentary: Optional[str] = None
    relevance: float = Field(..., ge=0.0, le=1.0)
    verification: Optional[str] = None


class EvidencePack(BaseModel):
    """LLM 只能引用本 Pack 内存在的 source（PROJECT-BRIEF 第九章白名单）。"""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=1)
    scenario: Optional[str] = None
    concepts: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)


class QuoteCandidate(BaseModel):
    """Quote Verifier 的候选命中。"""

    model_config = ConfigDict(extra="forbid")

    passage_id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    text_type: TextType
    similarity: float = Field(..., ge=0.0, le=1.0)


class QuoteVerification(BaseModel):
    """``POST /api/knowledge/verify-quote`` 契约（``02-architecture.md`` §9.4，冻结）。

    必须**分别**表达「这句话存在」与「出处正确」两个独立指标
    （PROJECT-BRIEF 第十一章）。
    """

    model_config = ConfigDict(extra="forbid")

    quote_exists: bool
    exact_match: bool
    normalized_match: bool
    source_correct: bool
    correct_source: Optional[str] = None
    similarity: float = Field(..., ge=0.0, le=1.0)
    match_type: Literal["exact", "normalized", "partial", "none"]
    candidates: List[QuoteCandidate] = Field(default_factory=list)
    trust_state: TrustState
    evidence_scope: Optional[str] = None
    verified_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="after")
    def _enforce_trust_state_consistency(self) -> "QuoteVerification":
        # 四态必须与 quote_exists / source_correct / match_type 自洽，
        # 防止"缺省即通过"（现状 Citation.verifiable 默认 True 的同类缺陷）。
        if self.trust_state == "verified" and not (self.quote_exists and self.source_correct):
            raise ValueError(
                "trust_state='verified' 要求 quote_exists=True 且 source_correct=True"
            )
        if self.trust_state == "citation_corrected":
            if not (self.quote_exists and not self.source_correct):
                raise ValueError(
                    "trust_state='citation_corrected' 要求 "
                    "quote_exists=True 且 source_correct=False"
                )
            if not (self.correct_source or "").strip():
                raise ValueError(
                    "trust_state='citation_corrected' 必须返回 correct_source"
                )
        if self.trust_state == "insufficient_evidence" and self.quote_exists:
            raise ValueError(
                "trust_state='insufficient_evidence' 要求 quote_exists=False"
            )
        return self


__all__ = [
    "UNKNOWN",
    "TextType",
    "TEXT_TYPES",
    "VerificationLevel",
    "VERIFICATION_LEVELS",
    "ProofreadStatus",
    "PROOFREAD_STATUSES",
    "AuthorizationStatus",
    "TrustState",
    "TRUST_STATES",
    "LEVEL_RANK",
    "CONSERVATIVE_VERIFICATION_LEVEL",
    "PASSAGE_FIELDS_29",
    "Passage",
    "Commentary",
    "SourceRecord",
    "EvidenceItem",
    "EvidencePack",
    "QuoteCandidate",
    "QuoteVerification",
]
