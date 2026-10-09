"""
悟典 - Quote Verifier（PHASE 5 / P5-01）

核心能力：把「**这句话存在**」与「**出处正确**」拆成**两个可独立判定**的指标
（PROJECT-BRIEF 第十一章）。这正是旧 ``citation_validator`` 无法表达的：
旧实现只做「原文与本次 rag_refs 互为子串」的单一布尔判定。

设计要点
--------
1. **全库回查**：查询的是**整个知识库**，而非"本次检索到的 rag_refs"。
   旧实现把"未检索到"与"不存在"混为一谈（``trust.md`` 用例 C8）。
2. **单向包含 + 长度下限**：只允许「引文是原典条目的子串」这一方向，
   并设长度下限，消除旧实现双向子串导致的
   「真实短句内嵌伪造长文」绕过（``trust.md`` 用例 C9）。
3. **繁简/标点归一化**，但归一化命中与逐字命中**分开报告**
   （``exact_match`` vs ``normalized_match``），不掩盖差异。
4. **两个独立字段**：``quote_exists`` 与 ``source_correct`` 互不派生，
   允许出现 ``quote_exists=True & source_correct=False``（``citation_corrected``）。

诚实性声明（重要）
-----------------
- 本模块**不生成**任何古籍原文；所有 ``correct_source`` / ``candidates``
  均指向仓库内**真实存在**的语料条目。
- 繁简归一化使用**内置字符映射表**（仓库未安装 ``opencc`` / ``zhconv``），
  覆盖先秦诸子常用异体字，但**不是**完备的繁简转换。未覆盖的字符会退化为
  ``normalized_match=False`` —— 即**漏报而非误报**，方向上是安全的。
  完备转换待引入真实转换库后替换（记为未验证项）。
- 无任何"默认通过"路径：找不到即 ``quote_exists=False``。
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from app.schemas.knowledge import QuoteCandidate, QuoteVerification
from app.services.trust_state import decide_trust_state

logger = logging.getLogger(__name__)

# ============================================================
# 阈值（P5-05 用例 B1/B2）
# ============================================================

#: 低于此长度（归一化后字符数）**不构成可核验引文** → ``quote_exists=False``。
#: 依据：``君子``（2 字）这类片段无法支撑任何思想结论（用例 B1）。
MIN_FRAGMENT_CHARS = 4

#: 达到此长度才可能判 ``verified``。介于两阈值之间记为 ``partial``，
#: **不计入 verified**（用例 B2：``不亦说乎`` 为截断片段）。
MIN_FULL_QUOTE_CHARS = 6

#: 判定 ``source_correct`` 时忽略的篇章后缀（``学而篇`` → ``学而``）。
_CHAPTER_SUFFIXES = ("篇", "章", "上", "下")

#: 归一化时剥离的标点/空白/引号（含全角与 CJK 引号）。
#: 用字符集合而非带转义的字符类构造，避免 Windows 控制台下的转义告警。
_STRIP_CHARS = set(
    " \t\r\n\u3000"          # 空白（含全角空格）
    "，。、！？；：（）()【】《》「」『』〈〉"
    "“”‘’·．"                # 全角标点与间隔号
    ",.!"                    # 半角标点（不含 \ 以免转义告警）
    "?"
    ";:'\""
    "-—…~／/・‧"
)


def _strip_punctuation(text: str) -> str:
    return "".join(ch for ch in text if ch not in _STRIP_CHARS)

# ============================================================
# 繁简归一化（内置映射，覆盖先秦诸子常用异体字）
# ============================================================

#: 繁体/异体 → 简体。**不完整**，仅覆盖本语料常见字形。
#: 未覆盖字符不会误报（只会漏判 ``normalized_match``）。
_TRADITIONAL_TO_SIMPLIFIED: Dict[str, str] = {
    # 虚词与高频字
    "於": "于", "與": "与", "為": "为", "無": "无", "後": "后", "從": "从",
    "來": "来", "個": "个", "們": "们", "這": "这", "那": "那", "對": "对",
    "當": "当", "應": "应", "會": "会", "能": "能", "還": "还", "雖": "虽",
    "爾": "尔", "汝": "汝", "矣": "矣", "乎": "乎", "哉": "哉", "焉": "焉",
    # 学/思/言
    "學": "学", "習": "习", "說": "说", "語": "语", "論": "论", "記": "记",
    "訓": "训", "講": "讲", "讀": "读", "寫": "写", "問": "问", "聞": "闻",
    "見": "见", "視": "视", "覺": "觉", "聽": "听", "聲": "声", "詩": "诗",
    "詞": "词", "賦": "赋", "傳": "传", "書": "书", "畫": "画",
    # 德行/伦理
    "禮": "礼", "義": "义", "聖": "圣", "賢": "贤", "仁": "仁", "德": "德",
    "愛": "爱", "親": "亲", "孝": "孝", "悌": "悌", "忠": "忠", "信": "信",
    "誠": "诚", "讓": "让", "謙": "谦", "恥": "耻", "勇": "勇", "智": "智",
    "貴": "贵", "賤": "贱", "貧": "贫", "富": "富", "榮": "荣", "辱": "辱",
    # 政/国
    "國": "国", "權": "权", "勢": "势", "亂": "乱", "治": "治", "政": "政",
    "賞": "赏", "罰": "罚", "刑": "刑", "法": "法", "術": "术", "數": "数",
    "計": "计", "謀": "谋", "議": "议", "論": "论", "軍": "军", "戰": "战",
    # 变化/时间
    "變": "变", "動": "动", "靜": "静", "過": "过", "進": "进", "達": "达",
    "遠": "远", "難": "难", "易": "易", "時": "时", "歲": "岁", "舊": "旧",
    "親": "亲", "觀": "观", "樂": "乐", "憂": "忧", "慮": "虑", "懼": "惧",
    # 自然/器物
    "車": "车", "馬": "马", "鳥": "鸟", "魚": "鱼", "龍": "龙", "風": "风",
    "雲": "云", "電": "电", "陽": "阳", "陰": "阴", "長": "长", "萬": "万",
    "億": "亿", "體": "体", "實": "实", "華": "华", "寶": "宝", "錢": "钱",
    "財": "财", "貨": "货", "買": "买", "賣": "卖", "價": "价", "總": "总",
    # 其他常见
    "眾": "众", "幾": "几", "別": "别", "麼": "么", "樣": "样", "種": "种",
    "點": "点", "頭": "头", "體": "体", "邊": "边", "裏": "里", "內": "内",
    "願": "愿", "覺": "觉", "慮": "虑", "關": "关", "開": "开", "閉": "闭",
    "門": "门", "間": "间", "際": "际", "際": "际", "歸": "归", "歲": "岁",
}


def to_simplified(text: str) -> str:
    """繁体/异体 → 简体（内置映射，不完整；未覆盖字符原样保留）。"""
    return "".join(_TRADITIONAL_TO_SIMPLIFIED.get(ch, ch) for ch in text)


def normalize_text(text: str) -> str:
    """归一化：NFKC → 繁转简 → 剥离标点/空白/引号。

    该函数是"内容等价"判定的**唯一**口径，供本模块与 ``citation_validator``
    共用，避免两套归一化逻辑分叉。
    """
    if not text:
        return ""
    # 全角 → 半角（NFKC 也会把部分异体字标准化）
    normalized = unicodedata.normalize("NFKC", text)
    normalized = to_simplified(normalized)
    normalized = _strip_punctuation(normalized)
    return normalized.strip()


def normalized_length(text: str) -> int:
    """归一化后的有效字符数（用于长度下限判定）。"""
    return len(normalize_text(text))


# ============================================================
# 语料条目
# ============================================================

@dataclass(frozen=True)
class CorpusEntry:
    """知识库中的一条可核验文本。"""

    passage_id: str
    source: str
    book: str
    chapter: str
    original: str
    text_type: str  # original | commentary | translation | modern_explanation
    norm: str       # 归一化正文（缓存，避免重复计算）

    @property
    def school(self) -> Optional[str]:
        return _BOOK_TO_SCHOOL.get(self.book)


#: 书名 → 学派（仅用于展示，不参与判定；未收录者返回 None，不猜测）
_BOOK_TO_SCHOOL: Dict[str, str] = {
    "论语": "儒家", "孟子": "儒家", "荀子": "儒家", "大学": "儒家", "中庸": "儒家",
    "传习录": "儒家",
    "道德经": "道家", "老子": "道家", "庄子": "道家",
    "墨子": "墨家",
    "韩非子": "法家", "商君书": "法家",
    "孙子兵法": "兵家",
}


def _repo_root() -> Path:
    # backend/app/services/quote_verifier.py → <repo>
    return Path(__file__).resolve().parents[3]


# ============================================================
# 语料加载（只读 JSON，不依赖 ChromaDB）
# ============================================================

_CORPUS_CACHE: Optional[List[CorpusEntry]] = None


def _add_entry(
    bucket: List[CorpusEntry], *, passage_id: str, source: str, book: str,
    chapter: str, original: str, text_type: str,
) -> None:
    text = (original or "").strip()
    if not text:
        return
    norm = normalize_text(text)
    if not norm:
        return
    bucket.append(CorpusEntry(
        passage_id=passage_id, source=source or f"《{book}》",
        book=book, chapter=chapter, original=text,
        text_type=text_type, norm=norm,
    ))


def _load_lunyu(bucket: List[CorpusEntry]) -> None:
    path = _repo_root() / "data" / "processed" / "lunyu.json"
    if not path.exists():
        logger.warning("quote_verifier: 缺少语料文件 %s", path)
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    book = data.get("book", "论语")
    for chapter in data.get("chapters", []):
        chapter_title = chapter.get("chapter_title", "")
        for verse in chapter.get("verses", []):
            verse_id = verse.get("verse_id", "")
            if not verse_id:
                continue
            _add_entry(
                bucket,
                passage_id=f"lunyu:{verse_id}",
                source=f"《{book}·{chapter_title}》",
                book=book, chapter=chapter_title,
                original=verse.get("original", ""),
                text_type="original",
            )


def _load_debate_classics(bucket: List[CorpusEntry]) -> None:
    path = _repo_root() / "data" / "processed" / "debate_classics.json"
    if not path.exists():
        logger.warning("quote_verifier: 缺少语料文件 %s", path)
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for _sage_key, classic in (data.get("classics") or {}).items():
        book = classic.get("book", "")
        for verse in classic.get("verses", []):
            verse_id = verse.get("id", "")
            if not verse_id:
                continue
            _add_entry(
                bucket,
                passage_id=verse_id,
                source=verse.get("source", f"《{book}》"),
                book=book,
                chapter=verse.get("chapter", ""),
                original=verse.get("original", ""),
                text_type="original",
            )


def _load_commentaries(bucket: List[CorpusEntry]) -> None:
    """L2 注疏。

    只索引 ``commentary``（注疏正文），**不索引其内嵌的 ``original``** ——
    后者与 L1 逐字重复，会造成同一文本出现两个真值
    （``classical-knowledge.md`` §5.2 / ``schemas/knowledge.py`` 分层约束）。
    """
    path = _repo_root() / "backend" / "data" / "commentaries" / "lunyu_zhuxi.json"
    if not path.exists():
        logger.warning("quote_verifier: 缺少注疏文件 %s", path)
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data.get("commentaries", []):
        verse_id = item.get("verse_id", "")
        commentary = item.get("commentary", "")
        if not verse_id or not commentary:
            continue
        _add_entry(
            bucket,
            passage_id=f"commentary:{verse_id}",
            source=item.get("source", "朱熹《论语集注》"),
            book="论语集注",
            chapter=item.get("chapter", ""),
            original=commentary,
            text_type="commentary",
        )


def load_corpus(*, reload: bool = False) -> List[CorpusEntry]:
    """加载并缓存全库语料（只读，不写任何文件）。"""
    global _CORPUS_CACHE
    if _CORPUS_CACHE is not None and not reload:
        return _CORPUS_CACHE

    bucket: List[CorpusEntry] = []
    _load_lunyu(bucket)
    _load_debate_classics(bucket)
    _load_commentaries(bucket)
    _CORPUS_CACHE = bucket
    logger.info("quote_verifier 语料加载完成: %d 条", len(bucket))
    return _CORPUS_CACHE


# ============================================================
# 出处解析与比较
# ============================================================

#: 视为"未提供出处"的哨兵值。
_NO_SOURCE_VALUES = frozenset({"", "无", "未知", "none", "null", "n/a"})


def is_source_missing(claimed_source: Optional[str]) -> bool:
    """声称出处是否缺失/无效。

    缺失出处**不得**被判为 ``source_correct=True``
    （消除旧 ``_check_classic_belonging`` 的空值放行缺陷）。
    """
    return (claimed_source or "").strip().lower() in _NO_SOURCE_VALUES


def parse_source(claimed_source: str) -> Tuple[str, str]:
    """解析出处为 ``(book, chapter)``。

    支持：``《论语·学而》`` / ``论语·学而篇`` / ``《孟子·公孙丑上》`` /
    ``《将进酒》``（无篇章）。
    """
    text = (claimed_source or "").strip()
    text = text.strip("《》").strip()
    if not text:
        return "", ""
    for sep in ("·", "・", "‧", ".", "／", "/"):
        if sep in text:
            book, _, chapter = text.partition(sep)
            return book.strip(), chapter.strip()
    return text, ""


def _canonical_chapter(chapter: str) -> str:
    """去掉 ``篇`` / ``章`` / ``上`` / ``下`` 等后缀，便于比较。"""
    value = (chapter or "").strip()
    for suffix in _CHAPTER_SUFFIXES:
        if value.endswith(suffix) and len(value) > len(suffix):
            value = value[: -len(suffix)]
    return value


def _source_matches_entry(
    claimed_book: str, claimed_chapter: str, entry: CorpusEntry,
) -> bool:
    """声称出处是否与该语料条目一致（书名必匹配；篇章若给出则须匹配）。"""
    if not claimed_book:
        return False
    if claimed_book != entry.book:
        return False
    if not claimed_chapter:
        # 只给了书名：书名正确即视为出处正确（篇章未声明，不算错误）
        return True
    entry_chapter = _canonical_chapter(entry.chapter)
    claimed = _canonical_chapter(claimed_chapter)
    if not entry_chapter:
        return False
    return claimed == entry_chapter or claimed in entry_chapter or entry_chapter in claimed


# ============================================================
# 匹配
# ============================================================

def _match_entries(
    quote_raw: str, quote_norm: str, entries: Iterable[CorpusEntry],
) -> List[Tuple[CorpusEntry, str, float]]:
    """单向包含匹配：``quote_norm`` 必须是条目正文的**子串**。

    返回 ``[(entry, match_type, similarity), ...]``，其中 ``match_type`` ∈
    ``exact`` / ``normalized`` / ``partial``：

    - ``exact``：**原始文本**逐字相等（最严格，唯一可能判 ``verified`` 的类型）。
    - ``normalized``：归一化后整体相等，或长度达标的摘句（繁简/标点差异）。
    - ``partial``：短于 :data:`MIN_FULL_QUOTE_CHARS` 的片段，**不计入 verified**。

    单向（只允许"引文 ⊆ 原典"）是消除「真实短句内嵌伪造长文」绕过的关键：
    反向包含（原典 ⊆ 引文）会让伪造长文因内嵌真实短句而通过。
    """
    raw_stripped = (quote_raw or "").strip()
    found: List[Tuple[CorpusEntry, str, float]] = []
    for entry in entries:
        if not entry.norm or quote_norm not in entry.norm:
            continue
        if entry.original.strip() == raw_stripped:
            match_type = "exact"
            similarity = 1.0
        elif entry.norm == quote_norm:
            match_type = "normalized"
            similarity = 1.0
        elif len(quote_norm) >= MIN_FULL_QUOTE_CHARS:
            # 完整长度的摘句：逐字包含，但非整条
            match_type = "normalized"
            similarity = round(len(quote_norm) / max(len(entry.norm), 1), 4)
        else:
            match_type = "partial"
            similarity = round(len(quote_norm) / max(len(entry.norm), 1), 4)
        found.append((entry, match_type, similarity))
    return found


_MATCH_RANK = {"exact": 0, "normalized": 1, "partial": 2}

#: 句界标点（CONTRACT-001 v2 §3.3）。
#: 注意：**只含**「。！？」——分号「；」不在 §3.3 列表内，不得自行加严。
_SENTENCE_BOUNDARY_RE = re.compile(r"[。！？]")


def crosses_sentence_boundary(
    entry_original: str, quote_norm: str, quote_raw: str,
) -> bool:
    """判断归一化引文是否**跨句**拼接而成（CONTRACT-001 v2 §3.3）。

    为什么需要：``_strip_punctuation`` 会删除「。！？「」」等标点，于是
    「上一句结尾 + 下一句开头」在归一化后会被**无缝拼接**，形成一个在原文中
    并不连续存在的字符串。例如把子贡的问句与孔子的答句粘成
    ``有一言而可以终身行之者乎子曰其恕乎``。若不拦截，这种拼接会获得
    ``exact_match=true``，甚至（在满足出处与完整性门时）被判 ``verified``
    并作为经典原文展示 —— 比修复前**更宽松**。

    判定方式（不依赖脆弱的「归一化下标 → 原文下标」反查）：
    把原文按句界切分；若归一化引文能**完整落在某一个句子之内**，则未跨句。
    否则视为跨句。

    例外：若**原始引文自身**含句界标点，说明引用者明确引用了跨句原文
    （例如整章引用），此时不算违规。
    """
    if any(mark in (quote_raw or "") for mark in "。！？"):
        return False
    for sentence in _SENTENCE_BOUNDARY_RE.split(entry_original or ""):
        if sentence and quote_norm in normalize_text(sentence):
            return False
    return True


def _select_best(
    matches: Sequence[Tuple[CorpusEntry, str, float]],
    claimed_book: str, claimed_chapter: str,
) -> Optional[Tuple[CorpusEntry, str, float]]:
    """选出最佳候选（确定性）。

    排序键（依次）：
    1. 书名与声称出处一致者优先（便于给出**同书**内的正确篇章）
    2. 匹配类型（``exact`` > ``normalized`` > ``partial``）
    3. 正文更短者优先（越短说明引文占该条目的比例越大 → 定位越精确）
    4. ``passage_id`` 字典序（保证跨进程稳定）
    """
    if not matches:
        return None

    def sort_key(item: Tuple[CorpusEntry, str, float]):
        entry, match_type, _sim = item
        book_pref = 0 if (claimed_book and entry.book == claimed_book) else 1
        chapter_pref = 0 if (
            claimed_chapter
            and _canonical_chapter(claimed_chapter) == _canonical_chapter(entry.chapter)
        ) else 1
        return (
            book_pref, chapter_pref, _MATCH_RANK.get(match_type, 9),
            len(entry.norm), entry.passage_id,
        )

    return sorted(matches, key=sort_key)[0]


def _build_candidates(
    matches: Sequence[Tuple[CorpusEntry, str, float]], limit: int = 5,
) -> List[QuoteCandidate]:
    """构造 ``candidates[]``，**同一出处只保留一条**，避免重复来源。

    去重键 = ``entry.source``。理由（``03-task-dag.md`` P5-05 用例 D1 /
    §13 GATE-5 判据 ⑧「``candidates[]`` 对摘句/全句不产生重复来源」）：

    同一段引文常在语料中**同时**出现两次——``lunyu.json`` 里嵌在完整章句内
    （``lunyu:8.7`` 全句），``debate_classics.json`` 里又是独立摘句
    （``lunyu-taibo-01``）。二者 ``source`` 相同（``《论语·泰伯》``）。
    若并列输出，同一出处会出现两个互不相干的 ``passage_id``，让调用方无法判断
    哪条才是"这条引文的出处"。

    保留规则：同出处内取**正文最短**者（越短说明引文占该条目的比例越大 →
    定位越精确），并列时按匹配类型与 ``passage_id`` 稳定排序。
    """
    best_by_source: Dict[str, Tuple[CorpusEntry, str, float]] = {}
    for entry, match_type, similarity in matches:
        current = best_by_source.get(entry.source)
        if current is None:
            best_by_source[entry.source] = (entry, match_type, similarity)
            continue
        cur_entry, cur_type, _cur_sim = current
        if (len(entry.norm), _MATCH_RANK.get(match_type, 9), entry.passage_id) < (
            len(cur_entry.norm), _MATCH_RANK.get(cur_type, 9), cur_entry.passage_id
        ):
            best_by_source[entry.source] = (entry, match_type, similarity)

    ordered = sorted(
        best_by_source.values(),
        key=lambda item: (
            _MATCH_RANK.get(item[1], 9), -item[2], len(item[0].norm), item[0].passage_id,
        ),
    )
    return [
        QuoteCandidate(
            passage_id=entry.passage_id,
            source=entry.source,
            text_type=entry.text_type,
            similarity=similarity,
        )
        for entry, _match_type, similarity in ordered[:limit]
    ]


# ============================================================
# 对外主入口
# ============================================================

def verify_quote(
    quote: str,
    claimed_source: Optional[str] = None,
    *,
    entries: Optional[Sequence[CorpusEntry]] = None,
) -> QuoteVerification:
    """校验一句引文：**分别**给出「这句话存在」与「出处正确」。

    Args:
        quote: 待校验引文。
        claimed_source: 模型声称的出处，如 ``《论语·学而》``。
            缺失/``"无"`` → ``source_correct=False``（不得放行）。
        entries: 可选语料覆盖（测试注入用）；默认加载全库。

    Returns:
        :class:`~app.schemas.knowledge.QuoteVerification`，
        含 ``quote_exists`` / ``exact_match`` / ``normalized_match`` /
        ``source_correct`` / ``correct_source`` / ``similarity`` /
        ``match_type`` / ``candidates`` / ``trust_state``。

    Examples:
        >>> result = verify_quote("己所不欲，勿施于人。", "《孟子·公孙丑上》")
        >>> result.quote_exists, result.source_correct
        (True, False)
        >>> result.trust_state
        'citation_corrected'
    """
    corpus = list(entries) if entries is not None else load_corpus()

    quote_norm = normalize_text(quote)
    claimed_book, claimed_chapter = parse_source(claimed_source or "")
    source_missing = is_source_missing(claimed_source)

    # --- 1. 长度下限：过短片段不构成可核验引文（用例 B1）---
    if not quote_norm or len(quote_norm) < MIN_FRAGMENT_CHARS:
        return QuoteVerification(
            quote_exists=False,
            exact_match=False,
            normalized_match=False,
            source_correct=False,
            correct_source=None,
            similarity=0.0,
            match_type="none",
            candidates=[],
            trust_state="insufficient_evidence",
            evidence_scope="corpus",
        )

    # --- 2. 全库单向包含匹配 ---
    matches = _match_entries(quote, quote_norm, corpus)

    if not matches:
        # 用例 C1 / C3：文本不存在 → 证据不足，禁止编造古文
        return QuoteVerification(
            quote_exists=False,
            exact_match=False,
            normalized_match=False,
            source_correct=False,
            correct_source=None,
            similarity=0.0,
            match_type="none",
            candidates=[],
            trust_state="insufficient_evidence",
            evidence_scope="corpus",
        )

    # --- 3. 判定「这句话存在」---
    quote_exists = True

    # --- 4. 判定「出处正确」（独立于文本存在性）---
    correct_entries = [
        (entry, match_type, similarity)
        for entry, match_type, similarity in matches
        if _source_matches_entry(claimed_book, claimed_chapter, entry)
    ]
    source_correct = bool(correct_entries) and not source_missing

    # --- 5. 最佳候选与逐字/归一化标志 ---
    best = _select_best(matches, claimed_book, claimed_chapter)
    assert best is not None  # matches 非空
    best_entry, best_match_type, best_similarity = best

    # 用于报告的"正确出处"：优先取与声称出处同书的条目，否则取最佳候选
    attribution_source = (
        _select_best(correct_entries, claimed_book, claimed_chapter)[0]
        if source_correct and correct_entries
        else best_entry
    )
    correct_source = attribution_source.source

    # exact_match：CONTRACT-001 v2 §2.2
    #   = 归一化引文是任一命中条目原文的**连续逐字子串**（且不跨句界）
    # **不要求**引文等于整条 passage —— 语料按章/verse 存储（如 lunyu:15.24
    # 含「子贡问曰：…己所不欲，勿施于人。」），若要求整条相等，则任何单句引用
    # 都不可能 exact，与数据集期望直接冲突（FIX-001 实测 12/12 失败均源于此）。
    #
    # 注意两处**不得**混入本判定（复核明确警告，误差余量为零）：
    #   1. **完整性门**（MIN_FULL_QUOTE_CHARS）属展示合同（§3.1/§3.2），
    #      不属于 exact_match；折进来会得到 17/18 = 0.9444（不达标）。
    #   2. **L1/text_type** 只约束 verified 与「可作经典原文展示」（§3.2/§4），
    #      不约束 exact_match。
    # 又：不得退化为「原文逐字相等」口径（17/18 = 0.9444），
    # 也不得要求 raw 逐字（qv-0017 繁体 於→于 需归一化后才命中）。
    #
    # `matches` 已由 _match_entries 保证 `quote_norm in entry.norm`（连续子串），
    # 故此处只需再排除跨句拼接。
    exact_match = any(
        not crosses_sentence_boundary(entry.original, quote_norm, quote)
        for entry, _match_type, _similarity in matches
    )
    normalized_match = best_match_type in ("exact", "normalized")

    # CONTRACT-001 v2 §3.1 / §3.2 / §4：
    #   完整性门 = len(N(q)) >= MIN_FULL_QUOTE_CHARS（共享常量，不另造阈值）
    #   L1 判定  = 用于**报告出处**的那条命中条目是否为 text_type=="original"
    # 二者只影响 verified/可展示，**不**影响 exact_match（见上）。
    completeness_gate = len(quote_norm) >= MIN_FULL_QUOTE_CHARS
    is_l1 = getattr(attribution_source, "text_type", None) == "original"

    trust_state = decide_trust_state(
        quote_exists=quote_exists,
        source_correct=source_correct,
        exact_match=exact_match,
        match_type=best_match_type,
        completeness_gate=completeness_gate,
        is_l1=is_l1,
    )

    return QuoteVerification(
        quote_exists=quote_exists,
        exact_match=exact_match,
        normalized_match=normalized_match,
        source_correct=source_correct,
        correct_source=None if source_correct else correct_source,
        similarity=best_similarity,
        match_type=best_match_type,
        candidates=_build_candidates(matches),
        trust_state=trust_state,
        evidence_scope="corpus",
    )


def verify_quote_dict(
    quote: str, claimed_source: Optional[str] = None,
) -> Dict[str, object]:
    """``verify_quote`` 的 dict 形式（便于 API / CLI 直接返回）。"""
    return verify_quote(quote, claimed_source).model_dump(mode="json")


__all__ = [
    "MIN_FRAGMENT_CHARS",
    "MIN_FULL_QUOTE_CHARS",
    "CorpusEntry",
    "load_corpus",
    "normalize_text",
    "to_simplified",
    "normalized_length",
    "is_source_missing",
    "parse_source",
    "verify_quote",
    "verify_quote_dict",
]
