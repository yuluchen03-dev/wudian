"""
悟典 - 现代问题结构化器（PHASE 3 / P3-01）

职责
----
把现代现实问题结构化为「场景 → 核心冲突 → 思想概念」，供 RAG V2 的
Stage 1（Query Analyzer）与 Stage 2（Modern→Classical 概念扩展）使用。

PROJECT-BRIEF 第七章明确要求：

    用户输入「同事抢了我的功劳，我该不该跟他撕破脸？」
    **不能直接丢给 embedding**。先转换 scene / actors / conflict /
    emotion / choices / concepts，再检索原典。

设计约束（本模块的硬性纪律）
----------------------------
1. **确定性**：纯规则 + 本体匹配。**不调用 LLM、不访问网络**，相同输入
   在任何环境都得到相同输出，可离线复现。
2. **不硬编**：无法归类时显式返回 ``scene=None, confidence=0.0``，
   绝不用「最相近的一个」凑答案。命中但置信度不足时置
   ``needs_clarification=True``。
3. **概念有依据**：``concepts`` 只能取自
   ``data/processed/modern_issue_ontology.json`` 的受控概念表，每个概念都
   带学派与释义；不做自由联想。

本模块**不修改** ``rag_service.py``：PHASE 4 的 retrieval pipeline 负责调用它。
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.issue import (
    LOW_CONFIDENCE_THRESHOLD,
    IssueStructure,
)

logger = logging.getLogger(__name__)

#: 本体文件位置（仓库根 / data / processed）
_ONTOLOGY_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "modern_issue_ontology.json"
)

#: 归一化时移除的字符：空白 + 常见中英文标点。
#: 只做「不影响语义」的归一化，不做繁简转换（避免误伤古文引用）。
_NORMALIZE_DROP = re.compile(r"[\s，。！？；：、,\.!\?;:\"'“”‘’（）()【】\[\]《》<>·…—\-]+")


class OntologyError(RuntimeError):
    """本体文件缺失或结构非法。"""


@lru_cache(maxsize=1)
def _load_ontology() -> Dict[str, Any]:
    """加载并校验本体（进程级缓存，只读一次）。"""
    if not _ONTOLOGY_PATH.exists():
        raise OntologyError(f"Modern Issue Ontology 不存在: {_ONTOLOGY_PATH}")
    try:
        with open(_ONTOLOGY_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:  # pragma: no cover - 防御性
        raise OntologyError(f"Modern Issue Ontology 不是合法 JSON: {exc}") from exc

    scenes = data.get("scenes")
    if not isinstance(scenes, dict) or not scenes:
        raise OntologyError("本体缺少非空的 scenes 字段")
    concepts = data.get("concepts")
    if not isinstance(concepts, dict) or not concepts:
        raise OntologyError("本体缺少非空的 concepts 受控词表")
    return data


def normalize(text: str) -> str:
    """归一化输入：去空白与标点、转小写。确定性、无副作用。"""
    if not text:
        return ""
    return _NORMALIZE_DROP.sub("", text).lower()


def _scene_score(normalized: str, spec: Dict[str, Any]) -> Tuple[float, List[str]]:
    """计算单个 scene 的得分与命中的触发词。

    得分 = specificity × Σ len(trigger)
    长触发词贡献更大，避免短词（如「钱」）压过具体短语（如「抢了我的功劳」）。
    """
    specificity = float(spec.get("specificity", 1.0))
    hits: List[str] = []
    raw = 0
    for trigger in spec.get("triggers", []):
        token = normalize(trigger)
        if token and token in normalized:
            hits.append(trigger)
            raw += len(token)
    return specificity * raw, hits


def _detect_emotions(normalized: str, ontology: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """从文本中检测情绪标记，返回 (情绪列表, 命中的标记词)。"""
    markers: Dict[str, str] = ontology.get("emotion_markers", {})
    found: List[str] = []
    matched: List[str] = []
    # 按标记长度降序，保证更具体的标记先命中（确定性顺序）
    for word in sorted(markers, key=lambda item: (-len(item), item)):
        token = normalize(word)
        if token and token in normalized:
            emotion = markers[word]
            matched.append(word)
            if emotion not in found:
                found.append(emotion)
    return found, matched


def structure(query: str) -> IssueStructure:
    """把现代问题文本结构化为 :class:`IssueStructure`。

    无法归类时返回 ``scene=None, confidence=0.0, needs_clarification=True``，
    且所有要素为空列表——这是**明确表示无匹配**，不是错误。
    """
    ontology = _load_ontology()
    scenes: Dict[str, Dict[str, Any]] = ontology["scenes"]
    version = str(ontology.get("ontology_version", "unknown"))

    original = query or ""
    normalized = normalize(original)

    # --- 空输入：显式低置信度，禁止归类 ---
    if not normalized:
        return IssueStructure(
            query=original,
            normalized_query=normalized,
            scene=None,
            confidence=0.0,
            needs_clarification=True,
            ontology_version=version,
        )

    # --- 逐 scene 打分 ---
    scores: Dict[str, float] = {}
    hits_by_scene: Dict[str, List[str]] = {}
    for scene_key, spec in scenes.items():
        score, hits = _scene_score(normalized, spec)
        if score > 0:
            scores[scene_key] = score
            hits_by_scene[scene_key] = hits

    # --- 无任何命中：显式低置信度，禁止归类 ---
    if not scores:
        return IssueStructure(
            query=original,
            normalized_query=normalized,
            scene=None,
            confidence=0.0,
            needs_clarification=True,
            ontology_version=version,
        )

    # 确定性排序：得分降序，同分按 scene 名字典序（避免依赖 dict 顺序）
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    primary_scene, primary_score = ranked[0]
    spec = scenes[primary_scene]

    confidence_full = float(ontology.get("matching", {}).get("confidence_full_score", 10.0))
    ratio = float(ontology.get("matching", {}).get("secondary_scene_ratio", 0.5))
    confidence = min(1.0, primary_score / confidence_full) if confidence_full > 0 else 0.0

    secondary = [
        name for name, value in ranked[1:]
        if value >= primary_score * ratio
    ]

    # --- 六要素：以本体中该 scene 的定义为准（有依据，非自由联想）---
    actors = list(spec.get("actors", []))
    conflict = list(spec.get("conflict", []))
    choices = list(spec.get("choices", []))
    concepts = list(spec.get("concepts", []))

    # 情绪：先取文本中实测到的标记，再并入该 scene 的默认情绪（去重保序）
    detected_emotions, matched_emotion_words = _detect_emotions(normalized, ontology)
    emotion = list(detected_emotions)
    for item in spec.get("emotion", []):
        if item not in emotion:
            emotion.append(item)

    # --- 可审计的命中记录 ---
    matched_rules: List[str] = []
    for name, _ in ranked:
        for hit in hits_by_scene.get(name, []):
            matched_rules.append(f"scene:{name}:trigger:{hit}")
    for word in matched_emotion_words:
        matched_rules.append(f"emotion:{ontology['emotion_markers'][word]}:marker:{word}")

    return IssueStructure(
        query=original,
        normalized_query=normalized,
        scene=primary_scene,
        secondary_scenes=secondary,
        actors=actors,
        conflict=conflict,
        emotion=emotion,
        choices=choices,
        concepts=concepts,
        confidence=round(confidence, 4),
        matched_rules=matched_rules,
        scores={name: round(value, 4) for name, value in ranked},
        needs_clarification=confidence < LOW_CONFIDENCE_THRESHOLD,
        ontology_version=version,
    )


def structure_to_dict(query: str) -> Dict[str, Any]:
    """便捷函数：返回可直接 JSON 序列化的 dict（供 API / Eval 使用）。"""
    return structure(query).model_dump()


def available_scenes() -> List[str]:
    """返回本体中实际定义的情境列表（用于测试与文档核对）。"""
    return sorted(_load_ontology()["scenes"].keys())


def ontology_version() -> str:
    """返回本体版本号。"""
    return str(_load_ontology().get("ontology_version", "unknown"))


def clear_cache() -> None:
    """清除本体缓存（测试用；生产路径无需调用）。"""
    _load_ontology.cache_clear()


__all__ = [
    "OntologyError",
    "available_scenes",
    "clear_cache",
    "normalize",
    "ontology_version",
    "structure",
    "structure_to_dict",
]
