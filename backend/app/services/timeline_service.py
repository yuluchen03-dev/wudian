"""
悟典 - 思想时间线服务
春秋战国历史事件、孔子生平大事记、经典成书时间线
将论语章句放入历史背景
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

# 数据文件路径
_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed"
_TIMELINE_FILE = _DATA_DIR / "timeline.json"

# 时间线数据缓存
_timeline_cache: Optional[Dict] = None

# 类别中文映射
CATEGORY_LABELS = {
    "history": "历史事件",
    "person": "人物生平",
    "classic": "经典成书",
}


def _load_timeline_data() -> Dict:
    """加载时间线原始数据（带缓存）"""
    global _timeline_cache
    if _timeline_cache is None:
        with open(_TIMELINE_FILE, "r", encoding="utf-8") as f:
            _timeline_cache = json.load(f)
    return _timeline_cache


def get_all_events() -> List[Dict]:
    """获取所有时间线事件（按年份排序）"""
    data = _load_timeline_data()
    events = data["events"]
    return sorted(events, key=lambda e: e["year"])


def get_events_by_category(category: str) -> List[Dict]:
    """
    按类别获取事件
    :param category: history / person / classic
    """
    events = get_all_events()
    return [e for e in events if e["category"] == category]


def get_events_filtered(
    categories: Optional[List[str]] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> List[Dict]:
    """
    筛选时间线事件
    :param categories: 类别列表，None 表示全部
    :param start_year: 起始年份
    :param end_year: 结束年份
    """
    events = get_all_events()

    if categories:
        events = [e for e in events if e["category"] in categories]

    if start_year is not None:
        events = [e for e in events if e["year"] >= start_year]

    if end_year is not None:
        events = [e for e in events if e["year"] <= end_year]

    return events


def get_timeline_data(
    categories: Optional[List[str]] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict:
    """
    获取时间线数据
    :return: dict 包含 total, categories, events
    """
    events = get_events_filtered(categories, start_year, end_year)

    all_categories = list(CATEGORY_LABELS.keys())

    return {
        "total": len(events),
        "categories": all_categories,
        "category_labels": CATEGORY_LABELS,
        "events": events,
    }


def get_event_by_id(event_id: str) -> Optional[Dict]:
    """根据 ID 获取单个事件"""
    events = get_all_events()
    return next((e for e in events if e["id"] == event_id), None)


def get_confucius_timeline() -> List[Dict]:
    """获取孔子生平时间线"""
    return get_events_by_category("person")


def search_events(keyword: str) -> List[Dict]:
    """关键词搜索事件"""
    events = get_all_events()
    keyword_lower = keyword.lower()
    results = []
    for e in events:
        if (keyword_lower in e["title"].lower() or
            keyword_lower in e["description"].lower() or
            any(keyword_lower in tag.lower() for tag in e.get("tags", []))):
            results.append(e)
    return results
