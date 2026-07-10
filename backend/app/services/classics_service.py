"""
悟典 - 经典内容服务
从 data/processed/ 下的 JSON 文件读取经典内容，不依赖数据库。

数据来源：
- data/processed/lunyu.json        论语全文（章节 + 句子 + 注释）
- data/processed/lunyu_quotes.json 论语名句精选（用于每日一句）

实体百科数据内置在代码中（来源于前端 mockData），后续可迁移到 JSON 文件。
"""
import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================================
# 路径 & 缓存
# ============================================================

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed"
_CATALOG_FILE = _DATA_DIR / "classics_catalog.json"
_LUNYU_FILE = _DATA_DIR / "lunyu.json"
_QUOTES_FILE = _DATA_DIR / "lunyu_quotes.json"

# 数据缓存（进程级）
_lunyu_cache: Optional[Dict] = None
_quotes_cache: Optional[List[Dict]] = None
_books_meta_cache: Optional[Dict[str, Dict]] = None


# ============================================================
# 书籍元信息（内置，后续可扩展为 JSON 文件）
# ============================================================

_BOOKS_META: Dict[str, Dict] = {
    "lunyu": {
        "id": "lunyu",
        "title": "论语",
        "category": "四书",
        "author": "孔子弟子及再传弟子",
        "dynasty": "春秋",
        "description": "记录孔子及其弟子言行的语录体散文集，儒家核心经典。",
        "coverColor": "#b91c1c",
    },
    "mengzi": {
        "id": "mengzi",
        "title": "孟子",
        "category": "四书",
        "author": "孟子及其弟子",
        "dynasty": "战国",
        "description": "记录孟子治国思想、仁政学说的儒家经典。",
        "coverColor": "#8a8050",
    },
    "daxue": {
        "id": "daxue",
        "title": "大学",
        "category": "四书",
        "author": "曾子",
        "dynasty": "战国",
        "description": "论述修身齐家治国平天下之道的儒家经典。",
        "coverColor": "#1c1917",
    },
    "zhongyong": {
        "id": "zhongyong",
        "title": "中庸",
        "category": "四书",
        "author": "子思",
        "dynasty": "战国",
        "description": "阐述「中庸」之道，讲究不偏不倚、执两用中的哲学。",
        "coverColor": "#6b4f30",
    },
}


# ============================================================
# 实体百科（内置，来源于前端 mockData.ts）
# ============================================================

_ENTITIES: Dict[str, Dict] = {
    "confucius": {
        "id": "confucius",
        "name": "孔子",
        "type": "人名",
        "description": "名丘，字仲尼，春秋末期鲁国人，儒家学派创始人，被尊为「至圣先师」。生于公元前551年，卒于公元前479年。",
        "relatedText": "子曰",
    },
    "youzi": {
        "id": "youzi",
        "name": "有子",
        "type": "人名",
        "description": "即有若，孔子弟子，字子有，少孔子四十三岁。在孔门中以学问著称，言貌类孔子。",
    },
    "zengzi": {
        "id": "zengzi",
        "name": "曾子",
        "type": "人名",
        "description": "即曾参，孔子弟子，字子舆，以孝道闻名，作《大学》，被尊为「宗圣」。",
    },
    "zixia": {
        "id": "zixia",
        "name": "子夏",
        "type": "人名",
        "description": "即卜商，孔子弟子，字子夏，擅长文学，为孔门十哲之一。",
    },
    "luzhou": {
        "id": "luzhou",
        "name": "鲁国",
        "type": "地名",
        "description": "周朝诸侯国，姬姓，都城曲阜，为周公旦封地。孔子出生与活动的主要区域。",
    },
    "junzi": {
        "id": "junzi",
        "name": "君子",
        "type": "概念",
        "description": "儒家理想人格，指有道德修养、行仁义之人。「君子务本，本立而道生。」",
    },
    "dao": {
        "id": "dao",
        "name": "道",
        "type": "概念",
        "description": "儒家核心范畴，指正确的政治主张、道德原则与人生理想。朝闻道，夕死可矣。",
    },
    "ren": {
        "id": "ren",
        "name": "仁",
        "type": "概念",
        "description": "儒家最高道德准则，指人与人之间的相亲相爱。樊迟问仁，子曰：「爱人。」",
    },
    "xiao": {
        "id": "xiao",
        "name": "孝",
        "type": "概念",
        "description": "儒家伦理核心，指子女对父母的敬爱与奉养。孝悌也者，其为仁之本与。",
    },
}


# ============================================================
# 数据加载
# ============================================================

def _load_lunyu() -> Dict:
    """加载论语 JSON 数据（带缓存）"""
    global _lunyu_cache
    if _lunyu_cache is None:
        try:
            with open(_LUNYU_FILE, "r", encoding="utf-8") as f:
                _lunyu_cache = json.load(f)
        except FileNotFoundError:
            logger.error("论语数据文件不存在: %s", _LUNYU_FILE)
            _lunyu_cache = {"chapters": []}
        except json.JSONDecodeError as e:
            logger.error("论语数据文件解析失败: %s", e)
            _lunyu_cache = {"chapters": []}
    return _lunyu_cache


def _load_quotes() -> List[Dict]:
    """加载名句精选 JSON 数据（带缓存）"""
    global _quotes_cache
    if _quotes_cache is None:
        try:
            with open(_QUOTES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _quotes_cache = data.get("quotes", [])
        except FileNotFoundError:
            logger.error("名句数据文件不存在: %s", _QUOTES_FILE)
            _quotes_cache = []
        except json.JSONDecodeError as e:
            logger.error("名句数据文件解析失败: %s", e)
            _quotes_cache = []
    return _quotes_cache


def _load_books_meta() -> Dict[str, Dict]:
    """Load catalog metadata from data/processed/classics_catalog.json."""
    global _books_meta_cache
    if _books_meta_cache is not None:
        return _books_meta_cache

    try:
        with open(_CATALOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        books = data.get("books", [])
        _books_meta_cache = {book["id"]: book for book in books if book.get("id")}
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("classics catalog load failed, using built-in fallback: %s", e)
        _books_meta_cache = _BOOKS_META

    return _books_meta_cache


# ============================================================
# 数据转换工具
# ============================================================

def _parse_annotation(ann: Dict) -> Dict:
    """将 JSON 中的注释对象转换为前端格式"""
    meaning: str = ann.get("meaning", "")
    is_tongjia = "同「" in meaning or "同\"" in meaning
    tongjia_origin = None
    if is_tongjia:
        # 从 "同「悦」，愉快" 中提取本字
        start = meaning.find("同「")
        if start != -1:
            end = meaning.find("」", start)
            if end != -1:
                tongjia_origin = meaning[start + 2: end]
        else:
            start = meaning.find("同\"")
            if start != -1:
                end = meaning.find("\"", start + 2)
                if end != -1:
                    tongjia_origin = meaning[start + 2: end]

    return {
        "char": ann.get("char", ""),
        "pinyin": ann.get("pinyin", ""),
        "meaning": meaning,
        "isTongjia": is_tongjia if is_tongjia else None,
        "tongjiaOrigin": tongjia_origin,
    }


def _verse_to_sentence(verse: Dict, book_id: str, chapter_order: int) -> Dict:
    """将 JSON 中的 verse 转换为前端 SentencePair 格式"""
    verse_id: str = verse.get("verse_id", f"{chapter_order}.?")
    sentence_id = verse_id.replace(".", "-")  # "1.1" -> "1-1"

    # 简单的实体关联推断：根据原文中出现的实体名称
    original = verse.get("original", "")
    entity_ids = []
    for eid, einfo in _ENTITIES.items():
        if einfo["name"] in original:
            entity_ids.append(eid)

    return {
        "id": sentence_id,
        "original": original,
        "translation": verse.get("translation", ""),
        "annotations": [_parse_annotation(a) for a in verse.get("annotations", [])],
        "entityIds": entity_ids,
        "title": verse.get("title"),
        "keywords": verse.get("keywords", []),
    }


def _chapter_id(book_id: str, chapter_order: int) -> str:
    """生成章节 ID，如 'lunyu-1'"""
    return f"{book_id}-{chapter_order}"


# ============================================================
# 公开查询方法
# ============================================================

def get_books() -> List[Dict]:
    """获取所有经典书目列表"""
    books = []
    for book_id, meta in _load_books_meta().items():
        total_chapters = _get_book_total_chapters(book_id)
        books.append({
            "id": meta["id"],
            "title": meta["title"],
            "category": meta["category"],
            "author": meta.get("author"),
            "dynasty": meta.get("dynasty"),
            "description": meta["description"],
            "coverColor": meta["coverColor"],
            "totalChapters": total_chapters,
        })
    return books


def get_book(book_id: str) -> Optional[Dict]:
    """获取单本书信息"""
    meta = _load_books_meta().get(book_id)
    if meta is None:
        return None
    total_chapters = _get_book_total_chapters(book_id)
    return {
        "id": meta["id"],
        "title": meta["title"],
        "category": meta["category"],
        "author": meta.get("author"),
        "dynasty": meta.get("dynasty"),
        "description": meta["description"],
        "coverColor": meta["coverColor"],
        "totalChapters": total_chapters,
    }


def _get_book_total_chapters(book_id: str) -> int:
    """获取书籍总章节数"""
    if book_id == "lunyu":
        data = _load_lunyu()
        return data.get("total_chapters", len(data.get("chapters", [])))
    else:
        return _load_books_meta().get(book_id, {}).get("totalChapters", 0)


def get_chapters(book_id: str) -> List[Dict]:
    """获取指定书籍的章节列表（简要信息，不含句子）"""
    if book_id != "lunyu":
        return []

    data = _load_lunyu()
    chapters = []
    for ch in data.get("chapters", []):
        order = ch.get("chapter_id", 0)
        verses = ch.get("verses", [])
        chapters.append({
            "id": _chapter_id(book_id, order),
            "bookId": book_id,
            "order": order,
            "title": f"{ch.get('chapter_title', '')}第{_cn_num(order)}",
            "summary": ch.get("summary"),
            "sentenceCount": len(verses),
        })
    return chapters


def get_chapter(chapter_id: str) -> Optional[Dict]:
    """获取章节详情（含句子）"""
    data = _load_lunyu()

    # chapter_id 格式: "lunyu-1"
    parts = chapter_id.rsplit("-", 1)
    if len(parts) != 2:
        return None
    book_id = parts[0]
    try:
        order = int(parts[1])
    except ValueError:
        return None

    if book_id != "lunyu":
        return None

    for ch in data.get("chapters", []):
        if ch.get("chapter_id") == order:
            sentences = [
                _verse_to_sentence(v, book_id, order)
                for v in ch.get("verses", [])
            ]
            return {
                "id": chapter_id,
                "bookId": book_id,
                "order": order,
                "title": f"{ch.get('chapter_title', '')}第{_cn_num(order)}",
                "summary": ch.get("summary"),
                "sentences": sentences,
            }
    return None


def get_verse(verse_id: str) -> Optional[Dict]:
    """
    获取单句详情

    :param verse_id: 句子 ID，格式 "1-1"（对应 verse_id "1.1"）
    """
    parts = verse_id.split("-")
    if len(parts) != 2:
        return None
    try:
        chapter_order = int(parts[0])
    except ValueError:
        return None

    chapter = get_chapter(_chapter_id("lunyu", chapter_order))
    if chapter is None:
        return None

    for sentence in chapter["sentences"]:
        if sentence["id"] == verse_id:
            return sentence
    return None


def get_entity(entity_id: str) -> Optional[Dict]:
    """获取实体百科详情"""
    return _ENTITIES.get(entity_id)


def get_all_entities() -> List[Dict]:
    """获取所有实体（列表）"""
    return list(_ENTITIES.values())


def get_daily_quote() -> Optional[Dict]:
    """
    获取每日一句
    根据当天日期从名句精选中选取一句，每天固定不变
    """
    quotes = _load_quotes()
    if not quotes:
        return None

    # 用日期作为种子选取，保证同一天返回相同结果
    today = date.today()
    day_index = today.toordinal() % len(quotes)
    q = quotes[day_index]

    # 解析 source 格式 "学而第一·1" -> chapterId
    source = q.get("source", "")
    chapter_id = _parse_source_to_chapter_id(source)

    return {
        "id": q.get("id", f"dq-{day_index}"),
        "text": q.get("original", ""),
        "translation": q.get("translation", ""),
        "source": f"论语·{source}" if source else "论语",
        "chapterId": chapter_id,
    }


# ============================================================
# 辅助函数
# ============================================================

_CN_NUMS = "零一二三四五六七八九十"


def _cn_num(n: int) -> str:
    """将 1-20 的数字转换为中文，如 1 -> '一', 10 -> '十', 11 -> '十一'"""
    if n <= 0:
        return str(n)
    if n <= 10:
        return _CN_NUMS[n]
    if n < 20:
        return "十" + _CN_NUMS[n - 10]
    if n == 20:
        return "二十"
    if n < 30:
        return "二十" + _CN_NUMS[n - 20]
    return str(n)


def _parse_source_to_chapter_id(source: str) -> str:
    """从 source 字段解析章节 ID

    例: "学而第一·1" -> "lunyu-1"
        "为政第二·3" -> "lunyu-2"
    """
    # 章节名 -> 章序号 映射（论语20篇）
    chapter_names = [
        "学而", "为政", "八佾", "里仁", "公冶长",
        "雍也", "述而", "泰伯", "子罕", "乡党",
        "先进", "颜渊", "子路", "宪问", "卫灵公",
        "季氏", "阳货", "微子", "子张", "尧曰",
    ]
    for i, name in enumerate(chapter_names, start=1):
        if source.startswith(name):
            return _chapter_id("lunyu", i)
    return _chapter_id("lunyu", 1)
