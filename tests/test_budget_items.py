"""
Tests for budget item endpoints:
  GET    /plans/{plan_id}/items/
  POST   /plans/{plan_id}/items/
  PUT    /plans/{plan_id}/items/{item_id}
  DELETE /plans/{plan_id}/items/{item_id}
"""
import pytest
from tests.conftest import create_plan, create_budget_item, get_expense_category_id, get_income_category_id


class TestListBudgetItems:
    async def test_list_items_empty(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.get(f"/api/v1/plans/{plan['id']}/items/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    async def test_list_items_unauthenticated(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.get(f"/api/v1/plans/{plan['id']}/items/")
        assert r.status_code == 403

    async def test_list_items_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.get(f"/api/v1/plans/{plan['id']}/items/", headers=second_user_headers)
        assert r.status_code == 403


class TestCreateBudgetItem:
    async def test_create_expense_item(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await create_budget_item(client, auth_headers, plan["id"], description="Miete", amount=800.0, type="expense")
        assert r.status_code == 201
        data = r.json()
        assert data["description"] == "Miete"
        assert data["amount"] == 800.0
        assert data["type"] == "expense"
        assert data["monthly_amount"] == 800.0

    async def test_create_income_item(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        cat_id = await get_income_category_id(client, auth_headers)
        r = await create_budget_item(client, auth_headers, plan["id"],
                                     description="Gehalt", amount=2500.0,
                                     type="income", category_id=cat_id)
        assert r.status_code == 201
        assert r.json()["type"] == "income"

    async def test_monthly_amount_monthly(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await create_budget_item(client, auth_headers, plan["id"], amount=300.0, payment_rhythm="monthly")
        assert r.json()["monthly_amount"] == 300.0

    async def test_monthly_amount_quarterly(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await create_budget_item(client, auth_headers, plan["id"], amount=300.0, payment_rhythm="quarterly")
        assert r.json()["monthly_amount"] == round(300.0 / 3, 2)

    async def test_monthly_amount_semi_annually(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await create_budget_item(client, auth_headers, plan["id"], amount=600.0, payment_rhythm="semi_annually")
        assert r.json()["monthly_amount"] == round(600.0 / 6, 2)

    async def test_monthly_amount_annually(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await create_budget_item(client, auth_headers, plan["id"], amount=1200.0, payment_rhythm="annually")
        assert r.json()["monthly_amount"] == round(1200.0 / 12, 2)

    async def test_create_item_with_note(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await create_budget_item(client, auth_headers, plan["id"], note="Faellig im Januar")
        assert r.status_code == 201
        assert r.json()["note"] == "Faellig im Januar"

    async def test_create_item_without_note(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await create_budget_item(client, auth_headers, plan["id"], note=None)
        assert r.status_code == 201
        assert r.json()["note"] is None

    async def test_create_item_negative_amount(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        cat_id = await get_expense_category_id(client, auth_headers)
        r = await client.post(f"/api/v1/plans/{plan['id']}/items/", json={
            "description": "Negativ",
            "amount": -100.0,
            "type": "expense",
            "category_id": cat_id,
            "payment_rhythm": "monthly",
        }, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_item_zero_amount(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        cat_id = await get_expense_category_id(client, auth_headers)
        r = await client.post(f"/api/v1/plans/{plan['id']}/items/", json={
            "description": "Null",
            "amount": 0.0,
            "type": "expense",
            "category_id": cat_id,
            "payment_rhythm": "monthly",
        }, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_item_missing_description(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        cat_id = await get_expense_category_id(client, auth_headers)
        r = await client.post(f"/api/v1/plans/{plan['id']}/items/", json={
            "amount": 100.0,
            "type": "expense",
            "category_id": cat_id,
            "payment_rhythm": "monthly",
        }, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_item_invalid_rhythm(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        cat_id = await get_expense_category_id(client, auth_headers)
        r = await client.post(f"/api/v1/plans/{plan['id']}/items/", json={
            "description": "Test",
            "amount": 100.0,
            "type": "expense",
            "category_id": cat_id,
            "payment_rhythm": "weekly",
        }, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_item_plan_not_found(self, client, auth_headers):
        cat_id = await get_expense_category_id(client, auth_headers)
        r = await client.post("/api/v1/plans/99999/items/", json={
            "description": "Test",
            "amount": 100.0,
            "type": "expense",
            "category_id": cat_id,
            "payment_rhythm": "monthly",
        }, headers=auth_headers)
        assert r.status_code == 404

    async def test_create_item_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        cat_id = await get_expense_category_id(client, second_user_headers)
        r = await client.post(f"/api/v1/plans/{plan['id']}/items/", json={
            "description": "Test",
            "amount": 100.0,
            "type": "expense",
            "category_id": cat_id,
            "payment_rhythm": "monthly",
        }, headers=second_user_headers)
        assert r.status_code == 403

    async def test_create_item_updates_plan_stats(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        await create_budget_item(client, auth_headers, plan["id"], amount=500.0, type="expense", payment_rhythm="monthly")
        await create_budget_item(client, auth_headers, plan["id"],
                                 amount=2000.0, type="income", payment_rhythm="monthly",
                                 category_id=await get_income_category_id(client, auth_headers))

        r = await client.get(f"/api/v1/plans/{plan['id']}", headers=auth_headers)
        data = r.json()
        assert data["budget_item_count"] == 2
        assert data["total_monthly_expenses"] == 500.0
        assert data["total_monthly_income"] == 2000.0
        assert data["monthly_balance"] == 1500.0


class TestUpdateBudgetItem:
    async def test_update_item_amount(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        item = (await create_budget_item(client, auth_headers, plan["id"], amount=100.0)).json()

        r = await client.put(f"/api/v1/plans/{plan['id']}/items/{item['id']}",
                             json={"amount": 250.0}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["amount"] == 250.0
        assert r.json()["monthly_amount"] == 250.0

    async def test_update_item_description(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        item = (await create_budget_item(client, auth_headers, plan["id"])).json()

        r = await client.put(f"/api/v1/plans/{plan['id']}/items/{item['id']}",
                             json={"description": "Neue Bezeichnung"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["description"] == "Neue Bezeichnung"

    async def test_update_item_rhythm_recalculates_monthly(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        item = (await create_budget_item(client, auth_headers, plan["id"],
                                         amount=1200.0, payment_rhythm="monthly")).json()
        assert item["monthly_amount"] == 1200.0

        r = await client.put(f"/api/v1/plans/{plan['id']}/items/{item['id']}",
                             json={"payment_rhythm": "annually"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["monthly_amount"] == 100.0

    async def test_update_item_not_found(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.put(f"/api/v1/plans/{plan['id']}/items/99999",
                             json={"amount": 100.0}, headers=auth_headers)
        assert r.status_code == 404

    async def test_update_item_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        item = (await create_budget_item(client, auth_headers, plan["id"])).json()
        r = await client.put(f"/api/v1/plans/{plan['id']}/items/{item['id']}",
                             json={"amount": 999.0}, headers=second_user_headers)
        assert r.status_code == 403


class TestDeleteBudgetItem:
    async def test_delete_item_success(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        item = (await create_budget_item(client, auth_headers, plan["id"])).json()

        r = await client.delete(f"/api/v1/plans/{plan['id']}/items/{item['id']}", headers=auth_headers)
        assert r.status_code == 204

        r = await client.get(f"/api/v1/plans/{plan['id']}/items/", headers=auth_headers)
        assert r.json() == []

    async def test_delete_item_updates_plan_stats(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        item = (await create_budget_item(client, auth_headers, plan["id"], amount=500.0)).json()

        r = await client.get(f"/api/v1/plans/{plan['id']}", headers=auth_headers)
        assert r.json()["budget_item_count"] == 1

        await client.delete(f"/api/v1/plans/{plan['id']}/items/{item['id']}", headers=auth_headers)

        r = await client.get(f"/api/v1/plans/{plan['id']}", headers=auth_headers)
        assert r.json()["budget_item_count"] == 0
        assert r.json()["total_monthly_expenses"] == 0.0

    async def test_delete_item_not_found(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.delete(f"/api/v1/plans/{plan['id']}/items/99999", headers=auth_headers)
        assert r.status_code == 404

    async def test_delete_item_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        item = (await create_budget_item(client, auth_headers, plan["id"])).json()
        r = await client.delete(f"/api/v1/plans/{plan['id']}/items/{item['id']}", headers=second_user_headers)
        assert r.status_code == 403
