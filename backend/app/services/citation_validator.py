"""
悟典 - 百家论道增强版引用校验器

职责：
- 校验引用的真实性
- 检查引用是否属于该圣贤的经典
- 提供引用状态反馈
"""
import logging
from typing import List, Tuple, Dict, Any

from app.schemas.debate import Citation
from app.services.rag_service import get_rag_service

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
        """校验引用，返回 (validated_citations, status)"""
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
        status = "all_verified" if all_verified else (
            "partial_verified" if has_valid_quote else "unverified"
        )
        return validated, status
    
    def _match_citation(self, citation: dict, rag_refs: List[dict]) -> bool:
        """匹配引用与RAG参考"""
        cit_original = citation.get("原文", citation.get("original", ""))
        if not cit_original or cit_original == "无":
            return False
        
        # 检查是否与RAG参考匹配
        for ref in rag_refs:
            ref_original = ref.get("original", "")
            if not ref_original:
                continue
            
            # 子串匹配
            if cit_original in ref_original or ref_original in cit_original:
                return True
            
            # 清理标点后匹配
            cleaned_cit = cit_original.replace("。", "").replace("，", "").replace("？", "").replace("！", "").replace("；", "").strip()
            cleaned_ref = ref_original.replace("。", "").replace("，", "").replace("？", "").replace("！", "").replace("；", "").strip()
            
            if cleaned_cit in cleaned_ref or cleaned_ref in cleaned_cit:
                return True
        
        return False
    
    def _check_classic_belonging(self, sage_key: str, citation: dict) -> bool:
        """检查引用是否属于该圣贤的经典"""
        source = citation.get("出处", citation.get("source", ""))
        classics = SAGE_CLASSICS.get(sage_key, [])
        if not source or source == "无":
            return True
        return any(c in source for c in classics)


# 全局实例
citation_validator = CitationValidator()
