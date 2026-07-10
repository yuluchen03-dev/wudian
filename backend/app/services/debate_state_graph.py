"""
Explicit state-graph orchestration for Baijia debate sessions.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from app.schemas.debate import (
    DebateGraphNode,
    DebateGraphTrace,
    DebateGraphTransition,
    DebateReportResponse,
    DebateRoundResponse,
    DebateStateGraphResponse,
)
from app.services.debate_engine import debate_engine
from app.services.debate_storage import debate_storage


NODES: List[DebateGraphNode] = [
    DebateGraphNode(id="init", label="开场建局", kind="start"),
    DebateGraphNode(id="round1", label="各陈己见", kind="agent_round"),
    DebateGraphNode(id="round2", label="交锋辩驳", kind="agent_round"),
    DebateGraphNode(id="intervention", label="论主介入", kind="human_agent"),
    DebateGraphNode(id="report", label="主持会诊", kind="moderator"),
    DebateGraphNode(id="done", label="收束完成", kind="terminal"),
]

TRANSITIONS: List[DebateGraphTransition] = [
    DebateGraphTransition(from_node="init", to_node="round1", action="run_round1_each_opinion"),
    DebateGraphTransition(from_node="round1", to_node="round2", action="run_round2_cross_debate"),
    DebateGraphTransition(from_node="round2", to_node="intervention", action="run_round2_cross_debate"),
    DebateGraphTransition(from_node="round2", to_node="report", action="generate_report"),
    DebateGraphTransition(from_node="intervention", to_node="report", action="generate_report"),
    DebateGraphTransition(from_node="report", to_node="done", action="return_report"),
    DebateGraphTransition(from_node="done", to_node="done", action="return_report"),
]


def _phase_to_node(phase: str) -> str:
    if phase == "round2":
        return "round2"
    if phase == "done":
        return "done"
    return phase


def _find_transition(current_node: str) -> DebateGraphTransition:
    for transition in TRANSITIONS:
        if transition.from_node == current_node:
            return transition
    raise ValueError(f"Unknown graph node: {current_node}")


class DebateStateGraph:
    """Small LangGraph-like runner for the existing debate engine."""

    async def execute_next(self, session_id: str):
        session = debate_engine._get(session_id)
        current_node = _phase_to_node(session.phase)
        transition = _find_transition(current_node)
        try:
            response = await self._run_transition(session_id, transition)
            trace = DebateGraphTrace(
                from_node=transition.from_node,
                to_node=transition.to_node,
                action=transition.action,
                ok=True,
            )
        except Exception as exc:
            trace = DebateGraphTrace(
                from_node=transition.from_node,
                to_node=transition.to_node,
                action=transition.action,
                ok=False,
                detail=str(exc),
            )
            session.graph_trace.append(trace)
            debate_storage.save(session)
            raise

        session = debate_engine._get(session_id)
        session.graph_trace.append(trace)
        debate_storage.save(session)
        return response

    def transition_for_phase(self, phase: str) -> DebateGraphTransition:
        return _find_transition(_phase_to_node(phase))

    def record_transition(
        self,
        session_id: str,
        transition: DebateGraphTransition,
        ok: bool = True,
        detail: str | None = None,
    ) -> None:
        session = debate_engine._get(session_id)
        session.graph_trace.append(
            DebateGraphTrace(
                from_node=transition.from_node,
                to_node=transition.to_node,
                action=transition.action,
                ok=ok,
                detail=detail or "",
            )
        )
        debate_storage.save(session)

    async def _run_transition(self, session_id: str, transition: DebateGraphTransition):
        session = debate_engine._get(session_id)
        if transition.action == "run_round1_each_opinion":
            rd = await debate_engine.run_round1_each_opinion(session_id)
            return DebateRoundResponse(session_id=session_id, round=rd, phase=session.phase, can_continue=True)
        if transition.action == "run_round2_cross_debate":
            rd = await debate_engine.run_round2_cross_debate(session_id)
            return DebateRoundResponse(session_id=session_id, round=rd, phase=session.phase, can_continue=True)
        if transition.action == "generate_report":
            report = await debate_engine.generate_report(session_id)
            return DebateReportResponse(session_id=session_id, report=report, phase="done")
        if transition.action == "return_report":
            if session.report:
                return DebateReportResponse(session_id=session_id, report=session.report, phase=session.phase)
            report = await debate_engine.generate_report(session_id)
            return DebateReportResponse(session_id=session_id, report=report, phase="done")
        raise ValueError(f"Unknown graph action: {transition.action}")

    def describe(self, session_id: str) -> DebateStateGraphResponse:
        session = debate_engine._get(session_id)
        return DebateStateGraphResponse(
            session_id=session_id,
            current_node=_phase_to_node(session.phase),
            nodes=NODES,
            transitions=TRANSITIONS,
            trace=session.graph_trace,
        )


debate_state_graph = DebateStateGraph()
