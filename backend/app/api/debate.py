"""
悟典 - 百家论道 API 路由

端点：
- POST /api/debate/start          开始辩论
- POST /api/debate/{id}/next-round  进入下一轮（自动判断当前阶段）
- POST /api/debate/{id}/intervene   用户介入
- POST /api/debate/{id}/summon      召唤踢馆名人
- GET  /api/debate/{id}/report      获取会诊报告
- GET  /api/debate/{id}/session     获取会话状态

流式端点（SSE）：
- POST /api/debate/{id}/next-round?stream=true
- POST /api/debate/{id}/intervene?stream=true
"""
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user_or_demo
from app.models.user import User
from app.schemas.debate import (
    DebateStartRequest,
    DebateStartResponse,
    DebateRoundResponse,
    DebateStateGraphResponse,
    UserInterventionRequest,
    DebateInterventionResponse,
    StandRequest,
    DebateStandResponse,
    MutualQuestionRequest,
    DebateMutualQuestionResponse,
    GuestDecisionRequest,
    GuestRosterResponse,
    DebateRandomGuestResponse,
    GuestDecisionResponse,
    DebateReportResponse,
    DebateErrorResponse,
    SummonRequest,
    DebateSummonResponse,
    ThoughtCompassRequest,
    ThoughtCompassResponse,
)
from app.services.debate_engine import debate_engine
from app.services.debate_state_graph import debate_state_graph
from app.services.debate_storage import debate_storage
from app.services.guest_roster import choose_random_guest, list_guest_roster, mark_collected
from app.services.thought_compass import analyze_thought_compass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debate", tags=["百家论道"])


@router.post("/thought-compass", response_model=ThoughtCompassResponse, summary="思想坐标定位")
async def thought_compass(req: ThoughtCompassRequest):
    """根据论主表述生成思想坐标定位。"""
    return analyze_thought_compass(req.statement)


# ============================================================
# 开始辩论
# ============================================================
@router.get("/guests/roster", response_model=GuestRosterResponse, summary="踢馆名人花名册")
async def guest_roster():
    """获取完整踢馆名人花名册、解锁与收集状态。"""
    return GuestRosterResponse(guests=list_guest_roster())


@router.post("/start", response_model=DebateStartResponse, summary="开始辩论")
async def start_debate(
    req: DebateStartRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """创建辩论会话，指定议题和可选的圣贤阵容"""
    logger.info("用户 %s 发起辩论: topic=%s", current_user.id, req.topic)
    session = await debate_engine.start_debate(topic=req.topic, sages=req.sages)
    return DebateStartResponse(
        session_id=session.id,
        topic=session.topic,
        participants=session.participants,
        phase=session.phase,
        message="辩论会话已创建，请调用 next-round 开始第一轮（各陈己见）",
    )


# ============================================================
# 进入下一轮（支持流式）
# ============================================================
@router.post("/{session_id}/next-round", summary="进入下一轮辩论")
async def next_round(
    session_id: str,
    stream: bool = Query(True, description="是否流式返回（SSE）"),
    current_user: User = Depends(get_current_user_or_demo),
):
    """根据当前阶段自动推进：init->Round1, round1->Round2, round2->报告"""
    logger.info("用户 %s 请求下一轮: session=%s, stream=%s", current_user.id, session_id, stream)

    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")

    if stream:
        return StreamingResponse(
            _stream_next_round(session_id, session.phase),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    # 非流式
    try:
        return await debate_state_graph.execute_next(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("next-round 异常: %s", e)
        raise HTTPException(status_code=500, detail="辩论引擎内部错误")


async def _stream_next_round(session_id: str, phase: str) -> AsyncGenerator[str, None]:
    """SSE 流式推进辩论"""
    transition = None
    try:
        transition = debate_state_graph.transition_for_phase(phase)
        if phase in ("init",):
            # 发送阶段事件
            yield _sse({"type": "phase_change", "phase": "round1", "label": "第一轮：各陈己见"})
            async for chunk in debate_engine.stream_round1(session_id):
                yield _sse_raw(chunk)
        elif phase in ("round1", "round2"):
            yield _sse({"type": "phase_change", "phase": "round2", "label": "第二轮：交锋辩驳"})
            async for chunk in debate_engine.stream_round2(session_id):
                yield _sse_raw(chunk)
        elif phase in ("intervention",):
            yield _sse({"type": "phase_change", "phase": "report", "label": "生成会诊报告"})
            report = await debate_engine.generate_report(session_id)
            yield _sse({"type": "report", "report": report.model_dump()})
        elif phase == "done":
            session = debate_engine.get_session(session_id)
            if session and session.report:
                yield _sse({"type": "report", "report": session.report.model_dump()})
            else:
                report = await debate_engine.generate_report(session_id)
                yield _sse({"type": "report", "report": report.model_dump()})
        else:
            yield _sse({"type": "error", "detail": f"未知阶段: {phase}"})
    except Exception as e:
        logger.error("流式 next-round 异常: %s", e)
        yield _sse({"type": "error", "detail": "内部服务错误"})

    if transition:
        debate_state_graph.record_transition(session_id, transition, ok=True)

    yield "data: [DONE]\n\n"


# ============================================================
# 用户介入（支持流式）
# ============================================================
@router.post("/{session_id}/intervene", summary="用户介入辩论")
async def intervene(
    session_id: str,
    req: UserInterventionRequest,
    stream: bool = Query(True, description="是否流式返回（SSE）"),
    current_user: User = Depends(get_current_user_or_demo),
):
    """用户追问、质疑或表态，由指定圣贤或主持Agent路由回应"""
    logger.info("用户 %s 介入辩论: session=%s, content=%s", current_user.id, session_id, req.content[:50])

    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")

    if stream:
        return StreamingResponse(
            _stream_intervene(session_id, req),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    try:
        speech = await debate_engine.handle_user_intervention(session_id, req)
        return DebateInterventionResponse(session_id=session_id, speech=speech, phase=session.phase)
    except Exception as e:
        logger.error("intervene 异常: %s", e)
        raise HTTPException(status_code=500, detail="辩论引擎内部错误")


async def _stream_intervene(session_id: str, req: UserInterventionRequest) -> AsyncGenerator[str, None]:
    try:
        async for chunk in debate_engine.stream_intervention(session_id, req):
            yield _sse_raw(chunk)
    except Exception as e:
        logger.error("流式 intervene 异常: %s", e)
        yield _sse({"type": "error", "detail": "内部服务错误"})
    yield "data: [DONE]\n\n"


# ============================================================
# 召唤踢馆名人
# ============================================================
@router.post("/{session_id}/stand", response_model=DebateStandResponse, summary="论主站队")
async def stand_with_sage(
    session_id: str,
    req: StandRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """论主选择站队，由被站队圣贤独立回应。"""
    logger.info("用户 %s 站队: session=%s, target=%s", current_user.id, session_id, req.target_sage)

    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")

    try:
        rd, speech = await debate_engine.take_side(session_id, req.stance, req.target_sage)
        return DebateStandResponse(session_id=session_id, speech=speech, round=rd, phase=session.phase)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("站队失败: %s", e)
        raise HTTPException(status_code=500, detail="站队失败")


@router.post("/{session_id}/mutual-question", response_model=DebateMutualQuestionResponse, summary="请其互问")
async def mutual_question(
    session_id: str,
    req: MutualQuestionRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """让两位圣贤围绕当前议题完成一问一答。"""
    logger.info(
        "用户 %s 请其互问: session=%s, from=%s, to=%s",
        current_user.id,
        session_id,
        req.from_sage,
        req.to_sage,
    )

    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")

    try:
        rd, question, answer = await debate_engine.mutual_question(
            session_id,
            req.from_sage,
            req.to_sage,
            req.question,
        )
        return DebateMutualQuestionResponse(
            session_id=session_id,
            question=question,
            answer=answer,
            round=rd,
            phase=session.phase,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("互问失败: %s", e)
        raise HTTPException(status_code=500, detail="互问失败")


@router.post("/{session_id}/guests/random", response_model=DebateRandomGuestResponse, summary="随机踢馆")
async def random_guest(
    session_id: str,
    current_user: User = Depends(get_current_user_or_demo),
):
    """随机触发一位已解锁踢馆名人入场。"""
    logger.info("用户 %s 触发随机踢馆: session=%s", current_user.id, session_id)
    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")

    try:
        sage_key = choose_random_guest(exclude=session.participants)
        result = await debate_engine.summon_guest_with_reactions(session_id, sage_key)
        return DebateRandomGuestResponse(
            session_id=session_id,
            sage_key=sage_key,
            speech=result.guest,
            reaction_round=result.reaction_round,
            phase=session.phase,
            triggered_randomly=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("随机踢馆失败: %s", e)
        raise HTTPException(status_code=500, detail="随机踢馆失败")


@router.post("/{session_id}/guests/{sage_key}/decision", response_model=GuestDecisionResponse, summary="踢馆名人留下或离去")
async def decide_guest(
    session_id: str,
    sage_key: str,
    req: GuestDecisionRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """决定踢馆名人留下或离去；留下会收集到花名册。"""
    logger.info("用户 %s 决定踢馆名人去留: session=%s, sage=%s, decision=%s", current_user.id, session_id, sage_key, req.decision)
    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")

    try:
        staying = req.decision == "stay"
        if staying:
            if sage_key not in session.participants:
                session.participants.append(sage_key)
            guest = mark_collected(sage_key)
        else:
            session.participants = [key for key in session.participants if key != sage_key]
            guest = next(item for item in list_guest_roster(session.participants) if item["sage_key"] == sage_key)
        debate_storage.save(session)
        guest["staying"] = staying
        return GuestDecisionResponse(
            session_id=session_id,
            sage_key=sage_key,
            staying=staying,
            guest=guest,
            participants=session.participants,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StopIteration:
        raise HTTPException(status_code=400, detail=f"未知踢馆名人: {sage_key}")
    except Exception as e:
        logger.error("踢馆名人去留决策失败: %s", e)
        raise HTTPException(status_code=500, detail="踢馆名人去留决策失败")


@router.post("/{session_id}/summon", response_model=DebateSummonResponse, summary="召唤踢馆名人")
async def summon_guest(
    session_id: str,
    req: SummonRequest,
    current_user: User = Depends(get_current_user_or_demo),
):
    """召唤踢馆名人加入辩论"""
    logger.info("用户 %s 召唤踢馆名人: session=%s, sage_key=%s", current_user.id, session_id, req.sage_key)
    
    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")
    
    try:
        result = await debate_engine.summon_guest_with_reactions(session_id, req.sage_key)
        return DebateSummonResponse(
            session_id=session_id,
            sage_key=req.sage_key,
            speech=result.guest,
            reaction_round=result.reaction_round,
            phase=session.phase,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("召唤失败: %s", e)
        raise HTTPException(status_code=500, detail="召唤失败")


# ============================================================
# 获取会诊报告
# ============================================================
@router.get("/{session_id}/report", response_model=DebateReportResponse, summary="获取会诊报告")
async def get_report(
    session_id: str,
    current_user: User = Depends(get_current_user_or_demo),
):
    """获取辩论会诊报告（若未生成则自动生成）"""
    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")

    if session.report:
        return DebateReportResponse(session_id=session_id, report=session.report, phase=session.phase)

    try:
        report = await debate_engine.generate_report(session_id)
        return DebateReportResponse(session_id=session_id, report=report, phase="done")
    except Exception as e:
        logger.error("获取报告异常: %s", e)
        raise HTTPException(status_code=500, detail="会诊报告生成失败")


# ============================================================
# 获取会话状态
# ============================================================
@router.get("/{session_id}/state-graph", response_model=DebateStateGraphResponse, summary="获取主持状态图")
async def get_state_graph(
    session_id: str,
    current_user: User = Depends(get_current_user_or_demo),
):
    """获取主持 Agent 的显式状态图、当前节点与执行轨迹。"""
    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")
    return debate_state_graph.describe(session_id)


@router.get("/{session_id}/session", summary="获取辩论会话状态")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user_or_demo),
):
    """获取辩论会话的当前状态"""
    session = debate_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"辩论会话不存在: {session_id}")
    return session.model_dump()


# ============================================================
# SSE 工具函数
# ============================================================
def _sse(data: dict) -> str:
    """将 dict 包装为 SSE data 行"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _sse_raw(chunk: str) -> str:
    """如果 chunk 已是 SSE 格式则直接返回，否则包装"""
    if chunk.startswith("data:"):
        return chunk if chunk.endswith("\n\n") else chunk + "\n\n"
    return f"data: {chunk}\n\n"


# ============================================================
# 预设话题
# ============================================================
PRESET_TOPICS = [
    {"id": "t1", "topic": "人性本善还是本恶？", "tags": ["人性", "伦理"]},
    {"id": "t2", "topic": "何为真正的勇气？", "tags": ["勇气", "修身"]},
    {"id": "t3", "topic": "治国应以德还是以法？", "tags": ["政治", "治国"]},
    {"id": "t4", "topic": "面对不公，该沉默还是发声？", "tags": ["正义", "处世"]},
    {"id": "t5", "topic": "君子应该如何对待金钱？", "tags": ["金钱", "义利"]},
    {"id": "t6", "topic": "知易行难，如何做到知行合一？", "tags": ["知行", "实践"]},
]


@router.get("/presets", summary="获取预设话题列表")
async def get_preset_topics():
    """获取预设话题列表"""
    return {"topics": PRESET_TOPICS}


@router.get("/history", summary="获取辩论历史列表")
async def get_debate_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user_or_demo),
):
    """获取辩论历史列表"""
    sessions = debate_storage.list_sessions(limit)
    return {"sessions": sessions}
