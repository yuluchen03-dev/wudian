"""
悟典 - Citation Guard（PHASE 5 / P5-02、P5-05）

职责
----
1. **Evidence Pack 白名单**：LLM 只能引用 ``EvidencePack`` 内存在的 source。
   Pack 外的 source 一律 ``verifiable=False``（**不得放行**）。
2. **收紧后的匹配**：消除旧 ``citation_validator`` 的两个真实缺陷
   （``docs/kb-v1/audit/trust.md`` T-04 / T-05）：
   - **双向子串**（旧 ``:83`` / ``:90`` 的 ``cit in ref or ref in cit``）
     → 改为**单向包含 + 长度下限**，消除「真实短句内嵌伪造长文」绕过。
   - **空出处放行**（旧 ``:99-100`` ``if not source or source == "无": return True``）
     → 空出处**不得**判为出处正确。
3. **出处正确性判定**：旧实现从不校验"出处与文本是否一致"（T-03）。
   本模块按 ``book`` / ``chapter`` 逐级比对。

与 ``citation_validator`` 的关系（**增量扩展，不推翻**）
----------------------------------------------------
``citation_validator.validate()`` 的签名与 ``SAGE_CLASSICS`` 保持不变
（PROJECT-BRIEF 第十九章兼容要求）。本模块提供**更严格**的判定函数，
供 ``citation_validator`` 内部复用，从而让既有调用方在不改签名的情况下
获得修复后的行为。

诚实性
------
- 不编造任何原文/出处；白名单来源由调用方传入的 Evidence Pack 决定。
- 无"默认通过"路径：无法确认即 ``False``。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from app.schemas.knowledge import EvidenceItem, EvidencePack
from app.services.quote_verifier import (
    MIN_FRAGMENT_CHARS,
    is_source_missing,
    normalize_text,
    parse_source,
)
from app.services.trust_state import decide_trust_state, is_verifiable

logger = logging.getLogger(__name__)


# ============================================================
# 白名单
# ============================================================

@dataclass(frozen=True)
class WhitelistEntry:
    """白名单中的一条可引用证据。"""

    evidence_id: str
    original: str
    source: str
    book: str
    chapter: str
    text_type: str
    norm: str


class CitationWhitelist:
    """由 ``EvidencePack`` 构建的引用白名单。

    ``EvidencePack`` 是 LLM **唯一**被允许引用的证据集合
    （PROJECT-BRIEF 第九章：「LLM 只能引用 Evidence Pack 中存在的 source」）。
    """

    def __init__(self, entries: Sequence[WhitelistEntry]):
        self._entries: List[WhitelistEntry] = list(entries)

    # ---------------- 构建 ----------------

    @classmethod
    def from_evidence_pack(cls, pack: EvidencePack) -> "CitationWhitelist":
        entries: List[WhitelistEntry] = []
        for item in pack.evidence:
            book, chapter = parse_source(item.source)
            norm = normalize_text(item.original)
            if not norm:
                # 空白正文不构成可引用证据，拒绝入白名单（不静默放行）
                logger.warning(
                    "CitationWhitelist: evidence_id=%s 正文归一化后为空，拒绝入白名单",
                    item.evidence_id,
                )
                continue
            entries.append(WhitelistEntry(
                evidence_id=item.evidence_id,
                original=item.original,
                source=item.source,
                book=book,
                chapter=chapter,
                text_type=item.text_type,
                norm=norm,
            ))
        return cls(entries)

    @classmethod
    def from_items(cls, items: Iterable[EvidenceItem]) -> "CitationWhitelist":
        return cls.from_evidence_pack(
            EvidencePack(query="_whitelist_", evidence=list(items))
        )

    # ---------------- 查询 ----------------

    @property
    def entries(self) -> Tuple[WhitelistEntry, ...]:
        return tuple(self._entries)

    @property
    def sources(self) -> Tuple[str, ...]:
        """白名单内允许引用的 source 集合（去重，保持顺序）。"""
        seen: Dict[str, None] = {}
        for entry in self._entries:
            seen.setdefault(entry.source, None)
        return tuple(seen)

    def __len__(self) -> int:
        return len(self._entries)

    def __bool__(self) -> bool:
        return bool(self._entries)

    def allows_source(self, source: Optional[str]) -> bool:
        """该 source 是否在白名单内（**空来源一律 False**）。"""
        if is_source_missing(source):
            return False
        target = (source or "").strip()
        return any(entry.source == target for entry in self._entries)

    def find(self, quote: str) -> List[WhitelistEntry]:
        """在白名单内做**单向**匹配，返回命中的条目。"""
        quote_norm = normalize_text(quote)
        if not quote_norm or len(quote_norm) < MIN_FRAGMENT_CHARS:
            return []
        return [e for e in self._entries if quote_norm in e.norm]


# ============================================================
# 收紧后的匹配与出处判定（供 citation_validator 复用）
# ============================================================

def quote_is_supported_by_refs(quote: str, rag_refs: Sequence[dict]) -> bool:
    """引文是否被本次检索结果支持（**单向包含 + 长度下限**）。

    替代旧 ``_match_citation`` 的双向子串逻辑。规则：

    1. 归一化后长度低于 :data:`MIN_FRAGMENT_CHARS` → ``False``
       （「君子」等 2 字片段不足以支撑结论）。
    2. 引文（归一化后）必须是**某条 ref 原文的子串** —— **只允许这一方向**。
       反向（ref ⊆ quote）被明确拒绝，否则「伪造长文内嵌真实短句」会通过。

    Args:
        quote: 待校验引文（citation 的 ``原文``）。
        rag_refs: 本次检索结果，每项含 ``original``（可选 ``source``）。
    """
    quote_norm = normalize_text(quote)
    if not quote_norm or len(quote_norm) < MIN_FRAGMENT_CHARS:
        return False

    for ref in rag_refs:
        ref_original = (ref or {}).get("original", "")
        if not ref_original:
            continue
        ref_norm = normalize_text(ref_original)
        if not ref_norm:
            continue
        # 单向：引文 ⊆ 检索结果原文
        if quote_norm in ref_norm:
            return True
    return False


def source_matches_quote(
    quote: str, claimed_source: Optional[str], rag_refs: Sequence[dict],
) -> bool:
    """声称出处是否与**命中该引文的**检索结果一致。

    取代旧 ``_check_classic_belonging`` 的"书名关键词包含"检查，后者
    无法发现「同书错篇」（``trust.md`` 用例 C7）且对空出处直接放行（C10）。

    规则：
    1. 出处缺失/``"无"`` → ``False``（**不得放行**）。
    2. 引文必须在某条 ref 中命中，且该 ref 的 ``source`` 与声称出处
       在 ``book``（必匹配）与 ``chapter``（若声明则须匹配）两级一致。
    """
    if is_source_missing(claimed_source):
        return False

    quote_norm = normalize_text(quote)
    if not quote_norm or len(quote_norm) < MIN_FRAGMENT_CHARS:
        return False

    claimed_book, claimed_chapter = parse_source(claimed_source or "")
    if not claimed_book:
        return False

    for ref in rag_refs:
        ref_original = (ref or {}).get("original", "")
        if not ref_original:
            continue
        ref_norm = normalize_text(ref_original)
        if not ref_norm or quote_norm not in ref_norm:
            continue
        ref_book, ref_chapter = parse_source((ref or {}).get("source", ""))
        if ref_book != claimed_book:
            continue
        if not claimed_chapter:
            return True
        if _chapters_match(claimed_chapter, ref_chapter):
            return True
    return False


def _chapters_match(claimed: str, actual: str) -> bool:
    """篇章比较：忽略 ``篇`` / ``章`` 后缀，允许包含关系。"""
    if not actual:
        # ref 未提供篇章 → 无法确认，不算匹配（保守）
        return False
    a = _strip_chapter_suffix(claimed)
    b = _strip_chapter_suffix(actual)
    if not a or not b:
        return False
    return a == b or a in b or b in a


def _strip_chapter_suffix(chapter: str) -> str:
    value = (chapter or "").strip()
    for suffix in ("篇", "章", "上", "下"):
        if value.endswith(suffix) and len(value) > len(suffix):
            value = value[: -len(suffix)]
    return value


# ============================================================
# 对外主入口：校验一组 citation
# ============================================================

@dataclass(frozen=True)
class GuardedCitation:
    """单条引用经 Guard 校验后的结果。"""

    citation_id: str
    source: str
    original: str
    verifiable: bool
    trust_state: str
    quote_exists: bool
    source_correct: bool
    correct_source: Optional[str]
    reason: str


def guard_citations(
    citations: Sequence[dict],
    *,
    whitelist: Optional[CitationWhitelist] = None,
    rag_refs: Optional[Sequence[dict]] = None,
) -> Tuple[List[GuardedCitation], str]:
    """对一组 citation 执行白名单 + 收紧匹配校验。

    Args:
        citations: 每项含 ``id`` / ``出处``(或 ``source``) / ``原文``(或 ``original``)。
        whitelist: Evidence Pack 白名单。**给定即启用**：Pack 外的 source 一律
            不可验证。``None`` 表示本次不启用白名单（向后兼容旧调用方）。
        rag_refs: 检索结果，用于"引文是否被检索支持"判定。

    Returns:
        ``(guarded, status)``，``status`` ∈
        ``all_verified`` / ``partial_verified`` / ``unverified``。

    判定顺序（任一失败即不可验证）：
    1. 引文过短 → 失败；
    2. 给了白名单但 source 不在白名单 → 失败（**不得放行**）；
    3. 引文未被本次检索结果支持 → 失败；
    4. 声称出处与命中条目不一致（含空出处）→ 失败。
    """
    refs = list(rag_refs or [])
    guarded: List[GuardedCitation] = []

    for cit in citations:
        citation_id = cit.get("id", "")
        source = cit.get("出处", cit.get("source", "")) or ""
        original = cit.get("原文", cit.get("original", "")) or ""

        quote_exists = False
        source_correct = False
        correct_source: Optional[str] = None
        reason = ""

        # 1. 引文长度 / 空值
        if not original or original == "无":
            reason = "引文为空或为『无』"
        else:
            quote_norm = normalize_text(original)
            if len(quote_norm) < MIN_FRAGMENT_CHARS:
                reason = (
                    f"引文过短（归一化后 {len(quote_norm)} 字，"
                    f"下限 {MIN_FRAGMENT_CHARS}），不构成可核验引文"
                )

        # 2. 白名单（Evidence Pack 之外一律拒绝）
        if not reason and whitelist is not None:
            if not whitelist.allows_source(source):
                reason = f"出处 {source!r} 不在 Evidence Pack 白名单内"

        # 3. 检索支持 + 出处正确性
        if not reason:
            supported = quote_is_supported_by_refs(original, refs)
            if not supported:
                reason = "引文未出现在本次检索结果中（可能为模型编造）"
            else:
                quote_exists = True
                source_correct = source_matches_quote(original, source, refs)
                if not source_correct:
                    correct_source = _infer_correct_source(original, refs)

        trust_state = decide_trust_state(
            quote_exists=quote_exists,
            source_correct=source_correct,
            exact_match=quote_exists and source_correct,
            match_type="exact" if (quote_exists and source_correct) else "none",
        )
        verifiable = quote_exists and source_correct and is_verifiable(
            trust_state, "exact",
        )

        guarded.append(GuardedCitation(
            citation_id=citation_id,
            source=source,
            original=original,
            verifiable=verifiable,
            trust_state=trust_state,
            quote_exists=quote_exists,
            source_correct=source_correct,
            correct_source=correct_source,
            reason=reason,
        ))

    has_valid = any(g.verifiable and g.original != "无" for g in guarded)
    all_verified = bool(guarded) and all(g.verifiable for g in guarded)
    status = "all_verified" if all_verified else (
        "partial_verified" if has_valid else "unverified"
    )
    return guarded, status


def _infer_correct_source(quote: str, rag_refs: Sequence[dict]) -> Optional[str]:
    """从检索结果中推断正确出处（**只返回真实存在的 ref source**）。"""
    quote_norm = normalize_text(quote)
    if not quote_norm:
        return None
    for ref in rag_refs:
        ref_original = (ref or {}).get("original", "")
        ref_source = (ref or {}).get("source", "")
        if not ref_original or not ref_source:
            continue
        if quote_norm in normalize_text(ref_original):
            return ref_source
    return None


__all__ = [
    "WhitelistEntry",
    "CitationWhitelist",
    "GuardedCitation",
    "guard_citations",
    "quote_is_supported_by_refs",
    "source_matches_quote",
]
