"""
悟典 - 趣味内容服务
金句卡片、情景小剧场、漫画解读

数据来源：data/processed/ 目录下的 JSON 文件。
服务启动时加载到内存，支持分页查询与详情获取。
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from app.schemas.content import (
    CardStyle,
    ComicBrief,
    ComicCharacter,
    ComicDetail,
    ComicListResponse,
    QuoteCardBrief,
    QuoteCardDetail,
    QuoteCardListResponse,
    TheaterBrief,
    TheaterDetail,
    TheaterLine,
    TheaterListResponse,
    TheaterRole,
    TheaterScene,
)

# 数据文件路径
_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"
_QUOTE_CARDS_FILE = _DATA_DIR / "quote_cards.json"
_THEATER_FILE = _DATA_DIR / "theater_scripts.json"
_COMICS_FILE = _DATA_DIR / "comics.json"


def _load_json(path: Path) -> list:
    """安全加载 JSON 文件"""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get("items", [])
    except (json.JSONDecodeError, OSError):
        return []


class ContentService:
    """趣味内容服务"""

    def __init__(self):
        self._quote_cards: List[dict] = []
        self._theaters: List[dict] = []
        self._comics: List[dict] = []
        self._loaded = False

    def _ensure_loaded(self):
        """懒加载数据"""
        if not self._loaded:
            self._quote_cards = _load_json(_QUOTE_CARDS_FILE)
            self._theaters = _load_json(_THEATER_FILE)
            self._comics = _load_json(_COMICS_FILE) or self._build_demo_comics()
            self._loaded = True

    # ---------- 金句卡片 ----------

    async def list_quote_cards(
        self, style: Optional[CardStyle] = None, page: int = 1, page_size: int = 20
    ) -> QuoteCardListResponse:
        """金句卡片列表"""
        self._ensure_loaded()
        items = self._quote_cards
        if style:
            items = [c for c in items if c.get("style") == style.value]

        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]

        briefs = [self._to_card_brief(c) for c in page_items]
        return QuoteCardListResponse(
            items=briefs, total=total, page=page, page_size=page_size
        )

    async def get_quote_card(self, card_id: str) -> QuoteCardDetail:
        """金句卡片详情"""
        self._ensure_loaded()
        for c in self._quote_cards:
            if c.get("id") == card_id:
                return self._to_card_detail(c)
        raise ValueError(f"金句卡片 {card_id} 不存在")

    async def like_quote_card(self, card_id: str) -> dict:
        """点赞金句卡片"""
        self._ensure_loaded()
        for c in self._quote_cards:
            if c.get("id") == card_id:
                c["like_count"] = c.get("like_count", 0) + 1
                return {"card_id": card_id, "like_count": c["like_count"]}
        raise ValueError(f"金句卡片 {card_id} 不存在")

    async def share_quote_card(self, card_id: str) -> dict:
        """记录分享次数"""
        self._ensure_loaded()
        for c in self._quote_cards:
            if c.get("id") == card_id:
                c["share_count"] = c.get("share_count", 0) + 1
                return {"card_id": card_id, "share_count": c["share_count"]}
        raise ValueError(f"金句卡片 {card_id} 不存在")

    def _to_card_brief(self, c: dict) -> QuoteCardBrief:
        return QuoteCardBrief(
            id=c["id"],
            quote=c["quote"],
            source=c["source"],
            style=CardStyle(c.get("style", "ink_wash")),
            image_keyword=c.get("image_keyword", ""),
            background_image=c.get("background_image", ""),
            like_count=c.get("like_count", 0),
            share_count=c.get("share_count", 0),
            created_at=c.get("created_at", "2024-01-01T00:00:00"),
        )

    def _to_card_detail(self, c: dict) -> QuoteCardDetail:
        brief = self._to_card_brief(c)
        return QuoteCardDetail(
            **brief.model_dump(),
            vernacular=c.get("vernacular", ""),
            modern_interpretation=c.get("modern_interpretation", ""),
            background_color=c.get("background_color", "#faf6ed"),
            accent_color=c.get("accent_color", "#b91c1c"),
            tags=c.get("tags", []),
            is_liked=False,
        )

    # ---------- 情景小剧场 ----------

    async def list_theaters(
        self, modern_setting: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> TheaterListResponse:
        """小剧场列表"""
        self._ensure_loaded()
        items = self._theaters
        if modern_setting:
            items = [t for t in items if t.get("modern_setting") == modern_setting]

        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]

        briefs = [self._to_theater_brief(t) for t in page_items]
        return TheaterListResponse(
            items=briefs, total=total, page=page, page_size=page_size
        )

    async def get_theater(self, theater_id: str) -> TheaterDetail:
        """小剧场详情"""
        self._ensure_loaded()
        for t in self._theaters:
            if t.get("id") == theater_id:
                return self._to_theater_detail(t)
        raise ValueError(f"小剧场 {theater_id} 不存在")

    def _to_theater_brief(self, t: dict) -> TheaterBrief:
        return TheaterBrief(
            id=t["id"],
            title=t["title"],
            summary=t.get("summary", ""),
            classical_source=t.get("classical_source", ""),
            modern_setting=t.get("modern_setting", ""),
            cover_keyword=t.get("cover_keyword", ""),
            scene_count=len(t.get("scenes", [])),
            like_count=t.get("like_count", 0),
            view_count=t.get("view_count", 0),
            created_at=t.get("created_at", "2024-01-01T00:00:00"),
        )

    def _to_theater_detail(self, t: dict) -> TheaterDetail:
        brief = self._to_theater_brief(t)
        roles = [
            TheaterRole(
                name=r.get("name", ""),
                description=r.get("description", ""),
                classical_origin=r.get("classical_origin"),
                avatar_keyword=r.get("avatar_keyword", ""),
                objective=r.get("objective", ""),
                fear=r.get("fear", ""),
                belief=r.get("belief", ""),
                strategy=r.get("strategy", ""),
                conflict_trigger=r.get("conflict_trigger", ""),
                stage_action=r.get("stage_action", ""),
            )
            for r in t.get("roles", [])
        ]
        scenes = [
            TheaterScene(
                title=s.get("title", ""),
                setting=s.get("setting", ""),
                lines=[
                    TheaterLine(
                        role=l.get("role", ""),
                        text=l.get("text", ""),
                        emotion=l.get("emotion"),
                        beat=l.get("beat", ""),
                        action=l.get("action", ""),
                        subtext=l.get("subtext", ""),
                        pressure=l.get("pressure", ""),
                        is_original_verse=l.get("is_original_verse", False),
                    )
                    for l in s.get("lines", [])
                ],
            )
            for s in t.get("scenes", [])
        ]
        return TheaterDetail(
            **brief.model_dump(),
            roles=roles,
            scenes=scenes,
            moral=t.get("moral", ""),
            tags=t.get("tags", []),
        )

    # ---------- 漫画解读 ----------

    async def list_comics(self, page: int = 1, page_size: int = 20) -> ComicListResponse:
        """漫画列表"""
        self._ensure_loaded()
        items = self._comics
        total = len(items)
        start = (page - 1) * page_size
        page_items = items[start : start + page_size]

        briefs = [
            ComicBrief(
                id=c["id"],
                title=c["title"],
                summary=c.get("summary", ""),
                classical_source=c.get("classical_source", ""),
                cover_keyword=c.get("cover_keyword", ""),
                panel_count=len(c.get("panels", [])),
                like_count=c.get("like_count", 0),
                created_at=c.get("created_at", "2024-01-01T00:00:00"),
            )
            for c in page_items
        ]
        return ComicListResponse(
            items=briefs, total=total, page=page, page_size=page_size
        )

    async def get_comic(self, comic_id: str) -> ComicDetail:
        """漫画详情"""
        self._ensure_loaded()
        for c in self._comics:
            if c.get("id") == comic_id:
                brief = ComicBrief(
                    id=c["id"],
                    title=c["title"],
                    summary=c.get("summary", ""),
                    classical_source=c.get("classical_source", ""),
                    cover_keyword=c.get("cover_keyword", ""),
                    panel_count=len(c.get("panels", [])),
                    like_count=c.get("like_count", 0),
                    created_at=c.get("created_at", "2024-01-01T00:00:00"),
                )
                from app.schemas.content import ComicPanel
                panels = [
                    ComicPanel(
                        index=p.get("index", i),
                        image_keyword=p.get("image_keyword", ""),
                        scene=p.get("scene", ""),
                        shot=p.get("shot", ""),
                        action=p.get("action", ""),
                        caption=p.get("caption", ""),
                        dialogue=p.get("dialogue", ""),
                        character=p.get("character", ""),
                        emotion=p.get("emotion", ""),
                        knowledge_anchor=p.get("knowledge_anchor", ""),
                        visual_metaphor=p.get("visual_metaphor", ""),
                        beat=p.get("beat", ""),
                        image_url=p.get("image_url", ""),
                        image_prompt=p.get("image_prompt", ""),
                        verse=p.get("verse"),
                    )
                    for i, p in enumerate(c.get("panels", []))
                ]
                characters = [
                    ComicCharacter(
                        name=character.get("name", ""),
                        role=character.get("role", ""),
                        description=character.get("description", ""),
                        visual_anchor=character.get("visual_anchor", ""),
                    )
                    for character in c.get("characters", [])
                ]
                return ComicDetail(
                    **brief.model_dump(),
                    style_guide=c.get("style_guide", ""),
                    characters=characters,
                    panels=panels,
                    tags=c.get("tags", []),
                )
        raise ValueError(f"漫画 {comic_id} 不存在")

    def _build_demo_comics(self) -> List[dict]:
        """构建演示漫画数据（MVP 阶段内置）"""
        return [
            {
                "id": "comic_001",
                "title": "孔子的课堂：因材施教",
                "summary": "同一个问题，孔子给子路和冉有不同答案，漫画解读因材施教",
                "classical_source": "《论语·先进》",
                "cover_keyword": "古代私塾课堂，孔子端坐，两个学生提问，水墨画风格",
                "like_count": 42,
                "created_at": "2024-06-01T00:00:00",
                "tags": ["教育", "因材施教", "论语"],
                "panels": [
                    {"index": 0, "image_keyword": "子路急匆匆跑来问孔子问题", "caption": "子路问：'闻斯行诸？'（听了就去做吗？）", "verse": "子路问：闻斯行诸？"},
                    {"index": 1, "image_keyword": "孔子摇头", "caption": "孔子说：'有父兄在，怎么能听了就做？'", "verse": "子曰：有父兄在，如之何其闻斯行之？"},
                    {"index": 2, "image_keyword": "冉有走来问同样的问题", "caption": "冉有问同样的问题：'闻斯行诸？'", "verse": "冉有问：闻斯行诸？"},
                    {"index": 3, "image_keyword": "孔子点头", "caption": "孔子说：'听了就去做！'", "verse": "子曰：闻斯行之"},
                    {"index": 4, "image_keyword": "公西华一脸困惑", "caption": "公西华困惑：同样的问题，为什么答案不同？"},
                    {"index": 5, "image_keyword": "孔子微笑解释", "caption": "孔子说：'子路冲动，所以要压一压；冉有退缩，所以要推一推'", "verse": "求也退，故进之；由也兼人，故退之"},
                ],
            },
            {
                "id": "comic_002",
                "title": "颜回的快乐：一箪食一瓢饮",
                "summary": "颜回在简陋环境中依然快乐，漫画解读安贫乐道",
                "classical_source": "《论语·雍也》",
                "cover_keyword": "简陋小屋中，一人安坐读书，窗外竹影，水墨画",
                "like_count": 38,
                "created_at": "2024-06-02T00:00:00",
                "tags": ["安贫乐道", "颜回", "论语"],
                "panels": [
                    {"index": 0, "image_keyword": "简陋巷子里的破旧小屋", "caption": "一箪食，一瓢饮，在陋巷", "verse": "一箪食，一瓢饮，在陋巷"},
                    {"index": 1, "image_keyword": "颜回安坐读书面带微笑", "caption": "人不堪其忧，回也不改其乐", "verse": "人不堪其忧，回也不改其乐"},
                    {"index": 2, "image_keyword": "其他人愁眉苦脸路过", "caption": "别人都受不了这种清苦……"},
                    {"index": 3, "image_keyword": "颜回抬头望天神情恬淡", "caption": "但颜回心中有道，自得其乐"},
                ],
            },
        ]


# 全局服务单例
content_service = ContentService()
