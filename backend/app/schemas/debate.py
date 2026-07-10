"""
悟典 - 百家论道辩论系统 Pydantic 数据模型

定义辩论会话、回合、发言、交锋、会诊报告等数据结构。
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


# ============================================================
# 请求模型
# ============================================================

class DebateStartRequest(BaseModel):
    """开始辩论请求"""
    topic: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="辩论议题，如'人性本善还是本恶？'",
    )
    sages: Optional[List[str]] = Field(
        None,
        description="指定参与辩论的圣贤key列表，None则使用默认阵容",
    )


class UserInterventionRequest(BaseModel):
    """用户介入请求"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="用户的追问、质疑或表态",
    )
    target_sage: Optional[str] = Field(
        None,
        description="指定回应的圣贤key，None则由主持Agent路由",
    )


class StandRequest(BaseModel):
    """论主站队请求"""
    stance: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="论主选择支持的立场或理由",
    )
    target_sage: Optional[str] = Field(
        None,
        description="论主站队的圣贤key，None则由主持Agent路由",
    )


class MutualQuestionRequest(BaseModel):
    """请其互问请求"""
    from_sage: str = Field(..., description="发起提问的圣贤key")
    to_sage: str = Field(..., description="被提问的圣贤key")
    question: Optional[str] = Field(
        None,
        max_length=300,
        description="可选指定问题，为空则由圣贤基于议题自行发问",
    )


class GuestDecisionRequest(BaseModel):
    """踢馆名人留下/离去请求"""
    decision: Literal["stay", "leave"] = Field(..., description="stay 表示留下并收集，leave 表示离场")


class SummonRequest(BaseModel):
    """召唤踢馆名人请求"""
    sage_key: str = Field(
        ...,
        description="要召唤的踢馆名人key，如 'li_bai', 'zhuge_liang'",
    )


class ThoughtCompassRequest(BaseModel):
    """思想坐标定位请求"""
    statement: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="论主输入的主张、追问或自我表述",
    )


# ============================================================
# 核心数据模型
# ============================================================

class Citation(BaseModel):
    """引用条目（复用 ai.py 的 Citation 结构）"""
    id: str = Field(..., description="引用标记，如 引1")
    source: str = Field(..., alias="出处", description="出处，如《论语·学而》")
    original: str = Field(..., alias="原文", description="经典原文")
    verifiable: bool = Field(True, description="是否通过引用校验")

    model_config = ConfigDict(populate_by_name=True)


class SentenceEvidence(BaseModel):
    """单句发言的经典检索证据"""
    sentence: str = Field(..., description="发言中的单句")
    source: str = Field("无", description="该句命中的经典出处")
    original: str = Field("无", description="该句命中的经典原文")
    similarity: float = Field(0.0, description="检索相似度")
    verifiable: bool = Field(False, description="是否有可核验原文")


class SageSpeech(BaseModel):
    """圣贤发言"""
    sage_key: str = Field(..., description="圣贤key")
    sage_name: str = Field(..., description="圣贤中文名")
    round_number: int = Field(..., description="所在回合号")
    content: str = Field("", description="发言正文（文言口吻）")
    vernacular: str = Field("", description="白话点睛")
    quote: str = Field("无", description="引用的经典原文")
    source: str = Field("无", description="原文出处")
    citations: List[Citation] = Field(default_factory=list, description="结构化引用列表")
    sentence_evidence: List[SentenceEvidence] = Field(default_factory=list, description="逐句经典检索证据")
    target_sage: Optional[str] = Field(None, description="交锋对象key（Round 2 用）")
    is_guest: bool = Field(False, description="是否为踢馆名人")
    confidence: str = Field("medium", description="置信度: high/medium/low")


class DebateClash(BaseModel):
    """交锋关系（用于前端连线可视化）"""
    from_sage: str = Field(..., description="发起反驳的圣贤key")
    to_sage: str = Field(..., description="被反驳的圣贤key")
    clash_type: Literal["agree", "disagree", "extend", "refute", "reframe"] = Field(
        ..., description="交锋类型：认同/反对/延伸/驳斥/重构"
    )
    summary: str = Field("", description="交锋要点摘要")


class DebateRound(BaseModel):
    """辩论回合"""
    round_number: int = Field(..., description="回合序号（1=各陈己见，2=交锋辩驳）")
    round_type: Literal[
        "opinion",
        "cross_debate",
        "intervention",
        "stance",
        "mutual_question",
        "guest",
        "guest_response",
    ] = Field(
        ..., description="回合类型"
    )
    speeches: List[SageSpeech] = Field(default_factory=list, description="本回合发言列表")
    clashes: List[DebateClash] = Field(default_factory=list, description="本回合交锋关系")


class DebateGuestResult(BaseModel):
    """踢馆结果：踢馆者发言 + 四子回应回合"""
    guest: SageSpeech
    reaction_round: DebateRound


class DebateReport(BaseModel):
    """百家会诊报告"""
    topic: str = Field(..., description="辩论议题")
    consensus: List[str] = Field(default_factory=list, description="共识点列表")
    divergences: List[str] = Field(default_factory=list, description="核心分歧列表")
    recommendations: List[Dict[str, str]] = Field(
        default_factory=list,
        description="各家建议，格式: [{'sage': '孔子', 'recommendation': '...'}]",
    )
    summary: str = Field("", description="总结陈词")
    participating_sages: List[str] = Field(default_factory=list, description="参与的圣贤列表")


class DebateGraphTrace(BaseModel):
    """状态图执行轨迹"""
    from_node: str
    to_node: str
    action: str
    ok: bool = True
    detail: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================
# 会话模型（内存状态）
# ============================================================

class DebateSession(BaseModel):
    """辩论会话（内存中维护，不持久化）"""
    id: str = Field(..., description="会话唯一ID")
    topic: str = Field(..., description="辩论议题")
    phase: Literal["init", "round1", "round2", "intervention", "report", "done"] = Field(
        "init", description="当前阶段"
    )
    participants: List[str] = Field(
        default_factory=list, description="参与圣贤的key列表"
    )
    rounds: List[DebateRound] = Field(default_factory=list, description="已完成的回合")
    report: Optional[DebateReport] = Field(None, description="会诊报告（完成后填充）")
    graph_trace: List[DebateGraphTrace] = Field(default_factory=list, description="主持状态图执行轨迹")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    round_counter: int = Field(0, description="已执行的回合数")

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 响应模型
# ============================================================

class DebateStartResponse(BaseModel):
    """开始辩论响应"""
    session_id: str
    topic: str
    participants: List[str]
    phase: str
    message: str = Field("", description="提示消息")


class DebateRoundResponse(BaseModel):
    """回合结果响应"""
    session_id: str
    round: DebateRound
    phase: str
    can_continue: bool = Field(True, description="是否可以继续下一轮")


class DebateGraphNode(BaseModel):
    """主持状态图节点"""
    id: str
    label: str
    kind: str


class DebateGraphTransition(BaseModel):
    """主持状态图边"""
    from_node: str
    to_node: str
    action: str


class DebateStateGraphResponse(BaseModel):
    """主持状态图响应"""
    session_id: str
    current_node: str
    nodes: List[DebateGraphNode]
    transitions: List[DebateGraphTransition]
    trace: List[DebateGraphTrace]


class DebateInterventionResponse(BaseModel):
    """用户介入响应"""
    session_id: str
    speech: SageSpeech
    phase: str


class DebateStandResponse(BaseModel):
    """论主站队响应"""
    session_id: str
    speech: SageSpeech
    round: DebateRound
    phase: str


class DebateMutualQuestionResponse(BaseModel):
    """请其互问响应"""
    session_id: str
    question: SageSpeech
    answer: SageSpeech
    round: DebateRound
    phase: str


class GuestRosterEntry(BaseModel):
    """踢馆名人花名册条目"""
    sage_key: str
    sage_name: str
    era: str
    core_thought: str
    unlocked: bool = True
    collected: bool = False
    staying: bool = False


class GuestRosterResponse(BaseModel):
    """踢馆名人花名册响应"""
    guests: List[GuestRosterEntry]


class DebateRandomGuestResponse(BaseModel):
    """随机踢馆响应"""
    session_id: str
    sage_key: str
    speech: SageSpeech
    reaction_round: Optional[DebateRound] = None
    phase: str
    triggered_randomly: bool = True


class GuestDecisionResponse(BaseModel):
    """踢馆名人留下/离去响应"""
    session_id: str
    sage_key: str
    staying: bool
    guest: GuestRosterEntry
    participants: List[str]


class DebateReportResponse(BaseModel):
    """会诊报告响应"""
    session_id: str
    report: DebateReport
    phase: str


class DebateSummonResponse(BaseModel):
    """召唤踢馆名人响应"""
    session_id: str
    sage_key: str
    speech: SageSpeech
    reaction_round: Optional[DebateRound] = None
    phase: str


class DebateErrorResponse(BaseModel):
    """辩论错误响应"""
    error: str
    detail: Optional[str] = None


class ThoughtCompassResponse(BaseModel):
    """思想坐标定位响应"""
    x: int
    y: int
    active_percent: int
    quiet_percent: int
    nearest_school: str
    label: str
    imprint: str
