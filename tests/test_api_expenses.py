import pytest
from httpx import AsyncClient

from mahmoney.models.expense import Expense


@pytest.mark.asyncio
async def test_create_expense(client: AsyncClient):
    response = await client.post(
        "/api/v1/expenses",
        json={
            "supplier_name": "Starbucks Athens",
            "supplier_country": "GR",
            "date": "2026-03-15T10:00:00Z",
            "total_amount": "4.50",
            "currency": "EUR",
            "payment_method": "card",
            "category": "meals",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["supplier_name"] == "Starbucks Athens"
    assert data["total_amount"] == "4.50"
    assert data["status"] == "pending_review"


@pytest.mark.asyncio
async def test_list_expenses(client: AsyncClient, sample_expense: Expense):
    response = await client.get("/api/v1/expenses")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["supplier_name"] == "Test Supplier"


@pytest.mark.asyncio
async def test_get_expense(client: AsyncClient, sample_expense: Expense):
    response = await client.get(f"/api/v1/expenses/{sample_expense.id}")
    assert response.status_code == 200
    assert response.json()["supplier_name"] == "Test Supplier"


@pytest.mark.asyncio
async def test_get_expense_not_found(client: AsyncClient):
    response = await client.get("/api/v1/expenses/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_expense(client: AsyncClient, sample_expense: Expense):
    response = await client.patch(
        f"/api/v1/expenses/{sample_expense.id}",
        json={"category": "meals", "notes": "Updated"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "meals"
    assert data["notes"] == "Updated"


@pytest.mark.asyncio
async def test_delete_expense(client: AsyncClient, sample_expense: Expense):
    response = await client.delete(f"/api/v1/expenses/{sample_expense.id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/expenses/{sample_expense.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_expense(client: AsyncClient, sample_expense: Expense):
    response = await client.post(f"/api/v1/expenses/{sample_expense.id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_filter_by_status(client: AsyncClient, sample_expense: Expense):
    response = await client.get("/api/v1/expenses?status=pending_review")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = await client.get("/api/v1/expenses?status=approved")
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_filter_by_category(client: AsyncClient, sample_expense: Expense):
    response = await client.get("/api/v1/expenses?category=other")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = await client.get("/api/v1/expenses?category=travel")
    assert response.status_code == 200
    assert response.json()["total"] == 0
