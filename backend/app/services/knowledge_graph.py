"""
悟典 - 知识图谱服务
构建孔门弟子关系图、儒家思想传承脉络、典故出处网络
提供图数据接口（nodes + edges）
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

# 数据文件路径
_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed"
_GRAPH_FILE = _DATA_DIR / "knowledge_graph.json"

# 图数据缓存
_graph_cache: Optional[Dict] = None


def _load_graph_data() -> Dict:
    """加载知识图谱原始数据（带缓存）"""
    global _graph_cache
    if _graph_cache is None:
        with open(_GRAPH_FILE, "r", encoding="utf-8") as f:
            _graph_cache = json.load(f)
    return _graph_cache


def _filter_nodes_by_type(nodes: List[Dict], subtypes: Set[str]) -> List[Dict]:
    """按子类型筛选节点"""
    return [n for n in nodes if n.get("subtype") in subtypes or n.get("type") == "concept"]


def get_disciples_graph() -> Dict:
    """
    获取孔门弟子关系图
    包含孔子及其直传弟子，以及他们之间的关系
    """
    data = _load_graph_data()
    all_nodes = data["nodes"]
    all_edges = data["edges"]

    # 弟子关系图包含：孔子（sage）+ 所有弟子（disciple）+ 相关概念
    disciple_subtypes = {"sage", "disciple"}
    node_ids = {n["id"] for n in all_nodes if n.get("subtype") in disciple_subtypes}

    # 也包含与孔子有直接关系的概念节点
    concept_edges = [e for e in all_edges if e["source"] == "confucius" and e["relation"] == "提出"]
    for e in concept_edges:
        node_ids.add(e["target"])

    nodes = [n for n in all_nodes if n["id"] in node_ids]
    edges = [e for e in all_edges if e["source"] in node_ids and e["target"] in node_ids]

    return {"nodes": nodes, "edges": edges}


def get_lineage_graph() -> Dict:
    """
    获取儒家思想传承脉络图
    包含从孔子到后世大儒的师承关系链
    """
    data = _load_graph_data()
    all_nodes = data["nodes"]
    all_edges = data["edges"]

    # 传承图包含：sage + disciple + lineage 类型的人物
    lineage_subtypes = {"sage", "disciple", "lineage"}
    node_ids = {n["id"] for n in all_nodes if n.get("subtype") in lineage_subtypes}

    # 也包含相关的概念节点
    concept_ids = set()
    for e in all_edges:
        if e["source"] in node_ids and e["target"] not in node_ids:
            target_node = next((n for n in all_nodes if n["id"] == e["target"]), None)
            if target_node and target_node.get("type") == "concept":
                concept_ids.add(e["target"])
        if e["target"] in node_ids and e["source"] not in node_ids:
            source_node = next((n for n in all_nodes if n["id"] == e["source"]), None)
            if source_node and source_node.get("type") == "concept":
                concept_ids.add(e["source"])

    node_ids = node_ids | concept_ids

    nodes = [n for n in all_nodes if n["id"] in node_ids]
    edges = [e for e in all_edges if e["source"] in node_ids and e["target"] in node_ids]

    return {"nodes": nodes, "edges": edges}


def get_full_graph() -> Dict:
    """
    获取完整知识图谱
    包含所有人物、概念节点及其关系
    """
    data = _load_graph_data()
    return {"nodes": data["nodes"], "edges": data["edges"]}


def get_graph_by_type(graph_type: str = "all") -> Dict:
    """
    根据类型获取图数据
    :param graph_type: disciples / lineage / all
    :return: 图数据 dict，包含 nodes 和 edges
    """
    if graph_type == "disciples":
        return get_disciples_graph()
    elif graph_type == "lineage":
        return get_lineage_graph()
    else:
        return get_full_graph()


def get_node_detail(node_id: str) -> Optional[Dict]:
    """
    获取节点详情（含关联节点和关系）
    """
    data = _load_graph_data()
    node = next((n for n in data["nodes"] if n["id"] == node_id), None)
    if not node:
        return None

    # 获取相关边
    related_edges = [e for e in data["edges"] if e["source"] == node_id or e["target"] == node_id]

    # 获取关联节点
    related_node_ids = set()
    for e in related_edges:
        related_node_ids.add(e["source"])
        related_node_ids.add(e["target"])
    related_node_ids.discard(node_id)

    related_nodes = [n for n in data["nodes"] if n["id"] in related_node_ids]

    return {
        "node": node,
        "related_edges": related_edges,
        "related_nodes": related_nodes,
    }
