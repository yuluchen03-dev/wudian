"""
悟典 - RAG 检索服务

功能：
- ChromaDB 向量数据库
- 文档分块（按章节 / 按句子）
- 向量化（OpenAI embeddings 或本地模型 fallback）
- 混合检索（向量 + 关键词 BM25-like）
- 返回原文引用与相关度

注意：chromadb / openai 为可选依赖。未安装时 RAGService 降级为
空检索（返回空列表），保证应用可正常启动。
"""
import os
import re
import json
import logging
import hashlib
import math
from pathlib import Path
from typing import List, Optional, Dict, Any

# 可选依赖：chromadb / openai 未安装时降级运行
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from chromadb.utils import embedding_functions
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    chromadb = None
    ChromaSettings = None
    embedding_functions = None

from app.core.config import settings
from app.schemas.ai import RAGReference

logger = logging.getLogger(__name__)


class LocalHashEmbeddingFunction:
    """Deterministic local embedding for Chroma indexes without external APIs."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def name(self) -> str:
        return "local_hash_embedding"

    def __call__(self, input: List[str]) -> List[List[float]]:
        return [self._embed_text(text) for text in input]

    def embed_query(self, input) -> List[List[float]]:
        if isinstance(input, str):
            return [self._embed_text(input)]
        return [self._embed_text(text) for text in input]

    def embed_documents(self, input) -> List[List[float]]:
        return [self._embed_text(text) for text in input]

    def _embed_text(self, text: str) -> List[float]:
        vector = [0.0] * self.dimensions
        tokens = self._tokenize(text)
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _tokenize(self, text: str) -> List[str]:
        normalized = re.sub(r"\s+", "", text.lower())
        latin = re.findall(r"[a-z0-9]+", normalized)
        chinese = re.findall(r"[\u4e00-\u9fff]", normalized)
        bigrams = [
            normalized[idx : idx + 2]
            for idx in range(max(0, len(normalized) - 1))
            if any("\u4e00" <= char <= "\u9fff" for char in normalized[idx : idx + 2])
        ]
        return latin + chinese + bigrams


# ============================================================
# 文本分块
# ============================================================

class TextChunker:
    """文本分块器：支持按句子、按章节、按固定长度"""

    # 简单中文断句：。！？；后分句
    SENTENCE_SPLIT = re.compile(r"[。！？；\n]+")

    @classmethod
    def split_sentences(cls, text: str) -> List[str]:
        """按句子分块"""
        parts = cls.SENTENCE_SPLIT.split(text)
        return [p.strip() for p in parts if p.strip()]

    @classmethod
    def split_by_length(cls, text: str, size: int = None, overlap: int = None) -> List[str]:
        """按固定长度分块（带 overlap）"""
        size = size or settings.RAG_CHUNK_SIZE
        overlap = overlap or settings.RAG_CHUNK_OVERLAP
        chunks = []
        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    @classmethod
    def split_chapter(cls, text: str, chapter_marker: str = "【") -> List[Dict[str, Any]]:
        """按章节分块，返回 [{text, chapter}]"""
        chapters = []
        current_chapter = "未分类"
        buffer = []
        for line in text.split("\n"):
            if line.strip().startswith(chapter_marker):
                if buffer:
                    chapters.append({
                        "text": "\n".join(buffer).strip(),
                        "chapter": current_chapter,
                    })
                    buffer = []
                current_chapter = line.strip().strip("【】")
            else:
                buffer.append(line)
        if buffer:
            chapters.append({
                "text": "\n".join(buffer).strip(),
                "chapter": current_chapter,
            })
        return [c for c in chapters if c["text"]]


# ============================================================
# RAG 服务
# ============================================================

class RAGService:
    """RAG 检索服务单例"""

    _instance: Optional["RAGService"] = None

    # P0R-02 / C3：百家论道向量检索的**相关性下限**。
    #
    # 原实现无任何下限，使完全无关的问题也返回「本派原典证据」，
    # 导致 `insufficient_evidence` 结构上不可达（违反 brief 第十二章与
    # 核心承诺「找不到，就不硬编」）。
    #
    # 取值 0.10，依据本地 hash embedding 的实测相似度分布：
    #   合法现代问题（brief ch.7/P0 要求可检索）：0.106 ~ 0.165
    #   无支撑问题（brief ch.12 要求拒答）：0.0 ~ 0.092（多数）
    # 注意两类在 0.10~0.16 存在**重叠**（如「孔子怎么看职场PUA」达 0.140），
    # 因 hash embedding 非语义，无法靠单一阈值完美区分；本阈值只做保守过滤，
    # 真正的语义判别属 PHASE 4（语义 embedding + reranker）范围。
    DEBATE_MIN_SIMILARITY: float = 0.10

    # 同义词映射：现代词汇 → 古文关键词（用于检索改写）
    SYNONYM_MAP: Dict[str, List[str]] = {
        "领导": ["上", "君", "上官", "君上"],
        "上司": ["上", "君"],
        "老板": ["上", "君"],
        "朋友": ["友", "朋", "交友"],
        "友情": ["友", "朋"],
        "错误": ["过", "愆"],
        "过失": ["过", "愆"],
        "学习": ["学", "习"],
        "思考": ["思"],
        "修养": ["修", "德", "修身"],
        "品德": ["德", "仁", "义"],
        "诚信": ["信", "忠"],
        "信用": ["信"],
        "孝顺": ["孝"],
        "父母": ["父", "母", "亲"],
        "君子": ["君子"],
        "小人": ["小人"],
        "工作": ["事", "为"],
        "职场": ["事", "为", "仕"],
        "压力": ["忧", "患"],
        "焦虑": ["忧", "患"],
        "失败": ["败", "失"],
        "成功": ["成", "达"],
        "快乐": ["乐", "说", "悦"],
        "悲伤": ["哀", "悲"],
        "愤怒": ["愠", "怒"],
        "选择": ["择", "取"],
        "立志": ["志"],
        "读书": ["学", "读"],
        "教育": ["教", "诲"],
        "智慧": ["知", "智"],
        "勇敢": ["勇"],
        "义气": ["义"],
        "礼仪": ["礼"],
        "音乐": ["乐", "音"],
        "治国": ["政", "国"],
        "政治": ["政"],
        "管理": ["政", "治"],
        "金钱": ["利", "财"],
        "利益": ["利"],
        "环境": ["里", "处"],
        "时间": ["时", "逝"],
        "珍惜": ["惜", "时"],
        "坚持": ["毅", "恒"],
        "反省": ["省", "察"],
        "知足": ["足", "安"],
        "谦虚": ["谦", "让"],
        "自信": ["信", "立"],
        "人生": ["生", "命"],
        "生死": ["生", "死"],
        "命运": ["命", "天"],
        "鬼神": ["鬼", "神"],
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # 文件回退索引：chromadb 不可用时用关键词匹配的经典原文列表
        # 格式: [{"id","text","book","chapter","verse_no","source","keywords"}]
        self._file_index: List[Dict[str, Any]] = []
        # 注疏索引：朱熹《论语集注》注疏数据
        self._commentary_index: List[Dict[str, Any]] = []
        # 百家论道专用索引：按圣贤/派别隔离，避免跨派检索串台。
        self._debate_classic_index: Dict[str, List[Dict[str, Any]]] = {}
        if not HAS_CHROMADB:
            logger.warning(
                "chromadb 未安装，RAGService 降级为关键词检索模式。"
                "安装 chromadb 后可启用向量检索：pip install chromadb"
            )
            self.client = None
            self.collection = None
            self.embed_fn = None
            self._load_file_index()
            self._load_commentary_index()
            self._load_debate_classic_index()
            self._initialized = True
            return

        # P0R-03 / B2：必须使用「已解析为绝对路径」的 persist dir。
        # 原实现直接用 settings.CHROMA_PERSIST_DIR（默认相对 "./chroma_db"），
        # 而 main.py:39 用的是 settings.resolved_chroma_persist_dir（绝对）。
        # 两者不一致会导致：当 CWD 不是 backend/ 时（例如从仓库根启动），
        # rag_service 会在错误位置静默新建一个空索引并降级，而 main.py 的
        # 健康检查仍按绝对路径判断、继续报 rag_available=true。
        # 统一改用 resolved_* 后，行为与 CWD 无关。
        self.persist_dir = settings.resolved_chroma_persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self.embed_fn = self._build_embed_fn()
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                embedding_function=self.embed_fn,
                metadata={"hnsw:space": "cosine"},
            )
            self._load_debate_classic_index()
            logger.info(
                f"RAGService 初始化: dir={self.persist_dir}, "
                f"collection={settings.CHROMA_COLLECTION}, "
                f"docs={self.collection.count()}"
            )
        except Exception as e:
            logger.warning(
                f"ChromaDB 初始化失败，降级为关键词检索模式: {e}"
            )
            self.client = None
            self.collection = None
            self.embed_fn = None
            self._load_file_index()
            self._load_commentary_index()
            self._load_debate_classic_index()
        self._initialized = True

    # ----------------------------------------------------------
    # 向量化函数
    # ----------------------------------------------------------
    def _build_embed_fn(self):
        """构建 embedding 函数：默认本地，显式配置后才调用外部 embedding API。"""
        if settings.RAG_EMBEDDING_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                api_base=settings.OPENAI_BASE_URL,
                model_name=settings.EMBEDDING_MODEL,
            )
        logger.info("RAG 使用本地哈希 embedding（无需外部 API）")
        return LocalHashEmbeddingFunction()

    # ----------------------------------------------------------
    # 文件回退索引（chromadb 不可用时）
    # ----------------------------------------------------------
    def _load_file_index(self):
        """从 data/processed/lunyu.json 加载经文到内存索引（关键词检索用）
        
        文档内容格式：【篇章】{chapter_title} 【原文】{original} 【译文】{translation} 【注释】{annotations}
        包含完整的原文+译文+出处，供 LLM 引用。
        """
        try:
            data_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "lunyu.json"
            if not data_path.exists():
                logger.warning(f"经文数据文件不存在: {data_path}")
                return
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            book = data.get("book", "论语")
            for chapter in data.get("chapters", []):
                ch_id = chapter.get("chapter_id", 0)
                ch_title = chapter.get("chapter_title", "")
                for verse in chapter.get("verses", []):
                    vid = verse.get("verse_id", "")
                    original = verse.get("original", "")
                    translation = verse.get("translation", "")
                    keywords = verse.get("keywords", [])
                    annotations = verse.get("annotations", [])
                    # 注释格式化为字符串
                    ann_text = "；".join(
                        f"{a.get('char','')}({a.get('pinyin','')}):{a.get('meaning','')}"
                        for a in annotations
                    ) if annotations else ""
                    # 完整文档内容
                    full_text = f"【篇章】{ch_title} 【原文】{original} 【译文】{translation}"
                    if ann_text:
                        full_text += f" 【注释】{ann_text}"
                    self._file_index.append({
                        "id": vid,
                        "text": full_text,
                        "original": original,
                        "translation": translation,
                        "book": book,
                        "chapter": ch_title,
                        "chapter_id": ch_id,
                        "verse_no": vid,
                        "source": f"《{book}·{ch_title}》",
                        "keywords": keywords,
                        "doc_type": "verse",
                    })
            logger.info(f"文件回退索引加载完成: {len(self._file_index)} 条经文")
        except Exception as e:
            logger.warning(f"加载文件回退索引失败: {e}")
            self._file_index = []

    def _load_commentary_index(self):
        """从 backend/data/commentaries/lunyu_zhuxi.json 加载朱熹注疏到内存索引"""
        try:
            # 注疏文件位于 backend/data/commentaries/
            comm_path = Path(__file__).resolve().parents[2] / "data" / "commentaries" / "lunyu_zhuxi.json"
            if not comm_path.exists():
                logger.info(f"注疏数据文件不存在: {comm_path}（可选功能）")
                return
            with open(comm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("commentaries", []):
                vid = item.get("verse_id", "")
                original = item.get("original", "")
                commentary = item.get("commentary", "")
                chapter = item.get("chapter", "")
                source = item.get("source", "朱熹《论语集注》")
                # 完整文档内容
                full_text = f"【篇章】{chapter} 【原文】{original} 【注疏】{commentary}"
                self._commentary_index.append({
                    "id": f"comm_{vid}",
                    "verse_id": vid,
                    "text": full_text,
                    "original": original,
                    "commentary": commentary,
                    "chapter": chapter,
                    "source": source,
                    "keywords": self._extract_keywords(original) + self._extract_keywords(commentary),
                    "doc_type": "commentary",
                })
            logger.info(f"注疏索引加载完成: {len(self._commentary_index)} 条注疏")
        except Exception as e:
            logger.warning(f"加载注疏索引失败: {e}")
            self._commentary_index = []

    def _load_debate_classic_index(self):
        """加载百家论道专用经典语料，按 sage_key 隔离索引。"""
        try:
            data_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "debate_classics.json"
            if not data_path.exists():
                logger.warning(f"百家论道经典语料不存在: {data_path}")
                return
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            classics = data.get("classics", {})
            for sage_key, classic in classics.items():
                book = classic.get("book", "")
                entries = []
                for verse in classic.get("verses", []):
                    original = verse.get("original", "")
                    if not original:
                        continue
                    keywords = verse.get("keywords", [])
                    translation = verse.get("translation", "")
                    keyword_text = " ".join(keywords)
                    full_text = (
                        f"【经典】{book} 【篇章】{verse.get('chapter', '')} "
                        f"【原文】{original} 【译文】{translation}"
                    )
                    if keyword_text:
                        full_text += f" 【关键词】{keyword_text}"
                    entries.append({
                        "id": verse.get("id", ""),
                        "sage_key": sage_key,
                        "text": full_text,
                        "original": original,
                        "translation": translation,
                        "book": book,
                        "chapter": verse.get("chapter", ""),
                        "source": verse.get("source", book),
                        "keywords": keywords,
                        "keywords_text": keyword_text,
                        "doc_type": "verse",
                    })
                if entries:
                    self._debate_classic_index[sage_key] = entries
            logger.info(
                "百家论道经典语料加载完成: %s",
                {key: len(value) for key, value in self._debate_classic_index.items()},
            )
        except Exception as e:
            logger.warning(f"加载百家论道经典语料失败: {e}")
            self._debate_classic_index = {}

    def _file_keyword_search(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """chromadb 不可用时的关键词匹配检索（含注疏索引 + 同义词扩展）"""
        if not self._file_index:
            return []
        # 同义词扩展：把现代词汇映射为古文关键词
        expanded_query = self._expand_synonyms(query)
        query_lower = query.lower()
        scored = []
        # 检索经文索引
        for item in self._file_index:
            score = 0.0
            # 关键词命中
            for kw in item.get("keywords", []):
                if kw in query or kw in expanded_query:
                    score += 2.0
            # 原文包含查询片段
            original = item.get("original", item.get("text", ""))
            if query in original:
                score += 3.0
            # 查询包含原文片段（子串匹配）
            for seg in self._extract_keywords(query) + self._extract_keywords(expanded_query):
                if seg in original or seg in item.get("text", ""):
                    score += 1.0
            if score > 0:
                scored.append({**item, "similarity": min(score / 5.0, 1.0)})
        # 检索注疏索引
        for item in self._commentary_index:
            score = 0.0
            for kw in item.get("keywords", []):
                if kw in query or kw in expanded_query:
                    score += 1.5
            original = item.get("original", "")
            commentary = item.get("commentary", "")
            if query in original:
                score += 2.0
            for seg in self._extract_keywords(query):
                if seg in original or seg in commentary:
                    score += 0.8
            if score > 0:
                scored.append({**item, "similarity": min(score / 5.0, 1.0)})
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    def _debate_keyword_search(
        self,
        sage_key: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """在指定圣贤自己的经典语料中检索。"""
        index = self._debate_classic_index.get(sage_key, [])
        if not index:
            return []

        expanded_query = self._expand_synonyms(query)
        query_terms = self._extract_keywords(query) + self._extract_keywords(expanded_query)
        scored = []
        for item in index:
            score = 0.0
            original = item.get("original", "")
            translation = item.get("translation", "")
            text = item.get("text", "")
            for kw in item.get("keywords", []):
                if kw in query or kw in expanded_query:
                    score += 3.0
            if query and (query in original or query in translation or query in text):
                score += 4.0
            for term in query_terms:
                if term in original:
                    score += 1.5
                elif term in translation or term in text:
                    score += 1.0

            # P0R-02 / C3：原先对 score == 0 的条目兜底为 0.25 并无条件 append，
            # 使完全无关的查询（实测 'asdfghjkl' 各派均返回 3 条 sims=0.0，
            # 「如何面对亲人的离世」四派各返回 3 条）也得到「本派原典证据」。
            # 这让「检索不到」在结构上不可达，使 PROJECT-BRIEF 第十二章的
            # `insufficient_evidence` 永远无法触发，直接违背核心承诺
            # 「找不到，就不硬编」。
            # 现在只保留有真实词面命中的条目；无命中则返回空列表，
            # 由上层走 insufficient_evidence / 拒答路径。
            if score <= 0:
                continue

            scored.append({**item, "similarity": min(score / 8.0, 1.0)})

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    def _expand_synonyms(self, query: str) -> str:
        """同义词扩展：把现代词汇映射为古文关键词，拼接成扩展查询"""
        expanded_parts = [query]
        for modern_word, ancient_words in self.SYNONYM_MAP.items():
            if modern_word in query:
                expanded_parts.extend(ancient_words)
        return " ".join(expanded_parts)

    def _build_debate_classic_documents(self) -> tuple[List[str], List[str], List[Dict[str, Any]]]:
        """把百家论道经典语料转成可写入 ChromaDB 的文档。"""
        ids: List[str] = []
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for sage_key, entries in self._debate_classic_index.items():
            for item in entries:
                verse_id = item.get("id", "")
                original = item.get("original", "")
                if not verse_id or not original:
                    continue
                doc_id = f"debate_{sage_key}_{verse_id}"
                ids.append(doc_id)
                texts.append(item.get("text", original))
                metadatas.append({
                    "scope": "debate_classic",
                    "sage_key": sage_key,
                    "book": item.get("book", ""),
                    "chapter": item.get("chapter", ""),
                    "verse_id": verse_id,
                    "verse_no": verse_id,
                    "original": original[:200],
                    "translation": item.get("translation", "")[:200],
                    "source": item.get("source", "未知"),
                    "keywords": item.get("keywords_text", ""),
                    "doc_type": item.get("doc_type", "verse"),
                })

        return ids, texts, metadatas

    def _debate_vector_search(
        self,
        sage_key: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """在 ChromaDB 中按 sage_key 过滤检索百家论道专属经典。

        P0R-02 / C3（后半）：原实现把向量检索结果**全部**返回，没有任何相关性
        下限，因此完全无关的问题也会拿到若干条相似度≈0 的「本派证据」，
        使 ``insufficient_evidence`` 在 debate 路径结构上不可达。

        现按相关性下限过滤。阈值依据（本地 hash embedding 实测原始相似度）：

            有真实关联的现代问题（brief ch.7/P0 要求必须能检索到）：
               我该不该躺平      -> confucius 0.165 / laozi 0.143 / mozi 0.106 / hanfeizi 0.109
            语料无支撑、应拒答的问题（brief ch.12 要求不硬编）：
               如何面对亲人的离世 -> 最高 0.092
               asdfghjkl          -> 最高 0.071
               孔子怎么看职场PUA   -> 最高 0.140（注意：此例与合法问题区间重叠）
               韩非子会建议我辞职吗 -> 最高 0.152（同上）

        说明：由于 hash embedding 非语义，两类查询的相似度**存在重叠区**
        （约 0.10–0.16），单靠阈值无法完美区分。这里取 ``DEBATE_MIN_SIMILARITY``
        作为保守下限，只滤掉明显无关联的条目（≈0 与 <0.10），
        保留「现代问题→古典思想」的可达性；真正的语义区分需 PHASE 4
        的语义 embedding + reranker，属后续阶段范围，不在本修复内假装达成。
        """
        if self.collection is None:
            return []

        expanded_query = self._expand_synonyms(query)
        try:
            results = self.collection.query(
                query_texts=[expanded_query],
                n_results=top_k,
                where={
                    "$and": [
                        {"scope": {"$eq": "debate_classic"}},
                        {"sage_key": {"$eq": sage_key}},
                    ],
                },
                include=["documents", "metadatas", "distances"],
            )
            formatted = self._format_results(results)
        except Exception as e:
            logger.warning("百家论道向量检索失败，降级为本派关键词检索: %s", e)
            return []

        filtered = [
            item for item in formatted
            if item.get("similarity", 0.0) >= self.DEBATE_MIN_SIMILARITY
        ]
        if not filtered and formatted:
            logger.debug(
                "百家论道向量检索无达到相关性下限的条目（sage=%s, 候选=%d, 最高=%.4f < %.4f），返回空",
                sage_key,
                len(formatted),
                max((i.get("similarity", 0.0) for i in formatted), default=0.0),
                self.DEBATE_MIN_SIMILARITY,
            )
        return filtered

    def _format_debate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """把百家论道检索结果统一格式化为 verses/commentaries。"""
        verses = []
        seen_ids = set()
        for item in results:
            meta = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else item
            verse_id = meta.get("verse_id", meta.get("id", ""))
            if verse_id in seen_ids:
                continue
            seen_ids.add(verse_id)
            original = meta.get("original", item.get("original", ""))
            translation = meta.get("translation", item.get("translation", ""))
            verses.append({
                "verse_id": verse_id,
                "original": original,
                "translation": translation,
                "chapter": meta.get("chapter", item.get("chapter", "")),
                "source": meta.get("source", item.get("source", "未知")),
                "similarity": item.get("similarity", 0.0),
            })
        return {"verses": verses, "commentaries": []}

    def _collection_has_debate_classics(self) -> bool:
        """判断现有 Chroma collection 是否已包含百家论道专属经典。"""
        if self.collection is None:
            return False
        try:
            rows = self.collection.get(
                where={"scope": "debate_classic"},
                limit=1,
                include=["metadatas"],
            )
            return bool(rows.get("ids"))
        except Exception as e:
            logger.info("检查百家论道向量索引失败，将重建索引: %s", e)
            return False

    def _clear_collection(self) -> None:
        """清空当前 Chroma collection，用于 force=True 的确定性重建。"""
        if self.collection is None:
            return
        try:
            rows = self.collection.get(include=[])
            ids = rows.get("ids", [])
            if ids:
                self.collection.delete(ids=ids)
        except Exception as e:
            logger.warning("清空 Chroma collection 失败，将继续 upsert 覆盖: %s", e)

    # ----------------------------------------------------------
    # 索引构建：从 data/processed/lunyu.json 与各派经典构建向量索引
    # ----------------------------------------------------------
    def build_index(self, force: bool = False) -> int:
        """构建向量索引。
        
        - 文档内容格式：【篇章】{chapter_title} 【原文】{original} 【译文】{translation} 【注释】{annotations}
        - 文档 metadata：{verse_id, chapter_id, chapter_title, original, translation, source, doc_type}
        - 同时索引注疏语料（朱熹《论语集注》）
        - 同时索引百家论道各派经典语料，metadata 标注 scope/sage_key 以便按派过滤
        - force=True: 强制重建（先清空再写入）
        - 若索引已存在且非强制，则跳过
        返回写入的文档数。
        """
        # chromadb 不可用时，文件回退索引已在 __init__ 中加载
        if self.collection is None:
            logger.info("chromadb 不可用，跳过向量索引构建（使用文件回退索引）")
            return len(self._file_index) + len(self._commentary_index)

        if force:
            self._clear_collection()

        # 已有数据且非强制重建
        if not force and self.collection.count() > 0 and self._collection_has_debate_classics():
            logger.info(f"向量索引已存在（{self.collection.count()} 条），跳过构建")
            return self.collection.count()

        # 读取经文数据
        try:
            data_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "lunyu.json"
            if not data_path.exists():
                logger.warning(f"经文数据文件不存在: {data_path}")
                return 0
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"读取经文数据失败: {e}")
            return 0

        book = data.get("book", "论语")
        ids, texts, metadatas = [], [], []
        for chapter in data.get("chapters", []):
            ch_id = chapter.get("chapter_id", 0)
            ch_title = chapter.get("chapter_title", "")
            for verse in chapter.get("verses", []):
                vid = verse.get("verse_id", "")
                original = verse.get("original", "")
                translation = verse.get("translation", "")
                annotations = verse.get("annotations", [])
                if not vid or not original:
                    continue
                # 注释格式化
                ann_text = "；".join(
                    f"{a.get('char','')}({a.get('pinyin','')}):{a.get('meaning','')}"
                    for a in annotations
                ) if annotations else ""
                keyword_text = " ".join(verse.get("keywords", []))
                # 完整文档内容
                doc_text = f"【篇章】{ch_title} 【原文】{original} 【译文】{translation}"
                if ann_text:
                    doc_text += f" 【注释】{ann_text}"
                if keyword_text:
                    doc_text += f" 【关键词】{keyword_text}"
                ids.append(vid)
                texts.append(doc_text)
                metadatas.append({
                    "scope": "sage_chat",
                    "book": book,
                    "chapter": ch_title,
                    "chapter_id": str(ch_id),
                    "verse_id": vid,
                    "verse_no": vid,
                    "original": original[:200],  # chromadb metadata 值不宜过长
                    "translation": translation[:200],
                    "source": f"《{book}·{ch_title}》",
                    "keywords": keyword_text,
                    "doc_type": "verse",
                })

        # 读取注疏数据并加入索引
        commentary_count = 0
        try:
            comm_path = Path(__file__).resolve().parents[2] / "data" / "commentaries" / "lunyu_zhuxi.json"
            if comm_path.exists():
                with open(comm_path, "r", encoding="utf-8") as f:
                    comm_data = json.load(f)
                for item in comm_data.get("commentaries", []):
                    vid = item.get("verse_id", "")
                    original = item.get("original", "")
                    commentary = item.get("commentary", "")
                    chapter = item.get("chapter", "")
                    source = item.get("source", "朱熹《论语集注》")
                    if not vid or not commentary:
                        continue
                    doc_text = f"【篇章】{chapter} 【原文】{original} 【注疏】{commentary}"
                    ids.append(f"comm_{vid}")
                    texts.append(doc_text)
                    metadatas.append({
                        "scope": "sage_chat",
                        "book": book,
                        "chapter": chapter,
                        "verse_id": vid,
                        "verse_no": vid,
                        "original": original[:200],
                        "commentary": commentary[:200],
                        "source": source,
                        "doc_type": "commentary",
                    })
                    commentary_count += 1
            else:
                logger.info("注疏数据文件不存在，跳过注疏索引构建")
        except Exception as e:
            logger.warning(f"读取注疏数据失败（不影响经文索引）: {e}")

        debate_ids, debate_texts, debate_metadatas = self._build_debate_classic_documents()
        ids.extend(debate_ids)
        texts.extend(debate_texts)
        metadatas.extend(debate_metadatas)

        if not ids:
            logger.warning("经文数据为空，未构建索引")
            return 0

        count = self.index_documents(ids, texts, metadatas)
        debate_count = len(debate_ids)
        logger.info(
            "向量索引构建完成: %s 条（学习经文 %s 条，注疏 %s 条，百家论道经典 %s 条）",
            count,
            count - commentary_count - debate_count,
            commentary_count,
            debate_count,
        )
        return count

    @property
    def is_available(self) -> bool:
        """RAG 服务是否可用（chromadb 或文件索引）

        P0R-03 / B2：原实现只判断 ``self.collection is not None``，
        因此「collection 存在但为 0 条」也会被报成可用 —— 空索引时
        main.py 的 ``healthy = llm_available and rag_available`` 会误报健康，
        而实际检索什么都返回不了。

        现改为要求**真实有数据**：collection 的 count() > 0，或有文件回退索引。
        count() 读取失败（例如 HNSW 段暂不可读）时保守返回 False，
        宁可报「不可用」也不要给出虚假的可用信号。
        """
        if len(self._file_index) > 0:
            return True
        if self.collection is None:
            return False
        try:
            return self.collection.count() > 0
        except Exception as e:
            logger.warning("检查 RAG 可用性时读取 collection.count() 失败: %s", e)
            return False

    # ----------------------------------------------------------
    # 索引：批量写入文档
    # ----------------------------------------------------------
    def index_documents(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> int:
        """批量索引文档到 ChromaDB"""
        if not ids or self.collection is None:
            return 0
        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info(f"RAG 索引: upsert {len(ids)} 条，当前共 {self.collection.count()} 条")
        return len(ids)

    def index_verse(
        self,
        verse_id: str,
        text: str,
        book: str,
        chapter: str,
        verse_no: int,
    ) -> None:
        """索引单条经文"""
        self.index_documents(
            ids=[verse_id],
            texts=[text],
            metadatas=[{
                "book": book,
                "chapter": chapter,
                "verse_no": verse_no,
                "source": f"《{book}·{chapter}》",
            }],
        )

    # ----------------------------------------------------------
    # 检索：向量检索
    # ----------------------------------------------------------
    def vector_search(
        self,
        query: str,
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        """纯向量检索"""
        if self.collection is None:
            # chromadb 不可用，降级为文件关键词检索
            return self._file_keyword_search(query, top_k=top_k or settings.RAG_TOP_K)
        top_k = top_k or settings.RAG_TOP_K
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            return self._format_results(results)
        except Exception as e:
            logger.warning(f"向量检索失败，降级为关键词检索: {e}")
            return self._file_keyword_search(query, top_k=top_k)

    # ----------------------------------------------------------
    # 检索：关键词检索（简易 BM25-like）
    # ----------------------------------------------------------
    def keyword_search(
        self,
        query: str,
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        """关键词检索：用 Chroma 的 where-document 过滤"""
        if self.collection is None:
            # chromadb 不可用，降级为文件关键词检索
            return self._file_keyword_search(query, top_k=top_k or settings.RAG_TOP_K)
        top_k = top_k or settings.RAG_TOP_K
        # 取查询中的关键词（中文按字拆分 + 简单去停用词）
        keywords = self._extract_keywords(query)
        if not keywords:
            return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k * 2,
                where_document={"$contains": keywords[0]},
                include=["documents", "metadatas", "distances"],
            )
            return self._format_results(results)[:top_k]
        except Exception as e:
            logger.warning(f"关键词检索失败: {e}")
            return []

    # ----------------------------------------------------------
    # 检索：混合检索（向量 + 关键词）
    # ----------------------------------------------------------
    def hybrid_search(
        self,
        query: str,
        top_k: int = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[RAGReference]:
        """混合检索：向量检索 + 关键词检索融合
        
        - 向量检索权重 0.7，关键词检索权重 0.3
        - 去重后按加权相关度排序
        - 返回 top_k 条最相关的经文
        """
        top_k = top_k or settings.RAG_TOP_K
        try:
            vec_results = self.vector_search(query, top_k=top_k)
            kw_results = self.keyword_search(query, top_k=top_k)
        except Exception as e:
            logger.warning(f"混合检索异常，返回空列表: {e}")
            return []

        # 合并去重（按 text 去重），加权融合
        merged: Dict[str, Dict[str, Any]] = {}
        for r in vec_results:
            text = r["text"]
            r["weighted_score"] = r["similarity"] * vector_weight
            if text not in merged or r["weighted_score"] > merged[text]["weighted_score"]:
                merged[text] = r
        for r in kw_results:
            text = r["text"]
            r["weighted_score"] = r["similarity"] * keyword_weight
            if text in merged:
                # 两路都命中：取加权之和
                merged[text]["weighted_score"] += r["weighted_score"]
            else:
                merged[text] = r

        ranked = sorted(merged.values(), key=lambda x: x.get("weighted_score", 0), reverse=True)
        return [
            RAGReference(
                text=r["text"],
                source=r["metadata"].get("source", "未知") if isinstance(r.get("metadata"), dict) else r.get("source", "未知"),
                chapter=r["metadata"].get("chapter") if isinstance(r.get("metadata"), dict) else r.get("chapter"),
                verse_no=r["metadata"].get("verse_no") if isinstance(r.get("metadata"), dict) else r.get("verse_no"),
                similarity=r["similarity"],
            )
            for r in ranked[:top_k]
        ]

    # ----------------------------------------------------------
    # 检索（高层）：返回引用 + 上下文文本
    # ----------------------------------------------------------
    async def retrieve(self, query: str, top_k: int = None) -> List[RAGReference]:
        """对外检索接口，返回 RAGReference 列表"""
        try:
            return self.hybrid_search(query, top_k=top_k)
        except Exception as e:
            logger.warning(f"RAG retrieve 异常，返回空列表: {e}")
            return []

    async def retrieve_for_sage_chat(
        self, query: str, top_k: int = 5
    ) -> Dict[str, Any]:
        """针对"与圣贤对话"场景的专用检索。
        
        - 把用户问题改写为检索 query（同义词扩展）
        - 返回结果包含原文、译文、出处、注疏
        - 返回结构: {"verses": [...], "commentaries": [...]}
        
        Returns:
            {
                "verses": [{"verse_id", "original", "translation", "chapter", "source", "similarity"}],
                "commentaries": [{"verse_id", "original", "commentary", "chapter", "source", "similarity"}],
            }
        """
        # 同义词扩展改写 query
        expanded_query = self._expand_synonyms(query)
        
        # 检索经文和注疏
        results = []
        try:
            if self.collection is not None:
                # chromadb 可用：向量检索
                results = self.vector_search(expanded_query, top_k=top_k * 2)
            else:
                # 文件回退检索
                results = self._file_keyword_search(expanded_query, top_k=top_k * 2)
        except Exception as e:
            logger.warning(f"retrieve_for_sage_chat 检索异常: {e}")
            results = []

        # 分离经文和注疏
        verses = []
        commentaries = []
        seen_verse_ids = set()
        
        for r in results:
            meta = r.get("metadata", {}) if isinstance(r.get("metadata"), dict) else r
            doc_type = meta.get("doc_type", r.get("doc_type", "verse"))
            similarity = r.get("similarity", 0.0)
            
            if doc_type == "commentary":
                vid = meta.get("verse_id", r.get("verse_id", ""))
                commentaries.append({
                    "verse_id": vid,
                    "original": meta.get("original", r.get("original", "")),
                    "commentary": meta.get("commentary", r.get("commentary", "")),
                    "chapter": meta.get("chapter", r.get("chapter", "")),
                    "source": meta.get("source", r.get("source", "朱熹《论语集注》")),
                    "similarity": similarity,
                })
            else:
                vid = meta.get("verse_id", meta.get("verse_no", r.get("verse_no", "")))
                if vid in seen_verse_ids:
                    continue
                seen_verse_ids.add(vid)
                # 优先用 metadata 中的完整原文/译文，否则从 text 中提取
                original = meta.get("original", "")
                translation = meta.get("translation", "")
                if not original:
                    # 从 text 字段提取（文件回退模式）
                    original = r.get("original", r.get("text", ""))
                    translation = r.get("translation", "")
                verses.append({
                    "verse_id": vid,
                    "original": original,
                    "translation": translation,
                    "chapter": meta.get("chapter", r.get("chapter", "")),
                    "source": meta.get("source", r.get("source", "未知")),
                    "similarity": similarity,
                })
        
        # 各取 top_k
        verses = sorted(verses, key=lambda x: x["similarity"], reverse=True)[:top_k]
        commentaries = sorted(commentaries, key=lambda x: x["similarity"], reverse=True)[:top_k]
        
        return {"verses": verses, "commentaries": commentaries}

    async def retrieve_for_debate_sage(
        self,
        sage_key: str,
        query: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """百家论道专用检索：只返回该圣贤/派别自己的经典语料。"""
        results = self._debate_vector_search(sage_key, query, top_k=top_k)
        if results:
            return self._format_debate_results(results)

        results = self._debate_keyword_search(sage_key, query, top_k=top_k)

        # 孔子沿用现有《论语》学习索引；其他圣贤必须使用专属语料。
        #
        # P0R-02 / C3 + C2：原实现无条件 `return await self.retrieve_for_sage_chat(...)`，
        # 而该路径是**无学派过滤**的全局检索（实测「如何面对失败」在孔子路径
        # 把《韩非子·外储说左上》排到第一位，相似度 0.115，属跨派泄露，
        # 违反 GATE-6 School Leakage < 1%）。现做两层过滤：
        #   1) 相关性下限 DEBATE_MIN_SIMILARITY（使 insufficient_evidence 可达）
        #   2) **学派白名单**：source 必须属于 SAGE_CLASSICS[sage_key]，
        #      与 citation_validator 的既有白名单保持同一真值来源。
        # 注意：这不会破坏「现代问题→古典思想」的可达性 —— 合法现代问题
        # （如「我该不该躺平」）命中的是《论语》，仍在白名单内。
        if not results and sage_key == "confucius":
            fallback = await self.retrieve_for_sage_chat(query, top_k=top_k)
            allowed_books = self._allowed_books_for(sage_key)

            def _keep(item: Dict[str, Any]) -> bool:
                if item.get("similarity", 0.0) < self.DEBATE_MIN_SIMILARITY:
                    return False
                src = str(item.get("source", ""))
                # 白名单为空（未登记的 sage）时不做学派过滤，避免误伤
                return (not allowed_books) or any(b in src for b in allowed_books)

            filtered_verses = [v for v in fallback.get("verses", []) if _keep(v)]
            filtered_commentaries = [c for c in fallback.get("commentaries", []) if _keep(c)]
            if not filtered_verses and not filtered_commentaries:
                logger.debug(
                    "孔子路径回退检索无通过相关性+学派白名单的条目（query=%r），返回空",
                    query[:30],
                )
            return {"verses": filtered_verses, "commentaries": filtered_commentaries}

        return self._format_debate_results(results)

    @staticmethod
    def _allowed_books_for(sage_key: str) -> List[str]:
        """返回该圣贤/学派允许的典籍名（用于跨派泄露防护）。

        单一真值来源：复用 ``citation_validator.SAGE_CLASSICS``，
        避免在 RAG 层再维护一份会与校验层分叉的白名单。
        未登记的 sage 返回空列表（调用方据此跳过学派过滤）。
        """
        try:
            from app.services.citation_validator import SAGE_CLASSICS

            return list(SAGE_CLASSICS.get(sage_key, []))
        except Exception:  # 导入失败不应使检索整体失败
            return []

    def build_context_text(self, refs: List[RAGReference]) -> str:
        """把检索结果格式化为可注入 prompt 的上下文文本"""
        if not refs:
            return "（无匹配原文）"
        lines = []
        for i, r in enumerate(refs, 1):
            lines.append(f"[{i}] 出处：{r.source}（相关度 {r.similarity:.2f}）\n原文：{r.text}")
        return "\n\n".join(lines)

    def build_sage_chat_context(self, sage_result: Dict[str, Any]) -> str:
        """把 retrieve_for_sage_chat 的结果格式化为可注入 prompt 的上下文文本。
        
        区分"原文"和"注疏"，供 LLM 分别引用。
        """
        verses = sage_result.get("verses", [])
        commentaries = sage_result.get("commentaries", [])
        
        if not verses and not commentaries:
            return "（无匹配原文）"
        
        lines = []
        if verses:
            lines.append("=== 检索到的《论语》原文 ===")
            for i, v in enumerate(verses, 1):
                lines.append(
                    f"[原文{i}] 出处：{v['source']}（相关度 {v['similarity']:.2f}）\n"
                    f"原文：{v['original']}\n"
                    f"译文：{v['translation']}"
                )
        if commentaries:
            lines.append("\n=== 检索到的注疏（朱熹《论语集注》）===")
            for i, c in enumerate(commentaries, 1):
                lines.append(
                    f"[注疏{i}] 出处：{c['source']}（相关度 {c['similarity']:.2f}）\n"
                    f"原文：{c['original']}\n"
                    f"注疏：{c['commentary']}"
                )
        return "\n\n".join(lines)

    def build_debate_context(self, sage_key: str, sage_result: Dict[str, Any]) -> str:
        """把百家论道专用检索结果格式化为 prompt 上下文。"""
        verses = sage_result.get("verses", [])
        commentaries = sage_result.get("commentaries", [])
        if not verses and not commentaries:
            return "（无匹配原文）"

        book_name = verses[0]["source"].strip("《》").split("·", 1)[0] if verses else "本派经典"
        lines = []
        if verses:
            lines.append(f"=== 检索到的《{book_name}》原文 ===")
            for i, v in enumerate(verses, 1):
                lines.append(
                    f"[原文{i}] 出处：{v['source']}（相关度 {v['similarity']:.2f}）\n"
                    f"原文：{v['original']}\n"
                    f"译文：{v['translation']}"
                )
        if commentaries:
            lines.append("\n=== 检索到的本派注疏 ===")
            for i, c in enumerate(commentaries, 1):
                lines.append(
                    f"[注疏{i}] 出处：{c['source']}（相关度 {c['similarity']:.2f}）\n"
                    f"原文：{c['original']}\n"
                    f"注疏：{c['commentary']}"
                )
        return "\n\n".join(lines)

    def is_low_confidence(self, refs: List[RAGReference]) -> bool:
        """判断是否低置信度（最高相关度低于阈值）"""
        if not refs:
            return True
        return refs[0].similarity < settings.RAG_SIMILARITY_THRESHOLD

    # ----------------------------------------------------------
    # 内部工具
    # ----------------------------------------------------------
    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """把 ChromaDB 的 query 结果格式化"""
        if not results or not results.get("documents"):
            return []
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]
        out = []
        for doc, meta, dist in zip(docs, metas, dists):
            # cosine distance -> similarity
            sim = max(0.0, 1.0 - dist)
            out.append({
                "text": doc,
                "metadata": meta or {},
                "similarity": sim,
            })
        return out

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """关键词提取：去掉常见虚词，取较长的字组 + 2-gram
        
        支持中文无空格分词：除了按标点分段外，还生成 2-gram 字组用于子串匹配。
        """
        stop = {"的", "了", "是", "在", "和", "与", "之", "于", "而", "也", "曰", "者", "乎",
                "我", "你", "他", "她", "它", "们", "这", "那", "怎", "么", "什", "为",
                "办", "呢", "啊", "吧", "吗", "不", "有", "无", "要", "会", "能", "可",
                "以", "及", "或", "并", "但", "如", "果", "因", "所", "以", "其"}
        keywords = []
        # 按标点和空格分段
        segments = re.split(r"[，。！？；：\s、""''（）()【】]+", text)
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            # 整段作为关键词（去掉停用词后）
            if len(seg) >= 2 and seg not in stop:
                keywords.append(seg)
            # 生成 2-gram 字组（适用于中文无空格文本）
            # 去掉单字停用词后的连续字组
            chars = [c for c in seg if c not in stop and c.strip()]
            for i in range(len(chars) - 1):
                bigram = chars[i] + chars[i + 1]
                if bigram not in keywords:
                    keywords.append(bigram)
            # 单字关键词（用于古文匹配，如"学""仁""礼"等）
            for c in seg:
                if c not in stop and len(c.strip()) > 0 and c not in keywords:
                    # 只保留有意义的单字（排除数字、字母）
                    if '\u4e00' <= c <= '\u9fff':
                        keywords.append(c)
        return keywords


# 全局单例
_rag: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """获取 RAG 服务单例（懒加载）"""
    global _rag
    if _rag is None:
        _rag = RAGService()
    return _rag
