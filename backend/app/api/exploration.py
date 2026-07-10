"""
悟典 - 互动探索 API 路由
知识图谱、思想时间线、典故溯源
"""
from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException

from app.services import knowledge_graph, timeline_service, idiom_service
from app.schemas.exploration import (
    GraphResponse,
    GraphData,
    GraphNode,
    GraphEdge,
    TimelineResponse,
    TimelineEvent,
    IdiomListResponse,
    IdiomDetailResponse,
)

router = APIRouter(prefix="/api/exploration", tags=["探索"])


# ========== 知识图谱 ==========

@router.get("/graph", response_model=GraphResponse, summary="获取知识图谱数据")
async def get_graph(
    type: str = Query("all", description="图类型: disciples(弟子关系图) / lineage(思想传承图) / all(完整图谱)"),
):
    """
    获取知识图谱数据

    - **disciples**: 孔门弟子关系图（孔子与直传弟子）
    - **lineage**: 儒家思想传承脉络图（孔子→曾子→子思→孟子→荀子→...）
    - **all**: 完整知识图谱（人物+概念+关系）
    """
    graph_data = knowledge_graph.get_graph_by_type(type)

    nodes = [GraphNode(**n) for n in graph_data["nodes"]]
    edges = [GraphEdge(**e) for e in graph_data["edges"]]
    graph = GraphData(nodes=nodes, edges=edges)

    return GraphResponse(
        type=type,
        total_nodes=len(nodes),
        total_edges=len(edges),
        graph=graph,
    )


@router.get("/graph/node/{node_id}", summary="获取节点详情")
async def get_node_detail(node_id: str):
    """获取知识图谱中某个节点的详情，包括关联节点和关系"""
    detail = knowledge_graph.get_node_detail(node_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
    return detail


# ========== 时间线 ==========

@router.get("/timeline", response_model=TimelineResponse, summary="获取思想时间线数据")
async def get_timeline(
    category: Optional[str] = Query(None, description="筛选类别: history / person / classic，多个用逗号分隔"),
    start_year: Optional[int] = Query(None, description="起始年份（公元前为负数）"),
    end_year: Optional[int] = Query(None, description="结束年份（公元前为负数）"),
):
    """
    获取思想时间线数据

    包含春秋战国历史事件、孔子生平大事记、经典成书时间线。
    可按类别和年份范围筛选。
    """
    categories = None
    if category:
        categories = [c.strip() for c in category.split(",") if c.strip()]

    data = timeline_service.get_timeline_data(
        categories=categories,
        start_year=start_year,
        end_year=end_year,
    )

    events = [TimelineEvent(**e) for e in data["events"]]

    return TimelineResponse(
        total=data["total"],
        categories=data["categories"],
        events=events,
    )


@router.get("/timeline/search", summary="搜索时间线事件")
async def search_timeline(
    q: str = Query(..., description="搜索关键词"),
):
    """关键词搜索时间线事件"""
    results = timeline_service.search_events(q)
    return {"total": len(results), "events": results}


# ========== 典故溯源 ==========

@router.get("/idioms", response_model=IdiomListResponse, summary="获取成语列表")
async def get_idioms(
    tag: Optional[str] = Query(None, description="按标签筛选"),
    chapter: Optional[int] = Query(None, description="按篇章序号筛选(1-20)"),
):
    """
    获取源自论语的成语列表

    可按标签或篇章筛选。每条成语包含出处、原文、释义、现代用法。
    """
    if tag:
        idioms = idiom_service.get_idioms_by_tag(tag)
    elif chapter is not None:
        idioms = idiom_service.get_idioms_by_chapter(chapter)
    else:
        idioms = idiom_service.get_all_idioms()

    return IdiomListResponse(
        total=len(idioms),
        idioms=idioms,
    )


@router.get("/idiom/{idiom}", response_model=IdiomDetailResponse, summary="获取成语溯源详情")
async def get_idiom_detail(idiom: str):
    """
    获取单个成语的溯源详情

    返回成语的出处篇章、原文、释义、现代用法示例。
    """
    detail = idiom_service.get_idiom_detail(idiom)
    if not detail:
        raise HTTPException(status_code=404, detail=f"未找到成语「{idiom}」的溯源信息")
    return IdiomDetailResponse(**detail)


@router.get("/idioms/search", summary="搜索成语")
async def search_idioms(
    q: str = Query(..., description="搜索关键词"),
):
    """关键词搜索成语（在成语、原文、释义、标签中搜索）"""
    results = idiom_service.search_idioms(q)
    return {"total": len(results), "idioms": results}


@router.get("/idioms/tags", summary="获取所有成语标签")
async def get_idiom_tags():
    """获取所有成语标签，用于前端筛选"""
    tags = idiom_service.get_all_tags()
    return {"tags": tags}
