# Frontend Contracts and Learning Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the real-API frontend honor backend contracts and complete reading, review, challenge, achievement, community, and AI flows without false success or permanent loading states.

**Architecture:** Introduce runtime-validated API contracts and typed errors at the network boundary. Add stable public slugs to bridge the JSON classics catalog with relational learning records, persist chapter reading and challenge attempts, and model every page request as explicit loading/success/empty/error state.

**Tech Stack:** Next.js, React, TypeScript, Axios, Zod, Vitest, Testing Library, FastAPI, SQLAlchemy, pytest.

---

## File Structure

- Modify `frontend/package.json`, `frontend/package-lock.json`: add Vitest, jsdom, Testing Library, user-event, and Zod.
- Create `frontend/vitest.config.ts`, `frontend/tests/setup.tsx`: component/unit test environment.
- Create `frontend/lib/api-error.ts`: typed normalized request errors.
- Create `frontend/lib/contracts.ts`: Zod schemas and adapters for backend response envelopes.
- Create `frontend/lib/sse.ts`: reusable parser with business-error propagation and cancellation.
- Modify `frontend/lib/api.ts`: consume contracts, Cookie refresh, idempotency keys, and exact learning endpoints.
- Modify `frontend/lib/auth.ts`: memory-only access token plus non-sensitive session/user state.
- Modify `frontend/lib/types.ts`: types that match real backend semantics.
- Modify `frontend/app/login/page.tsx`, `frontend/app/register/page.tsx`, `frontend/components/Navbar.tsx`: async session bootstrap and server logout.
- Modify `backend/app/models/classic.py`: stable `slug`/`external_id` fields.
- Create `backend/app/models/challenge.py`: durable chapter attempt.
- Modify `backend/app/models/__init__.py`, `backend/app/services/seed_service.py`: export and populate stable IDs.
- Create `backend/migrations/versions/20260719_03_learning_contracts.py`: slug, progress, and challenge schema changes/backfill.
- Modify `backend/app/schemas/learning.py`, `backend/app/services/progress_service.py`, `backend/app/services/quiz_service.py`, `backend/app/api/learning.py`: chapter read/progress/challenge contracts.
- Modify `frontend/app/achievements/page.tsx`, `frontend/app/review/page.tsx`, `frontend/app/challenge/page.tsx`, `frontend/app/reader/page.tsx`, `frontend/app/community/page.tsx`: real response and error states.
- Modify `frontend/components/reader/ReadingView.tsx`: target highlight and persisted read state.
- Modify `frontend/components/sage/SageChat.tsx`: complete citation navigation.
- Modify `frontend/components/community/PKArena.tsx`: deterministic timer and single submission.
- Create focused `.test.ts`, `.test.tsx`, and backend test files named in each task.

### Task 1: Add Behavioral Frontend Tests and Typed API Errors

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/tests/setup.tsx`
- Create: `frontend/lib/api-error.ts`
- Test: `frontend/tests/apiError.test.ts`

- [ ] **Step 1: Install the test and contract dependencies**

Run from `frontend/`:

```bash
npm install zod
npm install --save-dev vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Add scripts:

```json
{
  "scripts": {
    "test:unit": "vitest run",
    "test:unit:watch": "vitest",
    "typecheck": "tsc --noEmit"
  }
}
```

- [ ] **Step 2: Configure Vitest**

```typescript
// frontend/vitest.config.ts
import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.tsx"],
    include: ["tests/**/*.test.{ts,tsx}"],
    restoreMocks: true,
  },
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
});
```

```typescript
// frontend/tests/setup.tsx
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 3: Write failing normalized-error tests**

```typescript
// frontend/tests/apiError.test.ts
import { describe, expect, it } from "vitest";
import { ApiError, normalizeApiError } from "@/lib/api-error";

describe("normalizeApiError", () => {
  it("preserves backend code, status, request id, and retry delay", () => {
    const error = normalizeApiError({
      response: {
        status: 429,
        data: { code: "rate_limited", message: "请求过于频繁", request_id: "request-123" },
        headers: { "retry-after": "30" },
      },
    });
    expect(error).toEqual(expect.objectContaining({ code: "rate_limited", status: 429, requestId: "request-123", retryAfter: 30 }));
  });

  it("maps transport failures without claiming success", () => {
    const error = normalizeApiError({ request: {} });
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe("network_error");
  });
});
```

- [ ] **Step 4: Run and verify failure**

```bash
npm run test:unit -- apiError.test.ts
```

Expected: FAIL because `frontend/lib/api-error.ts` is absent.

- [ ] **Step 5: Implement the typed error**

```typescript
// frontend/lib/api-error.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status?: number,
    public readonly requestId?: string,
    public readonly retryAfter?: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type AxiosLikeError = {
  response?: { status?: number; data?: Record<string, unknown>; headers?: Record<string, string> };
  request?: unknown;
  message?: string;
};

export function normalizeApiError(input: unknown): ApiError {
  if (input instanceof ApiError) return input;
  const error = (input ?? {}) as AxiosLikeError;
  if (error.response) {
    const data = error.response.data ?? {};
    const retry = Number(error.response.headers?.["retry-after"]);
    return new ApiError(
      typeof data.message === "string" ? data.message : `请求失败 (${error.response.status ?? 0})`,
      typeof data.code === "string" ? data.code : `http_${error.response.status ?? 0}`,
      error.response.status,
      typeof data.request_id === "string" ? data.request_id : undefined,
      Number.isFinite(retry) ? retry : undefined,
      data.details,
    );
  }
  if (error.request) return new ApiError("网络异常，请检查连接后重试", "network_error");
  return new ApiError(error.message || "请求失败", "client_error");
}
```

- [ ] **Step 6: Run and commit**

```bash
npm run test:unit -- apiError.test.ts
npm run typecheck
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/tests/setup.tsx frontend/lib/api-error.ts frontend/tests/apiError.test.ts
git commit -m "test: add frontend behavioral test harness"
```

Expected: test and typecheck PASS.

### Task 2: Move Authentication to Memory and Refresh Cookies

**Files:**
- Modify: `frontend/lib/auth.ts`
- Modify: `frontend/lib/api.ts`
- Create: `frontend/lib/contracts.ts`
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/app/login/page.tsx`
- Modify: `frontend/app/register/page.tsx`
- Modify: `frontend/components/Navbar.tsx`
- Test: `frontend/tests/authSession.test.ts`

- [ ] **Step 1: Write failing session-store tests**

```typescript
// frontend/tests/authSession.test.ts
import { beforeEach, describe, expect, it } from "vitest";
import { authSession } from "@/lib/auth";

describe("authSession", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    authSession.clear();
  });

  it("keeps access token in memory and never localStorage", () => {
    authSession.set({ accessToken: "access", csrfToken: "csrf", user: { id: 1, username: "alice", email: "a@example.test", level: 1, expPoints: 0 } });
    expect(authSession.getAccessToken()).toBe("access");
    expect(localStorage.getItem("wudian_access_token")).toBeNull();
    expect(localStorage.getItem("wudian_refresh_token")).toBeNull();
  });

  it("clear removes memory and non-sensitive cached user", () => {
    authSession.set({ accessToken: "access", csrfToken: "csrf", user: { id: 1, username: "alice", email: "a@example.test", level: 1, expPoints: 0 } });
    authSession.clear();
    expect(authSession.getSnapshot().authenticated).toBe(false);
    expect(sessionStorage.getItem("wudian_user")).toBeNull();
  });
});
```

- [ ] **Step 2: Run and verify failure**

```bash
npm run test:unit -- authSession.test.ts
```

Expected: FAIL because tokens are stored in `localStorage` and `authSession` does not exist.

- [ ] **Step 3: Implement the in-memory external store**

```typescript
// frontend/lib/auth.ts
import type { UserInfo } from "./types";

type Session = { accessToken: string | null; csrfToken: string | null; user: UserInfo | null; initialized: boolean };
type Snapshot = Session & { authenticated: boolean };
const storedCsrf = typeof window === "undefined" ? null : sessionStorage.getItem("wudian_csrf");
let state: Session = { accessToken: null, csrfToken: storedCsrf, user: null, initialized: false };
let snapshot: Snapshot = { ...state, authenticated: false };
const listeners = new Set<() => void>();

function publish(next: Session) {
  state = next;
  snapshot = { ...next, authenticated: Boolean(next.accessToken && next.user) };
  listeners.forEach((listener) => listener());
}

export const authSession = {
  getSnapshot: () => snapshot,
  subscribe(listener: () => void) { listeners.add(listener); return () => listeners.delete(listener); },
  getAccessToken: () => state.accessToken,
  getCsrfToken: () => state.csrfToken,
  set(input: { accessToken: string; csrfToken: string; user: UserInfo }) {
    publish({ ...input, initialized: true });
    sessionStorage.setItem("wudian_user", JSON.stringify(input.user));
    sessionStorage.setItem("wudian_csrf", input.csrfToken);
  },
  markInitialized() { publish({ ...state, initialized: true }); },
  clear() { publish({ accessToken: null, csrfToken: null, user: null, initialized: true }); sessionStorage.removeItem("wudian_user"); sessionStorage.removeItem("wudian_csrf"); },
};
```

- [ ] **Step 4: Define and use the authentication response contract**

```typescript
// frontend/lib/contracts.ts
import { z } from "zod";

const user = z.object({
  id: z.number(), username: z.string(), email: z.string(), nickname: z.string().nullable().optional(),
  avatar: z.string().nullable().optional(), level: z.number(), exp_points: z.number(),
});
const auth = z.object({ access_token: z.string().min(1), token_type: z.literal("bearer"), csrf_token: z.string().min(1), user });

export function parseAuthResponse(input: unknown) {
  const value = auth.parse(input);
  return {
    accessToken: value.access_token,
    csrfToken: value.csrf_token,
    user: { id: value.user.id, username: value.user.username, email: value.user.email, nickname: value.user.nickname ?? undefined, avatar: value.user.avatar ?? undefined, level: value.user.level, expPoints: value.user.exp_points },
  };
}
```

- [ ] **Step 5: Change Axios to Cookie refresh**

Set `withCredentials: true`. Attach `authSession.getAccessToken()` in the request interceptor. Refresh with an empty body, credentials, and `X-CSRF-Token`; never read or write a refresh token in JavaScript.

```typescript
const resp = await axios.post(`${API_BASE}/auth/refresh`, {}, {
  withCredentials: true,
  headers: { "X-CSRF-Token": authSession.getCsrfToken() ?? "" },
});
authSession.set(parseAuthResponse(resp.data));
```

Normalize every rejection with `normalizeApiError`. A 401 from login/register/refresh does not recurse; one refresh can be active at a time; queued requests receive the new in-memory access token or the same terminal auth error.

- [ ] **Step 6: Bootstrap and clear the server session**

Add `api.bootstrapSession()` that calls `/auth/csrf` when `authSession.getCsrfToken()` is empty, stores the returned non-sensitive token in the session store, then calls refresh once and marks the store initialized on 401. Add `api.logout()` that POSTs `/auth/logout` with the CSRF header and clears local state in `finally`. The root layout calls bootstrap once before rendering auth-dependent navigation.

Login/register call `authSession.set` from the new response shape. Navbar renders its auth actions from `useSyncExternalStore(authSession.subscribe, authSession.getSnapshot, authSession.getSnapshot)` and calls the server logout before navigation.

- [ ] **Step 7: Run tests and forbidden storage search**

```bash
npm run test:unit -- authSession.test.ts
npm run typecheck
rg -n "wudian_refresh_token|localStorage.*access|refresh_token:" frontend --glob '!node_modules/**'
```

Expected: tests/typecheck PASS; no production frontend token persistence remains.

- [ ] **Step 8: Commit**

```bash
git add frontend/lib/auth.ts frontend/lib/api.ts frontend/lib/contracts.ts frontend/lib/types.ts frontend/app/login/page.tsx frontend/app/register/page.tsx frontend/components/Navbar.tsx frontend/tests/authSession.test.ts
git commit -m "fix: keep auth tokens out of browser storage"
```

### Task 3: Validate Achievement, Rank, and Review Contracts

**Files:**
- Modify: `frontend/lib/contracts.ts`
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/achievements/page.tsx`
- Modify: `frontend/app/review/page.tsx`
- Test: `frontend/tests/learningContracts.test.ts`
- Test: `frontend/tests/reviewFlow.test.tsx`

- [ ] **Step 1: Write failing real-response adapter tests**

```typescript
// frontend/tests/learningContracts.test.ts
import { describe, expect, it } from "vitest";
import { parseAchievements, parseRank, parseReviewStats } from "@/lib/contracts";

describe("learning contracts", () => {
  it("parses the backend achievement envelope", () => {
    const result = parseAchievements({ code: 0, message: "ok", data: { total: 1, unlocked_count: 0, achievements: [{ code: "first_read", type: "learning", name: "初窥门径", description: "完成阅读", icon: "BookOpen", exp_reward: 10, unlocked: false, unlocked_at: null }] } });
    expect(result.total).toBe(1);
    expect(result.achievements[0]).toEqual(expect.objectContaining({ code: "first_read", expReward: 10, unlocked: false }));
  });

  it("normalizes rank percentage to 0..100 without NaN", () => {
    const result = parseRank({ code: 0, message: "ok", data: { current_rank: { code: "scholar", name: "秀才", min_exp: 100, icon: "Book" }, next_rank: null, exp: 5000, exp_to_next: 0, progress_pct: 100, all_ranks: [] } });
    expect(result.progressPct).toBe(100);
    expect(Number.isNaN(result.progressPct)).toBe(false);
  });

  it("maps backend review counters exactly", () => {
    expect(parseReviewStats({ code: 0, message: "ok", data: { due_count: 2, mastered_count: 3, learning_count: 4, reviewed_today: 5, total_in_srs: 9 } }).reviewedToday).toBe(5);
  });
});
```

- [ ] **Step 2: Run and verify failure**

```bash
npm run test:unit -- learningContracts.test.ts
```

Expected: FAIL because the parsers and matching types do not exist.

- [ ] **Step 3: Define exact Zod contracts and adapters**

```typescript
// append to frontend/lib/contracts.ts

const envelope = <T extends z.ZodTypeAny>(data: T) => z.object({ code: z.number(), message: z.string(), data });
const achievement = z.object({ code: z.string(), type: z.string(), name: z.string(), description: z.string().nullable(), icon: z.string().nullable(), exp_reward: z.number(), unlocked: z.boolean(), unlocked_at: z.string().nullable() });
const achievements = envelope(z.object({ total: z.number(), unlocked_count: z.number(), achievements: z.array(achievement) }));
const rankDefinition = z.object({ code: z.string(), name: z.string(), min_exp: z.number(), icon: z.string() });
const rank = envelope(z.object({ current_rank: rankDefinition, next_rank: rankDefinition.nullable(), exp: z.number(), exp_to_next: z.number(), progress_pct: z.number().finite().min(0).max(100), all_ranks: z.array(rankDefinition) }));
const reviewStats = envelope(z.object({ due_count: z.number(), mastered_count: z.number(), learning_count: z.number(), reviewed_today: z.number(), total_in_srs: z.number() }));

export const parseAchievements = (input: unknown) => {
  const value = achievements.parse(input).data;
  return { total: value.total, unlockedCount: value.unlocked_count, achievements: value.achievements.map((item) => ({ code: item.code, type: item.type, name: item.name, description: item.description ?? "", icon: item.icon ?? "Award", expReward: item.exp_reward, unlocked: item.unlocked, unlockedAt: item.unlocked_at ?? undefined })) };
};
export const parseRank = (input: unknown) => {
  const value = rank.parse(input).data;
  const mapDefinition = (item: z.infer<typeof rankDefinition>) => ({ code: item.code, name: item.name, minExp: item.min_exp, icon: item.icon });
  return { currentRank: mapDefinition(value.current_rank), nextRank: value.next_rank ? mapDefinition(value.next_rank) : null, exp: value.exp, expToNext: value.exp_to_next, progressPct: value.progress_pct, allRanks: value.all_ranks.map(mapDefinition) };
};
export const parseReviewStats = (input: unknown) => {
  const value = reviewStats.parse(input).data;
  return { dueCount: value.due_count, masteredCount: value.mastered_count, learningCount: value.learning_count, reviewedToday: value.reviewed_today, totalInSrs: value.total_in_srs };
};
```

Add matching exported interfaces to `frontend/lib/types.ts`; remove the legacy `unlocked/locked`, numeric `current_rank`, fractional `progress`, and fake review metrics.

- [ ] **Step 4: Consume only parsed contracts**

`api.getAchievements`, `getRank`, `getReviewStats`, and `getDueReviews` pass the complete response envelope to parsers. `AchievementsPage` filters `achievements` by `unlocked`; `RankCard` displays `rank.currentRank.name` and uses `rank.progressPct` directly. `ReviewPage` renders only counters the server actually returns.

- [ ] **Step 5: Write and run the failed-review UI test**

```typescript
// frontend/tests/reviewFlow.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

vi.mock("@/lib/api", () => ({ api: { getDueReviews: vi.fn().mockResolvedValue({ dueCount: 1, items: [{ recordId: 1, verseId: 1, originalText: "学而时习之", translation: "学习后复习", repetitions: 1, easeFactor: 2.5, intervalDays: 1, nextReviewAt: null }] }), getReviewStats: vi.fn().mockResolvedValue({ dueCount: 1, masteredCount: 0, learningCount: 1, reviewedToday: 0, totalInSrs: 1 }), submitReview: vi.fn().mockRejectedValue(new Error("offline")) } }));

it("keeps the current card and shows an error when review submission fails", async () => {
  const ReviewPage = (await import("@/app/review/page")).default;
  render(<ReviewPage />);
  await screen.findByText("学而时习之");
  await userEvent.click(screen.getByRole("button", { name: /记得很清楚/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent("提交失败");
  expect(screen.getByText("学而时习之")).toBeInTheDocument();
  expect(screen.queryByText("复习完成")).not.toBeInTheDocument();
});
```

- [ ] **Step 6: Verify and commit**

```bash
npm run test:unit -- learningContracts.test.ts reviewFlow.test.tsx
npm run typecheck
git add frontend/lib/contracts.ts frontend/lib/types.ts frontend/lib/api.ts frontend/app/achievements/page.tsx frontend/app/review/page.tsx frontend/tests/learningContracts.test.ts frontend/tests/reviewFlow.test.tsx
git commit -m "fix: align learning response contracts"
```

Expected: tests and typecheck PASS; no `NaN%` path remains.

### Task 4: Add Stable Learning IDs and a Persistent Chapter Challenge

**Files:**
- Modify: `backend/app/models/classic.py`
- Create: `backend/app/models/challenge.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/services/seed_service.py`
- Modify: `backend/app/schemas/learning.py`
- Modify: `backend/app/services/progress_service.py`
- Modify: `backend/app/services/quiz_service.py`
- Modify: `backend/app/api/learning.py`
- Create: `backend/migrations/versions/20260719_03_learning_contracts.py`
- Test: `backend/tests/test_chapter_challenge.py`
- Modify: `frontend/lib/contracts.ts`
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/challenge/page.tsx`
- Test: `frontend/tests/challengeFlow.test.tsx`

- [ ] **Step 1: Write failing backend chapter-contract tests**

```python
# backend/tests/test_chapter_challenge.py
import pytest


@pytest.mark.asyncio
async def test_chapter_quiz_uses_chapter_slug_not_verse_id(authenticated_client, seeded_lunyu):
    response = await authenticated_client.get("/api/learning/quiz/chapter/lunyu-1?count=10")
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert items
    assert {item["chapter_id"] for item in items} == {seeded_lunyu.first_chapter_id}


@pytest.mark.asyncio
async def test_chapter_attempt_is_persisted_and_replayed(authenticated_client, seeded_lunyu):
    quiz = (await authenticated_client.get("/api/learning/quiz/chapter/lunyu-1?count=3")).json()["data"]["items"]
    payload = {"chapter_slug": "lunyu-1", "answers": [{"quiz_id": item["quiz_id"], "user_answer": {}, "time_spent": 1} for item in quiz]}
    headers = {"Idempotency-Key": "chapter-attempt-0001"}
    first = await authenticated_client.post("/api/learning/quiz/chapter/submit", json=payload, headers=headers)
    second = await authenticated_client.post("/api/learning/quiz/chapter/submit", json=payload, headers=headers)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_chapter_challenge.py -q
```

Expected: FAIL because only `/quiz/{verse_id}` exists.

- [ ] **Step 3: Add stable external identifiers**

Add these columns and constraints:

```python
class ClassicBook(Base, BaseModelMixin):
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

class Chapter(Base, BaseModelMixin):
    external_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False, index=True)

class Verse(Base, BaseModelMixin):
    external_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False, index=True)
```

The seed writes `ClassicBook.slug="lunyu"`, `Chapter.external_id=f"lunyu-{chapter_number}"`, and `Verse.external_id=f"lunyu-{json_verse_id}"`. Prefixing verse IDs prevents collisions when more classics are seeded. The migration backfills existing Lunyu rows before setting `nullable=False`.

- [ ] **Step 4: Add a durable challenge attempt**

```python
# backend/app/models/challenge.py
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ChallengeAttempt(Base):
    __tablename__ = "challenge_attempts"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_challenge_user_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id: Mapped[int] = mapped_column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

- [ ] **Step 5: Add chapter endpoints and validate question ownership**

Define `GET /quiz/chapter/{chapter_slug}` before `/quiz/{verse_id}`. Resolve the chapter by `Chapter.external_id`, call `QuizService.get_quiz_for_chapter`, and include `chapter_id` and `chapter_slug` in the response.

Define `POST /quiz/chapter/submit` with:

```python
class ChapterQuizSubmitRequest(BaseModel):
    chapter_slug: str
    answers: list[QuizAnswerItem] = Field(min_length=1, max_length=20)
```

Before scoring, query every submitted quiz ID and reject 422 if any quiz belongs to a different chapter. Hash the canonical request payload. A matching user/key/hash replays `result_json`; a matching user/key with a different hash returns 409. Store the `ChallengeAttempt`, quiz records, and reward in one transaction; do not also create a generic `IdempotencyRecord` for this endpoint. `ProgressService.get_chapter_tree` marks a chapter completed when the user has at least one passed `ChallengeAttempt`; the next chapter unlocks only after that.

- [ ] **Step 6: Generate migration and run backend tests**

```bash
python -m alembic revision --autogenerate --rev-id 20260719_03 -m "learning contracts"
python -m alembic upgrade head
python -m pytest tests/test_chapter_challenge.py -q
python -m alembic check
```

Expected: PASS and no pending migration operations.

- [ ] **Step 7: Change the frontend challenge contract**

`ChallengeLevel.chapterSlug` replaces the ambiguous `chapterId`. `api.getChallengeQuestions` calls `/learning/quiz/chapter/${chapterSlug}`. `submitChallengeAnswers` sends `chapter_slug`, an `Idempotency-Key` generated once when the attempt begins, and never sends `verse_id: Number(chapterId)`.

```typescript
// frontend/tests/challengeFlow.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

const { apiMock } = vi.hoisted(() => ({ apiMock: {
  getChallengeLevels: vi.fn(), getChallengeQuestions: vi.fn(), submitChallengeAnswers: vi.fn(),
} }));
vi.mock("@/lib/api", () => ({ api: apiMock }));

beforeEach(() => vi.clearAllMocks());

it("leaves loading, shows retry, and recovers after level loading fails", async () => {
  apiMock.getChallengeLevels
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValueOnce([{ id: "lunyu-1", chapterSlug: "lunyu-1", title: "学而", order: 1, sentenceCount: 3, locked: false, passed: false, stars: 0 }]);
  const ChallengePage = (await import("@/app/challenge/page")).default;
  render(<ChallengePage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("加载失败");
  expect(screen.queryByText("正在加载闯关地图")).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "重新加载" }));
  expect(await screen.findByText("学而")).toBeInTheDocument();
  expect(apiMock.getChallengeLevels).toHaveBeenCalledTimes(2);
});
```

- [ ] **Step 8: Verify and commit**

```bash
python -m pytest backend/tests/test_chapter_challenge.py -q
npm --prefix frontend run test:unit -- challengeFlow.test.tsx
npm --prefix frontend run typecheck
git add backend/app/models/classic.py backend/app/models/challenge.py backend/app/models/__init__.py backend/app/services/seed_service.py backend/app/schemas/learning.py backend/app/services/progress_service.py backend/app/services/quiz_service.py backend/app/api/learning.py backend/migrations/versions/20260719_03_learning_contracts.py backend/tests/test_chapter_challenge.py frontend/lib/contracts.ts frontend/lib/types.ts frontend/lib/api.ts frontend/app/challenge/page.tsx frontend/tests/challengeFlow.test.tsx
git commit -m "fix: persist chapter challenge attempts"
```

### Task 5: Persist Chapter Reading and Honor Citation Targets

**Files:**
- Modify: `backend/app/schemas/learning.py`
- Modify: `backend/app/services/progress_service.py`
- Modify: `backend/app/api/learning.py`
- Test: `backend/tests/test_book_progress.py`
- Modify: `frontend/lib/contracts.ts`
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/reader/page.tsx`
- Modify: `frontend/components/reader/ReadingView.tsx`
- Modify: `frontend/components/sage/SageChat.tsx`
- Create: `frontend/lib/citation-target.ts`
- Test: `frontend/tests/readerPersistence.test.tsx`
- Test: `frontend/tests/citationNavigation.test.tsx`

- [ ] **Step 1: Write failing persisted progress tests**

```python
# backend/tests/test_book_progress.py
import pytest


@pytest.mark.asyncio
async def test_complete_chapter_marks_all_verses_read(authenticated_client, seeded_lunyu):
    headers = {"Idempotency-Key": "read-lunyu-1-0001"}
    completed = await authenticated_client.post("/api/learning/chapters/lunyu-1/complete", json={"study_duration": 60}, headers=headers)
    assert completed.status_code == 200
    progress = await authenticated_client.get("/api/learning/books/lunyu/progress")
    assert progress.json()["data"]["read_chapter_ids"] == ["lunyu-1"]


@pytest.mark.asyncio
async def test_book_progress_is_isolated_by_user(user_client_factory, seeded_lunyu):
    _, alice = await user_client_factory("alice")
    _, bob = await user_client_factory("bob")
    await alice.post("/api/learning/chapters/lunyu-1/complete", json={"study_duration": 10}, headers={"Idempotency-Key": "alice-read-0001"})
    assert (await bob.get("/api/learning/books/lunyu/progress")).json()["data"]["read_chapter_ids"] == []
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_book_progress.py -q
```

Expected: FAIL because only aggregate progress and `complete-verse` exist.

- [ ] **Step 3: Add exact book/chapter progress endpoints**

```python
class CompleteChapterRequest(BaseModel):
    study_duration: int = Field(default=0, ge=0, le=86400)

class BookProgressResponse(BaseModel):
    book_slug: str
    total_chapters: int
    read_chapter_ids: list[str]
    current_chapter_id: str | None
    streak_days: int
    last_read_at: str | None
```

`complete_chapter` resolves all non-deleted verses in `Chapter.external_id`, updates their progress in one bulk service method, divides duration deterministically across verses, calls `_sync_user_stats` once, and stores one idempotent response. `get_book_progress` considers a chapter read only when every non-deleted verse has mastery at least `MASTERY_READ`; it returns stable external IDs, not numeric counts masquerading as chapter arrays.

- [ ] **Step 4: Write failing reader and citation tests**

```typescript
// frontend/tests/readerPersistence.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { ToastProvider } from "@/components/ui/Toast";

const { apiMock } = vi.hoisted(() => ({ apiMock: {
  getChapters: vi.fn().mockResolvedValue([{ id: "lunyu-1", bookId: "lunyu", order: 1, title: "学而", sentences: [] }]),
  getChapter: vi.fn().mockResolvedValue({ id: "lunyu-1", bookId: "lunyu", order: 1, title: "学而", sentences: [{ id: "1.1", original: "学而时习之", translation: "学习后复习" }] }),
  getBookProgress: vi.fn().mockResolvedValue({ bookSlug: "lunyu", totalChapters: 1, readChapterIds: [], currentChapterId: null, streakDays: 0, lastReadAt: null }),
  completeChapter: vi.fn().mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce({ bookSlug: "lunyu", totalChapters: 1, readChapterIds: ["lunyu-1"], currentChapterId: "lunyu-1", streakDays: 1, lastReadAt: "2026-07-19T00:00:00Z" }),
} }));
vi.mock("@/lib/api", () => ({ api: apiMock }));
vi.mock("next/navigation", () => ({ useSearchParams: () => new URLSearchParams("book=lunyu&chapter=lunyu-1&highlight=学而时习之") }));

it("shows success only after chapter progress is persisted", async () => {
  const ReaderPage = (await import("@/app/reader/page")).default;
  render(<ToastProvider><ReaderPage /></ToastProvider>);
  expect(await screen.findByText("学而时习之")).toBeInTheDocument();
  const button = screen.getByRole("button", { name: "标记已读" });
  await userEvent.click(button);
  expect(await screen.findByText(/保存阅读进度失败/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "标记已读" })).toBeEnabled();
  await userEvent.click(screen.getByRole("button", { name: "标记已读" }));
  expect(await screen.findByRole("button", { name: /本章已读/ })).toBeDisabled();
});
```

```typescript
// frontend/tests/citationNavigation.test.ts
import { expect, it } from "vitest";
import { citationReaderUrl } from "@/lib/citation-target";

it("builds a complete reader target for a Lunyu citation", () => {
  const url = citationReaderUrl({ text: "学而时习之", source: "《论语·学而》", chapter: "学而篇" });
  const parsed = new URL(url, "https://app.example.test");
  expect(parsed.pathname).toBe("/reader");
  expect(parsed.searchParams.get("book")).toBe("lunyu");
  expect(parsed.searchParams.get("chapter")).toBe("lunyu-1");
  expect(parsed.searchParams.get("highlight")).toBe("学而时习之");
});
```

- [ ] **Step 5: Consume route parameters and render a real mark**

`ReaderContent` reads `book`, `chapter`, `highlight`, and `source`. It selects the requested chapter after loading the list. Pass `highlight` into `ReadingView`; split only the matching original text and render:

```tsx
<mark data-reader-highlight className="bg-bronze-200/70 text-inherit dark:bg-bronze-700/60">
  {matchedText}
</mark>
```

After the target chapter mounts, scroll the first `[data-reader-highlight]` into view. If no match exists, keep the correct chapter open and show a non-blocking toast. Replace `ReadingView`'s numeric `readChapters` prop with `readChapterIds: string[]` and compare `chapter.id`, never display order numbers as persisted IDs. `handleChapterRead` awaits `api.completeChapter`, updates from the returned server progress, and shows success only afterward.

Create the tested helper:

```typescript
// frontend/lib/citation-target.ts
const LUNYU_CHAPTERS = ["学而", "为政", "八佾", "里仁", "公冶长", "雍也", "述而", "泰伯", "子罕", "乡党", "先进", "颜渊", "子路", "宪问", "卫灵公", "季氏", "阳货", "微子", "子张", "尧曰"];

type CitationTarget = { text: string; source: string; chapter?: string; book?: string; chapterId?: string };

export function citationReaderUrl(citation: CitationTarget): string {
  const source = citation.source || "";
  const book = citation.book || (source.includes("论语") ? "lunyu" : undefined);
  const chapterIndex = LUNYU_CHAPTERS.findIndex((title) => source.includes(title) || citation.chapter?.includes(title));
  const chapter = citation.chapterId || (book === "lunyu" && chapterIndex >= 0 ? `lunyu-${chapterIndex + 1}` : undefined);
  const params = new URLSearchParams();
  if (book) params.set("book", book);
  if (chapter) params.set("chapter", chapter);
  if (citation.text) params.set("highlight", citation.text);
  if (source) params.set("source", source);
  return `/reader?${params.toString()}`;
}
```

`SageChat` calls this function for every citation instead of requiring `citation.chapter` and constructing a partial URL inline.

- [ ] **Step 6: Verify and commit**

```bash
python -m pytest backend/tests/test_book_progress.py -q
npm --prefix frontend run test:unit -- readerPersistence.test.tsx citationNavigation.test.tsx
npm --prefix frontend run typecheck
git add backend/app/schemas/learning.py backend/app/services/progress_service.py backend/app/api/learning.py backend/tests/test_book_progress.py frontend/lib/contracts.ts frontend/lib/citation-target.ts frontend/lib/types.ts frontend/lib/api.ts frontend/app/reader/page.tsx frontend/components/reader/ReadingView.tsx frontend/components/sage/SageChat.tsx frontend/tests/readerPersistence.test.tsx frontend/tests/citationNavigation.test.ts
git commit -m "fix: persist reading and honor citation targets"
```

### Task 6: Parse SSE Without Swallowing Business Errors

**Files:**
- Create: `frontend/lib/sse.ts`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/components/sage/SageChat.tsx`
- Modify: `frontend/app/roundtable/page.tsx`
- Test: `frontend/tests/sseParser.test.ts`

- [ ] **Step 1: Write failing parser tests**

```typescript
// frontend/tests/sseParser.test.ts
import { describe, expect, it } from "vitest";
import { consumeSse } from "@/lib/sse";

function stream(chunks: string[]) {
  return new ReadableStream<Uint8Array>({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(new TextEncoder().encode(chunk)));
      controller.close();
    },
  });
}

describe("consumeSse", () => {
  it("parses events split across chunks", async () => {
    const events: unknown[] = [];
    await consumeSse(stream(["data: {\"content\":\"学\",", "\"type\":\"chunk\"}\n\n", "data: [DONE]\n\n"]), { onEvent: (event) => events.push(event) });
    expect(events).toEqual([{ content: "学", type: "chunk" }]);
  });

  it("throws a business error instead of swallowing it", async () => {
    await expect(consumeSse(stream(["data: {\"type\":\"error\",\"code\":\"llm_unavailable\",\"message\":\"AI 暂不可用\"}\n\n"]), { onEvent: () => undefined })).rejects.toMatchObject({ code: "llm_unavailable" });
  });
});
```

- [ ] **Step 2: Run and verify failure**

```bash
npm run test:unit -- sseParser.test.ts
```

Expected: FAIL because `consumeSse` does not exist.

- [ ] **Step 3: Implement a reusable parser**

```typescript
// frontend/lib/sse.ts
import { ApiError } from "./api-error";

export async function consumeSse(
  body: ReadableStream<Uint8Array>,
  options: { onEvent: (event: Record<string, unknown>) => void; signal?: AbortSignal },
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      if (options.signal?.aborted) throw new DOMException("Aborted", "AbortError");
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      const frames = buffer.split(/\r?\n\r?\n/);
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        const data = frame.split(/\r?\n/).filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trimStart()).join("\n");
        if (!data || data === "[DONE]") continue;
        let event: Record<string, unknown>;
        try { event = JSON.parse(data); } catch { throw new ApiError("流式响应格式错误", "invalid_sse"); }
        if (event.type === "error" || typeof event.error === "string") {
          throw new ApiError(String(event.message ?? event.error ?? "流式请求失败"), String(event.code ?? "stream_error"));
        }
        options.onEvent(event);
      }
      if (done) break;
    }
    if (buffer.trim()) throw new ApiError("流式响应意外中断", "stream_truncated");
  } finally {
    reader.releaseLock();
  }
}
```

- [ ] **Step 4: Use the parser and AbortController**

Replace both hand-written SSE loops in `api.ts`. Include `Authorization` from `authSession`, pass `signal`, and parse non-2xx JSON through `normalizeApiError` before reading the body. `SageChat` and Roundtable keep accumulated text on interruption, show the typed error, and expose retry/cancel actions.

- [ ] **Step 5: Verify and commit**

```bash
npm run test:unit -- sseParser.test.ts
npm run typecheck
git add frontend/lib/sse.ts frontend/lib/api.ts frontend/components/sage/SageChat.tsx frontend/app/roundtable/page.tsx frontend/tests/sseParser.test.ts
git commit -m "fix: propagate SSE business errors"
```

### Task 7: End Permanent Loading and Make PK Timeout Deterministic

**Files:**
- Modify: `frontend/app/community/page.tsx`
- Modify: `frontend/app/challenge/page.tsx`
- Modify: `frontend/app/achievements/page.tsx`
- Modify: `frontend/components/community/PKArena.tsx`
- Test: `frontend/tests/pageErrorStates.test.tsx`
- Test: `frontend/tests/pkTimer.test.tsx`

- [ ] **Step 1: Write failing page-state tests**

```typescript
// frontend/tests/pageErrorStates.test.tsx
import { render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { ToastProvider } from "@/components/ui/Toast";
import { authSession } from "@/lib/auth";

const { apiMock } = vi.hoisted(() => ({ apiMock: {
  getGroups: vi.fn(), getNotes: vi.fn(), getLeaderboard: vi.fn(),
  getChallengeLevels: vi.fn(), getAchievements: vi.fn(), getRank: vi.fn(), getLearningLeaderboard: vi.fn(),
} }));
vi.mock("@/lib/api", () => ({ api: apiMock }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

beforeEach(() => {
  vi.clearAllMocks();
  authSession.set({ accessToken: "token", csrfToken: "csrf", user: { id: 1, username: "alice", email: "a@example.test", level: 1, expPoints: 0 } });
});

it("community leaves loading and offers retry after load failure", async () => {
  apiMock.getGroups.mockRejectedValue(new Error("offline"));
  apiMock.getNotes.mockRejectedValue(new Error("offline"));
  const CommunityPage = (await import("@/app/community/page")).default;
  render(<ToastProvider><CommunityPage /></ToastProvider>);
  expect(await screen.findByRole("alert")).toHaveTextContent("加载失败");
  expect(screen.queryByText("正在加载社区")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "重新加载" })).toBeEnabled();
});

it("challenge leaves loading after its map request fails", async () => {
  apiMock.getChallengeLevels.mockRejectedValue(new Error("offline"));
  const ChallengePage = (await import("@/app/challenge/page")).default;
  render(<ChallengePage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("加载失败");
  expect(screen.queryByText("正在加载闯关地图")).not.toBeInTheDocument();
});

it("achievements leaves loading after either required request fails", async () => {
  apiMock.getAchievements.mockRejectedValue(new Error("offline"));
  apiMock.getRank.mockResolvedValue({ currentRank: { code: "first", name: "童生", minExp: 0, icon: "Book" }, nextRank: null, exp: 0, expToNext: 0, progressPct: 100, allRanks: [] });
  const AchievementsPage = (await import("@/app/achievements/page")).default;
  render(<AchievementsPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("加载失败");
  expect(screen.queryByText("正在加载成就")).not.toBeInTheDocument();
});
```

Use `Promise.allSettled` only when partial content is useful; otherwise use `try/catch/finally` and a single page error.

- [ ] **Step 2: Write a fake-timer PK test**

```typescript
// frontend/tests/pkTimer.test.tsx
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import PKArena from "@/components/community/PKArena";

it("locks answers and submits exactly once when time reaches zero", async () => {
  vi.useFakeTimers();
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  const onSubmit = vi.fn().mockResolvedValue({ pkId: "pk-1", myScore: 0, opponentScore: 10, result: "lose", correctCount: 0, totalCount: 1, expGained: 10, ratingChange: -1, newRating: 999 });
  render(<PKArena onMatch={async () => ({ pkId: "pk-1", opponent: { userId: 2, username: "opponent", level: 1 }, questions: [{ index: 0, question: "Q", options: ["A", "B"], verseSource: "S" }], timeLimitSeconds: 1 })} onSubmit={onSubmit} />);
  await user.click(screen.getByRole("button", { name: /开始匹配/ }));
  await act(async () => { vi.advanceTimersByTime(1000); });
  expect(onSubmit).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("button", { name: "A" })).toBeDisabled();
  vi.useRealTimers();
});
```

- [ ] **Step 3: Implement explicit page states**

Each page keeps `{ status: "loading" | "ready" | "empty" | "error"; message?: string }`. Every request exits loading in `finally`; mutation errors show a toast/inline alert and roll back optimistic state. Leaderboard scope changes cancel or ignore stale requests.

- [ ] **Step 4: Implement one owned timer and one submit promise**

In `PKArena`, store the interval in a ref, clear it on unmount/reset, and keep `submittingRef`. When time transitions from 1 to 0, set `locked=true` and call `submitOnce()` outside the state updater. `submitOnce` returns the same in-flight promise and catches errors to show a retry state; answer buttons are disabled when locked or submitting.

- [ ] **Step 5: Verify and commit**

```bash
npm run test:unit -- pageErrorStates.test.tsx pkTimer.test.tsx
npm run typecheck
git add frontend/app/community/page.tsx frontend/app/challenge/page.tsx frontend/app/achievements/page.tsx frontend/components/community/PKArena.tsx frontend/tests/pageErrorStates.test.tsx frontend/tests/pkTimer.test.tsx
git commit -m "fix: make page failures and PK timeout recoverable"
```

### Task 8: Run Contract and Workflow Regression

**Files:**
- Modify: `frontend/package.json`
- Modify: `package.json`

- [ ] **Step 1: Include behavioral tests in default commands**

Keep all existing CJS wiring/resource tests and append `npm run test:unit`. Add the previously omitted runtime asset and Python plaque tests to the root test workflow as separate scripts so a missing Python executable produces a real failure.

```json
{
  "scripts": {
    "test:behavior": "npm --prefix frontend run test:unit",
    "test:runtime-assets": "npm --prefix frontend run test:runtime-assets",
    "test:plaque-asset": "python -m pytest frontend/tests/tengwangPlaqueAsset.test.py -q"
  }
}
```

- [ ] **Step 2: Run backend workflow tests**

```bash
python -m pytest backend/tests/test_chapter_challenge.py backend/tests/test_book_progress.py backend/tests/test_idempotency.py -q
```

Expected: PASS.

- [ ] **Step 3: Run frontend behavioral, type, and legacy tests**

```bash
npm --prefix frontend run test:unit
npm --prefix frontend run typecheck
npm --prefix frontend run test
npm run test:runtime-assets
npm run test:plaque-asset
```

Expected: PASS with no skipped contract test.

- [ ] **Step 4: Run production build in real API mode**

```bash
npm --prefix frontend run build
```

Expected: production build succeeds with `NEXT_PUBLIC_USE_MOCK=false`; no page reads a refresh token or maps a chapter ID to a verse ID.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json package.json
git commit -m "test: run real workflow regression by default"
```

## Plan Completion Gate

Run from the repository root:

```bash
npm test
npm --prefix frontend run test:unit
npm --prefix frontend run typecheck
npm --prefix frontend run build
python -m alembic check
rg -n "wudian_refresh_token|verse_id: Number\(chapter|catch \{\s*\}" frontend --glob '!node_modules/**'
```

Expected: all tests and build pass; no pending migration diff; no refresh token storage, chapter-to-verse coercion, or empty business-error catch remains; reading and challenge responses persist across reloads and users remain isolated.
