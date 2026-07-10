export interface ThoughtCompassMark {
  x: number;
  y: number;
  activePercent: number;
  quietPercent: number;
  nearestSchool: string;
  label: string;
  imprint: string;
}

type BackendThoughtCompass = {
  x?: number;
  y?: number;
  active_percent?: number;
  quiet_percent?: number;
  nearest_school?: string;
  label?: string;
  imprint?: string;
};

export function normalizeBackendThoughtCompass(payload: BackendThoughtCompass): ThoughtCompassMark {
  return {
    x: payload.x ?? 50,
    y: payload.y ?? 50,
    activePercent: payload.active_percent ?? 50,
    quietPercent: payload.quiet_percent ?? 50,
    nearestSchool: payload.nearest_school || "儒道之间",
    label: payload.label || "中道调和派",
    imprint: payload.imprint || "今日论道，你的思想坐标已落定。",
  };
}

const activeKeywords = ["做", "行动", "意义", "责任", "承担", "努力", "改变", "实干", "进取"];
const quietKeywords = ["歇", "休", "累", "放下", "自在", "不争", "平静", "躺平", "绑架", "焦虑"];
const publicKeywords = ["责任", "天下", "他人", "社会", "工作", "团队", "家国", "公平"];

export function analyzeThoughtCompass(statement: string): ThoughtCompassMark {
  const text = statement.trim();
  const activeScore = scoreText(text, activeKeywords);
  const quietScore = scoreText(text, quietKeywords);
  const publicScore = scoreText(text, publicKeywords);

  const activePercent = clamp(38 + activeScore * 8 - quietScore * 4 + publicScore * 3, 8, 92);
  const quietPercent = clamp(100 - activePercent, 8, 92);
  const x = clamp(activePercent, 5, 95);
  const y = clamp(44 + publicScore * 8 + activeScore * 4 - quietScore * 3, 8, 92);
  const nearestSchool = getNearestSchool(x, y);
  const label = buildLabel(activePercent, quietPercent, publicScore);

  return {
    x,
    y,
    activePercent,
    quietPercent,
    nearestSchool,
    label,
    imprint: `今日论道，你自成一家，我们称之为「${label}」。你的思想坐标：有为 ${activePercent}% / 守静 ${quietPercent}%，最接近${nearestSchool}。`,
  };
}

function scoreText(text: string, keywords: string[]): number {
  return keywords.reduce((score, keyword) => score + (text.includes(keyword) ? 1 : 0), 0);
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.round(value)));
}

function getNearestSchool(x: number, y: number): string {
  if (x >= 58 && y >= 54) return "儒墨之间";
  if (x <= 42 && y <= 52) return "道家一侧";
  if (x >= 58 && y <= 50) return "法家一侧";
  if (x >= 36 && x <= 56 && y >= 38 && y <= 62) return "儒道之间";
  return y > 60 ? "墨家一侧" : "儒道之间";
}

function buildLabel(activePercent: number, quietPercent: number, publicScore: number): string {
  if (quietPercent > activePercent && activePercent >= 30) return "逍遥实干派";
  if (activePercent >= 65 && publicScore >= 2) return "担当进取派";
  if (activePercent >= 65) return "务实行路派";
  if (quietPercent >= 65) return "守静自适派";
  return "中道调和派";
}
