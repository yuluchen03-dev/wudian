"""
SAFETY-001：生产 ChromaDB 索引隔离的回归测试。

背景
----
``backend/chroma_db`` 是生产数据。测试若在未隔离的情况下打开它，
``build_index(force=True)``（见 ``tests/test_debate_classic_rag.py:20,51``）
会**清空并重建**生产 collection。2026-10-08 已实际发生过一次索引损坏。

本文件断言：
1. 测试进程使用的向量索引目录**不是**生产目录；
2. ``conftest.py`` 是**强制**指定隔离目录，而不是 ``setdefault``
   （否则环境里已有的 ``CHROMA_PERSIST_DIR`` 会被沿用，可能指向生产）；
3. 隔离目录是**相对路径且位于 backend 之下**——这不是洁癖：
   ``tests/test_hackathon_readiness.py:15-24`` 断言配置解析结果
   ``startswith(backend_root)``，用绝对临时路径会让该断言失败；
4. 完整性校验工具**确实能**发现内容变化（对工具本身做反向测试，
   避免"永远返回无差异"的假安全）。
"""
from __future__ import annotations

import os
from pathlib import Path

from _chroma_fingerprint import (
    assert_content_unchanged,
    content_fingerprint,
    file_fingerprint,
    production_chroma_dir,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _resolved(value: str) -> Path:
    """按 config._resolve_backend_path 的规则解析（相对路径基于 backend）。"""
    p = Path(value)
    return (p if p.is_absolute() else (BACKEND_DIR / p)).resolve()


class TestNoProductionChroma:
    """确保测试永不打开生产索引。"""

    def test_no_test_uses_production_chroma(self):
        """测试环境的索引目录必须 != 生产目录。"""
        raw = os.environ.get("CHROMA_PERSIST_DIR")
        assert raw, "conftest 必须显式设置 CHROMA_PERSIST_DIR"
        active = _resolved(raw)
        prod = production_chroma_dir(BACKEND_DIR)
        assert active != prod, (
            f"测试正在使用**生产**索引目录 {prod}；"
            f"这会在 build_index(force=True) 时清空生产数据。"
        )

    def test_isolation_is_forced_not_inherited(self):
        """隔离必须是强制的：隔离目录必须带本进程 PID 后缀。

        若 conftest 用 setdefault 而环境里预先设了别的值，
        这里就会拿到与 PID 无关的目录，从而暴露该漏洞。
        """
        raw = os.environ["CHROMA_PERSIST_DIR"]
        assert str(os.getpid()) in raw, (
            f"CHROMA_PERSIST_DIR={raw!r} 不含本进程 PID，"
            "说明隔离不是强制的（可能沿用了继承值）"
        )

    def test_isolated_dir_is_relative_under_backend(self):
        """隔离目录必须是相对路径且解析到 backend 之下。"""
        raw = os.environ["CHROMA_PERSIST_DIR"]
        assert not Path(raw).is_absolute(), (
            f"{raw!r} 是绝对路径；test_hackathon_readiness.py:15-24 会因此失败"
        )
        active = _resolved(raw)
        assert str(active).startswith(str(BACKEND_DIR)), (
            f"隔离目录 {active} 不在 backend 之下"
        )
        assert active != production_chroma_dir(BACKEND_DIR)

    def test_conftest_source_forces_assignment(self):
        """直接读 conftest 源码，确认没有回退成 setdefault。"""
        src = (BACKEND_DIR / "tests" / "conftest.py").read_text(encoding="utf-8")
        assert 'os.environ.setdefault("CHROMA_PERSIST_DIR"' not in src, (
            "conftest 又用回了 setdefault：继承来的 CHROMA_PERSIST_DIR 会被沿用，"
            "若它指向生产索引则测试会直接操作生产数据"
        )
        assert 'os.environ["CHROMA_PERSIST_DIR"] =' in src, (
            "conftest 必须**强制赋值** CHROMA_PERSIST_DIR"
        )


class TestFingerprintTool:
    """完整性工具自身必须有效（反向测试，防止假安全）。"""

    def test_content_fingerprint_on_isolated_dir(self):
        """在隔离目录上取内容指纹（绝不指向生产目录）。"""
        active = _resolved(os.environ["CHROMA_PERSIST_DIR"])
        fp = content_fingerprint(active)
        assert isinstance(fp["doc_count"], int)
        assert len(fp["id_md5"]) == 32

    def test_assert_content_unchanged_detects_real_change(self):
        """工具必须能报出变化——否则就是"永远通过"的假安全。"""
        before = {"doc_count": 143, "id_md5": "a" * 32, "hnsw_segments": {"x": {"size": 1}}}
        same = {"doc_count": 143, "id_md5": "a" * 32, "hnsw_segments": {"x": {"size": 1}}}
        assert assert_content_unchanged(before, same) == []

        changed_count = dict(same, doc_count=142)
        assert assert_content_unchanged(before, changed_count), "条数变化必须被发现"

        changed_ids = dict(same, id_md5="b" * 32)
        assert assert_content_unchanged(before, changed_ids), "id 变化必须被发现"

        changed_seg = dict(same, hnsw_segments={"x": {"size": 999}})
        assert assert_content_unchanged(before, changed_seg), "HNSW 段变化必须被发现"

    def test_file_fingerprint_records_hnsw_segments(self):
        """文件级指纹必须记录 HNSW 段（生产损坏的可见证据）。"""
        active = _resolved(os.environ["CHROMA_PERSIST_DIR"])
        fp = file_fingerprint(active)
        assert "hnsw_segments" in fp
        # 隔离目录可能尚为空（未 build），此处只要求结构正确、不要求有条目
        assert isinstance(fp["hnsw_segments"], dict)

    def test_production_dir_is_not_the_isolated_dir(self):
        prod = production_chroma_dir(BACKEND_DIR)
        active = _resolved(os.environ["CHROMA_PERSIST_DIR"])
        assert prod.name == "chroma_db"
        assert prod != active


class TestEvalRunnerIsIsolated:
    """Eval 运行器同样必须默认隔离（SAFETY-001 覆盖 eval，不只覆盖 pytest）。"""

    def _src(self) -> str:
        p = BACKEND_DIR.parent / "eval" / "scripts" / "run_eval.py"
        assert p.exists(), f"找不到 {p}"
        return p.read_text(encoding="utf-8")

    def test_eval_defaults_to_isolated_chroma_copy(self):
        """run_eval.py 必须默认指向临时副本，而不是生产目录。"""
        src = self._src()
        assert "_isolate_chroma()" in src, "run_eval 必须默认隔离"
        assert "used_production" in src, "必须记录本次是否使用了生产索引"
        assert "copytree" in src, (
            "隔离应基于生产索引的**副本**，否则检索类指标会因空目录而恒为 0"
        )

    def test_eval_requires_explicit_flag_for_production(self):
        """使用生产索引必须显式开关，且附带读前/读后指纹校验。"""
        src = self._src()
        assert "--use-production-chroma" in src
        assert "assert_content_unchanged" in src, "读生产必须校验内容指纹"
