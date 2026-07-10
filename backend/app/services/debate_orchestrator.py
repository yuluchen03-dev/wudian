"""
悟典 - 百家论道辩论调度器

职责：
- 协调主持Agent、圣贤Agent、引用校验的完整流程
- 管理辩论轮次流转
- 集成跑题检测和死循环防护
"""
import logging
from typing import List, Optional

from app.schemas.debate import DebateSession, DebateRound, SageSpeech, DebateClash
from app.services.debate_engine import (
    debate_engine, _speak, _build_opinion_messages,
    _build_cross_messages, _build_intervention_messages,
)
from app.services.moderator_agent import moderator_agent
from app.services.rag_service import get_rag_service
from app.services.sage_persona import SAGES, get_sage, build_sage_system_prompt, get_sage_name

logger = logging.getLogger(__name__)


class DebateOrchestrator:
    """辩论调度器：协调多Agent协作"""

    def __init__(self):
        self.engine = debate_engine
        self.moderator = moderator_agent

    async def orchestrate_round1(self, session_id: str) -> DebateRound:
        """协调第一轮辩论（各陈己见）"""
        session = self.engine._get(session_id)
        session.phase = "round1"
        rd = DebateRound(round_number=1, round_type="opinion")

        rag = get_rag_service()

        for sk in session.participants:
            try:
                # 1. 圣贤发言
                sr = await rag.retrieve_for_sage_chat(session.topic, top_k=5)
                ctx = rag.build_sage_chat_context(sr)
                msgs = _build_opinion_messages(sk, session.topic, ctx)
                refs = sr.get("verses", []) + sr.get("commentaries", [])
                speech = await _speak(sk, msgs, 1, refs)

                # 2. 主持Agent检测跑题
                is_drift = await self.moderator.check_topic_drift(session.topic, speech)
                if is_drift:
                    speech.content = f"（主持提醒：请围绕议题「{session.topic}」发言）\n" + speech.content

                rd.speeches.append(speech)
                logger.info("R1 - %s 完成", get_sage_name(sk))
            except Exception as e:
                logger.error("R1 - %s 失败: %s", get_sage_name(sk), e)
                rd.speeches.append(SageSpeech(
                    sage_key=sk, sage_name=get_sage_name(sk), round_number=1,
                    content=f"（{get_sage_name(sk)}暂时无法发言）", confidence="low",
                ))

        session.rounds.append(rd)
        session.round_counter = 1
        session.phase = "round2"
        return rd

    async def orchestrate_round2(self, session_id: str) -> DebateRound:
        """协调第二轮辩论（交锋辩驳）"""
        session = self.engine._get(session_id)
        if session.round_counter < 1:
            raise ValueError("没有第一轮辩论记录")
        session.phase = "round2"

        # 获取第一轮的发言作为上下文
        r1_speeches = session.rounds[0].speeches if session.rounds else []
        rd = DebateRound(round_number=2, round_type="cross_debate")

        rag = get_rag_service()

        for sk in session.participants:
            try:
                # 过滤掉自己的发言
                others = [s for s in r1_speeches if s.sage_key != sk]
                sr = await rag.retrieve_for_sage_chat(session.topic, top_k=5)
                ctx = rag.build_sage_chat_context(sr)
                msgs = _build_cross_messages(sk, session.topic, ctx, others)
                refs = sr.get("verses", []) + sr.get("commentaries", [])
                speech = await _speak(sk, msgs, 2, refs)

                # 主持Agent检测跑题
                is_drift = await self.moderator.check_topic_drift(session.topic, speech)
                if is_drift:
                    speech.content = f"（主持提醒：请围绕议题「{session.topic}」发言）\n" + speech.content

                rd.speeches.append(speech)

                # 记录交锋关系
                tgt = speech.target_sage
                if tgt and tgt in SAGES:
                    rd.clashes.append(DebateClash(
                        from_sage=sk, to_sage=tgt,
                        clash_type="disagree", summary=speech.content[:100],
                    ))
                logger.info("R2 - %s 完成", get_sage_name(sk))
            except Exception as e:
                logger.error("R2 - %s 失败: %s", get_sage_name(sk), e)
                rd.speeches.append(SageSpeech(
                    sage_key=sk, sage_name=get_sage_name(sk), round_number=2,
                    content=f"（{get_sage_name(sk)}暂时无法发言）", confidence="low",
                ))

        session.rounds.append(rd)
        session.round_counter = 2
        session.phase = "intervention"
        return rd

    async def orchestrate_intervention(self, session_id: str, content: str, target_sage: Optional[str] = None) -> SageSpeech:
        """协调用户介入"""
        session = self.engine._get(session_id)

        # 如果没有指定目标圣贤，由主持Agent路由
        if not target_sage or target_sage not in SAGES:
            target_sage = await self.moderator.route_intervention(session, content)

        # 生成介入回应
        rag = get_rag_service()
        sr = await rag.retrieve_for_sage_chat(content, top_k=5)
        ctx = rag.build_sage_chat_context(sr)

        # _build_intervention_messages 内部自行遍历 session.rounds 获取历史
        msgs = _build_intervention_messages(target_sage, session.topic, ctx, content, session)
        refs = sr.get("verses", []) + sr.get("commentaries", [])
        speech = await _speak(target_sage, msgs, session.round_counter + 1, refs)

        # 更新 session 状态
        session.rounds.append(DebateRound(
            round_number=session.round_counter + 1,
            round_type="intervention",
            speeches=[speech],
        ))
        session.round_counter += 1

        return speech

    async def check_should_continue(self, session_id: str) -> bool:
        """检查辩论是否应继续"""
        session = self.engine._get(session_id)
        return await self.moderator.should_continue(session)


# 全局实例
debate_orchestrator = DebateOrchestrator()