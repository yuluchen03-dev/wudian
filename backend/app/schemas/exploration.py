"""
悟典 - 互动探索层数据模型
知识图谱、思想时间线、典故溯源的 Pydantic Schema 定义
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ========== 知识图谱 ==========

class GraphNode(BaseModel):
    """图节点"""
    id: str = Field(..., description="节点唯一标识")
    label: str = Field(..., description="显示名称")
    type: str = Field(..., description="节点类型: person / concept")
    subtype: Optional[str] = Field(None, description="子类型: sage / disciple / lineage")
    courtesy_name: Optional[str] = Field(None, description="字号")
    real_name: Optional[str] = Field(None, description="本名")
    birth_year: Optional[int] = Field(None, description="出生年份（公元前为负数）")
    death_year: Optional[int] = Field(None, description="逝世年份（公元前为负数）")
    era: Optional[str] = Field(None, description="时代")
    description: Optional[str] = Field(None, description="简介")
    core_thought: Optional[str] = Field(None, description="核心思想")
    tags: List[str] = Field(default_factory=list, description="标签")


class GraphEdge(BaseModel):
    """图边"""
    source: str = Field(..., description="起点节点 ID")
    target: str = Field(..., description="终点节点 ID")
    relation: str = Field(..., description="关系类型: 师生 / 师承 / 提出 / 阐发 / 包含 / 发展")
    label: Optional[str] = Field(None, description="关系标签")
    description: Optional[str] = Field(None, description="关系描述")


class GraphData(BaseModel):
    """完整图数据"""
    nodes: List[GraphNode] = Field(..., description="节点列表")
    edges: List[GraphEdge] = Field(..., description="边列表")


class GraphResponse(BaseModel):
    """图数据响应"""
    type: str = Field(..., description="图类型: disciples / lineage / all")
    total_nodes: int = Field(..., description="节点总数")
    total_edges: int = Field(..., description="边总数")
    graph: GraphData = Field(..., description="图数据")


# ========== 时间线 ==========

class TimelineEvent(BaseModel):
    """时间线事件"""
    id: str = Field(..., description="事件唯一标识")
    year: int = Field(..., description="年份（公元前为负数）")
    year_label: str = Field(..., description="年份显示文本")
    title: str = Field(..., description="事件标题")
    category: str = Field(..., description="类别: history / person / classic")
    description: str = Field(..., description="事件描述")
    tags: List[str] = Field(default_factory=list, description="标签")


class TimelineResponse(BaseModel):
    """时间线响应"""
    total: int = Field(..., description="事件总数")
    categories: List[str] = Field(..., description="可用类别列表")
    events: List[TimelineEvent] = Field(..., description="事件列表")


# ========== 典故溯源 ==========

class Idiom(BaseModel):
    """成语典故"""
    idiom: str = Field(..., description="成语")
    original_text: str = Field(..., description="经典原句")
    source: str = Field(..., description="出处，如：论语·学而")
    chapter: str = Field(..., description="篇章全称，如：学而第一")
    chapter_num: int = Field(..., description="篇章序号")
    verse_num: int = Field(..., description="章句序号")
    meaning: str = Field(..., description="释义")
    modern_usage: str = Field(..., description="现代用法示例")
    tags: List[str] = Field(default_factory=list, description="标签")


class IdiomListResponse(BaseModel):
    """成语列表响应"""
    total: int = Field(..., description="成语总数")
    idioms: List[Idiom] = Field(..., description="成语列表")


class IdiomDetailResponse(Idiom):
    """成语详情响应（继承 Idiom 并可扩展）"""
    pass
