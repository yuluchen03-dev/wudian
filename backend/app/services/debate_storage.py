"""
悟典 - 百家论道辩论持久化存储

职责：
- 持久化辩论会话到文件系统
- 提供会话加载和缓存
- 支持会话历史查询
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List

from app.schemas.debate import DebateSession
from app.core.config import settings

logger = logging.getLogger(__name__)


class DebateStorage:
    """辩论会话持久化（文件存储）"""
    
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            storage_dir = settings.DEBATE_STORAGE_DIR
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, DebateSession] = {}
    
    def save(self, session: DebateSession) -> None:
        """保存会话到文件"""
        self._cache[session.id] = session
        path = self.storage_dir / f"{session.id}.json"
        with open(path, "w", encoding="utf-8") as f:
            f.write(session.model_dump_json(indent=2))
        logger.info(f"保存会话: {session.id}")
    
    def load(self, session_id: str) -> Optional[DebateSession]:
        """加载会话"""
        if session_id in self._cache:
            return self._cache[session_id]
        
        path = self.storage_dir / f"{session_id}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            session = DebateSession(**data)
            self._cache[session_id] = session
            logger.info(f"加载会话: {session_id}")
            return session
        
        return None
    
    def list_sessions(self, limit: int = 20) -> List[DebateSession]:
        """列出最近的会话"""
        sessions = []
        for path in sorted(self.storage_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(DebateSession(**data))
            except Exception as e:
                logger.error(f"加载会话失败 {path}: {e}")
        return sessions
    
    def delete(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._cache:
            del self._cache[session_id]
        
        path = self.storage_dir / f"{session_id}.json"
        if path.exists():
            path.unlink()
            logger.info(f"删除会话: {session_id}")
            return True
        
        return False


# 全局实例
debate_storage = DebateStorage()