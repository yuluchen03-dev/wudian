"""
认证 API 集成测试
覆盖 JWT 签发/校验、过期 token、密码处理、注册/登录流程
"""
import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.main import app


class TestJWTHandling:
    """JWT 签发与校验测试"""

    def test_access_token_is_valid(self, db_session):
        """测试 access token 能够正确签发和校验"""
        token = create_access_token({"sub": "1", "username": "testuser"})
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("sub") == "1"
        assert payload.get("type") == "access"

    def test_refresh_token_is_valid(self):
        """测试 refresh token 能够正确签发和校验"""
        token = create_refresh_token({"sub": "1"})
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("type") == "refresh"

    def test_token_encoding_is_jwt(self):
        """测试 token 格式为有效的 JWT"""
        token = create_access_token({"sub": "1", "username": "test"})
        # JWT 应该有三个以点分隔的部分
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_has_expiration(self):
        """测试 token 包含过期时间"""
        token = create_access_token({"sub": "1"})
        payload = decode_token(token)
        assert payload is not None
        assert "exp" in payload
        assert payload["exp"] > int(datetime.now(timezone.utc).timestamp())


class TestExpiredToken:
    """过期 token 测试"""

    def test_expired_token_returns_none(self):
        """过期 token 应该返回 None"""
        import jwt as pyjwt
        from app.core.config import settings

        expired_token = pyjwt.encode(
            {
                "sub": "1",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
                "type": "access",
            },
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        payload = decode_token(expired_token)
        assert payload is None

    def test_invalid_signature_returns_none(self):
        """签名无效的 token 应该返回 None"""
        import jwt as pyjwt

        wrong_token = pyjwt.encode(
            {
                "sub": "1",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
                "type": "access",
            },
            "wrong-secret-key",
            algorithm="HS256",
        )

        payload = decode_token(wrong_token)
        assert payload is None

    def test_empty_token_returns_none(self):
        """空 token 应该返回 None"""
        payload = decode_token("")
        assert payload is None


class TestPasswordHandling:
    """密码处理测试"""

    def test_password_hash_is_bcrypt_format(self):
        """密码哈希应该是 bcrypt 格式"""
        hashed = get_password_hash("testpassword123")
        # bcrypt 哈希格式: $2b$12$...
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_correct_password(self):
        """正确密码应该通过验证"""
        hashed = get_password_hash("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_incorrect_password(self):
        """错误密码应该验证失败"""
        hashed = get_password_hash("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        """相同密码应该生成不同的哈希（盐值随机）"""
        hash1 = get_password_hash("samepassword")
        hash2 = get_password_hash("samepassword")
        assert hash1 != hash2

    def test_password_length_limit(self):
        """密码截断在 72 字节：超长密码与其 72 字节前缀验证等价"""
        long_password = "a" * 100  # 超过 72 字节
        hash_short = get_password_hash("a" * 72)
        # bcrypt 每次哈希盐值随机，两次哈希不可能相同；用验证语义断言截断行为
        assert verify_password(long_password, hash_short) is True


class TestAuthFlows:
    """注册与登录流程测试"""

    def test_register_success(self, client, db_session):
        """成功注册新用户"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser_test",
                "email": "newuser_test@test.com",
                "password": "securepass123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self, client, db_session):
        """重复用户名注册应该失败"""
        # 首先注册一个用户
        client.post(
            "/api/auth/register",
            json={
                "username": "duplicateuser_test",
                "email": "dup1_test@test.com",
                "password": "password123",
            },
        )

        # 再尝试用相同用户名注册
        response = client.post(
            "/api/auth/register",
            json={
                "username": "duplicateuser_test",
                "email": "dup2_test@test.com",
                "password": "password456",
            },
        )

        assert response.status_code == 409
        assert "用户名已被注册" in response.json()["detail"]

    def test_register_duplicate_email(self, client, db_session):
        """重复邮箱注册应该失败"""
        # 首先注册一个用户
        client.post(
            "/api/auth/register",
            json={
                "username": "emailuser_test1",
                "email": "email_test@test.com",
                "password": "password123",
            },
        )

        # 再尝试用相同邮箱注册
        response = client.post(
            "/api/auth/register",
            json={
                "username": "emailuser_test2",
                "email": "email_test@test.com",
                "password": "password456",
            },
        )

        assert response.status_code == 409
        assert "邮箱已被注册" in response.json()["detail"]

    def test_login_success(self, client, db_session):
        """成功登录"""
        # 先注册用户
        client.post(
            "/api/auth/register",
            json={
                "username": "loginuser_test",
                "email": "login_test@test.com",
                "password": "loginpass123",
            },
        )

        # 再登录
        response = client.post(
            "/api/auth/login",
            json={"username": "loginuser_test", "password": "loginpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, db_session):
        """错误密码登录应该失败"""
        # 先注册用户
        client.post(
            "/api/auth/register",
            json={
                "username": "wrongpassuser_test",
                "email": "wrongpass_test@test.com",
                "password": "correctpass123",
            },
        )

        # 用错误密码登录
        response = client.post(
            "/api/auth/login",
            json={"username": "wrongpassuser_test", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """不存在的用户登录应该失败"""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistentuser_test", "password": "anypassword"},
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_get_me_with_valid_token(self, client, db_session):
        """用有效 token 获取用户信息"""
        # 注册并登录
        register_resp = client.post(
            "/api/auth/register",
            json={
                "username": "meuser_test",
                "email": "me_test@test.com",
                "password": "mepass123",
            },
        )
        token = register_resp.json()["access_token"]

        # 获取用户信息
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "meuser_test"
        assert data["email"] == "me_test@test.com"

    def test_get_me_without_token_returns_401(self, client):
        """未携带 token 获取用户信息应该返回 401"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_refresh_access_token(self, client, db_session):
        """用 refresh token 刷新 access token"""
        # 注册用户
        register_resp = client.post(
            "/api/auth/register",
            json={
                "username": "refreshuser_test",
                "email": "refresh_test@test.com",
                "password": "refreshpass123",
            },
        )
        refresh_token = register_resp.json()["refresh_token"]

        # 刷新 token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_access_token_fails(self, client, db_session):
        """用 access token 刷新应该失败"""
        # 注册用户
        register_resp = client.post(
            "/api/auth/register",
            json={
                "username": "badrefreshuser_test",
                "email": "badrefresh_test@test.com",
                "password": "password123",
            },
        )
        access_token = register_resp.json()["access_token"]

        # 用 access token 刷新
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401
        assert "token 类型错误" in response.json()["detail"]

    def test_login_by_email(self, client, db_session):
        """用邮箱登录"""
        # 注册用户
        client.post(
            "/api/auth/register",
            json={
                "username": "emaillogin_test",
                "email": "emaillogin_test@test.com",
                "password": "emailloginpass123",
            },
        )

        # 用邮箱登录
        response = client.post(
            "/api/auth/login",
            json={"username": "emaillogin_test@test.com", "password": "emailloginpass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
