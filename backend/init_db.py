"""
悟典 - 数据库初始化脚本

功能：
1. 创建所有表（基于 app.models 中的 SQLAlchemy 模型）
2. 从 data/processed/lunyu.json 导入经典数据到 classic_books、chapters、verses 表
3. 从 data/processed/lunyu_quotes.json 导入名句数据
4. 从 data/processed/idioms.json 导入典故数据
5. 创建一个测试用户（用户名: test, 密码: test123）

运行方式：
    cd backend
    python init_db.py
"""
import asyncio
import json
import sys
import os
import random
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Windows 控制台 UTF-8 支持（避免 emoji/中文输出报错）
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 确保可以 import app 包
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine, async_session_factory, init_db, close_db
from app.core.config import settings
# 导入所有模型，确保 Base.metadata 包含全部表定义
import app.models  # noqa: F401
from app.models.user import User
from app.models.classic import ClassicBook, Chapter, Verse
from app.models.community import StudyGroup, GroupMember
from app.models.note import Note
from app.models.checkin import Checkin


# ============================================================
# 数据文件路径
# ============================================================
DATA_DIR = BACKEND_DIR.parent / "data" / "processed"
LUNYU_FILE = DATA_DIR / "lunyu.json"
LUNYU_QUOTES_FILE = DATA_DIR / "lunyu_quotes.json"
IDIOMS_FILE = DATA_DIR / "idioms.json"


# ============================================================
# 密码哈希（直接复用 security.py 的 bcrypt 实现，保证一致性）
# ============================================================
def hash_password(password: str) -> str:
    """使用 security.py 的 bcrypt 哈希密码"""
    from app.core.security import get_password_hash
    return get_password_hash(password)


# ============================================================
# 破坏性操作守卫（安全硬约束，DSH-SA-004 / SA001-01）
# ============================================================
# clear_data() 会对 18 张表执行 DELETE FROM（含 users/notes/study_groups/verses）。
# 原实现在 main() 的「步骤 2」无条件调用它，所以 `python init_db.py` 一条命令
# 就会清空 settings.DATABASE_URL 解析到的**任何**数据库——包括真实/生产库。
# 原代码只是在 :517-518 打印目标与环境，那是**告知**，不是**守卫**。
#
# 现在改为 fail-closed 的两道门（不确定即拒绝）：
#   1) 目标白名单：解析出的数据库必须是本地 SQLite 且落在 backend/ 目录之下，
#      并且文件名形如 wudian.db / test_wudian_*.db / *_dev.db。
#      任何其它目标（PostgreSQL、远程主机、backend 之外的路径、无法解析的 URL）
#      一律拒绝。
#   2) 显式意图：破坏性清空必须显式给出 --yes（或 WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE=1），
#      否则拒绝，避免它成为例行调用的静默副作用。
# 拒绝时打印解析后的真实目标与环境，让人看清被保护的是什么、以及如何有意继续。
# ============================================================

#: 允许被清空的 SQLite 文件名模式（仅限本地开发/测试库）。
#: 注意：**不含 wudian.db** —— backend/wudian.db 是本项目的真实/生产库
#: （见 main.py 的健康检查与 config.resolved_database_path）。把它放进白名单会让
#: `--yes` 直接清空生产库，违背 fail-closed。开发库请用 *_dev.db 或 test_wudian_*.db。
_ALLOWED_DB_SUFFIXES = ("_dev.db",)
_ALLOWED_DB_PREFIXES = ("test_wudian_",)

#: 明确拒绝的文件名（真实/生产库），即使给了 --yes 也拒绝。
_FORBIDDEN_DB_NAMES = ("wudian.db",)


class DestructiveOperationRefused(RuntimeError):
    """破坏性数据库操作被守卫拒绝。"""


def _resolve_db_file(url: str) -> Optional[Path]:
    """把 sqlite URL 解析为绝对文件路径；非本地 SQLite 返回 None。"""
    if not url or not url.startswith("sqlite"):
        return None
    # 形如 sqlite+aiosqlite:///./wudian.db 或 sqlite:///D:/x/y.db
    raw = url.split(":///", 1)[1] if ":///" in url else url.rsplit("/", 1)[-1]
    if not raw:
        return None
    p = Path(raw)
    if not p.is_absolute():
        p = BACKEND_DIR / raw
    return p.resolve()


def _is_allowed_target(db_file: Optional[Path]) -> bool:
    """目标是否属于允许清空的本地开发/测试库。

    fail-closed：只有**明确认得**的开发/测试库特征才返回 True。
    """
    if db_file is None:
        return False
    try:
        if BACKEND_DIR.resolve() not in db_file.parents:
            return False
    except OSError:
        return False
    name = db_file.name
    # 真实/生产库名一律拒绝（不受 --yes 影响）。
    if name in _FORBIDDEN_DB_NAMES:
        return False
    return (
        name.endswith(_ALLOWED_DB_SUFFIXES)
        or name.startswith(_ALLOWED_DB_PREFIXES)
    )


def ensure_destructive_allowed(session: AsyncSession) -> None:
    """在 clear_data 执行任何 DELETE **之前**校验；不允许则抛异常拒绝。

    仅在 --yes / 环境变量给出显式意图时返回正常；否则抛
    :class:`DestructiveOperationRefused`，且**不执行任何 DELETE**。
    """
    url = settings.resolved_database_url
    db_file = _resolve_db_file(url)
    env = settings.APP_ENV
    confirmed = bool(os.environ.get("WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE")) or _CLI_CONFIRMED

    problems = []
    if db_file is None:
        problems.append(
            "目标不是本地 SQLite 文件（可能是 PostgreSQL 或远程数据库）"
        )
    elif db_file.name in _FORBIDDEN_DB_NAMES:
        problems.append(
            f"目标文件名 {db_file.name} 是真实/生产库，即使显式确认也不允许清空"
        )
    elif not _is_allowed_target(db_file):
        problems.append(
            "目标不在允许清空的本地开发/测试库特征内"
            f"（允许：*{_ALLOWED_DB_SUFFIXES} / {_ALLOWED_DB_PREFIXES}*）"
        )
    if env == "production":
        problems.append("APP_ENV=production，绝不允许清空")
    if not confirmed:
        problems.append(
            "缺少显式意图：请加 --yes，或设 WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE=1"
        )

    if problems:
        raise DestructiveOperationRefused(
            "\n"
            "======================================================================\n"
            "🛑 已拒绝执行破坏性操作（clear_data：18 张表的 DELETE FROM）。\n"
            f"   解析后的数据库目标: {url}\n"
            f"   解析后的数据库文件: {db_file if db_file is not None else '（非本地 SQLite）'}\n"
            f"   APP_ENV           : {env}\n"
            f"   已给出的显式确认  : {confirmed}\n"
            "   拒绝原因:\n"
            + "".join(f"     - {p}\n" for p in problems)
            + "   本操作未被拒绝时才会执行删除；本次**未执行任何 DELETE**。\n"
            "   若目标是可清空的开发库（*_dev.db / test_wudian_*.db），请显式确认后重试：\n"
            "     python init_db.py --yes\n"
            "======================================================================\n"
        )


#: 由 __main__ 在解析 argv 后设置：是否显式给出 --yes。
_CLI_CONFIRMED = False


def _parse_cli_confirm(argv: List[str]) -> bool:
    """解析 --yes / -y；不认识的参数一律忽略（保持原 CLI 行为）。"""
    return any(a in ("--yes", "-y") for a in argv)


# ============================================================
# 清空旧数据（幂等）
# ============================================================
async def clear_data(session: AsyncSession):
    """清空相关表数据（按依赖顺序）。

    DSH-SA-004：本函数是破坏性操作，执行前必须通过
    :func:`ensure_destructive_allowed` 守卫；守卫在**第一条 execute 之前**，
    拒绝时不会发出任何 DELETE。
    """
    # 守卫必须位于任何 execute 之前 —— 不要在本行之上添加 DELETE。
    ensure_destructive_allowed(session)

    print("🧹 清空旧数据...")
    # 按外键依赖顺序删除
    tables = [
        "verse_embeddings",
        "ai_chat_logs",
        "quiz_records",
        "quizzes",
        "comments",
        "notes",
        "note_likes",
        "srs_records",
        "progress",
        "checkins",
        "achievements",
        "group_members",
        "pk_matches",
        "study_groups",
        "verses",
        "chapters",
        "classic_books",
        "users",
    ]
    from sqlalchemy import text
    for table_name in tables:
        await session.execute(text(f"DELETE FROM {table_name}"))
    await session.commit()
    print("   旧数据已清空")


# ============================================================
# 创建测试用户
# ============================================================
async def create_test_user(session: AsyncSession) -> User:
    """创建测试用户（用户名: test, 密码: test123）"""
    print("👤 创建测试用户...")

    # 检查是否已存在
    stmt = select(User).where(User.username == "test")
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        print("   测试用户已存在，跳过")
        return existing

    user = User(
        username="test",
        email="test@wudian.local",
        hashed_password=hash_password("test123"),
        nickname="测试学者",
        bio="悟典平台测试用户",
        level=1,
        exp_points=0,
        streak_days=0,
        total_study_days=0,
        total_verses_learned=0,
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    print(f"   ✅ 测试用户已创建: id={user.id}, username={user.username}")
    return user


# ============================================================
# 导入论语数据
# ============================================================
async def import_lunyu(session: AsyncSession) -> dict:
    """
    从 lunyu.json 导入数据到 classic_books、chapters、verses 表。

    数据结构：
    {
        "book": "论语",
        "author": "...",
        "dynasty": "...",
        "description": "...",
        "total_chapters": 20,
        "chapters": [
            {
                "chapter_id": 1,
                "chapter_title": "学而",
                "summary": "...",
                "verses": [
                    {
                        "verse_id": "1.1",
                        "original": "...",
                        "translation": "...",
                        "annotations": [...],
                        "keywords": [...],
                        "title": "..."
                    },
                    ...
                ]
            },
            ...
        ]
    }
    """
    print("📖 导入论语数据...")

    if not LUNYU_FILE.exists():
        print(f"   ❌ 文件不存在: {LUNYU_FILE}")
        return {}

    with open(LUNYU_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. 创建书籍
    book = ClassicBook(
        title=data.get("book", "论语"),
        category="四书",
        description=data.get("description", ""),
        author=data.get("author", ""),
        era=data.get("dynasty", ""),
        sort_order=1,
    )
    session.add(book)
    await session.flush()  # 获取 book.id
    print(f"   📚 书籍已创建: {book.title} (id={book.id})")

    chapter_count = 0
    verse_count = 0

    # 2. 创建章节和经文
    for ch in data.get("chapters", []):
        chapter = Chapter(
            book_id=book.id,
            chapter_number=ch.get("chapter_id", chapter_count + 1),
            title=ch.get("chapter_title", f"第{chapter_count + 1}章"),
            description=ch.get("summary", ""),
        )
        session.add(chapter)
        await session.flush()  # 获取 chapter.id
        chapter_count += 1

        for idx, v in enumerate(ch.get("verses", []), start=1):
            # 解析 verse_id "1.1" -> verse_number 1
            verse_id_str = str(v.get("verse_id", f"{ch.get('chapter_id', 1)}.{idx}"))
            try:
                verse_number = int(verse_id_str.split(".")[-1])
            except (ValueError, IndexError):
                verse_number = idx

            # 拼接注释为可读文本
            annotations = v.get("annotations", [])
            annotation_text = ""
            if annotations:
                parts = []
                for ann in annotations:
                    char = ann.get("char", "")
                    pinyin = ann.get("pinyin", "")
                    meaning = ann.get("meaning", "")
                    parts.append(f"{char}（{pinyin}）：{meaning}")
                annotation_text = "\n".join(parts)

            # 拼接解读：标题 + 关键词
            interpretation = ""
            title = v.get("title", "")
            keywords = v.get("keywords", [])
            if title:
                interpretation += f"【主题】{title}"
            if keywords:
                if interpretation:
                    interpretation += "\n"
                interpretation += f"【关键词】{'、'.join(keywords)}"

            verse = Verse(
                book_id=book.id,
                chapter_id=chapter.id,
                verse_number=verse_number,
                original_text=v.get("original", ""),
                translation=v.get("translation", ""),
                annotation=annotation_text or None,
                interpretation=interpretation or None,
                pinyin=None,
                audio_url=None,
            )
            session.add(verse)
            verse_count += 1

        await session.flush()

    await session.commit()
    print(f"   ✅ 导入完成: {chapter_count} 章, {verse_count} 条经文")
    return {
        "book_id": book.id,
        "book_title": book.title,
        "chapter_count": chapter_count,
        "verse_count": verse_count,
    }


# ============================================================
# 导入名句数据
# ============================================================
def load_lunyu_quotes() -> list:
    """加载论语名句数据（存于内存，供 daily-quote 等接口使用）"""
    print("💬 加载论语名句数据...")

    if not LUNYU_QUOTES_FILE.exists():
        print(f"   ⚠️ 文件不存在: {LUNYU_QUOTES_FILE}")
        return []

    with open(LUNYU_QUOTES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    quotes = data.get("quotes", [])
    print(f"   ✅ 加载 {len(quotes)} 条名句")
    return quotes


# ============================================================
# 导入典故数据
# ============================================================
def load_idioms() -> list:
    """加载典故数据（存于内存，供 idiom_service 使用）"""
    print("🔤 加载典故数据...")

    if not IDIOMS_FILE.exists():
        print(f"   ⚠️ 文件不存在: {IDIOMS_FILE}")
        return []

    with open(IDIOMS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    idioms = data.get("idioms", [])
    print(f"   ✅ 加载 {len(idioms)} 条典故")
    return idioms


# ============================================================
# 创建社区种子数据（演示用户、小组、笔记）
# ============================================================
async def create_community_seed(session: AsyncSession) -> dict:
    """创建社区种子数据：演示用户、示例小组、示例笔记"""
    print("👥 创建社区种子数据...")

    stats = {"users": 0, "groups": 0, "notes": 0}

    # 1. 创建演示用户（古代学者角色，用于 PK 匹配和排行榜）
    demo_users_data = [
        {"username": "zengzi", "email": "zengzi@wudian.local", "nickname": "曾子", "level": 12, "exp_points": 3200, "streak_days": 45, "pk_rating": 1180},
        {"username": "zigong", "email": "zigong@wudian.local", "nickname": "子贡", "level": 15, "exp_points": 4500, "streak_days": 60, "pk_rating": 1320},
        {"username": "zilu", "email": "zilu@wudian.local", "nickname": "子路", "level": 10, "exp_points": 2100, "streak_days": 30, "pk_rating": 1050},
        {"username": "yanhui", "email": "yanhui@wudian.local", "nickname": "颜回", "level": 20, "exp_points": 6800, "streak_days": 90, "pk_rating": 1550},
        {"username": "ziyou", "email": "ziyou@wudian.local", "nickname": "子游", "level": 8, "exp_points": 1500, "streak_days": 15, "pk_rating": 980},
    ]

    created_users = {}
    for ud in demo_users_data:
        stmt = select(User).where(User.username == ud["username"])
        existing = (await session.execute(stmt)).scalars().first()
        if existing:
            created_users[ud["username"]] = existing
            continue

        user = User(
            username=ud["username"],
            email=ud["email"],
            hashed_password=hash_password("wudian123"),
            nickname=ud["nickname"],
            level=ud["level"],
            exp_points=ud["exp_points"],
            streak_days=ud["streak_days"],
            total_study_days=ud["streak_days"],
            pk_rating=ud["pk_rating"],
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()
        created_users[ud["username"]] = user
        stats["users"] += 1

    await session.flush()

    # 2. 创建示例学习小组
    zengzi = created_users.get("zengzi")
    zigong = created_users.get("zigong")
    yanhui = created_users.get("yanhui")
    zilu = created_users.get("zilu")

    if zengzi:
        # 小组1：论语入门共读
        group1 = StudyGroup(
            name="论语入门共读",
            description="从《学而》篇开始，逐章精读《论语》，适合初学者。",
            category="beginner",
            owner_id=zengzi.id,
            book_id="1",
            group_type="public",
            is_private=False,
            max_members=50,
            member_count=3,
        )
        session.add(group1)
        await session.flush()

        # 组长
        session.add(GroupMember(
            group_id=group1.id, user_id=zengzi.id, role="owner", joined_at=datetime.utcnow()
        ))
        # 成员
        if zilu:
            session.add(GroupMember(
                group_id=group1.id, user_id=zilu.id, role="member", joined_at=datetime.utcnow()
            ))
        if zigong:
            session.add(GroupMember(
                group_id=group1.id, user_id=zigong.id, role="member", joined_at=datetime.utcnow()
            ))
        stats["groups"] += 1

    if yanhui:
        # 小组2：论语进阶研读
        group2 = StudyGroup(
            name="论语进阶研读",
            description="深入探讨《论语》中的义理与思想，适合有一定基础的学习者。",
            category="advanced",
            owner_id=yanhui.id,
            book_id="1",
            group_type="public",
            is_private=False,
            max_members=30,
            member_count=2,
        )
        session.add(group2)
        await session.flush()

        session.add(GroupMember(
            group_id=group2.id, user_id=yanhui.id, role="owner", joined_at=datetime.utcnow()
        ))
        if zengzi:
            session.add(GroupMember(
                group_id=group2.id, user_id=zengzi.id, role="member", joined_at=datetime.utcnow()
            ))
        stats["groups"] += 1

        # 小组3：仁义主题共读
        group3 = StudyGroup(
            name="仁义主题共读",
            description="围绕「仁」「义」主题，跨章节研读相关经文。",
            category="theme",
            owner_id=yanhui.id,
            book_id="1",
            group_type="public",
            is_private=False,
            max_members=20,
            member_count=1,
        )
        session.add(group3)
        await session.flush()

        session.add(GroupMember(
            group_id=group3.id, user_id=yanhui.id, role="owner", joined_at=datetime.utcnow()
        ))
        stats["groups"] += 1

    await session.flush()

    # 3. 创建示例笔记
    notes_data = []
    if zengzi:
        notes_data.append({
            "user_id": zengzi.id,
            "title": "学而时习之：学习方法论",
            "content": "「学而时习之，不亦说乎？」这句话揭示了学习的两个关键：学与习。学是获取新知，习是反复实践。只有将所学付诸实践，才能真正内化为自己的修养。在现代生活中，我们常常只「学」不「习」，读完就忘，这违背了孔子教导的学习之道。",
            "book_id": "1",
            "chapter_id": "1",
            "verse_text": "学而时习之，不亦说乎？",
            "group_id": None,
            "tags": ["学习方法", "学而"],
            "is_essence": True,
        })
    if yanhui:
        notes_data.append({
            "user_id": yanhui.id,
            "title": "吾日三省吾身的现代意义",
            "content": "曾子曰：「吾日三省吾身：为人谋而不忠乎？与朋友交而不信乎？传不习乎？」这种每日自省的功夫，在今天依然有价值。我们可以每天问自己三个问题：今天工作是否尽心？与人交往是否诚信？所学是否实践？这种反思习惯能持续提升自我。",
            "book_id": "1",
            "chapter_id": "1",
            "verse_text": "吾日三省吾身：为人谋而不忠乎？与朋友交而不信乎？传不习乎？",
            "group_id": None,
            "tags": ["自省", "修身", "学而"],
            "is_essence": True,
        })
    if zigong:
        notes_data.append({
            "user_id": zigong.id,
            "title": "君子务本的深刻内涵",
            "content": "有子曰：「君子务本，本立而道生。孝弟也者，其为仁之本与！」「务本」二字极为重要。无论做什么事，都要抓住根本。儒家认为孝悌是仁的根本，推而广之，做人的根本在于修身。现代人常被枝节事务困扰，忘记了根本，这是值得反思的。",
            "book_id": "1",
            "chapter_id": "1",
            "verse_text": "君子务本，本立而道生。",
            "group_id": None,
            "tags": ["务本", "孝悌", "修身"],
            "is_essence": False,
        })
    if zilu:
        notes_data.append({
            "user_id": zilu.id,
            "title": "巧言令色与真诚待人",
            "content": "子曰：「巧言令色，鲜矣仁。」孔子批评花言巧语、面目伪善的人。在社交媒体时代，这种现象更加普遍。真诚是人际交往的基石，我们应该少一些包装，多一些真实。读《论语》让我反思自己的言行是否真诚。",
            "book_id": "1",
            "chapter_id": "1",
            "verse_text": "巧言令色，鲜矣仁。",
            "group_id": None,
            "tags": ["真诚", "学而"],
            "is_essence": False,
        })

    import json as _json
    for nd in notes_data:
        note = Note(
            user_id=nd["user_id"],
            verse_id=None,
            title=nd["title"],
            content=nd["content"],
            book_id=nd["book_id"],
            chapter_id=nd["chapter_id"],
            verse_text=nd["verse_text"],
            group_id=nd["group_id"],
            tags=_json.dumps(nd["tags"], ensure_ascii=False),
            is_public=True,
            is_essence=nd["is_essence"],
            likes=random.randint(5, 50),
            comment_count=0,
            favorites=0,
        )
        session.add(note)
        stats["notes"] += 1

    await session.commit()
    print(f"   ✅ 社区种子数据: {stats['users']} 用户, {stats['groups']} 小组, {stats['notes']} 笔记")
    return stats


# ============================================================
# 主流程
# ============================================================
async def main():
    print("=" * 60)
    print("🚀 悟典数据库初始化脚本")
    print(f"   数据库: {settings.DATABASE_URL}")
    print(f"   解析后: {settings.resolved_database_url}")
    print(f"   环境: {settings.APP_ENV}")
    if not _CLI_CONFIRMED and not os.environ.get("WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE"):
        print("   ⚠️ 未给出 --yes：若目标不允许清空，步骤 2 将被拒绝。")
    print("=" * 60)

    # 0. 破坏性操作预检（DSH-SA-004）：在**建表之前**就先拒绝，
    #    避免「表已创建、清空才失败」的半途状态。
    try:
        ensure_destructive_allowed(None)  # session 不参与校验，仅为复用同一守卫
    except DestructiveOperationRefused as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # 1. 创建所有表
    print("\n📦 步骤 1: 创建数据库表...")
    await init_db()
    print("   ✅ 所有表已创建")

    # 2. 清空旧数据（幂等）
    print("\n📦 步骤 2: 清空旧数据...")
    async with async_session_factory() as session:
        await clear_data(session)

    # 3. 导入数据
    print("\n📦 步骤 3: 导入数据...")
    async with async_session_factory() as session:
        # 创建测试用户
        user = await create_test_user(session)

        # 导入论语
        lunyu_stats = await import_lunyu(session)

    # 4. 创建社区种子数据
    print("\n📦 步骤 4: 创建社区种子数据...")
    async with async_session_factory() as session:
        community_stats = await create_community_seed(session)

    # 加载名句和典故（验证文件可读）
    quotes = load_lunyu_quotes()
    idioms = load_idioms()

    # 5. 汇总
    print("\n" + "=" * 60)
    print("🎉 数据库初始化完成！")
    print(f"   - 测试用户: test / test123 (id={user.id})")
    if lunyu_stats:
        print(f"   - 书籍: {lunyu_stats['book_title']} (id={lunyu_stats['book_id']})")
        print(f"   - 章节: {lunyu_stats['chapter_count']} 章")
        print(f"   - 经文: {lunyu_stats['verse_count']} 条")
    print(f"   - 名句: {len(quotes)} 条（文件已加载）")
    print(f"   - 典故: {len(idioms)} 条（文件已加载）")
    if community_stats:
        print(f"   - 社区种子: {community_stats['users']} 演示用户, {community_stats['groups']} 小组, {community_stats['notes']} 笔记")
    print(f"\n   数据库文件: {settings.DATABASE_URL}")
    print("=" * 60)

    await close_db()
    return 0


if __name__ == "__main__":
    # DSH-SA-004：破坏性清空必须显式给出 --yes（或 WUDIAN_INIT_DB_ALLOW_DESTRUCTIVE=1）。
    _CLI_CONFIRMED = _parse_cli_confirm(sys.argv[1:])
    _rc = asyncio.run(main())
    sys.exit(_rc or 0)
