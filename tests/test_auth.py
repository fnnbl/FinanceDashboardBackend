"""
Tests for authentication endpoints:
  POST /auth/register
  POST /auth/token
  GET  /auth/me
"""
from tests.conftest import register, get_token


class TestRegister:
    async def test_register_success(self, client):
        r = await register(client)
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "user@example.com"
        assert data["name"] == "Test User"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_email(self, client):
        await register(client)
        r = await register(client)
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"]

    async def test_register_invalid_email(self, client):
        r = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
            "name": "Test",
        })
        assert r.status_code == 422

    async def test_register_password_too_short(self, client):
        r = await client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "password": "1234567",
            "name": "Test",
        })
        assert r.status_code == 422

    async def test_register_password_max_length(self, client):
        r = await client.post("/api/v1/auth/register", json={
            "email": "long@example.com",
            "password": "a" * 73,
            "name": "Test",
        })
        assert r.status_code == 422

    async def test_register_missing_email(self, client):
        r = await client.post("/api/v1/auth/register", json={
            "password": "password123",
        })
        assert r.status_code == 422

    async def test_register_without_name(self, client):
        r = await client.post("/api/v1/auth/register", json={
            "email": "noname@example.com",
            "password": "password123",
        })
        assert r.status_code == 201
        assert r.json()["name"] is None


class TestLogin:
    async def test_login_success(self, client):
        await register(client)
        r = await client.post("/api/v1/auth/token", data={
            "username": "user@example.com",
            "password": "password123",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        await register(client)
        r = await client.post("/api/v1/auth/token", data={
            "username": "user@example.com",
            "password": "wrongpassword",
        })
        assert r.status_code == 401
        assert "Incorrect" in r.json()["detail"]

    async def test_login_nonexistent_user(self, client):
        r = await client.post("/api/v1/auth/token", data={
            "username": "ghost@example.com",
            "password": "password123",
        })
        assert r.status_code == 401

    async def test_login_missing_credentials(self, client):
        r = await client.post("/api/v1/auth/token", data={})
        assert r.status_code == 422


class TestGetMe:
    async def test_get_me_success(self, client, auth_headers):
        r = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "user@example.com"
        assert "id" in data

    async def test_get_me_no_token(self, client):
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 403

    async def test_get_me_invalid_token(self, client):
        r = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401
