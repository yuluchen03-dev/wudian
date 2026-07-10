"""
悟典 - SRS 间隔重复算法 (SM-2 改进版)
纯函数实现，无外部依赖。

SM-2 算法核心思想：
  根据用户对知识点的回忆质量(0-5)，动态调整：
    - repetitions: 连续正确重复次数
    - ease_factor: 难度系数 EF (≥1.3)
    - interval:    下次复习间隔(天)

改进点：
  1. EF 下限保护到 1.3
  2. 引入"简单加成"(easy bonus) 提升"非常简单"时的间隔
  3. 质量评分 < 3 时重置重复次数并立即复习
  4. 添加 fuzz 抖动避免大量卡片同一天到期
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


# 默认参数
DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
EASY_BONUS = 1.3          # 质量为 5 时的间隔加成
FUZZ_RATIO = 0.05         # 间隔抖动比例 ±5%

# 质量评分含义 (SuperMemo 标准):
#   0 - 完全没有印象
#   1 - 错误，但看到答案觉得熟悉
#   2 - 错误，但看到答案觉得很容易想起来
#   3 - 勉强正确，回忆很费力
#   4 - 正确，略有迟疑
#   5 - 完美正确，毫不费力


@dataclass(frozen=True)
class SRSResult:
    """单次复习计算结果"""
    repetitions: int        # 新的连续正确次数
    ease_factor: float      # 新的难度系数
    interval_days: int      # 新的间隔(天)
    next_review_at: datetime  # 下次复习时间(UTC)
    is_relearn: bool        # 是否进入重学(质量<3)

    def to_dict(self) -> dict:
        return {
            "repetitions": self.repetitions,
            "ease_factor": round(self.ease_factor, 4),
            "interval_days": self.interval_days,
            "next_review_at": self.next_review_at.isoformat(),
            "is_relearn": self.is_relearn,
        }


def _fuzz_interval(interval: int) -> int:
    """对间隔施加 ±5% 的随机抖动，避免同批卡片同日到期"""
    if interval <= 1:
        return interval
    delta = max(1, int(interval * FUZZ_RATIO))
    return max(1, interval + random.randint(-delta, delta))


def sm2(
    quality: int,
    repetitions: int,
    ease_factor: float,
    interval_days: int,
    *,
    now: datetime | None = None,
    apply_fuzz: bool = True,
) -> SRSResult:
    """
    SM-2 改进算法核心计算。

    参数:
        quality:      本次答题质量 0-5
        repetitions:  之前的连续正确次数
        ease_factor:  之前的难度系数 (≥1.3)
        interval_days:之前的间隔天数
        now:          当前时间(测试注入)，默认 UTC now
        apply_fuzz:   是否对间隔施加抖动

    返回:
        SRSResult: 包含更新后的 repetitions / ease_factor / interval_days / next_review_at
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # 参数校验
    if quality < 0 or quality > 5:
        raise ValueError(f"quality 必须在 0-5 之间，收到 {quality}")
    if ease_factor < MIN_EASE_FACTOR:
        ease_factor = MIN_EASE_FACTOR
    if repetitions < 0:
        repetitions = 0
    if interval_days < 0:
        interval_days = 0

    # ---- 1. 更新难度系数 EF ----
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if new_ef < MIN_EASE_FACTOR:
        new_ef = MIN_EASE_FACTOR

    # ---- 2. 计算重复次数与间隔 ----
    is_relearn = quality < 3

    if is_relearn:
        # 回忆失败: 重置重复次数，当天/次日复习
        new_reps = 0
        new_interval = 1 if quality == 0 else 1
    else:
        # 回忆成功
        new_reps = repetitions + 1
        if new_reps == 1:
            new_interval = 1
        elif new_reps == 2:
            new_interval = 3
        else:
            # 间隔 = 上次间隔 * EF
            base_interval = max(interval_days, 1) * new_ef
            # 质量为 5 (完美) 时给予 easy bonus
            if quality == 5:
                base_interval *= EASY_BONUS
            new_interval = int(round(base_interval))

    new_interval = max(1, int(new_interval))

    if apply_fuzz and new_interval > 1:
        new_interval = _fuzz_interval(new_interval)

    # ---- 3. 计算下次复习时间 ----
    next_review_at = now + timedelta(days=new_interval)

    return SRSResult(
        repetitions=new_reps,
        ease_factor=round(new_ef, 4),
        interval_days=new_interval,
        next_review_at=next_review_at,
        is_relearn=is_relearn,
    )


def quality_from_correctness(is_correct: bool, *, hesitation_seconds: float = 0.0) -> int:
    """
    根据答题正确性与犹豫时间，映射到 SM-2 质量评分。
    适用于前端仅返回"对/错"的简化场景。
    """
    if not is_correct:
        return 2
    # 正确: 根据犹豫时间细分
    if hesitation_seconds <= 3:
        return 5
    elif hesitation_seconds <= 8:
        return 4
    else:
        return 3


def is_due(next_review_at: datetime | None, *, now: datetime | None = None) -> bool:
    """判断某条复习记录是否已到期(含过期)"""
    if next_review_at is None:
        return False
    if now is None:
        now = datetime.now(timezone.utc)
    return next_review_at <= now
