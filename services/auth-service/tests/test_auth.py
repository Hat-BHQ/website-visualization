from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import hash_refresh_token
from app.models.enums import UserStatus
from app.models.module import Module
from app.models.refresh_token import RefreshToken
from app.models.user import User


async def login(client, email: str, password: str = "password"):
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    return response


async def me(client, access_token: str):
    return await client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})


@pytest.mark.asyncio
async def test_login_success_returns_access_token(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "admin.hqa@company.com")
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failure_returns_401(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "admin.hqa@company.com", password="wrong-password")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_cannot_login(auth_test_context):
    client = auth_test_context["client"]
    settings = auth_test_context["settings"]
    sessionmaker = async_sessionmaker(auth_test_context["engine"], expire_on_commit=False)

    async with sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == "user.hqa@company.com"))
        user = result.scalar_one()
        user.status = UserStatus.inactive
        await session.commit()

    response = await login(client, "user.hqa@company.com")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_hqa_admin_me_returns_hqa_module(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "admin.hqa@company.com")
    tokens = response.json()

    response = await me(client, tokens["access_token"])
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin.hqa@company.com"
    assert body["modules"]
    assert body["modules"][0]["code"] == "HQA"
    assert body["modules"][0]["role"] == "admin"
    assert "hqa.ebay.sync" in body["modules"][0]["permissions"]


@pytest.mark.asyncio
async def test_hqa_user_does_not_receive_hqs_module(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "user.hqa@company.com")
    tokens = response.json()

    response = await me(client, tokens["access_token"])
    body = response.json()
    codes = {module["code"] for module in body["modules"]}
    assert codes == {"HQA"}


@pytest.mark.asyncio
async def test_multi_user_receives_both_modules(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "multi@company.com")
    tokens = response.json()

    response = await me(client, tokens["access_token"])
    body = response.json()
    codes = {module["code"] for module in body["modules"]}
    assert codes == {"HQA", "HQS"}


@pytest.mark.asyncio
async def test_superadmin_receives_all_modules(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "root@company.com")
    tokens = response.json()

    response = await me(client, tokens["access_token"])
    body = response.json()
    codes = {module["code"] for module in body["modules"]}
    assert body["is_superadmin"] is True
    assert codes == {"HQA", "HQS"}


@pytest.mark.asyncio
async def test_refresh_rotation_returns_new_refresh_token(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "admin.hqa@company.com")
    tokens = response.json()

    response = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != tokens["refresh_token"]


@pytest.mark.asyncio
async def test_old_refresh_token_cannot_be_reused(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "admin.hqa@company.com")
    tokens = response.json()

    refresh_response = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 200

    reuse_response = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse_response.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(auth_test_context):
    client = auth_test_context["client"]
    response = await login(client, "admin.hqa@company.com")
    tokens = response.json()

    logout_response = await client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout_response.status_code == 200

    refresh_response = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 401
