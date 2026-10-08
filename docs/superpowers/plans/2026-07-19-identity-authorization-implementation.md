# Identity and Authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure every authenticated action uses the real user, refresh sessions are revocable, abusive requests are rate limited, retries are idempotent, and debate/community data cannot cross user boundaries.

**Architecture:** Keep bearer access tokens for API authorization, but hold them in frontend memory and rotate opaque refresh tokens in Secure HttpOnly cookies. Persist refresh sessions, fixed-window rate counters, idempotency results, and debate session JSON in PostgreSQL; make all authorization decisions at backend query boundaries.

**Tech Stack:** FastAPI dependencies, SQLAlchemy async, PostgreSQL, PyJWT, bcrypt, HMAC-SHA256 CSRF tokens, pytest, httpx.

---

## File Structure

- Modify `backend/app/core/security.py`: explicit password byte validation and PyJWT access tokens.
- Create `backend/app/models/auth_session.py`: refresh session and rate-limit bucket models.
- Create `backend/app/models/idempotency.py`: durable write-result cache.
- Create `backend/app/models/debate.py`: owner-bound debate session payload.
- Modify `backend/app/models/__init__.py`, `backend/app/models/user.py`: export and relate new models.
- Create `backend/app/services/auth_session_service.py`: issue, rotate, revoke, and locate opaque refresh tokens.
- Create `backend/app/services/rate_limit_service.py`: PostgreSQL fixed-window counters.
- Create `backend/app/core/rate_limit.py`: FastAPI dependency factory and stable 429 responses.
- Create `backend/app/services/idempotency_service.py`: claim and replay write outcomes.
- Create `backend/app/services/debate_repository.py`: async database persistence and owner checks.
- Modify `backend/app/schemas/auth.py`, `backend/app/api/auth.py`, `backend/app/core/deps.py`: cookie/CSRF authentication contract.
- Modify `backend/app/api/community.py`, `backend/app/services/community_service.py`: current-user identity and atomic operations.
- Modify `backend/app/services/debate_storage.py`: in-process cache only; no filesystem writes.
- Modify `backend/app/services/debate_engine.py`, `backend/app/services/debate_state_graph.py`, `backend/app/api/debate.py`: database persistence and ownership at every route.
- Create `backend/migrations/versions/20260719_02_identity_ownership.py`: auth, rate-limit, idempotency, and debate tables plus constraints.
- Create `backend/tests/test_password_security.py`, `backend/tests/test_auth_sessions.py`, `backend/tests/test_rate_limits.py`, `backend/tests/test_idempotency.py`, `backend/tests/test_community_identity.py`, `backend/tests/test_debate_ownership.py`: security regression tests.
- Modify existing debate API tests to authenticate real fixture users.

### Task 1: Reject Oversized Passwords and Replace python-jose

**Files:**
- Modify: `backend/app/core/security.py`
- Modify: `backend/app/schemas/auth.py`
- Test: `backend/tests/test_password_security.py`

- [ ] **Step 1: Write failing byte-boundary tests**

```python
# backend/tests/test_password_security.py
import pytest
from pydantic import ValidationError

from app.core.security import PasswordTooLongError, get_password_hash, verify_password
from app.schemas.auth import UserCreate


def test_password_at_72_utf8_bytes_hashes_and_verifies():
    password = "密" * 24
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)


def test_password_over_72_utf8_bytes_is_rejected_not_truncated():
    with pytest.raises(PasswordTooLongError):
        get_password_hash("密" * 25)


def test_registration_schema_rejects_password_over_72_bytes():
    with pytest.raises(ValidationError):
        UserCreate(username="tester", email="tester@example.test", password="密" * 25)
```

- [ ] **Step 2: Run and verify failure**

Run from `backend/`:

```bash
python -m pytest tests/test_password_security.py -q
```

Expected: FAIL because current hashing silently slices to 72 bytes and the schema counts characters only.

- [ ] **Step 3: Implement explicit validation and PyJWT**

```python
# backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import settings


MAX_PASSWORD_BYTES = 72


class PasswordTooLongError(ValueError):
    pass


def password_bytes(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise PasswordTooLongError("密码 UTF-8 编码后不能超过 72 字节")
    return encoded


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password_bytes(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password_bytes(plain_password), hashed_password.encode("ascii"))
    except (PasswordTooLongError, ValueError, TypeError, UnicodeError):
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {**data, "iat": now, "exp": now + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)), "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM], options={"require": ["exp", "iat", "sub", "type"]})
    except InvalidTokenError:
        return None
```

Delete `create_refresh_token`; refresh tokens become opaque random values in Task 2.

- [ ] **Step 4: Add Pydantic byte validation**

```python
from pydantic import field_validator


class UserCreate(BaseModel):
    # keep existing username/email fields
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("密码 UTF-8 编码后不能超过 72 字节")
        return value
```

- [ ] **Step 5: Verify tests and imports**

```bash
python -m pytest tests/test_password_security.py -q
rg -n "python-jose|from jose|create_refresh_token" app tests
```

Expected: tests PASS and the search returns no production import of python-jose or JWT refresh creation.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/security.py backend/app/schemas/auth.py backend/tests/test_password_security.py
git commit -m "fix: reject oversized passwords explicitly"
```

### Task 2: Add Rotating Refresh Sessions, Cookies, CSRF, and Logout

**Files:**
- Create: `backend/app/models/auth_session.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/user.py`
- Create: `backend/app/services/auth_session_service.py`
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/api/auth.py`
- Create: `backend/migrations/versions/20260719_02_identity_ownership.py`
- Test: `backend/tests/test_auth_sessions.py`

- [ ] **Step 1: Write failing cookie and rotation tests**

```python
# backend/tests/test_auth_sessions.py
import pytest


@pytest.mark.asyncio
async def test_login_sets_http_only_refresh_cookie_and_returns_no_refresh_token(api_client, user_factory):
    user = await user_factory(username="alice", password="Correct-Horse-123")
    response = await api_client.post("/api/auth/login", json={"username": user.username, "password": "Correct-Horse-123"})
    assert response.status_code == 200
    assert "refresh_token" not in response.json()
    cookie = response.headers["set-cookie"]
    assert "wudian_refresh=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


@pytest.mark.asyncio
async def test_refresh_rotates_cookie_and_rejects_reuse(api_client, user_factory):
    user = await user_factory(username="alice", password="Correct-Horse-123")
    login = await api_client.post("/api/auth/login", json={"username": user.username, "password": "Correct-Horse-123"})
    old_cookie = login.cookies["wudian_refresh"]
    csrf = login.json()["csrf_token"]
    refreshed = await api_client.post("/api/auth/refresh", headers={"X-CSRF-Token": csrf})
    assert refreshed.status_code == 200
    assert refreshed.cookies["wudian_refresh"] != old_cookie
    api_client.cookies.set("wudian_refresh", old_cookie)
    reused = await api_client.post("/api/auth/refresh", headers={"X-CSRF-Token": csrf})
    assert reused.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_session_and_clears_cookie(authenticated_client):
    login = await authenticated_client.post("/api/auth/login", json={"username": "authenticated", "password": "Correct-Horse-123"})
    response = await authenticated_client.post("/api/auth/logout", headers={"X-CSRF-Token": login.json()["csrf_token"]})
    assert response.status_code == 204
    assert "Max-Age=0" in response.headers["set-cookie"]
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_auth_sessions.py -q
```

Expected: FAIL because refresh tokens are returned in JSON and are not persisted or revocable.

- [ ] **Step 3: Add the refresh session model**

```python
# backend/app/models/auth_session.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class RefreshSession(Base, TimestampMixin):
    __tablename__ = "refresh_sessions"
    __table_args__ = (
        Index("ix_refresh_session_user_active", "user_id", "revoked_at"),
        Index("ix_refresh_session_family", "family_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    family_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[str | None] = mapped_column(String(36))
    user_agent_hash: Mapped[str | None] = mapped_column(String(64))
    user = relationship("User", back_populates="refresh_sessions")
```

Add `refresh_sessions = relationship("RefreshSession", back_populates="user", cascade="all, delete-orphan")` to `User`.

- [ ] **Step 4: Implement opaque issue, rotate, revoke, and deterministic CSRF**

```python
# backend/app/services/auth_session_service.py
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.auth_session import RefreshSession


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def csrf_for(session_id: str) -> str:
    return hmac.new(settings.JWT_SECRET_KEY.encode("utf-8"), f"csrf:{session_id}".encode("utf-8"), hashlib.sha256).hexdigest()


class AuthSessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def issue(self, user_id: int, user_agent: str = "", family_id: str | None = None) -> tuple[str, RefreshSession, str]:
        raw = secrets.token_urlsafe(48)
        session = RefreshSession(
            id=str(uuid.uuid4()), family_id=family_id or str(uuid.uuid4()), user_id=user_id,
            token_hash=_hash(raw), expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            user_agent_hash=_hash(user_agent) if user_agent else None,
        )
        self.db.add(session)
        await self.db.flush()
        return raw, session, csrf_for(session.id)

    async def locate(self, raw: str) -> RefreshSession | None:
        return await self.db.scalar(select(RefreshSession).where(RefreshSession.token_hash == _hash(raw)))

    async def rotate(self, raw: str, csrf: str, user_agent: str = "") -> tuple[str, RefreshSession, str] | None:
        current = await self.locate(raw)
        now = datetime.now(timezone.utc)
        if current is None or current.expires_at <= now or not hmac.compare_digest(csrf, csrf_for(current.id)):
            return None
        if current.rotated_at or current.revoked_at:
            if current:
                await self.revoke_family(current.family_id)
            return None
        next_raw, replacement, next_csrf = await self.issue(current.user_id, user_agent, current.family_id)
        current.rotated_at = now
        current.replaced_by_id = replacement.id
        await self.db.flush()
        return next_raw, replacement, next_csrf

    async def csrf_for_refresh_cookie(self, raw: str) -> str | None:
        current = await self.locate(raw)
        if current is None or current.revoked_at or current.expires_at <= datetime.now(timezone.utc):
            return None
        return csrf_for(current.id)

    async def revoke_family(self, family_id: str) -> None:
        await self.db.execute(update(RefreshSession).where(RefreshSession.family_id == family_id, RefreshSession.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc)))
```

- [ ] **Step 5: Change the API response and Cookie helpers**

```python
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    csrf_token: str
    user: UserResponse
```

In `backend/app/api/auth.py`, use `Response.set_cookie` after registration/login/refresh:

```python
def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.COOKIE_NAME, value=token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True, secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE, domain=settings.COOKIE_DOMAIN,
        path="/api/auth",
    )
```

Refresh reads `Cookie(default=None, alias=settings.COOKIE_NAME)` and `Header(default=None, alias=settings.CSRF_HEADER_NAME)`, calls `rotate`, verifies the session user is active, and commits before returning the next access token. Logout locates the Cookie, revokes its family, deletes the Cookie, and returns 204. Add `GET /api/auth/csrf`: it accepts the refresh Cookie, checks the `Origin` against `settings.CORS_ORIGINS`, returns `{ "csrf_token": ... }` from `csrf_for_refresh_cookie`, and never mutates state. On refresh-token reuse, commit after `revoke_family` and before raising 401 so family revocation is durable.

- [ ] **Step 6: Generate and verify the migration**

```bash
python -m alembic revision --autogenerate --rev-id 20260719_02 -m "identity ownership"
python -m alembic upgrade head
python -m alembic check
```

Expected: the revision creates `refresh_sessions` and later tables added in this plan; no pending model diff remains at plan completion.

- [ ] **Step 7: Run tests**

```bash
python -m pytest tests/test_auth_sessions.py tests/test_password_security.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/auth_session.py backend/app/models/user.py backend/app/models/__init__.py backend/app/services/auth_session_service.py backend/app/schemas/auth.py backend/app/api/auth.py backend/migrations/versions/20260719_02_identity_ownership.py backend/tests/test_auth_sessions.py
git commit -m "feat: add rotating refresh sessions"
```

### Task 3: Enforce Database-Backed Rate Limits

**Files:**
- Modify: `backend/app/models/auth_session.py`
- Create: `backend/app/services/rate_limit_service.py`
- Create: `backend/app/core/rate_limit.py`
- Modify: `backend/app/api/auth.py`
- Modify: `backend/app/api/ai.py`
- Modify: `backend/migrations/versions/20260719_02_identity_ownership.py`
- Test: `backend/tests/test_rate_limits.py`

- [ ] **Step 1: Write failing limit tests**

```python
# backend/tests/test_rate_limits.py
import pytest


@pytest.mark.asyncio
async def test_sixth_login_in_one_minute_is_rate_limited(api_client):
    for _ in range(5):
        response = await api_client.post("/api/auth/login", json={"username": "missing", "password": "wrong-password"})
        assert response.status_code == 401
    limited = await api_client.post("/api/auth/login", json={"username": "missing", "password": "wrong-password"})
    assert limited.status_code == 429
    assert limited.json()["code"] == "rate_limited"
    assert int(limited.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_rate_limits_are_scoped_by_key(api_client):
    for name in ("alice", "bob"):
        response = await api_client.post("/api/auth/login", json={"username": name, "password": "wrong-password"})
        assert response.status_code == 401
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_rate_limits.py -q
```

Expected: FAIL because the sixth request still returns 401.

- [ ] **Step 3: Add the counter model**

```python
class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"
    __table_args__ = (UniqueConstraint("scope", "bucket_key", "window_start", name="uq_rate_limit_window"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scope: Mapped[str] = mapped_column(String(40), nullable=False)
    bucket_key: Mapped[str] = mapped_column(String(64), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
```

- [ ] **Step 4: Implement an atomic fixed-window increment**

```python
# backend/app/services/rate_limit_service.py
import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_session import RateLimitBucket


class RateLimitService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def hit(self, scope: str, identity: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = datetime.now(timezone.utc)
        epoch = int(now.timestamp())
        window_epoch = epoch - epoch % window_seconds
        window_start = datetime.fromtimestamp(window_epoch, timezone.utc)
        bucket_key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        bucket = await self.db.scalar(
            select(RateLimitBucket).where(
                RateLimitBucket.scope == scope,
                RateLimitBucket.bucket_key == bucket_key,
                RateLimitBucket.window_start == window_start,
            ).with_for_update()
        )
        if bucket is None:
            bucket = RateLimitBucket(scope=scope, bucket_key=bucket_key, window_start=window_start, count=0, expires_at=window_start + timedelta(seconds=window_seconds * 2))
            self.db.add(bucket)
        bucket.count += 1
        await self.db.flush()
        retry_after = max(1, int((window_start + timedelta(seconds=window_seconds) - now).total_seconds()))
        return bucket.count <= limit, retry_after
```

Handle the concurrent first-insert unique conflict by wrapping the create branch in a nested transaction and re-selecting the bucket with `FOR UPDATE`; do not catch and ignore `IntegrityError` outside a savepoint.

- [ ] **Step 5: Add route dependencies**

Create a dependency factory that combines `request.client.host` with normalized account/user identity, calls `hit`, and raises:

```python
raise HTTPException(
    status_code=429,
    detail="请求过于频繁，请稍后重试",
    headers={"Retry-After": str(retry_after)},
)
```

Apply the approved defaults: login 5/minute per IP+account, register 3/hour per IP, refresh 30/minute per IP+session, AI 10/minute and 30/hour per IP+user. The rate-limit dependency commits its counter in a separate transaction before returning or raising 429; otherwise request-level rollback would erase failed-login counters.

All AI endpoints in `backend/app/api/ai.py` use `get_current_active_user`; none may obtain a fabricated demo user. After the debate routes are migrated in Task 6, delete `_make_demo_user` and `get_current_user_or_demo` from `backend/app/core/deps.py`.

- [ ] **Step 6: Run tests and migration check**

```bash
python -m pytest tests/test_rate_limits.py -q
python -m alembic check
```

Expected: PASS; no model changes remain outside revision `20260719_02`.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/auth_session.py backend/app/services/rate_limit_service.py backend/app/core/rate_limit.py backend/app/api/auth.py backend/app/api/ai.py backend/migrations/versions/20260719_02_identity_ownership.py backend/tests/test_rate_limits.py
git commit -m "feat: add database backed request limits"
```

### Task 4: Replace Community Demo Identity With the Authenticated User

**Files:**
- Modify: `backend/app/api/community.py`
- Modify: `backend/app/services/community_service.py`
- Test: `backend/tests/test_community_identity.py`

- [ ] **Step 1: Write failing two-user API tests**

```python
# backend/tests/test_community_identity.py
import pytest


@pytest.mark.asyncio
async def test_group_creation_uses_authenticated_owner(user_client_factory):
    alice, alice_client = await user_client_factory("alice")
    bob, bob_client = await user_client_factory("bob")
    created = await alice_client.post("/api/community/groups", json={"name": "Alice group", "description": "real owner", "category": "free", "is_private": False, "max_members": 20})
    assert created.status_code == 200
    group_id = created.json()["id"]
    detail = await bob_client.get(f"/api/community/groups/{group_id}")
    assert detail.json()["owner_id"] == alice.id
    assert detail.json()["is_joined"] is False


@pytest.mark.asyncio
async def test_anonymous_writes_are_rejected(api_client):
    response = await api_client.post("/api/community/groups/1/join")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_note_like_is_isolated_by_user(user_client_factory, seeded_public_note):
    _, alice = await user_client_factory("alice")
    _, bob = await user_client_factory("bob")
    assert (await alice.post(f"/api/community/notes/{seeded_public_note.id}/like")).json()["liked"] is True
    assert (await bob.get(f"/api/community/notes/{seeded_public_note.id}")).json()["is_liked"] is False
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_community_identity.py -q
```

Expected: FAIL because all routes use user 1001.

- [ ] **Step 3: Replace hard-coded constants with dependencies**

Delete `_CURRENT_USER_ID`, `_CURRENT_USERNAME`, and `_CURRENT_LEVEL`. Use these route shapes:

```python
@router.post("/groups")
async def create_group(
    req: GroupCreate,
    service: CommunityService = Depends(_get_service),
    current_user: User = Depends(get_current_active_user),
):
    return await service.create_group(current_user.id, current_user.username, current_user.level, req)


@router.get("/groups/{group_id}")
async def get_group(
    group_id: int,
    service: CommunityService = Depends(_get_service),
    current_user: User | None = Depends(get_optional_current_user),
):
    return await service.get_group(group_id, current_user_id=current_user.id if current_user else None)
```

Apply `get_current_active_user` to create/join/leave/check-in/note/like/comment/PK routes. Apply `get_optional_current_user` to public group/note detail and lists. Public leaderboard does not inject a fabricated current user; it may optionally identify a logged-in user's own rank.

- [ ] **Step 4: Remove fallback author identity**

In `comment_note`, require the user row to exist and construct `AuthorBrief` only from `_author_from_user(user)`. If it is missing, raise `ValueError("用户不存在")`; never reconstruct an author from request-supplied username or level.

- [ ] **Step 5: Run focused and full backend tests**

```bash
python -m pytest tests/test_community_identity.py -q
python -m pytest tests -q
```

Expected: focused tests PASS. Update any demo test that relied on anonymous writes to authenticate a fixture user.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/community.py backend/app/services/community_service.py backend/tests/test_community_identity.py backend/tests
git commit -m "fix: enforce community user identity"
```

### Task 5: Make Rewarding Writes Atomic and Idempotent

**Files:**
- Create: `backend/app/models/idempotency.py`
- Create: `backend/app/services/idempotency_service.py`
- Modify: `backend/app/models/checkin.py`
- Modify: `backend/app/models/achievement.py`
- Modify: `backend/app/models/community.py`
- Modify: `backend/app/services/community_service.py`
- Modify: `backend/app/api/community.py`
- Modify: `backend/migrations/versions/20260719_02_identity_ownership.py`
- Test: `backend/tests/test_idempotency.py`

- [ ] **Step 1: Write failing replay tests**

```python
# backend/tests/test_idempotency.py
import pytest
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
async def test_pk_submit_replay_returns_same_result_without_double_reward(user_client_factory):
    user, client = await user_client_factory("alice")
    match = await client.post("/api/community/pk/match", json={"question_count": 5})
    payload = {"pk_id": match.json()["pk_id"], "answers": [], "duration_seconds": 300}
    headers = {"Idempotency-Key": "pk-submit-00000001"}
    first = await client.post("/api/community/pk/submit", json=payload, headers=headers)
    second = await client.post("/api/community/pk/submit", json=payload, headers=headers)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    refreshed = await client.get("/api/auth/me")
    assert refreshed.json()["exp_points"] == first.json()["exp_gained"]


@pytest.mark.asyncio
async def test_same_key_with_different_payload_returns_conflict(user_client_factory):
    _, client = await user_client_factory("alice")
    headers = {"Idempotency-Key": "write-key-00000001"}
    first = await client.post("/api/community/groups/1/checkin", headers=headers)
    second = await client.post("/api/community/groups/2/checkin", headers=headers)
    assert first.status_code in {200, 400, 404}
    assert second.status_code == 409
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_idempotency.py -q
```

Expected: FAIL because replayed writes are not durably recognized.

- [ ] **Step 3: Add the durable record model**

```python
# backend/app/models/idempotency.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class IdempotencyRecord(Base, TimestampMixin):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_idempotency_user_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer)
    response_json: Mapped[dict | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

- [ ] **Step 4: Implement claim and replay semantics**

```python
# backend/app/services/idempotency_service.py
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency import IdempotencyRecord


def payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class IdempotencyConflict(Exception):
    pass


class IdempotencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def claim(self, user_id: int, key: str, payload: dict) -> tuple[IdempotencyRecord, dict | None]:
        digest = payload_hash(payload)
        record = await self.db.scalar(select(IdempotencyRecord).where(IdempotencyRecord.user_id == user_id, IdempotencyRecord.key == key).with_for_update())
        if record:
            if record.request_hash != digest:
                raise IdempotencyConflict
            return record, record.response_json
        record = IdempotencyRecord(user_id=user_id, key=key, request_hash=digest)
        self.db.add(record)
        await self.db.flush()
        return record, None

    async def complete(self, record: IdempotencyRecord, status_code: int, response_json: dict) -> None:
        record.status_code = status_code
        record.response_json = response_json
        record.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
```

Handle concurrent first claims with a nested transaction and re-select, as in rate limiting. A claimed but incomplete record returns 409 `request_in_progress`; a completed record replays its stored status and body.

- [ ] **Step 5: Apply it to rewarding writes**

Require `Idempotency-Key` with 8-128 ASCII URL-safe characters on community check-in, PK submit, learning check-in, quiz submit, complete chapter, and review submit. Claim before mutations and store the serialized Pydantic response in the same database transaction as rewards. Remove internal `commit()` calls from `CommunityService`; the request-level `get_db` dependency owns commit/rollback.

Add `scope_key: Mapped[str] = mapped_column(String(64), nullable=False)` to `Checkin` and replace the current uniqueness rule with `UniqueConstraint("user_id", "checkin_date", "scope_key", name="uq_checkin_user_date_scope")`. Learning check-in writes `scope_key="global"`; group check-in writes `scope_key=f"group:{group_id}"`. This avoids PostgreSQL's multiple-NULL behavior and prevents a global check-in from masquerading as every group check-in.

Add `UniqueConstraint("user_id", "badge_type", name="uq_achievement_user_badge")` to `Achievement`.

Add `session_payload: Mapped[dict] = mapped_column(JSON, nullable=False)` and `expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)` to `PkMatch`. Persist question indices, opponent answers, time limit, and owner in this payload. `pk_submit` loads the row with `FOR UPDATE`, verifies `player1_id`, `status`, and expiry, calculates once, writes scores/rewards/result, and changes status to `completed` in the same transaction. Remove `_pk_sessions`; an application restart must not lose an in-progress match.

Add `session_payload: Mapped[dict] = mapped_column(JSON, nullable=False)` and `expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)` to `PkMatch`. `pk_match` persists question indices, opponent answers, time limit, and owner in this payload. `pk_submit` loads the `PkMatch` row with `FOR UPDATE`, verifies `player1_id`, `status`, and expiry, calculates once, writes scores/rewards/result, and changes status to `completed` in the same transaction. Remove `_pk_sessions`; an application restart must not lose an in-progress match.

- [ ] **Step 6: Run tests and migration check**

```bash
python -m pytest tests/test_idempotency.py tests/test_community_identity.py -q
python -m alembic check
```

Expected: PASS; reward totals change once under replay.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/idempotency.py backend/app/models/checkin.py backend/app/models/achievement.py backend/app/models/community.py backend/app/models/__init__.py backend/app/services/idempotency_service.py backend/app/services/community_service.py backend/app/api/community.py backend/migrations/versions/20260719_02_identity_ownership.py backend/tests/test_idempotency.py
git commit -m "feat: make rewarding writes idempotent"
```

### Task 6: Persist Debate Sessions With Owner Isolation

**Files:**
- Create: `backend/app/models/debate.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/services/debate_repository.py`
- Modify: `backend/app/services/debate_storage.py`
- Modify: `backend/app/services/debate_engine.py`
- Modify: `backend/app/services/debate_state_graph.py`
- Modify: `backend/app/api/debate.py`
- Modify: `backend/migrations/versions/20260719_02_identity_ownership.py`
- Test: `backend/tests/test_debate_ownership.py`
- Modify: `backend/tests/test_debate_action_apis.py`
- Modify: all other debate API tests that create anonymous sessions

- [ ] **Step 1: Write failing owner-isolation tests**

```python
# backend/tests/test_debate_ownership.py
import pytest


@pytest.mark.asyncio
async def test_debate_history_contains_only_current_users_sessions(user_client_factory):
    _, alice = await user_client_factory("alice")
    _, bob = await user_client_factory("bob")
    alice_id = (await alice.post("/api/debate/start", json={"topic": "Alice topic"})).json()["session_id"]
    bob_id = (await bob.post("/api/debate/start", json={"topic": "Bob topic"})).json()["session_id"]
    history = (await alice.get("/api/debate/history")).json()["sessions"]
    assert {item["id"] for item in history} == {alice_id}
    assert bob_id not in {item["id"] for item in history}


@pytest.mark.asyncio
async def test_other_user_cannot_read_or_mutate_session(user_client_factory):
    _, alice = await user_client_factory("alice")
    _, bob = await user_client_factory("bob")
    session_id = (await alice.post("/api/debate/start", json={"topic": "Private topic"})).json()["session_id"]
    assert (await bob.get(f"/api/debate/{session_id}/session")).status_code == 403
    assert (await bob.post(f"/api/debate/{session_id}/next-round?stream=false")).status_code == 403


@pytest.mark.asyncio
async def test_anonymous_debate_start_is_rejected(api_client):
    assert (await api_client.post("/api/debate/start", json={"topic": "Anonymous"})).status_code == 401
```

- [ ] **Step 2: Run and verify failure**

```bash
python -m pytest tests/test_debate_ownership.py -q
```

Expected: FAIL because debate routes use `get_current_user_or_demo`, session rows have no owner, and history is global.

- [ ] **Step 3: Add the database record and repository**

```python
# backend/app/models/debate.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DebateSessionRecord(Base):
    __tablename__ = "debate_sessions"
    __table_args__ = (Index("ix_debate_owner_created", "owner_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    phase: Mapped[str] = mapped_column(String(24), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

```python
# backend/app/services/debate_repository.py
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.debate import DebateSessionRecord
from app.schemas.debate import DebateSession


class DebateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, owner_id: int, session: DebateSession) -> None:
        now = datetime.now(timezone.utc)
        self.db.add(DebateSessionRecord(id=session.id, owner_id=owner_id, topic=session.topic, phase=session.phase, payload=session.model_dump(mode="json"), created_at=now, updated_at=now))
        await self.db.flush()

    async def require_owned(self, owner_id: int, session_id: str) -> DebateSession:
        record = await self.db.get(DebateSessionRecord, session_id)
        if record is None:
            raise HTTPException(status_code=404, detail="辩论会话不存在")
        if record.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="无权访问此辩论会话")
        return DebateSession.model_validate(record.payload)

    async def save(self, owner_id: int, session: DebateSession) -> None:
        await self.require_owned(owner_id, session.id)
        record = await self.db.get(DebateSessionRecord, session.id)
        record.phase = session.phase
        record.payload = session.model_dump(mode="json")
        record.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def list_owned(self, owner_id: int, limit: int) -> list[DebateSession]:
        rows = (await self.db.scalars(select(DebateSessionRecord).where(DebateSessionRecord.owner_id == owner_id).order_by(DebateSessionRecord.created_at.desc()).limit(limit))).all()
        return [DebateSession.model_validate(row.payload) for row in rows]
```

- [ ] **Step 4: Turn file storage into an in-process cache**

`DebateStorage.save`, `load`, and `delete` may manage `_cache`, but must not create directories, open files, glob JSON, or list global sessions. Remove `storage_dir` and delete `list_sessions`; rename the module docstring to state that PostgreSQL is authoritative.

- [ ] **Step 5: Enforce ownership on every route**

Replace `get_current_user_or_demo` with `get_current_active_user`. Before any route reads or mutates a `session_id`, call `repository.require_owned(current_user.id, session_id)` and hydrate the engine cache with `debate_storage.save(session)`. After every non-stream mutation, call `repository.save` before returning.

For SSE generators, pass `owner_id` into the generator and open a fresh `async_session_factory()` at completion or error to save the final session and transition trace. Never hold the request dependency session across an unbounded stream.

`/history` calls `list_owned`. Public `/presets`, `/guests/roster`, and `/thought-compass` remain ownerless only if they do not create, read, or mutate personal session data.

Delete `_make_demo_user` and `get_current_user_or_demo` from `backend/app/core/deps.py` after `rg -n "get_current_user_or_demo" backend/app` confirms no route imports them.

- [ ] **Step 6: Update old tests to use authenticated clients**

Replace each anonymous `TestClient(app).post("/api/debate/start", ...)` with the shared authenticated fixture. Keep engine unit tests that do not cross the API boundary independent of authentication.

- [ ] **Step 7: Run debate tests and verify no runtime JSON is written**

```bash
python -m pytest tests/test_debate_ownership.py tests/test_debate_action_apis.py tests/test_debate_state_graph.py -q
git status --short backend/data/debates data/debates
```

Expected: tests PASS and the status command shows no newly generated JSON.

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/debate.py backend/app/models/__init__.py backend/app/services/debate_repository.py backend/app/services/debate_storage.py backend/app/services/debate_engine.py backend/app/services/debate_state_graph.py backend/app/api/debate.py backend/app/core/deps.py backend/migrations/versions/20260719_02_identity_ownership.py backend/tests
git commit -m "fix: isolate debate sessions by owner"
```

### Task 7: Enforce Security Coverage and Full Regression

**Files:**
- Create: `backend/pyproject.toml`
- Modify: `package.json`

- [ ] **Step 1: Configure pytest and focused coverage gates**

```toml
# backend/pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--strict-markers --strict-config"

[tool.coverage.run]
branch = true
source = ["app"]

[tool.coverage.report]
show_missing = true
skip_covered = false
```

- [ ] **Step 2: Add deterministic security test scripts**

Merge into the root `scripts` object:

```json
{
  "backend:test:security": "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Push-Location backend; python -m pytest tests/test_password_security.py tests/test_auth_sessions.py tests/test_rate_limits.py tests/test_idempotency.py tests/test_community_identity.py tests/test_debate_ownership.py --cov=app.core --cov=app.api.auth --cov=app.api.community --cov=app.services.auth_session_service --cov=app.services.debate_repository --cov-branch --cov-fail-under=80; $code=$LASTEXITCODE; Pop-Location; exit $code\""
}
```

CI later uses the same pytest arguments directly on Linux rather than PowerShell.

- [ ] **Step 3: Run security and full test suites**

```bash
npm run backend:test:security
npm test
```

Expected: focused statement/branch coverage is at least 80%; all existing tests pass; no API test silently falls back to demo identity.

- [ ] **Step 4: Run static searches for forbidden patterns**

```bash
rg -n "_CURRENT_USER_ID|_CURRENT_USERNAME|get_current_user_or_demo|\[:72\]|refresh_token.*localStorage|data/debates" backend/app frontend/lib
```

Expected: no production authentication route, community route, debate route, or password implementation matches. A clearly isolated development-only helper may remain only when it is unreachable under production configuration and has a direct test proving that gate.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml package.json
git commit -m "test: enforce identity security coverage"
```

## Plan Completion Gate

Run from the repository root:

```bash
npm run backend:test:security
npm test
python -m alembic check
rg -n "_CURRENT_USER_ID|_CURRENT_USERNAME|get_current_user_or_demo|\[:72\]" backend/app
```

Expected: the security suite and full regression pass; Alembic reports no pending operations; the forbidden-pattern search returns no production usage; two-user tests prove community and debate isolation; replay tests prove rewards are applied once.
