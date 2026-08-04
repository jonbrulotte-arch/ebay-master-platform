"""Integration tests for analytics API endpoints."""
import pytest
from httpx import AsyncClient


async def _auth_headers(client: AsyncClient, email: str = "analytics@example.com") -> dict:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "username": "analyticsuser",
    })
    login = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "password123",
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_analytics_summary_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/analytics/summary")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_analytics_summary_empty_returns_zeros(client: AsyncClient):
    headers = await _auth_headers(client)
    resp = await client.get(
        "/api/v1/analytics/summary",
        params={"from_date": "2024-01-01", "to_date": "2024-01-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_count"] == 0
    assert data["gross_revenue"] == 0
    assert data["net_profit"] == 0
    assert data["units_sold"] == 0


@pytest.mark.asyncio
async def test_analytics_revenue_over_time(client: AsyncClient):
    headers = await _auth_headers(client, "rev@example.com")
    resp = await client.get(
        "/api/v1/analytics/revenue-over-time",
        params={"from_date": "2024-01-01", "to_date": "2024-01-31", "granularity": "day"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_analytics_top_products(client: AsyncClient):
    headers = await _auth_headers(client, "top@example.com")
    resp = await client.get(
        "/api/v1/analytics/top-products",
        params={"from_date": "2024-01-01", "to_date": "2024-01-31", "limit": 10},
        headers=headers,
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_analytics_fee_breakdown(client: AsyncClient):
    headers = await _auth_headers(client, "fee@example.com")
    resp = await client.get(
        "/api/v1/analytics/fee-breakdown",
        params={"from_date": "2024-01-01", "to_date": "2024-01-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "final_value_fees" in data
    assert "net_profit" in data


@pytest.mark.asyncio
async def test_analytics_summary_invalid_dates(client: AsyncClient):
    headers = await _auth_headers(client, "dates@example.com")
    resp = await client.get(
        "/api/v1/analytics/summary",
        params={"from_date": "not-a-date", "to_date": "2024-01-31"},
        headers=headers,
    )
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_analytics_summary_previous_period(client: AsyncClient):
    headers = await _auth_headers(client, "prev@example.com")
    resp = await client.get(
        "/api/v1/analytics/summary",
        params={
            "from_date": "2024-02-01",
            "to_date": "2024-02-29",
            "include_previous": "true",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # previous_period may be None if no data, but key should exist
    assert "previous_period" in data
