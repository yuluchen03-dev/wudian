"""
SAFETY-001：生产 ChromaDB 索引的指纹与完整性校验工具。

为什么需要它
------------
``backend/chroma_db`` 是**生产数据**。测试、Eval、审计、临时探针一旦在未隔离的
情况下打开它，就可能（a）清空重建（``build_index(force=True)``）或
（b）改写其字节。2026-10-08 已实际发生过一次索引损坏事故。

因此凡是**确实必须**读取生产索引的场合，都必须先记录指纹、后再次记录，
任何变化一律 FAIL 并立即报告，不得静默接受。

两类指纹（必须区分，否则会误判）
--------------------------------
1. :func:`file_fingerprint` —— **纯读文件字节**，不打开数据库。
   含 ``chroma.sqlite3`` 的 sha256 与 HNSW 段文件的大小/哈希。

2. :func:`content_fingerprint` —— 需要**打开集合**，给出条数与 id 指纹。
   ⚠️ 注意：chromadb 的 ``PersistentClient`` 在**打开/关闭时就会写入目录元数据**，
   即使只做只读查询，``chroma.sqlite3`` 的字节也会变化（2026-10-09 独立复核实测）。

因此「内容未变」的判据只能是 **content_fingerprint（条数 + id 指纹）**
与 **HNSW 段文件**，**不能**用 ``chroma.sqlite3`` 的 sha256——
后者因 chromadb 自身的固有行为而改变，属**已知且预期**，不是数据损坏。
本模块把这一区别显式编码，避免用错判据制造假警报或漏报真损坏。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "HNSW_SEGMENT_NAMES",
    "assert_content_unchanged",
    "content_fingerprint",
    "dumps",
    "file_fingerprint",
    "fingerprint_of_collection",
    "production_chroma_dir",
    "sha256_file",
]

HNSW_SEGMENT_NAMES = ("data_level0.bin", "header.bin", "length.bin", "link_lists.bin")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def production_chroma_dir(backend_dir: Optional[Path] = None) -> Path:
    """生产索引目录（``backend/chroma_db``）。

    与 ``config.py`` 的默认 ``CHROMA_PERSIST_DIR="./chroma_db"`` 同一解析规则：
    相对路径基于 backend 目录。
    """
    base = Path(backend_dir) if backend_dir else Path(__file__).resolve().parent.parent
    return (base / "chroma_db").resolve()


def file_fingerprint(persist_dir: str | Path) -> Dict[str, Any]:
    """文件级指纹：不打开数据库，纯读字节。"""
    base = Path(persist_dir)
    out: Dict[str, Any] = {"dir": str(base), "exists": base.exists()}
    sqlite = base / "chroma.sqlite3"
    if sqlite.exists():
        out["sqlite_sha256"] = sha256_file(sqlite)
        out["sqlite_size"] = sqlite.stat().st_size
    segments: Dict[str, Dict[str, Any]] = {}
    if base.exists():
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.name in HNSW_SEGMENT_NAMES:
                segments[str(p.relative_to(base))] = {
                    "size": p.stat().st_size,
                    "sha256": sha256_file(p),
                }
    out["hnsw_segments"] = segments
    return out


def fingerprint_of_collection(collection) -> Dict[str, Any]:
    """从**已有的** collection 对象取内容指纹（纯函数，不新建 client）。

    单独抽出这一层的原因：chromadb 在同一进程内对同一路径只允许一个
    ``PersistentClient``，且**设置不同即报错**
    （``ValueError: An instance of Chroma already exists ... with different settings``）。
    ``app.services.rag_service`` 已经用带自定义 embedding function 的设置打开了
    隔离目录，此时再新建一个默认设置的 client 就会冲突。因此优先复用已打开的
    collection。
    """
    ids = sorted(str(i) for i in collection.get(include=[])["ids"])
    return {
        "collection": getattr(collection, "name", "unknown"),
        "doc_count": len(ids),
        "id_md5": hashlib.md5("\n".join(ids).encode()).hexdigest(),
    }


def content_fingerprint(
    persist_dir: str | Path, collection: str = "wudian_verses",
) -> Dict[str, Any]:
    """内容级指纹：条数 + id md5。

    ⚠️ 打开集合会改写 ``chroma.sqlite3`` 的目录元数据（chromadb 固有行为），
    故本函数**不得**与其前的 ``file_fingerprint`` 混淆使用。

    优先复用 app 已打开的 collection；若 app 尚未初始化（例如独立脚本场景），
    才自行新建 client。
    """
    # 1) 优先复用 app 已打开的 collection（避免 chromadb 单例设置冲突）
    try:
        from app.services.rag_service import get_rag_service

        svc = get_rag_service()
        col = getattr(svc, "collection", None)
        if col is not None:
            return fingerprint_of_collection(col)
    except Exception:
        pass  # app 不可用 -> 走独立路径

    # 2) 独立路径：自行新建 client
    import chromadb

    client = chromadb.PersistentClient(path=str(persist_dir))
    return fingerprint_of_collection(client.get_collection(collection))


def assert_content_unchanged(
    before: Dict[str, Any], after: Dict[str, Any], *, label: str = "production chroma",
) -> List[str]:
    """比较两次**内容级**指纹；返回差异描述列表（空列表 = 未变）。

    只比较内容与 HNSW 段，**不比较** ``chroma.sqlite3`` 的 sha256（见模块 docstring）。
    """
    problems: List[str] = []
    if before.get("doc_count") != after.get("doc_count"):
        problems.append(
            f"{label}: doc_count 变化 {before.get('doc_count')} -> {after.get('doc_count')}"
        )
    if before.get("id_md5") != after.get("id_md5"):
        problems.append(
            f"{label}: id_md5 变化 {before.get('id_md5')} -> {after.get('id_md5')}"
        )
    b_seg = before.get("hnsw_segments") or {}
    a_seg = after.get("hnsw_segments") or {}
    if set(b_seg) != set(a_seg):
        problems.append(f"{label}: HNSW 段文件集合变化 {sorted(b_seg)} -> {sorted(a_seg)}")
    else:
        for name, meta in b_seg.items():
            if meta != a_seg.get(name):
                problems.append(f"{label}: HNSW 段 {name} 变化 {meta} -> {a_seg.get(name)}")
    return problems


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
