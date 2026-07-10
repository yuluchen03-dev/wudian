"""
悟典 - 测验服务
多题型支持(选择/填空/配对/连线)、题目随机抽取、错题本管理、答题反馈。

适配现有 Quiz 模型字段:
  - quiz_type (非 question_type): choice/fill/match/translate/explain/order
  - options: JSON 数组
  - answer: Text (非 JSON) - 存储正确答案文本或 JSON 字符串
  - difficulty, explanation, tags, book_id, chapter_id, verse_id

适配现有 QuizRecord 模型字段:
  - user_answer: Text (非 JSON)
  - is_correct: Integer (0/1, 非 Boolean)
  - score: Float
  - answered_at: DateTime
  - 无 verse_id / in_wrong_book / resolved 字段
  - 错题本通过 is_correct == 0 查询
"""
from __future__ import annotations
import json
import random
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classic import Verse, Chapter, ClassicBook
from app.models.quiz import Quiz, QuizRecord


PASS_THRESHOLD = 70  # 通关正确率 70%


class QuizService:
    """测验服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_quiz_for_verse(self, verse_id: int, *, count: int = 5) -> list[dict]:
        """
        获取某条经文的测验题。
        若题库不足，自动生成基础题(填空/选择)。
        """
        stmt = (
            select(Quiz)
            .where(
                and_(
                    Quiz.verse_id == verse_id,
                    Quiz.is_deleted == False,
                )
            )
            .order_by(Quiz.difficulty.asc())
        )
        quizzes = (await self.db.execute(stmt)).scalars().all()

        # 若题库不足，动态生成
        if len(quizzes) < count:
            verse = await self._get_verse(verse_id)
            if verse:
                generated = self._generate_basic_quizzes(verse)
                quizzes = list(quizzes) + generated

        random.shuffle(quizzes)
        selected = quizzes[:count]

        return [self._quiz_to_dict(q) for q in selected]

    async def get_quiz_for_chapter(self, chapter_id: int, *, count: int = 10) -> list[dict]:
        """获取某章节的测验题(跨该章所有经文)。"""
        stmt = (
            select(Quiz)
            .where(
                and_(
                    Quiz.chapter_id == chapter_id,
                    Quiz.is_deleted == False,
                )
            )
            .order_by(Quiz.difficulty.asc())
        )
        quizzes = (await self.db.execute(stmt)).scalars().all()

        # 题库不足则从该章经文动态生成
        if len(quizzes) < count:
            verse_stmt = select(Verse).where(
                and_(Verse.chapter_id == chapter_id, Verse.is_deleted == False)
            )
            verses = (await self.db.execute(verse_stmt)).scalars().all()
            for v in verses:
                quizzes = list(quizzes) + self._generate_basic_quizzes(v)

        random.shuffle(quizzes)
        selected = quizzes[:count]
        return [self._quiz_to_dict(q) for q in selected]

    async def submit_answer(
        self,
        user_id: int,
        quiz_id: int,
        user_answer: Any,
        *,
        time_spent: int = 0,
    ) -> dict:
        """
        提交单题答案。
        user_answer 可以是 dict/list/str，内部序列化为文本存储。
        返回: 是否正确、正确答案、解析。
        同时写入 QuizRecord。
        """
        quiz = await self._get_quiz(quiz_id)
        if quiz is None:
            raise ValueError(f"题目 {quiz_id} 不存在")

        is_correct = self._check_answer(quiz, user_answer)
        answer_text = self._serialize_answer(user_answer)

        # 写入记录 (is_correct 为 0/1)
        record = QuizRecord(
            user_id=user_id,
            quiz_id=quiz_id,
            user_answer=answer_text,
            is_correct=1 if is_correct else 0,
            score=1.0 if is_correct else 0.0,
            time_spent=time_spent,
            answered_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        await self.db.flush()

        return {
            "quiz_id": quiz_id,
            "is_correct": is_correct,
            "correct_answer": quiz.answer,
            "explanation": quiz.explanation or "",
            "in_wrong_book": not is_correct,
        }

    async def submit_quiz_batch(
        self,
        user_id: int,
        answers: list[dict],
    ) -> dict:
        """
        批量提交测验答案(一组题)。
        answers: [{"quiz_id": int, "user_answer": Any, "time_spent": int}, ...]
        返回: 总分、正确率、是否通关、逐题反馈、错题列表。
        """
        results = []
        correct_count = 0
        wrong_list = []
        total = len(answers)
        total_time = 0

        for a in answers:
            quiz_id = a.get("quiz_id")
            user_answer = a.get("user_answer", {})
            time_spent = a.get("time_spent", 0)
            total_time += time_spent

            feedback = await self.submit_answer(
                user_id, quiz_id, user_answer, time_spent=time_spent
            )
            results.append(feedback)
            if feedback["is_correct"]:
                correct_count += 1
            else:
                wrong_list.append(feedback)

        score = int(round(correct_count / total * 100)) if total > 0 else 0
        passed = score >= PASS_THRESHOLD

        return {
            "total": total,
            "correct_count": correct_count,
            "wrong_count": total - correct_count,
            "score": score,
            "passed": passed,
            "pass_threshold": PASS_THRESHOLD,
            "total_time": total_time,
            "results": results,
            "wrong_list": wrong_list,
        }

    # ---------- 错题本 ----------

    async def get_wrong_book(self, user_id: int, *, limit: int = 50, offset: int = 0) -> dict:
        """
        获取错题本列表 (is_correct == 0 的记录)。
        由于现有 QuizRecord 无 resolved 字段，此处取最近答错的题目。
        """
        stmt = (
            select(QuizRecord, Quiz)
            .join(Quiz, QuizRecord.quiz_id == Quiz.id)
            .where(
                and_(
                    QuizRecord.user_id == user_id,
                    QuizRecord.is_correct == 0,
                    QuizRecord.is_deleted == False,
                )
            )
            .order_by(QuizRecord.answered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.db.execute(stmt)).all()

        items = []
        for record, quiz in rows:
            items.append({
                "record_id": record.id,
                "quiz_id": quiz.id,
                "verse_id": quiz.verse_id,
                "question_type": quiz.quiz_type,
                "question": quiz.question,
                "options": quiz.options,
                "user_answer": record.user_answer,
                "correct_answer": quiz.answer,
                "explanation": quiz.explanation,
                "created_at": record.answered_at.isoformat() if record.answered_at else None,
            })

        # 总数
        count_stmt = select(func.count(QuizRecord.id)).where(
            and_(
                QuizRecord.user_id == user_id,
                QuizRecord.is_correct == 0,
                QuizRecord.is_deleted == False,
            )
        )
        total = int((await self.db.execute(count_stmt)).scalar() or 0)

        return {"items": items, "total": total, "limit": limit, "offset": offset}

    async def resolve_wrong(self, user_id: int, record_id: int) -> bool:
        """
        将错题标记为已攻克。
        由于现有 QuizRecord 无 resolved 字段，此处通过新增一条正确记录来表示攻克。
        """
        stmt = select(QuizRecord).where(
            and_(
                QuizRecord.id == record_id,
                QuizRecord.user_id == user_id,
                QuizRecord.is_deleted == False,
            )
        )
        record = (await self.db.execute(stmt)).scalars().first()
        if record is None:
            return False
        # 标记该错误记录为已攻克: 通过更新 is_correct 无法保留历史，
        # 改为软删除该错题记录(从错题本移除)
        record.is_deleted = True
        await self.db.flush()
        return True

    async def retry_wrong(self, user_id: int, record_id: int, user_answer: Any) -> dict:
        """重做错题本中的某题。"""
        stmt = select(QuizRecord).where(
            and_(
                QuizRecord.id == record_id,
                QuizRecord.user_id == user_id,
                QuizRecord.is_deleted == False,
            )
        )
        record = (await self.db.execute(stmt)).scalars().first()
        if record is None:
            raise ValueError(f"记录 {record_id} 不存在")

        quiz = await self._get_quiz(record.quiz_id)
        is_correct = self._check_answer(quiz, user_answer)
        answer_text = self._serialize_answer(user_answer)

        # 新增一条记录
        new_record = QuizRecord(
            user_id=user_id,
            quiz_id=record.quiz_id,
            user_answer=answer_text,
            is_correct=1 if is_correct else 0,
            score=1.0 if is_correct else 0.0,
            time_spent=0,
            answered_at=datetime.now(timezone.utc),
        )
        self.db.add(new_record)

        if is_correct:
            # 攻克错题: 软删除原错题记录
            record.is_deleted = True

        await self.db.flush()

        return {
            "is_correct": is_correct,
            "correct_answer": quiz.answer,
            "explanation": quiz.explanation or "",
            "resolved": is_correct,
        }

    # ---------- 内部工具 ----------

    async def _get_verse(self, verse_id: int) -> Optional[Verse]:
        stmt = select(Verse).where(Verse.id == verse_id)
        return (await self.db.execute(stmt)).scalars().first()

    async def _get_quiz(self, quiz_id: int) -> Optional[Quiz]:
        stmt = select(Quiz).where(Quiz.id == quiz_id)
        return (await self.db.execute(stmt)).scalars().first()

    def _quiz_to_dict(self, quiz: Quiz) -> dict:
        return {
            "quiz_id": quiz.id,
            "verse_id": quiz.verse_id,
            "question_type": quiz.quiz_type,
            "difficulty": quiz.difficulty,
            "question": quiz.question,
            "options": quiz.options,
            # 不返回 answer，避免泄露答案
        }

    def _serialize_answer(self, answer: Any) -> str:
        """将用户答案序列化为文本存储。"""
        if isinstance(answer, str):
            return answer
        try:
            return json.dumps(answer, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(answer)

    def _parse_answer(self, answer_text: str) -> Any:
        """尝试将文本答案解析回 JSON。"""
        if not answer_text:
            return None
        try:
            return json.loads(answer_text)
        except (json.JSONDecodeError, TypeError):
            return answer_text

    def _check_answer(self, quiz: Quiz, user_answer: Any) -> bool:
        """
        根据题型判定答案是否正确。
        quiz.answer 是 Text，可能存纯文本或 JSON 字符串。
        """
        correct_raw = quiz.answer or ""
        correct = self._parse_answer(correct_raw)
        qtype = quiz.quiz_type

        if qtype == "choice":
            # 单选: 比较选中的索引
            if isinstance(correct, dict):
                correct_idx = correct.get("selected")
            else:
                correct_idx = correct
            if isinstance(user_answer, dict):
                user_idx = user_answer.get("selected")
            else:
                user_idx = user_answer
            return str(user_idx) == str(correct_idx)

        elif qtype == "fill":
            # 填空: 去除空白后比较
            if isinstance(correct, dict):
                correct_text = str(correct.get("text", "")).strip()
            else:
                correct_text = str(correct or "").strip()
            if isinstance(user_answer, dict):
                user_text = str(user_answer.get("text", "")).strip()
            else:
                user_text = str(user_answer or "").strip()
            return user_text == correct_text

        elif qtype == "match":
            # 配对: 比较配对映射
            if isinstance(correct, dict):
                correct_pairs = correct.get("pairs", {})
            else:
                correct_pairs = {}
            if isinstance(user_answer, dict):
                user_pairs = user_answer.get("pairs", {})
            else:
                user_pairs = {}
            return user_pairs == correct_pairs

        elif qtype == "link":
            # 连线: 比较连线集合
            if isinstance(correct, dict):
                correct_links = set(tuple(sorted(p)) for p in correct.get("links", []))
            else:
                correct_links = set()
            if isinstance(user_answer, dict):
                user_links = set(tuple(sorted(p)) for p in user_answer.get("links", []))
            else:
                user_links = set()
            return user_links == correct_links

        elif qtype in ("translate", "explain", "order"):
            # 翻译/解释/排序: 文本比较(容错空白)
            if isinstance(correct, dict):
                correct_text = str(correct.get("text", "")).strip()
            else:
                correct_text = str(correct or "").strip()
            if isinstance(user_answer, dict):
                user_text = str(user_answer.get("text", "")).strip()
            else:
                user_text = str(user_answer or "").strip()
            return user_text == correct_text

        else:
            return False

    def _generate_basic_quizzes(self, verse: Verse) -> list[Quiz]:
        """
        当题库不足时，根据经文动态生成基础题。
        生成: 1 道填空题(原文填空) + 1 道选择题(翻译选原文)。
        注意: 这些题对象仅在内存中用于返回，不落库(避免重复生成)。
        """
        quizzes: list[Quiz] = []
        text = verse.original_text or ""
        translation = verse.translation or ""

        if text and len(text) >= 4:
            fill_len = min(4, max(2, len(text) // 4))
            start = len(text) // 2 - fill_len // 2
            blank_text = text[:start] + "____" + text[start + fill_len:]
            answer_text = text[start:start + fill_len]

            q1 = Quiz(
                verse_id=verse.id,
                chapter_id=verse.chapter_id,
                book_id=verse.book_id,
                quiz_type="fill",
                difficulty=2,
                question=f"补全原文：{blank_text}",
                options=None,
                answer=json.dumps({"text": answer_text}, ensure_ascii=False),
                explanation=f"原文为：{text}",
            )
            quizzes.append(q1)

        if text and translation:
            q2 = Quiz(
                verse_id=verse.id,
                chapter_id=verse.chapter_id,
                book_id=verse.book_id,
                quiz_type="choice",
                difficulty=1,
                question=f"下列哪句原文对应此翻译：「{translation[:30]}...」",
                options=[
                    {"index": 0, "text": text},
                    {"index": 1, "text": "(干扰项)"},
                    {"index": 2, "text": "(干扰项)"},
                    {"index": 3, "text": "(干扰项)"},
                ],
                answer=json.dumps({"selected": 0}, ensure_ascii=False),
                explanation=f"原文「{text}」对应翻译「{translation}」",
            )
            quizzes.append(q2)

        return quizzes
