"""
Tests for plan endpoints:
  GET    /plans/
  POST   /plans/
  GET    /plans/{id}
  PUT    /plans/{id}
  DELETE /plans/{id}
  POST   /plans/{id}/duplicate
  GET    /plans/{id}/export/pdf
  GET    /plans/{id}/export/csv
"""
from tests.conftest import register, auth, create_plan, create_budget_item, get_expense_category_id


class TestListPlans:
    async def test_list_plans_empty(self, client, auth_headers):
        r = await client.get("/api/v1/plans/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    async def test_list_plans_returns_own_plans_only(self, client, auth_headers, second_user_headers):
        await create_plan(client, auth_headers, name="Plan A")
        await create_plan(client, auth_headers, name="Plan B")
        await create_plan(client, second_user_headers, name="Other Plan")

        r = await client.get("/api/v1/plans/", headers=auth_headers)
        assert r.status_code == 200
        names = [p["name"] for p in r.json()]
        assert "Plan A" in names
        assert "Plan B" in names
        assert "Other Plan" not in names

    async def test_list_plans_unauthenticated(self, client):
        r = await client.get("/api/v1/plans/")
        assert r.status_code == 403


class TestCreatePlan:
    async def test_create_plan_success(self, client, auth_headers):
        r = await client.post("/api/v1/plans/", json={"name": "Haushaltsplan", "description": "Monatlich"}, headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Haushaltsplan"
        assert data["description"] == "Monatlich"
        assert data["budget_item_count"] == 0
        assert data["total_monthly_income"] == 0.0
        assert data["total_monthly_expenses"] == 0.0
        assert data["monthly_balance"] == 0.0

    async def test_create_plan_without_description(self, client, auth_headers):
        r = await client.post("/api/v1/plans/", json={"name": "Nur Name"}, headers=auth_headers)
        assert r.status_code == 201
        assert r.json()["description"] is None

    async def test_create_plan_missing_name(self, client, auth_headers):
        r = await client.post("/api/v1/plans/", json={"description": "Kein Name"}, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_plan_empty_name(self, client, auth_headers):
        r = await client.post("/api/v1/plans/", json={"name": ""}, headers=auth_headers)
        assert r.status_code == 422

    async def test_create_plan_unauthenticated(self, client):
        r = await client.post("/api/v1/plans/", json={"name": "Test"})
        assert r.status_code == 403


class TestGetPlan:
    async def test_get_plan_success(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.get(f"/api/v1/plans/{plan['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == plan["id"]

    async def test_get_plan_not_found(self, client, auth_headers):
        r = await client.get("/api/v1/plans/99999", headers=auth_headers)
        assert r.status_code == 404

    async def test_get_plan_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.get(f"/api/v1/plans/{plan['id']}", headers=second_user_headers)
        assert r.status_code == 403

    async def test_get_plan_includes_stats(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        await create_budget_item(client, auth_headers, plan["id"], amount=1200.0, payment_rhythm="annually", type="expense")

        r = await client.get(f"/api/v1/plans/{plan['id']}", headers=auth_headers)
        data = r.json()
        assert data["budget_item_count"] == 1
        assert data["total_monthly_expenses"] == round(1200.0 / 12, 2)
        assert data["monthly_balance"] == round(-1200.0 / 12, 2)


class TestUpdatePlan:
    async def test_update_plan_success(self, client, auth_headers):
        plan = await create_plan(client, auth_headers, name="Alt")
        r = await client.put(f"/api/v1/plans/{plan['id']}", json={"name": "Neu", "description": "Aktualisiert"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Neu"
        assert r.json()["description"] == "Aktualisiert"

    async def test_update_plan_not_found(self, client, auth_headers):
        r = await client.put("/api/v1/plans/99999", json={"name": "X"}, headers=auth_headers)
        assert r.status_code == 404

    async def test_update_plan_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.put(f"/api/v1/plans/{plan['id']}", json={"name": "X"}, headers=second_user_headers)
        assert r.status_code == 403


class TestDeletePlan:
    async def test_delete_plan_success(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.delete(f"/api/v1/plans/{plan['id']}", headers=auth_headers)
        assert r.status_code == 204

        r = await client.get(f"/api/v1/plans/{plan['id']}", headers=auth_headers)
        assert r.status_code == 404

    async def test_delete_plan_not_found(self, client, auth_headers):
        r = await client.delete("/api/v1/plans/99999", headers=auth_headers)
        assert r.status_code == 404

    async def test_delete_plan_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.delete(f"/api/v1/plans/{plan['id']}", headers=second_user_headers)
        assert r.status_code == 403

    async def test_delete_plan_cascades_items(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        await create_budget_item(client, auth_headers, plan["id"])

        await client.delete(f"/api/v1/plans/{plan['id']}", headers=auth_headers)
        r = await client.get("/api/v1/plans/", headers=auth_headers)
        assert all(p["id"] != plan["id"] for p in r.json())


class TestDuplicatePlan:
    async def test_duplicate_plan_success(self, client, auth_headers):
        plan = await create_plan(client, auth_headers, name="Original")
        await create_budget_item(client, auth_headers, plan["id"], description="Miete", amount=800.0)

        r = await client.post(f"/api/v1/plans/{plan['id']}/duplicate", headers=auth_headers)
        assert r.status_code == 201
        data = r.json()
        assert "Kopie von" in data["name"]
        assert data["budget_item_count"] == 1

    async def test_duplicate_plan_not_found(self, client, auth_headers):
        r = await client.post("/api/v1/plans/99999/duplicate", headers=auth_headers)
        assert r.status_code == 404

    async def test_duplicate_plan_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.post(f"/api/v1/plans/{plan['id']}/duplicate", headers=second_user_headers)
        assert r.status_code == 403


class TestExports:
    async def test_pdf_export(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.get(f"/api/v1/plans/{plan['id']}/export/pdf", headers=auth_headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"

    async def test_csv_export(self, client, auth_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.get(f"/api/v1/plans/{plan['id']}/export/csv", headers=auth_headers)
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    async def test_export_wrong_user(self, client, auth_headers, second_user_headers):
        plan = await create_plan(client, auth_headers)
        r = await client.get(f"/api/v1/plans/{plan['id']}/export/pdf", headers=second_user_headers)
        assert r.status_code == 403
