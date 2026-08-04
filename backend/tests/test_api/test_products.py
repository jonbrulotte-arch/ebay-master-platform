"""Integration tests for the products API."""
import pytest
from httpx import AsyncClient


async def _make_user(client: AsyncClient, email: str = "products@example.com") -> dict:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "username": "productsuser",
    })
    login = await client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "password123",
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    headers = await _make_user(client)
    resp = await client.get("/api/v1/products", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    headers = await _make_user(client, "create@example.com")
    resp = await client.post("/api/v1/products", headers=headers, json={
        "sku": "TEST-001",
        "title": "Test Product",
        "condition": "NEW",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["sku"] == "TEST-001"
    assert data["title"] == "Test Product"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient):
    headers = await _make_user(client, "get@example.com")
    create_resp = await client.post("/api/v1/products", headers=headers, json={
        "sku": "GET-001",
        "title": "Gettable Product",
    })
    product_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/products/{product_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == product_id


@pytest.mark.asyncio
async def test_get_nonexistent_product(client: AsyncClient):
    headers = await _make_user(client, "notfound@example.com")
    import uuid
    resp = await client.get(f"/api/v1/products/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient):
    headers = await _make_user(client, "update@example.com")
    create_resp = await client.post("/api/v1/products", headers=headers, json={
        "sku": "UPD-001",
        "title": "Original Title",
    })
    product_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/v1/products/{product_id}", headers=headers, json={
        "title": "Updated Title",
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"
    assert resp.json()["sku"] == "UPD-001"  # unchanged


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient):
    headers = await _make_user(client, "delete@example.com")
    create_resp = await client.post("/api/v1/products", headers=headers, json={
        "sku": "DEL-001",
        "title": "To Be Deleted",
    })
    product_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/products/{product_id}", headers=headers)
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/products/{product_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_products_scoped_to_user(client: AsyncClient):
    """Products are only visible to the owning user."""
    headers1 = await _make_user(client, "user1@example.com")
    headers2 = await _make_user(client, "user2@example.com")

    create_resp = await client.post("/api/v1/products", headers=headers1, json={
        "sku": "PRIVATE-001",
        "title": "User 1 Product",
    })
    product_id = create_resp.json()["id"]

    # user2 should not see user1's product
    resp = await client.get(f"/api/v1/products/{product_id}", headers=headers2)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_sku_rejected(client: AsyncClient):
    headers = await _make_user(client, "dup_sku@example.com")
    await client.post("/api/v1/products", headers=headers, json={
        "sku": "DUP-SKU",
        "title": "First Product",
    })
    resp = await client.post("/api/v1/products", headers=headers, json={
        "sku": "DUP-SKU",
        "title": "Second Product",
    })
    assert resp.status_code in (409, 400)
