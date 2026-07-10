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
# 清空旧数据（幂等）
# ============================================================
async def clear_data(session: AsyncSession):
    """清空相关表数据（按依赖顺序）"""
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
    print(f"   环境: {settings.APP_ENV}")
    print("=" * 60)

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


if __name__ == "__main__":
    asyncio.run(main())
