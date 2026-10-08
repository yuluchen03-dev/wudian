"""
悟典 - 百家论道增强版引用校验器

职责：
- 校验引用的真实性
- 检查引用是否属于该圣贤的经典
- 提供引用状态反馈

PHASE 5 收紧说明（P5-05，增量扩展，**不推翻**）
---------------------------------------------
原实现有三个已实测缺陷（``docs/kb-v1/audit/trust.md`` T-03/T-04/T-05）：
1. **双向子串匹配**（``cit in ref or ref in cit``）→「真实短句内嵌伪造长文」通过；
2. **空出处直接放行**（``if not source or source == "无": return True``）→ 跨派检查失效；
3. **从不校验出处与文本是否一致** →「同书错篇」「跨书错派」均通过。

修复方式：把匹配与出处判定**委托**给 ``citation_guard``（单一真值来源），
``validate()`` 签名与 ``SAGE_CLASSICS`` **保持不变**，既有调用方无需改动。
"""
import logging
from typing import List, Tuple, Dict, Any

from app.schemas.debate import Citation
from app.services.rag_service import get_rag_service
from app.services.citation_guard import (
    quote_is_supported_by_refs,
    source_matches_quote,
)

logger = logging.getLogger(__name__)

# 圣贤经典映射
SAGE_CLASSICS = {
    "confucius": ["论语", "春秋", "诗经", "尚书", "礼记", "周易"],
    "mencius": ["孟子"],
    "laozi": ["道德经", "老子"],
    "mozi": ["墨子"],
    "hanfeizi": ["韩非子", "韩非"],
    "wang_yangming": ["传习录", "王阳明"],
    "li_bai": ["李白", "将进酒", "行路难"],
    "su_shi": ["苏轼", "东坡", "定风波", "水调歌头"],
    "fan_zhongyan": ["范仲淹", "岳阳楼记"],
    "wang_anshi": ["王安石", "登飞来峰", "游褒禅山记"],
    "zhuge_liang": ["诸葛亮", "孔明", "诫子书", "出师表"],
}


class CitationValidator:
    """增强版引用校验器"""
    
    def __init__(self):
        self.rag = get_rag_service()
    
    async def validate(self, sage_key: str, citations: List[dict], rag_refs: List[dict]) -> Tuple[List[Citation], str]:
        """校验引用，返回 (validated_citations, status)

        判定顺序（PHASE 5 收紧后）：
        1. 引文必须**被本次检索结果单向支持**（消除双向子串与过短片段）；
        2. 声称出处必须与**命中该引文的**检索结果一致（消除空出处放行）；
        3. 仍需通过 ``SAGE_CLASSICS`` 学派归属检查（兼容保留）。
        """
        validated = []
        all_verified = True
        
        for cit in citations:
            verifiable = self._match_citation(cit, rag_refs)
            
            # 额外校验：检查引用是否属于该圣贤的经典
            if verifiable:
                belong_check = self._check_classic_belonging(sage_key, cit)
                if not belong_check:
                    verifiable = False
                    logger.warning("跨派引用: %s 引用了不属于本派的经典", sage_key)
            
            if not verifiable:
                all_verified = False
            
            validated.append(Citation(
                id=cit.get("id", ""),
                source=cit.get("出处", cit.get("source", "")),
                original=cit.get("原文", cit.get("original", "")),
                verifiable=verifiable,
            ))
        
        has_valid_quote = any(c.verifiable and c.original != "无" for c in validated)
        # 空引用集合不构成"全部通过"（原实现因 all_verified 初值 True 而误报）
        status = "all_verified" if (all_verified and validated) else (
            "partial_verified" if has_valid_quote else "unverified"
        )
        return validated, status
    
    def _match_citation(self, citation: dict, rag_refs: List[dict]) -> bool:
        """匹配引用与RAG参考（PHASE 5 收紧：单向包含 + 长度下限 + 出处一致）。

        旧实现只做双向子串匹配且**从不读出处**，导致：
        - 「真实短句内嵌伪造长文」被判可验证（双向包含）；
        - 「同书错篇」被放过（只比文本，不比出处）。

        现要求**两个条件同时成立**：文本被检索结果支持，且出处与命中条目一致。
        """
        cit_original = citation.get("原文", citation.get("original", ""))
        if not cit_original or cit_original == "无":
            return False

        # 1. 文本必须被本次检索结果单向支持
        if not quote_is_supported_by_refs(cit_original, rag_refs):
            return False

        # 2. 声称出处必须与命中该文本的检索结果一致
        cit_source = citation.get("出处", citation.get("source", ""))
        return source_matches_quote(cit_original, cit_source, rag_refs)
    
    def _check_classic_belonging(self, sage_key: str, citation: dict) -> bool:
        """检查引用是否属于该圣贤的经典。

        PHASE 5 修复：空出处**不再**直接放行（原 ``:99-100`` 的
        ``if not source or source == "无": return True`` 使跨派检查失效）。
        空出处视为**无法确认归属** → 返回 False（保守拒绝）。
        """
        source = citation.get("出处", citation.get("source", ""))
        classics = SAGE_CLASSICS.get(sage_key, [])
        if not source or source == "无":
            # 无法确认归属时不得放行（原实现返回 True 属缺陷）
            return False
        return any(c in source for c in classics)


# 全局实例
citation_validator = CitationValidator()
