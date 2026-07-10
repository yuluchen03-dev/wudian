"""
悟典 - 趣味内容层数据模型
金句卡片、情景小剧场、漫画解读
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
#  金句卡片
# ============================================================

class CardStyle(str, Enum):
    """卡片排版风格"""
    INK_WASH = "ink_wash"          # 水墨风
    GOLD_SEAL = "gold_seal"        # 金印朱砂
    BAMBOO_SCROLL = "bamboo_scroll"  # 竹简风
    MOONLIGHT = "moonlight"        # 月夜风
    CLOUD_MIST = "cloud_mist"      # 云雾风


class QuoteCardBrief(BaseModel):
    """金句卡片列表项"""
    id: str
    quote: str = Field(..., description="名句原文")
    source: str = Field(..., description="出处，如《论语·学而》")
    style: CardStyle
    image_keyword: str = Field("", description="配图关键词（用于AI生图）")
    background_image: str = Field("", description="Quote card background image public path")
    like_count: int = 0
    share_count: int = 0
    created_at: datetime


class QuoteCardDetail(QuoteCardBrief):
    """金句卡片详情"""
    vernacular: str = Field(..., description="白话翻译")
    modern_interpretation: str = Field(..., description="现代解读")
    background_color: str = Field("#faf6ed", description="背景色")
    accent_color: str = Field("#b91c1c", description="点缀色")
    tags: List[str] = []
    is_liked: bool = False


class QuoteCardListResponse(BaseModel):
    """金句卡片列表响应"""
    items: List[QuoteCardBrief]
    total: int
    page: int
    page_size: int


# ============================================================
#  情景小剧场
# ============================================================

class TheaterLine(BaseModel):
    """小剧场台词"""
    role: str = Field(..., description="角色名")
    text: str = Field(..., description="台词")
    emotion: Optional[str] = Field(None, description="情绪/动作提示，如(叹气)")
    beat: str = Field("", description="戏剧节拍，如受阻/试探/转折/承诺")
    action: str = Field("", description="可演出的舞台动作")
    subtext: str = Field("", description="潜台词：角色真正想争取或隐藏的东西")
    pressure: str = Field("", description="本句施加或承受的冲突压力")
    is_original_verse: bool = Field(False, description="是否为原文引用")


class TheaterRole(BaseModel):
    """小剧场角色"""
    name: str
    description: str = Field("", description="角色介绍")
    classical_origin: Optional[str] = Field(None, description="对应的历史人物")
    avatar_keyword: str = Field("", description="头像生图关键词")
    objective: str = Field("", description="角色在本剧中的外在目标")
    fear: str = Field("", description="角色害怕失去或暴露的东西")
    belief: str = Field("", description="角色的核心信念")
    strategy: str = Field("", description="角色达成目标的说话/行动策略")
    conflict_trigger: str = Field("", description="触发角色反击或失控的冲突点")
    stage_action: str = Field("", description="角色标志性舞台动作")


class TheaterScene(BaseModel):
    """小剧场场景"""
    title: str
    setting: str = Field("", description="场景描述")
    lines: List[TheaterLine]


class TheaterBrief(BaseModel):
    """小剧场列表项"""
    id: str
    title: str
    summary: str
    classical_source: str = Field(..., description="原典出处")
    modern_setting: str = Field(..., description="现代场景，如'职场'/'校园'")
    cover_keyword: str = Field("", description="封面生图关键词")
    scene_count: int = 1
    like_count: int = 0
    view_count: int = 0
    created_at: datetime


class TheaterDetail(TheaterBrief):
    """小剧场详情"""
    roles: List[TheaterRole]
    scenes: List[TheaterScene]
    moral: str = Field(..., description="寓意/启示")
    tags: List[str] = []


class TheaterListResponse(BaseModel):
    """小剧场列表响应"""
    items: List[TheaterBrief]
    total: int
    page: int
    page_size: int


# ============================================================
#  漫画解读
# ============================================================

class ComicPanel(BaseModel):
    """漫画分镜"""
    index: int
    image_keyword: str = Field("", description="分镜生图关键词")
    scene: str = Field("", description="场景描述")
    shot: str = Field("", description="镜头语言")
    action: str = Field("", description="画面动作")
    caption: str = Field("", description="分镜配文")
    dialogue: str = Field("", description="对白")
    character: str = Field("", description="当前角色")
    emotion: str = Field("", description="角色情绪")
    knowledge_anchor: str = Field("", description="知识锚点")
    visual_metaphor: str = Field("", description="视觉隐喻")
    beat: str = Field("", description="节奏功能")
    image_url: str = Field("", description="漫画面板图 public path")
    image_prompt: str = Field("", description="Agens 生图提示词")
    verse: Optional[str] = Field(None, description="对应原文")


class ComicCharacter(BaseModel):
    """漫画角色圣经"""
    name: str
    role: str = ""
    description: str = ""
    visual_anchor: str = ""


class ComicBrief(BaseModel):
    """漫画列表项"""
    id: str
    title: str
    summary: str
    classical_source: str
    cover_keyword: str
    panel_count: int
    like_count: int = 0
    created_at: datetime


class ComicDetail(ComicBrief):
    """漫画详情"""
    style_guide: str = ""
    characters: List[ComicCharacter] = []
    panels: List[ComicPanel]
    tags: List[str] = []


class ComicListResponse(BaseModel):
    """漫画列表响应"""
    items: List[ComicBrief]
    total: int
    page: int
    page_size: int
