"""
悟典 - AI 降级回复服务

当 LLM 不可用时（openai 未安装或 API_KEY 未配置），
提供基于规则的简单回复，确保 AI 接口仍能返回基本内容。

策略：
- 从 data/processed/lunyu.json 加载经文
- 基于关键词匹配返回相关原文 + 白话翻译
- 拼装结构化回复，模拟 LLM 输出格式
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.schemas.ai import VerseExplanation, RAGReference, QuizQuestion

logger = logging.getLogger(__name__)


class AIFallbackService:
    """LLM 不可用时的降级回复服务"""

    _instance: Optional["AIFallbackService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._verses: List[Dict[str, Any]] = []
        self._load_verses()
        self._initialized = True

    def _load_verses(self):
        """从 data/processed/lunyu.json 加载经文"""
        try:
            data_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "lunyu.json"
            if not data_path.exists():
                logger.warning(f"经文数据文件不存在: {data_path}")
                return
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            book = data.get("book", "论语")
            for chapter in data.get("chapters", []):
                ch_title = chapter.get("chapter_title", "")
                for verse in chapter.get("verses", []):
                    self._verses.append({
                        "verse_id": verse.get("verse_id", ""),
                        "original": verse.get("original", ""),
                        "translation": verse.get("translation", ""),
                        "annotations": verse.get("annotations", []),
                        "keywords": verse.get("keywords", []),
                        "title": verse.get("title", ""),
                        "book": book,
                        "chapter": ch_title,
                        "source": f"《{book}·{ch_title}》",
                    })
            logger.info(f"AIFallback 加载 {len(self._verses)} 条经文")
        except Exception as e:
            logger.warning(f"AIFallback 加载经文失败: {e}")

    @property
    def is_available(self) -> bool:
        return len(self._verses) > 0

    def _find_verse(self, verse_id: str) -> Optional[Dict[str, Any]]:
        """按 verse_id 精确查找"""
        for v in self._verses:
            if v["verse_id"] == verse_id:
                return v
        return None

    def _search_verses(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """关键词模糊查找"""
        if not self._verses:
            return []
        scored = []
        for v in self._verses:
            score = 0.0
            for kw in v.get("keywords", []):
                if kw in query:
                    score += 2.0
            if query in v["original"]:
                score += 3.0
            if v["verse_id"] == query:
                score += 5.0
            if score > 0:
                scored.append((score, v))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [v for _, v in scored[:top_k]]

    def _to_rag_ref(self, verse: Dict[str, Any], similarity: float = 0.8) -> RAGReference:
        return RAGReference(
            text=verse["original"],
            source=verse["source"],
            chapter=verse["chapter"],
            verse_no=verse["verse_id"],
            similarity=similarity,
        )

    # ----------------------------------------------------------
    # 逐句精讲降级
    # ----------------------------------------------------------
    def explain_verse(
        self,
        verse_id: str,
        text: Optional[str] = None,
        context: Optional[str] = None,
        depth: str = "standard",
    ) -> VerseExplanation:
        """降级版逐句精讲：返回经文原文 + 白话翻译 + 注释"""
        verse = self._find_verse(verse_id)
        if not verse and text:
            # 尝试用 text 匹配
            results = self._search_verses(text, top_k=1)
            if results:
                verse = results[0]

        if not verse:
            return VerseExplanation(
                verse_id=verse_id,
                original_text=text or verse_id,
                translation="（AI 讲解功能未启用，且未找到对应经文。请配置 LLM API_KEY 后使用完整讲解功能。）",
                background="",
                modern_analogy="",
                reflection="",
                confidence=0.0,
                disclaimer="降级模式：LLM 未配置",
            )

        # 拼装注释
        annotations = verse.get("annotations", [])
        key_words = [a.get("char", "") for a in annotations if a.get("char")]

        return VerseExplanation(
            verse_id=verse_id,
            original_text=verse["original"],
            translation=verse["translation"],
            background=f"本句出自《论语·{verse['chapter']}》。",
            modern_analogy="（降级模式不提供现代类比，配置 LLM 后可获取完整讲解）",
            reflection=f"关键词：{', '.join(verse.get('keywords', []))}",
            key_words=key_words,
            references=[self._to_rag_ref(verse)],
            confidence=0.6,
            disclaimer="降级模式：基于规则匹配，配置 LLM API_KEY 后可获取 AI 深度讲解",
        )

    # ----------------------------------------------------------
    # 文白翻译降级
    # ----------------------------------------------------------
    def translate_text(self, text: str, direction: str = "to_modern") -> str:
        """降级版翻译：尝试匹配经文原文返回内置翻译"""
        if direction == "to_classical":
            return "（降级模式不支持白话转文言，请配置 LLM API_KEY 后使用）"

        # 精确匹配原文
        for v in self._verses:
            if text.strip() in v["original"] or v["original"] in text:
                return v["translation"]

        # 关键词匹配
        results = self._search_verses(text, top_k=1)
        if results:
            return f"可能相关：{results[0]['translation']}"

        return "（降级模式未找到匹配经文，请配置 LLM API_KEY 后使用完整翻译功能）"

    # ----------------------------------------------------------
    # 与圣贤对话降级
    # ----------------------------------------------------------
    async def chat_with_sage(
        self,
        sage: str,
        question: str,
        history: List[dict] = None,
    ) -> str:
        """降级版圣贤对话：返回相关经文作为回复"""
        sage_names = {
            "confucius": "孔子",
            "mencius": "孟子",
            "wang_yangming": "王阳明",
            "laozi": "老子",
            "mozi": "墨子",
            "hanfeizi": "韩非子",
        }
        sage_name = sage_names.get(sage, "圣贤")

        results = self._search_verses(question, top_k=3)
        if not results:
            return (
                f"（降级模式）{sage_name}曰：此问未能在经典中找到直接对应。"
                f"请配置 LLM API_KEY 后获取更深入的对话。\n\n"
                f"---\n本回复为降级模式生成，非 AI 实时对话。"
            )

        lines = [f"（降级模式）{sage_name}曰：\n"]
        for i, v in enumerate(results, 1):
            lines.append(f"{i}. {v['original']}")
            lines.append(f"   译文：{v['translation']}")
            lines.append(f"   ——{v['source']}\n")

        lines.append("请配置 LLM API_KEY 后获取更深入的圣贤对话体验。")
        lines.append("\n---\n本回复为降级模式生成，非 AI 实时对话。")
        return "\n".join(lines)

    def chat_with_sage_full(
        self,
        sage: str,
        question: str,
        history: List[dict] = None,
    ) -> tuple:
        """降级版非流式圣贤对话，返回 (reply_text, references)"""
        sage_names = {
            "confucius": "孔子",
            "mencius": "孟子",
            "wang_yangming": "王阳明",
            "laozi": "老子",
            "mozi": "墨子",
            "hanfeizi": "韩非子",
        }
        sage_name = sage_names.get(sage, "圣贤")
        results = self._search_verses(question, top_k=3)
        refs = [self._to_rag_ref(v, similarity=0.7) for v in results]

        if not results:
            return (
                f"（降级模式）{sage_name}曰：此问未能在经典中找到直接对应。"
                f"请配置 LLM API_KEY 后获取更深入的对话。",
                [],
            )

        lines = [f"（降级模式）{sage_name}曰：\n"]
        for i, v in enumerate(results, 1):
            lines.append(f"{i}. {v['original']}")
            lines.append(f"   译文：{v['translation']}")
            lines.append(f"   ——{v['source']}\n")
        lines.append("请配置 LLM API_KEY 后获取更深入的圣贤对话体验。")
        return "\n".join(lines), refs

    # ----------------------------------------------------------
    # 生成测验题降级
    # ----------------------------------------------------------
    def generate_quiz(
        self,
        verse_id: str,
        quiz_type: str = "choice",
        difficulty: str = "medium",
        count: int = 3,
        verse_text: Optional[str] = None,
    ) -> List[QuizQuestion]:
        """降级版测验题：生成简单的填空/判断题"""
        verse = self._find_verse(verse_id)
        if not verse and verse_text:
            results = self._search_verses(verse_text, top_k=1)
            if results:
                verse = results[0]

        if not verse:
            return []

        questions = []
        original = verse["original"]
        translation = verse["translation"]
        source = verse["source"]

        if quiz_type == "fill":
            # 填空题：从原文中挖空
            annotations = verse.get("annotations", [])
            for ann in annotations[:count]:
                char = ann.get("char", "")
                meaning = ann.get("meaning", "")
                if char and char in original:
                    blanked = original.replace(char, "（）", 1)
                    questions.append(QuizQuestion(
                        question=f"填空：{blanked}\n出处：{source}",
                        answer=char,
                        explanation=f"{char}（{ann.get('pinyin', '')}）：{meaning}",
                        quiz_type="fill",
                        difficulty=difficulty,
                    ))
        elif quiz_type == "judge":
            # 判断题
            questions.append(QuizQuestion(
                question=f"判断：「{original}」出自{source}。\n（正确/错误）",
                answer="正确",
                explanation=f"该句确实出自{source}。",
                quiz_type="judge",
                difficulty=difficulty,
            ))
            if translation:
                questions.append(QuizQuestion(
                    question=f"判断：「{original}」的白话翻译是：「{translation}」\n（正确/错误）",
                    answer="正确",
                    explanation="该翻译为标准白话译文。",
                    quiz_type="judge",
                    difficulty=difficulty,
                ))
        else:
            # 默认简答题
            questions.append(QuizQuestion(
                question=f"请解释「{original}」的含义。\n出处：{source}",
                answer=translation,
                explanation=f"该句出自{source}。",
                quiz_type="explain",
                difficulty=difficulty,
            ))

        # 不足 count 时补充
        while len(questions) < count and verse.get("keywords"):
            kw = verse["keywords"][len(questions) % len(verse["keywords"])]
            questions.append(QuizQuestion(
                question=f"「{original}」中体现了哪个核心思想？\nA. {kw}\nB. 无关选项\nC. 无关选项\nD. 无关选项",
                answer="A",
                explanation=f"该句的核心关键词之一是「{kw}」。",
                quiz_type="choice",
                difficulty=difficulty,
            ))

        return questions[:count]


# 全局单例
ai_fallback = AIFallbackService()
