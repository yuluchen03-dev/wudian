"""
悟典 - 百家论道主持Agent

职责：
- 路由用户介入到合适的圣贤
- 检测发言是否跑题
- 判断辩论是否应继续
- 生成会诊报告
"""
import logging
from typing import List, Optional

from app.schemas.debate import DebateSession, SageSpeech, DebateRound
from app.services.llm_client import llm_client
from app.services.sage_persona import SAGES
from app.core.config import settings

logger = logging.getLogger(__name__)

# 跑题检测提示词
TOPIC_DRIFT_SYSTEM = """你是一个辩论主持人，负责判断发言是否偏离议题。

判断标准：
1. 发言是否与议题直接相关
2. 是否在讨论议题的核心问题
3. 是否有实质性内容而非空泛议论

请以JSON格式返回：{"is_drift": true/false, "reason": "判断理由"}"""

# 继续判断提示词
SHOULD_CONTINUE_SYSTEM = """你是一个辩论主持人，判断辩论是否应继续。

判断标准：
1. 是否还有新的观点可以提出
2. 是否陷入了重复论证
3. 是否达到了有价值的结论

请以JSON格式返回：{"should_continue": true/false, "reason": "判断理由"}"""


class ModeratorAgent:
    """主持Agent：控场与路由"""
    
    async def check_topic_drift(self, topic: str, speech: SageSpeech) -> bool:
        """跑题检测：判断圣贤发言是否偏离议题"""
        messages = [
            {"role": "system", "content": TOPIC_DRIFT_SYSTEM},
            {"role": "user", "content": f"议题：{topic}\n发言：{speech.content}\n是否跑题？"},
        ]
        result = await llm_client.complete_json(messages, temperature=0.1)
        return result.get("is_drift", False)
    
    async def route_intervention(self, session: DebateSession, content: str) -> str:
        """路由用户介入到最合适的圣贤"""
        # 优先：用户指定的目标
        # 其次：基于发言内容的关键词匹配
        # 最后：最后一个发言的圣贤
        
        # 简单实现：返回最后一个发言的圣贤
        if session.rounds:
            last_round = session.rounds[-1]
            if last_round.speeches:
                return last_round.speeches[-1].sage_key
        
        # 如果没有发言记录，返回第一个参与者
        return session.participants[0] if session.participants else "confucius"
    
    async def should_continue(self, session: DebateSession) -> bool:
        """判断辩论是否应继续（防死循环）"""
        # 简单实现：最多3轮
        if session.round_counter >= settings.DEBATE_MAX_ROUNDS:
            return False
        
        # 收集最近两轮的发言
        if len(session.rounds) < 2:
            return True
        
        recent_rounds = session.rounds[-2:]
        all_speeches = []
        for rd in recent_rounds:
            all_speeches.extend(rd.speeches)
        
        if not all_speeches:
            return True
        
        # 检查发言内容是否有实质性变化
        messages = [
            {"role": "system", "content": SHOULD_CONTINUE_SYSTEM},
            {"role": "user", "content": f"最近发言：\n{chr(10).join([s.content[:200] for s in all_speeches])}"},
        ]
        result = await llm_client.complete_json(messages, temperature=0.1)
        return result.get("should_continue", True)


# 全局实例
moderator_agent = ModeratorAgent()