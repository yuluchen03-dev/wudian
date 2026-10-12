"""
悟典 - 百家论道多智能体辩论引擎
复用: llm_client, rag_service, sage_persona
"""
import uuid
import json
import logging
import re
from typing import Dict, List, Optional, AsyncGenerator, Any, Tuple

from app.schemas.debate import (
    DebateSession, DebateRound, SageSpeech, DebateClash,
    DebateReport, Citation, SentenceEvidence, UserInterventionRequest, DebateGuestResult,
)
from app.services.llm_client import llm_client
from app.services.rag_service import get_rag_service
from app.services.sage_persona import SAGES, get_sage, build_sage_system_prompt, get_sage_name
from app.services.citation_validator import citation_validator
from app.services.debate_storage import debate_storage
from app.core.config import settings

logger = logging.getLogger(__name__)
_sessions: Dict[str, DebateSession] = {}
DEFAULT_PARTICIPANTS = settings.DEBATE_DEFAULT_PARTICIPANTS
_EXTRA_SAGES = set(settings.DEBATE_EXTRA_SAGES)

FALLBACK_QUOTES: Dict[str, Dict[str, str]] = {
    "confucius": {"quote": "士不可以不弘毅，任重而道远。", "source": "《论语·泰伯》"},
    "laozi": {"quote": "夫唯不争，故天下莫能与之争。", "source": "《道德经》"},
    "mozi": {"quote": "赖其力者生，不赖其力者不生。", "source": "《墨子》"},
    "hanfeizi": {"quote": "法不阿贵，绳不挠曲。", "source": "《韩非子·有度》"},
    "mencius": {"quote": "富贵不能淫，贫贱不能移，威武不能屈。", "source": "《孟子·滕文公下》"},
    "wang_yangming": {"quote": "知者行之始，行者知之成。", "source": "《传习录》"},
    "li_bai": {"quote": "人生得意须尽欢，莫使金樽空对月。", "source": "《将进酒》"},
    "su_shi": {"quote": "也无风雨也无晴。", "source": "《定风波》"},
    "fan_zhongyan": {"quote": "先天下之忧而忧，后天下之乐而乐。", "source": "《岳阳楼记》"},
    "wang_anshi": {"quote": "不畏浮云遮望眼，自缘身在最高层。", "source": "《登飞来峰》"},
    "zhuge_liang": {"quote": "非淡泊无以明志，非宁静无以致远。", "source": "《诫子书》"},
}

FALLBACK_STANCES: Dict[str, str] = {
    "confucius": "君子可以暂退以养志，却不可把疲惫误作弃道。先辨明你守的是什么志，再决定进退。",
    "laozi": "当放下的是争胜与攀比，不是生活本身。若退一步能复其自然，此退反是进。",
    "mozi": "不取命定之说。力气可以换到更有利天下与自身的地方，不能任由自己坠入无为之弃。",
    "hanfeizi": "先算清利害与退路。若无功无备而求安逸，势必受制；务实计功，方能长久。",
    "mencius": "人在困顿中更要护住本心。义之所在，不因贫贱威迫而移。",
    "wang_yangming": "你所谓知道该做什么，若不能行，便还未真知。且在一件小事上致良知。",
    "li_bai": "别只在内卷与躺平之间打转。天地甚阔，仍可痛快选择一种不负此生的活法。",
    "su_shi": "风雨来时不必硬扛成英雄，也不必倒下成败局。把日子过通透，路自然宽些。",
    "fan_zhongyan": "个人疲惫值得照看，但不能忘记自己与他人相连。退守也应保留担当。",
    "wang_anshi": "若赛道逼人至困，不只调心，还要改方法、改结构、改所处之势。",
    "zhuge_liang": "先宁静，再致远。休整不是放弃，而是为了更长程地尽责。",
}

FALLBACK_TARGETS: Dict[str, str] = {
    "confucius": "laozi",
    "laozi": "hanfeizi",
    "mozi": "laozi",
    "hanfeizi": "confucius",
    "mencius": "hanfeizi",
    "wang_yangming": "confucius",
    "li_bai": "confucius",
    "su_shi": "hanfeizi",
    "fan_zhongyan": "li_bai",
    "wang_anshi": "laozi",
    "zhuge_liang": "li_bai",
}


def _get_available_participants(requested: Optional[List[str]] = None) -> List[str]:
    if requested:
        available = [s for s in requested if s in SAGES]
        if available:
            return available
    return list(DEFAULT_PARTICIPANTS)


async def _retrieve_debate_context(sage_key: str, query: str, top_k: int = 5) -> tuple[str, List[dict]]:
    rag = get_rag_service()
    sr = await rag.retrieve_for_debate_sage(sage_key=sage_key, query=query, top_k=top_k)
    ctx = rag.build_debate_context(sage_key, sr)
    refs = sr.get("verses", []) + sr.get("commentaries", [])
    return ctx, refs


def _validate_citations(citations: List[dict], rag_refs: List[dict]) -> tuple[List[Citation], bool]:
    rag_originals = set()
    for ref in rag_refs:
        orig = ref.get("original", "")
        if orig:
            rag_originals.add(orig.strip())
            cleaned = orig.replace("。","").replace("，","").replace("？","").replace("！","").replace("；","").strip()
            if cleaned:
                rag_originals.add(cleaned)
    validated, all_verified = [], True
    for cit in citations:
        cit_id = cit.get("id", "")
        cit_source = cit.get("出处", cit.get("source", ""))
        cit_original = cit.get("原文", cit.get("original", ""))
        verifiable = False
        if cit_original and cit_original != "无":
            cit_cleaned = cit_original.replace("。","").replace("，","").replace("？","").replace("！","").replace("；","").strip()
            for rt in rag_originals:
                if cit_cleaned in rt or rt in cit_cleaned or cit_original in rt or rt in cit_original:
                    verifiable = True
                    break
        if not verifiable and cit_original and cit_original != "无":
            all_verified = False
            logger.warning("引用校验失败: '%s' 无法在RAG中匹配", cit_original[:30])
        validated.append(Citation(id=cit_id, source=cit_source, original=cit_original, verifiable=verifiable))
    return validated, all_verified


async def _validate_sage_citations(
    sage_key: str,
    citations: List[dict],
    rag_refs: List[dict],
) -> tuple[List[Citation], str]:
    return await citation_validator.validate(sage_key, citations, rag_refs)


def _split_sentences(text: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if not normalized:
        return []
    parts = re.findall(r"[^。！？!?]+[。！？!?]?", normalized)
    return [part.strip() for part in parts if part.strip()]


async def _bind_sentence_evidence(sage_key: str, content: str) -> List[SentenceEvidence]:
    evidence: List[SentenceEvidence] = []
    sentences = _split_sentences(content)
    if not sentences:
        return evidence
    rag = get_rag_service()
    for sentence in sentences:
        try:
            result = await rag.retrieve_for_debate_sage(sage_key=sage_key, query=sentence, top_k=1)
            refs = result.get("verses", []) + result.get("commentaries", [])
            ref = refs[0] if refs else {}
            original = ref.get("original", "") or "无"
            source = ref.get("source", "") or "无"
            evidence.append(
                SentenceEvidence(
                    sentence=sentence,
                    source=source,
                    original=original,
                    similarity=float(ref.get("similarity", 0.0) or 0.0),
                    verifiable=bool(refs and original != "无" and source != "无"),
                )
            )
        except Exception as e:
            logger.warning("逐句经典证据绑定失败: sage=%s sentence=%s error=%s", sage_key, sentence[:30], e)
            evidence.append(SentenceEvidence(sentence=sentence))
    return evidence


def _build_opinion_messages(sage_key: str, topic: str, rag_context: str) -> List[dict]:
    sage = get_sage(sage_key)
    sys_prompt = build_sage_system_prompt(sage_key, rag_context)
    user_msg = f"""【百家论道 · 各陈己见】
议题：{topic}
现在轮到你发言。请以{sage.name}的身份，围绕议题阐述立场。
要求：体现核心思想与说话风格，引用本派经典原文，3-6句文言口吻论述+白话点睛。
严格按JSON格式输出：
{{
  "content": "用{sage.name}口吻的论述（3-6句）",
  "vernacular": "白话点睛（1-3句）",
  "quote": "引用的经典原文（无则填'无'）",
  "source": "原文出处（无则填'无'）",
  "citations": [{{"id":"引1","出处":"...","原文":"..."}}],
  "confidence": "high|medium|low"
}}"""
    return [{"role":"system","content":sys_prompt},{"role":"user","content":user_msg}]


def _build_cross_messages(sage_key: str, topic: str, rag_context: str, other_speeches: List[SageSpeech]) -> List[dict]:
    sage = get_sage(sage_key)
    sys_prompt = build_sage_system_prompt(sage_key, rag_context)
    speeches_text = ""
    for sp in other_speeches:
        speeches_text += f"\n--- {sp.sage_name}的观点 ---\n{sp.content}\n"
        if sp.quote and sp.quote != "无":
            speeches_text += f"引用：「{sp.quote}」（{sp.source}）\n"
    user_msg = f"""【百家论道 · 交锋辩驳】
议题：{topic}
其他圣贤的观点：{speeches_text}
请针对以上观点回应。可赞同并补充、驳斥引用本派经典反驳、或延伸深化。
要求：体现{sage.name}核心思想，引用本派经典，保持论道风度（辩驳非攻讦），指明回应对象。
严格按JSON格式输出：
{{
  "content": "交锋回应（3-6句）",
  "vernacular": "白话点睛（1-3句）",
  "quote": "引用的经典原文",
  "source": "原文出处",
  "citations": [{{"id":"引1","出处":"...","原文":"..."}}],
  "target_sage": "主要回应的圣贤key",
  "clash_type": "agree|disagree|extend|refute",
  "confidence": "high|medium|low"
}}"""
    return [{"role":"system","content":sys_prompt},{"role":"user","content":user_msg}]


def _build_intervention_messages(sage_key: str, topic: str, rag_context: str, user_content: str, session: DebateSession) -> List[dict]:
    sage = get_sage(sage_key)
    sys_prompt = build_sage_system_prompt(sage_key, rag_context)
    history_text = ""
    for rd in session.rounds:
        for sp in rd.speeches:
            history_text += f"\n[{sp.sage_name}] {sp.content}\n"
    user_msg = f"""【百家论道 · 论主追问】
议题：{topic}
辩论历史：{history_text}
论主的问题："{user_content}"
请以{sage.name}身份回应，引用本派经典。
严格按JSON格式输出：
{{
  "content": "回应论主（3-6句）",
  "vernacular": "白话点睛（1-3句）",
  "quote": "引用的经典原文",
  "source": "原文出处",
  "citations": [{{"id":"引1","出处":"...","原文":"..."}}],
  "confidence": "high|medium|low"
}}"""
    return [{"role":"system","content":sys_prompt},{"role":"user","content":user_msg}]


def _build_stance_messages(sage_key: str, topic: str, rag_context: str, stance: str, session: DebateSession) -> List[dict]:
    sage = get_sage(sage_key)
    sys_prompt = build_sage_system_prompt(sage_key, rag_context)
    recent = []
    for rd in session.rounds[-2:]:
        for sp in rd.speeches:
            recent.append(f"[{sp.sage_name}] {sp.content[:160]}")
    history_text = "\n".join(recent)
    user_msg = f"""【百家论道 · 论主站队】
议题：{topic}
论主当前站队：{stance}
近期辩论记录：
{history_text}

请以{sage.name}身份回应论主的站队：可以肯定、提醒偏差、补充边界或提出修正。
要求：
1. 这是“站队”独立动作，不是普通追问。
2. 必须围绕论主选择的立场作答。
3. 引用本派经典支撑回应。
严格按JSON格式输出：
{{
  "content": "回应论主站队（3-6句）",
  "vernacular": "白话点睛（1-3句）",
  "quote": "引用的经典原文",
  "source": "原文出处",
  "citations": [{{"id":"引1","出处":"...","原文":"..."}}],
  "target_sage": "{sage_key}",
  "clash_type": "extend",
  "confidence": "high|medium|low"
}}"""
    return [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]


def _build_mutual_question_messages(
    sage_key: str,
    target_sage: str,
    topic: str,
    rag_context: str,
    session: DebateSession,
    question: Optional[str] = None,
    answer_to: Optional[SageSpeech] = None,
) -> List[dict]:
    sage = get_sage(sage_key)
    target_name = get_sage_name(target_sage)
    sys_prompt = build_sage_system_prompt(sage_key, rag_context)
    if answer_to:
        action = "回应对方提问"
        focus = f"{answer_to.sage_name}刚才向你发问：{answer_to.content}"
        output_content = "回应对方提问（3-6句）"
    else:
        action = "向对方发问"
        focus = question or f"请围绕议题向{target_name}提出一个能逼出分歧的追问。"
        output_content = "向对方提出问题，并简述追问理由（2-4句）"
    user_msg = f"""【百家论道 · 请其互问】
议题：{topic}
动作：{action}
对象：{target_name}({target_sage})
焦点：{focus}

请以{sage.name}身份完成本轮互问。必须点名回应对象，并引用本派经典。
严格按JSON格式输出：
{{
  "content": "{output_content}",
  "vernacular": "白话点睛（1-2句）",
  "quote": "引用的经典原文",
  "source": "原文出处",
  "citations": [{{"id":"引1","出处":"...","原文":"..."}}],
  "target_sage": "{target_sage}",
  "clash_type": "extend",
  "confidence": "high|medium|low"
}}"""
    return [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]


def _build_guest_messages(sage_key, topic, rag_context, all_speeches):
    """构建踢馆名人发言的prompt"""
    sage = get_sage(sage_key)
    sys_prompt = build_sage_system_prompt(sage_key, rag_context)
    
    history = ""
    for sp in all_speeches:
        history += f"\n[{sp.sage_name}] {sp.content[:200]}\n"
    
    user_msg = f"""【百家论道 · 踢馆挑战】
议题：{topic}
已有辩论记录：{history}
你是中途加入的挑战者。请以{sage.name}身份，针对已有辩论发表你的独特见解。
要求：
1. 体现{sage.name}核心思想
2. 引用本派经典
3. 可以赞同、反对或补充任何已有观点
4. 指出回应对象
严格按JSON格式输出：（同交锋辩驳格式）"""
    
    return [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]


def _build_guest_reaction_messages(
    sage_key: str,
    topic: str,
    rag_context: str,
    guest_speech: SageSpeech,
    session: DebateSession,
) -> List[dict]:
    """构建四子对踢馆者的回应 prompt"""
    sage = get_sage(sage_key)
    sys_prompt = build_sage_system_prompt(sage_key, rag_context)
    user_msg = f"""【百家论道 · 回应踢馆】
议题：{topic}
踢馆者：{guest_speech.sage_name}
踢馆观点：{guest_speech.content}

请以{sage.name}身份，针对踢馆者的观点作出回应。
要求：
1. 必须回应踢馆者，不要泛泛重述己见
2. 引用本派经典支撑回应
3. 保持论道风度，可赞同、反驳或重构
严格按JSON格式输出：
{{
  "content": "回应踢馆者（3-6句）",
  "vernacular": "白话点睛（1-3句）",
  "quote": "引用的经典原文",
  "source": "原文出处",
  "citations": [{{"id":"引1","出处":"...","原文":"..."}}],
  "target_sage": "{guest_speech.sage_key}",
  "clash_type": "agree|disagree|extend|refute|reframe",
  "confidence": "high|medium|low"
}}"""
    return [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}]


def _build_report_messages(session: DebateSession) -> List[dict]:
    all_speeches = ""
    for rd in session.rounds:
        labels = {1:"各陈己见",2:"交锋辩驳"}.get(rd.round_number, f"第{rd.round_number}轮")
        all_speeches += f"\n=== 第{rd.round_number}轮：{labels} ===\n"
        for sp in rd.speeches:
            all_speeches += f"\n【{sp.sage_name}】{sp.content}\n"
            if sp.quote and sp.quote != "无":
                all_speeches += f"引用：「{sp.quote}」（{sp.source}）\n"
    sage_names = [get_sage_name(s) for s in session.participants]
    sys_msg = "你是百家论道主持Agent。汇总全场辩论，抽取共识与分歧，提炼各家建议，生成客观精炼的会诊报告。语气庄重凝练。"
    user_msg = f"""【百家论道 · 会诊报告】
议题：{session.topic}
参与圣贤：{'、'.join(sage_names)}
辩论记录：{all_speeches}
严格按JSON格式输出：
{{
  "consensus": ["共识点1","共识点2"],
  "divergences": ["分歧1","分歧2"],
  "recommendations": [{{"sage":"孔子","recommendation":"..."}}],
  "summary": "总结陈词（3-5句）"
}}"""
    return [{"role":"system","content":sys_msg},{"role":"user","content":user_msg}]


async def _speak(sage_key: str, messages: List[dict], round_num: int, rag_refs: List[dict]) -> SageSpeech:
    try:
        data = await llm_client.complete_json(messages, temperature=0.8)
    except Exception as e:
        logger.warning("LLM不可用，使用%s离线论道兜底: %s", get_sage_name(sage_key), e)
        data = _fallback_speech_data(sage_key, round_num)
    raw_citations = data.get("citations", [])
    validated_citations, _ = await _validate_sage_citations(sage_key, raw_citations, rag_refs)
    if not validated_citations and data.get("quote") and data.get("quote") != "无":
        validated_citations = [
            Citation(
                id="引1",
                source=data.get("source", "无"),
                original=data.get("quote", "无"),
                verifiable=False,
            )
        ]
    content = data.get("content", "")
    sentence_evidence = await _bind_sentence_evidence(sage_key, content)
    return SageSpeech(
        sage_key=sage_key, sage_name=get_sage_name(sage_key), round_number=round_num,
        content=content, vernacular=data.get("vernacular",""),
        quote=data.get("quote","无"), source=data.get("source","无"),
        citations=validated_citations, sentence_evidence=sentence_evidence, target_sage=data.get("target_sage"),
        confidence=data.get("confidence","medium"),
    )


def _fallback_speech_data(sage_key: str, round_num: int) -> Dict[str, Any]:
    sage = get_sage(sage_key)
    quote = FALLBACK_QUOTES.get(sage_key, {"quote": "无", "source": "无"})
    stance = FALLBACK_STANCES.get(sage_key, sage.core_thought)
    if round_num == 1:
        content = f"{sage.name}曰：{stance}"
        vernacular = stance
        target = None
        clash_type = "extend"
    elif sage_key in {"li_bai", "su_shi", "fan_zhongyan", "wang_anshi", "zhuge_liang"}:
        content = f"{sage.name}踢馆曰：诸子所论各有锋芒，然吾别开一径。{stance}"
        vernacular = stance
        target = FALLBACK_TARGETS.get(sage_key)
        clash_type = "reframe"
    else:
        target = FALLBACK_TARGETS.get(sage_key)
        target_name = get_sage_name(target) if target in SAGES else "诸子"
        content = f"{sage.name}回应{target_name}曰：其言可听，然不可执一端。{stance}"
        vernacular = stance
        clash_type = "refute" if sage_key in {"mozi", "hanfeizi"} else "disagree"

    return {
        "content": content,
        "vernacular": vernacular,
        "quote": quote["quote"],
        "source": quote["source"],
        "citations": [{"id": "引1", "出处": quote["source"], "原文": quote["quote"]}],
        "target_sage": target,
        "clash_type": clash_type,
        "confidence": "medium",
    }


class DebateEngine:
    """百家论道辩论引擎"""

    async def start_debate(self, topic: str, sages: Optional[List[str]] = None) -> DebateSession:
        sid = str(uuid.uuid4())[:12]
        participants = _get_available_participants(sages)
        session = DebateSession(id=sid, topic=topic, phase="init", participants=participants)
        _sessions[sid] = session
        # 保存到持久化存储
        debate_storage.save(session)
        logger.info("辩论会话创建: id=%s, topic=%s, participants=%s", sid, topic, participants)
        return session

    async def run_round1_each_opinion(self, session_id: str) -> DebateRound:
        session = self._get(session_id)
        session.phase = "round1"
        rd = DebateRound(round_number=1, round_type="opinion")
        for sk in session.participants:
            try:
                ctx, refs = await _retrieve_debate_context(sk, session.topic, top_k=5)
                msgs = _build_opinion_messages(sk, session.topic, ctx)
                speech = await _speak(sk, msgs, 1, refs)
                rd.speeches.append(speech)
                logger.info("R1 - %s 完成", get_sage_name(sk))
            except Exception as e:
                logger.error("R1 - %s 失败: %s", get_sage_name(sk), e)
                rd.speeches.append(SageSpeech(sage_key=sk, sage_name=get_sage_name(sk), round_number=1,
                    content=f"（{get_sage_name(sk)}暂时无法发言）", confidence="low"))
        session.rounds.append(rd)
        session.round_counter = 1
        session.phase = "round2"
        # 保存到持久化存储
        debate_storage.save(session)
        return rd

    async def stream_round1(self, session_id: str) -> AsyncGenerator[str, None]:
        session = self._get(session_id)
        session.phase = "round1"
        rd = DebateRound(round_number=1, round_type="opinion")
        for sk in session.participants:
            sn = get_sage_name(sk)
            yield json.dumps({"type":"sage_start","sage_key":sk,"sage_name":sn,"round":1}, ensure_ascii=False)
            try:
                ctx, refs = await _retrieve_debate_context(sk, session.topic, top_k=5)
                msgs = _build_opinion_messages(sk, session.topic, ctx)
                if llm_client.is_available:
                    full = ""
                    async for chunk in llm_client.stream(msgs, temperature=0.8):
                        full += chunk
                        yield json.dumps({"type":"sage_chunk","sage_key":sk,"sage_name":sn,"content":chunk}, ensure_ascii=False)
                    try:
                        data = llm_client._parse_json(full)
                    except Exception:
                        data = {"content":full,"vernacular":"","quote":"无","source":"无","citations":[],"confidence":"medium"}
                else:
                    data = _fallback_speech_data(sk, 1)
                    yield json.dumps({"type":"sage_chunk","sage_key":sk,"sage_name":sn,"content":data["content"]}, ensure_ascii=False)
                vc, _ = await _validate_sage_citations(sk, data.get("citations",[]), refs)
                if not vc and data.get("quote") and data.get("quote") != "无":
                    vc = [Citation(id="引1", source=data.get("source","无"), original=data.get("quote","无"), verifiable=False)]
                content = data.get("content", full)
                sentence_evidence = await _bind_sentence_evidence(sk, content)
                sp = SageSpeech(sage_key=sk, sage_name=sn, round_number=1,
                    content=content, vernacular=data.get("vernacular",""),
                    quote=data.get("quote","无"), source=data.get("source","无"),
                    citations=vc, sentence_evidence=sentence_evidence, confidence=data.get("confidence","medium"))
                rd.speeches.append(sp)
                yield json.dumps({"type":"sage_end","sage_key":sk,"sage_name":sn,"speech":sp.model_dump()}, ensure_ascii=False)
            except Exception as e:
                # 不记录异常负载（可能含 Authorization/Bearer）；对外也只给稳定错误码。
                logger.error("R1流式 - %s 失败", sn)
                yield json.dumps({"type":"sage_error","sage_key":sk,"sage_name":sn,"error":"llm_unavailable"}, ensure_ascii=False)
        session.rounds.append(rd)
        session.round_counter = 1
        session.phase = "round2"
        # 保存到持久化存储
        debate_storage.save(session)
        yield json.dumps({"type":"round_done","round":1}, ensure_ascii=False)

    async def run_round2_cross_debate(self, session_id: str) -> DebateRound:
        session = self._get(session_id)
        if session.round_counter < 1:
            raise ValueError("请先完成第一轮")
        session.phase = "round2"
        r1_speeches = session.rounds[0].speeches if session.rounds else []
        rd = DebateRound(round_number=2, round_type="cross_debate")
        for sk in session.participants:
            try:
                others = [s for s in r1_speeches if s.sage_key != sk]
                ctx, refs = await _retrieve_debate_context(sk, session.topic, top_k=5)
                msgs = _build_cross_messages(sk, session.topic, ctx, others)
                speech = await _speak(sk, msgs, 2, refs)
                rd.speeches.append(speech)
                tgt = speech.target_sage
                if tgt and tgt in SAGES:
                    rd.clashes.append(DebateClash(from_sage=sk, to_sage=tgt,
                        clash_type="disagree", summary=speech.content[:100]))
                logger.info("R2 - %s 完成", get_sage_name(sk))
            except Exception as e:
                logger.error("R2 - %s 失败: %s", get_sage_name(sk), e)
                rd.speeches.append(SageSpeech(sage_key=sk, sage_name=get_sage_name(sk), round_number=2,
                    content=f"（{get_sage_name(sk)}暂时无法发言）", confidence="low"))
        session.rounds.append(rd)
        session.round_counter = 2
        session.phase = "intervention"
        # 保存到持久化存储
        debate_storage.save(session)
        return rd

    async def stream_round2(self, session_id: str) -> AsyncGenerator[str, None]:
        session = self._get(session_id)
        if session.round_counter < 1:
            raise ValueError("请先完成第一轮")
        session.phase = "round2"
        r1_speeches = session.rounds[0].speeches if session.rounds else []
        rd = DebateRound(round_number=2, round_type="cross_debate")
        for sk in session.participants:
            sn = get_sage_name(sk)
            others = [s for s in r1_speeches if s.sage_key != sk]
            yield json.dumps({"type":"sage_start","sage_key":sk,"sage_name":sn,"round":2}, ensure_ascii=False)
            try:
                ctx, refs = await _retrieve_debate_context(sk, session.topic, top_k=5)
                msgs = _build_cross_messages(sk, session.topic, ctx, others)
                if llm_client.is_available:
                    full = ""
                    async for chunk in llm_client.stream(msgs, temperature=0.85):
                        full += chunk
                        yield json.dumps({"type":"sage_chunk","sage_key":sk,"sage_name":sn,"content":chunk}, ensure_ascii=False)
                    try:
                        data = llm_client._parse_json(full)
                    except Exception:
                        data = {"content":full,"vernacular":"","quote":"无","source":"无","citations":[],"confidence":"medium","target_sage":None,"clash_type":"disagree"}
                else:
                    data = _fallback_speech_data(sk, 2)
                    yield json.dumps({"type":"sage_chunk","sage_key":sk,"sage_name":sn,"content":data["content"]}, ensure_ascii=False)
                vc, _ = await _validate_sage_citations(sk, data.get("citations",[]), refs)
                if not vc and data.get("quote") and data.get("quote") != "无":
                    vc = [Citation(id="引1", source=data.get("source","无"), original=data.get("quote","无"), verifiable=False)]
                content = data.get("content", full)
                sentence_evidence = await _bind_sentence_evidence(sk, content)
                sp = SageSpeech(sage_key=sk, sage_name=sn, round_number=2,
                    content=content, vernacular=data.get("vernacular",""),
                    quote=data.get("quote","无"), source=data.get("source","无"),
                    citations=vc, sentence_evidence=sentence_evidence, target_sage=data.get("target_sage"), confidence=data.get("confidence","medium"))
                rd.speeches.append(sp)
                tgt = data.get("target_sage")
                if tgt and tgt in SAGES:
                    rd.clashes.append(DebateClash(from_sage=sk, to_sage=tgt,
                        clash_type=data.get("clash_type","disagree"), summary=sp.content[:100]))
                yield json.dumps({"type":"sage_end","sage_key":sk,"sage_name":sn,"speech":sp.model_dump()}, ensure_ascii=False)
            except Exception as e:
                # 不记录异常负载（可能含 Authorization/Bearer）；对外也只给稳定错误码。
                logger.error("R2流式 - %s 失败", sn)
                yield json.dumps({"type":"sage_error","sage_key":sk,"sage_name":sn,"error":"llm_unavailable"}, ensure_ascii=False)
        session.rounds.append(rd)
        session.round_counter = 2
        session.phase = "intervention"
        # 保存到持久化存储
        debate_storage.save(session)
        yield json.dumps({"type":"round_done","round":2,"clashes":[c.model_dump() for c in rd.clashes]}, ensure_ascii=False)

    async def handle_user_intervention(self, session_id: str, intervention: UserInterventionRequest) -> SageSpeech:
        session = self._get(session_id)
        target = intervention.target_sage
        if not target or target not in SAGES:
            target = session.rounds[-1].speeches[-1].sage_key if session.rounds and session.rounds[-1].speeches else session.participants[0]
        ctx, refs = await _retrieve_debate_context(target, intervention.content, top_k=5)
        msgs = _build_intervention_messages(target, session.topic, ctx, intervention.content, session)
        speech = await _speak(target, msgs, session.round_counter + 1, refs)
        session.rounds.append(DebateRound(round_number=session.round_counter+1, round_type="intervention", speeches=[speech]))
        session.round_counter += 1
        # 保存到持久化存储
        debate_storage.save(session)
        return speech

    async def take_side(self, session_id: str, stance: str, target_sage: Optional[str] = None) -> Tuple[DebateRound, SageSpeech]:
        """Record a user stance as its own debate action."""
        session = self._get(session_id)
        target = target_sage
        if not target or target not in SAGES:
            target = session.participants[0] if session.participants else "confucius"
        if target not in session.participants:
            session.participants.append(target)

        ctx, refs = await _retrieve_debate_context(target, stance, top_k=5)
        msgs = _build_stance_messages(target, session.topic, ctx, stance, session)
        speech = await _speak(target, msgs, session.round_counter + 1, refs)
        speech.target_sage = target

        rd = DebateRound(
            round_number=session.round_counter + 1,
            round_type="stance",
            speeches=[speech],
        )
        session.rounds.append(rd)
        session.round_counter += 1
        session.phase = "intervention"
        session.report = None
        debate_storage.save(session)
        return rd, speech

    async def mutual_question(
        self,
        session_id: str,
        from_sage: str,
        to_sage: str,
        question: Optional[str] = None,
    ) -> Tuple[DebateRound, SageSpeech, SageSpeech]:
        """Let two sages question and answer each other as an explicit action."""
        session = self._get(session_id)
        if from_sage not in SAGES:
            raise ValueError(f"Unknown source sage: {from_sage}")
        if to_sage not in SAGES:
            raise ValueError(f"Unknown target sage: {to_sage}")
        if from_sage == to_sage:
            raise ValueError("from_sage and to_sage must be different")
        for sage_key in (from_sage, to_sage):
            if sage_key not in session.participants:
                session.participants.append(sage_key)

        round_number = session.round_counter + 1
        from_ctx, from_refs = await _retrieve_debate_context(from_sage, question or session.topic, top_k=5)
        question_msgs = _build_mutual_question_messages(
            from_sage,
            to_sage,
            session.topic,
            from_ctx,
            session,
            question=question,
        )
        question_speech = await _speak(from_sage, question_msgs, round_number, from_refs)
        question_speech.target_sage = to_sage

        to_ctx, to_refs = await _retrieve_debate_context(to_sage, question_speech.content or session.topic, top_k=5)
        answer_msgs = _build_mutual_question_messages(
            to_sage,
            from_sage,
            session.topic,
            to_ctx,
            session,
            answer_to=question_speech,
        )
        answer_speech = await _speak(to_sage, answer_msgs, round_number, to_refs)
        answer_speech.target_sage = from_sage

        rd = DebateRound(
            round_number=round_number,
            round_type="mutual_question",
            speeches=[question_speech, answer_speech],
            clashes=[
                DebateClash(
                    from_sage=from_sage,
                    to_sage=to_sage,
                    clash_type="extend",
                    summary=question_speech.content[:100],
                )
            ],
        )
        session.rounds.append(rd)
        session.round_counter = round_number
        session.phase = "intervention"
        session.report = None
        debate_storage.save(session)
        return rd, question_speech, answer_speech

    async def stream_intervention(self, session_id: str, intervention: UserInterventionRequest) -> AsyncGenerator[str, None]:
        session = self._get(session_id)
        target = intervention.target_sage
        if not target or target not in SAGES:
            target = session.rounds[-1].speeches[-1].sage_key if session.rounds and session.rounds[-1].speeches else session.participants[0]
        sn = get_sage_name(target)
        yield json.dumps({"type":"sage_start","sage_key":target,"sage_name":sn,"context":"intervention"}, ensure_ascii=False)
        ctx, refs = await _retrieve_debate_context(target, intervention.content, top_k=5)
        msgs = _build_intervention_messages(target, session.topic, ctx, intervention.content, session)
        if llm_client.is_available:
            full = ""
            async for chunk in llm_client.stream(msgs, temperature=0.8):
                full += chunk
                yield json.dumps({"type":"sage_chunk","sage_key":target,"sage_name":sn,"content":chunk}, ensure_ascii=False)
            try:
                data = llm_client._parse_json(full)
            except Exception:
                data = {"content":full,"vernacular":"","quote":"无","source":"无","citations":[],"confidence":"medium"}
        else:
            data = _fallback_speech_data(target, session.round_counter + 1)
            data["content"] = f"{sn}答论主曰：汝问「{intervention.content[:80]}」，此问切身。{data['vernacular']}"
            yield json.dumps({"type":"sage_chunk","sage_key":target,"sage_name":sn,"content":data["content"]}, ensure_ascii=False)
        vc, _ = await _validate_sage_citations(target, data.get("citations",[]), refs)
        if not vc and data.get("quote") and data.get("quote") != "无":
            vc = [Citation(id="引1", source=data.get("source","无"), original=data.get("quote","无"), verifiable=False)]
        content = data.get("content", full)
        sentence_evidence = await _bind_sentence_evidence(target, content)
        sp = SageSpeech(sage_key=target, sage_name=sn, round_number=session.round_counter+1,
            content=content, vernacular=data.get("vernacular",""),
            quote=data.get("quote","无"), source=data.get("source","无"),
            citations=vc, sentence_evidence=sentence_evidence, confidence=data.get("confidence","medium"))
        session.rounds.append(DebateRound(round_number=session.round_counter+1, round_type="intervention", speeches=[sp]))
        session.round_counter += 1
        # 保存到持久化存储
        debate_storage.save(session)
        yield json.dumps({"type":"sage_end","sage_key":target,"sage_name":sn,"speech":sp.model_dump()}, ensure_ascii=False)

    async def summon_guest(self, session_id: str, sage_key: str) -> SageSpeech:
        """召唤踢馆名人加入辩论"""
        result = await self.summon_guest_with_reactions(session_id, sage_key)
        return result.guest

    async def summon_guest_with_reactions(self, session_id: str, sage_key: str) -> DebateGuestResult:
        """召唤踢馆名人，并让默认四子分别回应。"""
        session = self._get(session_id)
        
        # 1. 验证踢馆名人可用
        if sage_key not in _EXTRA_SAGES and sage_key not in SAGES:
            raise ValueError(f"不可召唤的圣贤: {sage_key}")
        
        # 2. 将踢馆名人加入参与者列表
        if sage_key not in session.participants:
            session.participants.append(sage_key)
        
        # 3. 收集所有已有发言作为上下文
        all_speeches = []
        for rd in session.rounds:
            all_speeches.extend(rd.speeches)
        
        # 4. 生成踢馆发言
        ctx, refs = await _retrieve_debate_context(sage_key, session.topic, top_k=5)
        msgs = _build_guest_messages(sage_key, session.topic, ctx, all_speeches)
        speech = await _speak(sage_key, msgs, session.round_counter + 1, refs)
        speech.is_guest = True
        
        # 5. 追加到当前轮次
        guest_round = DebateRound(
            round_number=session.round_counter + 1,
            round_type="guest",
            speeches=[speech],
        )
        session.rounds.append(guest_round)
        session.round_counter += 1

        reaction_round = await self._run_guest_reactions(session, speech)
        session.rounds.append(reaction_round)
        session.round_counter = reaction_round.round_number
        session.phase = "intervention"
        session.report = None
        # 保存到持久化存储
        debate_storage.save(session)
        
        return DebateGuestResult(guest=speech, reaction_round=reaction_round)

    async def _run_guest_reactions(self, session: DebateSession, guest_speech: SageSpeech) -> DebateRound:
        core_participants = [sage_key for sage_key in DEFAULT_PARTICIPANTS if sage_key in session.participants]
        round_number = session.round_counter + 1
        rd = DebateRound(round_number=round_number, round_type="guest_response")
        for sk in core_participants:
            try:
                ctx, refs = await _retrieve_debate_context(sk, session.topic, top_k=5)
                msgs = _build_guest_reaction_messages(sk, session.topic, ctx, guest_speech, session)
                reaction = await _speak(sk, msgs, round_number, refs)
                reaction.target_sage = guest_speech.sage_key
                rd.speeches.append(reaction)
                rd.clashes.append(
                    DebateClash(
                        from_sage=sk,
                        to_sage=guest_speech.sage_key,
                        clash_type="reframe" if sk in {"confucius", "laozi"} else "refute",
                        summary=reaction.content[:100],
                    )
                )
            except Exception as e:
                logger.error("%s 回应踢馆失败: %s", get_sage_name(sk), e)
                rd.speeches.append(
                    SageSpeech(
                        sage_key=sk,
                        sage_name=get_sage_name(sk),
                        round_number=round_number,
                        content=f"（{get_sage_name(sk)}暂时无法回应踢馆）",
                        target_sage=guest_speech.sage_key,
                        confidence="low",
                    )
                )
        return rd

    async def generate_report(self, session_id: str) -> DebateReport:
        session = self._get(session_id)
        session.phase = "report"
        msgs = _build_report_messages(session)
        try:
            data = await llm_client.complete_json(msgs, temperature=0.5)
        except Exception:
            # 不记录异常负载（可能含 Authorization/Bearer）。
            logger.error("会诊报告生成失败")
            data = {
                "consensus": [
                    "纯粹消极的放弃不可取，进退都需要保留清醒判断。",
                    "论主应先辨明自己是需要休整、换路，还是已经放弃行动。",
                ],
                "divergences": [
                    "儒家重守志与担当，道家重顺势与不争。",
                    "墨家反宿命、强调强力实践，法家强调利害、制度与退路。",
                    "踢馆名人提供诗性、旷达、家国或变法等第三视角。",
                ],
                "recommendations": [
                    {"sage": get_sage_name(s), "recommendation": FALLBACK_STANCES.get(s, "保留自身立场，同时听取诸家之长。")}
                    for s in session.participants
                ],
                "summary": "本次论道不替论主给出唯一答案，而是把不同世界观并置：该退时退，该进时进，关键是不要让疲惫伪装成宿命，也不要让进取沦为盲目内卷。",
            }
        report = DebateReport(topic=session.topic, consensus=data.get("consensus",[]),
            divergences=data.get("divergences",[]), recommendations=data.get("recommendations",[]),
            summary=data.get("summary",""), participating_sages=[get_sage_name(s) for s in session.participants])
        session.report = report
        session.phase = "done"
        # 保存到持久化存储
        debate_storage.save(session)
        return report

    def get_session(self, session_id: str) -> Optional[DebateSession]:
        # 首先从内存缓存获取
        session = _sessions.get(session_id)
        if session:
            return session
        
        # 然后从持久化存储加载
        session = debate_storage.load(session_id)
        if session:
            _sessions[session_id] = session
            return session
        
        return None

    def _get(self, session_id: str) -> DebateSession:
        # 首先从内存缓存获取
        session = _sessions.get(session_id)
        if session:
            return session
        
        # 然后从持久化存储加载
        session = debate_storage.load(session_id)
        if session:
            _sessions[session_id] = session
            return session
        
        raise ValueError(f"辩论会话不存在: {session_id}")


debate_engine = DebateEngine()
