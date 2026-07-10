from app.schemas.debate import ThoughtCompassResponse


ACTIVE_KEYWORDS = ["做", "行动", "意义", "责任", "承担", "努力", "改变", "实干", "进取"]
QUIET_KEYWORDS = ["歇", "休", "累", "放下", "自在", "不争", "平静", "躺平", "绑架", "焦虑"]
PUBLIC_KEYWORDS = ["责任", "天下", "他人", "社会", "工作", "团队", "家国", "公平"]


def analyze_thought_compass(statement: str) -> ThoughtCompassResponse:
    text = statement.strip()
    active_score = _score_text(text, ACTIVE_KEYWORDS)
    quiet_score = _score_text(text, QUIET_KEYWORDS)
    public_score = _score_text(text, PUBLIC_KEYWORDS)

    active_percent = _clamp(38 + active_score * 8 - quiet_score * 4 + public_score * 3, 8, 92)
    quiet_percent = _clamp(100 - active_percent, 8, 92)
    x = _clamp(active_percent, 5, 95)
    y = _clamp(44 + public_score * 8 + active_score * 4 - quiet_score * 3, 8, 92)
    nearest_school = _get_nearest_school(x, y)
    label = _build_label(active_percent, quiet_percent, public_score)

    return ThoughtCompassResponse(
        x=x,
        y=y,
        active_percent=active_percent,
        quiet_percent=quiet_percent,
        nearest_school=nearest_school,
        label=label,
        imprint=(
            f"今日论道，你自成一家，我们称之为「{label}」。"
            f"你的思想坐标：有为 {active_percent}% / 守静 {quiet_percent}%，最接近{nearest_school}。"
        ),
    )


def _score_text(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, round(value)))


def _get_nearest_school(x: int, y: int) -> str:
    if x >= 58 and y >= 54:
        return "儒墨之间"
    if x <= 42 and y <= 52:
        return "道家一侧"
    if x >= 58 and y <= 50:
        return "法家一侧"
    if 36 <= x <= 56 and 38 <= y <= 62:
        return "儒道之间"
    return "墨家一侧" if y > 60 else "儒道之间"


def _build_label(active_percent: int, quiet_percent: int, public_score: int) -> str:
    if quiet_percent > active_percent and active_percent >= 30:
        return "逍遥实干派"
    if active_percent >= 65 and public_score >= 2:
        return "担当进取派"
    if active_percent >= 65:
        return "务实行路派"
    if quiet_percent >= 65:
        return "守静自适派"
    return "中道调和派"
