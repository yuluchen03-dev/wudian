"""
悟典 - 典故溯源服务
成语/俗语 → 经典原句的映射
返回出处、原文、释义、演变
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

# 数据文件路径
_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed"
_IDIOMS_FILE = _DATA_DIR / "idioms.json"

# 典故数据缓存
_idioms_cache: Optional[Dict] = None


def _load_idioms_data() -> Dict:
    """加载典故原始数据（带缓存）"""
    global _idioms_cache
    if _idioms_cache is None:
        with open(_IDIOMS_FILE, "r", encoding="utf-8") as f:
            _idioms_cache = json.load(f)
    return _idioms_cache


def get_all_idioms() -> List[Dict]:
    """获取所有成语列表"""
    data = _load_idioms_data()
    return data["idioms"]


def get_idiom_list() -> Dict:
    """
    获取成语列表（摘要信息）
    :return: dict 包含 total 和 idioms
    """
    idioms = get_all_idioms()
    return {
        "total": len(idioms),
        "idioms": idioms,
    }


def get_idiom_detail(idiom: str) -> Optional[Dict]:
    """
    获取单个成语的溯源详情
    :param idiom: 成语名称
    :return: 成语详情 dict 或 None
    """
    idioms = get_all_idioms()
    # 精确匹配优先
    result = next((i for i in idioms if i["idiom"] == idiom), None)
    if result:
        return result

    # 模糊匹配（包含关系）
    result = next((i for i in idioms if idiom in i["idiom"] or i["idiom"] in idiom), None)
    return result


def search_idioms(keyword: str) -> List[Dict]:
    """
    关键词搜索成语
    在成语、原文、释义、标签中搜索
    """
    idioms = get_all_idioms()
    keyword_lower = keyword.lower()
    results = []
    for i in idioms:
        if (keyword_lower in i["idiom"].lower() or
            keyword_lower in i["original_text"].lower() or
            keyword_lower in i["meaning"].lower() or
            keyword_lower in i["source"].lower() or
            any(keyword_lower in tag.lower() for tag in i.get("tags", []))):
            results.append(i)
    return results


def get_idioms_by_chapter(chapter_num: int) -> List[Dict]:
    """
    按篇章获取成语
    :param chapter_num: 篇章序号（1-20）
    """
    idioms = get_all_idioms()
    return [i for i in idioms if i["chapter_num"] == chapter_num]


def get_idioms_by_tag(tag: str) -> List[Dict]:
    """按标签获取成语"""
    idioms = get_all_idioms()
    return [i for i in idioms if tag in i.get("tags", [])]


def get_all_tags() -> List[str]:
    """获取所有标签"""
    idioms = get_all_idioms()
    tags = set()
    for i in idioms:
        tags.update(i.get("tags", []))
    return sorted(tags)
