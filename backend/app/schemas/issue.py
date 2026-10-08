"""
悟典 - Modern Issue Ontology 结构化结果模型（PHASE 3 / P3-01）

设计依据
--------
- PROJECT-BRIEF 第七章：现代问题结构化。必须覆盖 21 类情境；用户输入
  「不能直接丢给 embedding」，须先转换为 scene / actors / conflict /
  emotion / choices / concepts。
- ``docs/kb-v1/02-architecture.md`` §3.2（PHASE 3 模块清单）、§2（数据流 Stage 1/2）。
- ``docs/kb-v1/01-gap-analysis.md`` §1.4（第七章当前 0 实现）。

本模块只描述**结构化结果**，不含任何 LLM 调用或网络访问。
数据源为 ``data/processed/modern_issue_ontology.json``（受控词表 + 触发词）。

与既有模块的关系
----------------
``backend/app/schemas/knowledge.py`` 中 ``Passage.concepts`` / ``modern_scenarios``
的注释写明「受控词表见 PHASE 3」。本模块的 :data:`SCENES` 与 ontology 的
``controlled_vocabularies`` 即为该受控词表的定义来源。
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============================================================
# 受控词表（与 modern_issue_ontology.json 保持一致）
# ============================================================

#: PROJECT-BRIEF 第七章列出的 21 类现代情境（冻结，不可增删而不改 brief）
SCENES: tuple[str, ...] = (
    "career",
    "workplace_conflict",
    "leadership",
    "achievement",
    "money",
    "competition",
    "family",
    "parent_child",
    "marriage",
    "friendship",
    "anxiety",
    "failure",
    "anger",
    "loneliness",
    "self_doubt",
    "choice",
    "responsibility",
    "justice",
    "fairness",
    "meaning",
    "ambition",
)

SCENE_SET = frozenset(SCENES)

#: 置信度低于该值时，结构化结果视为「不确定」，下游不得据此强行检索。
LOW_CONFIDENCE_THRESHOLD: float = 0.4


class IssueStructure(BaseModel):
    """现代问题的结构化结果。

    语义约定
    --------
    - ``scene is None`` 且 ``confidence == 0.0``：**无法归类**。这不是错误，
      而是明确表示「本体中没有匹配项」，下游必须降级（不得硬编归类）。
    - ``needs_clarification=True``：命中但置信度不足（< 0.4），下游应提示
      用户补充信息，而不是把低置信度结果当作事实使用。
    - ``concepts`` 只能取自 ontology 的受控概念表；空列表表示未映射，
      不得用占位概念填充。
    """

    model_config = ConfigDict(extra="forbid")

    # --- 原始输入 ---
    query: str = Field(..., description="归一化前的原始用户输入")
    normalized_query: str = Field(
        ..., description="归一化后的输入（去空白 + 小写），用于复现匹配过程",
    )

    # --- 结构化六要素（PROJECT-BRIEF 第七章）---
    scene: Optional[str] = Field(
        None, description="主情境，取自 21 类受控词表；无法归类时为 None",
    )
    secondary_scenes: List[str] = Field(
        default_factory=list, description="次要情境（得分达到主情境一定比例）",
    )
    actors: List[str] = Field(default_factory=list, description="涉及的行动者")
    conflict: List[str] = Field(default_factory=list, description="核心冲突维度")
    emotion: List[str] = Field(default_factory=list, description="情绪")
    choices: List[str] = Field(default_factory=list, description="可选行动")
    concepts: List[str] = Field(
        default_factory=list,
        description="映射到的中国思想概念（受控词表，有本体依据）",
    )

    # --- 判定元信息 ---
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="置信度 0–1；0.0 表示无法归类",
    )
    matched_rules: List[str] = Field(
        default_factory=list,
        description="命中的确定性规则（触发词 / 情绪标记），用于可复现审计",
    )
    scores: Dict[str, float] = Field(
        default_factory=dict, description="各 scene 的原始得分，便于调试与复核",
    )
    needs_clarification: bool = Field(
        False,
        description="置信度不足（< LOW_CONFIDENCE_THRESHOLD）时为 True",
    )
    ontology_version: str = Field(
        ..., description="所用本体版本，保证结果可追溯",
    )

    @field_validator("scene")
    @classmethod
    def _scene_in_vocabulary(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in SCENE_SET:
            raise ValueError(
                f"scene {value!r} 不在 PROJECT-BRIEF 第七章的 21 类受控词表中",
            )
        return value

    @field_validator("secondary_scenes")
    @classmethod
    def _secondary_in_vocabulary(cls, value: List[str]) -> List[str]:
        invalid = [item for item in value if item not in SCENE_SET]
        if invalid:
            raise ValueError(f"secondary_scenes 含非法情境: {invalid}")
        return value


class IssueStructureRequest(BaseModel):
    """结构化的请求模型（供后续 API 复用；PHASE 3 不注册路由）。"""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=1, description="现代现实问题原文")
