/**
 * 悟典 - 闯关/测验 mock 数据
 * 基于 mockChapters 经文动态生成填空/选择题，减少重复数据维护。
 */
import { mockChapters } from "./mockData";
import type {
  ChallengeLevel,
  ChallengeQuestion,
  ChallengeResult,
  ChallengeAnswer,
  QuestionFeedback,
} from "./types";

/** 根据章节顺序生成关卡列表 */
export function generateChallengeLevels(): ChallengeLevel[] {
  return mockChapters.map((chapter, index) => ({
    id: `level-${chapter.id}`,
    chapterId: chapter.id,
    title: chapter.title,
    order: chapter.order,
    sentenceCount: chapter.sentences.length,
    // 第一章默认解锁，其余按前一关通关解锁（本地 mock 中第一章已解锁）
    locked: index > 0,
    passed: false,
    bestScore: undefined,
    stars: 0,
  }));
}

/** 生成干扰项（从同章节其他句子中随机抽取） */
function generateDistractors(
  original: string,
  chapterIndex: number,
  count: number
): string[] {
  const others = mockChapters[chapterIndex].sentences
    .map((s) => s.original)
    .filter((s) => s !== original);
  const shuffled = others.sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}

/** 生成某关卡的全部题目 */
export function generateQuestionsForLevel(chapterId: string): ChallengeQuestion[] {
  const chapterIndex = mockChapters.findIndex((c) => c.id === chapterId);
  if (chapterIndex === -1) return [];

  const chapter = mockChapters[chapterIndex];
  const questions: ChallengeQuestion[] = [];

  chapter.sentences.forEach((sentence, idx) => {
    const original = sentence.original;
    const translation = sentence.translation || "";

    // 1. 填空题：遮住中间 2-4 个字
    if (original.length >= 6) {
      const blankLen = Math.min(4, Math.max(2, Math.floor(original.length / 4)));
      const start = Math.floor((original.length - blankLen) / 2);
      const blankText = original.slice(0, start) + "____" + original.slice(start + blankLen);
      const answer = original.slice(start, start + blankLen);

      questions.push({
        quizId: idx * 2 + 1,
        verseId: sentence.id,
        questionType: "fill",
        difficulty: 2,
        question: `补全原文：${blankText}`,
        correctAnswer: answer,
        explanation: `原文为：${original}。译文：${translation}`,
      });
    }

    // 2. 选择题：根据译文选原文
    if (translation) {
      const distractors = generateDistractors(original, chapterIndex, 3);
      const options = [original, ...distractors].sort(() => Math.random() - 0.5);

      questions.push({
        quizId: idx * 2 + 2,
        verseId: sentence.id,
        questionType: "choice",
        difficulty: 1,
        question: `下列哪句原文对应此翻译：「${translation.slice(0, 36)}${translation.length > 36 ? "..." : ""}」`,
        options: options.map((text, index) => ({ index, text })),
        correctAnswer: options.indexOf(original),
        explanation: `原文「${original}」对应译文「${translation}」`,
      });
    }
  });

  return questions;
}

/** 本地判题（mock 模式使用） */
export function judgeLocalAnswers(
  questions: ChallengeQuestion[],
  answers: ChallengeAnswer[]
): ChallengeResult {
  const startTime = Date.now();
  let totalTime = 0;
  const results: QuestionFeedback[] = [];
  let correctCount = 0;

  answers.forEach((answer) => {
    const q = questions.find((item) => item.quizId === answer.quizId);
    if (!q) return;

    totalTime += answer.timeSpent || 0;
    const user = answer.userAnswer;
    const correct = q.correctAnswer;
    let isCorrect = false;

    if (q.questionType === "choice") {
      isCorrect = String(user) === String(correct);
    } else if (q.questionType === "fill") {
      isCorrect = String(user).trim() === String(correct).trim();
    } else {
      isCorrect = String(user).trim() === String(correct).trim();
    }

    if (isCorrect) correctCount += 1;

    results.push({
      quizId: q.quizId,
      isCorrect,
      correctAnswer: correct,
      explanation: q.explanation || "",
    });
  });

  const total = answers.length;
  const score = total > 0 ? Math.round((correctCount / total) * 100) : 0;
  const passThreshold = 70;
  const passed = score >= passThreshold;

  return {
    total,
    correctCount,
    wrongCount: total - correctCount,
    score,
    passed,
    passThreshold,
    totalTime,
    results,
    expGained: passed ? (score === 100 ? 30 : 15) : 0,
  };
}

export const PASS_THRESHOLD = 70;
