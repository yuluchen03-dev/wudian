"""
DSH-SA-004：``init_db.py`` 破坏性 ``clear_data`` 守卫的回归测试。

背景（安全缺陷 SA001-01）
------------------------
``backend/init_db.py`` 的 ``clear_data()`` 会对 **18 张表**执行
``DELETE FROM {table}``（含 ``users`` / ``notes`` / ``study_groups`` / ``verses``），
并在 ``main()`` 的「步骤 2」被**无条件**调用。原实现没有确认、没有 ``--yes``、
没有 dry-run、没有环境检查、也没有拒绝路径——只把目标打印出来（那是**告知**，不是
**守卫**）。于是 ``python init_db.py`` 会清空 ``DATABASE_URL`` 解析到的任何数据库。

本文件断言守卫是 **fail-closed** 的：
1. 生产形态目标（PostgreSQL / 远程 / backend 之外）必须**拒绝**；
2. 真实库文件名 ``wudian.db`` 即使给了 ``--yes`` 也必须**拒绝**；
3. 缺少显式意图时拒绝；
4. 拒绝路径**不执行任何 DELETE**（用假 session 计数 execute 调用）；
5. 拒绝信息里必须出现**解析后的真实目标**，让人看清被保护的是什么；
6. 合法开发路径（``*_dev.db`` + ``--yes``）**仍然放行**（负向对照）；
7. 守卫位于 ``clear_data`` 中**第一条 execute 之前**（源码顺序断言）。

所有测试只用**一次性 SQLite 目标**，绝不指向真实/生产数据库；本文件不建立任何
数据库连接（守卫是纯校验函数，不碰 session）。
"""
from __future__ import annotations

import ast
import asyncio
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import init_db  # noqa: E402
from init_db import (  # noqa: E402
    DestructiveOperationRefused,
    clear_data,
    ensure_destructive_allowed,
)


class _FakeSession:
    """只记录 execute 调用次数，绝不连接任何数据库。"""

    def __init__(self):
        self.executed: list[str] = []

    async def execute(self, stmt, *args, **kwargs):
        self.executed.append(str(stmt))

    async def commit(self):
        self.executed.append("COMMIT")


def _guard_with(url: str, env: str, *, confirmed: bool = False,
                monkeypatch=None) -> None:
    """在指定 DATABASE_URL / APP_ENV / 确认状态下运行守卫。"""
    fake_settings = mock.Mock()
    fake_settings.resolved_database_url = url
    fake_settings.APP_ENV = env
    monkeypatch.setattr(init_db, "settings", fake_settings)
    monkeypatch.setattr(init_db, "_CLI_CONFIRMED", confirmed)
    monkeypatch.delenv("WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE", raising=False)
    ensure_destructive_allowed(None)


# ---------------------------------------------------------------------------
# 1. 生产形态目标必须拒绝
# ---------------------------------------------------------------------------

class TestNonDevelopmentTargetsRefused:
    @pytest.mark.parametrize("url,env", [
        ("postgresql+asyncpg://u:p@db.prod.internal:5432/wudian_db", "production"),
        ("postgresql+asyncpg://u:p@localhost:5432/wudian_db", "development"),
        ("sqlite+aiosqlite:///C:/elsewhere/other.db", "development"),
        ("sqlite+aiosqlite:////srv/shared/prod.db", "development"),
        ("", "development"),
    ])
    def test_refused(self, url, env, monkeypatch):
        with pytest.raises(DestructiveOperationRefused):
            _guard_with(url, env, monkeypatch=monkeypatch)

    def test_production_env_refused_even_with_yes(self, monkeypatch):
        """APP_ENV=production 时，即使 --yes 也必须拒绝。"""
        with pytest.raises(DestructiveOperationRefused):
            _guard_with(
                "sqlite+aiosqlite:///./test_wudian_999.db", "production",
                confirmed=True, monkeypatch=monkeypatch,
            )

    def test_real_db_name_refused_even_with_yes(self, monkeypatch):
        """backend/wudian.db 是真实/生产库：--yes 也不得放行。"""
        with pytest.raises(DestructiveOperationRefused) as ei:
            _guard_with(
                "sqlite+aiosqlite:///./wudian.db", "development",
                confirmed=True, monkeypatch=monkeypatch,
            )
        assert "真实/生产库" in str(ei.value)


# ---------------------------------------------------------------------------
# 2. 缺少显式意图必须拒绝
# ---------------------------------------------------------------------------

class TestExplicitIntentRequired:
    def test_dev_db_without_confirmation_refused(self, monkeypatch):
        """合法开发库但没给 --yes：仍拒绝（不做例行调用的静默副作用）。"""
        with pytest.raises(DestructiveOperationRefused) as ei:
            _guard_with(
                "sqlite+aiosqlite:///./test_wudian_123.db", "development",
                confirmed=False, monkeypatch=monkeypatch,
            )
        assert "缺少显式意图" in str(ei.value)


# ---------------------------------------------------------------------------
# 3. 拒绝时必须「零 DELETE」
# ---------------------------------------------------------------------------

class TestRefusalIssuesNoDelete:
    # 本仓库未安装/未配置 pytest-asyncio（无 asyncio_mode），因此沿用仓库既有
    # 约定：用 asyncio.run(...) 驱动协程，而不是 @pytest.mark.asyncio
    # （后者无插件时会被**静默跳过**，产生假通过）。
    def test_clear_data_refuses_without_executing_any_delete(self, monkeypatch):
        """clear_data 在拒绝路径上不得执行任何 execute。"""
        fake_settings = mock.Mock()
        fake_settings.resolved_database_url = "postgresql+asyncpg://u:p@h:5432/prod"
        fake_settings.APP_ENV = "production"
        monkeypatch.setattr(init_db, "settings", fake_settings)
        monkeypatch.setattr(init_db, "_CLI_CONFIRMED", False)
        monkeypatch.delenv("WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE", raising=False)

        session = _FakeSession()
        with pytest.raises(DestructiveOperationRefused):
            asyncio.run(clear_data(session))
        assert session.executed == [], (
            f"拒绝路径仍然执行了语句：{session.executed}"
        )

    def test_clear_data_deletes_when_allowed(self, monkeypatch):
        """负向对照：合法开发库 + --yes 时确实执行 18 张表的 DELETE。"""
        fake_settings = mock.Mock()
        fake_settings.resolved_database_url = "sqlite+aiosqlite:///./test_wudian_777.db"
        fake_settings.APP_ENV = "development"
        monkeypatch.setattr(init_db, "settings", fake_settings)
        monkeypatch.setattr(init_db, "_CLI_CONFIRMED", True)
        monkeypatch.delenv("WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE", raising=False)

        session = _FakeSession()
        asyncio.run(clear_data(session))
        deletes = [s for s in session.executed if s.startswith("DELETE FROM")]
        assert len(deletes) == 18, f"应有 18 条 DELETE，实际 {len(deletes)}: {deletes}"
        assert "COMMIT" in session.executed


# ---------------------------------------------------------------------------
# 4. 拒绝信息必须点明被保护的目标
# ---------------------------------------------------------------------------

class TestRefusalMessageNamesTarget:
    def test_message_contains_resolved_target_and_env(self, monkeypatch):
        url = "postgresql+asyncpg://u:p@db.prod.internal:5432/wudian_db"
        with pytest.raises(DestructiveOperationRefused) as ei:
            _guard_with(url, "production", monkeypatch=monkeypatch)
        msg = str(ei.value)
        assert url in msg, "拒绝信息必须含解析后的数据库目标"
        assert "production" in msg, "拒绝信息必须含 APP_ENV"
        assert "未执行任何 DELETE" in msg

    def test_message_names_resolved_file_for_sqlite(self, monkeypatch):
        with pytest.raises(DestructiveOperationRefused) as ei:
            _guard_with("sqlite+aiosqlite:///./wudian.db", "development",
                        monkeypatch=monkeypatch)
        assert "wudian.db" in str(ei.value)


# ---------------------------------------------------------------------------
# 5. 18 张表枚举 + 守卫顺序（源码级）
# ---------------------------------------------------------------------------

EXPECTED_TABLES = [
    "verse_embeddings", "ai_chat_logs", "quiz_records", "quizzes", "comments",
    "notes", "note_likes", "srs_records", "progress", "checkins",
    "achievements", "group_members", "pk_matches", "study_groups",
    "verses", "chapters", "classic_books", "users",
]


class TestTableEnumerationAndOrder:
    def _tree(self):
        src = (BACKEND_DIR / "init_db.py").read_text(encoding="utf-8")
        return ast.parse(src)

    def test_eighteen_tables_and_guard_precedes_first_execute(self):
        """守卫必须位于 clear_data 中第一条 execute 之前。"""
        tree = self._tree()
        fn = next(
            (n for n in ast.walk(tree)
             if isinstance(n, ast.AsyncFunctionDef) and n.name == "clear_data"),
            None,
        )
        assert fn is not None, "找不到 clear_data"

        guard_line = None
        first_execute_line = None
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name == "ensure_destructive_allowed" and guard_line is None:
                    guard_line = node.lineno
                if name == "execute" and first_execute_line is None:
                    first_execute_line = node.lineno

        assert guard_line is not None, "clear_data 里找不到守卫调用"
        assert first_execute_line is not None, "clear_data 里找不到 execute"
        assert guard_line < first_execute_line, (
            f"守卫在第 {guard_line} 行，却在第 {first_execute_line} 行的 execute 之后"
        )

    def test_table_list_matches_expected_eighteen(self):
        tree = self._tree()
        found = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "tables":
                        try:
                            found = ast.literal_eval(node.value)
                        except Exception:
                            pass
        assert found == EXPECTED_TABLES, f"18 张表清单不符：{found}"

    def test_tables_targeted_count_is_eighteen(self):
        assert len(EXPECTED_TABLES) == 18
        for must in ("users", "notes", "study_groups", "verses"):
            assert must in EXPECTED_TABLES


# ---------------------------------------------------------------------------
# 6. 合法开发路径仍然可用（不碰真实库）
# ---------------------------------------------------------------------------

class TestLegitimateDevelopmentPathWorks:
    @pytest.mark.parametrize("url", [
        "sqlite+aiosqlite:///./test_wudian_555.db",
        "sqlite+aiosqlite:///./wudian_dev.db",
    ])
    def test_allowed_with_confirmation(self, url, monkeypatch):
        """合法开发库 + 显式意图 → 不抛异常（放行）。"""
        _guard_with(url, "development", confirmed=True, monkeypatch=monkeypatch)

    def test_env_var_confirmation_also_works(self, monkeypatch):
        fake_settings = mock.Mock()
        fake_settings.resolved_database_url = "sqlite+aiosqlite:///./test_wudian_556.db"
        fake_settings.APP_ENV = "development"
        monkeypatch.setattr(init_db, "settings", fake_settings)
        monkeypatch.setattr(init_db, "_CLI_CONFIRMED", False)
        monkeypatch.setenv("WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE", "1")
        ensure_destructive_allowed(None)  # 不抛异常即通过

    def test_cli_flag_parsing(self):
        assert init_db._parse_cli_confirm(["--yes"]) is True
        assert init_db._parse_cli_confirm(["-y"]) is True
        assert init_db._parse_cli_confirm([]) is False
        assert init_db._parse_cli_confirm(["--dry-run"]) is False
