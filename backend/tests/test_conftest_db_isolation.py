"""
DSH-SA-003：测试数据库 ``DATABASE_URL`` 继承隔离的回归测试。

背景（安全缺陷 SA001-02）
------------------------
``backend/tests/conftest.py:35`` 原实现是::

    os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///./test_wudian_{_PID}.db")

``setdefault`` 的语义是「环境里已经有就沿用」。因此只要 ``DATABASE_URL`` 已经存在
（开发者 shell、CI 变量、``.env``、或继承自父进程），pytest 就会**静默采纳**它。
如果它指向一个真实数据库，``conftest.py:126`` 的 ``await init_db()`` 会
``Base.metadata.create_all``，``TestClient`` 会随后对那个库建表/写入。

这与同一文件 ``conftest.py:58-66`` 已经修好的 ``CHROMA_PERSIST_DIR`` 是**同一类**
继承型缺陷：SAFETY-001 正是因为「继承来的值指向生产目录」导致 2026-10-08 索引损坏，
才把 ``CHROMA_PERSIST_DIR`` 从 ``setdefault`` 改成**硬赋值**。``DATABASE_URL`` 当时
被漏掉了，本文件即用来关闭这个不对称。

本文件断言
----------
1. 环境里预先放一个「真实库形态」的 ``DATABASE_URL`` 时，**实际生效**的测试库
   不得是它（而是 per-process 隔离库）——这是 RED 断言，修复前必须失败；
2. 未设置 ``DATABASE_URL`` 的普通开发者路径同样落在隔离库上；
3. 隔离仍然是 **per-process（PID 后缀）**，不是共享固定库
   （``conftest.py:52-56`` 记录了共享固定库导致的并发竞态）；
4. ``conftest.py`` 源码里 ``DATABASE_URL`` 不再使用 ``setdefault``，
   且确实是**硬赋值**——用源码断言防止将来改回去。

全部断言在**子进程**里完成：环境变量必须在 ``conftest.py`` 执行**之前**注入，
而本进程的 ``conftest.py`` 早已执行完毕，无法回溯验证「继承」这一场景。
子进程用 ``-p no:cacheprovider`` 且会清理自己产生的隔离 DB/Chroma 目录。
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

# 安装探针：在子进程里**先导入 conftest**（触发它的隔离逻辑），再读取 conftest
# 当时实际生效的 DATABASE_URL / CHROMA_PERSIST_DIR，打印到 stdout。
# 这里用独立的 ``-c`` 脚本而非 pytest 钩子，原因是必须精确控制「导入时机」：
# 探针必须在 conftest 执行之后、但在 test 模块导入之前读到值。
_PROBE = '''
import os, sys
sys.path.insert(0, {pytest_root!r})
sys.path.insert(0, {tests_dir!r})
import conftest  # noqa: F401  <- 触发隔离逻辑（硬赋值 + 警告）
print("SA003_EFFECTIVE_DATABASE_URL=" + os.environ.get("DATABASE_URL", ""))
print("SA003_EFFECTIVE_CHROMA_DIR=" + os.environ.get("CHROMA_PERSIST_DIR", ""))
'''


def _run_probe(extra_env: dict) -> dict:
    """在**子进程**里导入 conftest，返回隔离逻辑生效后的值。

    ``extra_env`` 里的变量会被显式设置（值为 None 表示从子进程环境中移除）。
    子进程只导入 conftest，不导入 app.main，因此不会建库、不会连 Chroma。
    """
    env = dict(os.environ)
    env.pop("DATABASE_URL", None)
    for k, v in extra_env.items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    script = _PROBE.format(
        pytest_root=str(BACKEND_DIR),
        tests_dir=str(BACKEND_DIR / "tests"),
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(BACKEND_DIR), env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300,
    )
    text = (proc.stdout or "") + (proc.stderr or "")

    def _grab(key: str) -> str:
        m = re.search(rf"^{key}=(.*)$", text, re.MULTILINE)
        return m.group(1).strip() if m else ""

    return {
        "effective_url": _grab("SA003_EFFECTIVE_DATABASE_URL"),
        "effective_chroma": _grab("SA003_EFFECTIVE_CHROMA_DIR"),
        "returncode": proc.returncode,
        "raw": text,
    }


def _isolated_url_pid(url: str) -> str:
    """从生效的 DATABASE_URL 里取出 PID 后缀；取不到返回空串。"""
    m = re.search(r"test_wudian_(\d+)\.db", url or "")
    return m.group(1) if m else ""


class TestDatabaseUrlNotInherited:
    """SA001-02 的核心 RED 断言：继承来的真实库 URL 不得生效。"""

    INHERITED_REAL_URL = "sqlite+aiosqlite:///./wudian.db"

    def test_inherited_real_database_url_is_not_adopted(self):
        """环境里预先放真实库 URL 时，生效的测试库必须**不是**它。

        修复前（``setdefault``）：生效值 = ``.../wudian.db`` → 断言失败（RED）。
        修复后（硬赋值）：生效值 = ``.../test_wudian_<pid>.db`` → 通过。
        """
        r = _run_probe({"DATABASE_URL": self.INHERITED_REAL_URL})
        eff = r["effective_url"]
        assert eff, (
            "子进程未产出探针输出，无法判定生效的 DATABASE_URL；"
            f"pytest returncode={r['returncode']}\n{r['raw'][-2000:]}"
        )
        assert "wudian.db" not in eff.replace("test_wudian_", ""), (
            f"继承了真实数据库 URL 并使其生效：{eff!r}。"
            "conftest.py 必须强制覆盖 DATABASE_URL，不得沿用环境里的值。"
        )
        assert "test_wudian_" in eff, (
            f"生效的测试库不是 per-process 隔离库：{eff!r}"
        )

    def test_inherited_postgres_url_is_not_adopted(self):
        """继承了 Postgres URL 时同样不得生效（生产形态）。"""
        r = _run_probe({
            "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/wudian_db",
        })
        eff = r["effective_url"]
        assert eff, (
            f"子进程未产出探针输出；returncode={r['returncode']}\n{r['raw'][-2000:]}"
        )
        assert "postgresql" not in eff, (
            f"继承了 Postgres URL 并使其生效：{eff!r}——测试会对着真实库建表。"
        )
        assert "test_wudian_" in eff


class TestNormalPathsStillIsolated:
    """普通路径（未设置 / 已设置）都必须落在隔离库上。"""

    def test_unset_database_url_resolves_to_isolated_db(self):
        """开发者未设置 DATABASE_URL 时落在 per-process 隔离库。"""
        r = _run_probe({"DATABASE_URL": None})
        eff = r["effective_url"]
        assert "test_wudian_" in eff, f"未隔离：{eff!r}"
        assert _isolated_url_pid(eff), f"隔离库缺少 PID 后缀：{eff!r}"

    def test_isolated_db_is_per_process(self):
        """隔离必须是 per-process：两次子进程的 PID 后缀必须不同。

        conftest.py:52-56 记录了共享固定库导致的并发竞态，这里把它钉死。
        """
        a = _run_probe({"DATABASE_URL": None})["effective_url"]
        b = _run_probe({"DATABASE_URL": None})["effective_url"]
        pa, pb = _isolated_url_pid(a), _isolated_url_pid(b)
        assert pa and pb and pa != pb, (
            f"两次子进程 PID 后缀相同或缺失（{pa!r} vs {pb!r}），"
            "说明测试库不是 per-process 的，并发 pytest 会互相删除表。"
        )

    def test_chroma_isolation_still_hard_assigned(self):
        """CHROMA_PERSIST_DIR 的 SAFETY-001 纪律不得被本次改动破坏。"""
        r = _run_probe({"DATABASE_URL": None})
        assert "chroma_db" not in r["effective_chroma"], (
            f"生效的 Chroma 目录指向生产：{r['effective_chroma']!r}"
        )
        assert "_test_iso_chroma_" in r["effective_chroma"]


class TestConftestSourceDiscipline:
    """源码级断言：防止将来把 DATABASE_URL 改回 setdefault。

    注意：conftest.py 的注释里会**引用**旧的 setdefault 写法来解释缺陷成因，
    因此断言必须只检查**可执行代码**，不能对整份源码做子串匹配——否则注释
    会被误判成缺陷。这里先剥掉注释行再断言。
    """

    def _src(self) -> str:
        return (BACKEND_DIR / "tests" / "conftest.py").read_text(encoding="utf-8")

    @staticmethod
    def _code_only(src: str) -> str:
        """剥掉整行注释，只保留可执行代码（对本文件足够，无行尾注释干扰）。"""
        return "\n".join(
            line for line in src.splitlines()
            if not line.lstrip().startswith("#")
        )

    def test_database_url_is_not_setdefault(self):
        code = self._code_only(self._src())
        assert 'setdefault("DATABASE_URL"' not in code, (
            "conftest 的可执行代码又用回了 setdefault(\"DATABASE_URL\", ...)："
            "继承来的 DATABASE_URL 会被沿用，若它指向真实库则测试会对其建表。"
        )

    def test_database_url_is_hard_assigned(self):
        code = self._code_only(self._src())
        assert 'os.environ["DATABASE_URL"] =' in code, (
            "conftest 必须**强制赋值** DATABASE_URL"
        )

    def test_chroma_and_database_follow_the_same_discipline(self):
        """两个变量必须对称：都硬赋值、都不得 setdefault（SAFETY-001）。"""
        code = self._code_only(self._src())
        assert 'os.environ["CHROMA_PERSIST_DIR"] =' in code
        assert 'os.environ["DATABASE_URL"] =' in code
        assert 'setdefault("CHROMA_PERSIST_DIR"' not in code
        assert 'setdefault("DATABASE_URL"' not in code


def teardown_module(module):
    """清理本文件可能产生的隔离 DB / Chroma 临时目录（按本进程 PID）。"""
    pid = os.getpid()
    for suffix in ("", "-wal", "-shm"):
        p = BACKEND_DIR / f"test_wudian_{pid}.db{suffix}"
        if p.exists():
            p.unlink()
    iso = BACKEND_DIR / f"_test_iso_chroma_{pid}"
    if iso.exists():
        shutil.rmtree(iso, ignore_errors=True)
